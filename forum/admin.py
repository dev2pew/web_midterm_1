from django.contrib import admin

from .models import Post, Thread


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "slug", "author", "created_at")
    search_fields = ("title", "slug", "author__username")
    list_select_related = ("author",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "thread", "author", "created_at")
    search_fields = ("thread__title", "author__username", "body")
    list_select_related = ("thread", "author")
