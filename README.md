# InvoiceAI Pro — Deployment Guide

This repository contains a Streamlit app (`vision.py`) for invoice extraction and comparison.

Quick options to launch as a website:

1) Streamlit Community Cloud (fastest)
- Push this repo to GitHub.
- Go to https://streamlit.io/cloud and create a new app pointing to this repo and the branch.
- Set the main file path to `vision.py`.
- In the Streamlit app settings, add a secret: `GOOGLE_API_KEY` with your Google API key.

2) Docker → Cloud Run / Render / Railway (production ready)
- Build locally:
```powershell
cd "d:\Invoice-Extractor-LLM-APP-main\Invoice-Extractor-LLM-APP-main"
docker build -t invoice-ai:latest .
docker run -p 8080:8080 -e GOOGLE_API_KEY="your_key_here" invoice-ai:latest
# open http://localhost:8080
```
- Push to Google Cloud Run (example):
```powershell
# build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT/invoice-ai
# deploy
gcloud run deploy invoice-ai --image gcr.io/YOUR_PROJECT/invoice-ai --platform managed --region us-central1 --allow-unauthenticated --set-env-vars GOOGLE_API_KEY="your_key_here"
```

3) GitHub Actions CI (automated build & publish to GHCR)
- A workflow is included (`.github/workflows/docker-build.yml`) to build and push a Docker image to GitHub Container Registry on push to `main`.
- After pushing to GitHub, add any necessary secrets (e.g., `GCP_SERVICE_ACCOUNT_JSON` for Cloud Run deployments).

Notes
- Do NOT commit your `.env` with keys. Use the hosting platform's secret manager (Streamlit Cloud secrets, GitHub Secrets, Cloud Run env vars).
- Make sure `requirements.txt` lists all dependencies (Streamlit, google-generativeai, python-dotenv, Pillow, etc.).

If you want, I can:
- Create a GitHub repo and push (you must provide the remote URL or create it and give me access details), or
- Create a Streamlit Cloud app for you (you will need to connect your GitHub), or
- Build and test the Docker image locally here if Docker is available.

Which option do you want me to do next?
