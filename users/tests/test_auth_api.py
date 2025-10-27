import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_register_returns_tokens_and_user():
    client = APIClient()
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "S3curePassw0rd!",
        "password2": "S3curePassw0rd!",
    }
    resp = client.post("/api/auth/register/", payload, format="json")
    assert resp.status_code == 201, resp.content
    data = resp.json()
    assert "user" in data and data["user"]["username"] == "alice"
    assert "access" in data and "refresh" in data


@pytest.mark.django_db
def test_login_with_token_obtain_pair():
    User.objects.create_user(
        username="bob", email="bob@example.com", password="S3curePassw0rd!"
    )
    client = APIClient()
    resp = client.post(
        "/api/auth/token/",
        {"username": "bob", "password": "S3curePassw0rd!"},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    data = resp.json()
    assert "access" in data and "refresh" in data


@pytest.mark.django_db
def test_me_requires_auth_and_returns_user():
    user = User.objects.create_user(username="carol", password="S3curePassw0rd!")
    client = APIClient()

    # UNAUTHENTICATED

    resp = client.get("/api/auth/me/")
    assert resp.status_code in (401, 403)

    # AUTHENTICATED WITH JWT

    login = client.post(
        "/api/auth/token/",
        {"username": "carol", "password": "S3curePassw0rd!"},
        format="json",
    )
    token = login.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    resp = client.get("/api/auth/me/")
    assert resp.status_code == 200
    assert resp.json()["username"] == "carol"
