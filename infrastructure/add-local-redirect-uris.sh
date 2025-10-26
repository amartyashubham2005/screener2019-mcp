#!/bin/bash

# Script to add local development redirect URIs to Azure AD app registration
# This allows testing Azure SSO locally with localhost and ngrok

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}Adding Local Development Redirect URIs${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Azure AD App Configuration
APP_ID="731e44f2-dc31-4802-88cf-3bec822882bc"
APP_NAME="screener2019-mcp-sso-dev"

# Redirect URIs
PROD_BACKEND_URI="https://api.jesterbot.com/api/v1/auth/azure/callback"
PROD_FRONTEND_URI="https://app.jesterbot.com/auth/callback"
LOCAL_BACKEND_URI="https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback"
LOCAL_FRONTEND_URI="http://localhost:5173/auth/callback"

echo -e "${YELLOW}Current Configuration:${NC}"
echo "  App ID: $APP_ID"
echo "  App Name: $APP_NAME"
echo ""

echo -e "${YELLOW}Redirect URIs to configure:${NC}"
echo "  Production Backend:  $PROD_BACKEND_URI"
echo "  Production Frontend: $PROD_FRONTEND_URI"
echo "  Local Backend:       $LOCAL_BACKEND_URI"
echo "  Local Frontend:      $LOCAL_FRONTEND_URI"
echo ""

# Check if Azure CLI is logged in
echo -e "${BLUE}[1/3]${NC} Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Azure. Please login...${NC}"
    az login
fi

TENANT_ID=$(az account show --query tenantId -o tsv)
echo -e "${GREEN}✓${NC} Logged in to tenant: $TENANT_ID"
echo ""

# Show current redirect URIs
echo -e "${BLUE}[2/3]${NC} Fetching current redirect URIs..."
CURRENT_URIS=$(az ad app show --id "$APP_ID" --query "web.redirectUris" -o json 2>/dev/null || echo "[]")
echo -e "${GREEN}✓${NC} Current redirect URIs:"
echo "$CURRENT_URIS" | jq -r '.[]' | while read uri; do
    echo "    • $uri"
done
echo ""

# Update redirect URIs
echo -e "${BLUE}[3/3]${NC} Updating redirect URIs..."
az ad app update \
    --id "$APP_ID" \
    --web-redirect-uris \
        "$PROD_BACKEND_URI" \
        "$PROD_FRONTEND_URI" \
        "$LOCAL_BACKEND_URI" \
        "$LOCAL_FRONTEND_URI"

echo -e "${GREEN}✓${NC} Redirect URIs updated successfully!"
echo ""

# Verify update
echo -e "${YELLOW}Verifying configuration...${NC}"
UPDATED_URIS=$(az ad app show --id "$APP_ID" --query "web.redirectUris" -o json)
echo "$UPDATED_URIS" | jq -r '.[]' | while read uri; do
    echo "  ✓ $uri"
done
echo ""

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✅ Configuration Complete!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Make sure your backend .env has:"
echo "   AZURE_REDIRECT_URI='$LOCAL_BACKEND_URI'"
echo ""
echo "2. Make sure your frontend .env has:"
echo "   VITE_API_BASE_URL=https://skylark-climbing-hermit.ngrok-free.app"
echo "   VITE_AZURE_REDIRECT_URI=$LOCAL_FRONTEND_URI"
echo ""
echo "3. Start your development environment:"
echo "   Terminal 1: cd mcp-server-python && source venv/bin/activate && python main.py"
echo "   Terminal 2: ngrok http 8000"
echo "   Terminal 3: cd mcp-admin-ui && npm run dev"
echo ""
echo "4. Test Azure SSO:"
echo "   Open http://localhost:5173/signin and click 'Sign in with Microsoft'"
echo ""

echo -e "${BLUE}Note:${NC} If your ngrok URL changes, run this script again and update"
echo "LOCAL_BACKEND_URI at the top of this script, then re-run."
echo ""
