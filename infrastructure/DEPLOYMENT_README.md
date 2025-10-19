# Azure Deployment Scripts

This directory contains scripts to automate the complete deployment of the MCP Server application to Azure, including infrastructure provisioning and Azure AD SSO configuration.

## 📁 Scripts Overview

### 1. `deploy.sh` - Infrastructure Deployment
Deploys core Azure resources using Bicep templates:
- Azure App Service (Backend)
- Azure Static Web Apps (Frontend)
- Azure Database for PostgreSQL
- Application Insights
- Resource Group

**Usage:**
```bash
./deploy.sh
```

### 2. `setup-azure-ad-app.sh` - Azure AD App Registration
Creates/updates Azure AD app registration for SSO authentication:
- Registers application in Azure AD
- Configures redirect URIs
- Sets up Microsoft Graph API permissions
- Generates client secret
- Creates service principal

**Usage:**
```bash
./setup-azure-ad-app.sh
```

### 3. `deploy-with-sso.sh` - Complete Deployment (Recommended)
Combines infrastructure deployment with Azure AD SSO setup in a single workflow:
- Runs infrastructure deployment
- Creates Azure AD app registration
- Configures App Service with SSO credentials
- Provides complete deployment summary

**Usage:**
```bash
./deploy-with-sso.sh
```

## 🚀 Quick Start

### Prerequisites

1. **Azure CLI** installed:
   ```bash
   # macOS
   brew install azure-cli

   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

   # Windows
   # Download from: https://aka.ms/installazurecliwindows
   ```

2. **jq** (JSON processor):
   ```bash
   # macOS
   brew install jq

   # Linux
   sudo apt-get install jq

   # Windows (via Chocolatey)
   choco install jq
   ```

3. **Azure Account** with appropriate permissions:
   - Contributor role on subscription
   - Application Administrator role in Azure AD (for app registration)

### First-Time Deployment

1. **Login to Azure:**
   ```bash
   az login
   ```

2. **Run the complete deployment:**
   ```bash
   cd infrastructure
   ./deploy-with-sso.sh
   ```

3. **Follow the prompts to enter:**
   - Project name (default: screener2019-mcp)
   - Environment (dev/staging/prod)
   - Azure region
   - Database credentials
   - JWT secret
   - MCP Gateway URLs
   - Backend/Frontend URLs

4. **Review the outputs** saved to:
   - `deployment-outputs-latest.txt` - Infrastructure details
   - `azure-ad-app-latest.txt` - Azure AD SSO credentials

### Updating Existing Deployment

The scripts are **idempotent** - they can be run multiple times safely:

- If resources exist, you'll be prompted to skip or update
- Azure AD app will be updated with new redirect URIs if needed
- Existing client secrets are preserved (new ones are appended)

## 📋 Deployment Outputs

### Infrastructure Outputs (`deployment-outputs-latest.txt`)

Contains:
- Backend and Frontend URLs
- App Service names
- Database connection details
- GitHub secrets configuration
- DNS configuration (if custom domains used)

**Example:**
```
Backend App Name: screener2019-mcp-dev-backend
Backend URL: https://screener2019-mcp-dev-backend.azurewebsites.net
Frontend URL: https://nice-tree-0abc123.2.azurestaticapps.net
PostgreSQL Server: screener2019-mcp-dev-postgres.postgres.database.azure.com
```

### Azure AD Outputs (`azure-ad-app-latest.txt`)

Contains:
- Application (Client) ID
- Directory (Tenant) ID
- Client Secret
- Redirect URIs
- Environment variables for backend/frontend

**Example:**
```
Application (client) ID: 12345678-1234-1234-1234-123456789abc
Directory (tenant) ID: 87654321-4321-4321-4321-cba987654321
Client Secret: abC~defGHI1234567890JKLmnoPQRST
```

## 🔐 Security Best Practices

### Client Secret Management

1. **Never commit secrets to version control**
   - Add `*-latest.txt` and `deployment-outputs-*.txt` to `.gitignore`
   - Store secrets in Azure Key Vault for production

2. **Rotate secrets before expiration**
   - Default expiration: 2 years
   - Set calendar reminder to rotate secrets
   - Use `setup-azure-ad-app.sh` to create new secrets

3. **Use environment-specific apps**
   - Separate Azure AD apps for dev/staging/prod
   - Different client secrets per environment
   - Isolated redirect URIs

### Azure AD Permissions

The app requests these delegated permissions from Microsoft Graph:
- `User.Read` - Read basic user profile
- `email` - Access user's email address
- `openid` - Sign in users
- `profile` - View basic profile info

**Admin consent** is required before users can sign in.

## 🏗️ Architecture Details

### Infrastructure Components

```
┌─────────────────────────────────────────────────────┐
│                  Azure Subscription                  │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────────────────────────────────┐   │
│  │         Resource Group                       │   │
│  │  (screener2019-mcp-dev-rg)                  │   │
│  ├─────────────────────────────────────────────┤   │
│  │                                               │   │
│  │  ┌──────────────────┐  ┌─────────────────┐ │   │
│  │  │ App Service (B1) │  │ PostgreSQL      │ │   │
│  │  │ Backend API      │──│ Flexible Server │ │   │
│  │  │ Python/FastAPI   │  │ (B1ms)          │ │   │
│  │  └──────────────────┘  └─────────────────┘ │   │
│  │                                               │   │
│  │  ┌──────────────────┐  ┌─────────────────┐ │   │
│  │  │ Static Web Apps  │  │ Application     │ │   │
│  │  │ Frontend (Free)  │  │ Insights        │ │   │
│  │  │ React/Vite       │  │ Monitoring      │ │   │
│  │  └──────────────────┘  └─────────────────┘ │   │
│  │                                               │   │
│  └─────────────────────────────────────────────┘   │
│                                                       │
└─────────────────────────────────────────────────────┘

         ↓ SSO Authentication via ↓

┌─────────────────────────────────────────────────────┐
│              Azure Active Directory                  │
├─────────────────────────────────────────────────────┤
│  App Registration: screener2019-mcp-sso-dev         │
│  - OAuth 2.0 Authorization Code Flow                │
│  - OpenID Connect                                     │
│  - Microsoft Graph API Permissions                   │
└─────────────────────────────────────────────────────┘
```

### Authentication Flow

```
User Browser                    Frontend                    Backend                    Azure AD
     │                             │                           │                           │
     │  1. Click "Sign in with MS" │                           │                           │
     ├─────────────────────────────>                           │                           │
     │                             │                           │                           │
     │  2. Redirect to /auth/azure/login                       │                           │
     │                             ├──────────────────────────>│                           │
     │                             │                           │                           │
     │  3. Redirect to Azure AD    │                           │  4. Authorize App        │
     │<────────────────────────────┴───────────────────────────┼─────────────────────────>│
     │                                                          │                           │
     │  5. Sign in with Microsoft credentials                  │                           │
     ├──────────────────────────────────────────────────────────────────────────────────>│
     │                                                          │                           │
     │  6. Redirect to callback with auth code                 │                           │
     │<─────────────────────────────────────────────────────────────────────────────────┤
     │                             │                           │                           │
     │  7. Send code to backend    │                           │                           │
     ├─────────────────────────────┼──────────────────────────>│                           │
     │                             │                           │                           │
     │                             │                           │  8. Exchange code for token
     │                             │                           ├──────────────────────────>│
     │                             │                           │                           │
     │                             │                           │  9. Get user profile     │
     │                             │                           │<──────────────────────────┤
     │                             │                           │                           │
     │  10. Return JWT token       │                           │                           │
     │<────────────────────────────┴───────────────────────────┤                           │
     │                             │                           │                           │
     │  11. Store JWT, redirect to app                         │                           │
     │                             │                           │                           │
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "az: command not found"
**Solution:** Install Azure CLI
```bash
# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### 2. "jq: command not found"
**Solution:** Install jq
```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq
```

#### 3. "Insufficient privileges to complete the operation"
**Solution:** You need admin privileges to:
- Create app registrations (Application Administrator role)
- Grant admin consent (Global Administrator or Privileged Role Administrator)

Contact your Azure AD admin or request role assignment.

#### 4. "The client secret has expired"
**Solution:** Create a new secret:
```bash
./setup-azure-ad-app.sh
# Select "Update existing app"
# New secret will be appended
```

#### 5. "Redirect URI mismatch"
**Solution:** Update redirect URIs:
1. Run `./setup-azure-ad-app.sh`
2. Enter correct Backend/Frontend URLs
3. Script will update the app registration

#### 6. "Failed to grant admin consent"
**Solution:** Grant manually in Azure Portal:
1. Go to Azure AD → App registrations
2. Select your app
3. Go to API permissions
4. Click "Grant admin consent for [Your Org]"

### Debug Mode

Enable verbose output:
```bash
set -x  # Enable debug mode
./deploy-with-sso.sh
set +x  # Disable debug mode
```

### Logs Location

- Script execution logs: Console output
- Deployment details: `deployment-outputs-<timestamp>.txt`
- Azure AD config: `azure-ad-app-<timestamp>.txt`
- Latest symlinks: `*-latest.txt`

## 📚 Additional Resources

### Azure Documentation
- [Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Static Web Apps](https://docs.microsoft.com/en-us/azure/static-web-apps/)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/en-us/azure/postgresql/)
- [Azure AD App Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)

### OAuth 2.0 & OpenID Connect
- [Microsoft Identity Platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [OAuth 2.0 Authorization Code Flow](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [OpenID Connect on Microsoft Identity Platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc)

### Security Best Practices
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)
- [Secure Application Development](https://docs.microsoft.com/en-us/azure/security/develop/)
- [Managing Application Secrets](https://docs.microsoft.com/en-us/azure/key-vault/general/overview)

## 💰 Cost Estimation

**Monthly Costs (Development Environment):**
- App Service B1: ~$13/month
- PostgreSQL Flexible Server B1ms: ~$12/month
- Static Web Apps: Free tier
- Application Insights: ~$2-5/month (depending on usage)
- **Total: ~$27-30/month**

**Production Environment (Recommended):**
- App Service P1V2: ~$75/month
- PostgreSQL Flexible Server D2s_v3: ~$85/month
- Static Web Apps Standard: ~$9/month
- Application Insights: ~$10-20/month
- **Total: ~$179-189/month**

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Azure Portal for resource status
3. Check deployment logs in `deployment-outputs-latest.txt`
4. Consult Azure documentation links

## 📝 License

This deployment configuration is part of the screener2019-mcp project.
