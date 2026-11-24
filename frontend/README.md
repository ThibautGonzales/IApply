# IApply frontend

Angular application.

## Run locally (without Docker)

Start the backend first (see `../backend/README.md` or `docker compose up db backend`), then:

```bash
cd frontend
npm install
npm start          # http://localhost:4200
```

Calls to `/api/...` are forwarded to the backend on `http://localhost:8000` by `proxy.conf.json`.

## Run the tests

```bash
npm test
```
