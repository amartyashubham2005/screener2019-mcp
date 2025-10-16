# Deployment Status - screener2019-mcp

**Date:** October 17, 2025
**Environment:** Development
**Status:** ✅ Infrastructure Deployed

---

## 📦 Azure Resources

| Resource | Name | Status |
|----------|------|--------|
| **Resource Group** | screener2019-mcp-dev-rg | ✅ Created |
| **Backend App Service** | screener2019-mcp-dev-backend | ✅ Created |
| **Frontend Static Web App** | screener2019-mcp-dev-frontend | ✅ Created |
| **PostgreSQL Server** | screener2019-mcp-dev-db-server | ✅ Created |
| **Database** | mcp_database | ✅ Created |
| **Application Insights** | screener2019-mcp-dev-insights | ✅ Created |
| **Log Analytics** | screener2019-mcp-dev-logs | ✅ Created |

---

## 🌐 URLs

### Current URLs
- **Backend API:** https://screener2019-mcp-dev-backend.azurewebsites.net
- **Frontend:** https://salmon-island-0c1c66710.3.azurestaticapps.net

### Target Custom Domains
- **Backend API:** https://api.jesterbot.com
- **Frontend:** https://jesterbot.com

---

## ✅ Completed Tasks

- [x] Azure infrastructure deployed via Bicep
- [x] PostgreSQL database created
- [x] Application Insights configured
- [x] Backend App Service configured with environment variables
- [x] Static Web App created for frontend
- [x] GitHub workflow files created
- [x] Backend workflow updated with correct app name

---

## 📋 Pending Tasks

### 1. Add GitHub Secrets

Navigate to: **GitHub Repository → Settings → Secrets and variables → Actions**

Add these 4 secrets:

#### AZURE_STATIC_WEB_APPS_API_TOKEN
```
c583938641644ec9bcefe55f647f3f85ea454164fc866d04e8a8a38e47f8f99a03-b03896d4-173b-4819-9955-69053ddfbc6401011000c1c66710
```

#### AZURE_RESOURCE_GROUP
```
screener2019-mcp-dev-rg
```

#### VITE_API_BASE_URL
```
https://api.jesterbot.com
```

#### AZURE_WEBAPP_PUBLISH_PROFILE
Get from Azure Portal:
1. Go to App Service → screener2019-mcp-dev-backend
2. Click "Download publish profile"
3. Copy entire XML content
4. Or use this command:
```bash
az webapp deployment list-publishing-profiles \
  --name screener2019-mcp-dev-backend \
  --resource-group screener2019-mcp-dev-rg \
  --xml
```

---

### 2. Configure DNS

Add these CNAME records at your DNS provider (where you manage jesterbot.com):

#### Backend API (api.jesterbot.com)
```
Type: CNAME
Name: api
Value: screener2019-mcp-dev-backend.azurewebsites.net
TTL: 3600
```

#### Frontend (jesterbot.com)
```
Type: CNAME
Name: @ (or www)
Value: salmon-island-0c1c66710.3.azurestaticapps.net
TTL: 3600
```

**Note:** DNS propagation typically takes 15 minutes to 48 hours.

---

### 3. Enable Custom Domains (After DNS Propagation)

#### Backend Custom Domain
```bash
az webapp config hostname add \
  --webapp-name screener2019-mcp-dev-backend \
  --resource-group screener2019-mcp-dev-rg \
  --hostname api.jesterbot.com

# Enable HTTPS
az webapp config ssl bind \
  --name screener2019-mcp-dev-backend \
  --resource-group screener2019-mcp-dev-rg \
  --certificate-thumbprint auto \
  --ssl-type SNI
```

#### Frontend Custom Domain
1. Go to Azure Portal
2. Navigate to: Static Web Apps → screener2019-mcp-dev-frontend
3. Click "Custom domains"
4. Click "Add"
5. Enter: jesterbot.com
6. Follow validation steps
7. SSL certificate will be automatically provisioned

---

### 4. Deploy Application Code

```bash
# Commit deployment configuration
git add .
git commit -m "Configure Azure deployment for dev environment"
git push origin main
```

GitHub Actions will automatically:
- Build and deploy the backend to App Service
- Build and deploy the frontend to Static Web App

---

### 5. Run Database Migrations

After the first deployment completes:

```bash
# SSH into backend app
az webapp ssh \
  --name screener2019-mcp-dev-backend \
  --resource-group screener2019-mcp-dev-rg
```

Inside SSH session:
```bash
cd /home/site/wwwroot
source antenv/bin/activate
alembic upgrade head
exit
```

---

### 6. Update CORS Configuration

Update allowed origins in `mcp-server-python/main.py`:

```python
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://jesterbot.com",
    "https://www.jesterbot.com",
    "https://salmon-island-0c1c66710.3.azurestaticapps.net",
]
```

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] Backend health check: https://screener2019-mcp-dev-backend.azurewebsites.net/api/v1/checks
  - Should return: `{"status": "healthy", ...}`
- [ ] Frontend loads: https://salmon-island-0c1c66710.3.azurestaticapps.net
- [ ] GitHub Actions workflows pass
- [ ] Database migrations completed successfully
- [ ] Can sign up / sign in
- [ ] Can create sources
- [ ] Can create MCP servers
- [ ] Custom domain DNS resolves correctly (after propagation)
- [ ] HTTPS works on custom domains

---

## 🔐 Security Notes

- All secrets are stored in GitHub Secrets (not in code)
- HTTPS enforced on all services
- PostgreSQL firewall configured to allow Azure services only
- Application Insights data retention: 30 days
- JWT secret configured for authentication
- Cookie-based authentication with HttpOnly flag

---

## 📊 Monitoring

### Application Insights
- Portal: Azure Portal → screener2019-mcp-dev-insights
- Connection string configured in backend app settings

### Logs
```bash
# Stream backend logs
az webapp log tail \
  --name screener2019-mcp-dev-backend \
  --resource-group screener2019-mcp-dev-rg

# Download logs
az webapp log download \
  --name screener2019-mcp-dev-backend \
  --resource-group screener2019-mcp-dev-rg \
  --log-file backend-logs.zip
```

---

## 💰 Cost Estimate

| Service | Tier | Monthly Cost |
|---------|------|-------------|
| App Service Plan | B1 (Basic) | ~$13 |
| Static Web App | Free | $0 |
| PostgreSQL Flexible Server | B1ms (Burstable) | ~$12 |
| Application Insights | Pay-as-you-go | ~$2-5 |
| Log Analytics | Pay-as-you-go | ~$1-3 |
| **Total** | | **~$28-33/month** |

---

## 🆘 Troubleshooting

### Backend not starting
```bash
az webapp log tail --name screener2019-mcp-dev-backend --resource-group screener2019-mcp-dev-rg
```

### Database connection issues
```bash
# Check database connection string
az webapp config appsettings list \
  --name screener2019-mcp-dev-backend \
  --resource-group screener2019-mcp-dev-rg \
  --query "[?name=='DATABASE_URL']"

# Test database connectivity
az postgres flexible-server connect \
  --name screener2019-mcp-dev-db-server \
  --admin-user <username> \
  --database mcp_database
```

### Frontend build failing
- Check GitHub Actions logs
- Verify `VITE_API_BASE_URL` is set correctly
- Ensure build output is in `dist/` directory

---

## 📚 Resources

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Complete deployment guide
- [QUICKSTART.md](./QUICKSTART.md) - Quick start guide
- [Azure Portal](https://portal.azure.com)
- [GitHub Actions](../../actions)

---

## 🎯 Next Steps After Going Live

1. **Set up staging environment** - Repeat deployment with `environment: staging`
2. **Configure monitoring alerts** - Set up alerts for errors and performance
3. **Enable backup strategy** - Configure automated database backups
4. **Set up Azure Front Door** - For global CDN and WAF (optional)
5. **Configure rate limiting** - Protect APIs from abuse
6. **Set up custom email domain** - For transactional emails
7. **Enable Azure AD authentication** - For enterprise SSO (optional)

---

**Last Updated:** October 17, 2025
**Deployment Script Version:** 1.0
**Bicep Template Version:** 1.0
