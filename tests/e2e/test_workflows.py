import pytest


@pytest.mark.e2e
def test_api_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    if "text/html" not in resp.headers.get("content-type", ""):
        data = resp.json()
        assert "status" in data or "message" in data


@pytest.mark.e2e
def test_frontend_root_available():
    """Integration-like smoke test; requires frontend running."""
    import requests

    url = "http://localhost:8050/"
    r = requests.get(url, timeout=5)
    assert r.status_code == 200
    assert "EVAonline" in r.text or "evaonline" in r.text
