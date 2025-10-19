# Azure SSO Local Development - "Invalid State Parameter" Fix

## Problem

You were getting this error during Azure AD callback:
```json
{
  "detail": "Invalid state parameter"
}
```

## Root Cause

The issue is with **cookie settings for cross-origin requests** in your local development setup:

- **Frontend**: `http://localhost:5173`
- **Backend**: `https://skylark-climbing-hermit.ngrok-free.app` (HTTPS via ngrok)

When the backend sets the `azure_state` cookie, it was configured with:
- `secure=True` (requires HTTPS)
- `samesite="lax"` (restricts cross-origin cookie sending)

However, when Microsoft redirects back to your frontend at `http://localhost:5173/auth/callback`, and the frontend then calls the backend callback endpoint, **the cookie wasn't being sent** because:

1. The cookie was set on the ngrok domain (`.ngrok-free.app`)
2. The request was coming from `localhost:5173` (different origin)
3. `SameSite=Lax` prevents the cookie from being sent in cross-site requests
4. The browser blocked the cookie due to cross-origin restrictions

## Solution Applied

Changed the cookie settings in `main.py` for Azure AD authentication:

### Before:
```python
response.set_cookie(
    key="azure_state",
    value=state,
    httponly=True,
    secure=True,        # ❌ Requires HTTPS
    samesite="lax",     # ❌ Blocks cross-origin
    max_age=600
)
```

### After:
```python
response.set_cookie(
    key="azure_state",
    value=state,
    httponly=True,
    secure=False,       # ✅ Works with HTTP localhost
    samesite="none",    # ✅ Allows cross-origin cookies
    max_age=600
)
```

The same fix was applied to:
1. `azure_state` cookie (CSRF protection)
2. `access_token` cookie (JWT authentication)

## Files Modified

**File**: `mcp-server-python/main.py`

**Lines changed**:
- Line ~239: `azure_state` cookie in `/api/v1/auth/azure/login`
- Line ~350: `access_token` cookie in `/api/v1/auth/azure/callback`
- Line ~357: `delete_cookie` for `azure_state`

## Important Notes

### For Local Development

These settings (`secure=False`, `samesite="none"`) are **appropriate for local development** where:
- Frontend runs on `localhost` (HTTP)
- Backend runs on `ngrok` (HTTPS)
- Cross-origin requests are necessary

### For Production Deployment

**You MUST change these settings back for production**:

```python
# Production settings (for api.jesterbot.com)
response.set_cookie(
    key="azure_state",
    value=state,
    httponly=True,
    secure=True,        # ✅ HTTPS only
    samesite="lax",     # ✅ CSRF protection
    max_age=600
)
```

**Why?**
- Production has both frontend and backend on HTTPS
- Production has same-site (both on `jesterbot.com` domain)
- `SameSite=Lax` provides better CSRF protection
- `Secure=True` ensures cookies only sent over HTTPS

## How to Test Now

1. **Restart your backend** (to load the new cookie settings):
   ```bash
   cd mcp-server-python
   source venv/bin/activate
   python main.py
   ```

2. **Make sure ngrok is running**:
   ```bash
   ngrok http 8000
   ```

3. **Start frontend**:
   ```bash
   cd mcp-admin-ui
   npm run dev
   ```

4. **Test the flow**:
   - Go to: http://localhost:5173/signin
   - Click "Sign in with Microsoft"
   - Complete Microsoft login
   - Should now successfully redirect back and log you in!

## Verification

### Check Cookie is Set

After clicking "Sign in with Microsoft", open browser DevTools:

1. **Network Tab** → Find request to `/api/v1/auth/azure/login`
2. **Response Headers** should show:
   ```
   Set-Cookie: azure_state=xxx; HttpOnly; Max-Age=600; Path=/; SameSite=None
   ```

### Check Cookie is Sent

When redirected back to `/api/v1/auth/azure/callback`:

1. **Network Tab** → Find request to `/api/v1/auth/azure/callback`
2. **Request Headers** should show:
   ```
   Cookie: azure_state=xxx
   ```

If you see the cookie in the request headers, it means the fix worked! ✅

## Alternative Approach: Using Environment Variable

For a more flexible solution, you could use an environment variable to toggle between local and production settings:

```python
import os

IS_LOCAL_DEV = os.getenv("IS_LOCAL_DEV", "false").lower() == "true"

response.set_cookie(
    key="azure_state",
    value=state,
    httponly=True,
    secure=not IS_LOCAL_DEV,  # False for local, True for production
    samesite="none" if IS_LOCAL_DEV else "lax",
    max_age=600
)
```

Then in your `.env`:
```bash
# For local development
IS_LOCAL_DEV=true

# For production (or omit entirely)
IS_LOCAL_DEV=false
```

## Security Implications

### Local Development (Current Settings)
- `secure=False`: Allows cookies over HTTP (needed for localhost)
- `samesite=none`: Allows cross-origin cookies (needed for localhost → ngrok)
- **Security**: Lower (but acceptable for local testing)

### Production (Must Change)
- `secure=True`: Cookies only sent over HTTPS
- `samesite=lax`: Prevents CSRF attacks
- **Security**: High (required for production)

## Summary

✅ **Fixed**: Changed cookie settings to allow cross-origin cookies for local development
⚠️ **Action Required**: Must change back to secure settings before production deployment
🧪 **Test**: Restart backend and try Azure SSO again

The Azure SSO flow should now work locally! 🚀
