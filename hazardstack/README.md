# HazardStack: India Multi-Hazard Nowcasting System

**Monsoon Flood + Earthquake Impact + Aftershock Prediction with Novel Readability Architecture**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

HazardStack is a **rigorous, publication-quality** multi-hazard nowcasting and forecasting system tailored for India. Instead of claiming to "predict earthquakes" (which the field does not support), it provides what emergency systems actually need:

- **Probabilistic hazard nowcasting + forecasting** with calibrated uncertainties
- **Real-time alerting** with geofencing
- **Explainable predictions** via a novel "readability layer" architecture

### What This System Does

1. **Extreme Rainfall Nowcast & Forecast** (0–6h nowcast, 6–72h forecast)
   - Calibrated probabilities of extreme rainfall events
   - Gamma/LogNormal distribution predictions for accumulation

2. **Riverine Flood Exceedance** (basin-wise)
   - Discharge/water-level threshold exceedance probabilities
   - Graph neural network propagation along river topology

3. **Earthquake Impact** (real-time shaking intensity + aftershock probability)
   - **NOT deterministic earthquake prediction** (scientifically unsupported)
   - Real-time shaking intensity estimation (MMI) from detected events
   - Aftershock probability forecasting (1h/24h/7d horizons)

### Novel Architecture: Readability Layer

The core innovation is a **readability-first architecture** that converts messy, noisy spatiotemporal data streams into stable, interpretable representations:

- **Causal State Space Model (SSM)** for streaming temporal sequences
- **Mask-aware denoising** with uncertainty estimation
- **Instability scoring** for attention weighting
- **Physics-guided constraints** (monotonicity, temporal smoothness)

## Why India-Tailored?

- Uses **IMD India-only long rainfall record** (1901–2024) for monsoon climatology
- Integrates **MOSDAC GSMaP_ISRO** tuned for Indian subcontinent
- Leverages **CWC flood forecasting** ecosystem
- Anchored to **NCS** (National Center for Seismology) for earthquakes
- Handles **INCOIS tsunami bulletins** (not ML fantasy)

## Project Structure

```
hazardstack/
├── README.md                    # This file
├── pyproject.toml              # Python dependencies
├── docker-compose.yml          # Docker orchestration
├── configs/
│   └── india_v1.yaml          # Main configuration
├── data/
│   ├── raw/                   # Raw data downloads
│   ├── interim/               # Intermediate processing
│   └── processed/             # Final tokenized datasets
├── hazard/
│   ├── common/                # Utilities (geo, metrics, calibration, losses)
│   ├── ingest/                # Data ingestion clients
│   ├── features/              # Feature engineering
│   ├── models/
│   │   ├── readability/       # Novel readability layer
│   │   ├── rain_model.py      # Rain nowcast/forecast
│   │   ├── flood_model.py     # Flood exceedance (GNN)
│   │   └── eq_model.py        # Earthquake impact + aftershock
│   ├── training/              # Training infrastructure
│   └── serving/               # Inference + risk computation
├── api/
│   ├── main.py               # FastAPI application
│   └── routes/               # API endpoints
├── scripts/
│   ├── download_*.py         # Data download scripts
│   ├── train_*.py            # Training scripts
│   └── evaluate.py           # Evaluation
└── infra/
    ├── docker/               # Dockerfiles
    └── k8s/                  # Kubernetes manifests
```

## Data Sources

### Monsoon / Rainfall

- **IMD daily gridded rainfall** (0.25°, 1901–2024): [imdpune.gov.in](https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html)
- **MOSDAC GSMaP_ISRO hourly** (0.1°, ~2000–now): [mosdac.gov.in](https://www.mosdac.gov.in/gsmap-isro-rain)
- **IMDAA regional reanalysis** (~12 km): [rcc.imdpune.gov.in](https://rcc.imdpune.gov.in/download.php)

### Flood

- **CWC flood forecasting portal**: [ffs.india-water.gov.in](https://ffs.india-water.gov.in)
- **CWC river discharge telemetry** (hourly): [nwdp.nwic.gov.in](https://nwdp.nwic.gov.in/dataset/river-discharge-telemetry-hourly-central-water-commission-cwc)
- **NRSC/ISRO Bhuvan flood products**: [bhuvan-app1.nrsc.gov.in](https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php)
- **Copernicus GloFAS** (global baseline): [ewds.climate.copernicus.eu](https://ewds.climate.copernicus.eu/datasets/cems-glofas-forecast)

### Earthquakes

- **NCS earthquake catalog**: [seismo.gov.in](https://seismo.gov.in/data-portal)
- **USGS event feeds** (global augmentation): [earthquake.usgs.gov](https://earthquake.usgs.gov/fdsnws/event/1/)
- **INCOIS tsunami bulletins**: [tsunami.incois.gov.in](https://tsunami.incois.gov.in)

## Installation

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (for containerized deployment)
- PostgreSQL with PostGIS (for spatial data)
- Redis (for caching)

### Quick Start with Docker

```bash
# Clone repository
git clone https://github.com/yourusername/hazardstack.git
cd hazardstack

# Copy environment template
cp .env.example .env

# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/api/v1/health
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

### Manual Installation

```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Set up configuration
cp .env.example .env
# Edit .env with your settings

# Initialize database (TODO: add migration scripts)
# python scripts/init_db.py

# Run API locally
python api/main.py
```

## Configuration

Edit `configs/india_v1.yaml` to customize:

- **Grid resolution** (H3 level 4 = ~5-10 km, level 5 = ~2-3 km)
- **Forecast horizons** (e.g., ["1h", "6h", "12h", "24h", "72h"])
- **Model hyperparameters** (transformer layers, GNN depth, etc.)
- **Risk thresholds** (LOW, MODERATE, HIGH, EXTREME cutoffs)
- **Data source URLs** and update intervals

## Usage

### API Endpoints

#### 1. Get Multi-Hazard Risk

```bash
curl "http://localhost:8000/api/v1/risk?lat=19.07&lon=72.88&radius_km=10&horizons=1h,6h,24h"
```

Response:
```json
{
  "query": {"lat": 19.07, "lon": 72.88, "radius_km": 10},
  "generated_at": "2025-12-15T21:30:00Z",
  "cells": [
    {
      "h3_id": "852a1073fffffff",
      "centroid": [19.08, 72.87],
      "risk": {
        "1h": {"level": "MODERATE", "score": 0.43},
        "6h": {"level": "HIGH", "score": 0.71}
      },
      "components": {
        "rain_extreme_6h": 0.68,
        "flood_12h": 0.22,
        "mmi_mean": 1.2,
        "aftershock_24h": 0.03
      },
      "explain": [
        {"feature": "R_acc_3h", "impact": 0.19},
        {"feature": "API_3d", "impact": 0.12}
      ]
    }
  ]
}
```

#### 2. Get Recent Events

```bash
curl "http://localhost:8000/api/v1/events/recent?hours=24&min_magnitude=3.0"
```

#### 3. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Training Models

```bash
# Train rain model
python scripts/train_rain.py --config configs/india_v1.yaml --output models/rain_v1.pt

# Train flood model
python scripts/train_flood.py --config configs/india_v1.yaml --output models/flood_v1.pt

# Train earthquake model
python scripts/train_eq.py --config configs/india_v1.yaml --output models/eq_v1.pt

# Export to ONNX for inference
python scripts/export_onnx.py --model models/rain_v1.pt --output models/rain_v1.onnx
```

### Evaluation

```bash
# Run comprehensive evaluation
python scripts/evaluate.py \
  --config configs/india_v1.yaml \
  --test-data data/processed/test/ \
  --models models/ \
  --output results/evaluation_report.json

# Metrics computed:
# - Brier score, log loss, CRPS
# - Expected Calibration Error (ECE)
# - Lead time at fixed false alarm rates
# - Regional backtesting (Western Ghats, Brahmaputra, etc.)
```

## Model Architecture Details

### Readability Layer

**Purpose**: Transform noisy streaming data into stable, interpretable tokens

**Components**:
1. **Causal Denoiser** (dilated convolutions with GLU gating)
   - Handles missing data via mask-aware processing
   - Outputs denoised features + uncertainty estimates

2. **Instability Scoring**
   - Computes "readability" score for each token
   - Used to downweight unreliable inputs in attention

3. **Token Mixer**
   - Combines features with positional/spatial/seasonal embeddings
   - Projects to d_model dimension for transformers

**Implementation**: `hazard/models/readability/`

### Rain Model

**Architecture**: Spatiotemporal Transformer

- **Temporal attention** across time for each cell
- **Local spatial attention** over k-ring H3 neighbors
- **Distribution heads**: Gamma/LogNormal parameters
- **Exceedance heads**: Binary classification for threshold exceedance

**Horizons**: 1h, 6h, 12h, 24h, 72h

**Implementation**: `hazard/models/rain_model.py`

### Flood Model

**Architecture**: Graph Neural Network + Temporal Aggregator

- **Basin topology** as directed graph (upstream → downstream)
- **Graph Attention Layers** for message passing
- **LSTM** for temporal aggregation (72h lookback)
- **Binary exceedance** prediction per basin

**Horizons**: 12h, 24h

**Implementation**: `hazard/models/flood_model.py`

### Earthquake Model

**Two submodules**:

1. **Ground Motion Model** (GMPE-style MLP)
   - Inputs: magnitude, depth, distance, site proxy
   - Outputs: MMI distribution (Gaussian mean + std)

2. **Neural Hawkes Process** (aftershock forecasting)
   - LSTM-based intensity function λ(t)
   - Outputs: P(aftershock ≥ M3.5 in next 1h/24h/7d)

**Implementation**: `hazard/models/eq_model.py`

## Physics-Guided Features

### Rain Features

- **Antecedent Precipitation Index (API)**: `Σ α^i * rain_{t-i}` with α=0.85
- **Climatological percentiles** (p95, p99) from IMD 1901–2024
- **Monsoon phase** encoding (pre-monsoon, SW monsoon, post-monsoon, winter)
- **Storm motion** (optical flow on satellite rainfall)

### Flood Features

- **Basin-aggregated rainfall** (area-weighted from cells)
- **API_7d, API_14d, API_30d** for soil saturation proxy
- **Upstream accumulation** via basin graph topology
- **Static basin descriptors** (area, slope, drainage density)

### Earthquake Features

- **ETAS-style clustering** features (event rate in past 1h/6h/24h)
- **Distance metrics** (hypocentral, epicentral)
- **Site proxy** (Vs30 or elevation + geology fallback)
- **Temporal decay** weighting: exp(-Δt/τ)

## Rigorous Evaluation

### Metrics

- **Probabilistic**: Brier score, log loss, CRPS
- **Calibration**: Expected Calibration Error (ECE), reliability diagrams
- **Operational**: Lead time at fixed false alarm rate (10%, 20%, 30%)

### Regional Backtesting

- **Western Ghats**: Orographic rain extremes
- **Indo-Gangetic Plains**: Riverine floods
- **Brahmaputra/NE**: Flash floods + landslides
- **Coastal**: Cyclone-driven deluges (Odisha/AP/TN)
- **Seismic**: Himalayan belt, NE India, Andaman-Nicobar

### Baselines

- **Rain**: Persistence + optical flow advection, ConvLSTM/UNet
- **Flood**: Linear reservoir model, GloFAS comparator
- **Earthquake**: Omori law vs. ETAS vs. Neural Hawkes

## Mobile App Integration

**Backend**: FastAPI with geofencing queries

**Client** (Flutter/React Native):
- Offline-first risk tiles (cached)
- Push notifications via FCM/APNS
- Alert format:
  ```
  "High flood risk (70%) in Brahmaputra basin within 12h.
   Follow CWC flood warnings: [link]"
  ```
- **Uncertainty included** in all alerts
- **Links to official sources** (IMD, CWC, NCS, INCOIS)

## Responsible AI Practices

### What We Do

✅ Calibrated probabilistic forecasts (not point predictions)
✅ Uncertainty quantification
✅ Explainable predictions (top-k feature contributions)
✅ Links to official government sources
✅ Conservative handling of missing data
✅ Temporal smoothness regularization (prevents alert jitter)

### What We Do NOT Do

❌ Claim deterministic earthquake prediction
❌ Make forecasts without uncertainty bounds
❌ Override official government warnings
❌ Use models without calibration
❌ Deploy without backtesting on historical disasters

## Contributing

We welcome contributions! Areas where help is needed:

1. **Data ingestion clients** (MOSDAC, CWC, NCS APIs)
2. **Feature engineering** (more physics-guided proxies)
3. **Mobile app** (Flutter implementation)
4. **Basin topology** (Indian river network graph)
5. **Evaluation** (more regional case studies)
6. **Documentation** (tutorials, examples)

See `CONTRIBUTING.md` for guidelines.

## Roadmap

### Phase 1: Monsoon Corridor (MVP)
- [ ] Complete rain nowcast model training
- [ ] Integrate IMD + MOSDAC data pipelines
- [ ] Deploy for Kerala Western Ghats (one region)
- [ ] Backtesting on 2018 Kerala floods

### Phase 2: Flood Integration
- [ ] Build CWC data ingestion
- [ ] Construct basin graph for major rivers
- [ ] Train flood GNN model
- [ ] Validate on Brahmaputra/Ganga basins

### Phase 3: Earthquake + Full India
- [ ] NCS real-time event ingestion
- [ ] Train GMPE + Hawkes models on Indian catalog
- [ ] Full India H3 grid deployment
- [ ] Mobile app beta release

### Phase 4: Publication & Scaling
- [ ] Submit to journal (e.g., *Environmental Data Science*, *Geoscientific Model Development*)
- [ ] Benchmark against operational systems
- [ ] State-level pilots with disaster management authorities
- [ ] Open data release (tokenized datasets)

## Citation

If you use HazardStack in your research, please cite:

```bibtex
@software{hazardstack2025,
  title={HazardStack: India Multi-Hazard Nowcasting with Readability Architecture},
  author={[Your Name]},
  year={2025},
  url={https://github.com/yourusername/hazardstack}
}
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- **IMD** (India Meteorological Department) for gridded rainfall data
- **MOSDAC/ISRO** for GSMaP_ISRO satellite rainfall
- **CWC** (Central Water Commission) for flood monitoring data
- **NCS** (National Center for Seismology) for earthquake catalog
- **INCOIS** for tsunami early warning bulletins
- **NRSC/ISRO** for disaster monitoring products

## Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/hazardstack/issues)
- **Email**: your.email@example.com
- **Documentation**: [Full docs](https://hazardstack.readthedocs.io) (coming soon)

---

**Disclaimer**: This is a research prototype. For official disaster warnings, always consult:
- Rain/cyclone: [IMD](https://mausam.imd.gov.in)
- Floods: [CWC](https://ffs.india-water.gov.in)
- Earthquakes: [NCS](https://seismo.gov.in)
- Tsunami: [INCOIS](https://tsunami.incois.gov.in)
