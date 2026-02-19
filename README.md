# Echo Voice Assistant

An advanced AI voice assistant built with Python (Flask) and Vanilla JS.

## 🚀 Live Demo
- **Frontend**: Deployed on [GitHub Pages](https://nuthanprasad7619.github.io/echo-voice-assistant/)
- **Backend**: Deployed on [Render](https://render.com/)

---

## Deployment Guide

### 1. Backend Deployment (Render)

1. Create a new Web Service on [Render](https://render.com/).
2. Connect your GitHub repository.
3. Set the following configuration:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn backend.app:app`
4. Copy your Render service URL (e.g., `https://your-app-name.onrender.com`).
5. Update `API_BASE_URL` in `frontend/script.js` with your Render URL.

### 2. Frontend Deployment (GitHub Pages)

The frontend is automatically deployed to GitHub Pages via a GitHub Actions workflow whenever you push to `main`.

To manually enable it:
1. Go to your repo on GitHub → **Settings** → **Pages**.
2. Set **Source** to the `gh-pages` branch.

---

## Local Development

1. Install dependencies: `pip install -r requirements.txt`
2. Run locally: `python backend/app.py`
3. Access in browser: `http://localhost:5000`
