import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from forum.models import Thread

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestFrontendAPIData:
    def test_thread_list_api_provides_badge_data(self, api_client):
        """
        Verify that the thread list endpoint includes necessary author data
        for frontend badge rendering.
        """

        user = baker.make(User, is_staff=False)
        baker.make(Thread, author=user, title="A regular thread")

        response = api_client.get("/api/threads/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        author_data = data[0]["author"]

        assert "username" in author_data
        assert "is_staff" in author_data
        assert "date_joined_unix" in author_data
        assert "silenced_until_unix" in author_data
        assert "banned_until_unix" in author_data

    def test_post_list_api_provides_badge_and_markdown_data(self, api_client):
        """
        Verify that the post list endpoint includes author badge data and
        rendered markdown in `body_html`.
        """
        user = baker.make(User)
        thread = baker.make(Thread)
        baker.make(
            "forum.Post",
            thread=thread,
            author=user,
            body="**bold text** and a <script>bad</script> tag",
        )

        response = api_client.get(f"/api/threads/{thread.slug}/posts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        post = data[0]

        # Check author data for badges
        author_data = post["author"]
        assert "is_staff" in author_data
        assert "date_joined_unix" in author_data

        # Check markdown rendering
        assert "body_html" in post
        assert "<strong>bold text</strong>" in post["body_html"]
        assert "<script>" not in post["body_html"]

    def test_profile_comment_list_provides_badge_and_markdown_data(self, api_client):
        """
        Verify that the profile comment list endpoint includes author badge
        data and rendered markdown.
        """
        profile_owner = baker.make(User)
        commenter = baker.make(User)
        baker.make(
            "users.ProfileComment",
            profile=profile_owner.profile,
            author=commenter,
            body="*italic* and @mention",
        )

        response = api_client.get(f"/api/users/{profile_owner.username}/comments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        comment = data[0]

        # Check author data for badges
        author_data = comment["author"]
        assert "is_staff" in author_data
        assert "date_joined_unix" in author_data

        # Check markdown rendering
        assert "body_html" in comment
        assert "<em>italic</em>" in comment["body_html"]
        assert "@mention" in comment["body_html"]
