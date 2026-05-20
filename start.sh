#!/bin/bash
# =============================================================================
#  CrimeGPT — Core Start & Launch Orchestration Script
#  Source: https://github.com/XploitMonk0x01/crimegpt
#
#  Usage:
#    chmod +x start.sh && ./start.sh
# =============================================================================

set -euo pipefail

# Make sure we run from the script directory
cd "$(dirname "$0")"

# ── Colours & Typography ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# ── Logging Helpers ───────────────────────────────────────────────────────────
info()    { echo -e "${BLUE}ℹ  $*${NC}"; }
success() { echo -e "${GREEN}✔  $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠  $*${NC}"; }
error()   { echo -e "${RED}✖  $*${NC}"; exit 1; }
divider() { echo -e "${CYAN}────────────────────────────────────────────────────────────${NC}"; }

# ── Banner ────────────────────────────────────────────────────────────────────
clear
echo -e "${BOLD}${CYAN}"
cat << 'EOF'
   ██████╗██████╗ ██╗███╗   ███╗███████╗ ██████╗ ██████╗ ████████╗
  ██╔════╝██╔══██╗██║████╗ ████║██╔════╝██╔════╝ ██╔══██╗╚══██╔══╝
  ██║     ██████╔╝██║██╔████╔██║█████╗  ██║  ███╗██████╔╝   ██║   
  ██║     ██╔══██╗██║██║╚██╔╝██║██╔══╝  ██║   ██║██╔═══╝    ██║   
  ╚██████╗██║  ██║██║██║ ╚═╝ ██║███████╗╚██████╔╝██║        ██║   
   ╚═════╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝        ╚═╝   
EOF
echo -e "${NC}"
echo -e "         ${BOLD}${YELLOW} CrimeGPT Application Runtime Launcher ${NC}"
divider
echo ""

# ── Verification of Setup ─────────────────────────────────────────────────────
info "Verifying system installation health..."

# 1. Check directories
if [ ! -d "backend/venv" ] || [ ! -d "frontend/node_modules" ]; then
  echo ""
  warn "CrimeGPT has not been completely installed or set up on this device."
  info "Please run the installation script first:"
  echo -e "  ${BOLD}${GREEN}./install.sh${NC}"
  echo ""
  exit 1
fi

# 2. Check compose command
if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
else
  error "Docker Compose command not found. Ensure Docker is running."
fi

# ── Spawning Docker Infrastructure (if not up) ──────────────────────────────────
info "Ensuring Docker infrastructure is active..."
$COMPOSE_CMD up -d

# Postgres check
for i in $(seq 1 15); do
  if $COMPOSE_CMD exec -T db pg_isready -U crimegpt >/dev/null 2>&1 || \
     docker exec "$(docker ps -qf name=postgres)" pg_isready >/dev/null 2>&1 || \
     docker exec "$(docker ps -qf name=crimegpt)" pg_isready >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

# ── Spawning Services ─────────────────────────────────────────────────────────
mkdir -p logs

# 1. Launch FastAPI Backend
info "Launching FastAPI backend API server..."
cd backend
./venv/bin/python -m uvicorn app.server:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload \
  > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
success "Backend initialized successfully (PID: $BACKEND_PID)"

# Wait for backend binding
sleep 2

# 2. Launch Vite Frontend
info "Launching React-Vite frontend UI server..."
cd frontend
npm run dev -- --host \
  > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
success "Frontend initialized successfully (PID: $FRONTEND_PID)"

# ── Launch Success Dashboard ──────────────────────────────────────────────────
echo ""
divider
echo -e "${BOLD}${GREEN}  🚀  CrimeGPT Services are active & running!${NC}"
divider
echo ""
echo -e "  🌐  ${BOLD}Web Interface :${NC}  ${BOLD}${CYAN}http://localhost:5173${NC}"
echo -e "  🔌  ${BOLD}Backend API   :${NC}  ${CYAN}http://127.0.0.1:8000${NC}"
echo -e "  📖  ${BOLD}API Docs      :${NC}  ${CYAN}http://127.0.0.1:8000/docs${NC}"
echo ""
echo -e "  🛡️   ${BOLD}Demo Auth Credentials:${NC}"
echo -e "      Badge Number:  ${YELLOW}PN-2024-ADMIN${NC}"
echo -e "      Security PIN:  ${YELLOW}1234${NC}"
echo ""
echo -e "  📁  ${BOLD}Live Output Logs:${NC}"
echo -e "      API Stream  →  ${MAGENTA}logs/backend.log${NC}"
echo -e "      Vite Stream →  ${MAGENTA}logs/frontend.log${NC}"
echo ""
echo -e "  ${YELLOW}💡 Press Ctrl+C in this terminal at any time to suspend services.${NC}"
divider
echo ""

# ── SIGINT / SIGTERM Process Lifecycle Cleaner ─────────────────────────────────
cleanup() {
  echo ""
  warn "Received termination signal. Shutting down system services..."
  
  info "Stopping backend server (PID: $BACKEND_PID)..."
  kill "$BACKEND_PID" 2>/dev/null || true
  
  info "Stopping frontend server (PID: $FRONTEND_PID)..."
  kill "$FRONTEND_PID" 2>/dev/null || true
  
  success "Web servers successfully suspended."

  echo ""
  read -rp "  Would you also like to shut down the PostgreSQL and Redis containers? [y/N]: " STOP_CONTAINERS
  if [[ "$STOP_CONTAINERS" =~ ^[Yy]$ ]]; then
    info "Running: $COMPOSE_CMD down"
    $COMPOSE_CMD down
    success "Docker databases brought down."
  else
    info "Docker databases kept running in background."
  fi

  echo -e "\n${BOLD}${GREEN}👋 Goodbye!${NC}"
  exit 0
}

trap cleanup INT TERM

# Wait on background subprocesses
wait "$BACKEND_PID" "$FRONTEND_PID"
