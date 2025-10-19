# Azure SSO Deployment Checklist

## Pre-Deployment Verification

- [x] Azure AD app registration created
- [x] Admin consent granted for API permissions
- [x] Backend code changes completed
- [x] Frontend code changes completed
- [x] Environment variables configured
- [x] Database migration created

## Backend Deployment Steps

### 1. Apply Database Migration

```bash
# SSH into backend App Service
az webapp ssh --name screener2019-mcp-dev-backend --resource-group screener2019-mcp-dev-rg

# Inside SSH session
cd /home/site/wwwroot
source antenv/bin/activate
alembic upgrade head
```

**Expected Output**: Migration `fd9b8c4c149f` should be applied successfully

### 2. Verify Environment Variables

Check that these are set in Azure App Service:

```bash
az webapp config appsettings list \
  --name screener2019-mcp-dev-backend \
  --resource-group screener2019-mcp-dev-rg \
  --query "[?name=='AZURE_CLIENT_ID' || name=='AZURE_TENANT_ID' || name=='AZURE_CLIENT_SECRET' || name=='AZURE_REDIRECT_URI']"
```

Should show:
- `AZURE_CLIENT_ID=731e44f2-dc31-4802-88cf-3bec822882bc`
- `AZURE_TENANT_ID=fd95fe1a-1798-4386-b8b9-882505eccaff`
- `AZURE_CLIENT_SECRET=H3B8<redacted>azD`
- `AZURE_REDIRECT_URI=https://api.jesterbot.com/api/v1/auth/azure/callback`

### 3. Deploy Backend Code

```bash
cd /home/user/workstore/fiverr/screener2019/mcp/mcp-server-python
git add .
git commit -m "feat: Add Azure AD SSO authentication"
git push origin main
```

### 4. Verify Backend Deployment

Test the Azure login endpoint:
```bash
curl -i https://api.jesterbot.com/api/v1/auth/azure/login
```

Should return:
- Status: `200 OK`
- JSON with `authorization_url` pointing to `login.microsoftonline.com`

## Frontend Deployment Steps

### 1. Verify Environment Variables

Check `mcp-admin-ui/.env`:
```bash
cat mcp-admin-ui/.env
```

Should contain:
```
VITE_AZURE_CLIENT_ID=731e44f2-dc31-4802-88cf-3bec822882bc
VITE_AZURE_TENANT_ID=fd95fe1a-1798-4386-b8b9-882505eccaff
VITE_AZURE_REDIRECT_URI=https://jesterbot.com/auth/callback
```

### 2. Build and Deploy Frontend

```bash
cd /home/user/workstore/fiverr/screener2019/mcp/mcp-admin-ui
npm run build
git add .
git commit -m "feat: Add Azure AD SSO login UI"
git push origin main
```

### 3. Verify Frontend Deployment

Open browser and check:
- Navigate to: https://jesterbot.com/signin
- "Sign in with Microsoft" button should be visible
- Button should have Microsoft logo (4-colored square)

## Testing Checklist

### Test 1: Azure AD Login Initiation
- [ ] Navigate to https://jesterbot.com/signin
- [ ] Click "Sign in with Microsoft"
- [ ] Should redirect to Microsoft login page
- [ ] URL should start with `https://login.microsoftonline.com`

### Test 2: Microsoft Authentication
- [ ] Enter Microsoft credentials on login page
- [ ] Complete any MFA challenges if required
- [ ] Should see consent screen (first time only)
- [ ] Click "Accept" on consent screen

### Test 3: Callback Processing
- [ ] Should redirect to https://jesterbot.com/auth/callback
- [ ] Should see loading spinner briefly
- [ ] Should show success checkmark
- [ ] Should redirect to https://jesterbot.com/sources

### Test 4: User Session
- [ ] Dashboard should load successfully
- [ ] User menu should show user's email
- [ ] Navigation should work correctly
- [ ] Refresh page - should stay logged in

### Test 5: Database Verification
```sql
-- Check if Azure AD user was created
SELECT id, email, full_name, auth_provider, azure_id, azure_tenant_id
FROM users
WHERE auth_provider = 'azure'
ORDER BY created_at DESC
LIMIT 1;
```

Expected result:
- `auth_provider` = "azure"
- `azure_id` should be populated
- `azure_tenant_id` = "fd95fe1a-1798-4386-b8b9-882505eccaff"
- `full_name` should be the user's display name from Azure AD

### Test 6: JWT Token Verification
- [ ] Open browser DevTools → Application → Cookies
- [ ] Find cookie named `access_token`
- [ ] Domain: `jesterbot.com` or `.jesterbot.com`
- [ ] HttpOnly: Yes
- [ ] Secure: Yes
- [ ] SameSite: Lax

### Test 7: Logout
- [ ] Click user menu → Sign out
- [ ] Should redirect to /signin
- [ ] Cookie should be cleared
- [ ] Navigating to /sources should redirect to /signin

## Error Scenarios to Test

### Test Error 1: Invalid State
- [ ] Manually navigate to callback with wrong state
- [ ] Should show error message
- [ ] Should redirect back to /signin

### Test Error 2: Missing Code
- [ ] Navigate to callback without code parameter
- [ ] Should show error message
- [ ] Should redirect back to /signin

### Test Error 3: Expired State Cookie
- [ ] Start login flow but don't complete within 10 minutes
- [ ] Complete login after 10 minutes
- [ ] Should show "Invalid state parameter" error
- [ ] Should redirect back to /signin

## Post-Deployment Verification

### Check Application Insights Logs

```bash
# Backend logs - check for Azure AD auth events
az monitor app-insights query \
  --app screener2019-mcp-dev-insights \
  --analytics-query "traces | where message contains 'Azure' | order by timestamp desc | take 20"
```

### Check Azure AD Sign-in Logs

1. Go to Azure Portal
2. Navigate to Azure Active Directory
3. Go to Monitoring → Sign-in logs
4. Filter by Application ID: `731e44f2-dc31-4802-88cf-3bec822882bc`
5. Verify successful sign-ins appear

### Check App Service Logs

```bash
# Stream backend logs
az webapp log tail \
  --name screener2019-mcp-dev-backend \
  --resource-group screener2019-mcp-dev-rg
```

Look for:
- "Azure AD callback successful"
- "User created/updated from Azure AD"
- No errors related to Azure authentication

## Rollback Plan

If issues occur, rollback steps:

### Backend Rollback
```bash
cd mcp-server-python
git revert HEAD
git push origin main

# Or manually revert to previous commit
git reset --hard <previous-commit-hash>
git push origin main --force
```

### Frontend Rollback
```bash
cd mcp-admin-ui
git revert HEAD
git push origin main
```

### Database Rollback
```bash
# SSH into backend
az webapp ssh --name screener2019-mcp-dev-backend --resource-group screener2019-mcp-dev-rg

# Downgrade migration
cd /home/site/wwwroot
source antenv/bin/activate
alembic downgrade -1
```

## Monitoring After Deployment

### Week 1: Daily Checks
- [ ] Check Azure AD sign-in logs daily
- [ ] Monitor Application Insights for errors
- [ ] Check user feedback/support tickets
- [ ] Verify no authentication errors in logs

### Week 2-4: Weekly Checks
- [ ] Review authentication success rate
- [ ] Check for any unusual patterns
- [ ] Monitor token expiration issues
- [ ] Verify SSO is working for all users

## Success Criteria

✅ All tests pass
✅ No errors in Application Insights
✅ Azure AD sign-in logs show successful authentications
✅ Users can sign in with Microsoft accounts
✅ JWT tokens are properly set and validated
✅ User data is correctly stored in database
✅ Logout works correctly

## Contacts

**Azure Support**: [Azure Portal Support](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)
**Azure AD Issues**: Check [Azure AD health status](https://status.azure.com/status)
**Application Issues**: Check Application Insights and App Service logs

## Notes

- Client secret expires: **2 years from creation** (2027)
- Set calendar reminder to rotate secret before expiration
- Keep `deployment-outputs-latest.txt` and `azure-ad-app-latest.txt` files secure
- Never commit secrets to version control
