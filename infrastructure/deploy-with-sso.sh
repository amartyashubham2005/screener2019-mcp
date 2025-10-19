#!/bin/bash

# Complete Azure Deployment with SSO Integration
# This script deploys infrastructure and configures Azure AD app registration

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_header() {
    echo ""
    echo -e "${CYAN}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
    echo ""
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header "🚀 Complete Azure Deployment with SSO"

echo "This script will:"
echo "  1. Deploy Azure infrastructure (App Services, Database, etc.)"
echo "  2. Create/configure Azure AD app registration for SSO"
echo "  3. Configure application settings with SSO credentials"
echo ""

read -p "Continue? (y/n): " CONTINUE
if [ "$CONTINUE" != "y" ]; then
    print_info "Deployment cancelled"
    exit 0
fi

# =============================================================================
# PHASE 1: Infrastructure Deployment
# =============================================================================

print_header "📦 PHASE 1: Infrastructure Deployment"

read -p "Do you want to deploy/update Azure infrastructure? (y/n): " DEPLOY_INFRA

if [ "$DEPLOY_INFRA" = "y" ]; then
    print_info "Running infrastructure deployment script..."

    if [ -f "$SCRIPT_DIR/deploy.sh" ]; then
        bash "$SCRIPT_DIR/deploy.sh"

        # Check if deployment was successful
        if [ $? -ne 0 ]; then
            print_error "Infrastructure deployment failed"
            exit 1
        fi

        print_info "Infrastructure deployment completed successfully"
    else
        print_error "deploy.sh not found in $SCRIPT_DIR"
        exit 1
    fi

    # Parse deployment outputs from latest file
    if [ -f "$SCRIPT_DIR/deployment-outputs-latest.txt" ]; then
        print_info "Reading deployment outputs..."
        BACKEND_URL=$(grep "Backend URL:" "$SCRIPT_DIR/deployment-outputs-latest.txt" | cut -d' ' -f3)
        FRONTEND_URL=$(grep "Frontend URL:" "$SCRIPT_DIR/deployment-outputs-latest.txt" | cut -d' ' -f3)
        BACKEND_APP_NAME=$(grep "Backend App Name:" "$SCRIPT_DIR/deployment-outputs-latest.txt" | cut -d' ' -f4)
        RESOURCE_GROUP=$(grep "Resource Group:" "$SCRIPT_DIR/deployment-outputs-latest.txt" | cut -d' ' -f3)

        # Try to get custom domains if configured
        BACKEND_CUSTOM=$(grep "Backend Custom Domain:" "$SCRIPT_DIR/deployment-outputs-latest.txt" | cut -d' ' -f4)
        if [ "$BACKEND_CUSTOM" != "Not" ] && [ -n "$BACKEND_CUSTOM" ]; then
            BACKEND_URL="https://$BACKEND_CUSTOM"
        fi

        FRONTEND_CUSTOM=$(grep "Frontend Custom Domain:" "$SCRIPT_DIR/deployment-outputs-latest.txt" | cut -d' ' -f4)
        if [ "$FRONTEND_CUSTOM" != "Not" ] && [ -n "$FRONTEND_CUSTOM" ]; then
            FRONTEND_URL="https://$FRONTEND_CUSTOM"
        fi
    else
        print_warning "Could not find deployment outputs file"
        read -p "Enter backend URL: " BACKEND_URL
        read -p "Enter frontend URL: " FRONTEND_URL
        read -p "Enter backend app name: " BACKEND_APP_NAME
        read -p "Enter resource group: " RESOURCE_GROUP
    fi
else
    print_info "Skipping infrastructure deployment"
    print_info "Please provide existing resource information:"
    read -p "Enter backend URL: " BACKEND_URL
    read -p "Enter frontend URL: " FRONTEND_URL
    read -p "Enter backend app name: " BACKEND_APP_NAME
    read -p "Enter resource group: " RESOURCE_GROUP
fi

# Verify we have the required information
if [ -z "$BACKEND_URL" ] || [ -z "$FRONTEND_URL" ]; then
    print_error "Backend and Frontend URLs are required"
    exit 1
fi

print_info "Using:"
print_info "  Backend: $BACKEND_URL"
print_info "  Frontend: $FRONTEND_URL"

# =============================================================================
# PHASE 2: Azure AD App Registration
# =============================================================================

print_header "🔐 PHASE 2: Azure AD App Registration"

read -p "Do you want to create/update Azure AD app registration for SSO? (y/n): " SETUP_AD

if [ "$SETUP_AD" = "y" ]; then
    print_info "Setting up Azure AD app registration..."

    # Create temporary input file for automated setup
    cat > /tmp/azure-ad-input.txt << EOF
${APP_NAME:-screener2019-mcp-sso}
${ENVIRONMENT:-dev}
$BACKEND_URL
$FRONTEND_URL
y
y
y
EOF

    if [ -f "$SCRIPT_DIR/setup-azure-ad-app.sh" ]; then
        # Run Azure AD setup with automated inputs
        bash "$SCRIPT_DIR/setup-azure-ad-app.sh" < /tmp/azure-ad-input.txt

        # Clean up temp file
        rm -f /tmp/azure-ad-input.txt

        # Check if setup was successful
        if [ $? -ne 0 ]; then
            print_error "Azure AD app registration failed"
            exit 1
        fi

        print_info "Azure AD app registration completed successfully"
    else
        print_error "setup-azure-ad-app.sh not found in $SCRIPT_DIR"
        rm -f /tmp/azure-ad-input.txt
        exit 1
    fi

    # Parse Azure AD outputs from latest file
    if [ -f "$SCRIPT_DIR/azure-ad-app-latest.txt" ]; then
        print_info "Reading Azure AD configuration..."
        AZURE_CLIENT_ID=$(grep "^Application (client) ID:" "$SCRIPT_DIR/azure-ad-app-latest.txt" | cut -d' ' -f4)
        AZURE_TENANT_ID=$(grep "^Directory (tenant) ID:" "$SCRIPT_DIR/azure-ad-app-latest.txt" | cut -d' ' -f4)
        AZURE_CLIENT_SECRET=$(grep "^Client Secret:" "$SCRIPT_DIR/azure-ad-app-latest.txt" | cut -d' ' -f3)
        AZURE_REDIRECT_URI="${BACKEND_URL}/api/v1/auth/azure/callback"
    else
        print_warning "Could not find Azure AD app configuration file"
        read -p "Enter Azure Client ID: " AZURE_CLIENT_ID
        read -p "Enter Azure Tenant ID: " AZURE_TENANT_ID
        read -sp "Enter Azure Client Secret: " AZURE_CLIENT_SECRET
        echo
        AZURE_REDIRECT_URI="${BACKEND_URL}/api/v1/auth/azure/callback"
    fi
else
    print_info "Skipping Azure AD app registration"
    print_info "If you already have an Azure AD app, enter credentials:"
    read -p "Azure Client ID (leave empty to skip): " AZURE_CLIENT_ID

    if [ -n "$AZURE_CLIENT_ID" ]; then
        read -p "Azure Tenant ID: " AZURE_TENANT_ID
        read -sp "Azure Client Secret: " AZURE_CLIENT_SECRET
        echo
        AZURE_REDIRECT_URI="${BACKEND_URL}/api/v1/auth/azure/callback"
    fi
fi

# =============================================================================
# PHASE 3: Configure Application Settings
# =============================================================================

if [ -n "$AZURE_CLIENT_ID" ] && [ -n "$BACKEND_APP_NAME" ] && [ -n "$RESOURCE_GROUP" ]; then
    print_header "⚙️  PHASE 3: Configure Application Settings"

    print_info "Configuring Azure App Service with SSO credentials..."

    # Add SSO environment variables to backend
    print_info "Adding Azure AD settings to backend App Service..."

    if az webapp config appsettings set \
        --name "$BACKEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
            AZURE_TENANT_ID="$AZURE_TENANT_ID" \
            AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
            AZURE_REDIRECT_URI="$AZURE_REDIRECT_URI" \
        --output none 2>/dev/null; then
        print_info "Backend application settings updated successfully"
    else
        print_warning "Failed to update backend application settings automatically"
        print_info "You can add them manually in Azure Portal or run:"
        echo ""
        echo "az webapp config appsettings set \\"
        echo "  --name $BACKEND_APP_NAME \\"
        echo "  --resource-group $RESOURCE_GROUP \\"
        echo "  --settings \\"
        echo "    AZURE_CLIENT_ID=$AZURE_CLIENT_ID \\"
        echo "    AZURE_TENANT_ID=$AZURE_TENANT_ID \\"
        echo "    AZURE_CLIENT_SECRET=*** \\"
        echo "    AZURE_REDIRECT_URI=$AZURE_REDIRECT_URI"
        echo ""
    fi

    # Restart backend to apply new settings
    print_info "Restarting backend App Service to apply settings..."
    az webapp restart --name "$BACKEND_APP_NAME" --resource-group "$RESOURCE_GROUP" --output none 2>/dev/null || true
fi

# =============================================================================
# FINAL SUMMARY
# =============================================================================

print_header "✅ DEPLOYMENT COMPLETE!"

echo "📋 Summary:"
echo ""
echo "Infrastructure:"
echo "  ✓ Backend URL: $BACKEND_URL"
echo "  ✓ Frontend URL: $FRONTEND_URL"
if [ -n "$BACKEND_APP_NAME" ]; then
    echo "  ✓ Backend App: $BACKEND_APP_NAME"
fi
if [ -n "$RESOURCE_GROUP" ]; then
    echo "  ✓ Resource Group: $RESOURCE_GROUP"
fi
echo ""

if [ -n "$AZURE_CLIENT_ID" ]; then
    echo "Azure AD SSO:"
    echo "  ✓ Client ID: $AZURE_CLIENT_ID"
    echo "  ✓ Tenant ID: $AZURE_TENANT_ID"
    echo "  ✓ Redirect URI: $AZURE_REDIRECT_URI"
    echo "  ✓ Backend configured: Yes"
    echo ""
fi

echo "📁 Configuration Files:"
[ -f "$SCRIPT_DIR/deployment-outputs-latest.txt" ] && echo "  - Infrastructure: $SCRIPT_DIR/deployment-outputs-latest.txt"
[ -f "$SCRIPT_DIR/azure-ad-app-latest.txt" ] && echo "  - Azure AD: $SCRIPT_DIR/azure-ad-app-latest.txt"
echo ""

print_header "🎯 NEXT STEPS"

echo "1️⃣  Frontend Environment Variables"
echo "   Add these to your frontend .env or GitHub secrets:"
echo ""
echo "   VITE_API_BASE_URL=$BACKEND_URL"
if [ -n "$AZURE_CLIENT_ID" ]; then
    echo "   VITE_AZURE_CLIENT_ID=$AZURE_CLIENT_ID"
    echo "   VITE_AZURE_TENANT_ID=$AZURE_TENANT_ID"
    echo "   VITE_AZURE_REDIRECT_URI=${FRONTEND_URL}/auth/callback"
fi
echo ""

echo "2️⃣  Deploy Your Code"
echo "   git add ."
echo "   git commit -m \"Configure Azure deployment with SSO\""
echo "   git push origin main"
echo ""

if [ -n "$BACKEND_APP_NAME" ]; then
    echo "3️⃣  Run Database Migrations"
    echo "   az webapp ssh --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
    echo "   cd /home/site/wwwroot && source antenv/bin/activate && alembic upgrade head"
    echo ""
fi

echo "4️⃣  Test Your Deployment"
echo "   Backend Health: ${BACKEND_URL}/api/v1/checks"
echo "   Frontend: $FRONTEND_URL"
if [ -n "$AZURE_CLIENT_ID" ]; then
    echo "   SSO Login: ${FRONTEND_URL}/signin (click 'Sign in with Microsoft')"
fi
echo ""

if [ -n "$AZURE_CLIENT_ID" ]; then
    print_warning "⚠️  SECURITY REMINDERS:"
    echo "   - Client Secret saved in: $SCRIPT_DIR/azure-ad-app-latest.txt"
    echo "   - Never commit secrets to version control"
    echo "   - Use Azure Key Vault in production"
    echo "   - Rotate client secret before expiration (2 years)"
    echo ""
fi

print_info "🎉 Deployment completed successfully!"
echo ""
