from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        unread = request.query_params.get("unread")
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")
        if unread in ("1", "true", "True"):
            qs = qs.filter(read_at__isnull=True)
        data = [
            {
                "id": n.id,
                "type": n.type,
                "payload": n.payload,
                "created_at": int(n.created_at.timestamp()),
                "read_at": int(n.read_at.timestamp()) if n.read_at else None,
            }
            for n in qs[:50]
        ]
        return Response(data)


class NotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            n = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if not n.read_at:
            n.read_at = timezone.now()
            n.save(update_fields=["read_at"])
        return Response({"ok": True})
