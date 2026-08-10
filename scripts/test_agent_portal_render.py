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
from apps.accounts.views import agent_dashboard_view

User = get_user_model()
agent_user = User.objects.filter(role='agent', username='dummy_agent').first()
if not agent_user:
    agent_user = User.objects.filter(role='agent').first()

print(f"Testing Agent Overview View with User: {agent_user.username}")
factory = RequestFactory()
request = factory.get('/dashboard/agent/')
request.user = agent_user

response = agent_dashboard_view(request)
print(f"Agent Overview Status Code: {response.status_code}")
content = response.content.decode('utf-8')
print(f"Response size: {len(content)} characters")

# Check essential elements
checks = [
    ('tab-btn-reports', 'Sidebar Reports Tab Button'),
    ('tab-content-reports', 'Reports Hub Content Pane'),
    ('report-preview-section', 'Live Report Preview Section'),
    ('triggerReportExport', 'Report Export Trigger Function'),
    ('setReportDatePreset', 'Date Preset Selector Function'),
    ('ledger', 'Ledger Report Type Export'),
    ('ticket-orders', 'Ticket Orders Export'),
    ('bookings', 'Bookings Export'),
    ('visas', 'Visas Export'),
    ('comprehensive', 'Master Audit Export')
]

all_passed = True
for string_match, label in checks:
    if string_match in content:
        print(f" [PASS] {label}")
    else:
        print(f" [FAIL] Missing {label} ({string_match})")
        all_passed = False

if all_passed:
    print("\nSUCCESS: All Agent Portal Reports & Export components successfully verified!")
else:
    print("\nWARNING: Some checks failed.")
