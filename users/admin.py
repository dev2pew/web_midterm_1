from django.contrib import admin

from .models import Profile, ProfileComment


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "device")
    search_fields = ("user__username", "device")
    list_select_related = ("user",)


@admin.register(ProfileComment)
class ProfileCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "author", "created_at")
    search_fields = ("profile__user__username", "author__username", "body")
    list_select_related = ("profile", "author")
