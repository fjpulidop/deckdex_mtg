# DeckDex MTG - Frontend

React + TypeScript frontend for DeckDex MTG, providing a modern web interface for managing your Magic: The Gathering card collection.

## Features

- **Dashboard**: View collection statistics and trends
- **Card Browser**: Search, filter, and sort your card collection
- **Real-time Updates**: WebSocket progress tracking for long-running processes
- **Modern UI**: Built with Tailwind CSS for a clean, responsive design

## Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

The frontend will be available at http://localhost:5173

The Vite dev server automatically proxies API requests to the backend:
- `/api/*` → `http://localhost:8000/api/*`
- `/ws/*` → `ws://localhost:8000/ws/*`

## Building for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API client functions
│   ├── components/
│   │   ├── StatsCards.tsx     # Collection statistics display
│   │   ├── PriceChart.tsx     # Price history chart (placeholder)
│   │   ├── CardTable.tsx      # Card collection table
│   │   ├── Filters.tsx        # Search and filter controls
│   │   ├── ActionButtons.tsx  # Process trigger buttons
│   │   └── ProcessModal.tsx   # Real-time progress modal
│   ├── hooks/
│   │   └── useApi.ts          # React Query hooks
│   ├── pages/
│   │   └── Dashboard.tsx      # Main dashboard page
│   ├── App.tsx                # App entry component
│   ├── main.tsx               # React entry point
│   └── index.css              # Tailwind CSS imports
├── package.json
├── vite.config.ts             # Vite configuration with proxy
├── tailwind.config.js         # Tailwind configuration
└── tsconfig.json              # TypeScript configuration
```

## Technologies

- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **TanStack Query**: Data fetching and caching
- **Tailwind CSS**: Utility-first styling
- **Lucide React**: Icon library

## Features Overview

### Dashboard

The main dashboard provides:
- **Statistics Cards**: Total cards, total value, last update time
- **Price Chart**: Placeholder for future price history tracking
- **Action Buttons**: Trigger card processing or price updates
- **Filters**: Search by name, filter by rarity
- **Card Table**: Sortable, paginated table of your collection

### Real-time Progress

When you trigger a process:
1. A modal appears showing connection status
2. Progress bar updates in real-time via WebSocket
3. Errors are displayed as they occur
4. Completion summary shows total processed and errors

### Data Caching

TanStack Query provides:
- 30-second stale time for stats and cards
- Automatic refetching every 30 seconds
- Background updates without blocking UI
- Optimistic UI updates

## API Integration

The frontend communicates with the backend via:

**REST API**:
- GET `/api/health` - Health check
- GET `/api/cards` - List cards (with pagination/search)
- GET `/api/stats` - Collection statistics
- POST `/api/process` - Trigger card processing
- POST `/api/prices/update` - Trigger price update
- GET `/api/jobs/{id}` - Job status

**WebSocket**:
- `ws://localhost:8000/ws/progress/{job_id}` - Real-time progress updates

## Development Tips

### Hot Reload

Vite provides instant HMR (Hot Module Replacement). Changes appear immediately without full page reload.

### TypeScript

The project uses strict TypeScript. All API types are defined in `src/api/client.ts`.

### Styling

Tailwind CSS utility classes are used throughout. Common patterns:
- `rounded-lg shadow` for cards
- `px-6 py-4` for padding
- `hover:bg-gray-50` for interactive elements

### State Management

- **TanStack Query**: Server state (API data)
- **React useState**: Local component state (filters, modals)
- No global state library needed for MVP

## Testing

Currently manual testing. To test:

1. Start backend: `cd backend && uvicorn api.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173
4. Verify:
   - Stats load correctly
   - Card table displays collection
   - Filters work (search, rarity)
   - Process buttons trigger jobs
   - Progress modal shows real-time updates

## Troubleshooting

### "Failed to fetch"
- Ensure backend is running on port 8000
- Check Vite proxy configuration in `vite.config.ts`

### WebSocket connection fails
- Backend must be running
- Job ID must be valid (created via POST to `/api/process`)
- Check browser console for WebSocket errors

### Tailwind styles not working
- Ensure `tailwind.config.js` content paths include all component files
- Check that `@tailwind` directives are in `index.css`
- Restart dev server after config changes

### TypeScript errors
- Run `npm run build` to see all type errors
- Check `tsconfig.json` if issues persist

## Future Enhancements

- Price history chart with real data (currently placeholder)
- Card detail modal with full information
- Export collection to CSV
- Advanced filtering (by set, color, type)
- Pagination improvements for large collections (>2000 cards)
- Mobile responsive design
- Dark mode toggle

## Related Documentation

- [Backend README](../backend/README.md) - API documentation
- [Main README](../README.md) - CLI documentation
- [Design Doc](../openspec/changes/web-mvp/design.md) - Technical decisions
