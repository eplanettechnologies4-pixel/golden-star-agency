import sys
import os

# Add core_admin folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.accounts.views import admin_chart_revenue_view, admin_chart_pie_view

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

factory = RequestFactory()
request = factory.get('/dashboard/admin/chart/trend/')
request.user = admin_user

print("--- Testing admin_chart_revenue_view ---")
try:
    response = admin_chart_revenue_view(request)
    print("STATUS CODE:", response.status_code)
    print("CONTENT TYPE:", response.get('Content-Type'))
    print("CONTENT LENGTH:", len(response.content))
except Exception as e:
    import traceback
    traceback.print_exc()

print("\n--- Testing admin_chart_pie_view ---")
try:
    response = admin_chart_pie_view(request)
    print("STATUS CODE:", response.status_code)
    print("CONTENT TYPE:", response.get('Content-Type'))
    print("CONTENT LENGTH:", len(response.content))
except Exception as e:
    import traceback
    traceback.print_exc()
