import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_me_profile_view_and_update():
    client = APIClient()
    u = User.objects.create_user(username="alice", password="S3curePassw0rd!")
    client.force_authenticate(user=u)

    r = client.get("/api/users/me/profile/")
    assert r.status_code == 200
    assert r.json()["user"]["username"] == "alice"

    r = client.patch("/api/users/me/profile/", {"bio": "Hello"}, format="json")
    assert r.status_code == 200
    assert r.json()["bio"] == "Hello"


@pytest.mark.django_db
def test_profile_comments_crud_and_rating():
    client = APIClient()
    owner = User.objects.create_user(username="owner", password="S3curePassw0rd!")
    visitor = User.objects.create_user(username="visitor", password="S3curePassw0rd!")

    # LIST COMMENTS (EMPTY)

    r = client.get("/api/users/owner/comments/")
    assert r.status_code == 200 and r.json() == []

    # CREATE REQUIRES AUTH

    r = client.post(
        "/api/users/owner/comments/", {"body": "Nice profile"}, format="json"
    )
    assert r.status_code in (401, 403)

    # CREATE COMMENT

    client.force_authenticate(user=visitor)
    r = client.post(
        "/api/users/owner/comments/", {"body": "Nice profile"}, format="json"
    )
    assert r.status_code == 201
    cid = r.json()["id"]

    # RATE COMMENT

    rate = client.post(
        f"/api/users/owner/comments/{cid}/rate/", {"value": 1}, format="json"
    )
    assert rate.status_code == 200 and rate.json()["score"] == 1

    # CREATED_AT SHOULD BE UNIX INT

    r = client.get("/api/users/owner/comments/")
    assert isinstance(r.json()[0]["created_at"], int)

    # CLEAR RATING

    rate = client.delete(f"/api/users/owner/comments/{cid}/rate/")
    assert rate.status_code == 200 and rate.json()["my_vote"] == 0

    # EDIT BY AUTHOR

    r = client.patch(
        f"/api/users/owner/comments/{cid}/",
        {"body": "Edited profile comment"},
        format="json",
    )
    assert r.status_code == 200 and r.json()["body"] == "Edited profile comment"

    # MARKDOWN RENDERING AND SANITIZATION

    r = client.post(
        "/api/users/owner/comments/",
        {"body": "Hello **world** <script>bad()</script>"},
        format="json",
    )
    assert r.status_code == 201
    c2 = r.json()
    assert "<strong>" in c2.get("body_html", "")
    assert "<script" not in c2.get("body_html", "")

    # PROFILE OWNER CANNOT EDIT OTHERS' COMMENT

    client.force_authenticate(user=owner)
    r = client.patch(
        f"/api/users/owner/comments/{cid}/",
        {"body": "Owner trying to edit visitor's comment"},
        format="json",
    )
    assert r.status_code in (401, 403)

    # PROFILE OWNER CAN DELETE ANY

    client.force_authenticate(user=owner)
    r = client.post("/api/users/owner/comments/", {"body": "Visitor 2"}, format="json")
    cid2 = r.json()["id"]
    client.force_authenticate(user=owner)
    r = client.delete(f"/api/users/owner/comments/{cid2}/")
    assert r.status_code == 204

    # ADMIN OVERRIDE DELETE

    r = client.post("/api/users/owner/comments/", {"body": "Again"}, format="json")
    cid3 = r.json()["id"]
    admin = User.objects.create_superuser(
        username="admin", email="admin@example.com", password="AdminPass123!"
    )
    client.force_authenticate(user=admin)
    r = client.get(f"/api/users/owner/comments/{cid3}/history/")
    assert r.status_code == 200
    r = client.delete(f"/api/users/owner/comments/{cid3}/")
    assert r.status_code == 204
    r = client.delete(f"/api/users/owner/comments/{cid2}/")
    assert r.status_code in (204, 404)
