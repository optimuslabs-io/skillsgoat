# Security Policy

This repository is a labeled research corpus of **inert-C2** malicious-looking
agent skills. Clone and **test in a local or cloud sandbox** you already
trust. Inert URLs do not mean it is safe to run pasture scripts or a live
agent next to production secrets. We do not endorse a sandbox vendor.
See [docs/SAFETY.md](docs/SAFETY.md).

## Why GitHub hosts this

This is permitted research tooling: labeled, inert-C2 fixtures for scoring
scanners, not a malware distribution kit. Network endpoints are RFC 2606 /
RFC 5737. Payloads do not phone home. GitHub's Acceptable Use Policy allows
security research and malware samples that are clearly marked and not used
to compromise others. Fixtures stay behind `goat lint`; live C2 is a lint
failure.

If this GitHub copy is taken down, the citable archive is Zenodo (DOI to be
attached on the `v0.3.0` dataset release). Cite [CITATION.cff](CITATION.cff).

## Report a vulnerability in the harness

If you find a bug in `goat.py`, `setup`, `tools/link_skills.py`, CI, or
packaging that could leak host paths, execute unexpected installs, or
weaken the inertness lint, open a private GitHub security advisory on
this repo (or email the maintainers listed in the GitHub org).

Do **not** file a public issue with a working exploit against the
harness.

## Scanner misses on the corpus

If a maintained scanner fails a SkillsGoat fixture it claims to cover,
notify the vendor privately first. Withhold mechanism-level detail until
they ship a fix or **90 days** pass. Evaluation reports should note
vendor-contact status.

## Out of scope

- Asking us to make a fixture "more exploitable" or to restore live C2
- Platform CVEs in Claude Code / Cursor / Codex (report those upstream)
- Scores quoted without a last-run date (see `evaluations/README.md`)
