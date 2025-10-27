from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View


def user_profile_page(request, username):
    # IF TARGET USER DOESN'T EXIST, SHOW 404-LIKE PAGE

    from django.contrib.auth import get_user_model
    from django.utils import timezone as djtz

    User = get_user_model()
    target = User.objects.filter(username=username).first()
    if not target:
        return render(
            request,
            "user_not_found.html",
            {"username": username},
            status=404,
        )

    # IF TARGET USER IS BANNED, SHOW BANNED PAGE

    tprof = getattr(target, "profile", None)
    if tprof and tprof.banned_until and tprof.banned_until > djtz.now():
        # ADMINS CAN VIEW BANNED USER PAGES

        if not (
            request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        ):
            return render(
                request, "user_banned.html", {"username": username}, status=403
            )

    # SERVER-RENDER SHELL; CONTENT LOADS VIA AJAX

    return render(request, "users/profile.html", {"username": username})


@login_required
def edit_profile_page(request, username):
    # SECURITY FIX: ENSURE THE LOGGED-IN USER CAN ONLY EDIT THEIR OWN PROFILE.

    if request.user.username != username:
        # RENDER THE CUSTOM 403 PAGE WITH A SPECIFIC MESSAGE

        return render(
            request,
            "403.html",
            {"exception": "You are not allowed to edit this profile."},
            status=403,
        )
    return render(request, "users/profile_edit.html", {"username": username})


def banned_page(request):
    return render(request, "banned.html")


class RegisterView(View):
    template_name = "users/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, self.template_name)

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("home")

        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        if not username or not password or not password2:
            messages.error(request, "Please fill in all required fields.")
            return render(
                request, self.template_name, {"username": username, "email": email}
            )
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(
                request, self.template_name, {"username": username, "email": email}
            )
        try:
            validate_password(password)
        except Exception as e:
            messages.error(
                request,
                "; ".join(
                    [
                        str(x)
                        for x in (e.messages if hasattr(e, "messages") else [str(e)])
                    ]
                ),
            )
            return render(
                request, self.template_name, {"username": username, "email": email}
            )
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(
                request, self.template_name, {"username": username, "email": email}
            )
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
        return redirect("home")
