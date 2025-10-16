#!/bin/bash

# Azure Infrastructure Deployment Script
# This script deploys all Azure resources using Bicep template

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Configuration
print_info "Starting Azure deployment configuration..."

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

# Login check
print_info "Checking Azure login status..."
if ! az account show &> /dev/null; then
    print_warning "Not logged in to Azure. Logging in..."
    az login
fi

# Display current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
print_info "Using subscription: $SUBSCRIPTION"
read -p "Is this correct? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    print_info "Available subscriptions:"
    az account list --output table
    read -p "Enter subscription ID or name: " SUB_ID
    az account set --subscription "$SUB_ID"
fi

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
        print_info "Deployment completed successfully!"
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

# Get Static Web App deployment token separately (using API key retrieval)
print_info "Retrieving Static Web App deployment token..."
STATIC_WEB_APP_TOKEN=$(az staticwebapp secrets list --name "$FRONTEND_APP_NAME" --resource-group "$RESOURCE_GROUP" --query properties.apiKey -o tsv)

if [ -z "$STATIC_WEB_APP_TOKEN" ]; then
    print_error "Failed to retrieve Static Web App deployment token"
    exit 1
fi

# Get publish profile for backend
print_info "Retrieving backend publish profile..."
if ! PUBLISH_PROFILE=$(az webapp deployment list-publishing-profiles --name "$BACKEND_APP_NAME" --resource-group "$RESOURCE_GROUP" --xml 2>&1); then
    print_warning "Failed to retrieve publish profile automatically"
    print_info "You can get it manually from Azure Portal: App Service → Deployment Center → Manage publish profile"
    PUBLISH_PROFILE="<Get from Azure Portal>"
fi

echo ""
echo "=========================================="
if [ "$SKIP_DEPLOY" = "true" ]; then
    print_info "✅ USING EXISTING DEPLOYMENT"
else
    print_info "✅ DEPLOYMENT COMPLETED SUCCESSFULLY!"
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
if [ -n "$BACKEND_DOMAIN" ] || [ -n "$FRONTEND_DOMAIN" ]; then
    echo "🔗 Custom Domains:"
    [ -n "$BACKEND_DOMAIN" ] && echo "   Backend: https://$BACKEND_DOMAIN"
    [ -n "$FRONTEND_DOMAIN" ] && echo "   Frontend: https://$FRONTEND_DOMAIN"
    echo ""
fi
echo "=========================================="
print_info "📋 NEXT STEPS"
echo "=========================================="
echo ""
print_info "1️⃣  Add GitHub Secrets (Settings → Secrets and variables → Actions):"
echo ""
echo "   AZURE_STATIC_WEB_APPS_API_TOKEN:"
echo "   $STATIC_WEB_APP_TOKEN"
echo ""
echo "   AZURE_RESOURCE_GROUP:"
echo "   $RESOURCE_GROUP"
echo ""
echo "   VITE_API_BASE_URL:"
if [ -n "$BACKEND_DOMAIN" ]; then
    echo "   https://$BACKEND_DOMAIN"
else
    echo "   $BACKEND_URL"
fi
echo ""
echo "   AZURE_WEBAPP_PUBLISH_PROFILE:"
echo "   (See deployment-outputs.txt or get from Azure Portal)"
echo ""
print_info "2️⃣  Update GitHub workflow file:"
echo "   Edit .github/workflows/deploy-backend.yml"
echo "   Set: AZURE_WEBAPP_NAME: $BACKEND_APP_NAME"
echo ""
if [ -n "$BACKEND_DOMAIN" ] || [ -n "$FRONTEND_DOMAIN" ]; then
    print_info "3️⃣  Configure DNS at your domain provider:"
    echo ""
    if [ -n "$BACKEND_DOMAIN" ]; then
        echo "   Backend CNAME Record:"
        echo "   Type: CNAME"
        echo "   Name: ${BACKEND_DOMAIN%%.*}"
        echo "   Value: ${BACKEND_URL#https://}"
        echo "   TTL: 3600"
        echo ""
    fi
    if [ -n "$FRONTEND_DOMAIN" ]; then
        echo "   Frontend CNAME Record:"
        echo "   Type: CNAME"
        echo "   Name: @ (or www)"
        echo "   Value: ${FRONTEND_URL#https://}"
        echo "   TTL: 3600"
        echo ""
    fi
    print_info "4️⃣  After DNS propagation, enable custom domains:"
    echo ""
    if [ -n "$BACKEND_DOMAIN" ]; then
        echo "   Backend:"
        echo "   az webapp config hostname add \\"
        echo "     --webapp-name $BACKEND_APP_NAME \\"
        echo "     --resource-group $RESOURCE_GROUP \\"
        echo "     --hostname $BACKEND_DOMAIN"
        echo ""
    fi
    if [ -n "$FRONTEND_DOMAIN" ]; then
        echo "   Frontend: Use Azure Portal → Static Web App → Custom domains"
        echo ""
    fi
fi
print_info "5️⃣  Deploy your code:"
echo "   git add ."
echo "   git commit -m \"Configure Azure deployment\""
echo "   git push origin main"
echo ""
print_info "6️⃣  Run database migrations (after first deployment):"
echo "   az webapp ssh --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
echo "   cd /home/site/wwwroot && source antenv/bin/activate && alembic upgrade head"
echo ""

# Save outputs to timestamped file
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_FILE="$(dirname "$0")/deployment-outputs-${TIMESTAMP}.txt"
cat > "$OUTPUT_FILE" << EOF
================================================================================
Azure Deployment Summary
================================================================================
Deployment Date: $(date)
Deployment Name: $DEPLOYMENT_NAME
Deployment Type: $([ "$SKIP_DEPLOY" = "true" ] && echo "Existing (Idempotent)" || echo "New Deployment")
Resource Group: $RESOURCE_GROUP
Location: $LOCATION
Environment: $ENVIRONMENT

================================================================================
Resource Details
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
GitHub Secrets Configuration
================================================================================
Add these secrets to your GitHub repository:
Settings → Secrets and variables → Actions → New repository secret

1. AZURE_STATIC_WEB_APPS_API_TOKEN
   Value: $STATIC_WEB_APP_TOKEN

2. AZURE_RESOURCE_GROUP
   Value: $RESOURCE_GROUP

3. VITE_API_BASE_URL
   Value: https://${BACKEND_DOMAIN:-${BACKEND_URL#https://}}

4. AZURE_WEBAPP_PUBLISH_PROFILE
   Get from Azure Portal or run:
   az webapp deployment list-publishing-profiles \\
     --name $BACKEND_APP_NAME \\
     --resource-group $RESOURCE_GROUP \\
     --xml

================================================================================
DNS Configuration (if using custom domains)
================================================================================
EOF

if [ -n "$BACKEND_DOMAIN" ]; then
    cat >> "$OUTPUT_FILE" << EOF
Backend DNS (api.jesterbot.com):
  Type: CNAME
  Name: ${BACKEND_DOMAIN%%.*}
  Value: ${BACKEND_URL#https://}
  TTL: 3600

EOF
fi

if [ -n "$FRONTEND_DOMAIN" ]; then
    cat >> "$OUTPUT_FILE" << EOF
Frontend DNS (jesterbot.com):
  Type: CNAME
  Name: @ (or www)
  Value: ${FRONTEND_URL#https://}
  TTL: 3600

EOF
fi

cat >> "$OUTPUT_FILE" << EOF
================================================================================
Next Steps
================================================================================
1. Add GitHub secrets listed above
2. Update workflow file: .github/workflows/deploy-backend.yml
   Set: AZURE_WEBAPP_NAME: $BACKEND_APP_NAME
3. Configure DNS records (if using custom domains)
4. Deploy code: git push origin main
5. Run database migrations after first deployment:
   az webapp ssh --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP
   cd /home/site/wwwroot && source antenv/bin/activate && alembic upgrade head

================================================================================
Verification URLs
================================================================================
Backend Health Check: ${BACKEND_URL}/api/v1/checks
Frontend: $FRONTEND_URL

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
Script Version: 1.1 (Idempotent)
================================================================================
EOF

print_info "Deployment details saved to: $OUTPUT_FILE"

# Also create a symlink to latest
LATEST_LINK="$(dirname "$0")/deployment-outputs-latest.txt"
ln -sf "$(basename "$OUTPUT_FILE")" "$LATEST_LINK" 2>/dev/null || true
print_info "Latest deployment link: $LATEST_LINK"
