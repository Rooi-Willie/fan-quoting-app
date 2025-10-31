# Quote Reference System - Hybrid Auto-Generation

## Overview
Implemented a hybrid quote reference system that auto-generates unique references while allowing manual override with validation.

## Pattern
**Format**: `Q[FULL_NAME_INITIALS][NUMBER]`
- Example: `QBV0001` for Bernard Viviers
- Example: `QJD0002` for Jane Doe
- Globally unique across all original quotes
- Revisions share the same reference as their original

## Implementation Details

### Phase 1: Database Constraint ✅
**File**: `database/init-scripts/01-schema.sql`

Added unique constraint to prevent duplicate original quotes:
```sql
CREATE UNIQUE INDEX unique_original_quote_ref 
ON quotes(quote_ref) 
WHERE original_quote_id IS NULL;
```

**Effect**: Database will reject duplicate quote_ref for original quotes, but allow revisions to share the same ref.

---

### Phase 2: API Endpoints ✅
**File**: `api/app/routers/saved_quotes.py`

#### 1. Get Next Quote Reference
```http
GET /saved-quotes/next-reference?user_initials=BV
```
**Response**:
```json
{
  "next_ref": "QBV0002",
  "pattern": "Q[INITIALS][NUMBER]",
  "example": "QBV0001"
}
```

#### 2. Validate Quote Reference
```http
GET /saved-quotes/validate-reference/QBV0001
```
**Response (Available)**:
```json
{
  "is_available": true,
  "quote_ref": "QBV0001"
}
```

**Response (Not Available)**:
```json
{
  "is_available": false,
  "quote_ref": "QBV0001",
  "suggestion": "QBV0002"
}
```

---

### Phase 3: CRUD Functions ✅
**File**: `api/app/crud.py`

#### Functions Added:

1. **`is_quote_ref_available(db, quote_ref)`**
   - Checks if a quote reference is available
   - Only checks original quotes (not revisions)
   - Returns True if available

2. **`generate_next_quote_ref(db, user_initials)`**
   - Generates next available quote reference
   - Pattern: Q[INITIALS][0000]
   - Extracts max number from existing quotes
   - Returns incremented number with leading zeros

**Logic**:
```python
# Find all quotes like "QBV0001", "QBV0002", etc.
# Extract numbers: [1, 2]
# Get max: 2
# Return: QBV0003
```

---

### Phase 4: Auto-Generation in UI ✅
**File**: `ui/common.py`

#### Function: `_fetch_next_quote_ref(user_initials)`
- Calls API endpoint to get next reference
- Falls back to pattern-based generation if API fails
- Used by `_new_quote_data()` when creating new quotes

#### Updated: `_new_quote_data()`
- Extracts user initials from full_name
- Example: "Bernard Viviers" → "BV"
- Calls `_fetch_next_quote_ref("BV")`
- Pre-populates quote reference automatically

---

### Phase 5: Validation & Auto-Suffix ✅
**File**: `ui/pages/quote_creation_tabs/review_quote_tab.py`

#### Function: `save_quote()`

**On CREATE (new quote)**:
1. Check if quote_ref is available via API
2. If NOT available:
   - Auto-append suffix: `QBV0001` → `QBV0001-A`
   - Try suffixes A-Z in sequence
   - If all exhausted, use suggested next number
   - Show warning to user about auto-adjustment
3. Proceed with save using validated/adjusted ref

**On UPDATE (edit quote)**:
- No validation needed (quote_ref is read-only when editing)

---

## User Experience

### Scenario 1: Normal Flow ✅
1. User clicks "Create New Quote"
2. System auto-generates: `QBV0001`
3. User fills in quote details
4. User clicks "Save Quote"
5. Quote saved successfully

### Scenario 2: Manual Override ✅
1. User clicks "Create New Quote"
2. System auto-generates: `QBV0002`
3. User manually changes to: `CUSTOM001`
4. User clicks "Save Quote"
5. System validates uniqueness
6. Quote saved if available, otherwise auto-suffixed

### Scenario 3: Duplicate Reference ✅
1. User clicks "Create New Quote"
2. User manually enters: `QBV0001` (already exists)
3. User clicks "Save Quote"
4. System detects duplicate
5. Auto-adjusts to: `QBV0001-A`
6. Shows warning: "Quote reference 'QBV0001' already exists. Auto-adjusted to 'QBV0001-A'"
7. Quote saved successfully

### Scenario 4: Edit Existing Quote ✅
1. User clicks "Edit Quote" on `QBV0001`
2. Quote reference field is **disabled** (read-only)
3. Tooltip: "Quote reference cannot be changed when editing to maintain revision history integrity"
4. User can edit other fields
5. Save updates the quote without changing ref

### Scenario 5: Create Revision ✅
1. User selects quote `QBV0001 Rev 1`
2. User clicks "Create New Revision"
3. System creates: `QBV0001 Rev 2`
4. Same quote_ref, incremented revision_number
5. Both linked via original_quote_id

---

## Database Behavior

### Original Quotes
```sql
-- These are UNIQUE (enforced by partial index)
id | quote_ref | original_quote_id | revision_number
1  | QBV0001   | NULL              | 1
2  | QBV0002   | NULL              | 1
3  | QJD0001   | NULL              | 1
```

### Revisions
```sql
-- These SHARE quote_ref with original (allowed by partial index)
id | quote_ref | original_quote_id | revision_number
4  | QBV0001   | 1                 | 2
5  | QBV0001   | 1                 | 3
6  | QBV0002   | 2                 | 2
```

**Key Point**: The unique constraint ONLY applies when `original_quote_id IS NULL`, allowing revisions to share the same ref.

---

## Pattern Flexibility

The system is designed to be flexible:

### Current Pattern
```python
# Pattern: Q[INITIALS][NUMBER]
user_initials = "BV"  # From "Bernard Viviers"
quote_ref = f"Q{user_initials}0001"  # → QBV0001
```

### Future Pattern Changes
To change the pattern, modify:

1. **`crud.generate_next_quote_ref()`** - Generation logic
2. **`_fetch_next_quote_ref()`** - Fallback pattern
3. **`_new_quote_data()`** - Initials extraction logic

Example alternative patterns:
- `[YEAR]-Q[INITIALS]-[NUMBER]` → `2025-QBV-0001`
- `Q[INITIALS][MONTH][NUMBER]` → `QBV100001`
- `[DEPT]-[INITIALS]-[NUMBER]` → `SALES-BV-0001`

---

## Testing Checklist

### After Deployment
- [ ] Rebuild database (drops all quotes, applies new constraint)
- [ ] Create new quote as Bernard Viviers → Should get `QBV0001`
- [ ] Create another quote as Bernard → Should get `QBV0002`
- [ ] Manually change ref to `QBV0001` → Should auto-adjust to `QBV0001-A`
- [ ] Edit existing quote → Ref field should be disabled
- [ ] Create revision → Should share same ref, increment revision_number
- [ ] Verify revision history shows all versions correctly

---

## Migration Notes

### For Existing Database
If you have existing quotes and don't want to rebuild:

1. Run this SQL to add the constraint:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS unique_original_quote_ref 
ON quotes(quote_ref) 
WHERE original_quote_id IS NULL;
```

2. Check for existing duplicates:
```sql
SELECT quote_ref, COUNT(*) 
FROM quotes 
WHERE original_quote_id IS NULL 
GROUP BY quote_ref 
HAVING COUNT(*) > 1;
```

3. If duplicates exist, manually fix them:
```sql
-- Example: Update duplicate QB001 to QB001-A
UPDATE quotes 
SET quote_ref = 'QB001-A' 
WHERE id = [duplicate_id];
```

---

## Deployment Steps

1. **Stop containers**:
   ```bash
   docker-compose down
   ```

2. **Rebuild database** (if fresh start):
   ```bash
   docker-compose up -d postgres
   # Database will run init scripts automatically
   ```

3. **Restart all services**:
   ```bash
   docker-compose up -d --build
   ```

4. **Test the system** with the checklist above

---

## Summary

✅ **Auto-generation**: Saves user time and ensures consistency
✅ **Manual override**: Power users can customize if needed
✅ **Uniqueness validation**: Prevents data corruption
✅ **Auto-suffix**: Handles edge cases gracefully
✅ **Revision safety**: Protects revision chain integrity
✅ **Pattern flexibility**: Easy to change pattern in future

The hybrid approach gives you the best of both worlds! 🎯
