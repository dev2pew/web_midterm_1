from datetime import datetime, timezone

from django.utils import timezone as djtz
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile


def _parse_unix(v):
    try:
        return datetime.fromtimestamp(int(v), tz=timezone.utc)
    except Exception:
        return None


class ModerationView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, username):
        try:
            profile = Profile.objects.select_related("user").get(
                user__username=username
            )
        except Profile.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        actor = request.user
        target = profile.user

        # RULES:
        # - ADMINS (STAFF, NOT SUPERUSER) CANNOT MODERATE THEMSELVES OR OTHER ADMINS/SUPERUSERS
        # - SUPERUSERS CAN MODERATE ANYONE EXCEPT THEMSELVES
        if actor.is_superuser:
            if target.id == actor.id:
                return Response(
                    {"detail": "Superusers cannot moderate themselves"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            # STAFF ADMIN
            if target.id == actor.id:
                return Response(
                    {"detail": "Admins cannot moderate themselves"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if target.is_staff or target.is_superuser:
                return Response(
                    {"detail": "Admins cannot moderate other admins"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # APPLY UPDATES; ALLOW EXPLICIT CLEARING WHEN KEY IS PRESENT WITH NULL/0/EMPTY
        if "silenced_until" in request.data:
            silenced = request.data.get("silenced_until")
            if silenced in (None, "", 0, "0"):
                profile.silenced_until = None
            else:
                profile.silenced_until = _parse_unix(silenced)
        if "banned_until" in request.data:
            banned = request.data.get("banned_until")
            if banned in (None, "", 0, "0"):
                profile.banned_until = None
            else:
                profile.banned_until = _parse_unix(banned)

        profile.save(update_fields=["silenced_until", "banned_until"])
        return Response(
            {
                "username": profile.user.username,
                "silenced_until": int(profile.silenced_until.timestamp())
                if profile.silenced_until
                else None,
                "banned_until": int(profile.banned_until.timestamp())
                if profile.banned_until
                else None,
            }
        )
