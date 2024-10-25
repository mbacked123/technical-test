from typing import List
from backend.models import (
    Transaction,
    TransactionRow,
    TransactionState,
    TransactionType,
)
from backend.models.interfaces import Database


def transactions(db: Database, user_id: int) -> List[TransactionRow]:
    """
    Returns all transactions of a user.
    """
    return [
        transaction
        for transaction in db.scan("transactions")
        if transaction.user_id == user_id
    ]


def transaction(db: Database, user_id: int, transaction_id: int) -> TransactionRow:
    """
    Returns a given transaction of the user
    """
    transaction = db.get("transactions", transaction_id)
    return transaction if transaction and transaction.user_id == user_id else None


def create_transaction(
    db: Database, user_id: int, transaction: Transaction
) -> TransactionRow:
    """
    Creates a new transaction (adds an ID) and returns it.
    """
    if transaction.type in (TransactionType.DEPOSIT, TransactionType.REFUND):
        initial_state = TransactionState.PENDING
    elif transaction.type == TransactionType.SCHEDULED_WITHDRAWAL:
        initial_state = TransactionState.SCHEDULED
    else:
        raise ValueError(f"Invalid transaction type {transaction.type}")
    transaction_row = TransactionRow(
        user_id=user_id, **transaction.dict(), state=initial_state
    )
    return db.put("transactions", transaction_row)


def compute_balance_payments_for_user(db: Database, user_id: int):
    """Computes the balance of payments for a user subscription."""
    transactions = [
        transaction
        for transaction in db.scan("transactions")
        if transaction.user_id == user_id
    ]

    # Calcul du solde de la cagnotte
    balance = sum(
        t.amount
        for t in transactions
        if t.type == TransactionType.DEPOSIT and t.state == TransactionState.COMPLETED
    )
    balance -= sum(
        t.amount
        for t in transactions
        if t.type == TransactionType.SCHEDULED_WITHDRAWAL
        and t.state == TransactionState.COMPLETED
    )
    balance -= sum(
        t.amount
        for t in transactions
        if t.type == TransactionType.REFUND
        and t.state in [TransactionState.COMPLETED, TransactionState.PENDING]
    )

    # Identifier les prélèvements programmés futurs
    scheduled_withdrawals = [
        t
        for t in transactions
        if t.type == TransactionType.SCHEDULED_WITHDRAWAL
        and t.state == TransactionState.SCHEDULED
    ]

    result = []
    for withdrawal in scheduled_withdrawals:
        amount = withdrawal.amount
        if balance >= amount:
            covered_amount = amount
            balance -= amount
            coverage_rate = 100
        elif balance > 0:
            covered_amount = balance
            coverage_rate = round(balance / amount * 100)
            balance = (
                0  # Le solde devient 0 car il ne peut plus couvrir de prélèvements
            )

        else:
            # Des qu'on finit pour le remboursement d'une echeance pas couvert à 100%
            covered_amount = 0
            coverage_rate = 0

        result.append(
            {
                "amount": amount,
                "covered_amount": covered_amount,
                "coverage_rate": coverage_rate,
            }
        )

    return {"scheduled_withdrawals": result, "remaining_balance": balance}
