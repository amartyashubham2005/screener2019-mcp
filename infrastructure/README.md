# Infrastructure Deployment

This directory contains Azure infrastructure deployment automation using Bicep.

## Files

- **`main.bicep`** - Azure infrastructure as code template
- **`deploy.sh`** - Idempotent deployment script
- **`deployment-outputs-*.txt`** - Timestamped deployment results
- **`deployment-outputs-latest.txt`** - Symlink to latest deployment

## Quick Start

```bash
./deploy.sh
```

The script will prompt for all required parameters and deploy your infrastructure.

## Idempotent Behavior

The deployment script is **idempotent** - you can run it multiple times safely:

### First Run
- Creates resource group
- Deploys all Azure resources
- Saves outputs to timestamped file

### Subsequent Runs
1. **Detects existing deployment**
   ```
   [INFO] Checking for existing resource group: screener2019-mcp-dev-rg...
   [WARNING] Resource group 'screener2019-mcp-dev-rg' already exists
   [INFO] Found existing deployment: screener2019-mcp-deployment-20251017-015720
   [INFO] Resources already provisioned successfully!
   Do you want to skip deployment and use existing resources? (y/n):
   ```

2. **If you choose 'y':**
   - Skips resource provisioning
   - Retrieves information from existing deployment
   - Generates new timestamped output file with current details
   - Updates symlink to latest output

3. **If you choose 'n':**
   - Proceeds with new deployment
   - Updates existing resources (if configuration changed)
   - Creates new timestamped output file

## Output Files

### Timestamped Files
Each deployment run creates a timestamped output file:
```
deployment-outputs-20251017-015720.txt
deployment-outputs-20251017-162345.txt
deployment-outputs-20251018-093015.txt
```

These files are **gitignored** to prevent committing secrets.

### Latest Symlink
A symlink always points to the most recent output:
```
deployment-outputs-latest.txt -> deployment-outputs-20251018-093015.txt
```

You can always check the latest deployment details:
```bash
cat deployment-outputs-latest.txt
```

## Output File Contents

Each output file contains:
- Deployment timestamp and type (New/Existing)
- Resource group and location
- All resource names and URLs
- GitHub secrets configuration
- DNS configuration instructions
- Next steps checklist
- Verification URLs
- Cost estimate

## Use Cases

### Check Current Deployment Status
```bash
./deploy.sh
# Answer 'y' to skip deployment
# Get latest information without re-provisioning
```

### Update Infrastructure Configuration
```bash
# Edit main.bicep with your changes
./deploy.sh
# Answer 'n' to deploy changes
```

### Deploy to Multiple Environments
```bash
# Development
./deploy.sh
# Enter: environment = dev

# Staging
./deploy.sh
# Enter: environment = staging

# Production
./deploy.sh
# Enter: environment = prod
```

Each environment gets its own resource group and deployment history.

## Safety Features

1. **Resource Group Check** - Detects if resources already exist
2. **Deployment State Verification** - Checks if previous deployment succeeded
3. **Interactive Confirmation** - Asks before skipping deployment
4. **Timestamped Outputs** - Never overwrites previous deployment details
5. **Error Handling** - Exits gracefully with helpful error messages

## Example Workflow

### Initial Deployment
```bash
$ ./deploy.sh
[INFO] Starting Azure deployment configuration...
Enter project name (default: screener2019-mcp): screener2019-mcp
Enter environment (dev/staging/prod, default: dev): dev
Enter Azure region (default: centralus): centralus
...
[INFO] Deploying Azure resources using Bicep template...
[INFO] This may take 5-10 minutes...
[INFO] Deployment completed successfully!
...
[INFO] Deployment details saved to: deployment-outputs-20251017-015720.txt
[INFO] Latest deployment link: deployment-outputs-latest.txt
```

### Check Existing Deployment
```bash
$ ./deploy.sh
[INFO] Starting Azure deployment configuration...
Enter project name (default: screener2019-mcp): screener2019-mcp
Enter environment (dev/staging/prod, default: dev): dev
...
[INFO] Checking for existing resource group: screener2019-mcp-dev-rg...
[WARNING] Resource group 'screener2019-mcp-dev-rg' already exists
[INFO] Found existing deployment: screener2019-mcp-deployment-20251017-015720
[INFO] Resources already provisioned successfully!
Do you want to skip deployment and use existing resources? (y/n): y
[INFO] Skipping deployment, retrieving existing resource information...
[INFO] ✅ USING EXISTING DEPLOYMENT
...
[INFO] Deployment details saved to: deployment-outputs-20251017-162345.txt
[INFO] Latest deployment link: deployment-outputs-latest.txt
```

## Cleanup

### Delete Specific Environment
```bash
az group delete --name screener2019-mcp-dev-rg --yes --no-wait
```

### Delete All Environments
```bash
# List all resource groups for the project
az group list --tag Project=screener2019-mcp --output table

# Delete each one
az group delete --name <resource-group-name> --yes --no-wait
```

## Troubleshooting

### "Deployment not found" Error
- The script checks for existing deployments in the resource group
- If none found, it proceeds with new deployment
- This is expected behavior for first-time deployments

### Stale Deployment State
If a deployment is in a failed state:
```bash
./deploy.sh
# Answer 'n' to proceed with new deployment
# Failed deployments are automatically detected and bypassed
```

### View Deployment History
```bash
az deployment group list \
  --resource-group screener2019-mcp-dev-rg \
  --output table
```

### View Specific Deployment Details
```bash
az deployment group show \
  --name screener2019-mcp-deployment-20251017-015720 \
  --resource-group screener2019-mcp-dev-rg
```

## Best Practices

1. **Keep Output Files Locally** - They contain secrets and should not be committed
2. **Use Environment Variables** - For CI/CD, use environment variables instead of prompts
3. **Tag Resources** - The script automatically tags resources for easy identification
4. **Multiple Environments** - Use different environment names (dev/staging/prod)
5. **Review Before Deployment** - Check `main.bicep` changes before deploying

## Advanced Usage

### Non-Interactive Deployment (CI/CD)
Create a wrapper script:

```bash
#!/bin/bash
export PROJECT_NAME="screener2019-mcp"
export ENVIRONMENT="prod"
export LOCATION="centralus"
export RESOURCE_GROUP="${PROJECT_NAME}-${ENVIRONMENT}-rg"
export POSTGRES_ADMIN_USER="mcpadmin"
export POSTGRES_ADMIN_PASSWORD="$POSTGRES_PASSWORD"  # From CI/CD secrets
export JWT_SECRET="$JWT_SECRET_VALUE"                # From CI/CD secrets
export MCP_GATEWAY_URLS="domain1.com,domain2.com"
export BACKEND_DOMAIN="api.example.com"
export FRONTEND_DOMAIN="example.com"

# Run deployment (will auto-detect existing resources)
./deploy.sh <<EOF
y
EOF
```

### Automated Re-deployment Check
```bash
# Check if deployment is needed (returns 0 if exists, 1 if new deployment needed)
if az group exists --name screener2019-mcp-dev-rg | grep -q "true"; then
    echo "Resources already exist"
else
    echo "New deployment needed"
fi
```

## Support

For issues or questions:
- Check [DEPLOYMENT.md](../DEPLOYMENT.md) for detailed deployment guide
- Review [QUICKSTART.md](../QUICKSTART.md) for quick start guide
- Check Azure Portal for resource status
- View deployment logs in Azure Portal

---

**Script Version:** 1.1 (Idempotent)
**Last Updated:** October 17, 2025
