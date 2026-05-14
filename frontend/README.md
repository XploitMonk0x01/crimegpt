# CrimeGPT Frontend

This is the frontend for CrimeGPT, built with React and Vite.

## Setup Instructions

### 1. Installation
Before running the application, make sure to install all the necessary dependencies. Navigate to the frontend directory and run:
```bash
npm install
```

### 2. Running the Frontend Development Server
To start the React frontend and make it accessible across your local network, run:
```bash
npm run dev -- --host
```
The application will be available at `http://localhost:5173/` and on your network IP (e.g., `http://192.168.x.x:5173/`).

---

## Important: Running the Backend
The frontend requires the Python backend to be running to function properly (otherwise you will encounter an `ECONNREFUSED` error when trying to log in).

To start the backend server:
1. Open a **new terminal window** and navigate to the backend directory:
   ```bash
   cd ../backend
   ```
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Start the FastAPI server:
   ```bash
   uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
   ```
