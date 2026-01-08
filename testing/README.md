# Testing App (Pramana CRUD + Verification)

This is a self-contained full-stack app under `./testing`.

## Structure
```
./testing
  backend
  frontend
  README.md
```

## Backend (Express + Prisma + SQLite)

### Setup
```
cd testing/backend
npm install
npx prisma generate
npx prisma migrate dev --name init
```

### Run
```
npm run dev:auto
```

Backend runs on `http://localhost:5000` by default, but if the port is taken it will automatically increment (5001, 5002, ...). The chosen port is printed at startup and a `testing/frontend/.env.local` file is written with `VITE_API_BASE_URL` pointing to the selected port.

### Environment
- `PRAMANA_BASE_URL` (default: `http://74.225.160.195:8080`)
- `DATABASE_URL` (default: `file:./dev.db`)
- `PRISMA_CLI_QUERY_ENGINE_TYPE` (set to `binary` for macOS stability)
- `PRISMA_SCHEMA_ENGINE_BINARY` (points to the local schema engine binary)

Override by editing `testing/backend/.env`.

### Example curl
Create (text-only):
```
curl -sS -X POST http://localhost:5000/api/posts \
  -F "title=Eiffel Tower" \
  -F "description=The Eiffel Tower is in Paris"
```

Create (with image):
```
curl -sS -X POST http://localhost:5000/api/posts \
  -F "title=Image claim" \
  -F "description=This shows a landmark" \
  -F "image=@/path/to/image.jpg"
```

Update:
```
curl -sS -X PUT http://localhost:5000/api/posts/<ID> \
  -F "title=Updated title" \
  -F "description=Updated description"
```

Delete:
```
curl -sS -X DELETE http://localhost:5000/api/posts/<ID>
```

Re-verify:
```
curl -sS -X POST http://localhost:5000/api/posts/<ID>/verify
```

List:
```
curl -sS http://localhost:5000/api/posts
```

## Frontend (Vite + React + Tailwind)

### Setup
```
cd testing/frontend
npm install
```

### Run
```
npm run dev
```

Frontend runs on `http://localhost:5173`.

### Environment
- `VITE_API_BASE_URL` (default: `http://localhost:5000`, overridden by `testing/frontend/.env.local` when the backend starts)

Override by editing `testing/frontend/.env`.

## Notes
- Image uploads are stored in `testing/backend/uploads`.
- If Pramana is unreachable, the backend stores a fallback verification result with `verdict=unknown` and an error explanation.

## Prisma Troubleshooting (macOS)
If `npx prisma migrate dev --name init` fails with `Schema engine error:`, use the schema engine binary explicitly (already set in `testing/backend/.env`):
```
PRISMA_SCHEMA_ENGINE_BINARY=./node_modules/@prisma/engines/schema-engine-darwin-arm64 \
  npx prisma migrate dev --name init
```
If migrations still fail, fallback to:
```
npx prisma db push
```
