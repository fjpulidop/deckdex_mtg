# DeckDex MTG

DeckDex MTG can use **PostgreSQL** as the primary store for your card collection (recommended) or **Google Sheets**. When using Postgres, you can import from a CSV or JSON file via the web Settings page and use full CRUD (create, edit, delete cards) in the dashboard.

![Logo](images/Deckdex.png)

A comprehensive tool for managing your Magic: The Gathering card collection with both CLI and Web interfaces. Fetches card data from Scryfall, tracks prices, and syncs everything to Google Sheets.

## Features

- 📊 **Collection Management**: Track cards, prices, and metadata
- 🌐 **Web Dashboard**: Modern UI with real-time updates
- ⚡ **CLI Tools**: Powerful command-line interface for automation
- 🔄 **Price Tracking**: Automated price updates with change detection
- 🤖 **AI Integration**: Optional OpenAI enrichment for strategies and tiers
- 📈 **Real-time Progress**: WebSocket-powered live updates

## Quick Start

### Web Interface (Recommended)

```bash
# Start backend (Terminal 1)
cd backend && uvicorn api.main:app --reload

# Start frontend (Terminal 2)
cd frontend && npm run dev

# Open http://localhost:5173
```

**First time?** Install dependencies:
```bash
pip install -r requirements.txt -r backend/requirements-api.txt
cd frontend && npm install
```

### CLI

```bash
# Update prices
python main.py --update_prices

# Process new cards with OpenAI enrichment
python main.py --use_openai

# Use production profile for performance
python main.py --profile production --update_prices
```

## Requirements

- Python 3.8+
- Node.js 18+ (for web interface)
- Google Sheets API credentials ([setup guide](https://developers.google.com/sheets/api/quickstart/python))
- OpenAI API key (optional)

**Google Sheet columns:**
```
Name, English name, Type, Description, Keywords, Mana Cost, Cmc, Color, Identity, 
Colors, Strength, Resistance, Rarity, Price, Release, Date, Set ID, Set Name, 
Number in Set, Edhrec, Rank, Game Strategy, Tier
```

## Setup

1. Clone and create virtual environment:
```bash
git clone <repo-url>
cd deckdex_mtg
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment (create `.env`):
```env
GOOGLE_API_CREDENTIALS=/path/to/credentials.json
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

**Optional – PostgreSQL (recommended):** Use Postgres as the collection store and enable CRUD and file import from Settings:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/deckdex
```
Run migrations with `./scripts/setup_db.sh` (Docker) or `python scripts/setup_db.py`. See `migrations/README.md`.

4. If using only Google Sheets: share your Google Sheet with the service account email from your credentials.

## Web Interface

### Architecture

```
Browser (localhost:5173)
    ↓
React Frontend (Vite + Tailwind + TanStack Query)
    ↓ REST + WebSocket
FastAPI Backend (port 8000)
    ↓
Core Logic (CardFetcher, Processor, SpreadsheetClient)
    ↓
Google Sheets (source of truth)
```

### Features

- **Dashboard**: Collection stats, total value, card count
- **Card Browser**: Search, filter, sort with pagination
- **Real-time Progress**: WebSocket updates for long operations
- **Job Management**: Background job tracking with cancel support
- **Elapsed Timers**: Live duration display for all operations

### API Endpoints

- `GET /api/health` - Service status
- `GET /api/cards` - List cards with pagination/search
- `GET /api/stats` - Collection statistics
- `POST /api/process` - Trigger card processing
- `POST /api/prices/update` - Update prices
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{id}` - Job status
- `POST /api/jobs/{id}/cancel` - Cancel running job
- `WebSocket /ws/progress/{id}` - Real-time updates

### Troubleshooting

**Blank page:** Restart frontend after `npm install`

**Backend errors:** Ensure both dependency files are installed:
```bash
pip install -r requirements.txt -r backend/requirements-api.txt
```

**Connection refused:** Start backend first on port 8000

**Job cancellation:** Click Stop button or use REST API:
```bash
# List jobs
curl http://localhost:8000/api/jobs/

# Cancel specific job
curl -X POST http://localhost:8000/api/jobs/<job_id>/cancel/
```

## CLI Reference

### Profiles

Choose pre-configured settings optimized for different scenarios:

```bash
# Balanced (default)
python main.py

# Development (conservative, easier debugging)
python main.py --profile development

# Production (optimized for thousands of cards)
python main.py --profile production

# Show configuration
python main.py --show-config
```

### Common Commands

```bash
# Update prices with progress tracking
python main.py --update_prices

# Process cards with OpenAI enrichment
python main.py --use_openai

# Test with limited cards
python main.py --limit 10 --dry-run --verbose

# Resume after interruption
python main.py --update_prices --resume-from 450

# Custom performance settings
python main.py --batch-size 50 --workers 8 --api-delay 0.05
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--profile` | default | Configuration profile (default/development/production) |
| `--batch-size` | 20 | Cards per batch |
| `--workers` | 4 | Parallel workers (1-10) |
| `--api-delay` | 0.1s | Delay between API calls |
| `--limit` | - | Process only N cards |
| `--resume-from` | - | Resume from row N |
| `--dry-run` | false | Simulate without writing |
| `--verbose` | false | DEBUG-level logging |

Full options: `python main.py --help`

### Environment Overrides

```bash
# Override via environment variables
export DECKDEX_PROCESSING_BATCH_SIZE=30
export DECKDEX_PROCESSING_MAX_WORKERS=6
export DECKDEX_OPENAI_ENABLED=true

python main.py
```

Priority: YAML < Environment Variables < CLI Flags

## Performance Features

1. **Parallel Processing**: ThreadPoolExecutor for concurrent API calls
2. **Smart Caching**: LRU cache for repeated queries
3. **Batch Operations**: Reduced Google Sheets API calls
4. **Incremental Writes**: Price updates written every 60 cards
5. **Change Detection**: Only updates modified prices
6. **Retry Logic**: Exponential backoff for failures
7. **HTTP Sessions**: Persistent connections
8. **Real-time Cancellation**: Stop jobs via stream injection

**Results:**
- 1000 cards in ~130 seconds (with incremental writes)
- Max 60 cards data loss on interruption (vs. all cards previously)
- Resume capability with `--resume-from`

## Configuration

Managed via `config.yaml` with three profiles:

```yaml
profiles:
  default:
    processing:
      batch_size: 20
      max_workers: 4
      api_delay: 0.1
      write_buffer_batches: 3
    # ... more settings

  development:
    # Conservative settings for debugging
    
  production:
    # Aggressive settings for large collections
```

**Security:** Store secrets in `.env`, not `config.yaml`:
```env
GOOGLE_API_CREDENTIALS=/path/to/credentials.json
OPENAI_API_KEY=sk-...
```

## Project Structure

```
deckdex_mtg/
├── backend/              # FastAPI REST + WebSocket API
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/       # API endpoints
│   │   ├── services/     # ProcessorService wrapper
│   │   └── websockets/   # Real-time progress
│   └── requirements-api.txt
├── frontend/             # React + Vite + Tailwind UI
│   ├── src/
│   │   ├── components/   # Dashboard, modals, tables
│   │   ├── pages/        # Main views
│   │   └── api/          # API client
│   └── package.json
├── deckdex/              # Core logic (unchanged)
│   ├── card_fetcher.py
│   ├── magic_card_processor.py
│   └── spreadsheet_client.py
├── main.py               # CLI entry point
├── config.yaml           # Configuration profiles
├── docker-compose.yml    # Optional containerization
└── README.md             # This file
```

## Docker

Levantar todo el proyecto (Postgres, backend y frontend):

```bash
# 1. Crear la base de datos y aplicar migraciones (solo la primera vez o tras borrar el volumen)
./scripts/setup_db.sh

# 2. Levantar los tres servicios
docker compose up --build

# Acceso
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

O en segundo plano: `docker compose up -d --build`. Para parar: `docker compose down`.

Opcional: crea un `.env` en la raíz con variables que necesite el backend (p. ej. `OPENAI_API_KEY`, `GOOGLE_API_CREDENTIALS` para OAuth). El compose ya define `DATABASE_URL` para el backend.

## Important Notes

⚠️ **Concurrency:** When using **Google Sheets** as the only source, do not run CLI and web simultaneously (writes conflict). When using **PostgreSQL** (`DATABASE_URL` set), CLI and web may run at the same time.

⚠️ **MVP Limitations:**
- No authentication (localhost only)
- Job state lost on backend restart
- No historical price tracking (planned)
- Desktop-first UI

✅ **CLI Compatibility:** All existing CLI commands work unchanged

## Testing

```bash
# Unit tests
python -m unittest discover -s tests

# Backend health
curl http://localhost:8000/api/health

# API documentation
open http://localhost:8000/docs

# Frontend
open http://localhost:5173
```

## Troubleshooting Common Issues

### Module Not Found Errors
```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r backend/requirements-api.txt
cd frontend && npm install
```

### Google Sheets Quota Exceeded
- Wait 60 seconds
- Backend caches for 30s to reduce calls
- Use `--api-delay` to slow requests

### WebSocket Connection Lost
- Progress continues in background
- Reopen modal from ActiveJobs panel
- Progress state preserved via REST + WebSocket

### Job Won't Cancel
```bash
# Find job ID
curl http://localhost:8000/api/jobs/

# Cancel via API
curl -X POST http://localhost:8000/api/jobs/<job_id>/cancel/

# Or restart backend
lsof -i :8000  # Find PID
kill <PID>
```

## Contributing

Contributions welcome! Please open an issue first to discuss changes.

## License

[MIT](https://choosealicense.com/licenses/mit/)

---

**Documentation:**
- [Backend API Reference](backend/README.md)
- [Frontend Components](frontend/README.md)
- [Design Document](openspec/changes/web-mvp/design.md)
- [Task List](openspec/changes/web-mvp/tasks.md)
