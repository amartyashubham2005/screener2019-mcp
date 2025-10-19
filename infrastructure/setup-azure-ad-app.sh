#!/bin/bash

# Azure AD Application Registration Script
# This script creates/updates an Azure AD app registration for SSO authentication

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

# Check if jq is installed (for JSON parsing)
if ! command -v jq &> /dev/null; then
    print_warning "jq is not installed. Installing jq for JSON parsing..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y jq
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install jq
    else
        print_error "Please install jq manually: https://stedolan.github.io/jq/download/"
        exit 1
    fi
fi

echo ""
echo "=========================================="
print_info "Azure AD App Registration Setup"
echo "=========================================="
echo ""

# Configuration
print_step "1/8 Configuring parameters..."

read -p "Enter application name (default: screener2019-mcp-sso): " APP_NAME
APP_NAME=${APP_NAME:-screener2019-mcp-sso}

read -p "Enter environment (dev/staging/prod, default: dev): " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-dev}

# Full app name with environment
FULL_APP_NAME="${APP_NAME}-${ENVIRONMENT}"

read -p "Enter backend URL (e.g., https://api.example.com or http://localhost:8000): " BACKEND_URL
if [ -z "$BACKEND_URL" ]; then
    print_error "Backend URL is required"
    exit 1
fi

read -p "Enter frontend URL (e.g., https://example.com or http://localhost:3000): " FRONTEND_URL
if [ -z "$FRONTEND_URL" ]; then
    print_error "Frontend URL is required"
    exit 1
fi

# Remove trailing slashes
BACKEND_URL=${BACKEND_URL%/}
FRONTEND_URL=${FRONTEND_URL%/}

# Construct redirect URIs
BACKEND_REDIRECT_URI="${BACKEND_URL}/api/v1/auth/azure/callback"
FRONTEND_REDIRECT_URI="${FRONTEND_URL}/auth/callback"

print_info "Backend Redirect URI: $BACKEND_REDIRECT_URI"
print_info "Frontend Redirect URI: $FRONTEND_REDIRECT_URI"

# Login check
print_step "2/8 Checking Azure login status..."
if ! az account show &> /dev/null; then
    print_warning "Not logged in to Azure. Logging in..."
    az login
fi

# Display current tenant
TENANT_ID=$(az account show --query tenantId -o tsv)
TENANT_NAME=$(az account show --query name -o tsv)
print_info "Using Azure AD Tenant: $TENANT_NAME (ID: $TENANT_ID)"

read -p "Is this the correct tenant for app registration? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    print_info "Available tenants:"
    az account list --query "[].{Name:name, TenantId:tenantId}" --output table
    read -p "Enter tenant ID: " TENANT_ID
    az account set --subscription "$TENANT_ID"
    TENANT_ID=$(az account show --query tenantId -o tsv)
fi

# Check if app already exists
print_step "3/8 Checking for existing app registration..."
EXISTING_APP_ID=$(az ad app list --display-name "$FULL_APP_NAME" --query "[0].appId" -o tsv 2>/dev/null)

if [ -n "$EXISTING_APP_ID" ]; then
    print_warning "App registration '$FULL_APP_NAME' already exists (ID: $EXISTING_APP_ID)"
    read -p "Do you want to update the existing app? (y/n): " UPDATE_APP

    if [ "$UPDATE_APP" != "y" ]; then
        print_info "Using existing app registration..."
        APP_ID=$EXISTING_APP_ID
        SKIP_CREATE=true
    else
        print_info "Will update existing app registration..."
        APP_ID=$EXISTING_APP_ID
        SKIP_CREATE=false
    fi
else
    print_info "No existing app found. Will create new app registration..."
    SKIP_CREATE=false
fi

# Create or update app registration
if [ "$SKIP_CREATE" != "true" ]; then
    print_step "4/8 Creating/updating app registration..."

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
            exit 1
        fi

        print_info "App created successfully with ID: $APP_ID"

        # Wait for app to be fully created
        print_info "Waiting for app registration to propagate..."
        sleep 5
    else
        # Update existing app
        print_info "Updating existing app registration: $FULL_APP_NAME"

        az ad app update \
            --id "$APP_ID" \
            --web-redirect-uris "$BACKEND_REDIRECT_URI" "$FRONTEND_REDIRECT_URI" \
            --enable-id-token-issuance true \
            --enable-access-token-issuance true \
            --required-resource-accesses @/tmp/required-resource-access.json

        print_info "App updated successfully"
    fi

    # Clean up temp file
    rm -f /tmp/required-resource-access.json
else
    print_info "Skipping app creation/update"
fi

# Get app details
print_step "5/8 Retrieving app details..."
APP_OBJECT_ID=$(az ad app show --id "$APP_ID" --query id -o tsv)
print_info "App Object ID: $APP_OBJECT_ID"

# Create client secret
print_step "6/8 Creating client secret..."
print_info "Creating new client secret (valid for 2 years)..."

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
    exit 1
fi

print_info "Client secret created successfully"
print_warning "IMPORTANT: Save the client secret now - it won't be shown again!"

# Create service principal if it doesn't exist
print_step "7/8 Creating service principal..."
SP_EXISTS=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].appId" -o tsv 2>/dev/null)

if [ -z "$SP_EXISTS" ]; then
    print_info "Creating service principal..."
    az ad sp create --id "$APP_ID" > /dev/null
    print_info "Service principal created"

    # Wait for service principal to propagate
    sleep 3
else
    print_info "Service principal already exists"
fi

# Get additional details
print_step "8/8 Gathering final details..."
APP_IDENTIFIER_URI=$(az ad app show --id "$APP_ID" --query identifierUris[0] -o tsv 2>/dev/null || echo "Not set")

# Grant admin consent (optional)
echo ""
print_warning "Admin consent is required for the app to access Microsoft Graph API"
read -p "Do you want to grant admin consent now? (requires admin privileges) (y/n): " GRANT_CONSENT

if [ "$GRANT_CONSENT" = "y" ]; then
    print_info "Granting admin consent..."

    if az ad app permission admin-consent --id "$APP_ID" 2>/dev/null; then
        print_info "Admin consent granted successfully"
    else
        print_warning "Failed to grant admin consent automatically"
        print_info "You may need to grant consent manually in Azure Portal:"
        print_info "Azure AD → App registrations → $FULL_APP_NAME → API permissions → Grant admin consent"
    fi
else
    print_warning "Skipping admin consent. You'll need to grant it manually later."
fi

# Save outputs to file
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_FILE="$(dirname "$0")/azure-ad-app-${TIMESTAMP}.txt"

cat > "$OUTPUT_FILE" << EOF
================================================================================
Azure AD App Registration Summary
================================================================================
Created: $(date)
App Name: $FULL_APP_NAME
Environment: $ENVIRONMENT

================================================================================
App Registration Details
================================================================================
Application (client) ID: $APP_ID
Directory (tenant) ID: $TENANT_ID
Object ID: $APP_OBJECT_ID

Client Secret: $CLIENT_SECRET
Secret Name: $SECRET_NAME
Secret Expires: $(date -d "+2 years" +%Y-%m-%d 2>/dev/null || date -v +2y +%Y-%m-%d 2>/dev/null)

================================================================================
Redirect URIs
================================================================================
Backend: $BACKEND_REDIRECT_URI
Frontend: $FRONTEND_REDIRECT_URI

================================================================================
API Permissions (Microsoft Graph - Delegated)
================================================================================
- User.Read: Sign in and read user profile
- email: View users' email address
- openid: Sign users in
- profile: View users' basic profile

Status: $([ "$GRANT_CONSENT" = "y" ] && echo "Admin consent granted" || echo "Pending admin consent")

================================================================================
Environment Variables for Backend (.env)
================================================================================
AZURE_CLIENT_ID=$APP_ID
AZURE_TENANT_ID=$TENANT_ID
AZURE_CLIENT_SECRET=$CLIENT_SECRET
AZURE_REDIRECT_URI=$BACKEND_REDIRECT_URI

================================================================================
Environment Variables for Frontend (.env)
================================================================================
VITE_AZURE_CLIENT_ID=$APP_ID
VITE_AZURE_TENANT_ID=$TENANT_ID
VITE_AZURE_REDIRECT_URI=$FRONTEND_REDIRECT_URI

================================================================================
GitHub Secrets (if using CI/CD)
================================================================================
Add these to your GitHub repository secrets:

AZURE_AD_CLIENT_ID: $APP_ID
AZURE_AD_TENANT_ID: $TENANT_ID
AZURE_AD_CLIENT_SECRET: $CLIENT_SECRET

================================================================================
Azure App Service Application Settings
================================================================================
If deploying to Azure App Service, add these application settings:

az webapp config appsettings set \\
  --name YOUR_BACKEND_APP_NAME \\
  --resource-group YOUR_RESOURCE_GROUP \\
  --settings \\
    AZURE_CLIENT_ID=$APP_ID \\
    AZURE_TENANT_ID=$TENANT_ID \\
    AZURE_CLIENT_SECRET=$CLIENT_SECRET \\
    AZURE_REDIRECT_URI=$BACKEND_REDIRECT_URI

================================================================================
Next Steps
================================================================================
1. Copy the environment variables above to your .env files
2. Grant admin consent if not done (Azure Portal → App registrations → API permissions)
3. Test the SSO login flow
4. Configure GitHub secrets for CI/CD deployment
5. Add Azure App Service application settings

================================================================================
Important Security Notes
================================================================================
- Keep the client secret secure and never commit it to version control
- Rotate the client secret before it expires (2 years)
- Use Azure Key Vault in production to store the client secret
- Monitor app sign-ins in Azure AD logs
- Review API permissions periodically

================================================================================
Useful Azure Portal Links
================================================================================
App Registration: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/$APP_ID
API Permissions: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/$APP_ID
Certificates & Secrets: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Credentials/appId/$APP_ID

================================================================================
EOF

echo ""
echo "=========================================="
print_info "✅ AZURE AD APP REGISTRATION COMPLETED!"
echo "=========================================="
echo ""
print_info "App Details:"
echo "   Name: $FULL_APP_NAME"
echo "   Application ID: $APP_ID"
echo "   Tenant ID: $TENANT_ID"
echo ""
print_warning "⚠️  IMPORTANT - Save these credentials securely:"
echo "   Client Secret: $CLIENT_SECRET"
echo ""
print_info "📋 Configuration saved to: $OUTPUT_FILE"

# Create symlink to latest
LATEST_LINK="$(dirname "$0")/azure-ad-app-latest.txt"
ln -sf "$(basename "$OUTPUT_FILE")" "$LATEST_LINK" 2>/dev/null || true
print_info "Latest config link: $LATEST_LINK"

echo ""
print_info "🔐 Add these to your backend .env file:"
echo "   AZURE_CLIENT_ID=$APP_ID"
echo "   AZURE_TENANT_ID=$TENANT_ID"
echo "   AZURE_CLIENT_SECRET=$CLIENT_SECRET"
echo "   AZURE_REDIRECT_URI=$BACKEND_REDIRECT_URI"
echo ""

print_info "🌐 Add these to your frontend .env file:"
echo "   VITE_AZURE_CLIENT_ID=$APP_ID"
echo "   VITE_AZURE_TENANT_ID=$TENANT_ID"
echo "   VITE_AZURE_REDIRECT_URI=$FRONTEND_REDIRECT_URI"
echo ""

if [ "$GRANT_CONSENT" != "y" ]; then
    print_warning "⚠️  Don't forget to grant admin consent in Azure Portal!"
    echo "   URL: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/$APP_ID"
    echo ""
fi

print_info "✅ Setup complete! You can now implement Azure SSO in your application."
echo ""
