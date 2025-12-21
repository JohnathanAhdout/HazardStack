# SPIRAL Web and Mobile Applications

Complete web dashboard and mobile app prototypes for the SPIRAL Multi-Hazard Prediction System.

## 🌐 Web Application

Modern, responsive web dashboard built with Next.js and React.

### Features

- **Interactive Risk Map** - Real-time visualization using Leaflet
- **Live Statistics** - Active monitoring cells, recent events, model accuracy
- **Alert Dashboard** - Recent earthquake, flood, and rainfall events
- **Risk Assessment Panel** - Detailed hazard analysis for any location
- **Responsive Design** - Works on desktop, tablet, and mobile browsers

### Technology Stack

- Next.js 14 (React 18)
- TypeScript
- Tailwind CSS
- Leaflet / React-Leaflet
- Axios for API calls

### Quick Start

```bash
cd web-app
npm install
npm run dev
# Open http://localhost:3000
```

See [web-app/README.md](web-app/README.md) for detailed documentation.

## 📱 Mobile Application

Cross-platform mobile app built with React Native and Expo.

### Features

- **Real-Time Alerts** - Push notifications for hazards
- **Location-Based** - Automatic risk assessment for your location
- **Interactive Maps** - Color-coded risk zones across India
- **Recent Events** - Track earthquakes, floods, and weather events
- **Offline Support** - Mock data fallback when API unavailable
- **Privacy-First** - Location data stays on device

### Technology Stack

- React Native with Expo
- TypeScript
- React Navigation
- React Native Maps
- Expo Notifications & Location

### Quick Start

```bash
cd mobile-app
npm install
npm start
# Scan QR code with Expo Go app
```

See [mobile-app/README.md](mobile-app/README.md) for detailed documentation.

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│         SPIRAL System               │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────┐   ┌─────────────┐ │
│  │   Web App   │   │  Mobile App │ │
│  │  (Next.js)  │   │   (Expo)    │ │
│  └──────┬──────┘   └──────┬──────┘ │
│         │                 │         │
│         └────────┬────────┘         │
│                  │                  │
│         ┌────────▼────────┐         │
│         │   FastAPI       │         │
│         │   Backend       │         │
│         └────────┬────────┘         │
│                  │                  │
│         ┌────────▼────────┐         │
│         │  ML Models      │         │
│         │  - Earthquake   │         │
│         │  - Flood        │         │
│         │  - Rain/GW      │         │
│         └─────────────────┘         │
└─────────────────────────────────────┘
```

## 📡 API Integration

Both applications connect to the SPIRAL API backend:

### Endpoints Used

- `GET /api/v1/risk` - Multi-hazard risk assessment
- `GET /api/v1/events/recent` - Recent earthquake events
- `GET /api/v1/health` - API health check

### Mock Data

Both apps include mock data for development and demonstration when the API is unavailable.

## 🚀 Deployment

### Web App Deployment

**Vercel (Recommended)**
```bash
cd web-app
vercel deploy
```

**Docker**
```bash
cd web-app
docker build -t spiral-web .
docker run -p 3000:3000 spiral-web
```

See [web-app/README.md](web-app/README.md) for more options.

### Mobile App Deployment

**iOS App Store**
```bash
cd mobile-app
eas build --platform ios
```

**Google Play Store**
```bash
cd mobile-app
eas build --platform android
```

See [mobile-app/README.md](mobile-app/README.md) for detailed instructions.

## 🎨 Design System

Both applications share a consistent design language:

### Colors

- **Primary Blue**: `#0066CC` - Main brand color
- **Success Green**: `#22C55E` - LOW risk, positive states
- **Warning Orange**: `#F59E0B` - MODERATE risk, warnings
- **Danger Red**: `#EF4444` - HIGH risk, errors
- **Extreme Dark Red**: `#7C2D12` - EXTREME risk

### Typography

- **Headers**: Bold, larger sizes
- **Body**: Regular weight, readable sizes
- **Captions**: Smaller, muted colors

### Components

Both apps feature:
- Risk level badges with consistent colors
- Event cards with magnitude indicators
- Statistics cards with icons
- Interactive maps with color-coded zones

## 📊 Features Comparison

| Feature | Web App | Mobile App |
|---------|---------|------------|
| Interactive Map | ✅ Leaflet | ✅ Native Maps |
| Real-Time Data | ✅ | ✅ |
| Push Notifications | ⚠️ Browser | ✅ Native |
| Location Services | ⚠️ Browser | ✅ Native |
| Offline Mode | ❌ | ✅ Mock Data |
| Responsive | ✅ Desktop/Mobile | N/A |
| Platform | Web Browser | iOS/Android |

## 🔒 Security & Privacy

### Web App
- HTTPS only in production
- API key rotation support
- No client-side data storage

### Mobile App
- Location data stays on device
- Encrypted API communication
- Optional location sharing
- Privacy-first notifications

## 🧪 Testing

### Web App
```bash
cd web-app
npm run lint
npm run build  # Test production build
```

### Mobile App
```bash
cd mobile-app
npm test
expo start -c  # Clear cache
```

## 📝 Development Guidelines

### Code Style

Both projects use:
- TypeScript for type safety
- ESLint for code quality
- Consistent naming conventions
- Component-based architecture

### Adding Features

1. Create component in appropriate directory
2. Add TypeScript types
3. Implement UI with Tailwind (web) or StyleSheet (mobile)
4. Connect to API service
5. Add error handling and loading states
6. Test on multiple devices/browsers

## 🐛 Troubleshooting

### Web App

**Map not loading**
- Check Leaflet CSS import
- Verify dynamic import for SSR

**API connection failed**
- Check NEXT_PUBLIC_API_URL in .env.local
- Verify CORS settings on API
- Falls back to mock data automatically

### Mobile App

**Location not working**
- Grant permissions in device settings
- Check GPS is enabled
- Verify location services in app settings

**Push notifications not working**
- Check notification permissions
- Verify Expo push credentials
- Test with demo notification

## 📚 Documentation

- [Web App Documentation](web-app/README.md)
- [Mobile App Documentation](mobile-app/README.md)
- [API Documentation](hazardstack/api/README.md)
- [Main Project README](README.md)

## 🤝 Contributing

See main [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/hazardstack/issues)
- **Documentation**: [spiral.readthedocs.io](https://spiral.readthedocs.io)
- **Email**: support@spiral.app

---

## Quick Start Summary

### Web App
```bash
cd web-app
npm install
npm run dev
```

### Mobile App
```bash
cd mobile-app
npm install
npm start
```

### API Backend
```bash
cd hazardstack
pip install -e .
python api/main.py
```

---

**Part of the SPIRAL Multi-Hazard Prediction System**

*Structured Physics-Informed Representation-Augmented Learning from Atmospheric Gravity Wave Signals for Multi-Hazard Prediction in India and Real-Time Web and Mobile Risk Alerts*
