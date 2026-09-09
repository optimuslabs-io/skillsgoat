## Summary

<!-- What changed and why. -->

## Checklist

- [ ] `goat lint`, `goat selftest`, and `pytest` pass in a sandbox
- [ ] `goat scan --blind --assert-only` passes (CI runs this)
- [ ] No live hosts, real credentials, or functioning malware
- [ ] Answer keys (`expected.yaml` / `chain.yaml`) stay outside `skill/`
- [ ] If this PR adds or re-runs a scanner matrix: `evaluations/README.md` updated with date, scanner version, collection snapshot, and **`blind: true`**. Do not cite `--no-blind` scores.
