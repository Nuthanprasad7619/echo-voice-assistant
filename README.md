# Echo Voice Assistant - Deployment Guide

This guide explains how to deploy this project using Vercel (Frontend) and Render (Backend).

## 1. Backend Deployment (Render)

1.  Create a new Web Service on [Render](https://render.com/).
2.  Connect your GitHub repository.
3.  Set the following configuration:
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn backend.app:app`
4.  Add an Environment Variable (optional):
    *   `PORT`: `10000` (Render's default)

## 2. Frontend Deployment (Vercel)

1.  Create a new Project on [Vercel](https://vercel.com/).
2.  Connect your GitHub repository.
3.  Set the following configuration:
    *   **Root Directory**: `frontend`
    *   **Framework Preset**: `Other` (Static)
    *   **Output Directory**: `.`
4.  Deploy.

### Important Note on API URL
Once your Render backend is live, you must update the `API_BASE_URL` in `frontend/script.js` with your actual Render service URL (e.g., `https://your-app-name.onrender.com`).

---

## Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Run locally: `python backend/app.py`
3. Access in browser: `http://localhost:5000`
