"""
ASGI CONFIG FOR LUCKY_FORUMS PROJECT.

IT EXPOSES THE ASGI CALLABLE AS A MODULE-LEVEL VARIABLE NAMED ``APPLICATION``.

FOR MORE INFORMATION ON THIS FILE, SEE

https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lucky_forums.settings")

application = get_asgi_application()
