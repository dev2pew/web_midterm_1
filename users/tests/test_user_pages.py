import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from model_bakery import baker

from forum.models import Thread

User = get_user_model()


@pytest.fixture
def users():
    """FIXTURE TO CREATE GUEST, USER, AND ADMIN ROLES WITH DJANGO TEST CLIENTS."""

    guest_client = Client()

    user_obj = User.objects.create_user(username="testuser", password="password")
    user_client = Client()
    assert user_client.login(username="testuser", password="password")

    admin_obj = User.objects.create_superuser(
        username="testadmin", password="password", email="a@a.com"
    )
    admin_client = Client()
    assert admin_client.login(username="testadmin", password="password")

    return {
        "guest": guest_client,
        "user": user_client,
        "admin": admin_client,
        "user_obj": user_obj,
    }


@pytest.mark.django_db
class TestPageVisibility:
    def test_home_page_visibility(self, users):
        r_guest = users["guest"].get("/")
        assert r_guest.status_code == 200
        assert b'href="/auth/login/"' in r_guest.content

        r_user = users["user"].get("/")
        assert r_user.status_code == 200
        assert b'href="/u/testuser/"' in r_user.content

    def test_auth_pages_for_guests(self, users):
        assert users["guest"].get("/auth/login/").status_code == 200
        assert users["guest"].get("/auth/register/").status_code == 200

    def test_auth_pages_redirect_for_logged_in_users(self, users):
        response_login = users["user"].get("/auth/login/")
        assert response_login.status_code == 302
        assert response_login.url == "/"

        response_register = users["user"].get("/auth/register/")
        assert response_register.status_code == 302
        assert response_register.url == "/"

    def test_profile_page_content(self, users):
        other_user = baker.make(User, username="otheruser")
        r_own = users["user"].get(f"/u/{users['user_obj'].username}/")
        assert r_own.status_code == 200
        assert b'href="/u/testuser/edit/"' in r_own.content
        assert b"btn-mod-open" not in r_own.content

        r_other = users["user"].get(f"/u/{other_user.username}/")
        assert r_other.status_code == 200
        assert f'href="/u/{other_user.username}/edit/"'.encode() not in r_other.content

        r_admin = users["admin"].get(f"/u/{other_user.username}/")
        assert r_admin.status_code == 200
        assert b"btn-mod-open" in r_admin.content

    def test_profile_edit_permissions(self, users):
        """VERIFY USERS CANNOT ACCESS THE EDIT PAGE OF OTHER USERS."""

        other_user = baker.make(User, username="otheruser")

        guest_response = users["guest"].get(f"/u/{other_user.username}/edit/")
        assert guest_response.status_code == 302

        user_response = users["user"].get(f"/u/{other_user.username}/edit/")
        assert user_response.status_code == 403
        assert b"permission denied" in user_response.content
        assert b"not allowed to edit this profile" in user_response.content

        own_response = users["user"].get(f"/u/{users['user_obj'].username}/edit/")
        assert own_response.status_code == 200

    def test_thread_detail_page_content(self, users):
        thread = baker.make(Thread, author=baker.make(User))
        url = f"/t/{thread.slug}/"

        r_guest = users["guest"].get(url)
        assert r_guest.status_code == 200
        assert b"login to reply" in r_guest.content

        r_user = users["user"].get(url)
        assert r_user.status_code == 200
        assert b"post reply" in r_user.content
