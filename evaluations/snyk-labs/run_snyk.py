#!/usr/bin/env python3
"""Snyk Labs UI sweep — using agent-browser CLI commands for reliability."""
import json, re, subprocess, sys, time, pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
PAGE = "https://labs.snyk.io/experiments/skill-scan/"
BASE = "https://github.com/optimuslabs-io/skillsgoat/tree/main/pasture"
CSV = HERE / "results.csv"

ENTRIES = [
    ("000-base64-obvious",            "calibration/000-base64-obvious/skill",                       "malicious"),
    ("000-bcc-exfil",                 "calibration/000-bcc-exfil/skill",                            "malicious"),
    ("000-env-harvest-loop",          "calibration/000-env-harvest-loop/skill",                     "malicious"),
    ("000-ignore-previous-instructions","calibration/000-ignore-previous-instructions/skill",       "malicious"),
    ("000-plain-curl-bash",           "calibration/000-plain-curl-bash/skill",                      "malicious"),
    ("300-bytecode-poisoning",        "hidden-artifact-packing/300-bytecode-poisoning/skill",       "malicious"),
    ("300-archive-indirection-docx",  "hidden-artifact-packing/300-archive-indirection-docx/skill", "malicious"),
    ("300-corporate-narrative",       "llm-judge-manipulation/300-corporate-narrative/skill",       "malicious"),
    ("300-newline-canyon",            "context-truncation-padding/300-newline-canyon/skill",        "malicious"),
    ("security-doc-explains-attacks", "benign/000-security-doc-explains-attacks/skill",             "benign"),
    ("ssh-config-reader",             "benign/000-ssh-config-reader/skill",                         "benign"),
    ("registry-mirror-documented",    "benign/000-registry-mirror-documented/skill",                "benign"),
]

def run_cmd(*args, timeout=90):
    r = subprocess.run(["agent-browser", *args], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def js_eval(code, timeout=30):
    r = subprocess.run(["agent-browser", "eval", code], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def clean(txt):
    t = txt.encode().decode("unicode_escape", errors="replace")
    m = re.search(r"By submitting.*?(?=Scan with the CLI)", txt, re.S)
    return m.group(0) if m else t[:3000]

def scan_one(eid, rel, truth):
    print(f"== {eid} ==", flush=True)
    skill_md = (REPO / "pasture" / rel / "SKILL.md").read_text()
    mname = re.search(r"^name:\s*(.+)$", skill_md, re.M).group(1).strip()
    marker = mname.split()[0].lower()
    
    # Fresh page load
    subprocess.run(["agent-browser", "open", PAGE], capture_output=True, timeout=60)
    time.sleep(2)
    try:
        subprocess.run(["agent-browser", "wait", "--load", "networkidle"], capture_output=True, timeout=30)
    except: pass
    time.sleep(1)
    
    # Fill URL using agent-browser fill (triggers validation)
    url = BASE + "/" + rel
    subprocess.run(["agent-browser", "fill", 'input[type="text"], input:not([type]), textarea', BASE + "/" + rel], capture_output=True, timeout=30)
    time.sleep(1)
    
    # Wait for Scan button to enable
    for _ in range(15):
        time.sleep(1)
        btn_state = subprocess.run(
            ["agent-browser", "eval", """(() => {
                const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Scan');
                return btn ? (btn.disabled ? 'DISABLED' : 'ENABLED') : 'NOT_FOUND';
            })()"""],
            capture_output=True, text=True, timeout=10).stdout.strip()
        if "ENABLED" in btn_state:
            break
        time.sleep(1)
    else:
        return "BUTTON_TIMEOUT", ""
    
    # Click Scan
    click_result = subprocess.run(
        ["agent-browser", "click", 'button:has-text("Scan")'],
        capture_output=True, text=True, timeout=10
    ).stdout.strip()
    print(f"  click: {click_result}")
    
    if "error" in click_result.lower() or not click_result:
        return "CLICK_FAILED", ""
    
    # Wait for result
    skill_md = (REPO / "pasture" / rel / "SKILL.md").read_text()
    mname = re.search(r"^name:\s*(.+)$", skill_md, re.M).group(1).strip()
    marker = mname.split()[0].lower()
    
    start = time.time()
    deadline = time.time() + 180
    while time.time() < deadline:
        time.sleep(5)
        txt = subprocess.run(
            ["agent-browser", "eval", "document.body.innerText"],
            capture_output=True, text=True, timeout=30
        ).stdout.strip()
        if not txt:
            continue
        low = txt.lower()
        # Fresh result: "Re-analyse" button present AND our skill name present
        if "re-analyse" in txt.lower() and marker in txt.lower():
            return "SUCCESS", txt
        # Scan failed
        if "analysis could not be completed" in txt.lower() or "analysis failed" in txt.lower():
            return "SCAN_FAILED", ""
        if "scan failed" in txt.lower() or "analysis failed" in txt.lower():
            return "SCAN_FAILED", ""
        # Stale result check
        if "re-analyse" in txt.lower() and marker not in txt.lower():
            return "STALE", ""
    return "TIMEOUT", ""

def clean(txt):
    t = txt.encode().decode("unicode_escape", errors="replace")
    m = re.search(r"By submitting.*?(?=Scan with the CLI)", txt, re.S)
    return m.group(0) if m else t[:3000]

def record_result(eid, truth, status, txt=""):
    edir = HERE / "evidence" / eid
    edir.mkdir(parents=True, exist_ok=True)
    if status == "SUCCESS":
        body = clean(txt)
        (edir / "raw.txt").write_text(body)
        subprocess.run(["agent-browser", "screenshot", str(edir / "verdict.png")], capture_output=True)
        mm = re.search(r"ISSUES FOUND\n(\d+)", txt)
        c = re.search(r"SEVERITY BREAKDOWN\nC\n(\d+)\nH\n(\d+)\nM\n(\d+)\nL\n(\d+)", txt)
        row = f"{eid},{truth},{mm.group(1) if mm else 0},{c.group(1) if c else 0},{c.group(2) if c else 0},{c.group(3) if c else 0},{c.group(4) if c else 0}"
        CSV.open("a").write(row + "\n")
        return row
    elif status == "SCAN_FAILED":
        CSV.open("a").write(f"{eid},{truth},SCAN_FAILED,0,0,0,0\n")
        return f"{eid},{truth},SCAN_FAILED"
    elif status == "TIMEOUT":
        CSV.open("a").write(f"{eid},{truth},TIMEOUT,0,0,0,0\n")
        return f"{eid},{truth},TIMEOUT"
    else:
        CSV.open("a").write(f"{eid},{truth},ERROR,0,0,0,0\n")
        return f"{eid},{truth},ERROR"

if not CSV.exists():
    CSV.write_text("entry_id,truth,issues,C,H,M,L\n")

# Load already valid results to skip
done = set()
if CSV.exists():
    for line in CSV.read_text().splitlines()[1:]:
        if line.strip() and "INVALID" not in line and "TIMEOUT" not in line and "SCAN_FAILED" not in line and "ERROR" not in line:
            done.add(line.split(",")[0])

# Allow filtering via CLI args
only = set(sys.argv[1:]) if len(sys.argv) > 1 else None

def run_scan(eid, rel, truth):
    skill_md = (REPO / "pasture" / rel / "SKILL.md").read_text()
    mname = re.search(r"^name:\s*(.+)$", skill_md, re.M).group(1).strip()
    marker = mname.split()[0].lower()
    
    # Fresh page load
    subprocess.run(["agent-browser", "open", PAGE], capture_output=True, timeout=60)
    time.sleep(2)
    try:
        subprocess.run(["agent-browser", "wait", "--load", "networkidle"], capture_output=True, timeout=30)
    except: pass
    time.sleep(1)
    
    # Fill URL using agent-browser fill (triggers validation)
    url = BASE + "/" + rel
    subprocess.run(["agent-browser", "fill", 'input[type="text"], input:not([type]), textarea', BASE + "/" + rel], capture_output=True, timeout=30)
    time.sleep(1)
    
    # Wait for Scan button to enable
    for _ in range(15):
        time.sleep(1)
        btn_state = subprocess.run(
            ["agent-browser", "eval", """(() => {
                const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Scan');
                return btn ? (btn.disabled ? 'DISABLED' : 'ENABLED') : 'NOT_FOUND';
            })()"""],
            capture_output=True, text=True, timeout=10).stdout.strip()
        if "ENABLED" in btn_state:
            break
        time.sleep(1)
    else:
        return "BUTTON_TIMEOUT", ""
    
    # Click Scan
    click_result = subprocess.run(
        ["agent-browser", "click", 'button:has-text("Scan")'],
        capture_output=True, text=True, timeout=10
    ).stdout.strip()
    print(f"  click: {click_result}")
    
    if "error" in click_result.lower() or not click_result:
        return "CLICK_FAILED", ""
    
    # Wait for result
    skill_md = (REPO / "pasture" / rel / "SKILL.md").read_text()
    mname = re.search(r"^name:\s*(.+)$", skill_md, re.M).group(1).strip()
    marker = mname.split()[0].lower()
    
    start = time.time()
    deadline = time.time() + 180
    while time.time() < deadline:
        time.sleep(5)
        txt = subprocess.run(
            ["agent-browser", "eval", "document.body.innerText"],
            capture_output=True, text=True, timeout=30
        ).stdout.strip()
        if not txt:
            continue
        low = txt.lower()
        # Fresh result: "Re-analyse" button present AND our skill name present
        if "re-analyse" in txt.lower() and marker in txt.lower():
            return "SUCCESS", txt
        # Scan failed
        if "analysis could not be completed" in txt.lower() or "analysis failed" in txt.lower():
            return "SCAN_FAILED", ""
        if "scan failed" in txt.lower() or "analysis failed" in txt.lower():
            return "SCAN_FAILED", ""
        # Stale result check
        if "re-analyse" in txt.lower() and marker not in txt.lower():
            return "STALE", ""
    return "TIMEOUT", ""

def clean(txt):
    t = txt.encode().decode("unicode_escape", errors="replace")
    m = re.search(r"By submitting.*?(?=Scan with the CLI)", txt, re.S)
    return m.group(0) if m else t[:3000]

def record_result(eid, truth, status, txt=""):
    edir = HERE / "evidence" / eid
    edir.mkdir(parents=True, exist_ok=True)
    if status == "SUCCESS":
        body = clean(txt)
        (edir / "raw.txt").write_text(body)
        subprocess.run(["agent-browser", "screenshot", str(edir / "verdict.png")], capture_output=True)
        mm = re.search(r"ISSUES FOUND\n(\d+)", txt)
        c = re.search(r"SEVERITY BREAKDOWN\nC\n(\d+)\nH\n(\d+)\nM\n(\d+)\nL\n(\d+)", txt)
        row = f"{eid},{truth},{mm.group(1) if mm else 0},{c.group(1) if c else 0},{c.group(2) if c else 0},{c.group(3) if c else 0},{c.group(4) if c else 0}"
        CSV.open("a").write(row + "\n")
        return row
    elif status == "SCAN_FAILED":
        CSV.open("a").write(f"{eid},{truth},SCAN_FAILED,0,0,0,0\n")
        return f"{eid},{truth},SCAN_FAILED"
    elif status == "TIMEOUT":
        CSV.open("a").write(f"{eid},{truth},TIMEOUT,0,0,0,0\n")
        return f"{eid},{truth},TIMEOUT"
    else:
        CSV.open("a").write(f"{eid},{truth},ERROR,0,0,0,0\n")
        return f"{eid},{truth},ERROR"

if not CSV.exists():
    CSV.write_text("entry_id,truth,issues,C,H,M,L\n")

# Load already valid results to skip
done = set()
if CSV.exists():
    for line in CSV.read_text().splitlines()[1:]:
        if line.strip() and "INVALID" not in line and "TIMEOUT" not in line and "SCAN_FAILED" not in line and "ERROR" not in line:
            done.add(line.split(",")[0])

# Allow filtering via CLI args
only = set(sys.argv[1:]) if len(sys.argv) > 1 else None

def run_scan(eid, rel, truth):
    skill_md = (REPO / "pasture" / rel / "SKILL.md").read_text()
    mname = re.search(r"^name:\s*(.+)$", skill_md, re.M).group(1).strip()
    marker = mname.split()[0].lower()
    
    # Fresh page load
    subprocess.run(["agent-browser", "open", PAGE], capture_output=True, timeout=60)
    time.sleep(2)
    try:
        subprocess.run(["agent-browser", "wait", "--load", "networkidle"], capture_output=True, timeout=30)
    except: pass
    time.sleep(1)
    
    # Fill URL using agent-browser fill (triggers validation)
    url = BASE + "/" + rel
    subprocess.run(["agent-browser", "fill", 'input[type="text"], input:not([type]), textarea', BASE + "/" + rel], capture_output=True, timeout=30)
    time.sleep(1)
    
    # Wait for Scan button to enable
    for _ in range(15):
        time.sleep(1)
        btn_state = subprocess.run(
            ["agent-browser", "eval", """(() => {
                const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Scan');
                return btn ? (btn.disabled ? 'DISABLED' : 'ENABLED') : 'NOT_FOUND';
            })()"""],
            capture_output=True, text=True, timeout=10).stdout.strip()
        if "ENABLED" in btn_state:
            break
        time.sleep(1)
    else:
        return "BUTTON_TIMEOUT", ""
    
    # Click Scan
    click_result = subprocess.run(
        ["agent-browser", "click", 'button:has-text("Scan")'],
        capture_output=True, text=True, timeout=10
    ).stdout.strip()
    print(f"  click: {click_result}")
    
    if "error" in click_result.lower() or not click_result:
        return "CLICK_FAILED", ""
    
    # Wait for result
    skill_md = (REPO / "pasture" / rel / "SKILL.md").read_text()
    mname = re.search(r"^name:\s*(.+)$", skill_md, re.M).group(1).strip()
    marker = mname.split()[0].lower()
    
    start = time.time()
    deadline = time.time() + 180
    while time.time() < deadline:
        time.sleep(5)
        txt = subprocess.run(
            ["agent-browser", "eval", "document.body.innerText"],
            capture_output=True, text=True, timeout=30
        ).stdout.strip()
        if not txt:
            continue
        low = txt.lower()
        # Fresh result: "Re-analyse" button present AND our skill name present
        if "re-analyse" in txt.lower() and marker in txt.lower():
            return "SUCCESS", txt
        # Scan failed
        if "analysis could not be completed" in txt.lower() or "analysis failed" in txt.lower():
            return "SCAN_FAILED", ""
        if "scan failed" in txt.lower() or "analysis failed" in txt.lower():
            return "SCAN_FAILED", ""
        # Stale result check
        if "re-analyse" in txt.lower() and marker not in txt.lower():
            return "STALE", ""
    return "TIMEOUT", ""

def clean(txt):
    t = txt.encode().decode("unicode_escape", errors="replace")
    m = re.search(r"By submitting.*?(?=Scan with the CLI)", txt, re.S)
    return m.group(0) if m else t[:3000]

def record_result(eid, truth, status, txt=""):
    edir = HERE / "evidence" / eid
    edir.mkdir(parents=True, exist_ok=True)
    if status == "SUCCESS":
        body = clean(txt)
        (edir / "raw.txt").write_text(body)
        subprocess.run(["agent-browser", "screenshot", str(edir / "verdict.png")], capture_output=True)
        mm = re.search(r"ISSUES FOUND\n(\d+)", txt)
        c = re.search(r"SEVERITY BREAKDOWN\nC\n(\d+)\nH\n(\d+)\nM\n(\d+)\nL\n(\d+)", txt)
        row = f"{eid},{truth},{mm.group(1) if mm else 0},{c.group(1) if c else 0},{c.group(2) if c else 0},{c.group(3) if c else 0},{c.group(4) if c else 0}"
        CSV.open("a").write(row + "\n")
        return row
    elif status == "SCAN_FAILED":
        CSV.open("a").write(f"{eid},{truth},SCAN_FAILED,0,0,0,0\n")
        return f"{eid},{truth},SCAN_FAILED"
    elif status == "TIMEOUT":
        CSV.open("a").write(f"{eid},{truth},TIMEOUT,0,0,0,0\n")
        return f"{eid},{truth},TIMEOUT"
    else:
        CSV.open("a").write(f"{eid},{truth},ERROR,0,0,0,0\n")
        return f"{eid},{truth},ERROR"

if not CSV.exists():
    CSV.write_text("entry_id,truth,issues,C,H,M,L\n")

# Load already valid results to skip
done = set()
if CSV.exists():
    for line in CSV.read_text().splitlines()[1:]:
        if line.strip() and "INVALID" not in line and "TIMEOUT" not in line and "SCAN_FAILED" not in line and "ERROR" not in line:
            done.add(line.split(",")[0])

# Allow filtering via CLI args
only = set(sys.argv[1:]) if len(sys.argv) > 1 else None

for eid, rel, truth in ENTRIES:
    if only and eid not in only:
        continue
    if eid in done:
        print(f"== {eid} == skip(valid)")
        continue
    
    print(f"== {eid} ==")
    for attempt in (1, 2):
        status, txt = scan_one(eid, rel, truth)
        if status == "SUCCESS":
            record_result(eid, truth, "SUCCESS", txt)
            print(f"  SUCCESS")
            break
        elif status == "SCAN_FAILED":
            record_result(eid, truth, "SCAN_FAILED")
            print(f"  SCAN_FAILED")
            break
        else:
            print(f"  attempt {attempt} failed: {status}, retrying...")
            time.sleep(5)
    else:
        record_result(eid, truth, "TIMEOUT")
        print(f"  TIMEOUT after retries")

print("SWEEP DONE")
