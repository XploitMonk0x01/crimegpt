<p align="center">
  <img src="crimegpt-logo.png" alt="crimeGPT banner logo" width="50%">
</p>


# CrimeGPT - An Powered Automation for Crime Documentation and Legal Intelligence

This is the React + Vite frontend for the CrimeGPT platform, designed specifically for Indian Law Enforcement Agencies. It features a high-density "Micro-Editorial" UI built with Tailwind CSS 4.0 and Framer Motion.

## 🚀 Quick Start

### 1. Installation
Navigate to the frontend directory and install the necessary dependencies:

```bash
cd frontend
npm install
```

### 2. Development Server
Start the development server with network access enabled. This allows other devices on your Wi-Fi to access the dashboard.

```bash
npm run dev -- --host
```

By default, the application will be available at:
- **Local:** `http://localhost:5173`
- **Network:** `http://<your-ip-address>:5173`

### 3. Build for Production
To generate a production-ready bundle:

```bash
npm run build
```

## 🛠 Features

- **Dynamic IP Detection**: Automatically connects to the backend API whether you are on `localhost` or a network IP.
- **Micro-Editorial Design**: A sleek, high-density interface designed for long shifts without eye strain.
- **LexBot Interface**: A centralized AI command center that transitions from a splash screen to a persistent assistant.
- **Voice Integration**: Native support for WebRTC audio capture for incident transcription.

## 🔑 Authentication (Demo Mode)

For quick testing during the hackathon, you can use the following pre-configured admin credentials:

- **Badge Number:** `PN-2024-ADMIN`
- **Security PIN:** `1234`

## 📂 Structure

- `src/components`: Reusable UI components (Sidebar, LexBot, FIRAutomator).
- `src/services`: API integration layers with axios.
- `src/store`: Global state management using Zustand.
- `src/index.css`: Core design system and Tailwind 4.0 utilities.

---
*Built for the Kanad S.H.I.E.L.D. Hackathon 2026*
