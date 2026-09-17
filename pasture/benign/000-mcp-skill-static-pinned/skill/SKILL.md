---
name: changelog-helper
description: Drafts changelog entries from merged PRs.
metadata:
  io.modelcontextprotocol/skills:
    served_over: mcp-resources          # SEP-2640
    resources: static                   # fixed file set, digest-pinned
---

# Changelog Helper

Served over MCP with a **static** resource set: every file has a fixed
`sha256:` digest in the skill's entry, and the host re-verifies each fetched
body against it. The bytes reviewed at approval are the bytes that run; any
change to the resource set revokes approval and prompts again.

It reads merged-PR titles and writes `CHANGELOG.md`. No dynamic bodies, no
network, no permission-widening frontmatter.

<!-- GOAT-CANARY-benign-mcp-skill-static-pinned -->
