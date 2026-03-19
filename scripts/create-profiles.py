#!/usr/bin/env python3
"""
create-profiles.py — Create CloudLab profiles for CHIME experiments

Creates two profiles:
  - chime-r6525-clemson: 11x r6525 at Clemson, Ubuntu 20.04
  - chime-r650-clemson:  10x r650  at Clemson, Ubuntu 20.04

Usage:
    python3 scripts/create-profiles.py

Requires: files/cloudlab.jwt (JWT token for CloudLab API)
"""

import json
import ssl
import http.client
from pathlib import Path

PORTAL_HOST = "boss.emulab.net"
PORTAL_PORT = 43794
JWT_PATH = Path(__file__).parent.parent / "files" / "cloudlab.jwt"
PROJECT = "CS620426SP"

# ─── geni-lib scripts ────────────────────────────────────────────────────────

SCRIPT_R6525 = """\
import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.emulab as emulab

request = portal.context.makeRequestRSpec()

for i in range(11):
    node = request.RawPC("node{}".format(i))
    node.hardware_type = "r6525"
    node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD"
    node.component_manager_id = "urn:publicid:IDN+clemson.cloudlab.us+authority+cm"

portal.context.printRequestRSpec()
"""

SCRIPT_R650 = """\
import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.emulab as emulab

request = portal.context.makeRequestRSpec()

for i in range(10):
    node = request.RawPC("node{}".format(i))
    node.hardware_type = "r650"
    node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD"
    node.component_manager_id = "urn:publicid:IDN+clemson.cloudlab.us+authority+cm"

portal.context.printRequestRSpec()
"""

PROFILES = [
    {
        "name": "chime-r6525-clemson",
        "description": "11x r6525 nodes at Clemson with Ubuntu 20.04 for CHIME experiments (10 CN + 1 MN)",
        "script": SCRIPT_R6525,
    },
    {
        "name": "chime-r650-clemson",
        "description": "10x r650 nodes at Clemson with Ubuntu 20.04 for CHIME experiments (9 CN + 1 MN)",
        "script": SCRIPT_R650,
    },
]

# ─── API helpers ─────────────────────────────────────────────────────────────

def load_jwt():
    token = JWT_PATH.read_text().strip()
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]
    return token


def api_request(method, path, body=None, jwt=None, depth=0):
    """Make an HTTPS request; follow up to 5 redirects."""
    if depth > 5:
        raise RuntimeError("Too many redirects")

    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(PORTAL_HOST, PORTAL_PORT, context=ctx, timeout=30)

    headers = {"Content-Type": "application/json"}
    if jwt:
        headers["x-api-token"] = jwt

    payload = json.dumps(body).encode() if body else None
    conn.request(method, path, body=payload, headers=headers)
    resp = conn.getresponse()

    if resp.status in (301, 302, 303, 307, 308):
        location = resp.getheader("Location", "")
        resp.read()
        conn.close()
        # Strip host if same host
        if location.startswith("https://"):
            from urllib.parse import urlparse
            parsed = urlparse(location)
            new_path = parsed.path
            if parsed.query:
                new_path += "?" + parsed.query
        else:
            new_path = location
        # For 307/308 preserve method; for others use GET
        new_method = method if resp.status in (307, 308) else "GET"
        return api_request(new_method, new_path, body if new_method == method else None, jwt, depth + 1)

    data = resp.read()
    conn.close()
    return resp.status, data


def create_profile(jwt, name, description, script):
    body = {
        "name": name,
        "description": description,
        "script": script,
        "project": PROJECT,
        "public": False,
    }
    status, data = api_request("POST", "/profiles", body, jwt)
    return status, data


def list_profiles(jwt):
    status, data = api_request("GET", "/profiles", jwt=jwt)
    return status, data


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    jwt = load_jwt()
    print(f"Loaded JWT from {JWT_PATH}")

    # List existing profiles first
    status, data = list_profiles(jwt)
    print(f"\nExisting profiles (GET /profiles): {status}")
    existing_names = set()
    try:
        profiles = json.loads(data)
        plist = profiles.get("profiles", profiles) if isinstance(profiles, dict) else profiles
        if isinstance(plist, list):
            for p in plist:
                pname = p.get("name") or p.get("id") or str(p)
                existing_names.add(pname)
                print(f"  - {pname}")
        else:
            print(f"  (unexpected format)")
    except Exception as e:
        print(f"  Parse error: {e}")
        print(f"  Raw: {data[:200]}")

    print()

    for profile in PROFILES:
        name = profile["name"]
        if name in existing_names:
            print(f"[SKIP] {name} already exists")
            continue

        print(f"[CREATE] {name} ...")
        status, data = create_profile(jwt, name, profile["description"], profile["script"])
        print(f"  Status: {status}")
        try:
            resp = json.loads(data)
            print(f"  Response: {json.dumps(resp, indent=2)[:400]}")
        except Exception:
            print(f"  Raw: {data[:400]}")
        print()


if __name__ == "__main__":
    main()
