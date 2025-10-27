import bleach
import markdown as md

ALLOWED_TAGS = [
    "p",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "a",
    "code",
    "pre",
    "blockquote",
    "br",
    "hr",
    "h1",
    "h2",
    "h3",
]
ALLOWED_ATTRS = {"a": ["href", "title", "rel", "target"]}


def render_markdown_safe(text: str) -> str:
    if not text:
        return ""
    html = md.markdown(text, extensions=["extra", "sane_lists", "smarty"])

    # GENERATE HTML

    cleaned = bleach.clean(
        html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True
    )

    # LINKIFY @MENTIONS TO PROFILE PAGES (SIMPLE REGEX)

    import re

    def repl(m):
        uname = m.group(1)
        return f'<a href="/u/{uname}/" class="text-decoration-none">@{uname}</a>'

    cleaned = re.sub(r"@([A-Za-z0-9_]{1,30})", repl, cleaned)
    return cleaned
