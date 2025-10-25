import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Thread(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads"
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:50] or "thread"
            # ENSURE UNIQUENESS WITH A SHORT RANDOM SUFFIX
            for _ in range(5):
                candidate = f"{base}-{uuid.uuid4().hex[:8]}"
                if not Thread.objects.filter(slug=candidate).exists():
                    self.slug = candidate
                    break
            else:
                self.slug = f"thread-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)


class Post(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"post by {self.author} on {self.thread}"


class PostEdit(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="edits")
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    body = models.TextField()
    edited_at = models.DateTimeField(default=timezone.now)


class PostRating(models.Model):
    VALUE_CHOICES = ((-1, "down"), (1, "up"))
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("post", "user")
