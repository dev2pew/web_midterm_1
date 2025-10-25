from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Post, PostRating, Thread


class UserInlineSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    date_joined_unix = serializers.SerializerMethodField()
    silenced_until_unix = serializers.SerializerMethodField()
    banned_until_unix = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
            "avatar",
            "is_staff",
            "is_superuser",
            "date_joined_unix",
            "silenced_until_unix",
            "banned_until_unix",
        ]
        read_only_fields = fields

    def get_avatar(self, obj):
        prof = getattr(obj, "profile", None)
        if prof and prof.avatar:
            try:
                return prof.avatar.url
            except Exception:
                return ""
        return ""

    def get_date_joined_unix(self, obj):
        if getattr(obj, "date_joined", None):
            return int(obj.date_joined.timestamp())
        return None

    def get_silenced_until_unix(self, obj):
        prof = getattr(obj, "profile", None)
        return (
            int(prof.silenced_until.timestamp())
            if prof and prof.silenced_until
            else None
        )

    def get_banned_until_unix(self, obj):
        prof = getattr(obj, "profile", None)
        return (
            int(prof.banned_until.timestamp()) if prof and prof.banned_until else None
        )


class ThreadSerializer(serializers.ModelSerializer):
    author = UserInlineSerializer(read_only=True)
    posts_count = serializers.IntegerField(source="posts.count", read_only=True)
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = [
            "id",
            "title",
            "slug",
            "author",
            "created_at",
            "updated_at",
            "posts_count",
        ]
        read_only_fields = [
            "id",
            "slug",
            "author",
            "created_at",
            "updated_at",
            "posts_count",
        ]

    def get_created_at(self, obj):
        return int(obj.created_at.timestamp())

    def get_updated_at(self, obj):
        return int(obj.updated_at.timestamp()) if obj.updated_at else None


class PostSerializer(serializers.ModelSerializer):
    author = UserInlineSerializer(read_only=True)
    thread = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    score = serializers.SerializerMethodField()
    my_vote = serializers.SerializerMethodField()
    last_edited_at = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    edit_count = serializers.SerializerMethodField()
    body_html = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "thread",
            "author",
            "body",
            "body_html",
            "created_at",
            "last_edited_at",
            "edit_count",
            "score",
            "my_vote",
        ]
        read_only_fields = [
            "id",
            "thread",
            "author",
            "created_at",
            "last_edited_at",
            "edit_count",
            "score",
            "my_vote",
            "body_html",
        ]

    def get_score(self, obj):
        # SUM OF VALUES; KEEP SIMPLE
        return sum(
            r.value for r in getattr(obj, "_prefetched_ratings", obj.ratings.all())
        )

    def get_my_vote(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0
        vote = obj.ratings.filter(user=request.user).first()
        return vote.value if vote else 0

    def get_edit_count(self, obj):
        return obj.edits.count()

    def get_last_edited_at(self, obj):
        return int(obj.edited_at.timestamp()) if obj.edited_at else None

    def get_created_at(self, obj):
        return int(obj.created_at.timestamp()) if obj.created_at else None

    def get_body_html(self, obj):
        from lucky_forums.utils import render_markdown_safe

        return render_markdown_safe(obj.body)
