# Deployment Changes Summary
**Date:** July 1, 2025  
**Deployment:** Fresh production deployment to Hetzner server (178.156.185.113)

## Files Modified During Deployment

### 1. `core/auth.py` 
**Issue:** Database dependency causing 500 errors  
**Fix:** Removed `db: AsyncSession = Depends(get_db)` parameters from authentication functions
- `get_current_user()` - Removed db parameter  
- `get_optional_user()` - Removed db parameter
- `get_user_or_none()` - Removed db parameter

**Impact:** Resolves 500 Internal Server Error on `/api/user-info` and `/api/opportunities`

### 2. `docker/caddy/Caddyfile`
**Issue:** Caddy auto-redirecting HTTP to HTTPS causing redirect loop with Cloudflare  
**Fix:** Changed `dock108.ai {` to `dock108.ai:80 {` to disable auto-HTTPS redirect

**Impact:** Fixes "Too many redirects" error when accessing https://dock108.ai

### 3. `frontend/.env` (Server Only)
**Created:** Production frontend environment configuration
```bash
VITE_API_URL=https://dock108.ai
VITE_PUBLIC_URL=https://dock108.ai
VITE_APP_ENV=production
# ... other production settings
```
**Saved locally as:** `frontend/.env.production.server`

### 4. `.env` (Server Only) 
**Used:** Existing `.env.production` configuration for backend
```bash
ENVIRONMENT=production
REFRESH_INTERVAL_MINUTES=30
# ... production settings with dock108.ai URLs
```
**Saved locally as:** `.env.production.server`

## Deployment Results

✅ **All Systems Operational:**
- **Frontend**: https://dock108.ai
- **API**: https://dock108.ai/health  
- **Database Consolidation**: Fixed and deployed
- **Production Schedule**: 30-minute intervals during business hours
- **Authentication**: Working (no more 500 errors)
- **Cloudflare**: Properly routing (no more redirect loops)

## Database Fix Deployed
The consolidation logic fix from `services/sync_bet_persistence.py` is now active:
- Bet offers load as single consolidated rows instead of multiple rows per sportsbook
- `books_count` properly reflects number of books per bet
- 30-minute refresh intervals during 7 AM - 10 PM EST

## Next Steps
- Monitor https://dock108.ai for proper data loading
- Verify bet cards show consolidated data (single rows with multiple book odds)
- Check production refresh schedule is working as expected