from django.urls import path

from .moderation_api import ModerationView

urlpatterns = [
    path("<str:username>/moderation/", ModerationView.as_view(), name="moderation"),
]
