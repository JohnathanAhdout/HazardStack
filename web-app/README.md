# SPIRAL Web Dashboard

Real-time multi-hazard prediction dashboard for SPIRAL (Structured Physics-Informed Representation-Augmented Learning from Atmospheric Gravity Wave Signals for Multi-Hazard Prediction in India and Real-Time Web and Mobile Risk Alerts).

## Features

- 🗺️ **Interactive Risk Map** - Real-time visualization of hazard risks across India
- 📊 **Live Statistics** - Monitor active cells, recent events, and model accuracy
- ⚠️ **Alert System** - Real-time notifications for earthquake, flood, and rainfall hazards
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices
- 🌊 **Atmospheric Gravity Wave Integration** - Enhanced rainfall predictions using gravity wave signals
- 🎯 **Multi-Hazard Display** - Unified view of earthquake, flood, and rain risks

## Tech Stack

- **Framework**: Next.js 14 (React 18)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Maps**: Leaflet / React-Leaflet
- **Charts**: Recharts
- **API**: Axios
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- SPIRAL API running (default: http://localhost:8000)

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your configuration
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Run development server
npm run dev

# Open browser to http://localhost:3000
```

### Build for Production

```bash
# Build optimized production bundle
npm run build

# Start production server
npm start
```

## Configuration

Edit `.env.local` to configure:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Map Configuration (optional)
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here

# Feature Flags
NEXT_PUBLIC_ENABLE_NOTIFICATIONS=true
NEXT_PUBLIC_ENABLE_EARTHQUAKE=true
NEXT_PUBLIC_ENABLE_FLOOD=true
NEXT_PUBLIC_ENABLE_RAIN=true
```

## Project Structure

```
web-app/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── Header.tsx         # App header/navigation
│   ├── MapView.tsx        # Interactive map
│   ├── RiskPanel.tsx      # Risk assessment panel
│   ├── AlertsList.tsx     # Recent events list
│   └── StatsOverview.tsx  # Statistics cards
├── lib/                   # Utilities
│   └── api.ts            # API client
├── public/               # Static assets
├── package.json          # Dependencies
└── tailwind.config.js    # Tailwind configuration
```

## API Integration

The dashboard connects to the SPIRAL API backend:

### Endpoints Used

- `GET /api/v1/risk` - Fetch risk data for location
- `GET /api/v1/events/recent` - Get recent earthquake events
- `GET /api/v1/health` - Check API health

### Mock Data

If the API is unavailable, the dashboard falls back to mock data for demonstration purposes.

## Features in Detail

### Interactive Map

- Click anywhere to get risk assessment for that location
- Color-coded circles show risk levels:
  - 🟢 Green: LOW risk
  - 🟡 Yellow: MODERATE risk
  - 🟠 Orange: HIGH risk
  - 🔴 Red: EXTREME risk

### Risk Panel

- Current risk level (6-hour horizon)
- Individual hazard components:
  - Extreme rainfall probability
  - Flood exceedance probability
  - Earthquake MMI intensity
- Location coordinates
- Last update timestamp

### Recent Events

- Magnitude and location
- Time elapsed since event
- Depth information
- Color-coded by severity

### Statistics Overview

- Active monitoring cells
- Recent events count (24h)
- Active gravity wave features
- Model accuracy (R² score)

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker

```bash
# Build image
docker build -t spiral-web .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://your-api-url spiral-web
```

### Traditional Hosting

```bash
# Build
npm run build

# Copy .next/, public/, package.json to server
# Run: npm install --production && npm start
```

## Performance

- **Initial Load**: < 2s (optimized build)
- **API Calls**: Cached for 30s
- **Map Rendering**: Lazy-loaded components
- **Bundle Size**: ~300KB (gzipped)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Map Not Loading

- Ensure Leaflet CSS is imported
- Check browser console for errors
- Verify component is client-side rendered

### API Connection Failed

- Confirm SPIRAL API is running
- Check NEXT_PUBLIC_API_URL in .env.local
- Review CORS settings on API server
- Dashboard will use mock data as fallback

### Build Errors

- Clear `.next` cache: `rm -rf .next`
- Delete `node_modules` and reinstall
- Ensure Node.js version 18+

## Contributing

See main repository CONTRIBUTING.md

## License

MIT License - see LICENSE file

## Contact

- Issues: [GitHub Issues](https://github.com/yourusername/hazardstack/issues)
- Documentation: [spiral.readthedocs.io](https://spiral.readthedocs.io)

---

**Part of the SPIRAL Multi-Hazard Prediction System**
