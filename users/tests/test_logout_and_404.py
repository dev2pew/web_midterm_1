import pytest
from django.test.utils import override_settings


@pytest.mark.django_db
def test_logout_page(client):
    # Logout should be a POST request
    r = client.post("/auth/logout/")
    # After logout, it should redirect to the logged_out.html template
    assert r.status_code == 200  # The final page is 200 OK
    assert b"you have been logged out" in r.content
    # META REFRESH OR JS PRESENT
    assert b"refresh" in r.content or b"setTimeout" in r.content


@pytest.mark.django_db
@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
def test_custom_404(client):
    r = client.get("/this-route-does-not-exist/")
    assert r.status_code == 404
    assert b"page not found" in r.content or b"404" in r.content
