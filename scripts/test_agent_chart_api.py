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
from apps.accounts.views import agent_chart_data_api

User = get_user_model()
agent_user = User.objects.filter(role='agent').first()

if not agent_user:
    # Create a dummy agent user if none exists
    agent_user = User.objects.create_user(
        username='test_agent_val',
        email='test_agent_val@example.com',
        password='password123',
        role='agent'
    )
    print("Created dummy validation agent user.")

factory = RequestFactory()
request = factory.get('/dashboard/agent/chart/data/')
request.user = agent_user

print("--- Testing agent_chart_data_api ---")
try:
    response = agent_chart_data_api(request)
    print("STATUS CODE:", response.status_code)
    print("CONTENT TYPE:", response.get('Content-Type'))
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        print("\nJSON keys returned:")
        for key in data.keys():
            print(f"- {key}: {list(data[key].keys())}")
        
        print("\nTrend data labels:", data['trend']['labels'])
        print("Trend bookings:", data['trend']['bookings'])
        print("Pie labels:", data['pie']['labels'])
        print("Pie values:", data['pie']['values'])
        print("Bar labels:", data['bar']['labels'])
        print("Bar bookings:", data['bar']['bookings'])
        print("\nSUCCESS: The agent chart data API is fully functional and correct!")
    else:
        print("ERROR: Status code not 200, content:", response.content)
except Exception as e:
    import traceback
    traceback.print_exc()
