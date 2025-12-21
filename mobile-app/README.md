# SPIRAL Mobile App

Cross-platform mobile application for real-time multi-hazard prediction, built with React Native and Expo.

## Features

- 📱 **Cross-Platform** - Runs on iOS and Android
- 🗺️ **Interactive Maps** - Real-time hazard visualization with risk zones
- 🔔 **Push Notifications** - Instant alerts for earthquakes, floods, and extreme rainfall
- 📍 **Location-Based** - Automatic risk assessment for your current location
- 📊 **Live Statistics** - Monitor recent events and model performance
- 🌊 **Gravity Wave Integration** - Enhanced predictions using atmospheric gravity wave signals
- 🔒 **Privacy-First** - Location data stays on your device

## Screenshots

[Screenshots would go here]

## Tech Stack

- **Framework**: React Native with Expo
- **Language**: TypeScript
- **Navigation**: React Navigation
- **Maps**: React Native Maps
- **State Management**: React Context
- **API Client**: Axios
- **Notifications**: Expo Notifications
- **Location**: Expo Location

## Getting Started

### Prerequisites

- Node.js 18+
- Expo CLI
- iOS Simulator (Mac) or Android Emulator
- SPIRAL API running (default: http://localhost:8000)

### Installation

```bash
# Install dependencies
npm install

# Install Expo CLI globally (if not already installed)
npm install -g expo-cli
```

### Development

```bash
# Start development server
npm start

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android

# Run in web browser
npm run web
```

### Running on Physical Device

1. Install the Expo Go app on your iOS or Android device
2. Scan the QR code from the development server
3. App will load on your device

## Project Structure

```
mobile-app/
├── App.tsx                # Main app entry point
├── app.json              # Expo configuration
├── src/
│   ├── screens/          # App screens
│   │   ├── HomeScreen.tsx       # Dashboard/home
│   │   ├── MapScreen.tsx        # Interactive map
│   │   ├── AlertsScreen.tsx     # Alerts list
│   │   └── SettingsScreen.tsx   # Settings
│   ├── components/       # Reusable components
│   │   ├── RiskCard.tsx         # Risk display card
│   │   ├── StatCard.tsx         # Statistics card
│   │   ├── EventCard.tsx        # Event list item
│   │   └── TabBarIcon.tsx       # Tab bar icons
│   ├── context/          # React context
│   │   └── LocationContext.tsx  # Location state
│   └── services/         # API services
│       └── api.ts               # API client
├── assets/              # Images, fonts, etc.
└── package.json         # Dependencies
```

## Features in Detail

### Home Screen

- Current risk level for your location
- System statistics (active cells, recent events)
- Hazard components breakdown
- Recent events feed
- Pull-to-refresh

### Map Screen

- Interactive map of India
- Color-coded risk zones:
  - 🟢 Green: LOW risk
  - 🟡 Yellow: MODERATE risk
  - 🟠 Orange: HIGH risk
  - 🔴 Red: EXTREME risk
- Tap anywhere to get risk assessment
- Your location marker
- Risk level legend

### Alerts Screen

- List of recent hazard events
- Filter by hazard type (earthquake, flood, rain)
- Detailed event information
- Time elapsed since event
- Pull-to-refresh

### Settings Screen

- Toggle notifications on/off
- Configure alert types
- Location tracking preferences
- Privacy settings
- About and help

## API Configuration

The app connects to the SPIRAL API backend. To configure:

1. Update API URL in `src/services/api.ts`:

```typescript
const API_URL = 'https://your-api-url.com'; // Production URL
```

2. For local development:
   - Ensure SPIRAL API is running on your machine
   - Use your machine's local IP (not localhost)
   - Example: `http://192.168.1.100:8000`

## Push Notifications

The app supports push notifications for hazard alerts:

### Setup for Production

1. **iOS**:
   - Configure APNs credentials in Expo
   - Update `app.json` with push notification settings

2. **Android**:
   - Configure FCM credentials in Expo
   - Update `app.json` with push notification settings

### Testing Notifications

Demo notification sent 5 seconds after app launch. See `App.tsx` for implementation.

## Building for Production

### iOS

```bash
# Build for iOS
expo build:ios

# Or use EAS Build (recommended)
eas build --platform ios
```

### Android

```bash
# Build APK
expo build:android -t apk

# Build App Bundle (for Play Store)
expo build:android -t app-bundle

# Or use EAS Build (recommended)
eas build --platform android
```

## App Store Deployment

### iOS App Store

1. Build IPA using `expo build:ios`
2. Upload to App Store Connect
3. Complete app metadata
4. Submit for review

### Google Play Store

1. Build App Bundle using `expo build:android`
2. Upload to Play Console
3. Complete store listing
4. Submit for review

## Permissions

The app requires the following permissions:

- **Location** (required): For location-based risk assessment
- **Notifications** (optional): For hazard alerts

Users are prompted for permissions on first launch.

## Mock Data

If the API is unavailable, the app uses mock data for demonstration. This allows the app to function offline for testing.

## Performance

- **Initial Load**: < 3s on average device
- **API Calls**: Automatic retry with fallback to mock data
- **Map Rendering**: Optimized with clustering for large datasets
- **App Size**: ~40MB (iOS), ~35MB (Android)

## Troubleshooting

### Map Not Loading

- Verify react-native-maps is properly installed
- Check Google Maps API key (Android)
- Ensure location permissions are granted

### API Connection Failed

- Check API URL in `src/services/api.ts`
- Verify API is running and accessible
- Check network connectivity
- App will use mock data as fallback

### Build Errors

- Clear cache: `expo start -c`
- Delete `node_modules` and reinstall
- Ensure Expo SDK version compatibility

### Location Not Working

- Grant location permissions in device settings
- Ensure GPS is enabled
- Try restarting the app

## Testing

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## Contributing

See main repository CONTRIBUTING.md

## License

MIT License - see LICENSE file

## Privacy

- Location data is only used for risk assessment
- No location data is stored on servers
- All data transmission is encrypted (HTTPS)
- See Privacy Policy for full details

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/hazardstack/issues)
- Email: support@spiral.app
- Documentation: [spiral.readthedocs.io](https://spiral.readthedocs.io)

---

**Part of the SPIRAL Multi-Hazard Prediction System**

*For official disaster warnings, always consult:*
- *Earthquakes: [NCS](https://seismo.gov.in)*
- *Floods: [CWC](https://ffs.india-water.gov.in)*
- *Weather: [IMD](https://mausam.imd.gov.in)*
- *Tsunami: [INCOIS](https://tsunami.incois.gov.in)*
