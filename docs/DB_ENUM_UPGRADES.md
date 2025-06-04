# Database Enum Upgrades - Phase 3.7

This document provides the playbook for safely adding new enum values to the bet-intel database without downtime.

## Overview

When adding new bet types, sports, or other enumerated values, follow this process to ensure zero-downtime deployments and forward compatibility.

## Enum Upgrade Process

### 1. Add New Value to Enum Definition

First, update your enum definition in the appropriate Python model:

```python
# In your SQLAlchemy model file
class BetType(enum.Enum):
    MONEYLINE = "h2h"
    SPREAD = "spreads" 
    TOTAL = "totals"
    PLAYER_POINTS = "player_points"
    # NEW: Add your new enum value
    PLAYER_ASSISTS = "player_assists"  # <- New addition
```

### 2. Generate Alembic Migration

Use Alembic's autogenerate feature to create the migration:

```bash
alembic revision --autogenerate -m "add enum value player_assists"
```

### 3. Edit the Migration File

**Important**: Alembic's autogenerate may not handle enum additions correctly. Manually edit the migration file to use PostgreSQL's safe enum addition:

```python
# In the generated migration file (e.g., versions/001_add_enum_value_player_assists.py)

def upgrade():
    # Use PostgreSQL's IF NOT EXISTS for safe enum addition
    op.execute("ALTER TYPE bet_type_enum ADD VALUE IF NOT EXISTS 'player_assists'")

def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # Consider using a feature flag approach for reversibility
    pass
```

### 4. Test Migration Locally

```bash
# Test upgrade
alembic upgrade head

# Verify enum values
psql -d your_database -c "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'bet_type_enum'::regtype;"
```

### 5. Deploy with Zero Downtime

```bash
# In production deployment
alembic upgrade head
```

The `IF NOT EXISTS` clause ensures the migration is idempotent and won't fail if the value already exists.

## Alternative: Feature Flag Approach

For complex enum changes or when you need rollback capability, consider using feature flags:

```python
# Instead of enum, use string field with validation
class BetType:
    VALID_TYPES = {
        "h2h": "Moneyline",
        "spreads": "Spread",
        "totals": "Total",
        "player_points": "Player Points",
        # Add new types here with feature flag checks
    }
    
    @classmethod
    def is_valid_type(cls, bet_type: str, feature_flags: Dict = None) -> bool:
        if bet_type in ["h2h", "spreads", "totals", "player_points"]:
            return True
        
        # New bet types behind feature flags
        if feature_flags and feature_flags.get("enable_player_assists"):
            if bet_type == "player_assists":
                return True
                
        return False
```

## Best Practices

### DO ✅
- Always use `IF NOT EXISTS` for enum additions
- Test migrations on a copy of production data
- Add comprehensive logging for new enum usage
- Update API documentation when adding new values
- Consider backward compatibility for client applications

### DON'T ❌ 
- Never remove enum values directly (breaks existing data)
- Don't deploy enum changes without proper testing
- Avoid complex enum modifications in a single migration
- Don't forget to update validation logic in application code

## Rollback Strategy

Since PostgreSQL doesn't support direct enum value removal:

1. **Immediate rollback**: Use feature flags to disable new functionality
2. **Long-term cleanup**: Plan a separate migration to clean up unused enum values
3. **Alternative**: Use string fields with application-level validation for complex enum evolution

## Example Migration Files

### Safe Enum Addition
```sql
-- Safe addition of new enum value
ALTER TYPE bet_type_enum ADD VALUE IF NOT EXISTS 'player_assists';
ALTER TYPE bet_type_enum ADD VALUE IF NOT EXISTS 'player_rebounds';
```

### Complex Enum Restructuring (Advanced)
```sql
-- For major enum changes, create new enum and migrate
CREATE TYPE bet_type_enum_new AS ENUM (
    'h2h', 'spreads', 'totals', 
    'player_points', 'player_assists', 'player_rebounds'
);

-- Update table to use new enum (requires application downtime)
ALTER TABLE bets ALTER COLUMN bet_type TYPE bet_type_enum_new 
    USING bet_type::text::bet_type_enum_new;

-- Drop old enum
DROP TYPE bet_type_enum;
ALTER TYPE bet_type_enum_new RENAME TO bet_type_enum;
```

## Integration with Phase 3 Pipeline

When adding new bet types, ensure:

1. **EV Calculation Pipeline** - Update `tasks/ev.py` to handle new bet types
2. **Cache Keys** - Update `core/cache.py` to include new bet type variations  
3. **Metrics** - Update `core/metrics.py` label sanitization for new types
4. **API Filtering** - Update role-based filtering in `app.py`

## Monitoring

After deploying enum changes:

```bash
# Monitor enum usage
SELECT bet_type, COUNT(*) FROM bets GROUP BY bet_type;

# Check for validation errors in logs
grep "Invalid bet_type" /var/log/bet-intel/app.log

# Verify cache performance with new enum values
redis-cli KEYS "*bet_type*" | wc -l
```

This process ensures that bet-intel can evolve its bet types safely while maintaining production stability. 