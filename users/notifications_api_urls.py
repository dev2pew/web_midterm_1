from django.urls import path

from .notifications_api import NotificationListView, NotificationReadView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications_list"),
    path("<int:pk>/read/", NotificationReadView.as_view(), name="notifications_read"),
]
