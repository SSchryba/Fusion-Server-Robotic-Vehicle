import requests
import http.client
import json

def check_api(endpoint, method='GET', data=None):
    url = f'http://localhost:8000{endpoint}'
    try:
        if method == 'GET':
            r = requests.get(url, timeout=5)
        elif method == 'POST':
            r = requests.post(url, json=data or {}, timeout=5)
        else:
            print(f'Unsupported method: {method}')
            return False
        print(f'[API] {endpoint} ({method}):', r.status_code, r.reason)
        if r.status_code >= 400:
            print('  Response:', r.text)
        return r.ok
    except Exception as e:
        print(f'[API] {endpoint} ({method}): ERROR - {e}')
        return False

def check_ui(path):
    try:
        conn = http.client.HTTPConnection('localhost', 5000, timeout=5)
        conn.request('GET', path)
        resp = conn.getresponse()
        print(f'[UI] {path}:', resp.status, resp.reason)
        return resp.status == 200
    except Exception as e:
        print(f'[UI] {path}: ERROR - {e}')
        return False

def main():
    print('--- Backend API Health Check ---')
    check_api('/fusion/respond', 'POST', {'prompt': 'healthcheck'})
    check_api('/fusion/status')
    check_api('/fusion/feedback', 'POST', {'model': 'test', 'feedback': 'ok'})
    check_api('/fusion/insight-data')
    check_api('/tools/list')
    check_api('/tools/fetch', 'POST', {'keyword_or_url': 'ocr', 'used_for': 'test'})
    check_api('/insight-dashboard')
    print('\n--- UI Health Check ---')
    check_ui('/')
    check_ui('/api/system_info')

if __name__ == '__main__':
    main() 