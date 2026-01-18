# 🚀 Render Deployment Guide

Deploy your Fund Analytics Platform to **Render.com** - a modern cloud platform with a generous free tier.

---

## 📋 Prerequisites

1. **GitHub Account** (free) - https://github.com/signup
2. **Render Account** - https://render.com (sign up with GitHub)

---

## Step 1: Push Code to GitHub (5 minutes)

### Create a New GitHub Repository

1. Go to https://github.com/new
2. **Repository name**: `fund-analytics-platform`
3. Select **Public** or **Private**
4. Click **Create repository**

### Push the Code

After extracting the ZIP file, open a terminal in that folder:

```bash
cd fund-analytics-platform

# Initialize git repository
git init
git add .
git commit -m "Initial commit - Fund Analytics Platform"

# Connect to your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/fund-analytics-platform.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to Render (10 minutes)

### Option A: Blueprint Deployment (Recommended - One Click)

1. Go to https://render.com and sign in with GitHub
2. Click **New** → **Blueprint**
3. Connect your GitHub account if not already done
4. Select your `fund-analytics-platform` repository
5. Render will detect the `render.yaml` file automatically
6. Review the services:
   - `fund-analytics-api` (Backend)
   - `fund-analytics-frontend` (Frontend)
7. Click **Apply**
8. Wait for deployment (~5-10 minutes)

### Option B: Manual Deployment

If Blueprint doesn't work, deploy services manually:

#### Deploy Backend First

1. Go to Render Dashboard → **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `fund-analytics-api`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. Add Environment Variables:
   - `CORS_ORIGINS`: `https://fund-analytics-frontend.onrender.com`
5. Click **Create Web Service**
6. Wait for deployment and note the URL (e.g., `https://fund-analytics-api.onrender.com`)

#### Deploy Frontend

1. Go to Render Dashboard → **New** → **Static Site**
2. Connect the same GitHub repository
3. Configure:
   - **Name**: `fund-analytics-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. Add Environment Variable:
   - `VITE_API_URL`: `https://fund-analytics-api.onrender.com/api`
5. Click **Create Static Site**

---

## Step 3: Verify Deployment

### Check Backend Health

Visit: `https://fund-analytics-api.onrender.com/health`

You should see:
```json
{
  "status": "healthy",
  "data_loaded": true,
  "fund_metrics_loaded": true,
  "fund_details_loaded": true,
  "benchmarks_loaded": true
}
```

### Check API Documentation

Visit: `https://fund-analytics-api.onrender.com/docs`

This shows all available API endpoints with interactive testing.

### Access Frontend

Visit: `https://fund-analytics-frontend.onrender.com`

You should see the Fund Analytics Platform!

---

## Step 4: Update CORS (If Needed)

If you see CORS errors in the browser console:

1. Go to Render Dashboard → `fund-analytics-api` → Environment
2. Update `CORS_ORIGINS` to include your actual frontend URL:
   ```
   https://fund-analytics-frontend.onrender.com
   ```
3. Click **Save Changes** - service will automatically redeploy

---

## 📍 Your URLs

After deployment, your application will be available at:

| Service | URL |
|---------|-----|
| Frontend | `https://fund-analytics-frontend.onrender.com` |
| Backend API | `https://fund-analytics-api.onrender.com` |
| API Docs | `https://fund-analytics-api.onrender.com/docs` |
| Health Check | `https://fund-analytics-api.onrender.com/health` |

---

## ⚡ Free Tier Details

### Render Free Tier
- 750 hours/month of running time
- 512 MB RAM
- Automatic HTTPS
- Custom domain support
- Auto-deploy from Git

### Important: Sleep Mode
- Free tier services "sleep" after 15 minutes of inactivity
- First request after sleep takes ~30-60 seconds to wake up
- Subsequent requests are fast

### Keep Alive (Optional)

To prevent sleep, use a free monitoring service:

1. Go to https://uptimerobot.com (free account)
2. Add a new monitor:
   - **URL**: `https://fund-analytics-api.onrender.com/health`
   - **Interval**: 5 minutes
3. This keeps your backend awake

---

## 🔧 Troubleshooting

### Backend Won't Start

1. Check logs in Render Dashboard → Your Service → Logs
2. Common issues:
   - Missing dependencies: Check `requirements.txt`
   - Port issue: Ensure using `$PORT` environment variable

### Frontend Shows Blank Page

1. Check browser console (F12) for errors
2. Verify `VITE_API_URL` is set correctly
3. Check if API is accessible

### CORS Errors

1. Verify `CORS_ORIGINS` includes your frontend URL
2. Make sure there are no trailing slashes
3. Redeploy backend after changing environment variables

### "Failed to fetch" Errors

1. Backend might be sleeping - wait 30 seconds and refresh
2. Check backend health endpoint
3. Verify API URL in frontend environment

---

## 🔄 Updating Your Application

Simply push to GitHub:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

Render automatically redeploys on push!

---

## 🌐 Custom Domain (Optional)

### Add Custom Domain

1. Go to Render Dashboard → Your Service → Settings
2. Click **Add Custom Domain**
3. Follow DNS configuration instructions
4. Render provides free SSL certificates

---

## 📊 Using Your Real Data

The platform includes demo data (50 sample funds). To use your real data:

1. **Host your `.pkl` files** on GitHub Releases
2. **Add environment variables** in Render:
   ```
   GITHUB_REPO=your-username/your-data-repo
   GITHUB_TOKEN=ghp_your_token
   ```
3. Redeploy the backend

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Backend deployed on Render
- [ ] Backend health check returns "healthy"
- [ ] Frontend deployed on Render
- [ ] VITE_API_URL set correctly
- [ ] CORS_ORIGINS includes frontend URL
- [ ] Frontend loads and displays funds
- [ ] Navigation and filters work

---

## 🆘 Need Help?

- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **React Docs**: https://react.dev

---

## 💰 Cost Summary

| Service | Monthly Cost |
|---------|-------------|
| Render Backend | $0 (free tier) |
| Render Frontend | $0 (free tier) |
| GitHub Repository | $0 (free) |
| **Total** | **$0** |

Happy deploying! 🎉
