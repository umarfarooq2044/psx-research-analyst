# PSX Research Analyst - FREE Automated Daily Reports

## 🎉 100% FREE Solution using GitHub Actions

This guide shows you how to set up **completely free** automated daily market reports.

---

## 📋 What You Get (FREE)

- ✅ **Pre-Market Report** at 8:30 AM PKT (Mon-Fri)
- ✅ **Post-Market Report** at 4:30 PM PKT (Mon-Fri)
- ✅ Automatic email delivery
- ✅ No credit card required
- ✅ 2,000 free minutes/month (more than enough!)

---

## 🚀 Setup Guide (10 minutes)

### Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in (or create free account)
2. Click **"New Repository"** (green button)
3. Name it: `psx-research-analyst`
4. Choose **Public** (free unlimited) or **Private** (2000 min/month free)
5. Click **Create Repository**

### Step 2: Upload Your Code

**Option A: Using GitHub Desktop (Easiest)**
1. Download [GitHub Desktop](https://desktop.github.com/)
2. Clone your new repository
3. Copy all files from `d:\a my work\psx_research_analyst` to the repo folder
4. Commit and Push

**Option B: Using Command Line**
```powershell
cd "d:\a my work\psx_research_analyst"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/psx-research-analyst.git
git push -u origin main
```

### Step 3: Add Email Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"** and add these 3 secrets:

| Secret Name | Value |
|-------------|-------|
| `EMAIL_SENDER` | Your Gmail address (e.g., `you@gmail.com`) |
| `EMAIL_PASSWORD` | Your Gmail App Password ([Create here](https://myaccount.google.com/apppasswords)) |
| `EMAIL_RECIPIENTS` | Comma-separated emails (e.g., `user1@email.com,user2@email.com`) |

### Step 4: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. Click **"I understand my workflows, go ahead and enable them"**
3. Done! ✅

---

## 🎯 Test It Now

To run a report immediately:

1. Go to **Actions** tab
2. Click **"PSX Daily Market Reports"** on the left
3. Click **"Run workflow"** dropdown (right side)
4. Select report type → Click **"Run workflow"**

---

## 📅 Automatic Schedule

Reports will run automatically:

| Report | Time (PKT) | Days |
|--------|------------|------|
| Pre-Market | 8:30 AM | Mon-Fri |
| Post-Market | 4:30 PM | Mon-Fri |

---

## 💡 Tips

- **Check Status**: Go to Actions tab to see if reports ran successfully
- **View Logs**: Click on any workflow run to see detailed logs
- **Download Reports**: Each run saves reports as downloadable artifacts

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| Email not sent | Check EMAIL_PASSWORD is a Gmail App Password (not regular password) |
| Workflow not running | Make sure Actions are enabled in repository |
| Timeout error | Free tier has 6-hour limit, our workflow uses ~45 min max |

---

## 💰 Cost: $0/month

GitHub Actions is **completely free** for:
- Public repositories: Unlimited
- Private repositories: 2,000 minutes/month (we use ~45 min/day = ~900 min/month)
