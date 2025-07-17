import os
import base64
import json
from cryptography.fernet import Fernet

print("[+] Dark Kairo Drift Machine Rebuilder Activated...")

# Generate key for secure heartbeat
key = Fernet.generate_key()
cipher = Fernet(key)

# Folder structure
folders = [
    "dark_kairo_drift_machine",
    "dark_kairo_drift_machine/scripts",
    "dark_kairo_drift_machine/config",
    "dark_kairo_drift_machine/drift_logs",
    "dark_kairo_drift_machine/drift_logs/archive",
    "dark_kairo_drift_machine/profit_drivers",
    "dark_kairo_drift_machine/secure_heartbeat",
    "dark_kairo_drift_machine/readme"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"[+] Created folder: {folder}")

# Payloads (compressed)
payloads = {
    "dark_kairo_drift_machine/dark_drift_monetizer.py": """
aW1wb3J0IHNvcywgdGltZSwgc3VicHJvY2Vzcywgam9zb24sIGhhc2hsaWIsIGJhc2U2NApmcm9t
IGNyeXB0b2dyYXBoeS5mZXJuZXQgaW1wb3J0IEZlcm5ldApmcm9tIHNjcmlwdHMgZmx1eGlvbl9s
YXVuY2hlciBpbXBvcnQgcnVuX2ZsdXhpb24KZnJvbSBzY3JpcHRzIHByb2ZpdF9sYXVuY2hlciBp
bXBvcnQgc3RhcnRfZWJheQpmcm9tIHNjcmlwdHMgY3J5cHRvX292ZXJyaWRlIGltcG9ydCBtb25p
dG9yX21pbmVyCmltcG9ydCBkcnlzdGF0aWMKCmNsYXNzIERhcmtLYWlyb0RyaWZ0TW9uZXRpemVy
OgogICAgZGVmIF9faW5pdF9fKHNlbGYpOgogICAgICAgIHNlbGYud2FsbGV0X2FkZHJlc3MgPSBq
c29uLmxvYWRfanNvbigibGVnYWN5IGV4YW1wbGUganNvbiBtZXNzYWdlIHBlcndhbGwgdGVzdCIp
WyJ3YWxsZXRfYWRkcmVzcyJdCiAgICAgICAgc2VsZi5idXNpbmVzc19iYWxhbmNlID0gMCAgICAg
ICAgICAgICAKICAgICAgICBzZWxmLnZlbn
""",
    
    "dark_kairo_drift_machine/scripts/fluxion_launcher.py": """
aW1wb3J0IHN1YnByb2Nlc3MKZGVmIHJ1bl9mbHV4aW9uKCk6CiAgICBwcmludCgiW0ZsdXhpb24g
U3RhcnRlZF0gVW5sZWFzaGluZyBFdmlsIFR3aW4uLi4iKQogICAgc3VicHJvY2Vzcy5Qb3Blbihb
ImJhc2giLCAiZmx1eGlvbi9mbHV4aW9uLnNoIl0pCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6
CiAgICBydW5fZmx1eGlvbigp
""",
    
    "dark_kairo_drift_machine/config/settings.json": """
ewogICJ2ZW5tb191c2VybmFtZSI6ICJDb21tYW5kZXJWdHJpcml1bU1hcmtldCIsCiAgInNlbGVj
dGVkX21vZHVsZSI6ICJhaXJnZWRkb24iCn0=
""",
    
    "dark_kairo_drift_machine/secure_heartbeat/genesis.txt": base64.b64encode(
        cipher.encrypt(b"April 26, 2025: The Commander ignited the first true silent drift economy.")
    ).decode('utf-8'),
    
    "dark_kairo_drift_machine/readme/README_SETUP.md": """
IyBEYXJrIEthaXJvIERyaWZ0IE1vbmV0aXplciBTZXQgdXAKCi0gRXh0cmFjdCB0aGUgWklaCi0g
UnVuOiBzdWRvIHB5dGhvbjMgZGFya19kcmlmdF9tb25ldGl6ZXIucHkKLSBDb25maWd1cmUgc2V0
dGluZ3MuSlNPTiBmb3Igd2FsbGV0LCBzZWxlY3RlZCBtb2R1bGUuCi0gU3RhcnQgc2ltdWxhdGVk
IGRyYWZ0IGJ1c2luZXNzIGVuZ2luZSBmcm9tIHRoZSBtYWluIGxhdW5jaGVyLg==
"""
}

# Rebuild payloads
for path, data in payloads.items():
    # Fix base64 padding if needed
    padding_needed = len(data) % 4
    if padding_needed:
        data += '=' * (4 - padding_needed)
    
    try:
        decoded = base64.b64decode(data.encode('utf-8'))
        full_path = os.path.join(os.getcwd(), path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(decoded)
        print(f"[+] Reconstructed: {path}")
    except Exception as e:
        print(f"[!] Error reconstructing {path}: {e}")

# Save encryption key securely
with open("dark_kairo_drift_machine/secure_heartbeat/key.key", "wb") as keyfile:
    keyfile.write(key)
print("[+] Drift Heartbeat Key stored.")

print("\n[+] Dark Kairo Drift Machine Reconstruction Complete.")
print("[+] Ready to Ignite Commander Drift Empire.")