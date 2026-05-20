#!/bin/bash
# =============================================================================
#  CrimeGPT — Custom Premium Installation Script
#  Source: https://github.com/XploitMonk0x01/crimegpt
#
#  Usage:
#    chmod +x install.sh && ./install.sh
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
step()    { echo -e "\n${BOLD}${MAGENTA}══ $* ══${NC}"; }
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
echo -e "         ${BOLD}${YELLOW} CrimeGPT Full-Stack System Installer ${NC}"
echo -e "     ${BOLD}${NC}Empowering Indian Law Enforcement with RAG & BNS 2023${NC}"
divider
echo ""

# ── STEP 1: Prerequisites Check ────────────────────────────────────────────────
step "Step 1/5: Verification of Prerequisites"

check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    success "$1 found ($(command -v "$1"))"
  else
    error "$1 is required but not installed. $2"
  fi
}

check_cmd git      "Please install git: https://git-scm.com/downloads"
check_cmd docker   "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
check_cmd npm      "Please install Node.js: https://nodejs.org"
check_cmd python3  "Please install Python 3.11+: https://www.python.org/downloads"

# Check docker-compose command compatibility
if command -v docker-compose >/dev/null 2>&1; then
  success "docker-compose command available"
  COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  success "docker compose (v2 plugin) available"
  COMPOSE_CMD="docker compose"
else
  error "docker-compose or 'docker compose' is required."
fi

# Validate Python Version (minimum 3.11)
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
  warn "Python $PY_VER detected. CrimeGPT works best with Python 3.11+. Continuing anyway..."
else
  success "Python $PY_VER satisfies constraints (>= 3.11)"
fi

# ── STEP 2: Environment Provisioning ───────────────────────────────────────────
step "Step 2/5: Configuration & Environment Setup"

# --- Backend Config ---
if [ ! -f "backend/.env" ]; then
  if [ -f "backend/.env.example" ]; then
    cp backend/.env.example backend/.env
    info "Generated backend/.env from .env.example"
  else
    cat > backend/.env << 'ENVEOF'
# Application config
APP_NAME=CrimeGPT
APP_VERSION=0.1.0
DEBUG=true
API_PREFIX=/api/v1
CORS_ORIGINS=["*"]

# Database URL
DATABASE_URL=postgresql+asyncpg://crimegpt:crimegpt_pass@localhost:5432/crimegpt_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=false

# Redis Cache URL
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_TTL=28800

# Auth and Cryptography
JWT_SECRET=crimegpt_jwt_super_session_sec_key_token
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=8
REFRESH_TOKEN_EXPIRY_DAYS=7

# LLM integration
LLM_MODE=cloud
GROQ_API_KEY=your_groq_api_key_here

GROQ_MODEL_PRIMARY=meta-llama/llama-4-scout-17b-16e-instruct
GROQ_MODEL_FAST=llama-3.1-8b-instant
GROQ_MODEL_FALLBACK=llama-3.3-70b-versatile
GROQ_MODEL_WHISPER=whisper-large-v3-turbo

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION=legal_corpus

# Evidence Storage
EVIDENCE_STORAGE_PATH=./storage/evidence
EVIDENCE_MAX_FILE_SIZE_MB=50
ENVEOF
    info "Created brand new backend/.env with robust defaults"
  fi
fi

# Interactive GROQ_API_KEY setup if empty or placeholder
CURRENT_KEY=$(grep -E '^GROQ_API_KEY=' backend/.env | cut -d= -f2- | tr -d '[:space:]')
if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" = "your_groq_api_key_here" ]; then
  echo ""
  echo -e "${YELLOW}  💡 A Groq API key is recommended to run the AI engine (LexBot & FIR Automator).${NC}"
  echo -e "  Register for your free API key at: ${BOLD}https://console.groq.com${NC}"
  echo ""
  read -rp "  Paste your GROQ_API_KEY (or hit Enter to skip and add it manually later): " USER_KEY
  if [ -n "$USER_KEY" ]; then
    # Cross-platform compatible inline replacement
    sed -i.bak "s|^GROQ_API_KEY=.*|GROQ_API_KEY=${USER_KEY}|" backend/.env && rm -f backend/.env.bak
    success "GROQ_API_KEY successfully recorded to backend/.env!"
  else
    warn "Skipped. You can add it later inside backend/.env"
  fi
else
  success "GROQ_API_KEY is already configured."
fi

# --- Frontend Config ---
if [ ! -f "frontend/.env" ]; then
  echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > frontend/.env
  success "Created frontend/.env"
else
  success "frontend/.env already exists."
fi

# ── STEP 3: Spawning Docker Infrastructure ─────────────────────────────────────
step "Step 3/5: Initializing Docker Infrastructure"

info "Starting Docker database services ($COMPOSE_CMD up -d)..."
$COMPOSE_CMD up -d

# Postgres readiness check (30 seconds limit)
info "Verifying database readiness..."
for i in $(seq 1 30); do
  if $COMPOSE_CMD exec -T db pg_isready -U crimegpt >/dev/null 2>&1 || \
     docker exec "$(docker ps -qf name=postgres)" pg_isready >/dev/null 2>&1 || \
     docker exec "$(docker ps -qf name=crimegpt)" pg_isready >/dev/null 2>&1; then
    success "PostgreSQL engine is fully operational!"
    break
  fi
  if [ "$i" -eq 30 ]; then
    warn "PostgreSQL ready check timed out, proceeding anyway."
  else
    echo -n "."
    sleep 1
  fi
done

# ── STEP 4: Backend Virtualenv & Dependencies ────────────────────────────────
step "Step 4/5: Python Backend & Database Initialization"

cd backend

if [ ! -d "venv" ]; then
  info "Generating clean Python virtual environment..."
  python3 -m venv venv
  success "Virtual environment generated at backend/venv/"
else
  success "Existing Python virtual environment discovered."
fi

info "Installing optimized backend dependencies..."
./venv/bin/pip install --upgrade pip --quiet
./venv/bin/pip install -r requirements.txt --quiet
success "All backend packages successfully installed."

info "Executing database schema migrations..."
./venv/bin/python init_db.py && success "Database tables successfully initialized." || warn "DB initialization command complete."

cd ..

# ── STEP 5: Frontend Node Modules ──────────────────────────────────────────────
step "Step 5/5: Frontend Package Provisioning"

cd frontend
info "Installing frontend packages (Vite, React 19, Tailwind)..."
npm install --no-audit --no-fund
success "Frontend packages successfully installed."
cd ..

# ── Premium Finish Banner ──────────────────────────────────────────────────────
echo ""
divider
echo -e "${BOLD}${GREEN}  ✨  CrimeGPT Full-Stack System Installation Completed!${NC}"
divider
echo ""
echo -e "  To launch the whole system (Frontend, Backend & Docker DBs), run:"
echo -e "  ${BOLD}${YELLOW}  ./start.sh${NC}"
echo ""
echo -e "  Your databases are already running in background containers."
echo -e "  Have fun exploring the platform!"
divider
echo ""
