# 🚀 Local Development Setup - Quick Start

## What Was Changed

### ✅ Backend Configuration
**File**: `mcp-server-python/.env`
```bash
AZURE_REDIRECT_URI='https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback'
```

### ✅ Frontend Configuration
**File**: `mcp-admin-ui/.env`
```bash
VITE_API_BASE_URL=https://skylark-climbing-hermit.ngrok-free.app
VITE_AZURE_REDIRECT_URI=http://localhost:5173/auth/callback
```

## 🎯 What You Need to Do at Azure

You need to add the local development redirect URIs to your Azure AD app registration.

### Option 1: Run the Script (Easiest) 🔧

```bash
cd infrastructure
./add-local-redirect-uris.sh
```

This will automatically add all the required redirect URIs.

### Option 2: Manual Configuration via Azure CLI

```bash
az ad app update \
  --id 731e44f2-dc31-4802-88cf-3bec822882bc \
  --web-redirect-uris \
    "https://api.jesterbot.com/api/v1/auth/azure/callback" \
    "https://app.jesterbot.com/auth/callback" \
    "https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback" \
    "http://localhost:5173/auth/callback"
```

### Option 3: Azure Portal (Step-by-Step)

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Find **screener2019-mcp-sso-dev**
4. Click **Authentication** in left menu
5. Under **Web** → **Redirect URIs**, click **Add URI**
6. Add these two URIs:
   - `https://skylark-climbing-hermit.ngrok-free.app/api/v1/auth/azure/callback`
   - `http://localhost:5173/auth/callback`
7. Click **Save**

## 🧪 Testing Locally

### Step 1: Start Backend
```bash
cd mcp-server-python
source venv/bin/activate
python main.py
```

### Step 2: Start Ngrok
```bash
ngrok http 8000
```

### Step 3: Start Frontend
```bash
cd mcp-admin-ui
npm run dev
```

### Step 4: Test Azure SSO
1. Open: http://localhost:5173/signin
2. Click "Sign in with Microsoft"
3. Login with Microsoft credentials
4. Should redirect back and log you in!

## ⚠️ Important Notes

### If Ngrok URL Changes
Every time ngrok restarts, you might get a new URL. If that happens:

1. **Update backend `.env`**:
   ```bash
   AZURE_REDIRECT_URI='https://NEW-NGROK-URL.ngrok-free.app/api/v1/auth/azure/callback'
   ```

2. **Update Azure AD** (run the script again or update manually):
   ```bash
   cd infrastructure
   # Edit add-local-redirect-uris.sh and update LOCAL_BACKEND_URI
   ./add-local-redirect-uris.sh
   ```

3. **Restart backend** to load new .env

### Using Fixed Ngrok Subdomain
If you have ngrok Pro, use a fixed subdomain to avoid this:
```bash
ngrok http 8000 --subdomain=mcp-dev
```
This gives you: `https://mcp-dev.ngrok.io` (never changes)

## 📚 Full Documentation

For detailed troubleshooting and more information, see:
- **LOCAL_DEVELOPMENT_AZURE_SSO.md** - Complete local dev guide
- **AZURE_SSO_IMPLEMENTATION.md** - Technical implementation details
- **DEPLOYMENT_CHECKLIST.md** - Production deployment steps

## 🆘 Quick Troubleshooting

### "redirect_uri_mismatch" Error
→ The URI isn't added to Azure AD. Run the script or add manually.

### CORS Errors
→ Backend already configured for localhost:5173. Should work automatically.

### "Invalid state parameter"
→ Clear cookies for localhost:5173 and try again.

### Backend Not Responding
→ Check ngrok is running and pointing to port 8000: `ngrok http 8000`

## ✅ Success Checklist

After running the setup:

- [ ] Azure AD has 4 redirect URIs (2 prod + 2 local)
- [ ] Backend .env has ngrok URL
- [ ] Frontend .env has ngrok URL for API and localhost:5173 for redirect
- [ ] Backend server is running on port 8000
- [ ] Ngrok tunnel is active
- [ ] Frontend dev server is running on port 5173
- [ ] Can click "Sign in with Microsoft" button
- [ ] Successfully redirected to Microsoft login
- [ ] Successfully redirected back after login

## 🎉 Ready to Test!

Once Azure AD is configured (run the script), you're all set to test Azure SSO locally!
