import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_superuser_has_profile():
    admin = User.objects.create_superuser(
        username="admin2", email="admin2@example.com", password="AdminPass123!"
    )
    assert hasattr(admin, "profile")
