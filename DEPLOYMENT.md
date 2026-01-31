# PSX Research Analyst - Google Cloud Deployment Guide

## 📋 Prerequisites

Before deploying, ensure you have:

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed ([Download here](https://cloud.google.com/sdk/docs/install))
3. **Gmail App Password** for sending emails ([Create App Password](https://myaccount.google.com/apppasswords))

---

## 🚀 Quick Deployment (5 minutes)

### For Windows Users:
```powershell
# Open PowerShell as Administrator
cd "d:\a my work\psx_research_analyst"

# Run deployment script
.\deploy_gcloud.ps1 -ProjectId "your-gcp-project-id"
```

### For Linux/Mac Users:
```bash
cd /path/to/psx_research_analyst

# Make script executable
chmod +x deploy_gcloud.sh

# Run deployment
./deploy_gcloud.sh
```

---

## 📅 Automated Schedule

Once deployed, reports will be automatically sent:

| Report Type | Time (PKT) | Days |
|-------------|------------|------|
| 📈 Pre-Market Analysis | 8:30 AM | Mon-Fri |
| 📊 Post-Market Analysis | 4:30 PM | Mon-Fri |

---

## 🔧 Manual Deployment Steps

If the script doesn't work, follow these steps manually:

### Step 1: Authenticate
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Step 2: Enable APIs
```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com cloudscheduler.googleapis.com secretmanager.googleapis.com
```

### Step 3: Create Secrets
```bash
echo "your-email@gmail.com" | gcloud secrets create email-sender --data-file=-
echo "your-app-password" | gcloud secrets create email-password --data-file=-
echo "recipient1@email.com,recipient2@email.com" | gcloud secrets create email-recipients --data-file=-
```

### Step 4: Build and Deploy
```bash
# Build Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/psx-research-analyst:latest .

# Create Post-Market Job
gcloud run jobs create psx-postmarket \
    --image gcr.io/YOUR_PROJECT_ID/psx-research-analyst:latest \
    --region asia-south1 \
    --memory 2Gi \
    --cpu 2 \
    --task-timeout 3600 \
    --set-secrets="EMAIL_SENDER=email-sender:latest,EMAIL_PASSWORD=email-password:latest,EMAIL_RECIPIENTS=email-recipients:latest" \
    --command="python" \
    --args="scheduler/orchestrator.py,--run,post_market"
```

### Step 5: Create Scheduler
```bash
# Create service account
gcloud iam service-accounts create psx-scheduler

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:psx-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

# Schedule post-market at 4:30 PM PKT
gcloud scheduler jobs create http psx-postmarket-schedule \
    --location=asia-south1 \
    --schedule="30 16 * * 1-5" \
    --time-zone="Asia/Karachi" \
    --uri="https://asia-south1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/YOUR_PROJECT_ID/jobs/psx-postmarket:run" \
    --http-method=POST \
    --oauth-service-account-email="psx-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

---

## 💰 Cost Estimate

| Resource | Monthly Cost (Est.) |
|----------|---------------------|
| Cloud Run Jobs (2 runs/day) | ~$5-10 |
| Cloud Scheduler | Free (up to 3 jobs) |
| Secret Manager | ~$0.06 |
| Cloud Build | Free tier covers this |
| **Total** | **~$5-15/month** |

---

## 🔍 Monitoring & Logs

### View Logs
```bash
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=psx-postmarket" --limit=50
```

### Check Job Status
```bash
gcloud run jobs executions list --job=psx-postmarket --region=asia-south1
```

### Run Job Manually
```bash
gcloud run jobs execute psx-postmarket --region=asia-south1
```

---

## 🛠️ Troubleshooting

### Common Issues:

1. **Email not sending**: Check Gmail App Password is correct
2. **Job timeout**: Increase `--task-timeout` value
3. **Memory issues**: Increase `--memory` to 4Gi
4. **Permission denied**: Ensure service account has proper IAM roles

### Update Deployment
```bash
# Rebuild and redeploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/psx-research-analyst:latest .
gcloud run jobs update psx-postmarket --image gcr.io/YOUR_PROJECT_ID/psx-research-analyst:latest --region=asia-south1
```

---

## 📧 Email Configuration

The system sends professional HTML reports to your configured recipients. To update recipients:

```bash
echo "new-recipient@email.com" | gcloud secrets versions add email-recipients --data-file=-
```

---

## 🔐 Security Notes

- Email credentials are stored in Google Secret Manager (encrypted)
- Service account has minimal required permissions
- No sensitive data is logged
