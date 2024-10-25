import json
from datetime import date

import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


@pytest.fixture
def deposit_transaction():
    return {
        "amount": 10.5,
        "type": "deposit",
        "date": date.today().strftime("%Y-%m-%d"),
    }


def test_hello():
    """
    test de hello
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_transactions():
    """test endpoint of getting transactions"""
    response = client.get("users/1/transactions")
    assert response.status_code == 200
    for transaction in response.json():
        assert transaction["user_id"] == 1


def test_get_existing_transaction():
    """test endpoint of getting existing transaction"""
    response = client.get("users/1/transactions/1")
    assert response.status_code == 200
    transaction = response.json()
    assert transaction["user_id"] == 1
    assert transaction["id"] == 1


def test_get_nonexisting_transaction():
    """test endpoint of getting nonexisting transaction"""
    response = client.get("users/1/transactions/9999")
    assert response.status_code == 404


def test_get_transaction_nonexisting_user():
    """test endpoint of getting nonexisting transaction with non-existing user"""
    response = client.get("users/999/transactions/1")
    assert response.status_code == 404


def test_create_transaction(deposit_transaction):
    """test endpoint of creating transaction"""
    response = client.post("users/2/transactions", json=deposit_transaction)
    assert response.status_code == 200
    transaction = response.json()
    assert transaction["user_id"] == 2
    assert transaction["amount"] == 10.5
    assert transaction["type"] == "deposit"
    assert transaction["date"] == date.today().isoformat()
    assert transaction["state"] == "pending"


def test_get_balance_with_a_noncovert_transaction():
    """test endpoint of getting balance with non-covert transaction"""
    response_dict = {
        "remaining_balance": 0,
        "scheduled_withdrawals": [
            {"amount": 20.0, "coverage_rate": 100, "covered_amount": 20.0},
            {"amount": 20.0, "coverage_rate": 100, "covered_amount": 20.0},
            {"amount": 20.0, "coverage_rate": 25, "covered_amount": 5.0},
            {"amount": 20.0, "coverage_rate": 0, "covered_amount": 0},
        ],
    }
    response = client.get("user/4/transactions/balance")

    assert response.status_code == 200
    assert response_dict == json.loads(response.text)


def test_get_balance_with_a_covert_transaction():
    """test endpoint of getting balance with covert transaction"""
    response_dict = {
        "remaining_balance": 10,
        "scheduled_withdrawals": [
            {"amount": 20.0, "coverage_rate": 100, "covered_amount": 20.0}
        ],
    }

    response = client.get("user/5/transactions/balance")

    assert response.status_code == 200
    assert response_dict == json.loads(response.text)


def test_get_balance_nonexisting_user():
    """test endpoint of getting balance with non-existing user"""
    response = client.get("user/999/transactions/balance")
    assert response.status_code == 404


def test_get_balance_nonexisting_transaction():
    """test endpoint of getting balance with non-existing transaction"""
    response = client.get("user/6/transactions/balance")
    assert response.status_code == 200
