import urllib.request
try:
    url = "http://127.0.0.1:8000/dashboard/admin/chart/trend/"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        print("URL:", response.geturl())
        print("STATUS:", response.status)
        print("HEADERS:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
        print("CONTENT LENGTH:", len(response.read()))
except Exception as e:
    print("ERROR:", e)
