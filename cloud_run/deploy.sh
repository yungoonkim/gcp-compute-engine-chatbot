#!/usr/bin/env bash
set -e

SERVICE_NAME="gemini-chatbot"
REGION="${REGION:-asia-northeast3}"
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)

echo "============================================================"
echo "🚀 Deploying Gemini Chatbot to Google Cloud Run"
echo "============================================================"
echo "Service Name : ${SERVICE_NAME}"
echo "Region       : ${REGION}"
echo "Project ID   : ${PROJECT_ID:-'(Current Active Project)'}"
echo "============================================================"

# Check if GEMINI_API_KEY secret exists
echo "[1/3] Checking Secret Manager for GEMINI_API_KEY..."
if gcloud secrets describe GEMINI_API_KEY &>/dev/null; then
    echo "✔ Found GEMINI_API_KEY in Secret Manager."
    SECRET_OPT="--set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest"
else
    echo "⚠ GEMINI_API_KEY secret not found in Secret Manager."
    echo "  You can bind it later in Google Cloud Console or create it via:"
    echo "  echo 'your_api_key' | gcloud secrets create GEMINI_API_KEY --data-file=-"
    SECRET_OPT=""
fi

# Deploy to Cloud Run
echo "[2/3] Building container & deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --source . \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 3 \
    --memory 512Mi \
    --cpu 1 \
    ${SECRET_OPT}

echo "============================================================"
echo "✔ Deployment completed successfully!"
echo "Service URL:"
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)'
echo "============================================================"
