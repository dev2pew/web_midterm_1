from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile, ProfileComment, ProfileCommentRating
from .serializers import ProfileCommentSerializer, ProfileSerializer, UserSerializer

User = get_user_model()


class MyProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile = request.user.profile
        return Response(ProfileSerializer(profile, context={"request": request}).data)

    def patch(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(
            profile, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserProfileDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        return Response(
            ProfileSerializer(user.profile, context={"request": request}).data
        )


class ProfileCommentsView(APIView):
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        comments = user.profile.comments.select_related("author").all()
        return Response(
            ProfileCommentSerializer(
                comments, many=True, context={"request": request}
            ).data
        )

    def post(self, request, username):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # MODERATION

        from django.utils import timezone as djtz

        from .models import Profile

        prof = Profile.objects.filter(user_id=request.user.id).first()
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            return Response({"detail": "Banned user"}, status=status.HTTP_403_FORBIDDEN)
        if prof and prof.silenced_until and prof.silenced_until > djtz.now():
            return Response(
                {"detail": "Silenced user"}, status=status.HTTP_403_FORBIDDEN
            )
        user = get_object_or_404(User, username=username)
        serializer = ProfileCommentSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        comment = ProfileComment.objects.create(
            profile=user.profile,
            author=request.user,
            body=serializer.validated_data["body"],
        )

        # NOTIFICATIONS

        try:
            from .notifications import notify_mentions, notify_profile_comment

            notify_profile_comment(request.user, user.profile, comment)
            notify_mentions(
                actor=request.user,
                text=comment.body,
                context={
                    "type": "profile_comment",
                    "username": user.username,
                    "comment_id": comment.id,
                },
            )
        except Exception:
            pass
        return Response(
            ProfileCommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ProfileCommentDetailView(APIView):
    def delete(self, request, username, pk):
        user = get_object_or_404(User, username=username)
        comment = get_object_or_404(ProfileComment, pk=pk, profile=user.profile)
        if request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or comment.author_id == request.user.id
            or user.id == request.user.id
        ):
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Not permitted"}, status=status.HTTP_403_FORBIDDEN)

    def patch(self, request, username, pk):
        user = get_object_or_404(User, username=username)
        comment = get_object_or_404(ProfileComment, pk=pk, profile=user.profile)

        # MODERATION

        from django.utils import timezone as djtz

        from .models import Profile

        prof = Profile.objects.filter(user_id=request.user.id).first()
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            return Response({"detail": "Banned user"}, status=status.HTTP_403_FORBIDDEN)
        if prof and prof.silenced_until and prof.silenced_until > djtz.now():
            return Response(
                {"detail": "Silenced user"}, status=status.HTTP_403_FORBIDDEN
            )
        if not (
            request.user.is_authenticated
            and (
                request.user.is_staff
                or request.user.is_superuser
                or comment.author_id == request.user.id
            )
        ):
            return Response(
                {"detail": "Not permitted"}, status=status.HTTP_403_FORBIDDEN
            )
        from .models import ProfileCommentEdit

        ProfileCommentEdit.objects.create(
            comment=comment, editor=request.user, body=comment.body
        )
        comment.body = request.data.get("body", comment.body)
        from django.utils import timezone as djtz

        comment.edited_at = djtz.now()
        comment.save(update_fields=["body", "edited_at"])
        return Response(
            ProfileCommentSerializer(comment, context={"request": request}).data
        )


class ProfileCommentHistoryView(APIView):
    def get(self, request, username, pk):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail": "Admins only"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, username=username)
        comment = get_object_or_404(ProfileComment, pk=pk, profile=user.profile)
        data = [
            {
                "body": e.body,
                "edited_at": int(e.edited_at.timestamp()),
                "editor_id": e.editor_id,
            }
            for e in comment.edits.order_by("-edited_at")
        ]
        return Response(data)


class ProfileCommentRateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username, pk):
        user = get_object_or_404(User, username=username)
        comment = get_object_or_404(ProfileComment, pk=pk, profile=user.profile)
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
        ProfileCommentRating.objects.update_or_create(
            comment=comment, user=request.user, defaults={"value": val}
        )
        score = comment.ratings.aggregate(score=Sum("value")).get("score") or 0
        return Response({"score": score, "my_vote": val})

    def delete(self, request, username, pk):
        user = get_object_or_404(User, username=username)
        comment = get_object_or_404(ProfileComment, pk=pk, profile=user.profile)
        ProfileCommentRating.objects.filter(comment=comment, user=request.user).delete()
        score = comment.ratings.aggregate(score=Sum("value")).get("score") or 0
        return Response({"score": score, "my_vote": 0})
