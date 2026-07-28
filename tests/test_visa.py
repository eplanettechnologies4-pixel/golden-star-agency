import pytest
from fastapi.testclient import TestClient
from fast_api.main import app

client = TestClient(app)

def test_visa_countries_endpoint():
    """
    Assert that the visa countries endpoint returns major packages successfully.
    """
    response = client.get("/visa/countries")
    assert response.status_code == 200
    countries = [c["name"] for c in response.json()["countries"]]
    assert "Saudi Arabia" in countries

def test_visa_apply_endpoint():
    response = client.post("/visa/apply")
    assert response.status_code == 200
    assert response.json()["status"] == "submitted"
