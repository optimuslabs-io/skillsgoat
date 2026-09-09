# Security Policy

This repository is a labeled research collection of **inert-C2** malicious-looking
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

Do not publish a mirror that drops the sandbox warnings or restores live
C2 — that is malware distribution, not this goat. If GitHub takes this
copy down, the citable archive is Zenodo (DOI to be attached on the
`v0.3.0` dataset release). Cite [CITATION.cff](CITATION.cff).

## Report a vulnerability in the harness

If you find a bug in `goat.py`, `setup`, `tools/link_skills.py`, CI, or
packaging that could leak host paths, execute unexpected installs, or
weaken the inertness lint, open a private GitHub security advisory on
this repo (or email the maintainers listed in the GitHub org).

Do **not** file a public issue with a working exploit against the
harness.

## Scanner results on the collection

SkillsGoat is a benchmark of public, deliberately-vulnerable fixtures, not a
vulnerability report against a product. A scanner missing a fixture is a
detection-rate result, not a 0-day: the technique is already public, so the
score arms no one. Results are published openly, the way AV-Comparatives and
MITRE ATT&CK evals name products and print numbers. The bar we hold is
accuracy, not secrecy:

- **Reproducible.** Every published number comes from `goat scan --blind`,
  with the scanner version, run date, and `blind` / `blind_salt` /
  `canary_token` recorded under `evaluations/`. Anyone can re-run it.
- **Versioned and dated.** Scores name the exact build and date; they go
  stale, so cite the date (see `evaluations/README.md`).
- **Right of reply.** Vendors are welcome to reproduce, contest, or annotate
  a result; corrections ship in the same ledger.
- **Courtesy notice for a genuinely novel bypass.** If a fixture is a
  technique not already public, we give the affected vendor a short heads-up
  before publishing the mechanism — a relationship courtesy, not an embargo.

## Out of scope

- Asking us to make a fixture "more exploitable" or to restore live C2
- Platform CVEs in Claude Code / Cursor / Codex (report those upstream)
- Scores quoted without a last-run date (see `evaluations/README.md`)
