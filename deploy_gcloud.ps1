# PowerShell script for Windows users
# ============================================================================
# PSX Research Analyst - Google Cloud Deployment Script (Windows)
# ============================================================================

param(
    [string]$ProjectId = "your-project-id",
    [string]$Region = "asia-south1"
)

$ErrorActionPreference = "Stop"

$ServiceName = "psx-research-analyst"
$ImageName = "gcr.io/$ProjectId/$ServiceName"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "PSX Research Analyst - Cloud Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Project: $ProjectId"
Write-Host "Region: $Region"
Write-Host "Service: $ServiceName"
Write-Host ""

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI is not installed" -ForegroundColor Red
    Write-Host "Please install from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Authenticate
Write-Host "[1/7] Authenticating with Google Cloud..." -ForegroundColor Yellow
gcloud auth login
gcloud config set project $ProjectId

# Enable APIs
Write-Host "[2/7] Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com run.googleapis.com cloudscheduler.googleapis.com secretmanager.googleapis.com

# Get email credentials
Write-Host "[3/7] Setting up secrets..." -ForegroundColor Yellow
$EmailSender = Read-Host "Email sender address"
$EmailPassword = Read-Host "Email password (App Password)" -AsSecureString
$EmailRecipients = Read-Host "Email recipients (comma-separated)"

# Convert secure string
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($EmailPassword)
$PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Create secrets
$EmailSender | gcloud secrets create email-sender --data-file=- 2>$null
if (-not $?) { $EmailSender | gcloud secrets versions add email-sender --data-file=- }

$PlainPassword | gcloud secrets create email-password --data-file=- 2>$null
if (-not $?) { $PlainPassword | gcloud secrets versions add email-password --data-file=- }

$EmailRecipients | gcloud secrets create email-recipients --data-file=- 2>$null
if (-not $?) { $EmailRecipients | gcloud secrets versions add email-recipients --data-file=- }

# Build image
Write-Host "[4/7] Building Docker image..." -ForegroundColor Yellow
gcloud builds submit --tag "${ImageName}:latest" .

# Deploy jobs
Write-Host "[5/7] Deploying Cloud Run Jobs..." -ForegroundColor Yellow

# Pre-Market Job
gcloud run jobs create psx-premarket `
    --image "${ImageName}:latest" `
    --region $Region `
    --memory 2Gi `
    --cpu 2 `
    --task-timeout 3600 `
    --set-secrets="EMAIL_SENDER=email-sender:latest,EMAIL_PASSWORD=email-password:latest,EMAIL_RECIPIENTS=email-recipients:latest" `
    --command="python" `
    --args="scheduler/orchestrator.py,--run,pre_market"

# Post-Market Job
gcloud run jobs create psx-postmarket `
    --image "${ImageName}:latest" `
    --region $Region `
    --memory 2Gi `
    --cpu 2 `
    --task-timeout 3600 `
    --set-secrets="EMAIL_SENDER=email-sender:latest,EMAIL_PASSWORD=email-password:latest,EMAIL_RECIPIENTS=email-recipients:latest" `
    --command="python" `
    --args="scheduler/orchestrator.py,--run,post_market"

# Setup scheduler
Write-Host "[6/7] Setting up Cloud Scheduler..." -ForegroundColor Yellow

# Create service account
gcloud iam service-accounts create psx-scheduler --display-name="PSX Scheduler" 2>$null

# Grant permissions
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:psx-scheduler@$ProjectId.iam.gserviceaccount.com" `
    --role="roles/run.invoker"

# Pre-Market Schedule (8:30 AM PKT, Mon-Fri)
gcloud scheduler jobs create http psx-premarket-schedule `
    --location=$Region `
    --schedule="30 8 * * 1-5" `
    --time-zone="Asia/Karachi" `
    --uri="https://$Region-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$ProjectId/jobs/psx-premarket:run" `
    --http-method=POST `
    --oauth-service-account-email="psx-scheduler@$ProjectId.iam.gserviceaccount.com"

# Post-Market Schedule (4:30 PM PKT, Mon-Fri)
gcloud scheduler jobs create http psx-postmarket-schedule `
    --location=$Region `
    --schedule="30 16 * * 1-5" `
    --time-zone="Asia/Karachi" `
    --uri="https://$Region-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$ProjectId/jobs/psx-postmarket:run" `
    --http-method=POST `
    --oauth-service-account-email="psx-scheduler@$ProjectId.iam.gserviceaccount.com"

Write-Host "[7/7] Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT SUCCESSFUL" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Scheduled Jobs:" -ForegroundColor White
Write-Host "  Pre-Market Analysis:  8:30 AM PKT (Mon-Fri)" -ForegroundColor Green
Write-Host "  Post-Market Analysis: 4:30 PM PKT (Mon-Fri)" -ForegroundColor Green
Write-Host ""
Write-Host "To run manually:" -ForegroundColor Yellow
Write-Host "  gcloud run jobs execute psx-premarket --region=$Region"
Write-Host "  gcloud run jobs execute psx-postmarket --region=$Region"
