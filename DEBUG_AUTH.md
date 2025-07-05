# Debug: "Anonymous (Inactive)" Issue

## The Problem
The UI shows "Anonymous (Inactive)" even when a user is logged in successfully.

## Root Cause Analysis

The issue is in the authentication flow:

1. **User logs in successfully** → Gets valid JWT token
2. **AuthContext tries to fetch user role** → Calls `/api/user-info`
3. **Backend might be failing** → Returns "anonymous" role or fails entirely
4. **Frontend fallback** → User gets role "anonymous" which displays as "Anonymous"
5. **Subscription check** → Shows "(Inactive)" because anonymous users aren't active

## Files Involved

- `/frontend/src/contexts/AuthContext.tsx` - Lines 81-133 (fetchUserRole function)
- `/frontend/src/hooks/usePermissions.ts` - Line 26 (role assignment)
- `/frontend/src/pages/DashboardPage.tsx` - Lines 128-130 (display logic)

## Quick Debug Steps

### 1. Check what the backend is returning

Open browser console at http://localhost:5173 and look for these logs:

```
🔗 Making request to: /api/user-info
✅ User role fetched from backend: {role: "???", subscription_status: "???"}
```

OR

```
❌ Failed to fetch user role: 401 Unauthorized
⚠️ Falling back to original user (no role fetched)
```

### 2. Test the `/api/user-info` endpoint directly

In browser console:
```javascript
// Check auth state
window.authTest.checkAuthState()

// Manually test the endpoint
fetch('/api/user-info', {
  headers: {
    'Authorization': `Bearer ${JSON.parse(localStorage.getItem('sb-<project>-auth-token')).access_token}`
  }
})
.then(r => r.json())
.then(console.log)
```

### 3. Check backend logs

```bash
docker compose logs -f api | grep -i "user-info\|auth"
```

## Expected vs Actual Behavior

### Expected:
```
✅ User role fetched from backend: {role: "basic", subscription_status: "active"}
✅ Updated user object: {email: "user@example.com", role: "basic"}
```

### Actual (problematic):
```
❌ Failed to fetch user role: 500 Internal Server Error
⚠️ Falling back to original user (no role fetched)
⚠️ Fallback user: {email: "user@example.com", role: undefined}
```

## Quick Fixes to Try

### Fix 1: Add better error handling in AuthContext

```typescript
// In fetchUserRole function, add more detailed logging:
console.log('Response status:', response.status);
console.log('Response headers:', response.headers);
const responseText = await response.text();
console.log('Response body:', responseText);
```

### Fix 2: Set proper default role in usePermissions

```typescript
// Instead of defaulting to 'free', handle the case better:
const userRole: UserRole = (user?.user_metadata?.role as UserRole) || 
  (isAuthenticated ? 'basic' : 'free');
```

### Fix 3: Check backend authentication

The `/api/user-info` endpoint might be:
- Not recognizing the JWT token
- Having database connection issues
- Not finding the user record in the backend database

## Most Likely Issues

1. **Backend Database Issue**: User exists in Supabase auth but not in your backend database
2. **JWT Verification Issue**: Backend can't verify the Supabase JWT
3. **CORS/Proxy Issue**: Frontend can't reach the backend properly
4. **Environment Variables**: Backend missing Supabase keys for JWT verification

## Immediate Test Commands

```bash
# 1. Check if backend is reachable
curl http://localhost:8000/health

# 2. Check if user-info endpoint exists (should return 401 without auth)
curl http://localhost:8000/api/user-info

# 3. Check backend logs for errors
docker compose logs api --tail=50

# 4. Check if backend has proper Supabase config
docker compose exec api env | grep SUPABASE
```

Run these tests and let me know what the output shows!