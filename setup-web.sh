#!/bin/bash
# Quick setup script for DeckDex MTG Web MVP

echo "🚀 DeckDex MTG Web MVP - Quick Setup"
echo "===================================="
echo ""

# Check if we're in the project root
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not found"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is required but not found"
    exit 1
fi

echo "1️⃣  Installing backend dependencies..."
cd backend
pip3 install -r requirements-api.txt
cd ..
pip3 install -r requirements.txt

echo ""
echo "2️⃣  Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Configure your environment variables:"
echo "   cp .env.example .env"
echo "   # Edit .env with your credentials"
echo ""
echo "2. Start the backend (terminal 1):"
echo "   cd backend"
echo "   uvicorn api.main:app --reload"
echo ""
echo "3. Start the frontend (terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Open http://localhost:5173 in your browser"
echo ""
