#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, hashlib, io, sys, time, zipfile, requests

def download_zip(url, retries=3, delay=2):
  for attempt in range(1, retries + 1):
    try:
      print(f"Downloading {url} (attempt {attempt}/{retries})...")
      resp = requests.get(url, timeout=30)
      resp.raise_for_status()
      data = resp.content
      if not zipfile.is_zipfile(io.BytesIO(data)):
        print("Error: downloaded content is not a valid ZIP file.", file=sys.stderr)
        sys.exit(1)
      print(f"Downloaded {len(data):,} bytes.")
      return data
    except Exception as e:
      print(f"Attempt {attempt} failed: {e}", file=sys.stderr)
      if attempt < retries:
        time.sleep(delay)
  print("Error: all download attempts failed.", file=sys.stderr)
  sys.exit(1)


def zip_fingerprint(fileobj):
  """Return a dict of {name: sha256_hex} for every entry in a ZIP file-like object."""
  fingerprints = {}
  with zipfile.ZipFile(fileobj) as zf:
    for name in zf.namelist():
      fingerprints[name] = hashlib.sha256(zf.read(name)).hexdigest()
  return fingerprints


def zips_match(remote_data, local_fh):
  try:
    a = zip_fingerprint(io.BytesIO(remote_data))
    b = zip_fingerprint(local_fh)
  except zipfile.BadZipFile as e:
    print(f"Error reading ZIP: {e}", file=sys.stderr)
    sys.exit(1)

  if a.keys() != b.keys():
    missing = a.keys() ^ b.keys()
    print(f"ZIPs differ - mismatched entries: {', '.join(sorted(missing))}")
    return False

  for name in a:
    if a[name] != b[name]:
      print(f"ZIPs differ - content mismatch in: {name}")
      return False

  return True


def recompress(data, output_path):
  """Write a new ZIP to output_path using LZMA compression."""
  with zipfile.ZipFile(io.BytesIO(data)) as zin, \
       zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_LZMA) as zout:
    names = zin.namelist()
    print(f"Recompressing {len(names)} entries with LZMA → {output_path}")
    for name in names:
      zout.writestr(name, zin.read(name))
  print("Done.")


def main():
  parser = argparse.ArgumentParser(description="Download a ZIP and compare it to a local copy; recompress if different.")
  parser.add_argument("url", help="URL of the ZIP file to download")
  parser.add_argument("output", help="Output path for the recompressed ZIP (used only when ZIPs differ)")
  parser.add_argument("-i", "--input", metavar="INPUT_ZIP", help="Local ZIP file to compare against (optional)")
  parser.add_argument("-r", "--retries", type=int, default=5, metavar="N", help="Number of download attempts (default: 5)")
  args = parser.parse_args()

  remote_data = download_zip(args.url, retries=args.retries)

  if args.input:
    try:
      with open(args.input, "rb") as fh:
        if not zipfile.is_zipfile(fh):
          print("Error: input file is not a valid ZIP.", file=sys.stderr)
          sys.exit(1)
        fh.seek(0)
        if zips_match(remote_data, fh):
          print("ZIPs match - nothing to do.")
          sys.exit(0)
    except OSError as e:
      print(f"Error reading input file: {e}", file=sys.stderr)
      sys.exit(1)

  recompress(remote_data, args.output)

if __name__ == "__main__":
  main()

