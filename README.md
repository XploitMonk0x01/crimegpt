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
<a href="#-modules"><kbd> <br> Modules <br> </kbd></a>&ensp;&ensp;
<a href="#-configuration"><kbd> <br> Configuration <br> </kbd></a>&ensp;&ensp;
<a href="#-contributing"><kbd> <br> Contributing <br> </kbd></a>

</div>

<br/>

---

<a id="-overview"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=OVERVIEW" width="450"/>

---
 
 **CrimeGPT** is a next-generation AI-powered platform engineered for modern Law Enforcement. It transforms the traditional, paper-heavy crime documentation process into a streamlined, digital-first workflow driven by Retrieval-Augmented Generation (RAG) and high-performance LLMs.
 
 > **Current State:** The platform is optimized for the **BNS 2023** (Bharatiya Nyaya Sanhita) legal framework, providing real-time intelligence and automated drafting for Indian Police Officers.
 
 ### 🚀 Core Value Proposition
 
 | Feature | Traditional Method | CrimeGPT Advantage |
 |---|---|---|
 | **FIR Generation** | 2-3 hours manual drafting | **< 30 seconds** AI-structured drafts |
 | **Legal Research** | Manual book lookups | **Instant** BNS 2023 RAG Intelligence |
 | **Evidence** | Physical logbooks | **Immutable** digital chain-of-custody |
 | **Intelligence** | Manual link detection | **AI-driven** MO pattern recognition |
 
 <div align="right">
   <br>
   <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
 </div>

---

<a id="-quick-start"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=QUICK+START" width="450"/>

---

### 🚀 Quick Start (Automated Setup)

The easiest way to get started is using the custom utility scripts. This handles all dependencies, environment setups, database schemas, and service coordination.

#### 1. Setup & Installation
Run the installer to configure your environment, download dependencies, and spin up databases:
```bash
./install.sh
```

#### 2. Run & Start
Launch all full-stack backend, frontend, and database services simultaneously:
```bash
./start.sh
```

---

### 🛠️ Manual Setup

If you prefer to run steps manually:

### 1. Clone the Repository

```bash
git clone https://github.com/XploitMonk0x01/crimegpt.git
cd crimegpt
```

### 2. Start Infrastructure (PostgreSQL + Redis)

```bash
docker-compose up -d
```

### 3. Backend Setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# Initialize database schema
python init_db.py

# Start API server
uvicorn app.server:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev -- --host
```

> [!TIP]
> The app will be available at `http://localhost:5173` (local) or your network IP for cross-device access.

### 💡 Troubleshooting
* **Python 3.13 Errors**: If you face `asyncpg` build errors, ensure you are using the latest `requirements.txt` which includes `asyncpg>=0.30.0`.
* **Resource Spikes**: We have removed `spacy` and `fastembed` to keep the installation lightweight and avoid high CPU/RAM usage during setup.

### Demo Credentials

| Field | Value |
|---|---|
| Badge Number | `PN-2024-ADMIN` |
| Security PIN | `1234` |

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-features"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=FEATURES" width="450"/>

---

### 🧠 LexBot — Legal Intelligence Agent
- Real-time Q&A powered by **Groq LLM** (Llama 3)
- Trained on **BNS 2023** (Bharatiya Nyaya Sanhita)
- Markdown-formatted responses with **bold**, *italic* and → pointer rendering
- RAG pipeline with ChromaDB for relevant legal section retrieval

### 📋 FIR Automator
- Natural language incident input → structured FIR draft
- **Sequential FIR numbering**: `FIR-00001`, `FIR-00002`, ...
- Persistent local storage — works even if backend is offline
- Click any FIR to view full details (complainant, location, narrative)
- Inline delete with confirmation
- Country-aware phone input with flag selector

### 📊 Command Dashboard
- Live stats: Total FIRs, Submitted, Approved, Rejected, **Drafts** (updates in real-time)
- Recent FIR activity feed with status badges

### 🗄️ Evidence Vault
- Secure digital evidence storage and retrieval

### 🔗 Case Linkage
- AI-powered pattern detection across multiple FIRs

### ⚙️ User Settings
- Slide-over settings panel with profile editing
- Notification, dark mode, and auto-save toggles
- Session and role information

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
├── frontend/                  # React + Vite SPA
│   ├── src/
│   │   ├── components/        # UI Components
│   │   │   ├── Dashboard.jsx  # Live stats + recent FIRs
│   │   │   ├── FIRAutomator.jsx # FIR drafting + management
│   │   │   ├── LexBot.jsx     # AI legal assistant
│   │   │   ├── Vault.jsx      # Evidence management
│   │   │   ├── CaseLinkage.jsx# Pattern analysis
│   │   │   ├── Sidebar.jsx    # Navigation + settings trigger
│   │   │   └── UserSettings.jsx # Settings slide-over panel
│   │   ├── services/
│   │   │   └── api.js         # Axios service layer
│   │   └── store/
│   │       ├── authStore.js   # Zustand auth state
│   │       └── firStore.js    # Zustand FIR state + localStorage
│   └── package.json
│
├── backend/                   # FastAPI Python API
│   ├── app/
│   │   ├── routes/            # API route handlers
│   │   ├── services/          # Business logic (RAG, LLM, FIR)
│   │   ├── schemas/           # Pydantic models
│   │   └── main.py            # App factory
│   ├── init_db.py             # Database initializer
│   └── .env                   # Environment config
│
├── install.sh                 # 🚀 Automated setup & dependency installer
├── start.sh                   # 🟢 Application runtime launcher
└── docker-compose.yml         # PostgreSQL + Redis
```

**Stack:**

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, Tailwind CSS 4, Framer Motion |
| State | Zustand + localStorage |
| Backend | FastAPI, Python 3.11+ (Supports 3.13) |
| AI/LLM | Groq API (Llama 3.3 70B) |
| RAG | ChromaDB (Lexical Fallback) |
| Database | PostgreSQL (Docker) |
| Cache | Redis (Docker) |
| Auth | JWT + demo bypass mode |

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

</td></tr></table>
</div>

### Command Dashboard
Real-time operational overview with FIR statistics. Draft count updates the moment a new FIR is saved anywhere in the app.

### FIR Automator
Paste or speak an incident narrative. The AI fills in structured fields — complainant details, location, applicable BNS sections. Save it as `FIR-00001` and it immediately appears in the list below.

### LexBot
Type any legal question in plain English. LexBot queries the BNS 2023 corpus via RAG and returns formatted, section-accurate answers in real time.

### Evidence Vault
Upload and manage digital evidence files tied to specific FIRs.

### Case Linkage
Identify related incidents across multiple FIRs using AI pattern analysis.

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-configuration"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=CONFIGURATION" width="450"/>

---

### `backend/.env`

```env
# Database
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=crimegpt_db
DB_USER=crimegpt
DB_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379

# AI
GROQ_API_KEY=your_groq_api_key_here

# Multi-model routing
# FIR drafting & legal Q&A (primary)
GROQ_MODEL_PRIMARY=llama-3.3-70b-versatile
# NER, classification (fast)
GROQ_MODEL_FAST=llama-3.1-8b-instant
# Complex legal reasoning (fallback)
GROQ_MODEL_FALLBACK=qwen/qwen3.6-27b
# Speech-to-text
GROQ_MODEL_WHISPER=whisper-large-v3-turbo
```

> [!IMPORTANT]
> Never commit your `.env` file. It is already listed in `.gitignore`.

> [!TIP]
> Get a free Groq API key at [console.groq.com](https://console.groq.com). The free tier supports up to 14,400 requests/day.

### `frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
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
  <sub>Last updated: May 2026</sub>
</div>
