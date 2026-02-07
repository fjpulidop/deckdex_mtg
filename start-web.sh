#!/bin/bash
# Start DeckDex MTG Web MVP
# This script starts both backend and frontend servers

echo "🚀 Starting DeckDex MTG Web MVP..."
echo ""

# Check if dependencies are installed
if [ ! -d "backend/api" ]; then
    echo "❌ Error: Backend not found. Are you in the project root?"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  Frontend dependencies not installed. Installing now..."
    cd frontend && npm install && cd ..
fi

# Check Python environment
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Backend dependencies not installed. Installing now..."
    pip3 install -r backend/requirements-api.txt
    pip3 install -r requirements.txt
fi

# Create logs directory if it doesn't exist
mkdir -p backend/logs

echo "✅ All dependencies ready"
echo ""
echo "Starting servers..."
echo ""
echo "📡 Backend will run on: http://localhost:8000"
echo "🌐 Frontend will run on: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Start backend in background
cd backend
uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend in foreground
cd frontend
npm run dev

# When frontend is stopped, kill backend too
kill $BACKEND_PID 2>/dev/null
