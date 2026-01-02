# Database Configuration Guide

This document explains how to configure the database connection for `ds-job-insights`.

## Overview

The service supports three methods for configuring the database connection, checked in priority order:

1. **Full URI** - Single environment variable with complete connection string
2. **Individual Components** - Separate variables for host, port, database, user, password
3. **AWS SSM Parameter Store** - Fetch connection string from AWS Systems Manager

## Configuration Methods

### Method 1: Full Connection URI (Recommended for Local Development)

Set a single environment variable with the complete PostgreSQL connection string:

```bash
export DATABASE_URI="postgresql://user:password@localhost:5432/workflow_manager"
```

**Pros:**
- Simple and straightforward
- Easy to copy/paste from database providers
- Works with connection strings from Heroku, Render, etc.

**Cons:**
- Password visible in environment variables
- Less flexible for changing individual components

### Method 2: Individual Components (Recommended for Docker/Kubernetes)

Set separate environment variables for each connection parameter:

```bash
export DB_HOST="localhost"
export DB_PORT="5432"          # Optional, defaults to 5432
export DB_NAME="workflow_manager"
export DB_USER="postgres"
export DB_PASSWORD="secret"
```

**Pros:**
- More flexible (can change host without rebuilding URI)
- Better for containerized environments
- Easier to use with secrets management (e.g., Kubernetes secrets)

**Cons:**
- More variables to manage
- Requires all variables to be set (except DB_PORT)

### Method 3: AWS SSM Parameter Store (Recommended for Production)

Use AWS Systems Manager Parameter Store to securely store the connection string:

```bash
export BUILDING_MODE="dev"      # or staging, prod
export AWS_REGION="eu-north-1"  # Optional, defaults to eu-north-1
```

The service will fetch the connection string from:
```
/dsw/mgr/db_uri-{BUILDING_MODE}
```

**Pros:**
- Secure (encrypted at rest)
- Centralized configuration management
- No secrets in environment variables
- Automatic rotation support

**Cons:**
- Requires AWS credentials and IAM permissions
- Adds dependency on AWS services
- Slower (network call to fetch parameter)

**Required IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/dsw/mgr/db_uri-*"
    }
  ]
}
```

## Examples

### Local Development with Docker Compose

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: workflow_manager
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secret
    ports:
      - "5432:5432"

  analyzer:
    build: .
    environment:
      DB_HOST: postgres
      DB_NAME: workflow_manager
      DB_USER: postgres
      DB_PASSWORD: secret
    depends_on:
      - postgres
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:
  DB_HOST: "postgres.default.svc.cluster.local"
  DB_NAME: "workflow_manager"
  DB_USER: "postgres"
  DB_PASSWORD: "super-secret-password"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: job-insights
spec:
  template:
    spec:
      containers:
      - name: analyzer
        image: ds-job-insights:latest
        envFrom:
        - secretRef:
            name: db-credentials
```

### AWS Lambda with SSM

```python
# lambda_function.py
import os

# Set environment in Lambda configuration
os.environ['BUILDING_MODE'] = 'prod'
os.environ['AWS_REGION'] = 'eu-north-1'

from src.analyzer import FailureAnalyzerJob

def handler(event, context):
    # Will automatically fetch from SSM: /dsw/mgr/db_uri-prod
    job = FailureAnalyzerJob(use_llm=True)
    summary = job.run()
    return summary.to_dict()
```

## Testing Configuration

Test your database configuration:

```bash
# Test connection
uv run python -c "
from src.db.queries import get_db_uri, get_db_session

print(f'Database URI: {get_db_uri()}')

with get_db_session() as session:
    result = session.execute('SELECT version()')
    print(f'Connected to: {result.scalar()}')
"
```

## Troubleshooting

### Connection Refused

```
sqlalchemy.exc.OperationalError: could not connect to server: Connection refused
```

**Solutions:**
- Check that PostgreSQL is running
- Verify `DB_HOST` and `DB_PORT` are correct
- Check firewall rules

### Authentication Failed

```
sqlalchemy.exc.OperationalError: FATAL: password authentication failed
```

**Solutions:**
- Verify `DB_USER` and `DB_PASSWORD` are correct
- Check PostgreSQL `pg_hba.conf` authentication settings

### SSM Parameter Not Found

```
botocore.exceptions.ClientError: An error occurred (ParameterNotFound)
```

**Solutions:**
- Verify `BUILDING_MODE` is set correctly
- Check that parameter exists: `/dsw/mgr/db_uri-{BUILDING_MODE}`
- Verify AWS credentials and IAM permissions
- Check `AWS_REGION` matches where parameter is stored

## Security Best Practices

1. **Never commit credentials** - Use `.env` files (add to `.gitignore`)
2. **Use secrets management** - Prefer SSM, Kubernetes secrets, or vault
3. **Rotate passwords regularly** - Especially for production databases
4. **Use read-only credentials** - This service only needs SELECT permissions
5. **Enable SSL/TLS** - Add `?sslmode=require` to connection string

Example with SSL:
```bash
export DATABASE_URI="postgresql://user:pass@host:5432/db?sslmode=require"
```

