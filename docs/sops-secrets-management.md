# SOPS Secrets Management

This project uses [SOPS (Secrets OPerationS)](https://github.com/mozilla/sops) for secure secrets management, following the established pattern from your infrastructure setup.

## Overview

SOPS encrypts secrets using GPG keys, allowing safe storage in version control while maintaining security. This approach enables:

- **Version control safety**: Encrypted files can be committed to git
- **Team collaboration**: Share GPG public keys for team access
- **Environment separation**: Different keys for dev/staging/prod
- **Audit trail**: Track changes to encrypted secrets

## Prerequisites

### 1. Install SOPS
```bash
# macOS
brew install sops

# Linux
curl -LO https://github.com/mozilla/sops/releases/latest/download/sops-v3.8.1.linux.amd64
sudo mv sops-v3.8.1.linux.amd64 /usr/local/bin/sops
sudo chmod +x /usr/local/bin/sops
```

### 2. GPG Key Setup
If you don't have a GPG key yet:

```bash
export KEY_NAME="your-name"
export KEY_COMMENT="key for sops"

gpg --batch --full-generate-key <<EOF
%no-protection
Key-Type: 1
Key-Length: 4096
Subkey-Type: 1
Subkey-Length: 4096
Expire-Date: 0
Name-Comment: ${KEY_COMMENT}
Name-Real: ${KEY_NAME}
EOF
```

### 3. Verify Setup
```bash
make secrets-check
```

## Usage

### Generate Initial Secrets
```bash
# Generate all secrets with SOPS encryption
make secrets

# This creates:
# - .env.sops (encrypted environment variables)
# - secrets/kubernetes-secrets.yaml (encrypted K8s secrets)
# - .env (unencrypted for local development)
```

### Working with Encrypted Files

#### Decrypt for Local Development
```bash
# Decrypt .env.sops to .env for local use
make secrets-decrypt
```

#### Edit Encrypted Secrets
```bash
# Edit encrypted environment variables
make secrets-edit

# Or edit directly
sops .env.sops
```

#### View Encrypted Content
```bash
# View decrypted content without saving
sops -d .env.sops

# View Kubernetes secrets
make secrets-k8s-decrypt
```

### Kubernetes Deployment

#### Apply Secrets to Cluster
```bash
# Decrypt and apply to current kubectl context
make secrets-k8s-apply

# Or manually
sops -d secrets/kubernetes-secrets.yaml | kubectl apply -f -
```

#### Verify Secrets in Cluster
```bash
kubectl get secrets -n apps simple-kanban-secrets
kubectl describe secret -n apps simple-kanban-secrets
```

## File Structure

```
simple-kanban/
├── .sops.yaml                    # SOPS configuration
├── .env.example                  # Template with placeholders
├── .env                         # Local development (gitignored)
├── .env.sops                    # Encrypted environment variables
└── secrets/
    └── kubernetes-secrets.yaml  # Encrypted K8s secret manifest
```

## Configuration Files

### `.sops.yaml`
Defines encryption rules and GPG keys:
```yaml
creation_rules:
  - path_regex: \.secrets\.yaml$
    encrypted_regex: ^(data|stringData)$
    pgp: YOUR_GPG_FINGERPRINT
  - path_regex: secrets/.*\.yaml$
    encrypted_regex: ^(data|stringData)$
    pgp: YOUR_GPG_FINGERPRINT
  - path_regex: \.env\.sops$
    pgp: YOUR_GPG_FINGERPRINT
```

### Environment Variables
The following secrets are managed:

- `JWT_SECRET_KEY`: JWT token signing
- `SESSION_SECRET_KEY`: Session encryption
- `POSTGRES_PASSWORD`: Database password
- `OAUTH2_CLIENT_SECRET`: OAuth2 integration
- `API_KEY`: External API access

These secrets must remain stable across redeploys. The Helm chart reuses existing `JWT_SECRET_KEY` and `SESSION_SECRET_KEY` from the in-cluster Secret (once created) so user sessions are not invalidated on every deploy.

## Team Collaboration

### Share GPG Public Key
```bash
# Export your public key
gpg --export --armor YOUR_GPG_FINGERPRINT > team-member.pub.asc

# Team members import it
gpg --import team-member.pub.asc
```

### Add Team Member to SOPS
Update `.sops.yaml` with multiple GPG keys:
```yaml
creation_rules:
  - path_regex: \.env\.sops$
    pgp: >-
      YOUR_GPG_FINGERPRINT,
      TEAM_MEMBER_GPG_FINGERPRINT
```

Re-encrypt existing files:
```bash
sops updatekeys .env.sops
sops updatekeys secrets/kubernetes-secrets.yaml
```

## Security Best Practices

1. **Never commit `.env`** - Only encrypted `.env.sops` is safe
2. **Rotate secrets regularly** - Generate new secrets every 90 days
3. **Use different keys per environment** - Separate dev/staging/prod keys
4. **Backup GPG keys securely** - Store in password manager or vault
5. **Monitor secret access** - Track who decrypts what and when

## Troubleshooting

### Common Issues

#### SOPS not found
```bash
# Install SOPS first
brew install sops  # macOS
```

#### No GPG keys
```bash
# Generate a new GPG key
make secrets  # Will guide you through setup
```

#### Permission denied
```bash
# Check GPG key permissions
gpg --list-secret-keys
```

#### Decryption fails
```bash
# Verify you have the correct GPG key
gpg --list-secret-keys --keyid-format LONG
```

### Recovery

If you lose access to encrypted files:

1. **GPG key backup**: Restore from secure backup
2. **Team member**: Have teammate re-encrypt with your new key
3. **Fresh start**: Generate new secrets (requires app restart)

## Integration with CI/CD

For automated deployments, store GPG private key as CI secret:

```bash
# Export private key for CI
gpg --export-secret-keys --armor YOUR_GPG_FINGERPRINT > ci-private-key.asc

# In CI, import and use
gpg --import ci-private-key.asc
sops -d .env.sops > .env
```

## Makefile Targets

- `make secrets`: Generate all secrets with SOPS encryption
- `make secrets-decrypt`: Decrypt .env.sops to .env
- `make secrets-edit`: Edit encrypted environment variables
- `make secrets-k8s-decrypt`: View Kubernetes secrets
- `make secrets-k8s-apply`: Apply secrets to Kubernetes
- `make secrets-check`: Verify SOPS and GPG setup
