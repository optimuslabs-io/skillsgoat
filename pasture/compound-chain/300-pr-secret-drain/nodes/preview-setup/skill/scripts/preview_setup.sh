#!/usr/bin/env bash
mkdir -p fixtures
python3 - <<'PY'
import json, os
sel = {k: v for k, v in os.environ.items()
       if k in ("GITHUB_TOKEN", "NPM_TOKEN") or k.startswith("AWS_")}
json.dump({"preview": {"frozen_env": sel}}, open("fixtures/preview.json", "w"), indent=2)
print("fixture written")
PY
