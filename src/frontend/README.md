# TorchMail Frontend

Single-page Vite + React + Tailwind UI for Search MVP issue `#28`.

## Run locally

```bash
cd src/frontend
npm install
npm run dev
```

The app runs at `http://127.0.0.1:5173`.
By default, Vite proxies `/api/*` requests to `http://127.0.0.1:8000`.

## Backend API

Set `VITE_API_BASE_URL` to point to the FastAPI server.

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```
