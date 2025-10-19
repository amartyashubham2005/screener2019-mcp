#!/bin/bash

# Complete Azure Deployment Script with SSO
# This script deploys all Azure resources and configures Azure AD for SSO

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if jq is installed (for JSON parsing in Azure AD setup)
if ! command -v jq &> /dev/null; then
    print_warning "jq is not installed. It's required for Azure AD app registration."
    print_info "Installing jq..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y jq
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install jq
    else
        print_warning "Please install jq manually: https://stedolan.github.io/jq/download/"
        print_info "Continuing without Azure AD setup..."
        SKIP_AZURE_AD=true
    fi
fi

echo ""
echo "=========================================="
print_info "Azure Deployment with SSO Integration"
echo "=========================================="
echo ""

# Configuration
print_step "1/3 Configuring deployment parameters..."

# Prompt for required parameters
read -p "Enter project name (default: screener2019-mcp): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-screener2019-mcp}

read -p "Enter environment (dev/staging/prod, default: dev): " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-dev}

read -p "Enter Azure region (default: centralus): " LOCATION
LOCATION=${LOCATION:-centralus}

read -p "Enter resource group name (default: ${PROJECT_NAME}-${ENVIRONMENT}-rg): " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-${PROJECT_NAME}-${ENVIRONMENT}-rg}

read -p "Enter PostgreSQL admin username: " POSTGRES_ADMIN_USER
if [ -z "$POSTGRES_ADMIN_USER" ]; then
    print_error "PostgreSQL admin username is required"
    exit 1
fi

read -sp "Enter PostgreSQL admin password (min 8 characters): " POSTGRES_ADMIN_PASSWORD
echo
if [ -z "$POSTGRES_ADMIN_PASSWORD" ]; then
    print_error "PostgreSQL admin password is required"
    exit 1
fi

read -sp "Enter JWT secret key (for authentication): " JWT_SECRET
echo
if [ -z "$JWT_SECRET" ]; then
    print_error "JWT secret key is required"
    exit 1
fi

read -p "Enter MCP Gateway URL pools (comma-separated, e.g., domain1.com,domain2.com): " MCP_GATEWAY_URLS
if [ -z "$MCP_GATEWAY_URLS" ]; then
    print_error "MCP Gateway URL pools are required"
    exit 1
fi

read -p "Enter backend custom domain (optional, e.g., api.example.com): " BACKEND_DOMAIN
read -p "Enter frontend custom domain (optional, e.g., example.com): " FRONTEND_DOMAIN

# Ask about Azure AD SSO setup
if [ "$SKIP_AZURE_AD" != "true" ]; then
    read -p "Do you want to configure Azure AD SSO? (y/n, default: y): " SETUP_SSO
    SETUP_SSO=${SETUP_SSO:-y}
else
    SETUP_SSO=n
fi

# Login check
print_info "Checking Azure login status..."
if ! az account show &> /dev/null; then
    print_warning "Not logged in to Azure. Logging in..."
    az login
fi

# Display current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)
print_info "Using subscription: $SUBSCRIPTION"
print_info "Using tenant: $TENANT_ID"
read -p "Is this correct? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    print_info "Available subscriptions:"
    az account list --output table
    read -p "Enter subscription ID or name: " SUB_ID
    az account set --subscription "$SUB_ID"
    TENANT_ID=$(az account show --query tenantId -o tsv)
fi

# =============================================================================
# PHASE 1: Infrastructure Deployment
# =============================================================================

print_step "2/3 Deploying Azure infrastructure..."

# Check if resource group exists
print_info "Checking for existing resource group: $RESOURCE_GROUP..."
RESOURCE_GROUP_EXISTS=$(az group exists --name "$RESOURCE_GROUP")

if [ "$RESOURCE_GROUP_EXISTS" = "true" ]; then
    print_warning "Resource group '$RESOURCE_GROUP' already exists"

    # Check for existing deployment
    LATEST_DEPLOYMENT=$(az deployment group list \
        --resource-group "$RESOURCE_GROUP" \
        --query "[0].name" -o tsv 2>/dev/null)

    if [ -n "$LATEST_DEPLOYMENT" ]; then
        print_info "Found existing deployment: $LATEST_DEPLOYMENT"

        # Get deployment state
        DEPLOYMENT_STATE=$(az deployment group show \
            --name "$LATEST_DEPLOYMENT" \
            --resource-group "$RESOURCE_GROUP" \
            --query properties.provisioningState -o tsv 2>/dev/null)

        if [ "$DEPLOYMENT_STATE" = "Succeeded" ]; then
            print_info "Resources already provisioned successfully!"
            read -p "Do you want to skip deployment and use existing resources? (y/n): " SKIP_DEPLOYMENT

            if [ "$SKIP_DEPLOYMENT" = "y" ] || [ "$SKIP_DEPLOYMENT" = "Y" ]; then
                print_info "Skipping deployment, retrieving existing resource information..."
                DEPLOYMENT_NAME="$LATEST_DEPLOYMENT"
                SKIP_DEPLOY=true
            else
                print_info "Proceeding with new deployment..."
                SKIP_DEPLOY=false
            fi
        else
            print_warning "Previous deployment state: $DEPLOYMENT_STATE"
            print_info "Proceeding with new deployment..."
            SKIP_DEPLOY=false
        fi
    else
        print_info "No previous deployments found"
        SKIP_DEPLOY=false
    fi
else
    print_info "Creating resource group: $RESOURCE_GROUP in $LOCATION..."
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --tags Project="$PROJECT_NAME" Environment="$ENVIRONMENT" ManagedBy="Bicep"
    SKIP_DEPLOY=false
fi

# Deploy Bicep template if needed
if [ "$SKIP_DEPLOY" != "true" ]; then
    print_info "Deploying Azure resources using Bicep template..."
    print_info "This may take 5-10 minutes..."

    DEPLOYMENT_NAME="${PROJECT_NAME}-deployment-$(date +%Y%m%d-%H%M%S)"

    # Deploy and capture exit code
    if az deployment group create \
        --name "$DEPLOYMENT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "$(dirname "$0")/main.bicep" \
        --parameters \
            projectName="$PROJECT_NAME" \
            environment="$ENVIRONMENT" \
            location="$LOCATION" \
            postgresAdminUsername="$POSTGRES_ADMIN_USER" \
            postgresAdminPassword="$POSTGRES_ADMIN_PASSWORD" \
            jwtSecret="$JWT_SECRET" \
            mcpGatewayUrlPools="$MCP_GATEWAY_URLS" \
            backendCustomDomain="$BACKEND_DOMAIN" \
            frontendCustomDomain="$FRONTEND_DOMAIN"; then
        print_info "Infrastructure deployment completed successfully!"
    else
        print_error "Deployment failed. Checking deployment status..."
        az deployment group show \
            --name "$DEPLOYMENT_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --query properties.error \
            --output json
        exit 1
    fi
fi

# Get deployment outputs
print_info "Retrieving deployment outputs..."

# Check if deployment exists first
if ! az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    print_error "Deployment '$DEPLOYMENT_NAME' not found in resource group '$RESOURCE_GROUP'"
    print_info "Checking recent deployments..."
    az deployment group list --resource-group "$RESOURCE_GROUP" --output table
    exit 1
fi

BACKEND_URL=$(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.backendAppUrl.value -o tsv)
FRONTEND_URL=$(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.frontendAppUrl.value -o tsv)
BACKEND_APP_NAME=$(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.backendAppName.value -o tsv)
FRONTEND_APP_NAME=$(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.frontendAppName.value -o tsv)

# Verify outputs were retrieved
if [ -z "$BACKEND_APP_NAME" ] || [ -z "$FRONTEND_APP_NAME" ]; then
    print_error "Failed to retrieve deployment outputs"
    exit 1
fi

# Override with custom domains if provided
if [ -n "$BACKEND_DOMAIN" ]; then
    BACKEND_URL="https://$BACKEND_DOMAIN"
fi
if [ -n "$FRONTEND_DOMAIN" ]; then
    FRONTEND_URL="https://$FRONTEND_DOMAIN"
fi

# Construct redirect URIs for Azure AD
BACKEND_REDIRECT_URI="${BACKEND_URL}/api/v1/auth/azure/callback"
FRONTEND_REDIRECT_URI="${FRONTEND_URL}/auth/callback"

# Get Static Web App deployment token
print_info "Retrieving Static Web App deployment token..."
STATIC_WEB_APP_TOKEN=$(az staticwebapp secrets list --name "$FRONTEND_APP_NAME" --resource-group "$RESOURCE_GROUP" --query properties.apiKey -o tsv)

if [ -z "$STATIC_WEB_APP_TOKEN" ]; then
    print_error "Failed to retrieve Static Web App deployment token"
    exit 1
fi

# =============================================================================
# PHASE 2: Azure AD App Registration (if enabled)
# =============================================================================

if [ "$SETUP_SSO" = "y" ] || [ "$SETUP_SSO" = "Y" ]; then
    print_step "3/3 Configuring Azure AD for SSO..."

    # Full app name with environment
    FULL_APP_NAME="${PROJECT_NAME}-sso-${ENVIRONMENT}"

    # Check if app already exists
    print_info "Checking for existing Azure AD app registration..."
    EXISTING_APP_ID=$(az ad app list --display-name "$FULL_APP_NAME" --query "[0].appId" -o tsv 2>/dev/null)

    if [ -n "$EXISTING_APP_ID" ]; then
        print_warning "Azure AD app '$FULL_APP_NAME' already exists (ID: $EXISTING_APP_ID)"
        read -p "Do you want to update the existing app? (y/n, default: y): " UPDATE_APP
        UPDATE_APP=${UPDATE_APP:-y}

        if [ "$UPDATE_APP" != "y" ]; then
            print_info "Using existing app registration..."
            APP_ID=$EXISTING_APP_ID
            SKIP_AD_CREATE=true
        else
            print_info "Will update existing app registration..."
            APP_ID=$EXISTING_APP_ID
            SKIP_AD_CREATE=false
        fi
    else
        print_info "No existing Azure AD app found. Creating new app registration..."
        SKIP_AD_CREATE=false
    fi

    # Create or update app registration
    if [ "$SKIP_AD_CREATE" != "true" ]; then
        # Create manifest for required resource access (Microsoft Graph permissions)
        cat > /tmp/required-resource-access.json << EOF
[
    {
        "resourceAppId": "00000003-0000-0000-c000-000000000000",
        "resourceAccess": [
            {
                "id": "e1fe6dd8-ba31-4d61-89e7-88639da4683d",
                "type": "Scope"
            },
            {
                "id": "64a6cdd6-aab1-4aaf-94b8-3cc8405e90d0",
                "type": "Scope"
            },
            {
                "id": "14dad69e-099b-42c9-810b-d002981feec1",
                "type": "Scope"
            },
            {
                "id": "37f7f235-527c-4136-accd-4a02d197296e",
                "type": "Scope"
            }
        ]
    }
]
EOF

        if [ -z "$EXISTING_APP_ID" ]; then
            # Create new app
            print_info "Creating new Azure AD app registration: $FULL_APP_NAME"

            APP_ID=$(az ad app create \
                --display-name "$FULL_APP_NAME" \
                --sign-in-audience "AzureADMyOrg" \
                --web-redirect-uris "$BACKEND_REDIRECT_URI" "$FRONTEND_REDIRECT_URI" \
                --enable-id-token-issuance true \
                --enable-access-token-issuance true \
                --required-resource-accesses @/tmp/required-resource-access.json \
                --query appId -o tsv)

            if [ -z "$APP_ID" ]; then
                print_error "Failed to create app registration"
                rm -f /tmp/required-resource-access.json
                SETUP_SSO=n
            else
                print_info "Azure AD app created successfully with ID: $APP_ID"
                sleep 5  # Wait for propagation
            fi
        else
            # Update existing app
            print_info "Updating existing Azure AD app registration: $FULL_APP_NAME"

            az ad app update \
                --id "$APP_ID" \
                --web-redirect-uris "$BACKEND_REDIRECT_URI" "$FRONTEND_REDIRECT_URI" \
                --enable-id-token-issuance true \
                --enable-access-token-issuance true \
                --required-resource-accesses @/tmp/required-resource-access.json

            print_info "Azure AD app updated successfully"
        fi

        # Clean up temp file
        rm -f /tmp/required-resource-access.json
    fi

    # Create/update client secret only if app was created/updated
    if [ -n "$APP_ID" ] && [ "$SKIP_AD_CREATE" != "true" ]; then
        print_info "Creating new client secret..."
        SECRET_NAME="${FULL_APP_NAME}-secret-$(date +%Y%m%d)"
        SECRET_RESPONSE=$(az ad app credential reset \
            --id "$APP_ID" \
            --append \
            --display-name "$SECRET_NAME" \
            --years 2 \
            --query '{clientId:appId, clientSecret:password}' -o json)

        CLIENT_SECRET=$(echo "$SECRET_RESPONSE" | jq -r '.clientSecret')

        if [ -z "$CLIENT_SECRET" ] || [ "$CLIENT_SECRET" = "null" ]; then
            print_error "Failed to create client secret"
            SETUP_SSO=n
        else
            print_info "Client secret created successfully"
        fi
    elif [ -n "$APP_ID" ]; then
        # Existing app, prompt for existing secret
        print_warning "Using existing app. If you need a new secret, create one in Azure Portal."
        read -sp "Enter existing client secret (or press Enter to skip SSO config): " CLIENT_SECRET
        echo
        if [ -z "$CLIENT_SECRET" ]; then
            print_warning "No client secret provided. Skipping SSO configuration."
            SETUP_SSO=n
        fi
    fi

    # Create service principal if it doesn't exist
    if [ -n "$APP_ID" ] && [ "$SKIP_AD_CREATE" != "true" ]; then
        print_info "Creating/checking service principal..."
        SP_EXISTS=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].appId" -o tsv 2>/dev/null)

        if [ -z "$SP_EXISTS" ]; then
            az ad sp create --id "$APP_ID" > /dev/null 2>&1 || true
            print_info "Service principal created"
            sleep 3
        else
            print_info "Service principal already exists"
        fi
    fi

    # Grant admin consent (optional)
    if [ -n "$APP_ID" ] && [ "$SKIP_AD_CREATE" != "true" ]; then
        echo ""
        print_warning "Admin consent is required for users to sign in with Microsoft"
        read -p "Do you want to grant admin consent now? (requires admin privileges) (y/n, default: n): " GRANT_CONSENT
        GRANT_CONSENT=${GRANT_CONSENT:-n}

        if [ "$GRANT_CONSENT" = "y" ]; then
            print_info "Granting admin consent..."
            if az ad app permission admin-consent --id "$APP_ID" 2>/dev/null; then
                print_info "Admin consent granted successfully"
                ADMIN_CONSENT_GRANTED=true
            else
                print_warning "Failed to grant admin consent automatically"
                print_info "You'll need to grant it manually in Azure Portal"
                ADMIN_CONSENT_GRANTED=false
            fi
        else
            print_info "Skipping admin consent. You'll need to grant it manually later."
            ADMIN_CONSENT_GRANTED=false
        fi
    fi

    # Configure App Service with SSO settings
    if [ -n "$APP_ID" ] && [ -n "$CLIENT_SECRET" ]; then
        print_info "Configuring backend App Service with SSO credentials..."

        if az webapp config appsettings set \
            --name "$BACKEND_APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --settings \
                AZURE_CLIENT_ID="$APP_ID" \
                AZURE_TENANT_ID="$TENANT_ID" \
                AZURE_CLIENT_SECRET="$CLIENT_SECRET" \
                AZURE_REDIRECT_URI="$BACKEND_REDIRECT_URI" \
            --output none 2>/dev/null; then
            print_info "Backend application settings updated successfully"

            # Restart backend to apply new settings
            print_info "Restarting backend App Service..."
            az webapp restart --name "$BACKEND_APP_NAME" --resource-group "$RESOURCE_GROUP" --output none 2>/dev/null || true
        else
            print_warning "Failed to update backend application settings automatically"
        fi
    fi
fi

# =============================================================================
# Final Summary and Outputs
# =============================================================================

echo ""
echo "=========================================="
if [ "$SKIP_DEPLOY" = "true" ]; then
    print_info "✅ USING EXISTING INFRASTRUCTURE"
else
    print_info "✅ INFRASTRUCTURE DEPLOYED SUCCESSFULLY!"
fi

if [ "$SETUP_SSO" = "y" ] && [ -n "$APP_ID" ]; then
    print_info "✅ AZURE AD SSO CONFIGURED!"
fi
echo "=========================================="
echo ""
echo "📦 Resources:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Backend App: $BACKEND_APP_NAME"
echo "   Frontend App: $FRONTEND_APP_NAME"
echo ""
echo "🌐 URLs:"
echo "   Backend: $BACKEND_URL"
echo "   Frontend: $FRONTEND_URL"
echo ""

if [ "$SETUP_SSO" = "y" ] && [ -n "$APP_ID" ]; then
    echo "🔐 Azure AD SSO:"
    echo "   App Name: $FULL_APP_NAME"
    echo "   Client ID: $APP_ID"
    echo "   Tenant ID: $TENANT_ID"
    echo "   Backend Redirect: $BACKEND_REDIRECT_URI"
    echo "   Frontend Redirect: $FRONTEND_REDIRECT_URI"
    echo ""
fi

if [ -n "$BACKEND_DOMAIN" ] || [ -n "$FRONTEND_DOMAIN" ]; then
    echo "🔗 Custom Domains:"
    [ -n "$BACKEND_DOMAIN" ] && echo "   Backend: https://$BACKEND_DOMAIN"
    [ -n "$FRONTEND_DOMAIN" ] && echo "   Frontend: https://$FRONTEND_DOMAIN"
    echo ""
fi

# Save outputs to timestamped file
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_FILE="$(dirname "$0")/deployment-outputs-${TIMESTAMP}.txt"
cat > "$OUTPUT_FILE" << EOF
================================================================================
Azure Deployment Summary
================================================================================
Deployment Date: $(date)
Deployment Name: $DEPLOYMENT_NAME
Resource Group: $RESOURCE_GROUP
Location: $LOCATION
Environment: $ENVIRONMENT

================================================================================
Infrastructure Details
================================================================================
Backend App Name: $BACKEND_APP_NAME
Backend URL: $BACKEND_URL
Backend Custom Domain: ${BACKEND_DOMAIN:-Not configured}

Frontend App Name: $FRONTEND_APP_NAME
Frontend URL: $FRONTEND_URL
Frontend Custom Domain: ${FRONTEND_DOMAIN:-Not configured}

PostgreSQL Server: $(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.postgresServerFqdn.value -o tsv)
Database Name: $(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.postgresDatabaseName.value -o tsv)

================================================================================
Azure AD SSO Configuration
================================================================================
EOF

if [ "$SETUP_SSO" = "y" ] && [ -n "$APP_ID" ]; then
    cat >> "$OUTPUT_FILE" << EOF
SSO Enabled: Yes
App Display Name: $FULL_APP_NAME
Application (Client) ID: $APP_ID
Directory (Tenant) ID: $TENANT_ID
Client Secret: $CLIENT_SECRET
Admin Consent: $([ "$ADMIN_CONSENT_GRANTED" = "true" ] && echo "Granted" || echo "Pending")

Backend Redirect URI: $BACKEND_REDIRECT_URI
Frontend Redirect URI: $FRONTEND_REDIRECT_URI

Backend Environment Variables:
  AZURE_CLIENT_ID=$APP_ID
  AZURE_TENANT_ID=$TENANT_ID
  AZURE_CLIENT_SECRET=$CLIENT_SECRET
  AZURE_REDIRECT_URI=$BACKEND_REDIRECT_URI

Frontend Environment Variables:
  VITE_AZURE_CLIENT_ID=$APP_ID
  VITE_AZURE_TENANT_ID=$TENANT_ID
  VITE_AZURE_REDIRECT_URI=$FRONTEND_REDIRECT_URI
EOF
else
    cat >> "$OUTPUT_FILE" << EOF
SSO Enabled: No
To enable SSO later, run: ./setup-azure-ad-app.sh
EOF
fi

cat >> "$OUTPUT_FILE" << EOF

================================================================================
GitHub Secrets Configuration
================================================================================
Add these secrets to your GitHub repository:
Settings → Secrets and variables → Actions → New repository secret

1. AZURE_STATIC_WEB_APPS_API_TOKEN
   Value: $STATIC_WEB_APP_TOKEN

2. AZURE_RESOURCE_GROUP
   Value: $RESOURCE_GROUP

3. VITE_API_BASE_URL
   Value: $BACKEND_URL

4. AZURE_WEBAPP_PUBLISH_PROFILE
   Get from: Azure Portal → App Service → Deployment Center → Manage publish profile
   Or run: az webapp deployment list-publishing-profiles --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --xml
EOF

if [ "$SETUP_SSO" = "y" ] && [ -n "$APP_ID" ]; then
    cat >> "$OUTPUT_FILE" << EOF

5. AZURE_AD_CLIENT_ID
   Value: $APP_ID

6. AZURE_AD_TENANT_ID
   Value: $TENANT_ID

7. AZURE_AD_CLIENT_SECRET
   Value: $CLIENT_SECRET
EOF
fi

cat >> "$OUTPUT_FILE" << EOF

================================================================================
Next Steps
================================================================================
1. Add GitHub secrets listed above
2. Update workflow file: .github/workflows/deploy-backend.yml
   Set: AZURE_WEBAPP_NAME: $BACKEND_APP_NAME
3. Deploy code: git push origin main
4. Run database migrations after first deployment:
   az webapp ssh --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP
   cd /home/site/wwwroot && source antenv/bin/activate && alembic upgrade head
EOF

if [ "$SETUP_SSO" = "y" ] && [ "$ADMIN_CONSENT_GRANTED" != "true" ]; then
    cat >> "$OUTPUT_FILE" << EOF
5. Grant admin consent in Azure Portal:
   https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/$APP_ID
EOF
fi

cat >> "$OUTPUT_FILE" << EOF

================================================================================
Verification URLs
================================================================================
Backend Health Check: ${BACKEND_URL}/api/v1/checks
Frontend: $FRONTEND_URL
EOF

if [ "$SETUP_SSO" = "y" ] && [ -n "$APP_ID" ]; then
    cat >> "$OUTPUT_FILE" << EOF
SSO Login Test: ${FRONTEND_URL}/signin (click "Sign in with Microsoft")
EOF
fi

cat >> "$OUTPUT_FILE" << EOF

================================================================================
Cost Estimate
================================================================================
App Service (B1): ~\$13/month
PostgreSQL (B1ms): ~\$12/month
Static Web App: Free
Application Insights: ~\$2-5/month
TOTAL: ~\$27-30/month

================================================================================
Generated: $(date)
Script Version: 2.0 (Unified with SSO)
================================================================================
EOF

print_info "Complete deployment details saved to: $OUTPUT_FILE"

# Create symlink to latest
LATEST_LINK="$(dirname "$0")/deployment-outputs-latest.txt"
ln -sf "$(basename "$OUTPUT_FILE")" "$LATEST_LINK" 2>/dev/null || true
print_info "Latest deployment link: $LATEST_LINK"

# Print next steps
echo ""
echo "=========================================="
print_info "📋 NEXT STEPS"
echo "=========================================="
echo ""

print_info "1️⃣  Add GitHub Secrets:"
echo ""
echo "   Required:"
echo "   - AZURE_STATIC_WEB_APPS_API_TOKEN"
echo "   - AZURE_RESOURCE_GROUP"
echo "   - VITE_API_BASE_URL"
echo "   - AZURE_WEBAPP_PUBLISH_PROFILE"

if [ "$SETUP_SSO" = "y" ] && [ -n "$APP_ID" ]; then
    echo ""
    echo "   For SSO:"
    echo "   - AZURE_AD_CLIENT_ID"
    echo "   - AZURE_AD_TENANT_ID"
    echo "   - AZURE_AD_CLIENT_SECRET"
fi

echo ""
echo "   (All values saved in: $OUTPUT_FILE)"
echo ""

if [ "$SETUP_SSO" = "y" ] && [ -n "$APP_ID" ]; then
    print_info "2️⃣  Add Frontend Environment Variables (.env):"
    echo ""
    echo "   VITE_API_BASE_URL=$BACKEND_URL"
    echo "   VITE_AZURE_CLIENT_ID=$APP_ID"
    echo "   VITE_AZURE_TENANT_ID=$TENANT_ID"
    echo "   VITE_AZURE_REDIRECT_URI=$FRONTEND_REDIRECT_URI"
    echo ""
fi

if [ "$SETUP_SSO" = "y" ] && [ "$ADMIN_CONSENT_GRANTED" != "true" ]; then
    print_warning "⚠️  Don't forget to grant admin consent!"
    echo "   Azure Portal: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/$APP_ID"
    echo ""
fi

print_info "3️⃣  Deploy your code:"
echo "   git add ."
echo "   git commit -m \"Configure Azure deployment\""
echo "   git push origin main"
echo ""

print_info "4️⃣  Run database migrations:"
echo "   az webapp ssh --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
echo "   cd /home/site/wwwroot && source antenv/bin/activate && alembic upgrade head"
echo ""

print_info "🎉 Deployment completed successfully!"
echo ""
