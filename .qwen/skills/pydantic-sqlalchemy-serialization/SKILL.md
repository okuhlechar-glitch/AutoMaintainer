---
name: pydantic-sqlalchemy-serialization
description: Fix TypeError when persisting Pydantic models with Enum/datetime fields through SQLAlchemy — model_dump() returns non-JSON-serializable Python objects that crash JSON columns.
source: auto-skill
extracted_at: '2026-06-11T20:01:07.219Z'
---

# Fixing Pydantic → SQLAlchemy Serialization Crashes

Use this when you get a `TypeError: Object of type <Enum|datetime> is not JSON serializable` error when SQLAlchemy tries to persist a Pydantic model to the database.

## Root Cause

Pydantic's default `model_dump()` (without `mode='json'`) returns **Python objects**, not JSON-safe values:

- `Enum` fields → Python enum instances (e.g., `IssueSeverity.LOW`), not plain strings
- `datetime` fields → Python `datetime` objects, not ISO strings
- Nested Pydantic models → dicts that **also** contain enum instances and datetime objects

When these values are assigned to SQLAlchemy **JSON columns**, SQLAlchemy's internal JSON serializer (`json.dumps`) can't handle them, causing the crash.

**Important**: SQLAlchemy **DateTime** columns handle Python `datetime` objects fine — the crash only happens when `datetime` objects appear **inside JSON column data** (nested in dicts/lists).

## The Wrong Fixes

1. **Using `model_dump(mode='json')` everywhere**: This converts ALL datetime fields to ISO strings, but SQLAlchemy DateTime columns need Python datetime objects, not strings. You'd get type mismatches.

2. **Adding a custom `JSONEncoder` to SQLAlchemy engine**: Works but is fragile — it silently serializes anything, hiding bugs. Also doesn't fix String columns receiving enum objects.

3. **String-based enums "should work"**: `class IssueSeverity(str, Enum)` makes `isinstance(val, str)` true, but SQLAlchemy's JSON serializer still crashes because it calls `json.dumps()` which doesn't recognize the enum's `__repr__`.

## The Right Fix: `db_dump()` with recursive serializer

Add a `db_dump()` method to your Pydantic model and a recursive `_serialize_for_db()` helper:

```python
def _serialize_for_db(obj: Any) -> Any:
    """Recursively convert Python objects to DB-compatible values."""
    if isinstance(obj, Enum):
        return obj.value           # Enum → string
    if isinstance(obj, datetime):
        return obj.isoformat()     # datetime → ISO string (for JSON columns)
    if isinstance(obj, dict):
        return {k: _serialize_for_db(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_for_db(item) for item in obj]
    if hasattr(obj, "model_dump") and isinstance(obj, BaseModel):
        return _serialize_for_db(obj.model_dump())
    return obj                     # str, int, float, None, bool pass through


class PipelineRun(BaseModel):
    # ... fields with Enums, datetime, nested Pydantic models ...
    
    def db_dump(self) -> dict[str, Any]:
        data = self.model_dump()
        serialized = _serialize_for_db(data)
        # Restore Python datetime for DateTime columns (not JSON columns)
        serialized["created_at"] = self.created_at
        serialized["updated_at"] = self.updated_at
        return serialized
```

Then use `db_dump()` instead of `model_dump()` in all DB persistence code:

```python
# In _persist_pipeline (update path):
data = pipeline.db_dump()
for key, value in data.items():
    setattr(existing, key, value)

# In pipeline_to_orm (insert path):
data = pipeline.db_dump()
return PipelineORM(**data)
```

## Verification Checklist

1. **Unit test**: Create a Pydantic model with enums and datetime, call `db_dump()`, verify:
   - Top-level enum fields → plain strings
   - Nested enum fields in dicts → plain strings  
   - Datetime inside JSON column data → ISO strings
   - Top-level datetime fields → Python datetime objects
   - All JSON column data is `json.dumps()`-compatible

2. **Integration test**: Create ORM object from `db_dump()` data and verify SQLAlchemy can persist it without TypeError.

3. **Roundtrip test**: `pipeline → db_dump() → PipelineORM(**data) → orm_to_pipeline() → PipelineRun` should preserve all data correctly.

## Common Pitfalls

- **Pydantic validator ordering**: `@field_validator("auth_token")` runs before fields defined AFTER `auth_token` are validated. Use `@model_validator(mode="after")` for cross-field checks instead.
- **Router-level dependencies**: A login endpoint on a router with `dependencies=[Depends(require_api_key)]` will ALWAYS require auth — route-level `public_endpoint` doesn't override, it stacks. Register login on the app directly.