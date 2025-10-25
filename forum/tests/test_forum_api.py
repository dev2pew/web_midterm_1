import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_threads_list_and_create():
    client = APIClient()

    # LIST WITHOUT DATA
    r = client.get("/api/threads/")
    assert r.status_code == 200
    assert r.json() == []

    # CREATE REQUIRES AUTH
    r = client.post("/api/threads/", {"title": "first thread"}, format="json")
    assert r.status_code in (401, 403)

    # CREATE WITH AUTH
    u = User.objects.create_user(username="alice", password="S3curePassw0rd!")
    client.force_authenticate(user=u)
    r = client.post("/api/threads/", {"title": "first thread"}, format="json")
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "first thread"
    assert data["author"]["username"] == "alice"
    assert data["slug"]

    # LIST NOW HAS ONE
    r = client.get("/api/threads/")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.django_db
def test_thread_retrieve_and_posts_flow():
    client = APIClient()
    u = User.objects.create_user(username="bob", password="S3curePassw0rd!")
    client.force_authenticate(user=u)

    # CREATE THREAD
    t = client.post("/api/threads/", {"title": "announcements"}, format="json").json()
    slug = t["slug"]

    # LISTING POSTS UNAUTH OK (EMPTY)
    client.force_authenticate(user=None)
    r = client.get(f"/api/threads/{slug}/posts/")
    assert r.status_code == 200
    assert r.json() == []

    # CREATE POST REQUIRES AUTH
    r = client.post(f"/api/threads/{slug}/posts/", {"body": "hello"}, format="json")
    assert r.status_code in (401, 403)

    # CREATE POST AUTHED
    client.force_authenticate(user=u)
    r = client.post(f"/api/threads/{slug}/posts/", {"body": "hello"}, format="json")
    assert r.status_code == 201
    post = r.json()
    assert post["body"] == "hello"
    assert post["thread"] == slug

    # RATING SET AND UNSET
    pid = post["id"]
    rate = client.post(
        f"/api/threads/{slug}/posts/{pid}/rate/", {"value": 1}, format="json"
    )
    assert rate.status_code == 200
    assert rate.json()["score"] == 1 and rate.json()["my_vote"] == 1
    rate = client.post(
        f"/api/threads/{slug}/posts/{pid}/rate/", {"value": -1}, format="json"
    )
    assert rate.status_code == 200
    assert rate.json()["score"] == -1 and rate.json()["my_vote"] == -1
    rate = client.delete(f"/api/threads/{slug}/posts/{pid}/rate/")
    assert rate.status_code == 200
    assert rate.json()["my_vote"] == 0

    # THREAD DETAIL
    r = client.get(f"/api/threads/{slug}/")
    assert r.status_code == 200
    detail = r.json()
    assert detail["slug"] == slug
    assert detail["posts_count"] == 1

    # EDIT POST BY AUTHOR
    r = client.patch(
        f"/api/threads/{slug}/posts/{pid}/",
        {"body": "edited"},
        format="json",
    )
    assert r.status_code == 200, r.content
    r = client.get(f"/api/threads/{slug}/posts/")
    p_after = r.json()[0]
    assert p_after["body"] == "edited"
    assert p_after["edit_count"] == 1
    assert isinstance(p_after["created_at"], int)
    assert p_after["last_edited_at"]

    # MARKDOWN RENDERING AND SANITIZATION
    r = client.post(
        f"/api/threads/{slug}/posts/",
        {"body": "**bold** <script>alert(1)</script>"},
        format="json",
    )
    assert r.status_code == 201
    created = r.json()
    assert "<strong>" in created.get("body_html", "")
    assert "<script" not in created.get("body_html", "")


@pytest.mark.django_db
def test_mentions_linkify_in_post_body():
    client = APIClient()
    author = User.objects.create_user(username="author2", password="x")
    other = User.objects.create_user(username="other2", password="x")
    client.force_authenticate(user=author)
    t = client.post("/api/threads/", {"title": "mentions"}, format="json").json()
    slug = t["slug"]
    p = client.post(
        f"/api/threads/{slug}/posts/", {"body": "ping @other2"}, format="json"
    ).json()
    assert 'href="/u/other2/"' in p.get("body_html", "")
    assert ">@other2<" in p.get("body_html", "")
