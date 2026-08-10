import requests

session = requests.Session()
login_url = 'http://127.0.0.1:8000/auth/login/'
res = session.get(login_url)
csrf = session.cookies.get('csrftoken') or ''
post_data = {
    'username': 'dummy_agent',
    'password': 'Password@123',
    'csrfmiddlewaretoken': csrf
}
session.post(login_url, data=post_data, headers={'Referer': login_url}, allow_redirects=True)

report_types = ['ledger', 'ticket-orders', 'bookings', 'visas', 'flights', 'comprehensive']
formats = ['pdf', 'word', 'excel', 'csv']

all_passed = True
for r in report_types:
    for f in formats:
        url = f'http://127.0.0.1:8000/dashboard/agent/api/reports/export/{r}/{f}/'
        resp = session.get(url)
        if resp.status_code == 200 and len(resp.content) > 50:
            print(f"[PASS] {r:15} | {f:6} | Status: 200 | Size: {len(resp.content)} bytes")
        else:
            print(f"[FAIL] {r:15} | {f:6} | Status: {resp.status_code}")
            all_passed = False

if all_passed:
    print("\nALL LIVE REPORT EXPORT ENDPOINTS WORKING 100%!")
