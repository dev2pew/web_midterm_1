from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone


class BanBlockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""
        if (request.user.is_authenticated) and hasattr(request.user, "profile"):
            prof = request.user.profile
            if prof.banned_until and prof.banned_until > timezone.now():
                # ALLOW SOME PATHS

                allowed = (
                    path.startswith("/static/")
                    or path.startswith("/media/")
                    or path.startswith("/auth/")
                    or path == "/banned/"
                )
                if not allowed:
                    if path.startswith("/api/"):
                        return JsonResponse({"detail": "Banned user"}, status=403)
                    return render(request, "banned.html", status=403)
        return self.get_response(request)
