from django.urls import path

from .profile_views import (
    MyProfileView,
    ProfileCommentDetailView,
    ProfileCommentHistoryView,
    ProfileCommentRateView,
    ProfileCommentsView,
    UserProfileDetailView,
)

urlpatterns = [
    path("me/profile/", MyProfileView.as_view(), name="my_profile"),
    path(
        "<str:username>/profile/", UserProfileDetailView.as_view(), name="user_profile"
    ),
    path(
        "<str:username>/comments/",
        ProfileCommentsView.as_view(),
        name="profile_comments",
    ),
    path(
        "<str:username>/comments/<int:pk>/",
        ProfileCommentDetailView.as_view(),
        name="profile_comment_detail",
    ),
    path(
        "<str:username>/comments/<int:pk>/rate/",
        ProfileCommentRateView.as_view(),
        name="profile_comment_rate",
    ),
    path(
        "<str:username>/comments/<int:pk>/history/",
        ProfileCommentHistoryView.as_view(),
        name="profile_comment_history",
    ),
]
