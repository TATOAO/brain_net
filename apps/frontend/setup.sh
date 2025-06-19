#!/bin/bash

echo "🚀 Setting up Brain Net Frontend..."

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm globally..."
    npm install -g pnpm
fi

# Install dependencies
echo "📦 Installing dependencies..."
pnpm install

# Check if backend is running
echo "🔍 Checking if backend is running on localhost:8000..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running!"
else
    echo "⚠️  Backend not detected on localhost:8000"
    echo "   Make sure to start the Brain Net backend first"
fi

echo "🎉 Setup complete!"
echo ""
echo "To start the development server:"
echo "  pnpm dev"
echo ""
echo "Then open http://localhost:3000 in your browser" 