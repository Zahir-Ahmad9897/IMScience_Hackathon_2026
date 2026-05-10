#!/bin/bash
# ============================================================
# deploy_gcp.sh — KisanAI GCP Cloud Run Deployment
# Run: bash deploy_gcp.sh
# ============================================================

set -e

# ── CONFIG — change these ────────────────────────────────────
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="kisanai"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# ── Load secrets from .env ───────────────────────────────────
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "=== KisanAI GCP Cloud Run Deployment ==="
echo "Project : $PROJECT_ID"
echo "Region  : $REGION"
echo "Service : $SERVICE_NAME"
echo ""

# ── Step 1: Set active GCP project ───────────────────────────
echo "[1/5] Setting GCP project..."
gcloud config set project $PROJECT_ID

# ── Step 2: Enable required APIs ─────────────────────────────
echo "[2/5] Enabling APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    --quiet

# ── Step 3: Build & push Docker image ────────────────────────
echo "[3/5] Building and pushing Docker image..."
gcloud builds submit \
    --tag $IMAGE:latest \
    --timeout=600 \
    .

# ── Step 4: Deploy to Cloud Run ──────────────────────────────
echo "[4/5] Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=3 \
    --timeout=300 \
    --port=8080 \
    --set-env-vars="\
OPENAI_API_KEY=$OPENAI_API_KEY,\
GROQ_API_KEY=$GROQ_API_KEY,\
OPENWEATHER_API_KEY=$OPENWEATHER_API_KEY,\
LANGCHAIN_API_KEY=$LANGCHAIN_API_KEY,\
LANGCHAIN_TRACING_V2=true,\
LANGCHAIN_PROJECT=KisanAI-MultiAgent,\
ALERT_EMAIL_SENDER=$ALERT_EMAIL_SENDER,\
ALERT_EMAIL_PASSWORD=$ALERT_EMAIL_PASSWORD,\
ALERT_EMAIL_RECEIVER=$ALERT_EMAIL_RECEIVER"

# ── Step 5: Get the live URL ──────────────────────────────────
echo "[5/5] Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format='value(status.url)')

echo ""
echo "========================================"
echo "  KisanAI DEPLOYED SUCCESSFULLY!"
echo "  Live URL: $SERVICE_URL"
echo "========================================"
