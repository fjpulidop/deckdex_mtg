# DeckDex MTG - Backend API

FastAPI backend for DeckDex MTG web interface, providing REST API and WebSocket endpoints for card collection management.

## Features

- **REST API**: Access collection data, statistics, and trigger processes
- **WebSocket**: Real-time progress updates for long-running operations
- **Caching**: 30-second TTL cache for collection and stats to reduce API calls
- **Integration**: Reuses existing `deckdex` core logic (MagicCardProcessor, CardFetcher, SpreadsheetClient)

## Setup

### Prerequisites

- Python 3.8+
- Existing DeckDex MTG installation (core dependencies from parent `requirements.txt`)
- Google Sheets API credentials configured
- Optional: OpenAI API key for card enrichment

### Installation

1. Install core dependencies first (from project root):
```bash
pip install -r requirements.txt
```

2. Install backend-specific dependencies:
```bash
cd backend
pip install -r requirements-api.txt
```

3. Configure environment variables (copy from root `.env.example`):
```bash
# Required
export GOOGLE_API_CREDENTIALS=/path/to/credentials.json

# Optional
export OPENAI_API_KEY=sk-your-key
export DECKDEX_PROFILE=default  # or development, production
```

## Running the Server

### Development Mode (Local)

```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

The API will be available at:
- API Base: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Using Docker Compose (Recommended)

From the project root:
```bash
# Start both backend and frontend
docker-compose up

# Stop services
docker-compose down
```

This starts:
- Backend on http://localhost:8000
- Frontend on http://localhost:5173

### Production Mode

```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check

```bash
# Check if API is running
curl http://localhost:8000/api/health
```

Response:
```json
{
  "service": "DeckDex MTG API",
  "version": "0.1.0",
  "status": "healthy"
}
```

### Cards

```bash
# List all cards (with pagination)
curl "http://localhost:8000/api/cards?limit=50&offset=0"

# Search cards by name
curl "http://localhost:8000/api/cards?search=lotus"

# Get single card details
curl "http://localhost:8000/api/cards/Black%20Lotus"
```

### Statistics

```bash
# Get collection statistics
curl http://localhost:8000/api/stats
```

Response:
```json
{
  "total_cards": 1234,
  "total_value": 15420.50,
  "average_price": 12.50,
  "last_updated": "2024-02-07T14:30:00"
}
```

### Process Execution

```bash
# Trigger card processing
curl -X POST http://localhost:8000/api/process

# Trigger price update
curl -X POST http://localhost:8000/api/prices/update

# Check job status
curl http://localhost:8000/api/jobs/{job_id}
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Process job created and queued"
}
```

### WebSocket Progress

Connect to WebSocket for real-time progress updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/progress/{job_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
  // { type: 'progress', current: 50, total: 100, percentage: 50.0, timestamp: '...' }
  // { type: 'error', card_name: 'Foo', error_type: 'not_found', message: '...', timestamp: '...' }
  // { type: 'complete', status: 'success', summary: {...}, timestamp: '...' }
};
```

## Testing Endpoints

### Using curl

```bash
# Health check
curl http://localhost:8000/api/health

# List cards
curl http://localhost:8000/api/cards

# Get stats
curl http://localhost:8000/api/stats

# Start process
curl -X POST http://localhost:8000/api/process

# Check job status (replace with actual job_id)
curl http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000
```

### Using Python

```python
import requests

# Get collection stats
response = requests.get('http://localhost:8000/api/stats')
print(response.json())

# Trigger process
response = requests.post('http://localhost:8000/api/process')
job_id = response.json()['job_id']
print(f"Job started: {job_id}")

# Check status
response = requests.get(f'http://localhost:8000/api/jobs/{job_id}')
print(response.json())
```

### Testing WebSocket (with wscat)

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket (replace job_id)
wscat -c ws://localhost:8000/ws/progress/123e4567-e89b-12d3-a456-426614174000

# You'll receive real-time progress events
```

## Architecture

```
backend/
├── api/
│   ├── main.py                 # FastAPI app entry point
│   ├── dependencies.py         # Shared utilities (caching, clients)
│   ├── routes/
│   │   ├── cards.py           # Card collection endpoints
│   │   ├── stats.py           # Statistics endpoints
│   │   └── process.py         # Process execution endpoints
│   ├── services/
│   │   └── processor_service.py  # Wrapper around MagicCardProcessor
│   └── websockets/
│       └── progress.py        # WebSocket progress handler
└── requirements-api.txt        # Backend dependencies
```

## Configuration

The backend uses the same configuration system as the CLI:
- `config.yaml` profiles (default, development, production)
- Environment variables with `DECKDEX_` prefix
- Defaults to `default` profile unless `DECKDEX_PROFILE` is set

## Logging

Logs are written to:
- Console (stderr) with colored output
- `logs/api.log` (rotation: 500MB, retention: 10 days)

Log levels:
- `INFO`: API requests, job lifecycle, cache operations
- `ERROR`: Exceptions, failed operations

## Caching

The backend implements two caches:
1. **Collection cache**: 30-second TTL for card data from Google Sheets
2. **Stats cache**: 30-second TTL for calculated statistics

Caches are automatically cleared when processes complete successfully.

## Concurrency

⚠️ **Important**: Only one process (card processing or price update) can run at a time. If you attempt to start a second process, you'll receive a `409 Conflict` response.

When using **Google Sheets** as the only data source, the CLI and web backend should not run processes simultaneously. When using **PostgreSQL** (`DATABASE_URL`), both may run at the same time.

## Error Handling

- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `409 Conflict`: Process already running
- `500 Internal Server Error`: Unexpected server error
- `503 Service Unavailable`: Google Sheets API quota exceeded (retry after 60s)

## Troubleshooting

### "Google credentials not found"
- Ensure `GOOGLE_API_CREDENTIALS` environment variable points to valid credentials JSON
- Check that the credentials file exists and is readable

### "API quota exceeded"
- Google Sheets API has rate limits (600 requests/minute)
- The backend implements caching to reduce API calls
- Wait 60 seconds and retry

### "Process already running"
- Only one process can run at a time
- Check active jobs with GET `/api/jobs/{job_id}`
- Wait for current job to complete

### WebSocket connection rejected
- Job ID must exist (check with POST to `/api/process` first)
- Ensure WebSocket client uses correct URL: `ws://localhost:8000/ws/progress/{job_id}`

## Development

### Project Structure
```
backend/
├── api/
│   ├── __init__.py
│   ├── main.py               # FastAPI app + middleware
│   ├── dependencies.py       # Shared deps (clients, caching)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── cards.py         # GET /api/cards
│   │   ├── stats.py         # GET /api/stats
│   │   └── process.py       # POST /api/process, /api/prices/update
│   ├── services/
│   │   ├── __init__.py
│   │   └── processor_service.py  # Wrapper for async execution
│   └── websockets/
│       ├── __init__.py
│       └── progress.py      # WebSocket handler
└── requirements-api.txt
```

### Adding New Endpoints

1. Create new router in `api/routes/`:
```python
from fastapi import APIRouter
router = APIRouter(prefix="/api/feature", tags=["feature"])

@router.get("/")
async def get_feature():
    return {"status": "ok"}
```

2. Include router in `api/main.py`:
```python
from .routes import cards, stats, process, feature
app.include_router(feature.router)
```

## Related Documentation

- [Main README](../README.md) - CLI documentation
- [Frontend README](../frontend/README.md) - React frontend setup
- [OpenSpec Design](../openspec/changes/web-mvp/design.md) - Technical design decisions
