"""Tests for the login endpoint — validates empty/whitespace password handling."""

import pytest
from unittest.mock import patch


@pytest.fixture()
def client():
    """TestClient with test settings and lifespan mocked to avoid DB/Redis."""
    from core.config import Settings

    test_settings = Settings(
        auth_enabled=True,
        admin_username="admin",
        admin_password="secret123",
        jwt_secret="test-jwt-secret",
        database_url="sqlite+aiosqlite:///./test_automaintainer.db",
        dashscope_api_key="",
    )

    # Mock lifespan to skip DB/Redis init
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_lifespan(app):
        yield

    import main as main_mod
    main_mod.app.router.lifespan_context = mock_lifespan

    from fastapi.testclient import TestClient

    # Patch get_settings everywhere to return test_settings
    with patch("core.config.get_settings", return_value=test_settings), \
         patch("core.auth.get_settings", return_value=test_settings), \
         patch("main.get_settings", return_value=test_settings):
        main_mod.settings = test_settings
        with TestClient(main_mod.app) as c:
            yield c


class TestLoginEmptyPassword:
    """Verify that empty or whitespace-only passwords return 400, not 500."""

    def test_empty_password_returns_400(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": ""},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "required" in data["detail"].lower()

    def test_whitespace_only_password_returns_400(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "   "},
        )
        assert resp.status_code == 400

    def test_empty_username_returns_400(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "", "password": "secret123"},
        )
        assert resp.status_code == 400

    def test_whitespace_only_username_returns_400(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "   ", "password": "secret123"},
        )
        assert resp.status_code == 400

    def test_valid_credentials_return_200(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "secret123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_missing_password_field_returns_not_500(self, client):
        """When password field is absent, should never return 500."""
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin"},
        )
        assert resp.status_code != 500
