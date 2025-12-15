// HazardStack Web App JavaScript

const API_BASE = 'http://localhost:8000/api/v1';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadSystemStats();
    setupEventListeners();
    loadRecentEvents();
});

// Setup event listeners
function setupEventListeners() {
    const queryBtn = document.getElementById('queryBtn');
    if (queryBtn) {
        queryBtn.addEventListener('click', queryRisk);
    }

    const exampleBtn = document.getElementById('exampleBtn');
    if (exampleBtn) {
        exampleBtn.addEventListener('click', loadExample);
    }
}

// Load system stats
async function loadSystemStats() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            document.getElementById('systemStatus').textContent = 'ONLINE';
            document.getElementById('systemStatus').className = 'stat-value';
            updateStat('cpuUsage', `${data.system.cpu_percent.toFixed(1)}%`);
            updateStat('memoryUsage', `${data.system.memory_percent.toFixed(1)}%`);
            updateStat('lastUpdate', new Date(data.timestamp).toLocaleTimeString());
        }
    } catch (error) {
        console.error('Failed to load system stats:', error);
        document.getElementById('systemStatus').textContent = 'OFFLINE';
        document.getElementById('systemStatus').style.color = '#ef4444';
    }
}

// Update stat value
function updateStat(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// Load example location (Mumbai)
function loadExample() {
    document.getElementById('latitude').value = '19.07';
    document.getElementById('longitude').value = '72.88';
    document.getElementById('radius').value = '10';
}

// Query risk
async function queryRisk() {
    const lat = document.getElementById('latitude').value;
    const lon = document.getElementById('longitude').value;
    const radius = document.getElementById('radius').value;
    const horizons = document.getElementById('horizons').value;

    if (!lat || !lon || !radius) {
        alert('Please fill in all fields');
        return;
    }

    const spinner = document.getElementById('spinner');
    const resultsDiv = document.getElementById('results');

    spinner.classList.add('active');
    resultsDiv.classList.remove('active');

    try {
        const response = await fetch(
            `${API_BASE}/risk?lat=${lat}&lon=${lon}&radius_km=${radius}&horizons=${horizons}`
        );
        const data = await response.json();

        spinner.classList.remove('active');
        displayResults(data);
    } catch (error) {
        console.error('Query failed:', error);
        spinner.classList.remove('active');
        alert('Failed to query risk. Make sure the API is running (docker-compose up -d)');
    }
}

// Display results
function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    const riskCardsDiv = document.getElementById('riskCards');

    if (!data.cells || data.cells.length === 0) {
        riskCardsDiv.innerHTML = '<p>No data available for this location.</p>';
        resultsDiv.classList.add('active');
        return;
    }

    // Clear previous results
    riskCardsDiv.innerHTML = '';

    // Create cards for each horizon
    const cell = data.cells[0]; // Show first cell as example
    const horizons = Object.keys(cell.risk);

    horizons.forEach(horizon => {
        const risk = cell.risk[horizon];
        const card = createRiskCard(horizon, risk, cell.components);
        riskCardsDiv.appendChild(card);
    });

    resultsDiv.classList.add('active');
}

// Create risk card
function createRiskCard(horizon, risk, components) {
    const card = document.createElement('div');
    card.className = 'risk-card';

    const scorePercent = (risk.score * 100).toFixed(0);

    card.innerHTML = `
        <div class="risk-header">
            <div>
                <h3>${horizon} Forecast</h3>
                <span class="risk-level ${risk.level}">${risk.level}</span>
            </div>
            <div class="risk-score">${scorePercent}%</div>
        </div>
        <div class="risk-components">
            <h4 style="margin-bottom: 0.75rem; font-size: 0.9rem;">Risk Components:</h4>
            ${components.rain_extreme_6h ? `
                <div class="component">
                    <span class="component-label">🌧️ Rain (6h):</span>
                    <span class="component-value">${(components.rain_extreme_6h * 100).toFixed(0)}%</span>
                </div>
            ` : ''}
            ${components.flood_12h ? `
                <div class="component">
                    <span class="component-label">🌊 Flood (12h):</span>
                    <span class="component-value">${(components.flood_12h * 100).toFixed(0)}%</span>
                </div>
            ` : ''}
            ${components.mmi_mean !== undefined ? `
                <div class="component">
                    <span class="component-label">⚡ Shaking (MMI):</span>
                    <span class="component-value">${components.mmi_mean.toFixed(1)}</span>
                </div>
            ` : ''}
            ${components.aftershock_24h ? `
                <div class="component">
                    <span class="component-label">📊 Aftershock (24h):</span>
                    <span class="component-value">${(components.aftershock_24h * 100).toFixed(0)}%</span>
                </div>
            ` : ''}
        </div>
    `;

    return card;
}

// Load recent events
async function loadRecentEvents() {
    try {
        const response = await fetch(`${API_BASE}/events/recent?hours=24`);
        const data = await response.json();

        updateStat('recentEvents', data.earthquakes.length + data.flood_bulletins.length);
    } catch (error) {
        console.error('Failed to load recent events:', error);
    }
}

// Auto-refresh stats every 30 seconds
setInterval(() => {
    loadSystemStats();
    loadRecentEvents();
}, 30000);
