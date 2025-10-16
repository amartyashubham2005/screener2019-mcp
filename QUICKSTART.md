# Quick Start - Azure Deployment

Deploy your MCP application to Azure in under 30 minutes.

## Prerequisites

- Azure subscription
- Azure CLI installed ([install here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- GitHub repository
- Domain name (e.g., example.com)

## Step-by-Step Deployment

### 1. Deploy Infrastructure (5 minutes)

```bash
# Clone your repository
git clone <your-repo>
cd mcp

# Login to Azure
az login

# Run deployment script
cd infrastructure
./deploy.sh
```

Follow the prompts to enter:
- Project name (e.g., `mcp`)
- Environment (`prod`)
- PostgreSQL username/password
- JWT secret (generate a secure random string)
- MCP Gateway URLs (comma-separated)
- Your custom domains

The script will:
- Create all Azure resources
- Output URLs and tokens
- Save configuration to `deployment-outputs.txt`

### 2. Configure GitHub Secrets (5 minutes)

Go to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add these secrets (values from deployment outputs):

```
AZURE_WEBAPP_PUBLISH_PROFILE
AZURE_STATIC_WEB_APPS_API_TOKEN
AZURE_RESOURCE_GROUP
VITE_API_BASE_URL
```

### 3. Configure DNS (5 minutes)

Add these DNS records at your domain provider:

**Backend (api.example.com):**
```
Type: CNAME
Name: api
Value: <your-backend-name>.azurewebsites.net
```

**Frontend (example.com):**
```
Type: CNAME
Name: @
Value: <your-static-webapp>.azurestaticapps.net
```

### 4. Deploy Code (5 minutes)

```bash
# Update workflow file with your backend app name
# Edit .github/workflows/deploy-backend.yml
nano .github/workflows/deploy-backend.yml

# Update this line:
# AZURE_WEBAPP_NAME: your-backend-name

# Commit and push
git add .
git commit -m "Configure Azure deployment"
git push origin main
```

GitHub Actions will automatically deploy both applications.

### 5. Run Database Migrations (2 minutes)

After first deployment:

```bash
az webapp ssh --name <your-backend-name> --resource-group <your-rg>
```

Inside SSH:
```bash
cd /home/site/wwwroot
source antenv/bin/activate
alembic upgrade head
exit
```

### 6. Configure Custom Domains (5 minutes)

After DNS propagates (wait 15-30 minutes):

**Backend:**
```bash
az webapp config hostname add \
  --webapp-name <your-backend-name> \
  --resource-group <your-rg> \
  --hostname api.example.com
```

**Frontend:**
- Go to Azure Portal → Static Web App
- Click "Custom domains" → "Add"
- Enter your domain and validate

### 7. Test Your Application

Open your browser:
- Frontend: `https://example.com`
- Backend API: `https://api.example.com/api/v1/checks`

## Verification Checklist

- [ ] Backend health check returns `{"status": "healthy"}`
- [ ] Frontend loads successfully
- [ ] Can sign up / sign in
- [ ] Can create sources
- [ ] Can create MCP servers
- [ ] HTTPS works on both domains
- [ ] GitHub Actions show successful deployments

## Troubleshooting

**Backend not starting?**
```bash
az webapp log tail --name <your-backend-name> --resource-group <your-rg>
```

**Frontend API calls failing?**
- Check CORS settings in `mcp-server-python/main.py`
- Verify `VITE_API_BASE_URL` secret is correct
- Check browser console for errors

**DNS not working?**
```bash
nslookup api.example.com
nslookup example.com
```

## What's Next?

- Update allowed CORS origins in backend
- Configure monitoring alerts
- Set up staging environment
- Review security settings

For detailed information, see [DEPLOYMENT.md](./DEPLOYMENT.md)

## Cost

Estimated monthly cost: **$30-40**
- App Service B1: $13
- PostgreSQL B1ms: $12
- Static Web App: Free
- Other services: $5-15

## Support

Issues? Check:
1. [DEPLOYMENT.md](./DEPLOYMENT.md) - Full deployment guide
2. [GitHub Actions logs](../../actions) - Deployment status
3. Azure Portal - Resource monitoring
4. Application Insights - Error tracking

---

**Congratulations!** Your application is now live on Azure with automated CI/CD. 🎉
