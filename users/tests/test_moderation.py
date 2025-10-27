import pytest
from django.contrib.auth import get_user_model
from django.test import Client as DjangoClient
from django.utils import timezone
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_moderation_silence_and_ban_block_posting():
    client = APIClient()
    admin = User.objects.create_superuser(
        username="admin", email="a@a.com", password="x"
    )
    u = User.objects.create_user(username="u1", password="x")

    # USER CAN CREATE THREAD INITIALLY

    client.force_authenticate(user=u)
    r = client.post("/api/threads/", {"title": "Hello"}, format="json")
    assert r.status_code == 201

    # ADMIN SILENCES FOR 1 HOUR

    client.force_authenticate(user=admin)
    now = int(timezone.now().timestamp())
    client.patch(
        f"/api/users/{u.username}/moderation/",
        {"silenced_until": now + 3600},
        format="json",
    )

    client.force_authenticate(user=u)
    r = client.post("/api/threads/", {"title": "Hello2"}, format="json")
    assert r.status_code in (401, 403)

    # ADMIN BANS FOR 1 HOUR

    client.force_authenticate(user=admin)
    client.patch(
        f"/api/users/{u.username}/moderation/",
        {"banned_until": now + 3600},
        format="json",
    )

    client.force_authenticate(user=u)
    r = client.post("/api/threads/", {"title": "Hello3"}, format="json")
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_admin_cannot_silence_admin_or_self():
    client = APIClient()
    admin1 = User.objects.create_user(username="admin1", password="x", is_staff=True)
    admin2 = User.objects.create_user(username="admin2", password="x", is_staff=True)
    now = int(timezone.now().timestamp())

    client.force_authenticate(user=admin1)

    # CANNOT SILENCE OTHER ADMIN

    r = client.patch(
        f"/api/users/{admin2.username}/moderation/",
        {"silenced_until": now + 3600},
        format="json",
    )
    assert r.status_code in (401, 403)

    # CANNOT SILENCE SELF

    r = client.patch(
        f"/api/users/{admin1.username}/moderation/",
        {"silenced_until": now + 3600},
        format="json",
    )
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_superuser_can_silence_anyone_except_self():
    client = APIClient()
    su = User.objects.create_superuser(username="root", email="r@x.com", password="x")
    admin = User.objects.create_user(username="a1", password="x", is_staff=True)
    user = User.objects.create_user(username="u2", password="x")
    now = int(timezone.now().timestamp())

    client.force_authenticate(user=su)

    # CAN SILENCE ADMIN

    r1 = client.patch(
        f"/api/users/{admin.username}/moderation/",
        {"silenced_until": now + 3600},
        format="json",
    )
    assert r1.status_code == 200

    # CAN SILENCE REGULAR USER

    r2 = client.patch(
        f"/api/users/{user.username}/moderation/",
        {"silenced_until": now + 3600},
        format="json",
    )
    assert r2.status_code == 200

    # CANNOT SILENCE SELF

    r3 = client.patch(
        f"/api/users/{su.username}/moderation/",
        {"silenced_until": now + 3600},
        format="json",
    )
    assert r3.status_code in (401, 403)


@pytest.mark.django_db
def test_banned_user_cannot_view_pages_or_api():
    client = APIClient()

    # SETUP THREAD BY SOMEONE ELSE

    author = User.objects.create_user(username="author", password="x")
    banned = User.objects.create_user(username="ban", password="x")
    client.force_authenticate(user=author)
    t = client.post("/api/threads/", {"title": "Hello"}, format="json").json()

    # BAN THE USER

    admin = User.objects.create_superuser(
        username="adminx", email="a@a.com", password="x"
    )
    client.force_authenticate(user=admin)
    now = int(timezone.now().timestamp())
    client.patch(
        f"/api/users/{banned.username}/moderation/",
        {"banned_until": now + 3600},
        format="json",
    )

    client.force_authenticate(user=banned)

    # PAGES BLOCKED VIA SESSION CLIENT

    session_client = DjangoClient()
    assert session_client.login(username="ban", password="x")
    r = session_client.get("/")
    assert r.status_code in (401, 403)
    r = session_client.get(f"/t/{t['slug']}/")
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_superuser_unsilence_unban():
    client = APIClient()
    su = User.objects.create_superuser(username="root2", email="r2@x.com", password="x")
    user = User.objects.create_user(username="u3", password="x")
    now = int(timezone.now().timestamp())

    client.force_authenticate(user=su)

    # SET BOTH

    r1 = client.patch(
        f"/api/users/{user.username}/moderation/",
        {"silenced_until": now + 1800, "banned_until": now + 1800},
        format="json",
    )
    assert r1.status_code == 200

    # VERIFY PRESENT

    prof = client.get(f"/api/users/{user.username}/profile/").json()
    assert prof["silenced_until_unix"] and prof["banned_until_unix"]

    # CLEAR BOTH

    r2 = client.patch(
        f"/api/users/{user.username}/moderation/",
        {"silenced_until": None, "banned_until": None},
        format="json",
    )
    assert r2.status_code == 200
    prof2 = client.get(f"/api/users/{user.username}/profile/").json()
    assert prof2["silenced_until_unix"] is None and prof2["banned_until_unix"] is None
