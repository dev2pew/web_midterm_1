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
    """Fixture to create guest, user, and admin roles."""
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
        # Guest cannot create
        r_guest = users["guest"].post("/api/threads/", data)
        assert r_guest.status_code == 401

        # User and Admin can create
        r_user = users["user"].post("/api/threads/", data)
        assert r_user.status_code == 201
        r_admin = users["admin"].post("/api/threads/", data)
        assert r_admin.status_code == 201

    def test_thread_modification_permissions(self, users):
        # Thread created by the standard user
        thread = baker.make(Thread, author=users["user_obj"], title="Original Title")
        url = f"/api/threads/{thread.slug}/"
        data = {"title": "Updated Title"}

        # Guest cannot edit or delete
        assert users["guest"].patch(url, data).status_code == 401
        assert users["guest"].delete(url).status_code == 401

        # User (author) can edit and delete their own thread
        assert users["user"].patch(url, data).status_code == 200
        assert users["user"].delete(url).status_code == 204

        # Admin can edit and delete other's thread
        thread2 = baker.make(Thread, author=users["user_obj"])
        url2 = f"/api/threads/{thread2.slug}/"
        assert users["admin"].patch(url2, data).status_code == 200
        assert users["admin"].delete(url2).status_code == 204

    def test_user_cannot_modify_others_thread(self, users):
        other_user = baker.make(User)
        thread = baker.make(Thread, author=other_user)
        url = f"/api/threads/{thread.slug}/"

        # The authenticated 'user' cannot modify a thread owned by 'other_user'
        assert users["user"].patch(url, {"title": "Hacked"}).status_code == 403
        assert users["user"].delete(url).status_code == 403


@pytest.mark.django_db
class TestPostPermissions:
    def test_post_creation_permissions(self, users):
        thread = baker.make(Thread)
        url = f"/api/threads/{thread.slug}/posts/"
        data = {"body": "A test post"}

        # Guest cannot create
        assert users["guest"].post(url, data).status_code == 401

        # User and Admin can create
        assert users["user"].post(url, data).status_code == 201
        assert users["admin"].post(url, data).status_code == 201

    def test_post_modification_permissions(self, users):
        thread = baker.make(Thread)
        post = baker.make(Post, thread=thread, author=users["user_obj"])
        url = f"/api/threads/{thread.slug}/posts/{post.id}/"
        data = {"body": "Updated body"}

        # Guest cannot modify
        assert users["guest"].patch(url, data).status_code == 401
        assert users["guest"].delete(url).status_code == 401

        # User (author) can modify their own post
        assert users["user"].patch(url, data).status_code == 200
        assert users["user"].delete(url).status_code == 204

        # Admin can modify other's post
        post2 = baker.make(Post, thread=thread, author=users["user_obj"])
        url2 = f"/api/threads/{thread.slug}/posts/{post2.id}/"
        assert users["admin"].patch(url2, data).status_code == 200
        assert users["admin"].delete(url2).status_code == 204

    def test_post_voting_permissions(self, users):
        post = baker.make(Post)
        url = f"/api/threads/{post.thread.slug}/posts/{post.id}/rate/"
        data = {"value": 1}

        # Guest cannot vote
        assert users["guest"].post(url, data).status_code == 401

        # User and Admin can vote
        assert users["user"].post(url, data).status_code == 200
        assert users["admin"].post(url, data).status_code == 200

    def test_post_history_view_permissions(self, users):
        post = baker.make(Post, author=users["user_obj"])
        url = f"/api/threads/{post.thread.slug}/posts/{post.id}/history/"

        # Guest and User cannot view history
        assert users["guest"].get(url).status_code == 401
        assert users["user"].get(url).status_code == 403

        # Admin can view history
        assert users["admin"].get(url).status_code == 200
