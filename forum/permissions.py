from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Allow reads for anyone; writes only for the object's author."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "author_id", None) == getattr(request.user, "id", None)
