# 🚀 Quick Start Guide - Azure Deployment with SSO

## TL;DR - One Command Deployment

```bash
cd infrastructure
./deploy-with-sso.sh
```

That's it! The script will guide you through:
1. ✅ Deploying Azure infrastructure
2. ✅ Creating Azure AD app for SSO
3. ✅ Configuring everything automatically

## 📋 What You'll Need

Before running the script, have these ready:

### Required Information
- [ ] **Azure Account** (with admin access)
- [ ] **Project Name** (e.g., "screener2019-mcp")
- [ ] **Environment** (dev/staging/prod)
- [ ] **Database Password** (min 8 characters)
- [ ] **JWT Secret** (for authentication)
- [ ] **MCP Gateway URLs** (comma-separated domains)

### Optional (for custom domains)
- [ ] **Backend Domain** (e.g., api.example.com)
- [ ] **Frontend Domain** (e.g., example.com)

## 🎯 Step-by-Step

### 1. Install Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install jq (JSON processor)
sudo apt-get install jq
```

### 2. Login to Azure

```bash
az login
```

### 3. Run Deployment

```bash
cd infrastructure
./deploy-with-sso.sh
```

### 4. Answer the Prompts

The script will ask you:

```
Enter project name (default: screener2019-mcp): [YOUR_PROJECT]
Enter environment (dev/staging/prod, default: dev): dev
Enter Azure region (default: centralus): centralus
Enter PostgreSQL admin username: admin
Enter PostgreSQL admin password: [SECURE_PASSWORD]
Enter JWT secret key: [RANDOM_STRING]
Enter MCP Gateway URL pools: domain1.com,domain2.com
```

### 5. Wait for Completion

The script will:
- ⏳ Deploy infrastructure (~5-10 minutes)
- ⏳ Create Azure AD app (~1 minute)
- ⏳ Configure settings (~30 seconds)

### 6. Save the Outputs

Two files are created with all your credentials:
- `deployment-outputs-latest.txt` - Infrastructure details
- `azure-ad-app-latest.txt` - SSO credentials

**🔒 Keep these files secure! They contain secrets.**

## 📝 Post-Deployment

### 1. Add Environment Variables to Frontend

Create `.env` in `mcp-admin-ui/`:

```bash
# From deployment-outputs-latest.txt
VITE_API_BASE_URL=https://your-backend.azurewebsites.net

# From azure-ad-app-latest.txt
VITE_AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789abc
VITE_AZURE_TENANT_ID=87654321-4321-4321-4321-cba987654321
VITE_AZURE_REDIRECT_URI=http://localhost:3000/auth/callback
```

### 2. Add GitHub Secrets

Go to GitHub → Settings → Secrets and variables → Actions

Add these secrets (values from `deployment-outputs-latest.txt`):
- `AZURE_STATIC_WEB_APPS_API_TOKEN`
- `AZURE_RESOURCE_GROUP`
- `VITE_API_BASE_URL`
- `AZURE_WEBAPP_PUBLISH_PROFILE`

Add these secrets (values from `azure-ad-app-latest.txt`):
- `AZURE_AD_CLIENT_ID`
- `AZURE_AD_TENANT_ID`
- `AZURE_AD_CLIENT_SECRET`

### 3. Deploy Your Code

```bash
git add .
git commit -m "Configure Azure deployment with SSO"
git push origin main
```

GitHub Actions will automatically deploy to Azure!

### 4. Run Database Migrations

SSH into your backend:

```bash
# Get app name from deployment-outputs-latest.txt
az webapp ssh --name YOUR_BACKEND_APP_NAME --resource-group YOUR_RESOURCE_GROUP

# Inside the SSH session:
cd /home/site/wwwroot
source antenv/bin/activate
alembic upgrade head
```

### 5. Grant Admin Consent (Important!)

1. Open Azure Portal
2. Go to Azure AD → App registrations
3. Find your app (e.g., "screener2019-mcp-sso-dev")
4. Go to API permissions
5. Click **"Grant admin consent for [Your Org]"**

This allows users to sign in with Microsoft.

## ✅ Verify Deployment

### Test Backend
```bash
curl https://your-backend.azurewebsites.net/api/v1/checks
```

Should return:
```json
{
  "status": "healthy",
  "service": "modular-mcp-server"
}
```

### Test Frontend
Open browser to: `https://your-frontend.azurestaticapps.net`

### Test SSO Login
1. Go to `/signin`
2. Click "Sign in with Microsoft"
3. You should be redirected to Microsoft login
4. After login, you should be back at your app

## 🆘 Quick Fixes

### "App registration failed"
**Solution:** You need Azure AD admin privileges
```bash
# Ask your Azure AD admin to run:
./setup-azure-ad-app.sh
```

### "Deployment failed"
**Solution:** Check if resource group already exists
```bash
# Delete resource group and try again:
az group delete --name YOUR_RESOURCE_GROUP --yes
./deploy-with-sso.sh
```

### "Client secret expired"
**Solution:** Create new secret
```bash
./setup-azure-ad-app.sh
# Choose "Update existing app"
```

### "Can't log in with SSO"
**Solution:** Grant admin consent
- Azure Portal → Azure AD → App registrations → Your App
- API permissions → Grant admin consent

## 📚 More Information

- **Full Documentation:** [DEPLOYMENT_README.md](./DEPLOYMENT_README.md)
- **Infrastructure Only:** Run `./deploy.sh`
- **SSO Only:** Run `./setup-azure-ad-app.sh`
- **Update Existing:** Scripts are idempotent - safe to re-run

## 💡 Pro Tips

1. **Use descriptive project names:** They'll be part of your URLs
2. **Keep deployment outputs:** Save those text files securely
3. **Use separate environments:** dev, staging, prod with different Azure AD apps
4. **Set up monitoring:** Check Application Insights in Azure Portal
5. **Enable auto-scaling:** For production, upgrade to Standard tier

## 🎉 Success Checklist

After deployment, you should have:

- ✅ Backend API running on Azure
- ✅ Frontend deployed to Azure Static Web Apps
- ✅ PostgreSQL database created
- ✅ Azure AD app registered
- ✅ SSO working
- ✅ All secrets securely stored
- ✅ GitHub Actions configured for CI/CD

**Total Time:** ~15-20 minutes (mostly waiting for Azure)

---

Need help? Check [DEPLOYMENT_README.md](./DEPLOYMENT_README.md) for detailed docs!
