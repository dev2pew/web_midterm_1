import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from rest_framework.test import APIClient

from forum.models import Post, Thread

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def users():
    """FIXTURE TO CREATE GUEST, USER, AND ADMIN ROLES."""

    guest = APIClient()
    user = baker.make(User, username="testuser")
    user_client = APIClient()
    user_client.force_authenticate(user=user)
    admin = baker.make(User, username="testadmin", is_staff=True)
    admin_client = APIClient()
    admin_client.force_authenticate(user=admin)
    return {
        "guest": guest,
        "user": user_client,
        "user_obj": user,
        "admin": admin_client,
    }


@pytest.mark.django_db
class TestThreadPermissions:
    def test_thread_creation_permissions(self, users):
        data = {"title": "A test thread"}
        # GUEST CANNOT CREATE

        r_guest = users["guest"].post("/api/threads/", data)
        assert r_guest.status_code == 401

        # USER AND ADMIN CAN CREATE

        r_user = users["user"].post("/api/threads/", data)
        assert r_user.status_code == 201
        r_admin = users["admin"].post("/api/threads/", data)
        assert r_admin.status_code == 201

    def test_thread_modification_permissions(self, users):
        # THREAD CREATED BY THE STANDARD USER

        thread = baker.make(Thread, author=users["user_obj"], title="Original Title")
        url = f"/api/threads/{thread.slug}/"
        data = {"title": "Updated Title"}

        # GUEST CANNOT EDIT OR DELETE

        assert users["guest"].patch(url, data).status_code == 401
        assert users["guest"].delete(url).status_code == 401

        # USER (AUTHOR) CAN EDIT AND DELETE THEIR OWN THREAD

        assert users["user"].patch(url, data).status_code == 200
        assert users["user"].delete(url).status_code == 204

        # ADMIN CAN EDIT AND DELETE OTHER'S THREAD

        thread2 = baker.make(Thread, author=users["user_obj"])
        url2 = f"/api/threads/{thread2.slug}/"
        assert users["admin"].patch(url2, data).status_code == 200
        assert users["admin"].delete(url2).status_code == 204

    def test_user_cannot_modify_others_thread(self, users):
        other_user = baker.make(User)
        thread = baker.make(Thread, author=other_user)
        url = f"/api/threads/{thread.slug}/"

        # THE AUTHENTICATED 'USER' CANNOT MODIFY A THREAD OWNED BY 'OTHER_USER'

        assert users["user"].patch(url, {"title": "Hacked"}).status_code == 403
        assert users["user"].delete(url).status_code == 403


@pytest.mark.django_db
class TestPostPermissions:
    def test_post_creation_permissions(self, users):
        thread = baker.make(Thread)
        url = f"/api/threads/{thread.slug}/posts/"
        data = {"body": "A test post"}

        # GUEST CANNOT CREATE

        assert users["guest"].post(url, data).status_code == 401

        # USER AND ADMIN CAN CREATE

        assert users["user"].post(url, data).status_code == 201
        assert users["admin"].post(url, data).status_code == 201

    def test_post_modification_permissions(self, users):
        thread = baker.make(Thread)
        post = baker.make(Post, thread=thread, author=users["user_obj"])
        url = f"/api/threads/{thread.slug}/posts/{post.id}/"
        data = {"body": "Updated body"}

        # GUEST CANNOT MODIFY

        assert users["guest"].patch(url, data).status_code == 401
        assert users["guest"].delete(url).status_code == 401

        # USER (AUTHOR) CAN MODIFY THEIR OWN POST

        assert users["user"].patch(url, data).status_code == 200
        assert users["user"].delete(url).status_code == 204

        # ADMIN CAN MODIFY OTHER'S POST

        post2 = baker.make(Post, thread=thread, author=users["user_obj"])
        url2 = f"/api/threads/{thread.slug}/posts/{post2.id}/"
        assert users["admin"].patch(url2, data).status_code == 200
        assert users["admin"].delete(url2).status_code == 204

    def test_post_voting_permissions(self, users):
        post = baker.make(Post)
        url = f"/api/threads/{post.thread.slug}/posts/{post.id}/rate/"
        data = {"value": 1}

        # GUEST CANNOT VOTE

        assert users["guest"].post(url, data).status_code == 401

        # USER AND ADMIN CAN VOTE

        assert users["user"].post(url, data).status_code == 200
        assert users["admin"].post(url, data).status_code == 200

    def test_post_history_view_permissions(self, users):
        post = baker.make(Post, author=users["user_obj"])
        url = f"/api/threads/{post.thread.slug}/posts/{post.id}/history/"

        # GUEST AND USER CANNOT VIEW HISTORY

        assert users["guest"].get(url).status_code == 401
        assert users["user"].get(url).status_code == 403

        # ADMIN CAN VIEW HISTORY

        assert users["admin"].get(url).status_code == 200
