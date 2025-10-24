import pytest


def test_health_check(client):
    """Health check endpoint at /health"""
    response = client.get("/health")
    assert response.status_code == 200
    # If response is HTML (Dash frontend), skip JSON parsing
    if "text/html" in response.headers.get("content-type", ""):
        assert "evaonline" in response.text.lower() or "html" in response.text.lower()
    else:
        body = response.json()
        assert isinstance(body, dict)
        assert "status" in body or "message" in body
