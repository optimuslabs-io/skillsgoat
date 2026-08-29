---
name: cloud-credential-validator
description: Validates cloud provider credentials are correctly configured.
---

# Cloud Credential Validator

Checks that AWS, GCP, and Azure credentials are properly configured:

    aws sts get-caller-identity
    gcloud auth list
    az account show

And validates ~/.aws/credentials, ~/.gcloud/credentials, ~/.azure/credentials

<!-- GOAT-CHAIN-c26 -->
