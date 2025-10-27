from django.db.models import Sum
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Post, PostRating, Thread
from .permissions import IsAuthorOrReadOnly
from .serializers import PostSerializer, ThreadSerializer


class ThreadViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Thread.objects.select_related("author").all()
    serializer_class = ThreadSerializer
    lookup_field = "slug"

    def get_permissions(self):
        from users.permissions import NotBanned

        if self.action in ["list", "retrieve"]:
            return [NotBanned()]
        # CREATE/DELETE REQUIRE AUTH; OBJECT-LEVEL DELETE CHECKED BELOW

        return [IsAuthenticated(), NotBanned()]

    def list(self, request, *args, **kwargs):
        # BLOCK BANNED USERS FROM VIEWING

        if request.user.is_authenticated:
            from django.utils import timezone as djtz

            prof = getattr(request.user, "profile", None)
            if prof and prof.banned_until and prof.banned_until > djtz.now():
                return Response(
                    {"detail": "banned user"}, status=status.HTTP_403_FORBIDDEN
                )
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            from django.utils import timezone as djtz

            prof = getattr(request.user, "profile", None)
            if prof and prof.banned_until and prof.banned_until > djtz.now():
                return Response(
                    {"detail": "banned user"}, status=status.HTTP_403_FORBIDDEN
                )
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        # MODERATION: PREVENT BANNED/SILENCED USERS FROM CREATING THREADS

        from django.utils import timezone as djtz

        from users.models import Profile

        prof = Profile.objects.filter(user_id=self.request.user.id).first()
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("banned user")
        if prof and prof.silenced_until and prof.silenced_until > djtz.now():
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("silenced user")
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        user = self.request.user
        if user.is_staff or user.is_superuser or instance.author_id == user.id:
            instance.delete()
        else:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("not allowed to delete this thread.")

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        if not (user.is_staff or user.is_superuser or instance.author_id == user.id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("not allowed to edit this thread.")
        serializer.save()


class PostViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PostSerializer

    def get_queryset(self):
        return (
            Post.objects.select_related("author", "thread")
            .filter(thread__slug=self.kwargs.get("thread_slug"))
            .all()
        )

    def get_permissions(self):
        from users.permissions import NotBanned

        if self.action in ["list", "retrieve"]:
            return [NotBanned()]
        return [IsAuthenticated(), NotBanned()]

    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            from django.utils import timezone as djtz

            prof = getattr(request.user, "profile", None)
            if prof and prof.banned_until and prof.banned_until > djtz.now():
                return Response(
                    {"detail": "banned user"}, status=status.HTTP_403_FORBIDDEN
                )
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        # MODERATION: PREVENT BANNED/SILENCED USERS FROM POSTING

        from django.utils import timezone as djtz

        from users.models import Profile

        prof = Profile.objects.filter(user_id=self.request.user.id).first()
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("banned user")
        if prof and prof.silenced_until and prof.silenced_until > djtz.now():
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("silenced user")
        thread = Thread.objects.get(slug=self.kwargs.get("thread_slug"))
        obj = serializer.save(author=self.request.user, thread=thread)
        # NOTIFICATIONS: THREAD OWNER AND MENTIONS

        try:
            from users.notifications import notify_mentions, notify_thread_reply

            notify_thread_reply(actor=self.request.user, thread=thread, post=obj)
            notify_mentions(
                actor=self.request.user,
                text=obj.body,
                context={"type": "post", "thread_slug": thread.slug, "post_id": obj.id},
            )
        except Exception:
            pass

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from django.utils import timezone as djtz

        from users.models import Profile

        prof = Profile.objects.filter(user_id=request.user.id).first()
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            return Response({"detail": "banned user"}, status=status.HTTP_403_FORBIDDEN)
        if prof and prof.silenced_until and prof.silenced_until > djtz.now():
            return Response(
                {"detail": "silenced user"}, status=status.HTTP_403_FORBIDDEN
            )
        thread = Thread.objects.get(slug=self.kwargs.get("thread_slug"))
        obj = serializer.save(author=request.user, thread=thread)
        try:
            from users.notifications import notify_mentions, notify_thread_reply

            notify_thread_reply(actor=request.user, thread=thread, post=obj)
            notify_mentions(
                actor=request.user,
                text=obj.body,
                context={"type": "post", "thread_slug": thread.slug, "post_id": obj.id},
            )
        except Exception:
            pass
        data = self.get_serializer(obj).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_destroy(self, instance):
        user = self.request.user
        if user.is_staff or user.is_superuser or instance.author_id == user.id:
            instance.delete()
        else:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("not allowed to delete this post.")

    def perform_update(self, serializer):
        # MODERATION: PREVENT SILENCED/BANNED USERS FROM EDITING

        from django.utils import timezone as djtz

        from users.models import Profile

        prof = Profile.objects.filter(user_id=self.request.user.id).first()
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("banned user")
        if prof and prof.silenced_until and prof.silenced_until > djtz.now():
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("silenced user")
        user = self.request.user
        instance = self.get_object()
        if not (user.is_staff or user.is_superuser or instance.author_id == user.id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("not allowed to edit this post.")
        from .models import PostEdit

        PostEdit.objects.create(post=instance, editor=user, body=instance.body)
        obj = serializer.save()
        obj.edited_at = timezone.now()
        obj.save(update_fields=["edited_at"])

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, thread_slug=None, pk=None):
        if not (request.user.is_staff or request.user.is_superuser):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Admins only")
        post = self.get_object()
        data = [
            {
                "body": e.body,
                "edited_at": int(e.edited_at.timestamp()),
                "editor_id": e.editor_id,
            }
            for e in post.edits.order_by("-edited_at")
        ]
        return Response(data)

    @action(detail=True, methods=["post", "delete"], url_path="rate")
    def rate(self, request, thread_slug=None, pk=None):
        post = self.get_object()
        user = request.user
        if request.method.lower() == "delete":
            PostRating.objects.filter(post=post, user=user).delete()
            score = post.ratings.aggregate(score=Sum("value")).get("score") or 0
            return Response({"score": score, "my_vote": 0}, status=status.HTTP_200_OK)
        try:
            val = int(request.data.get("value", 0))
        except (TypeError, ValueError):
            return Response(
                {"detail": "value must be 1 or -1"}, status=status.HTTP_400_BAD_REQUEST
            )
        if val not in (-1, 1):
            return Response(
                {"detail": "value must be 1 or -1"}, status=status.HTTP_400_BAD_REQUEST
            )
        PostRating.objects.update_or_create(
            post=post, user=user, defaults={"value": val}
        )
        score = post.ratings.aggregate(score=Sum("value")).get("score") or 0
        return Response({"score": score, "my_vote": val})
