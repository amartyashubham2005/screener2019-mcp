# Local Development Setup for Azure AD SSO

## Current Local Setup
- **Frontend**: http://localhost:5173 (Vite dev server)
- **Backend**: https://skylark-climbing-hermit.ngrok-free.app (ngrok tunnel)

## Configuration Changes Made

### ✅ Backend `.env` Updated
```bash
AZURE_REDIRECT_URI='https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback'
```

### ✅ Frontend `.env` Updated
```bash
VITE_API_BASE_URL=https://skylark-climbing-hermit.ngrok-free.app
VITE_AZURE_REDIRECT_URI=http://localhost:5173/auth/callback
```

## Azure AD App Registration Configuration Required

You need to add the local development redirect URIs to your Azure AD app registration. Here are two ways to do it:

---

## Method 1: Using Azure CLI (Recommended - Fastest)

Run this command to add both redirect URIs:

```bash
az ad app update \
  --id 731e44f2-dc31-4802-88cf-3bec822882bc \
  --web-redirect-uris \
    "https://api.jesterbot.com/api/v1/auth/azure/callback" \
    "https://app.jesterbot.com/auth/callback" \
    "https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback" \
    "http://localhost:5173/auth/callback"
```

**Note**: This keeps your existing production URIs and adds the new local development URIs.

---

## Method 2: Using Azure Portal (Step-by-Step)

### Step 1: Navigate to Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Azure Active Directory" in the top search bar
3. Click on **Azure Active Directory**
4. In the left menu, click **App registrations**
5. Click on **All applications** tab
6. Find and click on **screener2019-mcp-sso-dev**

### Step 2: Add Redirect URIs

1. In the left menu, click **Authentication**
2. Under **Platform configurations**, find **Web** section
3. Click **Add URI** button (you'll see it under the existing redirect URIs)

4. Add the following URIs one by one:

   **Backend Ngrok URI:**
   ```
   https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback
   ```

   **Frontend Localhost URI:**
   ```
   http://localhost:5173/auth/callback
   ```

5. Click **Save** at the bottom of the page

### Step 3: Verify Configuration

Your redirect URIs should now show:

✅ **Production URIs** (already configured):
- `https://api.jesterbot.com/api/v1/auth/azure/callback`
- `https://app.jesterbot.com/auth/callback`

✅ **Development URIs** (newly added):
- `https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback`
- `http://localhost:5173/auth/callback`

**Screenshot Reference:**

```
Platform configurations
━━━━━━━━━━━━━━━━━━━━
Web
  Redirect URIs
    • https://api.jesterbot.com/api/v1/auth/azure/callback
    • https://app.jesterbot.com/auth/callback
    • https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback
    • http://localhost:5173/auth/callback
```

---

## Important Notes About Ngrok

### ⚠️ Ngrok URL Changes

**If your ngrok URL changes**, you'll need to:

1. **Update backend `.env`**:
   ```bash
   AZURE_REDIRECT_URI='https://YOUR-NEW-NGROK-URL.ngrok-free.app/api/v1/auth/azure/callback'
   ```

2. **Update Azure AD redirect URIs** (use one of the methods above):
   ```bash
   az ad app update \
     --id 731e44f2-dc31-4802-88cf-3bec822882bc \
     --web-redirect-uris \
       "https://api.jesterbot.com/api/v1/auth/azure/callback" \
       "https://app.jesterbot.com/auth/callback" \
       "https://YOUR-NEW-NGROK-URL.ngrok-free.app/api/v1/auth/azure/callback" \
       "http://localhost:5173/auth/callback"
   ```

3. **Restart your backend** to load the new environment variable

### 💡 Using Ngrok with Fixed Subdomain (Paid Feature)

If you have ngrok Pro/Business, you can use a fixed subdomain:

```bash
ngrok http 8000 --subdomain=mcp-dev
```

This gives you a consistent URL: `https://mcp-dev.ngrok.io`

---

## Testing Local Azure SSO

### Step 1: Start Backend Server

```bash
cd mcp-server-python
source venv/bin/activate
python main.py
```

Should show:
```
Starting MCP server on 0.0.0.0:8000 (SSE)
```

### Step 2: Start Ngrok Tunnel

In a new terminal:
```bash
ngrok http 8000
```

**Important**: If the ngrok URL changed from `skylark-climbing-hermit.ngrok-free.app`, update:
- Backend `.env` → `AZURE_REDIRECT_URI`
- Azure AD app registration redirect URIs

### Step 3: Start Frontend Dev Server

```bash
cd mcp-admin-ui
npm run dev
```

Should show:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Step 4: Test Azure SSO Flow

1. Open browser: http://localhost:5173/signin
2. Click **"Sign in with Microsoft"**
3. You should be redirected to Microsoft login page
4. Enter your Microsoft credentials
5. After authentication, you should be redirected back to http://localhost:5173/auth/callback
6. The callback page should show a loading spinner, then success
7. You should be redirected to http://localhost:5173/sources

### Step 5: Verify in Browser DevTools

**Check Cookies:**
- Open DevTools → Application → Cookies → `http://localhost:5173`
- Should see `access_token` cookie
- Note: For localhost, the cookie won't be marked as "Secure"

**Check Console:**
- Should see: `API_BASE_URL https://skylark-climbing-hermit.ngrok-free.app`
- No CORS errors should appear

**Check Network Tab:**
- Request to `/api/v1/auth/azure/login` should return 200 with `authorization_url`
- Request to `/api/v1/auth/azure/callback` should return 200 with user data

---

## Common Issues & Solutions

### Issue 1: "redirect_uri_mismatch" Error

**Symptom**: Azure shows error: "The reply URL specified in the request does not match..."

**Solution**:
1. Check the exact redirect URI in the error message
2. Add that exact URI to Azure AD app registration
3. Make sure there are no trailing slashes or typos

### Issue 2: CORS Errors

**Symptom**: Browser console shows CORS errors when calling backend

**Solution**:
The backend `main.py` already has CORS configured for localhost. Verify these origins are included:
```python
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # ✅ Your Vite dev server
    "http://localhost:8080",
    "https://app.jesterbot.com"
]
```

### Issue 3: "Invalid state parameter"

**Symptom**: Error during callback: "Invalid state parameter"

**Solution**:
1. Clear browser cookies for localhost:5173
2. Try the login flow again
3. State cookie may have expired (10-minute timeout)

### Issue 4: Backend Not Accessible via Ngrok

**Symptom**: Ngrok tunnel shows connection errors

**Solutions**:
1. Make sure backend is running on port 8000
2. Check ngrok dashboard: http://localhost:4040
3. Verify ngrok is forwarding to correct port:
   ```bash
   ngrok http 8000
   ```

### Issue 5: "Access token required in cookies"

**Symptom**: After successful Azure login, requests fail with auth error

**Solution**:
1. Check that callback successfully set the cookie
2. Verify `credentials: "include"` is set in frontend API calls (already done in `api.ts`)
3. Check browser cookie settings allow third-party cookies

---

## Switching Between Local and Production

### For Local Development:

**Backend `.env`:**
```bash
AZURE_REDIRECT_URI='https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback'
```

**Frontend `.env`:**
```bash
VITE_API_BASE_URL=https://skylark-climbing-hermit.ngrok-free.app
VITE_AZURE_REDIRECT_URI=http://localhost:5173/auth/callback
```

### For Production Deployment:

**Backend `.env`:**
```bash
AZURE_REDIRECT_URI='https://api.jesterbot.com/api/v1/auth/azure/callback'
```

**Frontend `.env`:**
```bash
VITE_API_BASE_URL=https://api.jesterbot.com
VITE_AZURE_REDIRECT_URI=https://app.jesterbot.com/auth/callback
```

**Note**: You can use different `.env` files:
- `.env.local` for local development
- `.env.production` for production deployment

---

## Alternative: Using ngrok for Frontend Too

If you want to test with HTTPS for frontend as well:

1. **Start frontend ngrok:**
   ```bash
   ngrok http 5173
   ```

   Let's say it gives: `https://abc123.ngrok-free.app`

2. **Update frontend `.env`:**
   ```bash
   VITE_AZURE_REDIRECT_URI=https://abc123.ngrok-free.app/auth/callback
   ```

3. **Add to Azure AD redirect URIs:**
   ```bash
   az ad app update \
     --id 731e44f2-dc31-4802-88cf-3bec822882bc \
     --web-redirect-uris \
       "https://api.jesterbot.com/api/v1/auth/azure/callback" \
       "https://app.jesterbot.com/auth/callback" \
       "https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback" \
       "https://abc123.ngrok-free.app/auth/callback"
   ```

4. **Access via ngrok URL:** `https://abc123.ngrok-free.app/signin`

---

## Quick Reference Commands

### Add Redirect URIs (Azure CLI)
```bash
az ad app update \
  --id 731e44f2-dc31-4802-88cf-3bec822882bc \
  --web-redirect-uris \
    "https://api.jesterbot.com/api/v1/auth/azure/callback" \
    "https://app.jesterbot.com/auth/callback" \
    "https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback" \
    "http://localhost:5173/auth/callback"
```

### View Current Redirect URIs
```bash
az ad app show \
  --id 731e44f2-dc31-4802-88cf-3bec822882bc \
  --query "web.redirectUris"
```

### Start Local Development Environment
```bash
# Terminal 1: Backend
cd mcp-server-python
source venv/bin/activate
python main.py

# Terminal 2: Ngrok
ngrok http 8000

# Terminal 3: Frontend
cd mcp-admin-ui
npm run dev
```

---

## Azure Portal Quick Links

- **App Registration**: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/731e44f2-dc31-4802-88cf-3bec822882bc
- **Authentication Settings**: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Authentication/appId/731e44f2-dc31-4802-88cf-3bec822882bc
- **API Permissions**: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/731e44f2-dc31-4802-88cf-3bec822882bc

---

## Summary Checklist

Before testing locally, ensure:

- [ ] Backend `.env` has ngrok URL in `AZURE_REDIRECT_URI`
- [ ] Frontend `.env` has ngrok URL in `VITE_API_BASE_URL`
- [ ] Frontend `.env` has localhost:5173 in `VITE_AZURE_REDIRECT_URI`
- [ ] Azure AD app has both redirect URIs added
- [ ] Backend server is running
- [ ] Ngrok tunnel is running and pointing to backend
- [ ] Frontend dev server is running on port 5173
- [ ] Browser has no old cookies for localhost:5173

Ready to test! 🚀
