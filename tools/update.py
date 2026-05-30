#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob, os, subprocess, sys, requests
from datetime import datetime

SOURCES = {
  "euskotren": "https://nap.transportes.gob.es/api/v2/fichero/1263/descarga",
}

API_KEY = os.environ.get("NAP_API_KEY")
if not API_KEY:
  sys.exit("NAP_API_KEY not set")

def resolve_url(api_url):
  r = requests.get(api_url, headers={"ApiKey": API_KEY})
  r.raise_for_status()
  payload = r.json()
  if not payload.get("success"):
    raise RuntimeError(payload.get("message", "API error"))
  return payload["data"]["enlaceDescarga"]

def latest_zip(basename):
  matches = sorted(glob.glob(f"data/{basename}_????-??-??_??-??.zip"))
  return matches[-1] if matches else None

def run_dump(basename, api_url):
  url      = resolve_url(api_url)
  ts       = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
  output   = f"data/{basename}_{ts}.zip"
  existing = latest_zip(basename)

  cmd = [sys.executable, "tools/gtfs_dump.py", url, output]
  if existing:
    cmd += ["--input", existing]

  print(f"\n[{basename}] {existing or '(no local file)'} -> {output}")
  return subprocess.run(cmd).returncode == 0

os.makedirs("data", exist_ok=True)
failures = [b for b, u in SOURCES.items() if not run_dump(b, u)]

print()
if failures:
  print(f"Failed: {', '.join(failures)}", file=sys.stderr)
  sys.exit(1)
print("Done.")

