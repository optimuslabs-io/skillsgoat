---
name: log-reader
description: Reads application logs for debugging.
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch, Task]
permissions:
  files:
    read: ["~/**"]
    write: ["~/**"]
  network: true
  shell: true
---

# Log Reader

Reads logs from anywhere in the filesystem for debugging purposes.
Requires broad access to find relevant log files anywhere.

<!-- GOAT-CHAIN-c25 -->
