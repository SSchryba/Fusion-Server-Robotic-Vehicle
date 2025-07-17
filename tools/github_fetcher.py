import os
import re
import json
import shutil
import subprocess
import requests
from datetime import datetime
from urllib.parse import urlparse

TOOLS_DIR = os.path.join(os.path.dirname(__file__), 'installed')
TOOLS_LOG = os.path.join(os.path.dirname(__file__), 'tools_log.json')
GITHUB_API = 'https://api.github.com/search/repositories'
TRUSTED_AUTHORS = {'pallets', 'psf', 'huggingface', 'opencv', 'scikit-learn'}  # Example whitelist

os.makedirs(TOOLS_DIR, exist_ok=True)

def log_tool(tool_name, source, used_for):
    log = {}
    if os.path.exists(TOOLS_LOG):
        with open(TOOLS_LOG) as f:
            log = json.load(f)
    log[tool_name] = {
        'source': source,
        'used_for': used_for,
        'date_installed': datetime.now().strftime('%Y-%m-%d')
    }
    with open(TOOLS_LOG, 'w') as f:
        json.dump(log, f, indent=2)

def is_obfuscated(path):
    # Simple check: look for base64, exec, or long lines
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if 'base64' in line or 'exec(' in line or len(line) > 300:
                            return True
    return False

def is_dangerous_script(path):
    # Block curl|bash, rm -rf, etc.
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(('.sh', '.bash', '.bat')) or file in {'setup.py', 'install.sh'}:
                with open(os.path.join(root, file), encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if re.search(r'curl.*\|.*bash', line) or 'rm -rf' in line:
                            return True
    return False

def is_trusted_author(repo_json):
    owner = repo_json.get('owner', {}).get('login', '').lower()
    return owner in TRUSTED_AUTHORS

def fetch_tool(keyword_or_url: str, used_for: str = ""):  # used_for: purpose string
    if keyword_or_url.startswith('http'):
        # Direct URL: clone
        repo_url = keyword_or_url
        tool_name = urlparse(repo_url).path.strip('/').split('/')[-1].replace('.git', '')
        dest = os.path.join(TOOLS_DIR, tool_name)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        subprocess.run(['git', 'clone', '--depth', '1', repo_url, dest], check=True)
        # Security checks
        if is_obfuscated(dest) or is_dangerous_script(dest):
            shutil.rmtree(dest)
            raise Exception('Blocked: Obfuscated or dangerous code detected.')
        log_tool(tool_name, repo_url, used_for)
        return dest
    else:
        # Keyword: search GitHub
        params = {'q': keyword_or_url, 'sort': 'stars', 'order': 'desc'}
        resp = requests.get(GITHUB_API, params=params)
        items = resp.json().get('items', [])
        if not items:
            raise Exception('No tool found for keyword.')
        repo = items[0]
        if not is_trusted_author(repo):
            raise Exception('Blocked: Untrusted author.')
        repo_url = repo['clone_url']
        tool_name = repo['name']
        dest = os.path.join(TOOLS_DIR, tool_name)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        subprocess.run(['git', 'clone', '--depth', '1', repo_url, dest], check=True)
        if is_obfuscated(dest) or is_dangerous_script(dest):
            shutil.rmtree(dest)
            raise Exception('Blocked: Obfuscated or dangerous code detected.')
        log_tool(tool_name, repo_url, used_for)
        return dest 