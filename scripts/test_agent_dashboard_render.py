import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
agent = User.objects.get(username='Danish')

client = Client()
client.force_login(agent)

print("--- Requesting /dashboard/agent/ ---")
response = client.get('/dashboard/agent/', HTTP_HOST='localhost')
print("Status code:", response.status_code)

if response.status_code != 200:
    print("Page error response content:")
    print(response.content[:1000].decode('utf-8'))
else:
    print("SUCCESS: Django template rendered correctly without internal server errors.")
