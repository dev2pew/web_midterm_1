import pytest
from django.test.utils import override_settings


@pytest.mark.django_db
def test_logout_page(client):
    # LOGOUT SHOULD BE A POST REQUEST

    r = client.post("/auth/logout/")
    # AFTER LOGOUT, IT SHOULD REDIRECT TO THE LOGGED_OUT.HTML TEMPLATE

    # THE FINAL PAGE IS 200 OK
    assert r.status_code == 200

    assert b"you have been logged out" in r.content

    # META REFRESH OR JS PRESENT
    assert b"refresh" in r.content or b"setTimeout" in r.content


@pytest.mark.django_db
@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
def test_custom_404(client):
    r = client.get("/this-route-does-not-exist/")
    assert r.status_code == 404
    assert b"page not found" in r.content or b"404" in r.content
