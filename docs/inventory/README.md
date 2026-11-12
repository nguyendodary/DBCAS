# Generated interface inventories

Both files in this directory are **generated**, not authored. Do not hand-edit them; edit the
source they read, then regenerate.

| File | Generated from | Content |
|---|---|---|
| `api-routes.json` | `backend/app/main.py` + `backend/app/routers/*.py` | every HTTP method/path FastAPI registers, its router file, handler name, source line, response model and the role guard (`CurrentAccount` / `LearnerOnly` / `AdminOnly` / `RoleManagerOnly`) |
| `frontend-routes.json` | `frontend/src/App.jsx` | every browser route, the component it renders and its access gate (public / authenticated / Learner / Administrator) |

```
npm run inventory:write    # regenerate both files
npm run inventory:check    # exit 1 when a committed inventory no longer matches its sources
```

`scripts/generate_route_inventory.py` parses the source statically with Python's `ast` module and a
line-addressed scan of the JSX `<Route>` elements. It imports no application code, reads no settings,
opens no database and makes no network call, so it runs identically offline.

## What these files deliberately do not claim

- They are **not** synchronized with code automatically. Drift surfaces only when
  `npm run inventory:check` runs — in CI, in a pre-commit step or by hand. Nothing rewrites a
  document when a route changes.
- Each file carries the SHA-256 of every source it read, so a changed router cannot keep an old
  inventory silently: the digests and the rendered JSON must both match.
- Route *semantics* stay authored. Roles beyond the guard, status codes, idempotency, error payloads
  and domain rules live in [../api-conventions.md](../api-conventions.md); use-case links live in
  [../diagrams/use-cases.svg](../diagrams/use-cases.svg).
- The API list reflects decorator order and prefix composition (`include_router` mount prefix +
  `APIRouter(prefix=...)`). It cannot show routes registered dynamically at runtime; DBCAS registers
  none, and a future `add_api_route` call would need the generator extended rather than this file
  patched.
- The page list covers `App.jsx` only. The built-in Help guide is a modal rendered through
  `HelpProvider` and has no URL, so it correctly appears in neither inventory.
