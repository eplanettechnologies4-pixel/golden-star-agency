"""
WSGI config for core_admin project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

# Ensure core_admin directory and apps are in sys.path dynamically
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
REPO_ROOT = os.path.dirname(BASE_DIR)
APPS_DIR = os.path.join(BASE_DIR, 'apps')

for p in [BASE_DIR, APPS_DIR, REPO_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Apply Python 3.14 compatibility patch
from config.patch_django import patch_django_context
patch_django_context()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
