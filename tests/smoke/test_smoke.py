"""Smoke tests for deployed environments."""

import os

import httpx


BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


def test_health_endpoint():
    """Return ok for the liveness endpoint."""
    response = httpx.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint():
    """Return ready for the readiness endpoint."""
    response = httpx.get(f"{BASE_URL}/ready", timeout=5)
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
