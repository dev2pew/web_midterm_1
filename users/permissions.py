from django.utils import timezone as djtz
from rest_framework.permissions import BasePermission


class NotBanned(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return True
        prof = getattr(user, "profile", None)
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            return False
        return True
