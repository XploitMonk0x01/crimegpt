#!/bin/bash

# CrimeGPT Automated Setup & Start Script
# This script handles infrastructure, backend, and frontend.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting CrimeGPT Development Environment Setup...${NC}"

# 1. Check Prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}❌ Docker is required but not installed. Aborting.${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}❌ docker-compose is required but not installed. Aborting.${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}❌ npm is required but not installed. Aborting.${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}❌ python3 is required but not installed. Aborting.${NC}"; exit 1; }

# 2. Infrastructure
echo -e "${BLUE}🐳 Starting Docker infrastructure (PostgreSQL, Redis)...${NC}"
docker-compose up -d

# 3. Backend Setup
echo -e "${BLUE}🐍 Setting up Backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo -e "${GREEN}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${GREEN}📥 Installing backend dependencies...${NC}"
./venv/bin/pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo -e "${GREEN}📄 Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  ACTION REQUIRED: Please update backend/.env with your GROQ_API_KEY!${NC}"
fi

echo -e "${GREEN}🏗️ Initializing database schema...${NC}"
./venv/bin/python init_db.py

# 4. Frontend Setup
echo -e "${BLUE}⚛️ Setting up Frontend...${NC}"
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo -e "${GREEN}📥 Installing frontend dependencies (this may take a minute)...${NC}"
    npm install --no-audit --no-fund
fi

# 5. Start Services
echo -e "${BLUE}🟢 Starting Services...${NC}"

# Start Backend in background
cd ../backend
./venv/bin/python -m uvicorn app.server:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Start Frontend in background
cd ../frontend
npm run dev -- --host > frontend.log 2>&1 &
FRONTEND_PID=$!

echo -e "${GREEN}✅ All services are launching!${NC}"
echo -e "📡 ${BLUE}Backend API:${NC} http://127.0.0.1:8000"
echo -e "📡 ${BLUE}Frontend UI:${NC} http://localhost:5173"
echo -e "📝 ${BLUE}Logs:${NC} backend/backend.log, frontend/frontend.log"
echo -e "${RED}💡 Press Ctrl+C to stop all services.${NC}"

# Handle termination
trap "echo -e '${RED}🛑 Stopping services...${NC}'; kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
