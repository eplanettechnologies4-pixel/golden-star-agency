import requests

session = requests.Session()
login_url = 'http://127.0.0.1:8000/auth/login/'
res = session.get(login_url)

# Get CSRF token
csrf = session.cookies.get('csrftoken') or ''
headers = {'Referer': login_url}
post_data = {
    'username': 'dummy_agent',
    'password': 'Password@123',
    'csrfmiddlewaretoken': csrf
}

res_login = session.post(login_url, data=post_data, headers=headers, allow_redirects=True)
print(f"Login Status: {res_login.status_code}, Final URL: {res_login.url}")

res_agent = session.get('http://127.0.0.1:8000/dashboard/agent/?tab=reports')
print(f"Agent Dashboard Status: {res_agent.status_code}")
content = res_agent.text

checks = [
    'tab-btn-reports',
    'tab-content-reports',
    'report-preview-section',
    'Wallet Ledger Statement',
    'Airline Ticket Orders Report',
    'Package Bookings Report',
    'Visa Applications Report',
    'Flight Quotations Report',
    'Comprehensive Business Audit'
]

for c in checks:
    print(f"[{'PASS' if c in content else 'FAIL'}] {c}")
