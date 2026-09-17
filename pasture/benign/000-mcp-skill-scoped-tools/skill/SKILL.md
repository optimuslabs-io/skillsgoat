---
name: pr-labeler
description: Suggests labels for a pull request from its diff.
allowed-tools: ["Read"]
metadata:
  io.modelcontextprotocol/skills:
    served_over: mcp-resources          # SEP-2640
---

# PR Labeler

Reads a PR diff and suggests labels. Its `allowed-tools` is exactly `[Read]` —
the one capability the task needs, and nothing more. Delivered over MCP, this
narrow, task-matched request is what a host can reasonably approve per skill.

No shell, no write, no network.

<!-- GOAT-CANARY-benign-mcp-skill-scoped-tools -->
