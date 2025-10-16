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
read -p "Enter project name (default: mcp): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-mcp}

read -p "Enter environment (dev/staging/prod, default: prod): " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-prod}

read -p "Enter Azure region (default: eastus): " LOCATION
LOCATION=${LOCATION:-eastus}

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

# Create resource group
print_info "Creating resource group: $RESOURCE_GROUP in $LOCATION..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --tags Project="$PROJECT_NAME" Environment="$ENVIRONMENT" ManagedBy="Bicep"

# Deploy Bicep template
print_info "Deploying Azure resources using Bicep template..."
print_info "This may take 5-10 minutes..."

DEPLOYMENT_NAME="${PROJECT_NAME}-deployment-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
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
        frontendCustomDomain="$FRONTEND_DOMAIN"

# Get deployment outputs
print_info "Retrieving deployment outputs..."
BACKEND_URL=$(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.backendAppUrl.value -o tsv)
FRONTEND_URL=$(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.frontendAppUrl.value -o tsv)
STATIC_WEB_APP_TOKEN=$(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.staticWebAppDeploymentToken.value -o tsv)
BACKEND_APP_NAME=$(az deployment group show --name "$DEPLOYMENT_NAME" --resource-group "$RESOURCE_GROUP" --query properties.outputs.backendAppName.value -o tsv)

# Get publish profile for backend
print_info "Retrieving backend publish profile..."
PUBLISH_PROFILE=$(az webapp deployment list-publishing-profiles --name "$BACKEND_APP_NAME" --resource-group "$RESOURCE_GROUP" --xml)

print_info "=========================================="
print_info "Deployment completed successfully!"
print_info "=========================================="
echo ""
print_info "Backend URL: $BACKEND_URL"
print_info "Frontend URL: $FRONTEND_URL"
echo ""
print_info "=========================================="
print_info "Next Steps:"
print_info "=========================================="
echo ""
print_info "1. Add GitHub Secrets (Settings > Secrets and variables > Actions):"
echo "   - AZURE_WEBAPP_PUBLISH_PROFILE"
echo "   - AZURE_STATIC_WEB_APPS_API_TOKEN: $STATIC_WEB_APP_TOKEN"
echo "   - AZURE_RESOURCE_GROUP: $RESOURCE_GROUP"
echo "   - VITE_API_BASE_URL: https://${BACKEND_DOMAIN:-$BACKEND_URL}"
echo ""
print_info "2. Configure custom domains:"
if [ -n "$BACKEND_DOMAIN" ]; then
    echo "   Backend DNS (CNAME): $BACKEND_DOMAIN -> ${BACKEND_URL#https://}"
fi
if [ -n "$FRONTEND_DOMAIN" ]; then
    echo "   Frontend DNS (CNAME): $FRONTEND_DOMAIN -> ${FRONTEND_URL#https://}"
fi
echo ""
print_info "3. Enable custom domains in Azure Portal after DNS propagation"
echo ""
print_info "4. Push code to GitHub to trigger automatic deployment"
echo ""
print_info "5. Run database migrations on backend after first deployment:"
echo "   az webapp ssh --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
echo "   cd /home/site/wwwroot && alembic upgrade head"
echo ""

# Save outputs to file
OUTPUT_FILE="$(dirname "$0")/deployment-outputs.txt"
cat > "$OUTPUT_FILE" << EOF
Deployment Date: $(date)
Resource Group: $RESOURCE_GROUP
Backend URL: $BACKEND_URL
Frontend URL: $FRONTEND_URL
Backend App Name: $BACKEND_APP_NAME

GitHub Secrets to Add:
======================
AZURE_WEBAPP_PUBLISH_PROFILE: (Copy from Azure Portal)
AZURE_STATIC_WEB_APPS_API_TOKEN: $STATIC_WEB_APP_TOKEN
AZURE_RESOURCE_GROUP: $RESOURCE_GROUP
VITE_API_BASE_URL: https://${BACKEND_DOMAIN:-${BACKEND_URL#https://}}
EOF

print_info "Deployment outputs saved to: $OUTPUT_FILE"
