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

**CrimeGPT** is a full-stack AI platform built for Indian Law Enforcement Agencies to streamline crime documentation, legal research, and case management. It replaces manual FIR drafting and legal lookups with an intelligent, AI-assisted workflow.

> Built at the **Kanad S.H.I.E.L.D. Hackathon 2026** — combining real-world law enforcement needs with cutting-edge AI.

### What makes it different?

| Traditional Process | CrimeGPT |
|---|---|
| Manual FIR writing (hours) | AI-drafted FIR in seconds |
| Physical law books | Real-time BNS 2023 query via LexBot |
| Paper-based case files | Centralized digital evidence vault |
| No pattern recognition | AI-powered case linkage |

<div align="right">
  <br>
  <a href="#-crimegpt-top"><kbd> <br> 🡅 <br> </kbd></a>
</div>

---

<a id="-quick-start"></a>
<img src="https://readme-typing-svg.herokuapp.com?font=Lexend+Giga&size=25&pause=1000&color=e63946&vCenter=true&width=435&height=25&lines=QUICK+START" width="450"/>

---

### Prerequisites

- **Node.js** `v18+` and **npm**
- **Python** `3.11+` and **pip**
- **Docker** & **Docker Compose**
- **Groq API Key** (free at [console.groq.com](https://console.groq.com))

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
# Edit .env with your GROQ_API_KEY, DB credentials

# Initialize database schema
python init_db.py

# Start API server
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev -- --host
```

> [!TIP]
> The app will be available at `http://localhost:5173` (local) or your network IP for cross-device access.

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
└── docker-compose.yml         # PostgreSQL + Redis
```

**Stack:**

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, Tailwind CSS 4, Framer Motion |
| State | Zustand + localStorage |
| Backend | FastAPI, Python 3.11 |
| AI/LLM | Groq API (Llama 3.3 70B) |
| RAG | ChromaDB + sentence-transformers |
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

# Auth
JWT_SECRET=your_jwt_secret
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
