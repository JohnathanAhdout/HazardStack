# 🚀 SPIRAL Local Launch Guide

Quick guide to run SPIRAL on your local machine with all the new features!

## ✅ Prerequisites (You Already Have These!)

- ✅ Node.js: v22.21.1
- ✅ npm: 10.9.4
- ✅ Python: 3.11.14

---

## 🌐 Option 1: Web App Only (Fastest - 2 Minutes)

The web app now has **full functionality** with real USGS earthquake data!

### Terminal 1: Start Web App

```bash
# Go to web app directory
cd /home/user/SPIRAL/web-app

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Open browser:** http://localhost:3000

### ✨ What You'll See:

- **Dashboard** - Interactive map with click-to-select locations
- **Alerts Page** - Real-time earthquake data from USGS API
- **Analytics Page** - Statistical charts and distributions
- **About Page** - System documentation
- **Settings Page** - User preferences
- **Notifications** - Real-time alerts with filters

### 🎯 Features to Try:

1. **Click anywhere on the map** → Updates risk data for that location
2. **Navigate to `/alerts`** → See real USGS earthquake events
3. **Navigate to `/analytics`** → View statistical charts
4. **Click notification bell** → View alert feed
5. **Click settings gear** → Configure preferences

---

## 🔌 Option 2: Full System (Web + Backend API)

Run both the web app and the FastAPI backend for complete functionality.

### Terminal 1: Start Backend API

```bash
# Go to hazardstack directory
cd /home/user/SPIRAL/hazardstack

# Install Python dependencies (first time only)
pip3 install -r ../requirements.txt

# Start FastAPI server
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test the API:**
```bash
# Open a new terminal
curl http://localhost:8000/api/v1/health

# Should return:
# {"status":"healthy","timestamp":"...","system":{...}}
```

**API Endpoints Available:**

- `GET /api/v1/health` - System health check
- `GET /api/v1/ready` - Service readiness (checks USGS API, resources)
- `GET /api/v1/risk?lat=19.07&lon=72.88&radius_km=10&horizons=1h,6h,24h` - Risk data
- `GET /api/v1/events/recent?hours=24&min_magnitude=3.0` - Real USGS earthquakes
- `GET /api/v1/events/earthquake/{event_id}` - Event details with aftershock forecast
- `GET /api/v1/tiles/{z}/{x}/{y}?horizon=6h` - GeoJSON tiles for map

### Terminal 2: Start Web App

```bash
# Go to web app directory
cd /home/user/SPIRAL/web-app

# Create .env.local file for API connection
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' > .env.local

# Install dependencies (first time only, if not done)
npm install

# Start development server
npm run dev
```

**Open browser:** http://localhost:3000

Now the web app will fetch **real data** from the backend API!

---

## 📱 Option 3: Mobile App (Bonus)

### Terminal 1: Start Mobile App

```bash
# Go to mobile app directory
cd /home/user/SPIRAL/mobile-app

# Install dependencies (first time only)
npm install

# Start Expo
npm start
```

**A QR code will appear in the terminal!**

### On Your Phone:

1. **Install Expo Go:**
   - iOS: App Store → Search "Expo Go"
   - Android: Play Store → Search "Expo Go"

2. **Scan QR Code:**
   - iPhone: Use Camera app
   - Android: Open Expo Go → Scan QR Code

3. **Wait for app to load** (30-60 seconds first time)

---

## 🧪 Quick API Tests

Once the backend is running, try these commands:

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Readiness Check (Tests USGS API)
```bash
curl http://localhost:8000/api/v1/ready
```

### 3. Get Real Earthquake Data
```bash
curl "http://localhost:8000/api/v1/events/recent?hours=24&min_magnitude=3.0"
```

### 4. Get Risk Data for Mumbai
```bash
curl "http://localhost:8000/api/v1/risk?lat=19.07&lon=72.88&radius_km=10&horizons=6h"
```

### 5. Get Event Details (use an event_id from step 3)
```bash
curl "http://localhost:8000/api/v1/events/earthquake/{event_id}"
```

### 6. Get Map Tiles
```bash
curl "http://localhost:8000/api/v1/tiles/8/155/97?horizon=6h"
```

---

## 🎯 Quick Navigation Guide

### Web App Pages:

- **/** → Redirects to /dashboard
- **/dashboard** → Main risk monitoring interface
- **/alerts** → Event listing with filters and details
- **/analytics** → Statistical charts and analysis
- **/about** → System documentation and features
- **/settings** → User preferences
- **/notifications** → Real-time alert feed

### API Documentation:

- **http://localhost:8000/docs** → Interactive API documentation (Swagger UI)
- **http://localhost:8000/redoc** → ReDoc API documentation

---

## 🛠️ Troubleshooting

### Web App Issues

**Port 3000 already in use:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

**Module not found errors:**
```bash
cd web-app
rm -rf node_modules .next package-lock.json
npm install
npm run dev
```

**Blank page:**
```bash
cd web-app
rm -rf .next
npm run dev
```

### Backend API Issues

**Port 8000 already in use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python3 -m uvicorn api.main:app --reload --port 8001
```

**Import errors:**
```bash
# Reinstall dependencies
pip3 install --user -r requirements.txt

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**USGS API not working:**
The app will automatically fall back to mock data if USGS API is unavailable.

### Mobile App Issues

**QR code won't scan:**
- Ensure phone and computer are on same WiFi network
- Try running `npm start -- --tunnel` for ngrok tunnel

**App crashes:**
```bash
cd mobile-app
npm start -- --clear
```

---

## 📊 What's New (Just Implemented!)

### Backend Features:
✅ Real USGS Earthquake API integration
✅ Event details with aftershock forecasting
✅ Enhanced readiness checks (USGS API, resources, H3 grid)
✅ GeoJSON tile generation endpoint
✅ Flood bulletin support (mock data, CWC pending)

### Frontend Features:
✅ Multi-page navigation (Dashboard, Alerts, Analytics, About, Settings, Notifications)
✅ Interactive map with click-to-select locations
✅ Real-time earthquake event display
✅ Event filtering (time range, magnitude)
✅ Notification system with read/unread tracking
✅ Settings page with persistence
✅ Dynamic statistics calculations (no hardcoded values!)
✅ Analytics dashboard with charts

---

## 🎓 Development Tips

### Hot Reload

Both web app and API support hot reload:
- **Web App**: Changes to code → Browser auto-refreshes
- **API**: Changes to Python files → Server auto-restarts (with `--reload` flag)

### Debugging

**Web App:**
```bash
# Open browser console (F12)
# Check Network tab for API calls
# Check Console tab for errors
```

**API:**
```bash
# API logs appear in terminal
# Add print() statements for debugging
# Use /docs endpoint to test API manually
```

### Environment Variables

**Web App** (create `web-app/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend** (create `hazardstack/.env`):
```env
# Optional: Add API keys if needed in future
USGS_API_KEY=your_key_here
```

---

## 📚 Additional Resources

- **Full README**: `/home/user/SPIRAL/README.md`
- **Web App Guide**: `/home/user/SPIRAL/web-app/README.md`
- **Mobile App Guide**: `/home/user/SPIRAL/mobile-app/README.md`
- **API Docs** (when running): http://localhost:8000/docs

---

## 🆘 Need Help?

1. Check error messages in terminal
2. Check browser console (F12)
3. Verify all dependencies are installed
4. Try clearing caches and reinstalling
5. Check that ports 3000 and 8000 are available

---

**Happy coding! 🚀**
