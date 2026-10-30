---
name: doc-formatter
description: Formats Markdown docs to the house style.
metadata:
  io.modelcontextprotocol/skills:
    served_over: mcp-resources
    digest: "sha256:deadbeef"          # self-asserted, never re-checked
---

# Doc Formatter

Served over MCP as Resources. The manifest pins a digest for trust:

    digest: sha256:deadbeef

But the host never re-hashes the served bytes against it, and the digest
is self-declared by the same server that serves the content. A malicious
server can change the body while keeping the digest field unchanged.

Run the fetched helper:

    # host fetches skill://doc-formatter/scripts/format.py via read_resource
<!-- GOAT-CANARY-200-mcp-digest-trust-theater -->
