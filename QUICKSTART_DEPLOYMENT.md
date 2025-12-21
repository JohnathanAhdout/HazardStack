# SPIRAL Quick Start Deployment Guide

Get SPIRAL up and running in minutes with this quick start guide.

## 🚀 Fastest Deploy (1 minute)

### Web App - Vercel (Recommended)

**One-Click Deploy:**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/SPIRAL/tree/main/web-app)

That's it! Your web app is live.

---

## 🐳 Docker Deployment (5 minutes)

### Full Stack with Docker Compose

```bash
# Clone repository
git clone https://github.com/yourusername/SPIRAL.git
cd SPIRAL

# Start everything
docker-compose up -d

# Access apps
# Web:  http://localhost:3000
# API:  http://localhost:8000
```

**Done!** All services are running.

---

## 💻 Local Development (10 minutes)

### 1. Web App

```bash
cd web-app
npm install
npm run dev
# Open http://localhost:3000
```

### 2. Mobile App

```bash
cd mobile-app
npm install
npm start
# Scan QR code with Expo Go app
```

### 3. API Backend

```bash
cd hazardstack
pip install -e .
python api/main.py
# API at http://localhost:8000
```

---

## 📱 Mobile App Testing

### Test on Your Phone (2 minutes)

1. Install Expo Go app from App Store or Play Store
2. Run `cd mobile-app && npm start`
3. Scan QR code with your phone
4. App loads instantly!

### Build APK for Android

```bash
cd mobile-app
npm install -g eas-cli
eas build --platform android --profile preview
# Download APK when ready
```

---

## ☁️ Production Deployment

### Web App

**Option 1: Vercel (Easiest)**
```bash
cd web-app
npm i -g vercel
vercel --prod
```

**Option 2: Docker**
```bash
cd web-app
docker build -t spiral-web .
docker run -p 3000:3000 spiral-web
```

### Mobile App

**iOS:**
```bash
cd mobile-app
eas build --platform ios --profile production
eas submit --platform ios
```

**Android:**
```bash
cd mobile-app
eas build --platform android --profile production
eas submit --platform android
```

---

## 🧪 Testing

### Web App
```bash
cd web-app
npm install
npm run dev
# Visit http://localhost:3000
# Test with mock data (works without API)
```

### Mobile App
```bash
cd mobile-app
npm install
npm start
# Scan QR code
# Test with mock data (works without API)
```

### API
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Test risk endpoint
curl "http://localhost:8000/api/v1/risk?lat=19.07&lon=72.88&radius_km=10"
```

---

## 🔧 Configuration

### Web App Environment

Create `web-app/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Mobile App Environment

Edit `mobile-app/src/services/api.ts`:
```typescript
const API_URL = 'http://your-ip:8000';
```

### API Environment

Create `hazardstack/.env`:
```env
DATABASE_URL=postgresql://user:pass@localhost/spiral
REDIS_URL=redis://localhost:6379
```

---

## 📊 Verify Deployment

### Web App Checks

✅ Page loads at http://localhost:3000
✅ Map displays correctly
✅ Statistics cards show data
✅ No console errors

### Mobile App Checks

✅ App loads in Expo Go
✅ Home screen shows risk data
✅ Map displays with markers
✅ Can navigate between tabs

### API Checks

```bash
# Health
curl http://localhost:8000/api/v1/health
# Should return: {"status":"healthy"}

# Risk data
curl "http://localhost:8000/api/v1/risk?lat=19.07&lon=72.88"
# Should return JSON with risk data
```

---

## 🐛 Quick Troubleshooting

### Web App Won't Start

```bash
cd web-app
rm -rf .next node_modules
npm install
npm run dev
```

### Mobile App Issues

```bash
cd mobile-app
expo start -c  # Clear cache
```

### Port Already in Use

```bash
# Web (3000)
lsof -ti:3000 | xargs kill -9

# API (8000)
lsof -ti:8000 | xargs kill -9
```

### API Not Responding

```bash
# Check if running
curl http://localhost:8000/api/v1/health

# Restart
cd hazardstack
python api/main.py
```

---

## 📚 Next Steps

1. **Customize**: Edit components in `web-app/components/` or `mobile-app/src/screens/`
2. **Deploy**: Follow [DEPLOYMENT.md](DEPLOYMENT.md) for production
3. **Scale**: Use Kubernetes configs in `kubernetes/`
4. **Monitor**: Add Sentry, Prometheus, or other tools

---

## 🆘 Need Help?

- **Full Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Web App**: See [web-app/README.md](web-app/README.md)
- **Mobile App**: See [mobile-app/README.md](mobile-app/README.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/SPIRAL/issues)

---

## ⚡ Deployment Comparison

| Method | Time | Difficulty | Best For |
|--------|------|------------|----------|
| Vercel One-Click | 1 min | ⭐ Easy | Web app demo |
| Docker Compose | 5 min | ⭐⭐ Moderate | Full stack local |
| Local Dev | 10 min | ⭐⭐ Moderate | Development |
| Production K8s | 30 min | ⭐⭐⭐⭐ Advanced | Scale |

---

## 🎯 Quick Commands Reference

```bash
# Web App
cd web-app && npm run dev

# Mobile App
cd mobile-app && npm start

# API
cd hazardstack && python api/main.py

# Full Stack (Docker)
docker-compose up -d

# Deploy Web to Vercel
cd web-app && vercel --prod

# Build Mobile APK
cd mobile-app && eas build --platform android
```

---

**Happy Deploying! 🌀**
