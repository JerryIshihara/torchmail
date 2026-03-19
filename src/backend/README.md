# TorchMail Backend API

FastAPI wrapper for the existing search engine in `src/search_engine`.

## Run locally

```bash
python -m pip install -r src/backend/requirements.txt
uvicorn src.backend.main:app --reload
```

## Endpoints

- `GET /api/health`
- `GET /api/search?q=machine+learning`
- `GET /api/search/{id}`
