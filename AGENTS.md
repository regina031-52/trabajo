# AGENTS.md

## Cursor Cloud specific instructions

### Repository layout

- **`main`** only contains a Java `.gitignore` template. Application code lives on **`conflict_180426_1544`** (FastAPI + React Refugios A*). Check out that branch before install/run: `git checkout conflict_180426_1544`.
- A separate product (Tabú inventory optimizer, tkinter) is on `origin/cursor/busqueda-tabu-inventario-19a9`; it is unrelated to the web stack.

### Services (Refugios A* web stack)

| Service | Port | Notes |
|---------|------|--------|
| MongoDB | 27017 | Required at backend import (`MONGO_URL`, `DB_NAME`); data is JSON on disk, DB can be empty |
| FastAPI (`uvicorn server:app`) | 8000 | Run from `backend/` with venv active |
| React (CRACO) | 3000 | Run from `frontend/`; needs `REACT_APP_BACKEND_URL` |

### MongoDB (no systemd in Cloud VM)

`mongod` does not auto-start. After VM boot, start once per session:

```bash
mkdir -p /data/db /var/log/mongodb
mongod --dbpath /data/db --logpath /var/log/mongodb/mongod.log --fork --bind_ip 127.0.0.1
```

### Environment files (not committed; create locally)

**`backend/.env`:**

```
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=refugios
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**`frontend/.env`:**

```
REACT_APP_BACKEND_URL=http://localhost:8000
```

### Backend Python deps

- Use a venv in `backend/.venv`.
- `emergentintegrations==0.1.0` in `requirements.txt` is not on PyPI and is unused by `server.py`. Install with: `grep -v '^emergentintegrations' requirements.txt | pip install -r /dev/stdin` (or maintain `requirements.local.txt`).

### Commands (standard)

See `frontend/package.json` and `backend/requirements.txt`. Typical dev session:

```bash
# terminal 1 — backend
cd backend && source .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8000

# terminal 2 — frontend
cd frontend && BROWSER=none CI=true yarn start
```

### Tests

- Backend integration tests hit a **running** API: `REACT_APP_BACKEND_URL=http://localhost:8000 pytest backend/tests/`.
- `test_api.py` expects an older graph (1792 nodes, 18 schools). Current data has ~8558 nodes and 19 schools; expect some failures in that file. `test_iteration4_ciudad_renacimiento.py` is closer but may still drift if graph JSON changes.

### Lint / build

- Frontend production build: `cd frontend && yarn build`.
- ESLint is wired through CRACO/webpack during `yarn start` / `yarn build`, not as a standalone root script.

### Hello-world (core behavior)

Search a street (e.g. "Costa Azul"), pick a result, click **Encontrar refugio más cercano**, or POST `/api/calcular-ruta` with a valid `nodo_origen` from `/api/buscar-nodos?q=...`.
