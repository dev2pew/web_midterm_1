import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from model_bakery import baker

from forum.models import Thread

User = get_user_model()


@pytest.mark.django_db
def test_home_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"threads" in r.content


@pytest.mark.django_db
def test_about_page(client):
    r = client.get("/about/")
    assert r.status_code == 200
    assert b"about" in r.content


@pytest.mark.django_db
def test_thread_edit_permissions():
    """
    Verify that only the author or an admin can access a thread's edit page.
    """

    author = User.objects.create_user(username="author", password="p")
    other_user = User.objects.create_user(username="other", password="p")
    admin = User.objects.create_superuser(
        username="admin", password="p", email="a@a.com"
    )
    thread = baker.make(Thread, author=author)
    url = f"/t/{thread.slug}/edit/"

    guest_client = Client()
    response_guest = guest_client.get(url)
    assert response_guest.status_code == 302

    other_client = Client()
    other_client.login(username="other", password="p")
    response_other = other_client.get(url)
    assert response_other.status_code == 403
    assert b"permission denied" in response_other.content
    assert b"not allowed to edit this thread" in response_other.content

    author_client = Client()
    author_client.login(username="author", password="p")
    response_author = author_client.get(url)
    assert response_author.status_code == 200

    admin_client = Client()
    admin_client.login(username="admin", password="p")
    response_admin = admin_client.get(url)
    assert response_admin.status_code == 200
