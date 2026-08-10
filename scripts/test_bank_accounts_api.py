import requests
import re

session = requests.Session()
login_url = 'http://127.0.0.1:8000/auth/login/'

resp = session.get(login_url)
csrf_match = re.search(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\']+)["\']', resp.text)
csrf_token = csrf_match.group(1) if csrf_match else ''

login_data = {
    'username': 'dummy_agent',
    'password': 'Password@123',
    'csrfmiddlewaretoken': csrf_token
}

login_resp = session.post(login_url, data=login_data, headers={'Referer': login_url})
print(f"Login Status: {login_resp.status_code}, URL: {login_resp.url}")

bank_resp = session.get("http://127.0.0.1:8000/dashboard/agent/api/bank-accounts/")
print(f"Bank Accounts API Status: {bank_resp.status_code}")
data = bank_resp.json()
accounts = data.get('accounts', [])
print(f"Found {len(accounts)} bank accounts:")
for a in accounts:
    print(f" - {a.get('bank_name')}: {a.get('account_title')} | Acc: {a.get('account_number')} | IBAN: {a.get('iban')} | Branch: {a.get('branch_name')}")
