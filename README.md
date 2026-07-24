<div align="center">

<a id="-crimegpt-top"></a>

[![GitHub stars](https://img.shields.io/github/stars/XploitMonk0x01/crimegpt?style=for-the-badge&logo=github&logoColor=white&labelColor=0d1117&color=e63946)](https://github.com/XploitMonk0x01/crimegpt/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/XploitMonk0x01/crimegpt?style=for-the-badge&logo=github&logoColor=white&labelColor=0d1117&color=e63946)](https://github.com/XploitMonk0x01/crimegpt/network)
[![License](https://img.shields.io/badge/license-MIT-e63946?style=for-the-badge&labelColor=0d1117)](LICENSE)
[![Built With](https://img.shields.io/badge/built%20with-React%20%2B%20FastAPI-e63946?style=for-the-badge&labelColor=0d1117)](https://github.com/XploitMonk0x01/crimegpt)

</div>

<p align="center">
  <img src="crimegpt-logo.png" alt="CrimeGPT Logo" width="55%"/>
</p>

<div align="center">

<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=13&pause=1000&color=e63946&vCenter=true&width=600&height=20&lines=AI-POWERED+CRIME+DOCUMENTATION+%26+LEGAL+INTELLIGENCE+PLATFORM" width="620"/>

<br/><br/>

<a href="#-quick-start"><kbd> <br> Quick Start <br> </kbd></a>&ensp;&ensp;
<a href="#-features"><kbd> <br> Features <br> </kbd></a>&ensp;&ensp;
<a href="#-architecture"><kbd> <br> Architecture <br> </kbd></a>&ensp;&ensp;
<a href="#-api-routes"><kbd> <br> API Routes <br> </kbd></a>&ensp;&ensp;
<a href="#-modules"><kbd> <br> Modules <br> </kbd></a>&ensp;&ensp;
<a href="#-configuration"><kbd> <br> Configuration <br> </kbd></a>&ensp;&ensp;
<a href="#-contributing"><kbd> <br> Contributing <br> </kbd></a>

</div>

<br/>

---

<a id="-overview"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=OVERVIEW" width="450"/>

---

**CrimeGPT** is a next-generation AI-powered platform engineered for modern Law Enforcement in India. It transforms the traditional, paper-heavy crime documentation process into a streamlined, digital-first workflow driven by Retrieval-Augmented Generation (RAG), multi-model LLM routing, and a full-stack React + FastAPI architecture.

> **Legal Framework:** Optimized for **BNS 2023** (Bharatiya Nyaya Sanhita), **BNSS** (Bharatiya Nagarik Suraksha Sanhita), **BSA** (Bharatiya Sakshya Adhiniyam), and **IT Act 2000**

### 🚀 Core Value Proposition

| Feature | Traditional Method | CrimeGPT Advantage |
|---|---|---|
| **FIR Generation** | 2–3 hours manual drafting | **&lt; 30 seconds** AI-structured drafts |
| **Legal Research** | Manual book lookups | **Instant** BNS 2023 RAG Intelligence |
| **Documents** | Manual typing of each form | **Auto-generated** Chargesheets, Remand, Seizure, etc. |
| **Evidence** | Physical logbooks | **Immutable** digital chain-of-custody + SHA-256 |
| **Intelligence** | Manual link detection | **AI-driven** MO pattern recognition |
| **Interoperability** | Siloed systems | **CCTNS / BharatPol** mock integration |

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-quick-start"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=QUICK+START" width="450"/>

---

### 🚀 Automated Setup (Recommended)

The installer handles all dependencies, Python venv, npm packages, Docker infrastructure, and database schemas:

```bash
git clone git@github.com:XploitMonk0x01/crimegpt.git
cd crimegpt
./install.sh
./start.sh
```

The `install.sh` script will:
1. ✅ Verify prerequisites (git, docker, npm, python3, docker-compose)
2. ✅ Prompt for Groq API key (optional — for LLM features)
3. ✅ Launch PostgreSQL, Redis, and ChromaDB via Docker
4. ✅ Set up Python virtual environment and install dependencies
5. ✅ Install frontend npm packages
6. ✅ Initialize database schema and seed demo data

### Manual Setup

#### 1. Start Infrastructure (PostgreSQL + Redis + ChromaDB)

```bash
docker compose up -d
```

#### 2. Backend Setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GROQ_API_KEY (get one at https://console.groq.com)
python init_db.py
python seed_demo.py
uvicorn app.server:app --host 127.0.0.1 --port 8000 --reload
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev -- --host
```

### Demo Credentials

| Role | Badge Number | Security PIN |
|---|---|---|
| **Admin** | `PN-2024-ADMIN` | `1234` |
| **Station Head (SHO)** | `PN-2024-SHO` | `1234` |
| **Investigating Officer (IO)** | `PN-2024-IO` | `1234` |

The app will be available at **`http://localhost:5173`**.

> [!TIP]
> The API docs (Swagger UI) are available at `http://127.0.0.1:8000/docs` when `DEBUG=true`.

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-features"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=FEATURES" width="450"/>

---

### 📋 FIR Automator
- Natural language incident input → structured AI FIR draft with NER extraction
- **Sequential FIR numbering**: `FIR-00001`, `FIR-00002`, ...
- Complainant & accused details, location, applicable BNS/IT sections
- Persistent local storage — works offline; syncs when backend is available
- Country-aware phone input with flag selector
- Full FIR lifecycle: **draft → submit → approve/reject**

### 🧠 LexBot — Legal Intelligence Agent
- Real-time Q&A powered by **Groq LLM** (multi-model routing)
- Trained on **BNS 2023**, **IT Act 2000** corpora via RAG pipeline
- **Hybrid retrieval**: ChromaDB vector search + BM25 lexical search fused via Reciprocal Rank Fusion
- Markdown-formatted responses with section citations
- RAG safety controls: prompt injection stripping, PII redaction (configurable)
- Configurable allowed domains for URL-based corpus ingestion

### 🗄️ Evidence Vault
- Secure digital evidence upload tied to specific FIRs
- **SHA-256 integrity hashing** on every upload
- **Immutable chain of custody** — append-only JSONB audit trail
- File type detection & image gallery preview
- Integrity verification endpoint
- Role-restricted upload (Inspector+)

### 📊 Command Dashboard
- **Role-aware**: IO sees personal stats; SHO/Admin see station-wide metrics
- Live FIR counts: Total, Draft, Submitted, Approved, Rejected
- Recent FIR activity feed with status badges
- Pending approvals queue (SHO/Admin)
- Audit log viewer (SHO/Admin)
- Crime analytics & trend data

### 🔗 Case Linkage
- **AI-powered pattern detection** across multiple FIRs
- Semantic similarity scoring using vector embeddings
- **Formal case linking** by Inspector+ officers
- MO (Modus Operandi) cluster analysis
- Find similar cases by configurable threshold (default 0.70)

### 📄 Document Generator
- **AI-powered generation** of 7 legal document types from FIR data:

| Document Type | Description |
|---|---|
| `chargesheet` | Purvani/Final Report under BNSS |
| `medical_letter` | Medical Treatment Letter for victims |
| `remand_request` | Police Custody Remand Request |
| `seizure_receipt` | Seizure & Search Receipt (Panchanama) |
| `court_custody_letter` | Court Custody Transfer Letter |
| `accused_panchanama` | Accused Observation Panchanama |
| `face_id_form` | Accused Face Identification Form |

- PDF export with metadata
- **Version history** — every generation creates a snapshot
- Multilingual document generation (English, Hindi, Gujarati)

### 📓 Case Diary
- **Timeline-based** investigation diary tied to each FIR
- 12 entry types: complaint received, FIR registered, investigation started, witness examined, evidence seized, spot visit, arrest made, remand requested, chargesheet filed, court hearing, etc.
- Ordered timeline with officer attribution
- Entry deletion (Inspector+ only)

### 🌐 LERS Cyber Portal
- Generate **LERS-compliant** law enforcement requests for:
  - **Meta / Facebook** — Emergency Disclosure, Account Preservation, Subscriber & IP Log
  - **WhatsApp** — Emergency Disclosure, Account Preservation
  - **Instagram** — Emergency Disclosure, Account Preservation
  - **Telegram** — Emergency Disclosure, Account Preservation
  - **X (Twitter)** — Emergency Disclosure, Account Preservation
- Generates legally-formatted notice templates with:
  - Section 94 BNSS / Section 91 CrPC legal authority
  - Platform-specific SLA data
  - Reference IDs and digital attestation
- Searchable FIR autocomplete for reference numbers
- Live demo credentials auto-filled for demo mode

### 🔐 Auth & RBAC
- **JWT-based authentication** with access + refresh token rotation
- **Redis-backed session management** with logout invalidation
- **4-tier Role-Based Access Control**:

| Capability | Constable | IO | SHO | Admin |
|---|---|---|---|---|
| FIR: create / edit | ✅ | ✅ | ✅ | ✅ |
| FIR: approve / reject | ❌ | ❌ | ✅ | ✅ |
| Evidence: upload | ❌ | ✅ | ✅ | ✅ |
| Case: link | ❌ | ✅ (Inspector) | ✅ | ✅ |
| Diary: delete | ❌ | ❌ | ✅ | ✅ |
| Officer: register | ❌ | ❌ | ❌ | ✅ |
| Audit: view | ❌ | ❌ | ✅ | ✅ |
| RAG corpus: ingest | ❌ | ❌ | ❌ | ✅ |

- Demo bypass mode for development (no DB query for mock users)

### 🔄 CCTNS / BharatPol Interoperability
- **Mock CCTNS National Grid FIR sync** with SHA-256 payload verification
- **BharatPol criminal record lookup** with deterministic mock responses
- CCTNS Reference ID generation and sync status API
- Audit-logged sync events

### 🌍 Multilingual Support
- **Speech-to-text** via Groq Whisper (`whisper-large-v3-turbo`)
- **Translation** between English ↔ Hindi ↔ Gujarati
- Audio transcription with 25MB file limit, multiple format support
- Configurable language for document generation

### 📋 Immutable Audit Trail
- **Append-only** audit log table — no updates or deletes
- Tracks: LOGIN, LOGOUT, FIR_CREATE, FIR_EDIT, FIR_SUBMIT, FIR_APPROVE, FIR_REJECT, FIR_SEARCH, FIR_EXPORT_PDF, CCTNS_SYNC, DOCUMENT_GENERATE, DOCUMENT_EXPORT_PDF, DIARY_ENTRY_ADD, DIARY_ENTRY_DELETE, EVIDENCE_UPLOAD, EVIDENCE_ACCESS, EVIDENCE_VERIFY, CASE_LINK, LEGAL_QUERY, TRANSLATE
- Each entry stores: officer, action, resource type/ID, details (JSONB), IP address, user agent, timestamp
- Eager-loaded officer metadata (badge_no, name) for display

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-architecture"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=ARCHITECTURE" width="450"/>

---

```
crimegpt/
├── frontend/                          # React + Vite SPA
│   ├── src/
│   │   ├── components/                # 11 UI Components
│   │   │   ├── Login.jsx              # Auth entry point
│   │   │   ├── Dashboard.jsx          # Role-based command center
│   │   │   ├── FIRAutomator.jsx       # AI FIR drafting
│   │   │   ├── LexBot.jsx             # Legal Q&A assistant
│   │   │   ├── Vault.jsx              # Evidence management
│   │   │   ├── CaseLinkage.jsx        # Cross-case pattern analysis
│   │   │   ├── CaseDiary.jsx          # Investigation timeline
│   │   │   ├── DocumentGenerator.jsx  # Legal doc auto-generation
│   │   │   ├── LERSPortal.jsx         # LERS cyber request platform
│   │   │   ├── Sidebar.jsx            # RBAC-aware navigation
│   │   │   └── UserSettings.jsx       # Profile & preferences
│   │   ├── services/
│   │   │   └── api.js                 # Axios service layer (auth, fir,
│   │   │                               #   evidence, legal, nlp, docs,
│   │   │                               #   diary, search, cctns, lers)
│   │   └── store/
│   │       ├── authStore.js           # Zustand auth state
│   │       └── firStore.js            # Zustand FIR state + localStorage
│   ├── package.json
│   └── vite.config.js
│
├── backend/                           # FastAPI Python API
│   ├── app/
│   │   ├── routes/                    # 12 API routers
│   │   │   ├── authRoutes.py          # POST /login, /refresh, /logout, /register
│   │   │   ├── firRoutes.py           # POST /generate, /submit, PATCH /{id}/edit, ...
│   │   │   ├── legalRoutes.py         # POST /query, GET /sections/search, /corpus/*
│   │   │   ├── evidenceRoutes.py      # POST /upload, GET /fir/{id}, /{id}/custody...
│   │   │   ├── caseRoutes.py          # GET /similar/{id}, POST /link, GET /clusters
│   │   │   ├── nlpRoutes.py           # POST /transcribe, /translate, GET /languages
│   │   │   ├── dashboardRoutes.py     # GET /officer, /inspector, /audit-logs, /analytics
│   │   │   ├── documentRoutes.py      # GET /types, POST /generate, /export-pdf, /versions
│   │   │   ├── caseDiaryRoutes.py     # GET /types, POST /{firId}/entry, DELETE /entry/{id}
│   │   │   ├── searchRoutes.py        # GET /search?q=...
│   │   │   ├── cctnsRoutes.py         # POST /sync-fir/{id}, GET /verify-person, /status/{id}
│   │   │   └── lersRoutes.py          # POST /generate, GET /platforms, /request-types
│   │   ├── controllers/              # Request/response orchestration
│   │   ├── services/                 # Business logic (14 services)
│   │   ├── models/                   # SQLAlchemy ORM (7 models)
│   │   ├── schemas/                  # Pydantic validation
│   │   ├── middleware/               # Auth, RBAC, error handler, rate limiter
│   │   ├── config/                   # Pydantic Settings (env-based)
│   │   ├── types/                    # Enums, response types
│   │   ├── utils/                    # JWT, hashing, hybrid_retrieval, text_extraction
│   │   └── main.py                   # App factory
│   ├── corpus/                       # Legal corpus for RAG ingestion
│   │   ├── bns_2023/                 # Bharatiya Nyaya Sanhita 2023
│   │   └── it_act_2000/              # Information Technology Act 2000
│   ├── init_db.py                    # DB schema initializer
│   ├── seed_demo.py                  # Demo data seeder
│   └── requirements.txt
│
├── docker-compose.yml                # PostgreSQL, Redis, ChromaDB
├── install.sh                        # Automated setup & dependency installer
├── start.sh                          # Application runtime launcher
├── docs/                             # Documentation
│   ├── day3/execution-plan.md        # Day 3 execution pack
│   ├── demo-checklist.md             # Demo walkthrough checklist
│   ├── document-compliance-matrix.md # PS document mapping
│   ├── eval/legal-benchmark.json     # Legal evaluation benchmark
│   └── samples/                      # 7 document sample outputs
└── README.md
```

### Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, Vite 8, Tailwind CSS 4, Framer Motion |
| **State** | Zustand + localStorage (offline FIR persistence) |
| **Backend** | FastAPI, Python 3.11+ (supports 3.13) |
| **Database** | PostgreSQL 15 (Docker) |
| **Cache** | Redis 7 (Docker) |
| **Vector Store** | ChromaDB (Docker) |
| **LLM Provider** | Groq API (Llama 3.3 70B / Llama 3.1 8B) |
| **LLM Local** | Ollama (Mistral 7B) |
| **STT** | Groq Whisper (whisper-large-v3-turbo) |
| **Auth** | JWT (access + refresh) + Redis session management |
| **Search** | Hybrid BM25 + ChromaDB vector (Reciprocal Rank Fusion) |

### Data Models

| Model | Table | Key Fields |
|---|---|---|
| **Officer** | `officers` | badge_no, role (constable/inspector/station_head/admin), station_id |
| **FIR** | `firs` | fir_no, complainant (JSONB), accused (JSONB), sections (TEXT[]), status |
| **Evidence** | `evidence` | fir_id, sha256_hash, chain_of_custody (JSONB[]), metadata_json |
| **CaseLink** | `case_links` | fir_id_a, fir_id_b, similarity_score, link_reason |
| **AuditLog** | `audit_logs` | action, resource_type, resource_id, details (JSONB), ip_address |
| **CaseDiaryEntry** | `case_diary_entries` | fir_id, entry_type, title, description, entry_date |
| **DocumentVersion** | `document_versions` | fir_id, document_type, version_no, content, metadata |

### FIR Lifecycle

```
DRAFT → SUBMITTED → APPROVED
                ↓
            REJECTED
```

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-api-routes"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=API+ROUTES" width="450"/>

---

All routes are mounted under `/api/v1` and require JWT authentication (except `/health`).

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | `/login` | Authenticate with badge_no + pin | Public (rate-limited) |
| POST | `/refresh` | Rotate refresh token | Public (rate-limited) |
| POST | `/logout` | Invalidate session | Authenticated |
| GET | `/me` | Current officer profile | Authenticated |
| POST | `/register` | Register new officer | Admin/SHO |

### FIR Management (`/api/v1/fir`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/generate` | AI draft from incident narrative |
| POST | `/submit` | Submit FIR with full data |
| GET | `/list` | List FIRs (filterable by status, paginated) |
| GET | `/{id}` | Get FIR by ID |
| PATCH | `/{id}/edit` | Edit draft FIR |
| POST | `/{id}/review` | Approve/reject FIR (SHO/Admin) |

### Legal Intelligence (`/api/v1/legal`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/query` | RAG-powered legal Q&A |
| GET | `/sections/search` | Search legal sections by keyword |
| POST | `/corpus/ingest` | Ingest corpus into vector store (Admin) |
| POST | `/corpus/ingest-urls` | Ingest URLs into vector store (Admin) |
| GET | `/corpus/stats` | Vector store statistics |

### Evidence Management (`/api/v1/evidence`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload evidence file (Inspector+) |
| GET | `/fir/{fir_id}` | List evidence for a FIR |
| GET | `/{id}/download` | Download evidence file |
| GET | `/{id}/custody` | Get custody chain |
| GET | `/{id}/verify` | Verify SHA-256 integrity |

### Case Linkage (`/api/v1/cases`)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/similar/{fir_id}` | Find semantically similar cases |
| POST | `/link` | Formally link two cases (Inspector+) |
| GET | `/clusters` | MO cluster analysis |

### NLP & Translation (`/api/v1/nlp`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/transcribe` | Speech-to-text (Groq Whisper) |
| POST | `/translate` | Translate text (en/hi/gu) |
| GET | `/languages` | List supported languages |

### Dashboard (`/api/v1/dashboard`)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/officer` | Personal dashboard | Authenticated |
| GET | `/inspector` | Station-wide dashboard | Inspector+ |
| GET | `/audit-logs` | Immutable audit trail | SHO/Admin |
| GET | `/analytics` | Crime analytics | Authenticated |

### Document Generation (`/api/v1/documents`)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/types` | List document types |
| POST | `/generate` | Generate document from FIR data |
| POST | `/export-pdf` | Export as downloadable PDF |
| GET | `/{fir_id}/versions` | List document versions |
| GET | `/versions/{id}` | Get specific version |

### Case Diary (`/api/v1/diary`)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/types` | List entry types |
| POST | `/{fir_id}/entry` | Add diary entry |
| GET | `/{fir_id}` | Get full case diary |
| DELETE | `/entry/{id}` | Delete entry (Inspector+) |

### Search (`/api/v1/search`)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Full-text FIR search |

### CCTNS / BharatPol (`/api/v1/cctns`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sync-fir/{fir_id}` | Sync FIR to CCTNS national grid |
| GET | `/verify-person` | BharatPol criminal record lookup |
| GET | `/status/{fir_id}` | CCTNS sync status |

### LERS Cyber Portal (`/api/v1/lers`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/generate` | Generate LERS notice |
| GET | `/platforms` | List supported platforms |
| GET | `/request-types` | List request types |

### Health (`/`)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-modules"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=MODULES" width="450"/>

---

<div align="center">
<table><tr><td>

[![Command](https://placehold.co/150x35/0d1117/e63946?text=COMMAND+DASHBOARD&font=Oswald)](#)
[![Automator](https://placehold.co/150x35/0d1117/e63946?text=FIR+AUTOMATOR&font=Oswald)](#)
[![LexBot](https://placehold.co/150x35/0d1117/e63946?text=LEXBOT+AI&font=Oswald)](#)
[![Vault](https://placehold.co/150x35/0d1117/e63946?text=EVIDENCE+VAULT&font=Oswald)](#)
[![Linkage](https://placehold.co/150x35/0d1117/e63946?text=CASE+LINKAGE&font=Oswald)](#)
[![Documents](https://placehold.co/150x35/0d1117/e63946?text=DOCUMENTS&font=Oswald)](#)
[![LERS](https://placehold.co/150x35/0d1117/e63946?text=LERS+PORTAL&font=Oswald)](#)

</td></tr></table>
</div>

### Command Dashboard
Role-aware operational overview. IOs see their own FIRs and case diary summaries. SHOs and Admins get station-wide metrics, pending approvals, recent FIR activity across all officers, audit logs, and crime trend analytics.

### FIR Automator
Paste or speak an incident narrative. The AI fills in structured fields — complainant details, accused info, incident location, applicable BNS/IT sections — and generates a formatted FIR. Save it and it immediately appears in the dashboard. Full lifecycle: draft → submit (to SHO) → approve/reject.

### LexBot
Type any legal question in plain English (or Hindi/Gujarati). LexBot queries the BNS 2023 and IT Act 2000 corpora via hybrid BM25 + ChromaDB vector search, then generates section-accurate, cited answers. Safety controls strip prompt injection attempts.

### Evidence Vault
Upload digital evidence files linked to specific FIRs. Each file is SHA-256 hashed on upload. Every access is logged in an immutable chain-of-custody. View uploaded images in a gallery, verify integrity, and track custody history.

### Case Linkage
AI-powered pattern detection across the FIR database. The system identifies semantically similar cases using vector embeddings, scores them, and presents potential links. Inspector+ officers can formally link cases and view MO clusters.

### Document Generator
AI auto-generates 7 types of legal documents — Chargesheet, Medical Letter, Remand Request, Seizure Receipt, Court Custody Letter, Accused Panchanama, and Face ID Form — populated from FIR data. Supports PDF export with version history snapshots.

### Case Diary
Timeline-based digital investigation diary. Officers log each investigative action (complaint, spot visit, witness exam, arrest, etc.) in chronological order, building a complete case history from FIR to chargesheet.

### LERS Cyber Portal
Generate Law Enforcement Request System (LERS) compliant legal notices for Meta, WhatsApp, Instagram, Telegram, and X. Supports Emergency Disclosure, Account Preservation, and Subscriber & IP Log requests under Section 94 BNSS / Section 91 CrPC.

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-configuration"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=CONFIGURATION" width="450"/>

---

### Backend (`backend/.env`)

```env
# Application
APP_NAME=CrimeGPT
APP_VERSION=0.1.0
DEBUG=true
API_PREFIX=/api/v1

# PostgreSQL (Docker: host port 5433 → container 5432)
DATABASE_URL=postgresql+asyncpg://crimegpt:crimegpt_pass@localhost:5433/crimegpt_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Auth
JWT_SECRET=change-me-to-a-real-secret-in-production
JWT_EXPIRY_HOURS=8
REFRESH_TOKEN_EXPIRY_DAYS=7

# LLM Provider
GROQ_API_KEY=your_groq_api_key_here

# Multi-model routing — each task uses the optimal model
GROQ_MODEL_PRIMARY=meta-llama/llama-4-scout-17b-16e-instruct  # FIR drafting, legal Q&A
GROQ_MODEL_FAST=llama-3.1-8b-instant                          # NER, classification
GROQ_MODEL_FALLBACK=llama-3.3-70b-versatile                   # Complex legal reasoning
GROQ_MODEL_WHISPER=whisper-large-v3-turbo                      # Speech-to-text

# Ollama (local fallback, used when LLM_MODE=local)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mistral:7b-instruct

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001

# RAG Ingestion
RAG_ALLOWED_DOMAINS=[]
RAG_STRIP_PROMPT_INJECTION=true
RAG_REDACT_PII=false

# Sentry (optional)
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_ENVIRONMENT=development

# Evidence Storage
EVIDENCE_STORAGE_PATH=./storage/evidence
EVIDENCE_MAX_FILE_SIZE_MB=50
```

> [!IMPORTANT]
> Never commit your `.env` file. It is already listed in `.gitignore`.

> [!TIP]
> Get a free Groq API key at [console.groq.com](https://console.groq.com). The free tier supports up to 14,400 requests/day.

### Frontend (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Docker Compose (`docker-compose.yml`)

| Service | Image | Host Port | Container Port | Purpose |
|---|---|---|---|---|
| `db` | postgres:15-alpine | **5433** | 5432 | Main database |
| `redis` | redis:7-alpine | 6379 | 6379 | Session cache |
| `chromadb` | chromadb/chroma:latest | 8001 | 8000 | Vector store |

### RAG Legal Corpus

Place legal text files in `backend/corpus/`:

```
corpus/
├── bns_2023/          # Bharatiya Nyaya Sanhita 2023 (replaces IPC)
├── it_act_2000/       # Information Technology Act 2000
└── pocso/             # POCSO Act
```

Ingest via admin API:
```bash
curl -X POST http://localhost:8000/api/v1/legal/corpus/ingest \
  -H "Authorization: Bearer <admin_jwt>" \
  -H "Content-Type: application/json"
```

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-contributing"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=CONTRIBUTING" width="450"/>

---

Contributions are welcome! Here's how to get involved:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/your-feature`
3. **Commit** your changes: `git commit -m "feat: add your feature"`
4. **Push** to your branch: `git push origin feat/your-feature`
5. **Open** a Pull Request

> [!NOTE]
> Please keep PRs focused — one feature or fix per PR makes review much easier.

### Development Setup

```bash
# Backend dev (with hot reload)
cd backend && source venv/bin/activate
uvicorn app.server:app --host 127.0.0.1 --port 8000 --reload

# Frontend dev (with HMR)
cd frontend && npm run dev -- --host
```

### Code Guidelines

- **Backend**: Clean architecture — routes → controllers → services → repositories. Routes contain zero business logic.
- **Frontend**: Components in `/components`, API calls in `/services/api.js`, state in `/store/`.
- **Models**: Async SQLAlchemy 2.0 with `async def` and `await` throughout.
- **Config**: All settings loaded from environment via Pydantic `BaseSettings`. Never use `os.environ` directly.
- **Audit**: All critical actions logged to the immutable `audit_logs` table.

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=STAR+HISTORY" width="450"/>

[![Stargazers over time](https://starchart.cc/XploitMonk0x01/crimegpt.svg?background=%230d1117&axis=%23e63946&line=%23e63946)](https://starchart.cc/XploitMonk0x01/crimegpt)

---

<div align="center">
  <sub>Built with ❤️ for the Kanad S.H.I.E.L.D. Hackathon 2026</sub>
  <br/>
  <sub>Last updated: July 2026</sub>
  <br/>
  <sub>Empowering Indian Law Enforcement with AI, RAG & BNS 2023</sub>
</div>