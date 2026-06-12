---
name: fastapi-auth-login
description: Implement JWT login for a FastAPI app that already has router-level auth dependencies — avoid the trap where login endpoints inherit the router's auth check.
source: auto-skill
extracted_at: '2026-06-11T18:54:08.244Z'
---

# Adding JWT Login to a FastAPI App with Router-Level Auth

Use this when you need to add a username/password login flow (JWT tokens) to a FastAPI backend that already uses `require_api_key` as a **router-level** dependency.

## Trap: Router-level dependencies are inherited by ALL routes

If the router is defined as:

```python
router = APIRouter(dependencies=[Depends(require_api_key)])
```

then **every route on this router** requires auth — including a hypothetical login route. Route-level `dependencies=[Depends(public_endpoint)]` does NOT override router-level dependencies; they **stack** (both run). A login endpoint here will always return 401 because `require_api_key` runs first and rejects the unauthenticated request.

**Fix**: Register the login endpoint directly on the `FastAPI` app instance, NOT on the protected router:

```python
# In main.py, NOT in routes.py
@app.post("/api/auth/login", dependencies=[Depends(public_endpoint)])
async def login(request: LoginRequest):
    ...
```

This bypasses the router-level `require_api_key` entirely. Only `public_endpoint` (rate limiting only) runs.

## Implementation pattern

### 1. Add PyJWT dependency

```txt
PyJWT==2.10.1
```

### 2. Config: Add JWT and admin credential settings

```python
class Settings(BaseSettings):
    auth_enabled: bool = True
    auth_token: str = ""          # Static API key (still accepted alongside JWT)
    jwt_secret: str = ""          # Auto-derived from auth_token or admin_password if empty
    jwt_expiration_hours: int = Field(default=24, ge=1, le=168)
    admin_username: str = "admin"
    admin_password: str = ""      # Must be set when auth_enabled=True
```

**Validator ordering trap**: `@field_validator("auth_token")` runs before `admin_password` is validated, so `info.data.get("admin_password")` returns `None`. Use `@model_validator(mode="after")` instead for cross-field checks:

```python
@model_validator(mode="after")
def validate_auth_config(self) -> "Settings":
    if self.auth_enabled and not self.auth_token and not self.admin_password:
        warnings.warn("...")
    return self
```

### 3. Auth module: JWT creation, verification, and updated require_api_key

```python
def _get_jwt_secret(settings) -> str:
    """Derive JWT signing secret from available config (fallback chain)."""
    if settings.jwt_secret:
        return settings.jwt_secret
    if settings.auth_token:
        return settings.auth_token
    if settings.admin_password:
        return settings.admin_password
    raise HTTPException(status_code=500, detail="No secret for JWT signing")

def create_access_token(username: str) -> str:
    settings = get_settings()
    secret = _get_jwt_secret(settings)
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
    return jwt.encode({"sub": username, "exp": expire}, secret, algorithm="HS256")

def verify_access_token(token: str) -> dict:
    secret = _get_jwt_secret(get_settings())
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

Update `require_api_key` to try JWT first, then static API key:

```python
async def require_api_key(request, bearer_credentials=Security(http_bearer), api_key=Depends(api_key_header)):
    settings = get_settings()
    _check_rate_limit(_get_client_ip(request))

    if not settings.auth_enabled:
        return {"user": "anonymous"}

    # Try JWT (Bearer token)
    if bearer_credentials and bearer_credentials.scheme.lower() == "bearer":
        token = bearer_credentials.credentials
        # Check if it's the static auth_token first
        if settings.auth_token and secrets.compare_digest(token, settings.auth_token):
            return {"user": "api_client"}
        # Otherwise treat as JWT
        payload = verify_access_token(token)
        return {"user": payload.get("sub", "unknown")}

    # Try X-API-Key header (static only)
    if api_key and settings.auth_token and secrets.compare_digest(api_key, settings.auth_token):
        return {"user": "api_client"}

    raise HTTPException(status_code=401, detail="Unauthorized")
```

### 4. Login endpoint on the app (not the router)

**Critical: Add handler-level empty-input validation before any business logic.** Pydantic `min_length=1` returns 422 with a confusing array-style `detail` that frontends often don't parse correctly, and whitespace-only strings (`"   "`) bypass `min_length=1` entirely. Remove `min_length=1` from the `LoginRequest` model and validate in the handler for consistent 400 responses:

```python
class LoginRequest(BaseModel):
    username: str = Field(..., max_length=128)   # NO min_length — handler validates
    password: str = Field(..., max_length=128)   # NO min_length — handler validates
```

Handler with defense-in-depth validation:

```python
@app.post("/api/auth/login", dependencies=[Depends(public_endpoint)])
async def login(request: LoginRequest):
    # FAIL FAST: reject empty/whitespace inputs before any secrets comparison
    if not request.username.strip() or not request.password.strip():
        raise HTTPException(status_code=400, detail="Username and password are required")

    settings = get_settings()  # module-level cached settings
    if not settings.auth_enabled:
        return {"access_token": create_access_token("anonymous"), "token_type": "bearer"}
    if not settings.admin_password:
        raise HTTPException(status_code=401, detail="Login disabled")
    if not secrets.compare_digest(request.username, settings.admin_username) or \
       not secrets.compare_digest(request.password, settings.admin_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_access_token(settings.admin_username), "token_type": "bearer"}
```

**Why handler-level instead of Pydantic-only**: Empty passwords sent as `""` trigger Pydantic's 422 with `detail: [{loc, msg, type}]` (an array, not a string). Frontends that do `new Error(error.detail)` get `[object Object]` instead of a readable message. Whitespace-only passwords like `"   "` pass `min_length=1` and reach `compare_digest`, which can match an empty `admin_password` default — or if all secrets are empty, `_get_jwt_secret` raises HTTPException(500). Handler-level `.strip()` checks prevent all these paths to 500.

### 5. Frontend: Auth context, login page, API client with auth headers

- **Auth context** (`lib/auth.tsx`): `AuthProvider` + `useAuth()` hook, stores JWT in localStorage
- **Login page** (`app/login/page.tsx`): Form that calls `login()` from auth context
- **AuthGuard** (`components/common/AuthGuard.tsx`): Redirects to `/login` if not authenticated
- **API client** (`lib/api.ts`): Reads token from localStorage, adds `Authorization: Bearer <token>` to all requests, clears token on 401 response
- **Layout** (`app/layout.tsx`): Wraps children with `<AuthProvider>` + `<AuthGuard>`
- **Sidebar**: Add "Sign out" button that calls `logout()` and redirects to `/login`

**Defense-in-depth on the frontend too:**

Login page — client-side validation before network request:
```tsx
async function handleSubmit(e: React.FormEvent) {
  e.preventDefault();
  setError(null);
  if (!username.trim()) { setError('Username is required'); return; }
  if (!password.trim()) { setError('Password is required'); return; }
  setLoading(true);
  try {
    await login(username.trim(), password.trim());
    router.push('/');
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Login failed');
  } finally { setLoading(false); }
}
```

Auth context — parse 422 Pydantic error arrays properly (FastAPI returns `detail: [{msg, loc, type}]`, not a string):
```tsx
if (!res.ok) {
  const error = await res.json().catch(() => ({ detail: res.statusText }));
  const detail = error.detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((e: { msg?: string; message?: string }) => e.msg || e.message || '')
      .filter(Boolean);
    throw new Error(messages.join('; ') || `Login failed: ${res.status}`);
  }
  throw new Error(detail || `Login failed: ${res.status}`);
}
```

### 6. Deployment: Pass auth env vars

Add `ADMIN_PASSWORD`, `ADMIN_USERNAME`, `JWT_SECRET`, `JWT_EXPIRATION_HOURS` to:
- `.env.example` and `.env.render`
- `docker-compose.yml` and `docker-compose.backend.yml`
- Render dashboard environment variables (manual step)

## Verification

1. Import check: `python -c "from main import app"`
2. Start server with `ADMIN_PASSWORD=testpass123 ADMIN_USERNAME=admin AUTH_ENABLED=true`
3. Test login: `POST /api/auth/login` with `{"username": "admin", "password": "testpass123"}` → 200 + JWT
4. Test JWT auth: `GET /api/pipelines` with `Authorization: Bearer <jwt>` → 200
5. Test wrong password → 401
6. Test no auth → 401
7. **Test empty password** `{"username": "admin", "password": ""}` → 400 (NOT 500 or 422)
8. **Test whitespace-only password** `{"username": "admin", "password": "   "}` → 400 (NOT 500)
9. Frontend: `npm run build` should succeed with `/login` page present

### Backend test fixture pattern

When testing login endpoints with `TestClient`, the lifespan context manager tries to init DB/Redis. Mock it out:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def mock_lifespan(app):
    yield

main_mod.app.router.lifespan_context = mock_lifespan
```

Also patch `get_settings` in all modules that import it (e.g., `core.config.get_settings`, `core.auth.get_settings`, `main.get_settings`) to inject test settings with known `admin_password` and `jwt_secret`, otherwise `create_access_token` → `_get_jwt_secret` may raise HTTPException(500).