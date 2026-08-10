import sys
import os

# Add core_admin to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from apps.accounts.models import User
from apps.accounts.views import agent_export_report_api

def test_exports():
    rf = RequestFactory()
    agent = User.objects.filter(role='agent', approval_status='approved').first()
    if not agent:
        print("No agent found!")
        return

    print(f"Testing exports for Agent: {agent.username} ({agent.company_name})")
    report_types = ['ledger', 'ticket-orders', 'bookings', 'visas', 'flights', 'comprehensive']
    formats = ['pdf', 'word', 'excel', 'csv']
    
    all_passed = True
    for r_type in report_types:
        for fmt in formats:
            url = f"/dashboard/agent/api/reports/export/{r_type}/{fmt}/?start_date=2026-01-01&end_date=2026-12-31"
            req = rf.get(url)
            req.user = agent
            response = agent_export_report_api(req, r_type, fmt)
            ct = response.headers.get('Content-Type', '')
            status = response.status_code
            passed = (status == 200)
            if not passed:
                all_passed = False
            print(f"[{'PASS' if passed else 'FAIL'}] {r_type.ljust(15)} | {fmt.ljust(6)} | Status: {status} | CT: {ct[:30]}")

    if all_passed:
        print("\nAll 24 Agent Report Export combinations PASSED successfully!")
    else:
        print("\nSome tests failed.")

if __name__ == '__main__':
    test_exports()
