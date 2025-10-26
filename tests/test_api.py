"""Test API endpoints."""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_index_page() -> None:
    """Test index page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Stryktips Bot" in response.content
