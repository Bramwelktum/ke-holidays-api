# 🚀 Quick Deploy to Render (Free) - 5 Minutes

Follow these simple steps to deploy your API for free on Render:

## Step 1: Push to GitHub

```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit: Kenya Holidays API"

# Create repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/ke-holidays-api.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy on Render

1. **Sign up/Login** at [render.com](https://render.com) (free)

2. **Create Blueprint**
   - Click "New +" → "Blueprint"
   - Click "Connect GitHub"
   - Select your repository `ke-holidays-api`
   - Click "Apply"

3. **Wait for Deployment**
   - Render will automatically:
     - Create a PostgreSQL database
     - Deploy your web service
     - Link them together
   - Takes 5-10 minutes

4. **Get Your URL**
   - After deployment, you'll get a URL like:
   - `https://ke-holidays-api.onrender.com`

## Step 3: Populate Database

After deployment completes:

1. Go to Render Dashboard
2. Click on your web service (not the database)
3. Click "Shell" tab
4. Run these commands:

```bash
# Ingest holidays for multiple years
python -m scripts.ingest 2024
python -m scripts.ingest 2025
python -m scripts.ingest 2026
python -m scripts.ingest 2027
```

**Note:** The `DATABASE_URL` environment variable is automatically set by Render, so you don't need to configure it manually.

## Step 4: Test Your API

Visit these URLs in your browser:

- **API Documentation**: `https://your-app.onrender.com/docs`
- **Health Check**: `https://your-app.onrender.com/health`
- **Holidays 2026**: `https://your-app.onrender.com/v1/holidays?year=2026`

## ✅ Done!

Your API is now live and publicly accessible! Anyone can call it:

```javascript
// Example: Check if today is a holiday
const today = new Date().toISOString().split('T')[0];
fetch(`https://your-app.onrender.com/v1/is-holiday?date=${today}`)
  .then(res => res.json())
  .then(data => console.log('Is holiday:', data.isHoliday));
```

## 📝 Important Notes

- **Free Tier Limitation**: The service sleeps after 15 minutes of inactivity. First request after sleep takes ~30 seconds to wake up.
- **Database**: Render provides a free PostgreSQL database that's automatically connected.
- **CORS**: Already configured to allow all origins (`*`), so anyone can call your API from web browsers.

## 🎯 Next Steps

- Share your API URL with others!
- Add more years: `python -m scripts.ingest 2028` (in Render Shell)
- Set up automated ingestion: See `.github/workflows/ingest.yml`

For more deployment options (Railway, Fly.io), see [DEPLOYMENT.md](./DEPLOYMENT.md)
