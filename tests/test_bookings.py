import pytest
from fastapi.testclient import TestClient
from fast_api.main import app

client = TestClient(app)

def test_booking_scaffold_response():
    """
    Assert that the bookings scaffolding endpoint returns status successfully.
    """
    response = client.post("/bookings/")
    assert response.status_code == 200
    assert response.json() == {"message": "Booking created successfully"}

def test_booking_detail_scaffold():
    response = client.get("/bookings/42")
    assert response.status_code == 200
    assert response.json() == {"booking_id": 42, "status": "pending"}
