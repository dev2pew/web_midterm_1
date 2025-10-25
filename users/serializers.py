from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile, ProfileComment, ProfileCommentRating

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    date_joined_unix = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    silenced_until_unix = serializers.SerializerMethodField()
    banned_until_unix = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined_unix",
            "is_staff",
            "is_superuser",
            "silenced_until_unix",
            "banned_until_unix",
        ]
        read_only_fields = fields

    def get_date_joined_unix(self, obj):
        return (
            int(obj.date_joined.timestamp())
            if getattr(obj, "date_joined", None)
            else None
        )

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


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    password2 = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        validate_password(attrs["password"])  # RUN DJANGO'S VALIDATORS
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password2", None)
        user = User.objects.create_user(password=password, **validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    silenced_until_unix = serializers.SerializerMethodField()
    banned_until_unix = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "user",
            "avatar",
            "bio",
            "device",
            "silenced_until_unix",
            "banned_until_unix",
        ]
        read_only_fields = ["user", "silenced_until_unix", "banned_until_unix"]

    def get_silenced_until_unix(self, obj):
        return int(obj.silenced_until.timestamp()) if obj.silenced_until else None

    def get_banned_until_unix(self, obj):
        return int(obj.banned_until.timestamp()) if obj.banned_until else None


class ProfileCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    score = serializers.SerializerMethodField()
    my_vote = serializers.SerializerMethodField()
    last_edited_at = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    edit_count = serializers.SerializerMethodField()
    body_html = serializers.SerializerMethodField()

    class Meta:
        model = ProfileComment
        fields = [
            "id",
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
            "author",
            "created_at",
            "last_edited_at",
            "edit_count",
            "score",
            "my_vote",
            "body_html",
        ]

    def get_score(self, obj):
        return sum(
            r.value for r in getattr(obj, "_prefetched_ratings", obj.ratings.all())
        )

    def get_my_vote(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0
        v = obj.ratings.filter(user=request.user).first()
        return v.value if v else 0

    def get_edit_count(self, obj):
        return obj.edits.count()

    def get_last_edited_at(self, obj):
        return int(obj.edited_at.timestamp()) if obj.edited_at else None

    def get_created_at(self, obj):
        return int(obj.created_at.timestamp()) if obj.created_at else None

    def get_body_html(self, obj):
        from lucky_forums.utils import render_markdown_safe

        return render_markdown_safe(obj.body)
