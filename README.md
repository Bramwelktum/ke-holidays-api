# Kenya Public Holidays API

A free, public FastAPI service providing Kenya public holidays with observed-date rule support.

## 🌐 Live API Endpoints

Once deployed, use these endpoints:

- **API Docs**: `https://your-app.onrender.com/docs`
- **Health Check**: `https://your-app.onrender.com/health`
- **Get Holidays**: `GET /v1/holidays?year=2026`
- **Date Range**: `GET /v1/holidays?from=2026-01-01&to=2026-12-31`
- **Is Holiday**: `GET /v1/is-holiday?date=2026-06-01`

## 🚀 Quick Deployment (Free Hosting)

**Deploy for free in 5 minutes!** See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

### Render (Recommended - Easiest)
1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. Click "New +" → "Blueprint"
4. Connect your GitHub repo
5. Render auto-detects `render.yaml` and deploys everything

**That's it!** Your API will be live at `https://your-app.onrender.com`

## 📚 API Features

- **Sunday Rule**: Holidays falling on Sunday automatically move to the next non-holiday day
- **Multiple Query Options**: By year or date range
- **Public Access**: CORS enabled for anyone to call from web browsers
- **Auto-generated Docs**: Interactive Swagger UI at `/docs`

## 🏃 Local Development

### Prerequisites
- Python 3.12+
- PostgreSQL (or Docker)

### Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ke-holidays-api.git
   cd ke-holidays-api
   ```

2. **Start PostgreSQL**
   ```bash
   docker compose up -d
   ```

3. **Setup Python environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Windows
   copy .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```
   
   Edit `.env` if needed (default uses port 5433 to avoid conflicts)

5. **Populate database**
   ```bash
   # Windows PowerShell
   Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') } }
   python -m scripts.ingest 2026
   
   # Linux/Mac
   export $(cat .env | xargs)
   python -m scripts.ingest 2026
   ```

6. **Run API**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Test locally**
   - API Docs: http://127.0.0.1:8000/docs
   - Health: http://127.0.0.1:8000/health
   - Holidays: http://127.0.0.1:8000/v1/holidays?year=2026

## 📖 Usage Examples

### Get all holidays for 2026
```bash
curl https://your-app.onrender.com/v1/holidays?year=2026
```

### Get holidays in a date range
```bash
curl "https://your-app.onrender.com/v1/holidays?from=2026-01-01&to=2026-03-31"
```

### Check if a date is a holiday
```bash
curl "https://your-app.onrender.com/v1/is-holiday?date=2026-06-01"
```

### JavaScript/Fetch Example
```javascript
// Get holidays for current year
const year = new Date().getFullYear();
const response = await fetch(`https://your-app.onrender.com/v1/holidays?year=${year}`);
const data = await response.json();
console.log(data.holidays);

// Check if today is a holiday
const today = new Date().toISOString().split('T')[0];
const checkResponse = await fetch(`https://your-app.onrender.com/v1/is-holiday?date=${today}`);
const result = await checkResponse.json();
console.log(result.isHoliday); // true or false
```

## 📁 Project Structure

```
ke-holidays-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── db.py            # Database configuration
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   └── logic.py         # Sunday rule logic
├── scripts/
│   └── ingest.py        # Holiday ingestion script
├── .github/
│   └── workflows/
│       └── ingest.yml   # Automated ingestion (optional)
├── render.yaml          # Render deployment config
├── Procfile             # Railway/Heroku config
├── fly.toml            # Fly.io config
└── docker-compose.yml   # Local PostgreSQL
```

## 🔧 Configuration

The API uses environment variables:

- `DATABASE_URL`: PostgreSQL connection string (auto-set by hosting platforms)
- `PORT`: Server port (auto-set by hosting platforms)

## 📝 License

This project is open source and available for free use.

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 More Information

For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)
