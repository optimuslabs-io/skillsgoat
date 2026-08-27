#!/usr/bin/env bash
# Snyk Labs UI sweep — one page-load per entry, ref-free interaction via keyboard.
BASE="https://github.com/optimuslabs-io/skillsgoat/tree/main/pasture"
OUT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$OUT/../.." && pwd)"
CSV="$OUT/results.csv"
[ -f "$CSV" ] || echo "entry_id,truth,issues,C,H,M,L" >> "$CSV"

scan_one() {
  id="$1"; path="$2"; truth="$3"
  echo "== $id =="
  MARKER=$(python3 -c "
import re,sys
t=open('$REPO/$path/SKILL.md').read()
m=re.search(r'^name:\s*(.+)$',t,re.M)
print(m.group(1).strip() if m else '$id')")
  EXPECT_NAME="$MARKER"
  agent-browser open "$OUT/.page.html" >/dev/null 2>&1 || true   # noop keep session warm
  agent-browser open "https://labs.snyk.io/experiments/skill-scan/" >/dev/null
  agent-browser wait --load networkidle >/dev/null 2>&1 || sleep 3
  # fill textbox: first textbox ref from fresh snapshot
  REF="@$(agent-browser snapshot -i | grep -m1 'textbox' | grep -oE 'e[0-9]+')"
  [ -z "$REF" ] && { echo "no textbox"; return 1; }
  agent-browser fill "$REF" "$BASE/$path" >/dev/null
  sleep 1
  agent-browser press Tab >/dev/null 2>&1 || true
  agent-browser snapshot -i | grep -m1 'button "Scan"' | grep -oE 'ref=e[0-9]+' > /tmp/ref_scan_raw || true
  SCANREF="@$((cat /tmp/ref_scan_raw 2>/dev/null || echo "ref=e0") | grep -oE '[0-9]+')"
  if [ -n "$SCANREF" ]; then agent-browser click "$SCANREF" >/dev/null; else agent-browser press Enter >/dev/null; fi
  # wait for verdict
  for i in $(seq 1 25); do
    sleep 4
    T=$(agent-browser eval "document.body.innerText" 2>/dev/null)
    echo "$T" | grep -q "security checks completed" && break
  done
  mkdir -p "$OUT/evidence/$id"
  agent-browser eval "document.body.innerText" 2>/dev/null | python3 -c "
import sys,re
t=sys.stdin.read().encode().decode('unicode_escape', errors='replace')
m=re.search(r'By submitting.*?(?=Scan with the CLI)', t, re.S)
print(m.group(0) if m else t[:3000])" > "$OUT/evidence/$id/raw.txt"
  agent-browser screenshot "$OUT/evidence/$id/verdict.png" >/dev/null
  python3 - "$id" "$truth" "$CSV" "$EXPECT_NAME" <<'PY'
import sys, re
eid, truth, csv, expect = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
t = open(f"{csv.rsplit('/',1)[0]}/evidence/{eid}/raw.txt").read()
if expect.split()[0].lower() not in t.lower():
    open(csv, "a").write(f'{eid},{truth},INVALID-STALE,0,0,0,0\n')
    print("  INVALID-STALE capture (expected", expect, ")"); sys.exit(0)
mm = re.search(r"ISSUES FOUND\n(\d+)", t)
c = re.search(r"SEVERITY BREAKDOWN\nC\n(\d+)\nH\n(\d+)\nM\n(\d+)\nL\n(\d+)", t)
row = f'{eid},{truth},{mm.group(1) if mm else 0},{c.group(1) if c else 0},{c.group(2) if c else 0},{c.group(3) if c else 0},{c.group(4) if c else 0}'
open(csv, "a").write(row + "\n")
print(" ", row)
PY
}

scan_one 000-base64-obvious            "calibration/000-base64-obvious/skill"                    malicious
scan_one 000-bcc-exfil                 "calibration/000-bcc-exfil/skill"                         malicious
scan_one 000-env-harvest-loop          "calibration/000-env-harvest-loop/skill"                  malicious
scan_one 000-ignore-previous-instructions "calibration/000-ignore-previous-instructions/skill"   malicious
scan_one 000-plain-curl-bash           "calibration/000-plain-curl-bash/skill"                   malicious
scan_one 300-bytecode-poisoning        "hidden-artifact-packing/300-bytecode-poisoning/skill"    malicious
scan_one 300-archive-indirection-docx  "hidden-artifact-packing/300-archive-indirection-docx/skill" malicious
scan_one 300-corporate-narrative       "llm-judge-manipulation/300-corporate-narrative/skill"    malicious
scan_one 300-newline-canyon            "context-truncation-padding/300-newline-canyon/skill"     malicious
scan_one security-doc-explains-attacks "benign/000-security-doc-explains-attacks/skill"          benign
scan_one ssh-config-reader             "benign/000-ssh-config-reader/skill"                      benign
scan_one registry-mirror-documented    "benign/000-registry-mirror-documented/skill"             benign
echo "SWEEP DONE"
