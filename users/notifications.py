import json
import re
from typing import Dict, Iterable

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Profile

User = get_user_model()

MENTION_RE = re.compile(r"@([A-Za-z0-9_]{1,30})")


def _create_notification(user_id: int, type_: str, payload: Dict):
    from .models import Notification

    Notification.objects.create(
        user_id=user_id, type=type_, payload=json.dumps(payload)
    )


def notify_thread_reply(actor, thread, post):
    if thread.author_id and thread.author_id != actor.id:
        _create_notification(
            user_id=thread.author_id,
            type_="thread_reply",
            payload={
                "thread_slug": thread.slug,
                "post_id": post.id,
                "actor": actor.username,
            },
        )


def notify_profile_comment(actor, profile: Profile, comment):
    if profile.user_id and profile.user_id != actor.id:
        _create_notification(
            user_id=profile.user_id,
            type_="profile_comment",
            payload={
                "username": profile.user.username,
                "comment_id": comment.id,
                "actor": actor.username,
            },
        )


def notify_mentions(actor, text: str, context: Dict):
    usernames = set(MENTION_RE.findall(text or ""))
    if not usernames:
        return
    found = User.objects.filter(username__in=list(usernames)).values_list(
        "id", "username"
    )
    for uid, uname in found:
        if uid == actor.id:
            continue
        payload = {"actor": actor.username, "mention": uname}
        payload.update(context)
        _create_notification(user_id=uid, type_="mention", payload=payload)
