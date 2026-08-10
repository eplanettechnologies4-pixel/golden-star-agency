import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_ADMIN_DIR = os.path.join(BASE_DIR, 'core_admin')
sys.path.insert(0, CORE_ADMIN_DIR)
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
import json
from apps.airline_ticketing.views import agent_my_orders_api, agent_my_activity_api
from apps.accounts.views import agent_dashboard_overview_api

User = get_user_model()
agent_user = User.objects.filter(role='agent', username='dummy_agent').first()

factory = RequestFactory()

# 1. Test my-activity
req = factory.get('/dashboard/agent/api/my-activity/')
req.user = agent_user
res = agent_my_activity_api(req)
print(f"my-activity Status: {res.status_code}")
act_data = json.loads(res.content.decode('utf-8'))
print(f"my-activity keys: {list(act_data.keys())}, entries count: {len(act_data.get('ledger_entries', []))}")

# 2. Test my-orders
req = factory.get('/dashboard/agent/api/my-orders/')
req.user = agent_user
res = agent_my_orders_api(req)
print(f"my-orders Status: {res.status_code}")
ord_data = json.loads(res.content.decode('utf-8'))
print(f"my-orders keys: {list(ord_data.keys())}, orders count: {len(ord_data.get('orders', []))}")

# 3. Test overview-stats
req = factory.get('/dashboard/agent/api/overview-stats/')
req.user = agent_user
res = agent_dashboard_overview_api(req)
print(f"overview-stats Status: {res.status_code}")
stats_data = json.loads(res.content.decode('utf-8'))
print(f"overview-stats keys: {list(stats_data.keys())}")
print("SUCCESS: All 3 preview APIs returned JSON successfully!")
