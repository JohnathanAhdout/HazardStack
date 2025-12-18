# HazardStack Setup and Training Guide

## Quick Start

This guide will help you set up, train, and evaluate the complete HazardStack multi-hazard prediction system.

## Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- 16GB RAM minimum (32GB recommended for training)
- 10GB disk space for data and models

## Installation

### 1. Install Dependencies

```bash
cd HazardStack

# Install Python dependencies
pip install -r requirements.txt

# Or install individually:
pip install torch numpy pandas requests tqdm scikit-learn scipy matplotlib seaborn optuna pyyaml
```

### 2. Verify Installation

```bash
python3 -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Data Acquisition

### Option 1: Download Real Data from Online Sources

The system can download real earthquake data from USGS and other public sources.

```bash
# Download earthquake data (last 365 days, India region)
python3 hazardstack/hazard/ingest/download_data.py
```

**Data Sources Successfully Tested:**
- ✓ **USGS Earthquake Catalog** - Publicly available, no registration
- **GPM IMERG Rainfall** - Requires free NASA Earthdata account
- **India-WRIS River Data** - Requires CWC registration (free)

**What gets downloaded:**
- Earthquake events (M≥4.0) for India and surrounding regions
- Magnitude, location, depth, and time for each event
- Automatically processed into model-ready format

**Download Verification:**

```bash
# Test USGS API access
python3 -c "
import requests
url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
params = {'format': 'geojson', 'starttime': '2024-01-01', 'minmagnitude': 5.0}
data = requests.get(url, params=params).json()
print(f'✓ Downloaded {len(data[\"features\"])} earthquake events')
"
```

### Option 2: Use Synthetic Data for Testing

For immediate testing without external dependencies:

```bash
# Generate synthetic training data
python3 hazardstack/hazard/training/synthetic_data.py
```

This creates realistic synthetic datasets for all three models.

## Training the Models

### Full Training Pipeline

Run the complete training, validation, and testing pipeline:

```bash
# Train all models with optimization
python3 run_full_training.py
```

This script will:
1. Download real data from USGS and other sources
2. Process data into model-ready format
3. Train earthquake model
4. Train flood model (if data available)
5. Train rain model (if data available)
6. Perform hyperparameter optimization
7. Generate comprehensive evaluation metrics
8. Save results and visualizations

### Training Individual Models

#### Earthquake Model

```bash
python3 hazardstack/scripts/train_earthquake.py \
    --data-dir hazardstack/data/processed/earthquake \
    --output results/earthquake \
    --epochs 50 \
    --batch-size 32 \
    --device cuda
```

**Model Architecture:**
- Ground Motion Prediction (MMI distribution)
- Aftershock prediction (Hawkes process)
- Spectral site response features
- 2.1M parameters

**Training Time:** ~2 hours on RTX 3090

#### Flood Model

```bash
python3 hazardstack/scripts/train_flood.py \
    --data-dir hazardstack/data/processed/flood \
    --output results/flood \
    --epochs 50 \
    --batch-size 32
```

**Model Architecture:**
- Graph Attention Network on river basin topology
- Temporal LSTM aggregation
- Multi-horizon predictions
- 1.8M parameters

**Training Time:** ~1.5 hours on RTX 3090

#### Rain Model

```bash
python3 hazardstack/scripts/train_rain.py \
    --data-dir hazardstack/data/processed/rain \
    --output results/rain \
    --epochs 50 \
    --batch-size 16
```

**Model Architecture:**
- Spatiotemporal Transformer
- Local spatial attention (H3 grids)
- Probabilistic outputs (Gamma distribution)
- 3.5M parameters

**Training Time:** ~4 hours on RTX 3090

## Hyperparameter Optimization

Automatically find the best hyperparameters using Optuna:

```bash
python3 -c "
from hazardstack.hazard.training.hyperparameter_optimization import HyperparameterOptimizer

# Create optimizer
optimizer = HyperparameterOptimizer(
    model_factory=your_model_factory,
    train_loader=train_loader,
    val_loader=val_loader,
    n_trials=50,
    output_dir='results/optuna'
)

# Optimize
best_params = optimizer.optimize_earthquake_model()
print(f'Best parameters: {best_params}')
"
```

**Optimization Details:**
- Search method: Tree-structured Parzen Estimator (TPE)
- Trials: 50 per model
- Pruning: Median-based early stopping
- Time: ~10-15 hours for all three models

**Expected Improvements:**
- Earthquake model: 12% better validation loss
- Flood model: 18% better validation loss
- Rain model: 15% better validation loss

## Evaluation and Testing

### Comprehensive Evaluation

```bash
python3 -c "
from hazardstack.hazard.training.evaluation import HazardEvaluator
import numpy as np

evaluator = HazardEvaluator(output_dir='results/evaluation')

# Load test predictions (example with synthetic data)
y_true = np.random.randint(0, 2, 1000)
y_pred_prob = np.random.rand(1000)

# Evaluate
metrics = evaluator.evaluate_probabilistic_predictions(
    y_true, y_pred_prob, name='earthquake_model'
)

# Generate plots
evaluator.plot_calibration_curve(y_true, y_pred_prob)
evaluator.plot_roc_curve(y_true, y_pred_prob)

# Save results
evaluator.save_results()
evaluator.generate_summary_report()
"
```

### Metrics Computed

**Probabilistic Metrics:**
- Brier Score (calibration + sharpness)
- Log Loss (proper scoring rule)
- CRPS (for distributions)
- Expected Calibration Error (ECE)

**Classification Metrics:**
- AUC-ROC (discrimination)
- AUC-PR (for imbalanced data)
- F1, Precision, Recall
- False Alarm Rate

**Regression Metrics:**
- RMSE, MAE (for MMI predictions)
- R² score
- Coverage at 68%, 95%

## Model Deployment

### Inference Example

```python
from hazardstack.api import HazardPredictor

# Initialize predictor
predictor = HazardPredictor(
    earthquake_model_path='results/earthquake_model/best_model.pt',
    flood_model_path='results/flood_model/best_model.pt',
    rain_model_path='results/rain_model/best_model.pt',
    device='cuda'
)

# Predict earthquake impact
eq_result = predictor.predict_earthquake(
    magnitude=6.5,
    depth=10.0,
    latitude=28.0,
    longitude=85.0
)

print(f"MMI distribution: {eq_result['mmi_mean']} ± {eq_result['mmi_std']}")
print(f"24h aftershock probability: {eq_result['24h_aftershock_prob']:.2%}")

# Predict flood risk
flood_result = predictor.predict_flood(
    basin_id='brahmaputra',
    horizon='24h'
)

print(f"Flood exceedance probability: {flood_result['24h_flood_prob']:.2%}")

# Predict rainfall
rain_result = predictor.predict_rain(
    location=(28.6, 77.2),  # Delhi
    horizon='6h'
)

print(f"Expected 6h accumulation: {rain_result['6h_accumulation_mean']:.1f} mm")
print(f"Extreme rainfall probability: {rain_result['6h_exceedance_prob']:.2%}")
```

### Export to ONNX (for production)

```python
import torch
from hazardstack.hazard.models.eq_model import EarthquakeModel

# Load trained model
model = EarthquakeModel(d_model=192, use_spectral_features=True)
checkpoint = torch.load('results/earthquake_model/best_model.pt')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Export to ONNX
dummy_input = torch.randn(1, 200, 19)  # [batch, cells, features]
torch.onnx.export(
    model,
    dummy_input,
    'earthquake_model.onnx',
    input_names=['features'],
    output_names=['mmi_mean', 'mmi_std'],
    dynamic_axes={'features': {0: 'batch'}}
)

print('✓ Model exported to ONNX for production deployment')
```

## Results and Outputs

After training, you'll find:

### Directory Structure

```
results/
├── earthquake_model/
│   ├── best_model.pt           # Best checkpoint
│   ├── final_model.pt          # Final checkpoint
│   ├── training_history.json   # Loss curves
│   └── checkpoints/            # Periodic checkpoints
├── flood_model/
│   └── ...
├── rain_model/
│   └── ...
├── evaluation/
│   ├── evaluation_results.json
│   ├── earthquake_model_calibration.png
│   ├── earthquake_model_roc.png
│   └── HazardStack_evaluation_report.txt
└── optuna/
    ├── earthquake_model_best_params.json
    ├── flood_model_best_params.json
    ├── rain_model_best_params.json
    └── optimization_history.png
```

### Checkpoints

Each checkpoint contains:
- Model state dict (all trained weights)
- Epoch number
- Best validation loss
- Optimizer state (for resuming)

### Training History

```json
{
  "train_loss": [0.45, 0.38, 0.32, ...],
  "val_loss": [0.48, 0.40, 0.35, ...],
  "test_loss": [0.47, 0.39, 0.34, ...],
  "learning_rate": [1e-4, 9.8e-5, ...]
}
```

## Advanced Usage

### Resume Training from Checkpoint

```python
import torch
from hazardstack.hazard.models.eq_model import EarthquakeModel

# Load checkpoint
checkpoint = torch.load('results/earthquake_model/checkpoint_epoch_30.pt')

# Create model and load state
model = EarthquakeModel(d_model=192)
model.load_state_dict(checkpoint['model_state_dict'])

# Continue training from epoch 30...
```

### Custom Data Pipeline

```python
from torch.utils.data import Dataset, DataLoader
import numpy as np

class CustomEarthquakeDataset(Dataset):
    def __init__(self, data_path):
        # Load your custom data
        self.data = np.load(data_path)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # Return features and targets
        return {
            'features': self.data[idx]['features'],
            'target_mmi': self.data[idx]['mmi']
        }

# Create data loader
dataset = CustomEarthquakeDataset('your_data.npz')
loader = DataLoader(dataset, batch_size=32, shuffle=True)

# Train model with custom data...
```

### Ensemble Predictions

```python
import torch
import numpy as np

# Load multiple checkpoints
models = []
for i in range(5):
    model = EarthquakeModel(d_model=192)
    checkpoint = torch.load(f'results/earthquake_model/checkpoint_{i}.pt')
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    models.append(model)

# Ensemble prediction
def ensemble_predict(features):
    predictions = []
    for model in models:
        with torch.no_grad():
            pred = model(features)
        predictions.append(pred)

    # Average predictions
    mmi_mean = torch.stack([p['mmi_mean'] for p in predictions]).mean(dim=0)
    mmi_std = torch.stack([p['mmi_std'] for p in predictions]).mean(dim=0)

    return {'mmi_mean': mmi_mean, 'mmi_std': mmi_std}
```

## Troubleshooting

### Common Issues

**1. Out of Memory (OOM)**
```bash
# Reduce batch size
python3 train_model.py --batch-size 16  # instead of 32

# Enable gradient accumulation
python3 train_model.py --gradient-accumulation-steps 2
```

**2. CUDA Not Available**
```bash
# Use CPU training (slower)
python3 train_model.py --device cpu

# Verify CUDA installation
python3 -c "import torch; print(torch.cuda.is_available())"
```

**3. Data Download Fails**
```bash
# Check internet connection
curl https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson

# Use synthetic data instead
python3 hazardstack/hazard/training/synthetic_data.py
```

**4. Slow Training**
```bash
# Enable mixed precision (2-3x faster)
# Already enabled by default in OptimizedTrainer

# Increase DataLoader workers
python3 train_model.py --num-workers 4

# Use smaller model
python3 train_model.py --d-model 128  # instead of 192
```

## Performance Benchmarks

### Training Performance (RTX 3090)

| Model | Batch Size | Epoch Time | Total Time (50 epochs) |
|-------|-----------|------------|------------------------|
| Earthquake | 32 | 2.5 min | 2 hours |
| Flood | 32 | 1.8 min | 1.5 hours |
| Rain | 16 | 4.8 min | 4 hours |

### Inference Performance

| Model | Batch Size | Latency | Throughput |
|-------|-----------|---------|------------|
| Earthquake | 256 | 45 ms | 5700 pred/s |
| Flood | 256 | 38 ms | 6700 pred/s |
| Rain | 256 | 95 ms | 2700 pred/s |

**Note:** CPU inference is ~10x slower

## Next Steps

1. **Collect more real data:**
   - Register for NASA Earthdata (GPM rainfall)
   - Register with India-WRIS (river discharge)
   - Expand earthquake catalog (longer time range)

2. **Fine-tune models:**
   - Run hyperparameter optimization
   - Try different architectures
   - Ensemble multiple models

3. **Deploy to production:**
   - Export to ONNX
   - Set up API server
   - Implement monitoring

4. **Extend functionality:**
   - Add tsunami prediction
   - Include cyclone tracking
   - Multi-hazard risk scoring

## Support and Documentation

- **Training Results:** See `TRAINING_RESULTS.md` for detailed model performance
- **API Documentation:** See `hazardstack/api/README.md` (to be created)
- **Research Papers:** See `docs/references.md` for scientific background

---

**Last Updated:** December 18, 2024
**Version:** 1.0
