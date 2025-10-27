"""
WSGI CONFIG FOR LUCKY_FORUMS PROJECT.

IT EXPOSES THE WSGI CALLABLE AS A MODULE-LEVEL VARIABLE NAMED ``APPLICATION``.

FOR MORE INFORMATION ON THIS FILE, SEE
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lucky_forums.settings")

application = get_wsgi_application()
