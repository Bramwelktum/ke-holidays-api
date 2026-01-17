# Free Deployment Guide for Kenya Holidays API

This guide shows you how to deploy the API for free on popular hosting platforms.

## Option 1: Render (Recommended - Easiest)

**Render** offers a free tier with PostgreSQL database included.

### Steps:

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/ke-holidays-api.git
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml` and deploy both the web service and PostgreSQL database
   - Wait for deployment (5-10 minutes)

3. **Set up the database**
   - Once deployed, your API will be live at: `https://ke-holidays-api.onrender.com`
   - You need to run the ingestion script to populate holidays
   - Go to Render Dashboard → Your Web Service → Shell
   - Run:
     ```bash
     export DATABASE_URL=<your-database-connection-string>
     python -m scripts.ingest 2026
     python -m scripts.ingest 2025
     # Add more years as needed
     ```

4. **Access your API**
   - API Docs: `https://YOUR-APP-NAME.onrender.com/docs`
   - Example: `https://YOUR-APP-NAME.onrender.com/v1/holidays?year=2026`

**Note:** Free tier on Render sleeps after 15 minutes of inactivity. First request after sleep takes ~30 seconds.

---

## Option 2: Railway

**Railway** offers free $5/month credit.

### Steps:

1. **Push to GitHub** (same as above)

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app) and sign up
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects the Python app

3. **Add PostgreSQL Database**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically set `DATABASE_URL` environment variable

4. **Configure Service**
   - Railway uses the `Procfile` automatically
   - Go to Settings → Generate Domain to get your public URL

5. **Populate Database**
   - Go to your service → Deployments → Click on the latest deployment
   - Open the "Shell" tab
   - Run:
     ```bash
     python -m scripts.ingest 2026
     python -m scripts.ingest 2025
     ```

6. **Access your API**
   - Your API will be available at: `https://YOUR-APP-NAME.up.railway.app`

---

## Option 3: Fly.io

**Fly.io** offers generous free tier.

### Steps:

1. **Install Fly CLI**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Create fly.toml** (already included in this repo)

3. **Deploy**
   ```bash
   fly auth login
   fly launch
   # Follow prompts
   ```

4. **Set up PostgreSQL**
   ```bash
   fly postgres create --name ke-holidays-db
   fly postgres attach ke-holidays-db --app ke-holidays-api
   ```

5. **Deploy and populate**
   ```bash
   fly deploy
   fly ssh console -C "python -m scripts.ingest 2026"
   ```

---

## Important Notes

### Environment Variables

All platforms automatically handle `DATABASE_URL` when you attach a PostgreSQL database. The app will use it automatically.

### CORS

The API includes CORS middleware allowing all origins (`*`), so anyone can call it from web browsers.

### Database Population

After deployment, remember to run the ingestion script for the years you need:
```bash
python -m scripts.ingest 2024
python -m scripts.ingest 2025
python -m scripts.ingest 2026
# etc.
```

You can run this via:
- **Render**: Dashboard → Shell
- **Railway**: Deployments → Shell tab
- **Fly.io**: `fly ssh console`

### Recommended: GitHub Actions (Automated Ingestion)

You can set up GitHub Actions to automatically run ingestion on a schedule. See `.github/workflows/ingest.yml` example.

---

## Testing Your Deployed API

Once deployed, test your API:

```bash
# Health check
curl https://YOUR-APP-NAME.onrender.com/health

# Get holidays for 2026
curl https://YOUR-APP-NAME.onrender.com/v1/holidays?year=2026

# Check if a date is a holiday
curl https://YOUR-APP-NAME.onrender.com/v1/is-holiday?date=2026-06-01

# Interactive docs
# Visit: https://YOUR-APP-NAME.onrender.com/docs
```

---

## Free Tier Limitations

| Platform | Free Tier Details |
|----------|-------------------|
| **Render** | Free tier sleeps after 15min inactivity. 750 hours/month free. |
| **Railway** | $5/month credit. Charges per usage. |
| **Fly.io** | 3 shared VMs, 160GB outbound data/month free. |

For a production API that stays "always on", consider Render's paid tier ($7/month) or Railway's usage-based pricing.

---

## Need Help?

- Check the API docs at `/docs` endpoint
- Review logs in your platform's dashboard
- Make sure DATABASE_URL is set correctly
- Ensure you've run the ingestion script for your needed years
