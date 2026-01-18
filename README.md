# Fund Analytics Platform - Setup & Deployment Guide

## 📁 Project Structure

```
fund-analytics-platform/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application entry
│   │   ├── config.py          # Configuration settings
│   │   ├── dependencies.py    # Dependency injection
│   │   ├── core/              # Business logic
│   │   │   ├── portfolio_metrics.py
│   │   │   └── data_loader.py
│   │   ├── models/            # Pydantic schemas
│   │   │   └── schemas.py
│   │   └── routers/           # API endpoints
│   │       ├── funds.py
│   │       ├── risk.py
│   │       ├── portfolio.py
│   │       └── benchmarks.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── main.jsx           # Entry point
│   │   ├── App.jsx            # Main App component
│   │   ├── api/               # API client
│   │   ├── components/        # Reusable components
│   │   ├── hooks/             # React Query hooks
│   │   ├── pages/             # Page components
│   │   ├── store/             # Zustand stores
│   │   ├── styles/            # CSS files
│   │   └── utils/             # Utility functions
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── .env.example
│
└── README.md
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn
- Supabase account (free tier)

### 1. Clone & Setup

```bash
# Create project directory
mkdir fund-analytics-platform
cd fund-analytics-platform

# Copy the backend and frontend folders here
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials:
# - SUPABASE_URL=your-supabase-url
# - SUPABASE_KEY=your-supabase-anon-key
# - GITHUB_TOKEN=your-github-token (for data loading)
# - GITHUB_REPO=your-repo (where .pkl files are hosted)
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# For local development, leave VITE_API_URL empty
# The Vite proxy will forward /api requests to the backend
```

### 4. Run Locally

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## ☁️ Production Deployment

### Option A: Vercel (Frontend) + Railway (Backend)

#### Deploy Frontend to Vercel

1. **Push to GitHub:**
```bash
cd frontend
git init
git add .
git commit -m "Initial frontend"
git remote add origin https://github.com/YOUR_USER/fund-analytics-frontend.git
git push -u origin main
```

2. **Deploy on Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repo
   - Configure:
     - Framework: Vite
     - Build Command: `npm run build`
     - Output Directory: `dist`
   - Add Environment Variable:
     - `VITE_API_URL` = `https://your-backend.railway.app/api`
   - Deploy

3. **Custom Domain (optional):**
   - Go to Project Settings → Domains
   - Add your domain

#### Deploy Backend to Railway

1. **Push to GitHub:**
```bash
cd backend
git init
git add .
git commit -m "Initial backend"
git remote add origin https://github.com/YOUR_USER/fund-analytics-backend.git
git push -u origin main
```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Choose "Deploy from GitHub repo"
   - Select your backend repo
   - Railway will auto-detect Dockerfile

3. **Configure Environment Variables:**
   - Go to your service → Variables
   - Add:
     ```
     SUPABASE_URL=your-supabase-url
     SUPABASE_KEY=your-supabase-anon-key
     GITHUB_TOKEN=your-github-token
     GITHUB_REPO=your-repo
     CORS_ORIGINS=https://your-frontend.vercel.app
     ```

4. **Generate Domain:**
   - Go to Settings → Domains
   - Generate a Railway domain or add custom

5. **Update Frontend:**
   - Go back to Vercel
   - Update `VITE_API_URL` with your Railway URL
   - Redeploy

### Option B: Render (Both)

#### Deploy Backend to Render

1. **Create New Web Service:**
   - Go to [render.com](https://render.com)
   - New → Web Service
   - Connect your GitHub repo
   - Configure:
     - Name: `fund-analytics-api`
     - Runtime: Docker
     - Instance Type: Free
   - Add Environment Variables (same as Railway)
   - Deploy

2. **Note the URL:** `https://fund-analytics-api.onrender.com`

#### Deploy Frontend to Render

1. **Create New Static Site:**
   - New → Static Site
   - Connect your frontend repo
   - Configure:
     - Name: `fund-analytics`
     - Build Command: `npm install && npm run build`
     - Publish Directory: `dist`
   - Add Environment Variable:
     - `VITE_API_URL` = `https://fund-analytics-api.onrender.com/api`
   - Deploy

---

## 🗄️ Database Setup (Supabase)

### Create Tables

Run these SQL commands in Supabase SQL Editor:

```sql
-- Risk Monitor Saved Configurations
CREATE TABLE IF NOT EXISTS risk_monitor_funds (
    id BIGSERIAL PRIMARY KEY,
    monitor_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    funds_list JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(monitor_name, user_id)
);

-- Saved Portfolios
CREATE TABLE IF NOT EXISTS portfolios (
    id BIGSERIAL PRIMARY KEY,
    portfolio_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    allocations JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(portfolio_name, user_id)
);

-- Enable Row Level Security (optional)
ALTER TABLE risk_monitor_funds ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust as needed)
CREATE POLICY "Users can read own monitors" ON risk_monitor_funds
    FOR SELECT USING (true);

CREATE POLICY "Users can insert own monitors" ON risk_monitor_funds
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own monitors" ON risk_monitor_funds
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete own monitors" ON risk_monitor_funds
    FOR DELETE USING (true);

-- Same for portfolios
CREATE POLICY "Users can read own portfolios" ON portfolios
    FOR SELECT USING (true);

CREATE POLICY "Users can insert own portfolios" ON portfolios
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own portfolios" ON portfolios
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete own portfolios" ON portfolios
    FOR DELETE USING (true);
```

---

## 📊 Data Files Setup

Your fund data files (`fund_metrics.pkl`, `fund_details.pkl`, `benchmarks.pkl`) should be hosted on GitHub Releases.

### Upload to GitHub Releases

1. **Create a private repo** for your data files
2. **Create a Release:**
   - Go to Releases → Draft a new release
   - Tag: `v1.0.0` (or date-based: `2024-01-15`)
   - Upload your `.pkl` files as assets
   - Publish release

3. **Generate Personal Access Token:**
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens
   - Generate a token with `repo` scope
   - Save this as `GITHUB_TOKEN`

4. **Configure Backend:**
   ```
   GITHUB_REPO=your-username/your-data-repo
   GITHUB_TOKEN=ghp_your_token_here
   ```

---

## 🔧 Configuration Reference

### Backend Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon/public key |
| `GITHUB_TOKEN` | Yes | GitHub PAT for data loading |
| `GITHUB_REPO` | Yes | Repo with data files (owner/repo) |
| `CORS_ORIGINS` | Yes | Allowed frontend origins (comma-separated) |
| `REDIS_URL` | No | Redis URL for caching (optional) |
| `DEBUG` | No | Enable debug mode (default: false) |

### Frontend Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes (prod) | Backend API URL (empty for dev proxy) |

---

## 🔄 Updating the Application

### Backend Updates

```bash
cd backend
git add .
git commit -m "Your changes"
git push origin main
# Railway/Render will auto-deploy
```

### Frontend Updates

```bash
cd frontend
npm run build  # Test build locally first
git add .
git commit -m "Your changes"
git push origin main
# Vercel/Render will auto-deploy
```

---

## 🐛 Troubleshooting

### CORS Errors
- Ensure `CORS_ORIGINS` includes your frontend URL
- Check for trailing slashes (should not have them)

### Data Not Loading
- Check `GITHUB_TOKEN` is valid and has `repo` scope
- Verify `GITHUB_REPO` format is `owner/repo`
- Check releases have the correct file names

### Slow First Load
- Free tier services sleep after inactivity
- First request wakes them up (can take 30-60 seconds)
- Consider paid tier for production use

### Backend Health Check
```bash
curl https://your-backend.railway.app/health
```
Should return:
```json
{"status": "healthy", "data_loaded": true, ...}
```

---

## 📈 Performance Tips

1. **Enable Redis caching** for production
2. **Use CDN** for static assets (Vercel does this automatically)
3. **Preload data** on backend startup
4. **Use React Query's** staleTime to reduce API calls
5. **Implement pagination** for large data sets

---

## 🔐 Security Checklist

- [ ] Use environment variables for all secrets
- [ ] Enable Supabase Row Level Security
- [ ] Use HTTPS only
- [ ] Implement rate limiting (FastAPI middleware)
- [ ] Add authentication (Supabase Auth recommended)
- [ ] Validate all user inputs (Pydantic does this)
- [ ] Keep dependencies updated

---

## 📞 Support

For issues:
1. Check the browser console for errors
2. Check backend logs (Railway/Render dashboard)
3. Verify all environment variables are set
4. Test API endpoints directly via `/docs`

---

## 🎉 Next Steps

After successful deployment:

1. **Implement remaining pages:**
   - Detailed Analysis
   - Advanced Comparison
   - Portfolio Construction
   - Recommended Portfolio

2. **Add authentication:**
   - Integrate Supabase Auth
   - Protect API endpoints
   - Add user management

3. **Enhance features:**
   - Real-time updates with WebSockets
   - PDF report generation
   - Email notifications
   - Mobile responsiveness

4. **Monitor & optimize:**
   - Add error tracking (Sentry)
   - Performance monitoring
   - Analytics (Plausible/PostHog)
