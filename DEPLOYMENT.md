# Azure Deployment Guide - MCP Application

Complete guide for deploying the MCP application (Python FastAPI backend + React frontend) to Azure with automated CI/CD.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Deploy Infrastructure](#deploy-infrastructure)
5. [Configure GitHub Actions](#configure-github-actions)
6. [Configure Custom Domains & DNS](#configure-custom-domains--dns)
7. [Post-Deployment Configuration](#post-deployment-configuration)
8. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
9. [Cost Estimation](#cost-estimation)

---

## Architecture Overview

**Services Used:**
- **Azure App Service** (Linux, Python 3.12) - Backend API
- **Azure Static Web Apps** - Frontend React application
- **Azure Database for PostgreSQL** (Flexible Server) - Database
- **Azure Application Insights** - Monitoring and logging
- **Azure Log Analytics** - Centralized logging

**URLs:**
- Backend: `https://api.example.com` (your custom domain)
- Frontend: `https://example.com` (your custom domain)

---

## Prerequisites

### Required Tools
1. **Azure CLI** - [Install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
   ```bash
   # Verify installation
   az --version
   ```

2. **GitHub Account** - With repository access
3. **Domain Name** - For custom DNS (e.g., example.com)
4. **Azure Subscription** - Active subscription with Owner/Contributor role

### Required Information
- [ ] Azure subscription ID
- [ ] Domain name (for DNS configuration)
- [ ] PostgreSQL admin username and password
- [ ] JWT secret key (generate secure random string)
- [ ] MCP Gateway URL pools (comma-separated domains)

---

## Initial Setup

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd mcp
```

### 2. Login to Azure
```bash
az login

# List subscriptions
az account list --output table

# Set active subscription
az account set --subscription "<subscription-id>"
```

---

## Deploy Infrastructure

### Option 1: Automated Script (Recommended)

Run the interactive deployment script:

```bash
cd infrastructure
./deploy.sh
```

The script will:
1. Prompt for all required parameters
2. Create resource group
3. Deploy all Azure resources using Bicep
4. Output deployment details and next steps
5. Save outputs to `deployment-outputs.txt`

**Parameters you'll be prompted for:**
- Project name (default: `mcp`)
- Environment (`dev`, `staging`, or `prod`)
- Azure region (default: `eastus`)
- Resource group name
- PostgreSQL admin username & password
- JWT secret key
- MCP Gateway URL pools
- Custom domains (optional)

### Option 2: Manual Deployment

```bash
cd infrastructure

# Create resource group
az group create \
  --name mcp-prod-rg \
  --location eastus

# Deploy Bicep template
az deployment group create \
  --name mcp-deployment \
  --resource-group mcp-prod-rg \
  --template-file main.bicep \
  --parameters \
    projectName='mcp' \
    environment='prod' \
    postgresAdminUsername='mcpadmin' \
    postgresAdminPassword='<SECURE_PASSWORD>' \
    jwtSecret='<SECURE_JWT_SECRET>' \
    mcpGatewayUrlPools='domain1.com,domain2.com' \
    backendCustomDomain='api.example.com' \
    frontendCustomDomain='example.com'

# Get deployment outputs
az deployment group show \
  --name mcp-deployment \
  --resource-group mcp-prod-rg \
  --query properties.outputs
```

---

## Configure GitHub Actions

### 1. Get Backend Publish Profile

```bash
# Navigate to Azure Portal > App Service > Your backend app
# Click "Get publish profile" or use CLI:
az webapp deployment list-publishing-profiles \
  --name mcp-prod-backend \
  --resource-group mcp-prod-rg \
  --xml > publish-profile.xml
```

Copy the entire contents of `publish-profile.xml`.

### 2. Get Static Web App Deployment Token

```bash
az staticwebapp secrets list \
  --name mcp-prod-frontend \
  --resource-group mcp-prod-rg \
  --query properties.apiKey -o tsv
```

### 3. Add GitHub Secrets

Go to your GitHub repository:
**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value | How to Get |
|------------|-------|------------|
| `AZURE_WEBAPP_PUBLISH_PROFILE` | XML content | From step 1 above |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Token string | From step 2 above |
| `AZURE_RESOURCE_GROUP` | `mcp-prod-rg` | Your resource group name |
| `VITE_API_BASE_URL` | `https://api.example.com` | Your backend URL |

### 4. Update Workflow Files

Update the App Service name in `.github/workflows/deploy-backend.yml`:

```yaml
env:
  AZURE_WEBAPP_NAME: mcp-prod-backend  # Change to your actual name
```

### 5. Trigger Deployment

```bash
# Make a commit and push to main branch
git add .
git commit -m "Configure Azure deployment"
git push origin main
```

GitHub Actions will automatically deploy both applications.

---

## Configure Custom Domains & DNS

### 1. Add DNS Records

**For Backend (api.example.com):**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | api | mcp-prod-backend.azurewebsites.net | 3600 |

**For Frontend (example.com):**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | @ or www | \<static-web-app-url\>.azurestaticapps.net | 3600 |

*Note: Static Web App URL is shown in deployment outputs or Azure Portal*

### 2. Wait for DNS Propagation

Check propagation status:
```bash
# Check backend DNS
nslookup api.example.com

# Check frontend DNS
nslookup example.com
```

DNS typically propagates within 15 minutes to 48 hours.

### 3. Configure Custom Domain in Azure

**Backend Custom Domain:**

```bash
# Add custom domain to App Service
az webapp config hostname add \
  --webapp-name mcp-prod-backend \
  --resource-group mcp-prod-rg \
  --hostname api.example.com

# Enable HTTPS (Azure provides free SSL certificate)
az webapp config ssl bind \
  --name mcp-prod-backend \
  --resource-group mcp-prod-rg \
  --certificate-thumbprint auto \
  --ssl-type SNI
```

Or via Azure Portal:
1. Go to App Service → Custom domains
2. Click "Add custom domain"
3. Enter `api.example.com` and validate
4. Add binding
5. Enable "HTTPS Only" in Configuration → General settings

**Frontend Custom Domain:**

```bash
# Add custom domain to Static Web App
az staticwebapp hostname set \
  --name mcp-prod-frontend \
  --resource-group mcp-prod-rg \
  --hostname example.com
```

Or via Azure Portal:
1. Go to Static Web App → Custom domains
2. Click "Add"
3. Enter `example.com`
4. Follow validation steps
5. SSL certificate is automatically provisioned

### 4. Update Frontend Environment Variable

Update the GitHub Secret `VITE_API_BASE_URL` to use your custom domain:

```
VITE_API_BASE_URL=https://api.example.com
```

Then redeploy frontend:
```bash
git commit --allow-empty -m "Update API base URL"
git push origin main
```

---

## Post-Deployment Configuration

### 1. Run Database Migrations

SSH into the backend App Service:

```bash
az webapp ssh \
  --name mcp-prod-backend \
  --resource-group mcp-prod-rg
```

Inside the SSH session:
```bash
cd /home/site/wwwroot
source antenv/bin/activate
alembic upgrade head
exit
```

Or use Azure Portal: App Service → SSH → Go!

### 2. Configure CORS (if needed)

The backend already has CORS configured in `main.py`. Update allowed origins:

```python
allowed_origins = [
    "https://example.com",
    "https://www.example.com",
    "https://your-static-webapp.azurestaticapps.net",
]
```

### 3. Update Environment Variables

Add/update additional environment variables in Azure Portal:
**App Service** → **Configuration** → **Application settings**

Common variables:
- `OPENAI_API_KEY` (if using OpenAI integrations)
- `ALLOWED_ORIGINS` (for CORS)
- Custom source configurations

### 4. Enable Health Checks

Health check is already configured at `/api/v1/checks`.

Verify in Azure Portal:
**App Service** → **Health check** → Set path to `/api/v1/checks`

### 5. Configure Monitoring

Application Insights is automatically configured. View in Azure Portal:
**Application Insights** → **mcp-prod-insights**

Key metrics to monitor:
- Request response time
- Failed requests
- Database connection pool
- Custom events from application

---

## Monitoring & Troubleshooting

### View Logs

**Backend Logs:**
```bash
# Stream logs in real-time
az webapp log tail \
  --name mcp-prod-backend \
  --resource-group mcp-prod-rg

# Download logs
az webapp log download \
  --name mcp-prod-backend \
  --resource-group mcp-prod-rg \
  --log-file backend-logs.zip
```

Or via Azure Portal: App Service → Log stream

**Frontend Logs:**

Static Web Apps don't have traditional logs. Check:
- GitHub Actions build logs for deployment issues
- Browser console for runtime errors
- Application Insights for user telemetry

### Common Issues

#### 1. Backend Not Starting

**Check:**
```bash
az webapp log tail --name mcp-prod-backend --resource-group mcp-prod-rg
```

**Common causes:**
- Missing environment variables
- Database connection failure
- Python dependency errors

**Fix:**
- Verify all environment variables are set
- Check PostgreSQL firewall allows Azure services
- Ensure `startup.sh` is executable

#### 2. Database Connection Errors

**Verify connection string:**
```bash
az webapp config appsettings list \
  --name mcp-prod-backend \
  --resource-group mcp-prod-rg \
  --query "[?name=='DATABASE_URL'].value" -o tsv
```

**Check PostgreSQL firewall:**
```bash
az postgres flexible-server firewall-rule list \
  --resource-group mcp-prod-rg \
  --name mcp-prod-db-server
```

#### 3. Frontend API Calls Failing

**Check:**
- CORS configuration in backend
- `VITE_API_BASE_URL` is correct in GitHub Secrets
- Custom domain SSL certificate is valid
- Network tab in browser dev tools

#### 4. GitHub Actions Failing

**Backend deployment:**
- Verify `AZURE_WEBAPP_PUBLISH_PROFILE` secret is correct
- Check workflow logs in GitHub Actions tab
- Ensure Python version matches (3.12)

**Frontend deployment:**
- Verify `AZURE_STATIC_WEB_APPS_API_TOKEN` is correct
- Check build output in workflow logs
- Verify `output_location: "dist"` matches Vite config

### Restart Services

```bash
# Restart backend
az webapp restart \
  --name mcp-prod-backend \
  --resource-group mcp-prod-rg

# Static Web Apps don't need restart (served from CDN)
```

---

## Cost Estimation

### Monthly Costs (USD, as of 2025)

| Service | Tier | Monthly Cost |
|---------|------|-------------|
| **App Service Plan** | B1 (Basic) | ~$13 |
| **Static Web App** | Free tier | $0 (up to 100GB bandwidth) |
| **PostgreSQL Flexible Server** | B1ms (Burstable) | ~$12 |
| **Application Insights** | Pay-as-you-go | ~$2-5 (low traffic) |
| **Log Analytics** | Pay-as-you-go | ~$1-3 |
| **Bandwidth** | Outbound | ~$1-5 (varies) |
| **Total Estimated** | | **~$30-40/month** |

### Scaling Options

**To reduce costs:**
- Use Free tier for PostgreSQL (limited performance)
- Reduce App Service Plan to Free F1 (limited features)
- Disable Application Insights (not recommended)

**To increase capacity:**
- Scale up App Service Plan to S1/P1V2 ($70-150/month)
- Enable PostgreSQL high availability (+$12/month)
- Scale out with multiple instances ($13/instance)

### Cost Optimization Tips

1. **Enable auto-shutdown** for non-prod environments
2. **Use reserved instances** for production (save up to 60%)
3. **Set up cost alerts** in Azure Portal
4. **Monitor Application Insights** data ingestion (can get expensive)

---

## Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Static Web Apps Documentation](https://docs.microsoft.com/en-us/azure/static-web-apps/)
- [Azure Database for PostgreSQL Documentation](https://docs.microsoft.com/en-us/azure/postgresql/)
- [GitHub Actions for Azure](https://github.com/Azure/actions)

---

## Support & Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Review Application Insights for errors
   - Check health check endpoint status

2. **Monthly:**
   - Review and optimize costs
   - Update dependencies (Python packages, npm packages)
   - Check for security updates

3. **Quarterly:**
   - Review and update infrastructure (Bicep template)
   - Perform disaster recovery testing
   - Review access permissions

### Backup Strategy

**Database Backups:**
- Automated daily backups (7-day retention)
- Manual backup before major changes:
  ```bash
  az postgres flexible-server backup create \
    --resource-group mcp-prod-rg \
    --name mcp-prod-db-server \
    --backup-name manual-backup-$(date +%Y%m%d)
  ```

**Application Code:**
- All code is in Git (GitHub)
- Tag releases for easy rollback
- Keep infrastructure code in version control

---

## CI/CD Pipeline Details

### Backend Deployment Flow

1. **Trigger:** Push to `main` branch with changes in `mcp-server-python/`
2. **Build:**
   - Checkout code
   - Set up Python 3.12
   - Install dependencies
   - Create deployment package
3. **Deploy:**
   - Upload to Azure App Service
   - Run startup script
   - Execute database migrations
4. **Verify:** Health check at `/api/v1/checks`

### Frontend Deployment Flow

1. **Trigger:** Push to `main` branch with changes in `mcp-admin-ui/`
2. **Build:**
   - Checkout code
   - Install npm dependencies
   - Run `npm run build`
   - Generate static assets
3. **Deploy:**
   - Upload to Azure Static Web Apps
   - Deploy to global CDN
4. **Verify:** Access frontend URL

### Rollback Strategy

**Backend rollback:**
```bash
# List deployment history
az webapp deployment list \
  --name mcp-prod-backend \
  --resource-group mcp-prod-rg

# Redeploy previous version from GitHub
# Option 1: Revert commit and push
git revert <commit-hash>
git push origin main

# Option 2: Deploy specific commit
git checkout <previous-commit>
git push origin main --force
```

**Frontend rollback:**
- Static Web Apps keeps previous deployments
- Rollback via Azure Portal: Static Web App → Deployments → Select version

---

## Security Checklist

- [ ] All secrets are stored in GitHub Secrets (not in code)
- [ ] HTTPS enforced on all domains
- [ ] PostgreSQL firewall configured (Azure services only)
- [ ] JWT secret is strong and unique
- [ ] Application Insights data retention configured
- [ ] Custom domains have valid SSL certificates
- [ ] CORS configured with specific origins (not `*`)
- [ ] Database connection uses SSL
- [ ] Sensitive environment variables not logged
- [ ] Health check endpoint doesn't expose sensitive data

---

## Next Steps After Deployment

1. **Test all functionality:**
   - User authentication (signup/signin)
   - Source CRUD operations
   - MCP Server CRUD operations
   - Search and fetch operations

2. **Configure monitoring alerts:**
   - High error rate
   - Slow response times
   - Database connection failures
   - High CPU/memory usage

3. **Set up custom email domain** (optional):
   - Configure SendGrid or Azure Communication Services
   - Update email templates

4. **Enable advanced features:**
   - Azure Front Door for global CDN
   - Azure Key Vault for secret management
   - Azure AD authentication
   - Rate limiting and throttling

5. **Documentation:**
   - Update API documentation
   - Create user guides
   - Document environment-specific configurations

---

**Deployment Complete! 🚀**

Your MCP application is now running on Azure with automated CI/CD. Every push to the `main` branch will automatically deploy changes to production.
