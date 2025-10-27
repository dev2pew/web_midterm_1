from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)
    device = models.CharField(max_length=120, blank=True)

    # MODERATION

    silenced_until = models.DateTimeField(null=True, blank=True)
    banned_until = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"profile({self.user.username})"


class ProfileComment(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile_comments",
    )
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]


class ProfileCommentEdit(models.Model):
    comment = models.ForeignKey(
        "ProfileComment", on_delete=models.CASCADE, related_name="edits"
    )
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    body = models.TextField()
    edited_at = models.DateTimeField(default=timezone.now)


class ProfileCommentRating(models.Model):
    VALUE_CHOICES = ((-1, "down"), (1, "up"))
    comment = models.ForeignKey(
        ProfileComment, on_delete=models.CASCADE, related_name="ratings"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("comment", "user")


class Notification(models.Model):
    TYPE_CHOICES = (
        ("thread_reply", "thread reply"),
        ("profile_comment", "profile comment"),
        ("mention", "mention"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)

    # JSON STRING TO KEEP SIMPLE

    payload = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
