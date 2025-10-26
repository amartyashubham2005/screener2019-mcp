# Azure AD SSO Implementation Summary

## Overview

Azure Active Directory (Azure AD) Single Sign-On (SSO) has been successfully implemented for the MCP Admin UI application. Users can now sign in using their Microsoft accounts in addition to the existing email/password authentication.

## What Was Implemented

### Backend Changes

#### 1. Database Schema Updates
- **File**: `mcp-server-python/database/models.py`
- **Changes**: Added Azure AD-specific fields to the User model:
  - `azure_id`: Unique identifier from Azure AD
  - `azure_tenant_id`: Azure AD tenant identifier
  - `full_name`: User's display name from Azure AD
  - `auth_provider`: Authentication method ("local" or "azure")
  - Made `hashed_password` nullable (Azure AD users don't need passwords)

#### 2. Database Migration
- **File**: `mcp-server-python/migrations/versions/fd9b8c4c149f_add_azure_ad_authentication_fields_to_.py`
- **Changes**: Alembic migration to add Azure AD fields to the users table
- **To apply**: Run `alembic upgrade head` on the deployed server

#### 3. Azure AD Service
- **File**: `mcp-server-python/auth/azure_ad.py`
- **Features**:
  - OAuth 2.0 authorization URL generation
  - Authorization code exchange for access tokens
  - Microsoft Graph API integration for user profile retrieval
  - Configuration validation

#### 4. User Repository Updates
- **File**: `mcp-server-python/repositories/user_repository.py`
- **New Methods**:
  - `get_user_by_azure_id()`: Find users by Azure AD ID
  - `create_azure_user()`: Create new users from Azure AD authentication
  - `update_azure_user()`: Update Azure AD user information

#### 5. Authentication Endpoints
- **File**: `mcp-server-python/main.py`
- **New Endpoints**:
  - `GET /api/v1/auth/azure/login`: Initiates OAuth flow
  - `GET /api/v1/auth/azure/callback`: Handles OAuth callback
- **Updated Endpoints**:
  - `GET /api/v1/me`: Now returns `full_name` and `auth_provider`

### Frontend Changes

#### 1. Environment Variables
- **Files**:
  - `mcp-admin-ui/.env`
  - `mcp-admin-ui/.env.example`
- **New Variables**:
  ```bash
  VITE_AZURE_CLIENT_ID=731e44f2-dc31-4802-88cf-3bec822882bc
  VITE_AZURE_TENANT_ID=fd95fe1a-1798-4386-b8b9-882505eccaff
  VITE_AZURE_REDIRECT_URI=https://app.jesterbot.com/auth/callback
  ```

#### 2. Auth Service Updates
- **File**: `mcp-admin-ui/src/services/auth.ts`
- **New Methods**:
  - `initiateAzureLogin()`: Starts Azure AD OAuth flow
  - `getCurrentUser()`: Fetches current user details
- **Updated Interfaces**: Added `auth_provider` to user data

#### 3. Sign In Form
- **File**: `mcp-admin-ui/src/components/auth/SignInForm.tsx`
- **Changes**:
  - Added "Sign in with Microsoft" button with Microsoft logo
  - Added divider between email/password and SSO login
  - Implemented `handleAzureLogin()` function

#### 4. Azure Callback Page
- **File**: `mcp-admin-ui/src/pages/AuthPages/AzureCallback.tsx`
- **Features**:
  - Handles OAuth callback from Azure AD
  - Displays loading/success/error states
  - Validates authorization code and state
  - Calls backend callback endpoint
  - Redirects to dashboard on success

#### 5. App Routing
- **File**: `mcp-admin-ui/src/App.tsx`
- **Changes**: Added `/auth/callback` route for Azure AD callback

## How It Works

### OAuth 2.0 Authorization Code Flow

1. **User Clicks "Sign in with Microsoft"**
   - Frontend calls `GET /api/v1/auth/azure/login`
   - Backend generates authorization URL with state parameter (CSRF protection)
   - Backend stores state in HTTP-only cookie
   - Frontend redirects user to Azure AD login page

2. **User Authenticates with Microsoft**
   - User enters Microsoft credentials on Microsoft's login page
   - Microsoft validates credentials and requests user consent

3. **Azure AD Redirects Back to Application**
   - Azure AD redirects to: `https://app.jesterbot.com/auth/callback?code=xxx&state=yyy`
   - Frontend callback page extracts code and state from URL

4. **Backend Processes Callback**
   - Frontend calls `GET /api/v1/auth/azure/callback?code=xxx&state=yyy`
   - Backend validates state (CSRF protection)
   - Backend exchanges code for access token with Azure AD
   - Backend fetches user profile from Microsoft Graph API
   - Backend creates or updates user in database
   - Backend generates JWT token and sets it in HTTP-only cookie

5. **User is Logged In**
   - Frontend receives user data
   - Frontend stores user in AuthContext
   - User is redirected to dashboard (`/sources`)

## Azure AD Configuration

The deployment scripts automatically created an Azure AD app registration with the following configuration:

### App Registration Details
- **Application ID**: `731e44f2-dc31-4802-88cf-3bec822882bc`
- **Tenant ID**: `fd95fe1a-1798-4386-b8b9-882505eccaff`
- **Display Name**: `screener2019-mcp-sso-dev`

### Redirect URIs
- **Backend**: `https://api.jesterbot.com/api/v1/auth/azure/callback`
- **Frontend**: `https://app.jesterbot.com/auth/callback`

### API Permissions (Microsoft Graph - Delegated)
- `User.Read`: Read user profile
- `email`: Access user's email address
- `openid`: Sign users in
- `profile`: View basic profile info

### Admin Consent
Admin consent has been granted for all permissions.

## Environment Variables

### Backend (.env)
The following environment variables are already configured on the Azure App Service:

```bash
AZURE_CLIENT_ID=731e44f2-dc31-4802-88cf-3bec822882bc
AZURE_TENANT_ID=fd95fe1a-1798-4386-b8b9-882505eccaff
AZURE_CLIENT_SECRET=H3B8<redacted>azD
AZURE_REDIRECT_URI=https://api.jesterbot.com/api/v1/auth/azure/callback
```

### Frontend (.env)
Already configured in `mcp-admin-ui/.env`:

```bash
VITE_AZURE_CLIENT_ID=731e44f2-dc31-4802-88cf-3bec822882bc
VITE_AZURE_TENANT_ID=fd95fe1a-1798-4386-b8b9-882505eccaff
VITE_AZURE_REDIRECT_URI=https://app.jesterbot.com/auth/callback
```

## Deployment Steps

### 1. Apply Database Migration

SSH into the backend App Service:
```bash
az webapp ssh --name screener2019-mcp-dev-backend --resource-group screener2019-mcp-dev-rg
```

Inside the SSH session:
```bash
cd /home/site/wwwroot
source antenv/bin/activate
alembic upgrade head
```

### 2. Deploy Backend Code

The Azure App Service already has the environment variables configured. Just push the code:

```bash
cd mcp-server-python
git add .
git commit -m "Add Azure AD SSO authentication"
git push origin main
```

GitHub Actions will automatically deploy to Azure App Service.

### 3. Deploy Frontend Code

```bash
cd mcp-admin-ui
git add .
git commit -m "Add Azure AD SSO login button and callback handler"
git push origin main
```

GitHub Actions will automatically deploy to Azure Static Web Apps.

## Testing the Implementation

### 1. Test Azure AD Login Flow

1. Navigate to `https://app.jesterbot.com/signin`
2. Click "Sign in with Microsoft"
3. You should be redirected to Microsoft's login page
4. Enter your Microsoft credentials
5. After successful authentication, you should be redirected back to `https://app.jesterbot.com/auth/callback`
6. The callback page should process the authentication and redirect you to `/sources`

### 2. Verify User Creation

Check if the user was created in the database:

```sql
SELECT id, email, full_name, auth_provider, azure_id, created_at
FROM users
WHERE auth_provider = 'azure';
```

### 3. Test JWT Token

After logging in, check that the JWT token is set in cookies:
- Open browser DevTools → Application → Cookies
- Look for `access_token` cookie
- Domain should be `app.jesterbot.com`
- Should be HTTP-only and Secure

## Security Features

1. **CSRF Protection**: State parameter validates OAuth callback
2. **HTTP-Only Cookies**: JWT token stored in HTTP-only cookie (not accessible to JavaScript)
3. **Secure Cookies**: Cookies marked as Secure (HTTPS only)
4. **SameSite Policy**: Cookies use SameSite=Lax to prevent CSRF attacks
5. **Client Secret**: Stored securely in Azure App Service environment variables
6. **Token Expiration**: JWT tokens expire after 24 hours

## User Account Linking

If a user already has an account with email/password authentication and then signs in with Microsoft using the same email:
- The existing account will be upgraded to Azure AD authentication
- The user's Azure AD ID and tenant ID will be added to their profile
- The user can continue to use both authentication methods
- Their `auth_provider` field will be set to "azure"

## Troubleshooting

### Issue: "Azure AD authentication is not configured"
**Solution**: Verify that all Azure AD environment variables are set in the backend `.env` file or App Service configuration.

### Issue: "Invalid state parameter"
**Solution**: This is a CSRF protection error. Clear browser cookies and try again. The state cookie may have expired (10-minute timeout).

### Issue: "Failed to exchange code for token"
**Solution**: Check that:
- Azure AD client secret is correct
- Redirect URI matches exactly what's configured in Azure AD app registration
- App registration has the correct API permissions

### Issue: Redirect loop after authentication
**Solution**: Verify that the frontend redirect URI in `.env` matches the one configured in Azure AD app registration.

### Issue: "User not found" after successful Azure login
**Solution**: Check database connection and ensure migrations have been applied.

## Architecture Diagram

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       │ 1. Click "Sign in with Microsoft"
       │
       ↓
┌─────────────────────────────────────────────────────────┐
│                Frontend (app.jesterbot.com)              │
│  - Calls GET /api/v1/auth/azure/login                   │
│  - Redirects to Azure AD                                │
└──────────────────────────┬──────────────────────────────┘
                           │
                           │ 2. Redirect to Azure AD
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│           Azure AD (login.microsoftonline.com)          │
│  - User enters Microsoft credentials                     │
│  - Microsoft validates and gets consent                  │
└──────────────────────────┬──────────────────────────────┘
                           │
                           │ 3. Redirect with code & state
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│      Frontend Callback (/auth/callback)                 │
│  - Extracts code & state from URL                       │
│  - Calls backend callback with params                    │
└──────────────────────────┬──────────────────────────────┘
                           │
                           │ 4. GET /api/v1/auth/azure/callback
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│       Backend (api.jesterbot.com)                       │
│  - Validates state (CSRF)                               │
│  - Exchanges code for token                              │
│  - Gets user info from Microsoft Graph                   │
│  - Creates/updates user in database                      │
│  - Generates JWT token                                   │
│  - Sets JWT in HTTP-only cookie                          │
└──────────────────────────┬──────────────────────────────┘
                           │
                           │ 5. Returns user data
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│                Frontend - User Logged In                 │
│  - Stores user in AuthContext                            │
│  - Redirects to /sources dashboard                       │
└─────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Test thoroughly** on the deployed environment
2. **Monitor Azure AD sign-in logs** in Azure Portal for any issues
3. **Set up monitoring** for authentication failures
4. **Consider adding** profile pictures from Microsoft Graph API
5. **Add support for** refreshing user profile information periodically
6. **Implement token refresh** if needed (current JWT expires after 24 hours)

## Reference Documentation

- [Azure AD OAuth 2.0 Authorization Code Flow](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [Microsoft Graph API User Resource](https://docs.microsoft.com/en-us/graph/api/resources/user)
- [Authlib Documentation](https://docs.authlib.org/en/latest/)

## Support

For issues or questions:
1. Check Azure AD sign-in logs in Azure Portal
2. Check Application Insights logs for backend errors
3. Check browser console for frontend errors
4. Verify all environment variables are correctly set
