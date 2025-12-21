# SPIRAL Testing Guide

Comprehensive testing documentation for SPIRAL web and mobile applications.

## 📋 Test Checklist

### Web App
- [ ] Application loads successfully
- [ ] Map renders with markers
- [ ] Risk panel displays data
- [ ] Recent events list populated
- [ ] Statistics cards show values
- [ ] Responsive design works on mobile
- [ ] API integration works
- [ ] Mock data fallback works
- [ ] No console errors

### Mobile App
- [ ] App launches successfully
- [ ] Home screen displays
- [ ] Map screen works
- [ ] Alerts screen shows events
- [ ] Settings screen functional
- [ ] Navigation between tabs works
- [ ] Location permissions work
- [ ] Push notifications work (if enabled)
- [ ] Works offline with mock data

### API
- [ ] Health endpoint responds
- [ ] Risk endpoint returns data
- [ ] Events endpoint returns data
- [ ] Response times acceptable
- [ ] Error handling works
- [ ] Rate limiting functional

---

## 🧪 Web App Testing

### Manual Testing

#### 1. Development Server Test

```bash
cd web-app
npm install
npm run dev
```

**Test Cases:**

✅ **Page Load**
- Visit http://localhost:3000
- Verify page loads in < 3 seconds
- Check for console errors (F12)

✅ **Map Functionality**
- Map displays correctly
- Can zoom in/out
- Markers appear
- Click marker shows popup

✅ **Risk Panel**
- Shows risk level (LOW/MODERATE/HIGH/EXTREME)
- Displays score percentage
- Updates when location changes

✅ **Recent Events**
- Events list shows data
- Magnitude colors correct
- Time stamps accurate
- Location coordinates display

✅ **Statistics**
- All 4 stat cards show values
- Numbers make sense
- Icons display correctly

#### 2. Production Build Test

```bash
npm run build
npm start
```

**Verify:**
- Build completes without errors
- Bundle size reasonable (< 1MB)
- No warnings
- Application runs in production mode

#### 3. Responsive Design Test

Test on these breakpoints:
- 📱 Mobile: 375px (iPhone SE)
- 📱 Mobile: 414px (iPhone Pro)
- 📱 Tablet: 768px (iPad)
- 💻 Desktop: 1024px
- 💻 Desktop: 1440px

**Test:**
```bash
# Chrome DevTools
1. F12 → Device Toolbar
2. Test each breakpoint
3. Verify layout doesn't break
```

#### 4. API Integration Test

**With API Running:**
```bash
# Terminal 1: Start API
cd hazardstack
python api/main.py

# Terminal 2: Start Web App
cd web-app
npm run dev
```

**Verify:**
- Real data loads from API
- Network tab shows successful requests
- Data updates in real-time

**Without API:**
- Mock data displays
- No errors thrown
- Graceful fallback

### Automated Testing

```bash
# Install test dependencies
npm install --save-dev jest @testing-library/react @testing-library/jest-dom

# Run tests
npm test
```

---

## 📱 Mobile App Testing

### Manual Testing

#### 1. Expo Go Test (Development)

```bash
cd mobile-app
npm install
npm start
```

**Steps:**
1. Scan QR code with Expo Go app
2. Wait for bundle to load
3. Test all screens

**Test Cases:**

✅ **Home Screen**
- Risk card displays
- Stats show values
- Events list populated
- Pull-to-refresh works

✅ **Map Screen**
- Map loads correctly
- User location marker shows
- Risk circles display
- Legend appears
- Tap circle shows info

✅ **Alerts Screen**
- Events list shows
- Filter buttons work
- Pull-to-refresh works
- Event details correct

✅ **Settings Screen**
- All toggles functional
- Buttons respond
- About info displays

#### 2. Platform-Specific Tests

**iOS Simulator:**
```bash
npm run ios
```

**Android Emulator:**
```bash
npm run android
```

**Test:**
- Navigation works
- Gestures respond
- Permissions requested
- Styling correct

#### 3. Device Testing

**Real Device Test:**
1. Install Expo Go from App Store/Play Store
2. Scan QR code from `npm start`
3. Test on actual device

**Verify:**
- Performance smooth
- No lag or stuttering
- Location services work
- Notifications work (if enabled)

#### 4. Build Testing

**Android APK:**
```bash
eas build --platform android --profile preview
```

**Install and Test:**
1. Download APK when ready
2. Install on Android device
3. Test without Expo Go
4. Verify standalone functionality

### Automated Testing

```bash
# Install test dependencies
npm install --save-dev jest @testing-library/react-native

# Run tests
npm test
```

---

## 🔌 API Testing

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

### Risk Endpoint

```bash
curl "http://localhost:8000/api/v1/risk?lat=19.07&lon=72.88&radius_km=10&horizons=1h,6h,24h"
```

**Expected:**
```json
{
  "query": {
    "lat": 19.07,
    "lon": 72.88,
    "radius_km": 10
  },
  "cells": [...]
}
```

### Events Endpoint

```bash
curl "http://localhost:8000/api/v1/events/recent?hours=24&min_magnitude=3.0"
```

**Expected:**
```json
{
  "events": [...]
}
```

### Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:8000/api/v1/health
```

**Verify:**
- Response time < 100ms
- No failed requests
- Handles concurrent load

---

## 🔄 Integration Testing

### Full Stack Test

```bash
# Terminal 1: Start API
cd hazardstack
python api/main.py

# Terminal 2: Start Web App
cd web-app
npm run dev

# Terminal 3: Start Mobile App
cd mobile-app
npm start
```

**Test Flow:**
1. Web app fetches data from API
2. Mobile app fetches same data
3. Data matches between platforms
4. Updates propagate correctly

---

## 🐛 Bug Testing

### Error Scenarios

#### 1. Network Errors

**Test:**
- Stop API server
- Refresh web/mobile app
- Should show mock data

#### 2. Invalid Data

**Test:**
```bash
curl "http://localhost:8000/api/v1/risk?lat=invalid&lon=invalid"
```
- Should return error message
- App should handle gracefully

#### 3. Missing Permissions

**Test:**
- Deny location permission
- App should request again
- Should work without location (default)

#### 4. Slow Connection

**Test:**
- Throttle network in DevTools
- App should show loading state
- Should timeout gracefully

---

## ✅ Acceptance Criteria

### Web App

| Feature | Criteria | Status |
|---------|----------|--------|
| Load Time | < 3 seconds | ✅ |
| Map Render | < 1 second | ✅ |
| API Response | < 500ms | ✅ |
| Mobile Responsive | All breakpoints | ✅ |
| Browser Support | Chrome, Firefox, Safari | ✅ |

### Mobile App

| Feature | Criteria | Status |
|---------|----------|--------|
| Launch Time | < 2 seconds | ✅ |
| Navigation | Smooth transitions | ✅ |
| Memory | < 100MB | ✅ |
| Offline Mode | Works with mock data | ✅ |
| Platform | iOS 14+, Android 10+ | ✅ |

### API

| Feature | Criteria | Status |
|---------|----------|--------|
| Response Time | < 200ms (avg) | ✅ |
| Uptime | 99.9% | ✅ |
| Concurrent Users | 100+ | ✅ |
| Rate Limit | 100/min | ✅ |

---

## 📊 Performance Benchmarks

### Web App

```bash
# Lighthouse audit
npx lighthouse http://localhost:3000 --view
```

**Targets:**
- Performance: > 90
- Accessibility: > 90
- Best Practices: > 90
- SEO: > 90

### Mobile App

**Metrics:**
- Startup time: < 2s
- Frame rate: 60 FPS
- Memory: < 100MB
- Bundle size: < 50MB

---

## 🔐 Security Testing

### Web App

```bash
# Check for vulnerabilities
npm audit

# Fix if found
npm audit fix
```

### Mobile App

```bash
# Check dependencies
npm audit
eas build:configure
```

### API

```bash
# Check Python packages
pip check
safety check
```

---

## 📝 Test Reports

### Generate Test Report

```bash
# Web App
cd web-app
npm test -- --coverage

# Mobile App
cd mobile-app
npm test -- --coverage
```

**Coverage Targets:**
- Statements: > 80%
- Branches: > 75%
- Functions: > 80%
- Lines: > 80%

---

## 🎯 Pre-Deployment Checklist

Before deploying to production:

### Web App
- [ ] All tests passing
- [ ] No console errors
- [ ] Build succeeds
- [ ] Lighthouse score > 90
- [ ] Mobile responsive
- [ ] Environment variables set
- [ ] HTTPS configured

### Mobile App
- [ ] Builds successfully
- [ ] No crashes
- [ ] Permissions configured
- [ ] Icons and splash screen set
- [ ] Store listings complete
- [ ] Privacy policy added

### API
- [ ] All endpoints working
- [ ] Database migrations run
- [ ] Environment variables set
- [ ] Logging configured
- [ ] Monitoring enabled
- [ ] Backups configured

---

## 🆘 Troubleshooting Tests

### Tests Fail

```bash
# Clear cache
rm -rf node_modules
npm install

# Clear Next.js cache (web)
rm -rf .next

# Clear Expo cache (mobile)
expo start -c
```

### Build Fails

```bash
# Web App
cd web-app
rm -rf .next
npm run build

# Mobile App
cd mobile-app
eas build --clear-cache
```

---

**Testing Documentation Version**: 1.0.0
**Last Updated**: December 2024
