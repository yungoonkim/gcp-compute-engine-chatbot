#!/usr/bin/env bash
set -e

SERVICE_NAME="gemini-chatbot-adc"
REGION="${REGION:-us-central1}"
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)' 2>/dev/null || true)

echo "============================================================"
echo "🚀 Deploying Gemini Chatbot (ADC Mode) to Google Cloud Run"
echo "============================================================"
echo "Service Name   : ${SERVICE_NAME}"
echo "Region         : ${REGION}"
echo "Project ID     : ${PROJECT_ID}"
echo "Project Number : ${PROJECT_NUMBER}"
echo "Auth Method    : ADC (Application Default Credentials)"
echo "============================================================"

# Ensure Service Account has Vertex AI User role for ADC
if [ -n "${PROJECT_NUMBER}" ]; then
    COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    echo "[1/3] Ensuring Compute Service Account has Vertex AI User role (roles/aiplatform.user)..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${COMPUTE_SA}" \
        --role="roles/aiplatform.user" \
        --condition=None --quiet >/dev/null || true
fi

# Ensure aiplatform.googleapis.com is enabled
echo "[2/3] Ensuring aiplatform.googleapis.com is enabled..."
gcloud services enable aiplatform.googleapis.com --project="${PROJECT_ID}" --quiet || true

# Deploy to Cloud Run (No API Key or Secret Manager mapping needed!)
echo "[3/3] Building container & deploying to Cloud Run via IAM/ADC..."
gcloud run deploy "${SERVICE_NAME}" \
    --source . \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 3 \
    --memory 512Mi \
    --cpu 1 \
    --set-env-vars VERTEX_AI_REGION="${REGION}",PROJECT_ID="${PROJECT_ID}"

echo "============================================================"
echo "✔ Deployment completed successfully with ADC authentication!"
echo "Service URL:"
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)'
echo "============================================================"
