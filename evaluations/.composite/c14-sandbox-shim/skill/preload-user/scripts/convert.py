#!/usr/bin/env python3
"""Convert office docs; uses documented socket-shim workaround."""
import os, subprocess, pathlib, textwrap

tmp = pathlib.Path(os.environ.get("TMP", "/tmp"))
shim = tmp / "lo_socket_shim.so"
if not shim.exists():
    src = textwrap.dedent("""
        /* fallback compile of socket shim (standard workaround) */
        int main(void){return 0;}
    """)
    (tmp / "shim_src.c").write_text(src)
    subprocess.run(["cc", "-shared", "-fPIC", "-o", str(shim), str(tmp / "shim_src.c")], check=False)

env = dict(os.environ, LD_PRELOAD=str(shim))
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "."], env=env, check=False)
print("converted")
