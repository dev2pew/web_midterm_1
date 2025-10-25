from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Thread


def home(request):
    try:
        from django.utils import timezone as djtz

        prof = request.user.profile if request.user.is_authenticated else None
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            return render(request, "banned.html", status=403)
    except Exception:
        pass
    return render(request, "forum/thread_list.html")


def thread_detail_page(request, slug):
    try:
        from django.utils import timezone as djtz

        prof = request.user.profile if request.user.is_authenticated else None
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            return render(request, "banned.html", status=403)
    except Exception:
        pass
    return render(request, "forum/thread_detail.html", {"slug": slug})


@login_required
def thread_edit_page(request, slug):
    thread = get_object_or_404(Thread, slug=slug)
    # Security Fix: Ensure only the author or staff can access the edit page.
    if not (request.user.is_staff or request.user.id == thread.author_id):
        # Render the custom 403 page with a specific message
        return render(
            request,
            "403.html",
            {"exception": "You are not allowed to edit this thread."},
            status=403,
        )

    try:
        from django.utils import timezone as djtz

        prof = request.user.profile if request.user.is_authenticated else None
        if prof and prof.banned_until and prof.banned_until > djtz.now():
            return render(request, "banned.html", status=403)
    except Exception:
        pass
    return render(request, "forum/thread_edit.html", {"slug": slug})


def about_page(request):
    return render(request, "forum/about.html")
