# 🚀 SPIRAL Prototypes - Quick Access Guide

Immediate access to fully functional web and mobile applications!

## 🌐 Web Dashboard (2 minutes)

### Start the Web App

```bash
cd web-app
npm install
npm run dev
```

**Then open:** http://localhost:3000

### What You'll See

✅ **Interactive Risk Map**
- Real-time hazard visualization
- Color-coded risk zones (Low/Moderate/High/Extreme)
- Click anywhere to get risk assessment

✅ **Live Dashboard**
- Active monitoring cells
- Recent earthquake events
- Model accuracy statistics
- Gravity wave feature status

✅ **Risk Assessment Panel**
- Current risk level for selected location
- Hazard breakdown (rain, flood, earthquake)
- Score percentages and metrics

✅ **Recent Events List**
- Earthquake events from last 24 hours
- Magnitude, location, depth, time
- Color-coded by severity

### Features

- 🗺️ Leaflet-powered interactive maps
- 📊 Real-time statistics cards
- 📱 Fully responsive (works on phone/tablet)
- 🔌 **Works with mock data** - no API needed!
- ⚡ Fast load times (< 2 seconds)

### Screenshot

![Web Dashboard](docs/images/system_architecture.png)

---

## 📱 Mobile App (2 minutes)

### Prerequisites

1. Install **Expo Go** app on your phone:
   - iOS: App Store
   - Android: Play Store

### Start the Mobile App

```bash
cd mobile-app
npm install
npm start
```

### Test on Your Phone

1. **Scan the QR code** displayed in terminal
2. App loads in Expo Go
3. Explore all features!

### What You'll See

**Home Screen:**
- Current risk level card
- System statistics (4 cards)
- Hazard component bars
- Recent events feed
- Pull-to-refresh

**Map Screen:**
- Interactive map of India
- Color-coded risk circles
- Your location marker
- Tap circles for details
- Risk level legend

**Alerts Screen:**
- Recent hazard events
- Filter by type (earthquake/flood/rain)
- Event details (magnitude, location, time)
- Pull-to-refresh

**Settings Screen:**
- Toggle notifications
- Configure alert types
- Location preferences
- About information

### Features

- 📍 Location-based risk assessment
- 🗺️ Native maps with markers
- 🔔 Push notification support
- 📊 Live event monitoring
- ⚡ Offline mode with mock data
- 🎨 Native iOS/Android experience

---

## 🎯 Quick Commands

### Web App

```bash
# Development
cd web-app && npm run dev

# Production build
cd web-app && npm run build

# Deploy to Vercel
cd web-app && vercel --prod
```

### Mobile App

```bash
# Development (Expo Go)
cd mobile-app && npm start

# Android APK (for testing)
cd mobile-app && eas build --platform android --profile preview

# Production builds
cd mobile-app && eas build --platform ios
cd mobile-app && eas build --platform android
```

---

## 🧪 Testing Without Backend

Both apps include **mock data** for demonstration:

### Web App Mock Data
- Located in: `web-app/lib/api.ts`
- Provides realistic risk assessments
- Simulates API responses
- Enables offline testing

### Mobile App Mock Data
- Located in: `mobile-app/src/services/api.ts`
- Provides sample events
- Simulates location-based data
- Enables offline functionality

**This means you can test both apps immediately without running the API backend!**

---

## 🔗 With Full Backend

To connect to the real API:

### 1. Start API Backend

```bash
cd hazardstack
pip install -e .
python api/main.py
# API runs on http://localhost:8000
```

### 2. Configure Web App

Edit `web-app/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Configure Mobile App

Edit `mobile-app/src/services/api.ts`:
```typescript
const API_URL = 'http://YOUR_IP:8000'; // Use your machine's IP, not localhost
```

### 4. Test Connection

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Get risk data
curl "http://localhost:8000/api/v1/risk?lat=19.07&lon=72.88"
```

---

## 📦 Full Stack with Docker

Run everything together:

```bash
docker-compose up -d

# Access:
# Web:    http://localhost:3000
# API:    http://localhost:8000
# Mobile: npm start (scan QR code)
```

---

## 🎨 Features Showcase

### Web Dashboard Features

| Feature | Description |
|---------|-------------|
| **Interactive Map** | Click anywhere to assess risk |
| **Risk Zones** | Color-coded circles show hazard levels |
| **Statistics** | Live metrics (cells, events, accuracy) |
| **Event Feed** | Recent earthquakes with details |
| **Responsive** | Works on all devices |

### Mobile App Features

| Feature | Description |
|---------|-------------|
| **Location Services** | Auto-detect your location |
| **Push Notifications** | Real-time hazard alerts |
| **Offline Mode** | Works without internet |
| **Native Performance** | Smooth 60fps animations |
| **Cross-Platform** | iOS & Android from one codebase |

---

## 🐛 Troubleshooting

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
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

### Map Not Loading (Web)

- Check browser console for errors
- Verify Leaflet CSS is imported
- Try hard refresh (Ctrl+Shift+R)

### Mobile App Won't Load

- Ensure phone and computer are on same Wi-Fi
- Check firewall isn't blocking ports
- Try restarting Expo server

---

## 📊 Demo Data

Both apps include realistic demo data:

### Locations (Mock Data)
- Mumbai: 19.07°N, 72.88°E
- Delhi: 28.7°N, 77.2°E
- Northeast India: 26.2°N, 91.7°E

### Events (Mock Data)
- M4.5 earthquake (Northern India, 2h ago)
- M3.8 earthquake (Gujarat, 8h ago)
- M5.2 earthquake (Northeast, 12h ago)

### Risk Levels
- LOW: 0.0 - 0.3
- MODERATE: 0.3 - 0.6
- HIGH: 0.6 - 0.8
- EXTREME: 0.8 - 1.0

---

## 🚀 Next Steps

1. **Try the prototypes** (2 minutes each)
2. **Customize** the components in `components/` or `src/screens/`
3. **Deploy** using Vercel (web) or EAS (mobile)
4. **Scale** with Docker or Kubernetes

---

## 📚 Additional Resources

- **Web App Docs**: [web-app/README.md](web-app/README.md)
- **Mobile App Docs**: [mobile-app/README.md](mobile-app/README.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Quick Deploy**: [QUICKSTART_DEPLOYMENT.md](QUICKSTART_DEPLOYMENT.md)

---

## ✨ Summary

**Web App:**
```bash
cd web-app && npm install && npm run dev
# http://localhost:3000
```

**Mobile App:**
```bash
cd mobile-app && npm install && npm start
# Scan QR code with Expo Go
```

**Both apps work immediately with mock data - no backend required!**

---

**Happy Testing! 🎉**
