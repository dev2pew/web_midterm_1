import json

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_notifications_on_thread_reply_and_mentions():
    client = APIClient()
    author = User.objects.create_user(username="author", password="x")
    replier = User.objects.create_user(username="replier", password="x")
    other = User.objects.create_user(username="other", password="x")

    # CREATE THREAD BY AUTHOR
    client.force_authenticate(user=author)
    t = client.post("/api/threads/", {"title": "Hello"}, format="json").json()

    # REPLY BY REPLIER WITH MENTION OF OTHER
    client.force_authenticate(user=replier)
    p = client.post(
        f"/api/threads/{t['slug']}/posts/", {"body": "Hi @other"}, format="json"
    ).json()

    # AUTHOR SHOULD HAVE A THREAD_REPLY NOTIFICATION; OTHER SHOULD HAVE MENTION
    client.force_authenticate(user=author)
    n = client.get("/api/notifications/?unread=1").json()
    assert any(i["type"] == "thread_reply" for i in n)

    client.force_authenticate(user=other)
    n2 = client.get("/api/notifications/?unread=1").json()
    assert any(i["type"] == "mention" for i in n2)
    # MENTION SHOULD INCLUDE POST TARGET
    mention = next(i for i in n2 if i["type"] == "mention")
    payload = (
        json.loads(mention["payload"])
        if isinstance(mention["payload"], str)
        else mention["payload"]
    )
    assert payload.get("type") == "post"
    assert payload.get("thread_slug") == t["slug"] and payload.get("post_id") == p["id"]


@pytest.mark.django_db
def test_notifications_on_profile_comment():
    client = APIClient()
    owner = User.objects.create_user(username="owner", password="x")
    commenter = User.objects.create_user(username="commenter", password="x")

    client.force_authenticate(user=commenter)
    r = client.post(
        "/api/users/owner/comments/", {"body": "Hello @owner"}, format="json"
    )
    assert r.status_code == 201

    client.force_authenticate(user=owner)
    n = client.get("/api/notifications/?unread=1").json()
    assert any(i["type"] == "profile_comment" for i in n)
    # MENTION TARGET FROM PROFILE COMMENT SHOULD INCLUDE COMMENT_ID
    mentions = [i for i in n if i["type"] == "mention"]
    if mentions:
        mp = (
            json.loads(mentions[0]["payload"])
            if isinstance(mentions[0]["payload"], str)
            else mentions[0]["payload"]
        )
        assert (
            mp.get("type") == "profile_comment"
            and mp.get("username") == "owner"
            and mp.get("comment_id")
        )
