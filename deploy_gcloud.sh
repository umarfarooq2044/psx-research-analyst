#!/bin/bash
# ============================================================================
# PSX Research Analyst - Google Cloud Deployment Script
# ============================================================================
# This script deploys the PSX Research Analyst to Google Cloud Run
# and sets up Cloud Scheduler for automated daily reports
# ============================================================================

set -e  # Exit on error

# Configuration - UPDATE THESE VALUES
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="asia-south1"  # Closest to Pakistan
SERVICE_NAME="psx-research-analyst"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "============================================"
echo "PSX Research Analyst - Cloud Deployment"
echo "============================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Please install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Authenticate and set project
echo "[1/7] Authenticating with Google Cloud..."
gcloud auth login --quiet
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "[2/7] Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com

# Create secrets for email configuration
echo "[3/7] Setting up secrets..."
echo "Please enter your email credentials:"

read -p "Email sender address: " EMAIL_SENDER
read -sp "Email password (App Password): " EMAIL_PASSWORD
echo ""
read -p "Email recipients (comma-separated): " EMAIL_RECIPIENTS

# Create secrets in Secret Manager
echo "${EMAIL_SENDER}" | gcloud secrets create email-sender --data-file=- 2>/dev/null || \
    echo "${EMAIL_SENDER}" | gcloud secrets versions add email-sender --data-file=-

echo "${EMAIL_PASSWORD}" | gcloud secrets create email-password --data-file=- 2>/dev/null || \
    echo "${EMAIL_PASSWORD}" | gcloud secrets versions add email-password --data-file=-

echo "${EMAIL_RECIPIENTS}" | gcloud secrets create email-recipients --data-file=- 2>/dev/null || \
    echo "${EMAIL_RECIPIENTS}" | gcloud secrets versions add email-recipients --data-file=-

# Build Docker image
echo "[4/7] Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}:latest .

# Deploy to Cloud Run - Pre-Market Job
echo "[5/7] Deploying Cloud Run Jobs..."

# Pre-Market Analysis Job (8:30 AM PKT)
gcloud run jobs create psx-premarket \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --memory 2Gi \
    --cpu 2 \
    --task-timeout 3600 \
    --set-secrets="EMAIL_SENDER=email-sender:latest,EMAIL_PASSWORD=email-password:latest,EMAIL_RECIPIENTS=email-recipients:latest" \
    --command="python" \
    --args="scheduler/orchestrator.py,--run,pre_market" \
    2>/dev/null || \
gcloud run jobs update psx-premarket \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --memory 2Gi \
    --cpu 2 \
    --task-timeout 3600 \
    --set-secrets="EMAIL_SENDER=email-sender:latest,EMAIL_PASSWORD=email-password:latest,EMAIL_RECIPIENTS=email-recipients:latest" \
    --command="python" \
    --args="scheduler/orchestrator.py,--run,pre_market"

# Post-Market Analysis Job (4:30 PM PKT)
gcloud run jobs create psx-postmarket \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --memory 2Gi \
    --cpu 2 \
    --task-timeout 3600 \
    --set-secrets="EMAIL_SENDER=email-sender:latest,EMAIL_PASSWORD=email-password:latest,EMAIL_RECIPIENTS=email-recipients:latest" \
    --command="python" \
    --args="scheduler/orchestrator.py,--run,post_market" \
    2>/dev/null || \
gcloud run jobs update psx-postmarket \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --memory 2Gi \
    --cpu 2 \
    --task-timeout 3600 \
    --set-secrets="EMAIL_SENDER=email-sender:latest,EMAIL_PASSWORD=email-password:latest,EMAIL_RECIPIENTS=email-recipients:latest" \
    --command="python" \
    --args="scheduler/orchestrator.py,--run,post_market"

# Set up Cloud Scheduler
echo "[6/7] Setting up Cloud Scheduler..."

# Create service account for scheduler
gcloud iam service-accounts create psx-scheduler \
    --display-name="PSX Scheduler Service Account" 2>/dev/null || true

# Grant permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:psx-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

# Pre-Market Schedule (8:30 AM PKT = 3:30 AM UTC)
gcloud scheduler jobs create http psx-premarket-schedule \
    --location=${REGION} \
    --schedule="30 3 * * 1-5" \
    --time-zone="Asia/Karachi" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/psx-premarket:run" \
    --http-method=POST \
    --oauth-service-account-email="psx-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" \
    2>/dev/null || \
gcloud scheduler jobs update http psx-premarket-schedule \
    --location=${REGION} \
    --schedule="30 8 * * 1-5" \
    --time-zone="Asia/Karachi"

# Post-Market Schedule (4:30 PM PKT = 11:30 AM UTC)
gcloud scheduler jobs create http psx-postmarket-schedule \
    --location=${REGION} \
    --schedule="30 16 * * 1-5" \
    --time-zone="Asia/Karachi" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/psx-postmarket:run" \
    --http-method=POST \
    --oauth-service-account-email="psx-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" \
    2>/dev/null || \
gcloud scheduler jobs update http psx-postmarket-schedule \
    --location=${REGION} \
    --schedule="30 16 * * 1-5" \
    --time-zone="Asia/Karachi"

echo "[7/7] Deployment complete!"
echo ""
echo "============================================"
echo "✅ DEPLOYMENT SUCCESSFUL"
echo "============================================"
echo ""
echo "Scheduled Jobs:"
echo "  📈 Pre-Market Analysis:  8:30 AM PKT (Mon-Fri)"
echo "  📊 Post-Market Analysis: 4:30 PM PKT (Mon-Fri)"
echo ""
echo "To run manually:"
echo "  gcloud run jobs execute psx-premarket --region=${REGION}"
echo "  gcloud run jobs execute psx-postmarket --region=${REGION}"
echo ""
echo "To view logs:"
echo "  gcloud logging read 'resource.type=cloud_run_job'"
echo ""
