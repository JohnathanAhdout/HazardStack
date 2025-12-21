# SPIRAL Deployment Guide

Complete deployment guide for SPIRAL web and mobile applications.

## 📋 Prerequisites

### Web App
- Node.js 18+
- npm or yarn
- Docker (optional)
- Vercel account (for cloud deployment)

### Mobile App
- Node.js 18+
- Expo account
- EAS CLI (`npm install -g eas-cli`)
- Apple Developer account (iOS)
- Google Play Console account (Android)

### Backend API
- Python 3.10+
- PostgreSQL with PostGIS
- Redis
- Docker (recommended)

---

## 🌐 Web App Deployment

### Option 1: Vercel (Recommended)

**One-Click Deploy:**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/hazardstack/tree/main/web-app)

**Manual Deploy:**

```bash
cd web-app

# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy to production
vercel --prod
```

**Environment Variables:**
```bash
# Add in Vercel dashboard
NEXT_PUBLIC_API_URL=https://your-api-url.com
```

### Option 2: Docker

**Build and Run:**

```bash
cd web-app

# Build image
docker build -t spiral-web .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  spiral-web
```

**Docker Compose (Full Stack):**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### Option 3: Traditional Hosting

```bash
cd web-app

# Install dependencies
npm ci

# Build production bundle
npm run build

# Start production server
npm start
```

**Nginx Configuration:**

```nginx
server {
    listen 80;
    server_name spiral.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 📱 Mobile App Deployment

### Setup EAS Build

```bash
cd mobile-app

# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Configure project
eas build:configure
```

### Build for Testing

**iOS Simulator:**
```bash
eas build --platform ios --profile development
```

**Android APK:**
```bash
eas build --platform android --profile preview
```

### Production Builds

**iOS (App Store):**
```bash
# Build for production
eas build --platform ios --profile production

# Submit to App Store
eas submit --platform ios
```

**Android (Play Store):**
```bash
# Build for production
eas build --platform android --profile production

# Submit to Play Store
eas submit --platform android
```

### Configuration

Edit `eas.json` for build settings:

```json
{
  "build": {
    "production": {
      "env": {
        "EXPO_PUBLIC_API_URL": "https://api.spiral.app"
      }
    }
  }
}
```

---

## 🔧 Backend API Deployment

### Docker (Recommended)

```bash
cd hazardstack

# Build image
docker build -f infra/docker/api.Dockerfile -t spiral-api .

# Run with Docker Compose
docker-compose -f infra/docker/docker-compose.yml up -d
```

### Manual Deployment

```bash
cd hazardstack

# Install dependencies
pip install -e .

# Set environment variables
export DATABASE_URL=postgresql://user:pass@localhost/spiral
export REDIS_URL=redis://localhost:6379

# Run migrations
python scripts/init_db.py

# Start API server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment Variables

```bash
# API Configuration
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379
API_KEY_SECRET=your-secret-key

# Model Paths
MODEL_PATH=/app/models

# Data Sources
USGS_API_URL=https://earthquake.usgs.gov/fdsnws/event/1
IMD_DATA_URL=https://imdpune.gov.in/
```

---

## 🚀 CI/CD Setup

### GitHub Actions

**Web App:**

1. Add secrets to GitHub repository:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

2. Push to `main` branch triggers deployment

**Mobile App:**

1. Add secrets:
   - `EXPO_TOKEN`

2. Push to `production` branch triggers builds

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

web-build:
  stage: build
  script:
    - cd web-app
    - npm ci
    - npm run build
  artifacts:
    paths:
      - web-app/.next

web-deploy:
  stage: deploy
  script:
    - cd web-app
    - vercel --prod --token=$VERCEL_TOKEN
  only:
    - main
```

---

## 🔒 Security Configuration

### SSL/TLS Certificates

**Let's Encrypt (Free):**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d spiral.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### API Security

```python
# Enable CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://spiral.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/risk")
@limiter.limit("100/minute")
async def get_risk(request: Request):
    pass
```

---

## 📊 Monitoring & Logging

### Web App - Vercel Analytics

```typescript
// Add to app/layout.tsx
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

### Mobile App - Sentry

```bash
npm install @sentry/react-native
```

```typescript
// Add to App.tsx
import * as Sentry from '@sentry/react-native';

Sentry.init({
  dsn: 'your-sentry-dsn',
  tracesSampleRate: 1.0,
});
```

### Backend API - Prometheus

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

---

## 🧪 Testing Deployments

### Web App

```bash
# Test production build locally
npm run build
npm start

# Visit http://localhost:3000
```

### Mobile App

```bash
# Test on device
expo start --no-dev --minify

# Scan QR code with Expo Go
```

### API

```bash
# Health check
curl https://api.spiral.app/api/v1/health

# Test risk endpoint
curl "https://api.spiral.app/api/v1/risk?lat=19.07&lon=72.88"
```

---

## 🔄 Database Migrations

### Initial Setup

```bash
# Create database
createdb spiral

# Install PostGIS
psql spiral -c "CREATE EXTENSION postgis;"

# Run migrations
python scripts/init_db.py
```

### Backup & Restore

```bash
# Backup
pg_dump spiral > backup.sql

# Restore
psql spiral < backup.sql
```

---

## 📈 Scaling

### Web App - Horizontal Scaling

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spiral-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spiral-web
  template:
    metadata:
      labels:
        app: spiral-web
    spec:
      containers:
      - name: web
        image: spiral/web:latest
        ports:
        - containerPort: 3000
```

### API - Load Balancing

```nginx
upstream api_backend {
    least_conn;
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    location / {
        proxy_pass http://api_backend;
    }
}
```

---

## 🐛 Troubleshooting

### Web App Issues

**Build Fails:**
```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

**Map Not Loading:**
- Ensure Leaflet CSS is imported
- Check browser console for errors

### Mobile App Issues

**Build Fails:**
```bash
# Clear Expo cache
expo start -c

# Reset EAS build
eas build --clear-cache
```

**Push Notifications Not Working:**
- Verify Expo push credentials
- Check device permissions

### API Issues

**Database Connection:**
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

**High Memory Usage:**
```bash
# Limit workers
uvicorn api.main:app --workers 2 --limit-concurrency 100
```

---

## 📚 Additional Resources

- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Expo Build](https://docs.expo.dev/build/introduction/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## 🆘 Support

- **Documentation**: [spiral.readthedocs.io](https://spiral.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/yourusername/hazardstack/issues)
- **Email**: support@spiral.app

---

**Last Updated**: December 2024
**Version**: 1.0.0
