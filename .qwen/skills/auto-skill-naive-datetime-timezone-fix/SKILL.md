---
name: naive-datetime-timezone-fix
description: Diagnose and fix frontend displaying inaccurate timestamps caused by backend using naive datetime.utcnow instead of timezone-aware datetime.now(UTC).
source: auto-skill
extracted_at: '2026-06-17T11:28:54.881Z'
---

# Fix Inaccurate Timestamps from Naive Datetimes

Use this when a frontend displays timestamps that appear off by several hours — the times don't match when the user actually performed an action (e.g., "pipeline started 2 hours ago" shows a different time than expected).

## Root Cause

`datetime.utcnow` is deprecated and returns **naive** (timezone-unaware) datetime objects. When serialized via `.isoformat()`, these produce strings without a timezone suffix: `"2026-06-17T10:30:00"` (no `+00:00`). JavaScript's `new Date()` interprets such strings as **local time**, not UTC. A user in UTC+2 would see 10:30 AM local instead of the correct 12:30 PM local.

Conversely, `datetime.now(timezone.utc)` returns timezone-aware objects. `.isoformat()` on these produces `"2026-06-17T10:30:00+00:00"` — JavaScript correctly parses this as UTC and converts to local time.

## Diagnosis

1. Check if timestamps appear shifted by the user's UTC offset (e.g., +2 hours off for UTC+2 users)
2. Search backend for `datetime.utcnow` usage:
   ```
   grep -rn "datetime.utcnow" backend/
   ```
3. Check API responses — if `.isoformat()` output lacks `+00:00` suffix, the datetime is naive

## Fix Pattern

### Pydantic models — replace `default_factory`

```python
# BEFORE (naive — no timezone info)
from datetime import datetime
created_at: datetime = Field(default_factory=datetime.utcnow)

# AFTER (timezone-aware — includes +00:00 in isoformat)
from datetime import datetime, timezone
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Important**: `default_factory` requires a callable. `datetime.now(timezone.utc)` is a method call (returns a datetime, not a callable), so wrap it in `lambda:`. `datetime.utcnow` was a callable reference (no args needed), which is why it worked directly.

### SQLAlchemy ORM — replace `default` and `onupdate`

```python
# BEFORE
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

# AFTER
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

Same lambda wrapper requirement for `default` and `onupdate`.

### Orchestrator/manual updates — already correct pattern

If the code uses a `_now()` helper, it may already be correct:
```python
def _now() -> datetime:
    return datetime.now(timezone.utc)
```

Just verify all timestamp assignments use this helper or `datetime.now(timezone.utc)` consistently.

## Verification

After the fix, confirm API responses include timezone suffixes:
```python
# Test that isoformat() now includes +00:00
from datetime import datetime, timezone
dt = datetime.now(timezone.utc)
assert "+00:00" in dt.isoformat()  # Should pass
```

Existing database records with naive datetimes will remain naive. For a full fix, you'd need a migration to add timezone info to historical rows. For most apps, only new records will be correct — old records will still display slightly off until migrated.

## Why this matters

- Users in non-UTC timezones see wrong times for every timestamp
- `datetime.utcnow` is deprecated in Python 3.12+ — it's a known antipattern
- The fix is mechanical (find-and-replace) but the lambda wrapper detail is easy to miss
