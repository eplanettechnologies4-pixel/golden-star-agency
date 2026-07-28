import pytest
from fastapi.testclient import TestClient
from fast_api.main import app

client = TestClient(app)

def test_wallet_ledger_scaffold():
    """
    Verify payment processing endpoint status response.
    """
    response = client.post("/payments/pay")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "transaction_id" in response.json()
