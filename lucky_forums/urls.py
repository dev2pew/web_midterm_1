from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.shortcuts import render
from django.urls import include, path

from forum.pages import about_page, home, thread_detail_page, thread_edit_page
from users.pages import RegisterView, banned_page, edit_profile_page, user_profile_page


# Define a custom 403 handler view
def permission_denied_view(request, exception=None):
    return render(request, "403.html", {"exception": exception}, status=403)


urlpatterns = [
    # PAGES
    path("", home, name="home"),
    path("about/", about_page, name="about"),
    path("t/<slug:slug>/", thread_detail_page, name="thread_detail"),
    path("t/<slug:slug>/edit/", thread_edit_page, name="thread_edit"),
    path("u/<str:username>/", user_profile_page, name="user_profile_page"),
    path("u/<str:username>/edit/", edit_profile_page, name="edit_profile_page"),
    path("banned/", banned_page, name="banned"),
    # AUTH PAGES
    path(
        "auth/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "auth/logout/",
        auth_views.LogoutView.as_view(template_name="registration/logged_out.html"),
        name="logout",
    ),
    path("auth/register/", RegisterView.as_view(), name="register"),
    # APIS
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.api_urls")),
    path("api/users/", include("users.profile_api_urls")),
    path("api/users/", include("users.moderation_api_urls")),
    path("api/notifications/", include("users.notifications_api_urls")),
    path("api/", include("forum.api_urls")),
]

# Set the custom 403 handler
handler403 = permission_denied_view

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
