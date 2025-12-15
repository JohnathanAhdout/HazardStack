# HazardStack Quick Start Guide

Get the API running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- 4GB+ RAM available
- Internet connection for pulling images

## Steps

### 1. Clone and Navigate

```bash
git clone https://github.com/yourusername/hazardstack.git
cd hazardstack
```

### 2. Start Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL with PostGIS (port 5432)
- Redis (port 6379)
- HazardStack API (port 8000)

### 3. Verify Health

```bash
# Wait ~30 seconds for services to start, then:
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-15T21:00:00.000000",
  "system": {
    "cpu_percent": 5.2,
    "memory_percent": 45.3,
    "disk_percent": 62.1
  }
}
```

### 4. Try a Risk Query

Query risk for Mumbai (lat=19.07, lon=72.88):

```bash
curl "http://localhost:8000/api/v1/risk?lat=19.07&lon=72.88&radius_km=10&horizons=1h,6h,24h" | jq
```

### 5. Explore Interactive Docs

Open in browser: http://localhost:8000/docs

Try the `/api/v1/risk` endpoint interactively.

## What's Running?

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: postgresql://hazard:hazard@localhost:5432/hazardstack
- **Cache**: redis://localhost:6379

## Next Steps

### Add Real Data (Coming Soon)

```bash
# Download IMD rainfall data
python scripts/download_imd.py --years 2020-2024 --output data/raw/imd/

# Download MOSDAC satellite data
python scripts/download_mosdac.py --date 2024-12-15 --output data/raw/mosdac/

# Build H3 grid
python scripts/build_grid.py --config configs/india_v1.yaml
```

### Train Models

```bash
# Train rain model (requires data)
python scripts/train_rain.py --config configs/india_v1.yaml

# Evaluate
python scripts/evaluate.py --config configs/india_v1.yaml
```

### Stop Services

```bash
docker-compose down
```

To also remove data volumes:
```bash
docker-compose down -v
```

## Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. Port 8000 already in use -> change in docker-compose.yml
# 2. Database not ready -> wait longer, check postgres logs
```

### Out of memory

```bash
# Reduce batch sizes in configs/india_v1.yaml
# Or allocate more memory to Docker
```

### Can't connect to database

```bash
# Check postgres is running
docker-compose ps

# Reset database
docker-compose down -v
docker-compose up -d
```

## Production Deployment

For production, see:
- `infra/k8s/` for Kubernetes manifests
- `DEPLOYMENT.md` for full production guide (coming soon)

## Getting Help

- **Documentation**: See README.md
- **Issues**: https://github.com/yourusername/hazardstack/issues
- **Discussions**: https://github.com/yourusername/hazardstack/discussions
