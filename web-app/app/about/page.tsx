'use client'

import Header from '@/components/Header'
import { Shield, Zap, Globe, BarChart3, AlertTriangle, Cloud } from 'lucide-react'

export default function About() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white rounded-lg shadow-lg p-8 mb-6">
          <h1 className="text-4xl font-bold mb-4">About SPIRAL</h1>
          <p className="text-xl mb-2">
            Spatiotemporal Prediction and Impact-based Risk Analysis for Layered hazards
          </p>
          <p className="text-blue-100">
            An advanced multi-hazard early warning system for rapid risk assessment and disaster preparedness
          </p>
        </div>

        {/* Mission Statement */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Our Mission</h2>
          <p className="text-gray-700 leading-relaxed">
            SPIRAL combines cutting-edge machine learning, real-time satellite data, and geospatial analysis to provide
            accurate, actionable risk predictions for multiple natural hazards. Our goal is to save lives and reduce
            economic losses by enabling communities and organizations to prepare for and respond to disasters before
            they occur.
          </p>
        </div>

        {/* Key Features */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-4">Key Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <FeatureCard
              icon={<Zap className="w-8 h-8" />}
              title="Real-Time Predictions"
              description="Sub-hourly risk forecasts updated continuously using the latest observational data and ML models"
              color="bg-yellow-500"
            />
            <FeatureCard
              icon={<Globe className="w-8 h-8" />}
              title="Multi-Hazard Coverage"
              description="Integrated monitoring for earthquakes, floods, extreme rainfall, and compound hazard events"
              color="bg-blue-500"
            />
            <FeatureCard
              icon={<BarChart3 className="w-8 h-8" />}
              title="Calibrated Probabilities"
              description="Rigorous statistical calibration ensures reliable probability estimates for decision-making"
              color="bg-green-500"
            />
            <FeatureCard
              icon={<Shield className="w-8 h-8" />}
              title="Impact-Based Warnings"
              description="Risk assessments tailored to exposure and vulnerability, not just hazard intensity"
              color="bg-purple-500"
            />
            <FeatureCard
              icon={<Cloud className="w-8 h-8" />}
              title="Satellite Data Integration"
              description="Near-real-time processing of INSAT-3D/3DR imagery for nowcasting extreme rainfall"
              color="bg-cyan-500"
            />
            <FeatureCard
              icon={<AlertTriangle className="w-8 h-8" />}
              title="Automated Alerts"
              description="Threshold-based notifications and bulletins delivered instantly when risks exceed predefined levels"
              color="bg-red-500"
            />
          </div>
        </div>

        {/* Technology Stack */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Technology Stack</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-bold text-lg mb-2">Data Sources</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                <li>INSAT-3D/3DR satellite imagery (IMD)</li>
                <li>ERA5 reanalysis data (ECMWF)</li>
                <li>USGS & NCS seismic networks</li>
                <li>CWC flood bulletins</li>
                <li>GDACS disaster alerts</li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-2">Core Technologies</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                <li>PyTorch & LightGBM for ML models</li>
                <li>H3 hexagonal grid system (Uber)</li>
                <li>FastAPI backend with Redis caching</li>
                <li>Next.js frontend with Leaflet maps</li>
                <li>Docker containerization</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Model Capabilities */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Model Capabilities</h2>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h3 className="font-bold mb-1">Extreme Rainfall Nowcasting</h3>
              <p className="text-gray-700">
                Detects gravity wave signatures in satellite imagery to predict flash flood-triggering rainfall
                events 1-6 hours in advance with 85%+ accuracy
              </p>
            </div>
            <div className="border-l-4 border-orange-500 pl-4">
              <h3 className="font-bold mb-1">Flood Risk Forecasting</h3>
              <p className="text-gray-700">
                Combines antecedent precipitation, soil moisture, topography, and rainfall forecasts to predict
                flood exceedance probabilities at 12-24 hour horizons
              </p>
            </div>
            <div className="border-l-4 border-red-500 pl-4">
              <h3 className="font-bold mb-1">Seismic Shaking Assessment</h3>
              <p className="text-gray-700">
                Real-time integration of earthquake data from NCS and USGS with Ground Motion Prediction Equations
                (GMPEs) to estimate Modified Mercalli Intensity (MMI) at any location
              </p>
            </div>
            <div className="border-l-4 border-purple-500 pl-4">
              <h3 className="font-bold mb-1">Aftershock Forecasting</h3>
              <p className="text-gray-700">
                Applies Omori's law and ETAS models to calculate aftershock probabilities following significant
                mainshock events
              </p>
            </div>
          </div>
        </div>

        {/* Use Cases */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Use Cases</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h3 className="font-bold mb-2">Emergency Management</h3>
              <p className="text-sm text-gray-700">
                Pre-positioning resources, activating response protocols, and issuing public warnings based on
                probabilistic risk forecasts
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <h3 className="font-bold mb-2">Infrastructure Operations</h3>
              <p className="text-sm text-gray-700">
                Protecting critical assets (dams, bridges, power plants) by triggering preventive measures when
                risk thresholds are exceeded
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <h3 className="font-bold mb-2">Humanitarian Planning</h3>
              <p className="text-sm text-gray-700">
                Identifying vulnerable communities in advance of hazard events to enable targeted evacuation and
                relief operations
              </p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <h3 className="font-bold mb-2">Research & Development</h3>
              <p className="text-sm text-gray-700">
                Providing high-resolution historical and forecast data for climate studies, hazard modeling, and
                risk assessment research
              </p>
            </div>
          </div>
        </div>

        {/* Contact & Links */}
        <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold mb-4">Get Involved</h2>
          <p className="mb-4">
            SPIRAL is an open-source project. We welcome contributions, feedback, and collaborations from
            researchers, developers, and disaster risk reduction practitioners.
          </p>
          <div className="flex gap-4 flex-wrap">
            <a
              href="https://github.com/JohnathanAhdout/SPIRAL"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-white text-gray-800 rounded-md hover:bg-gray-100 transition"
            >
              View on GitHub
            </a>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition">
              Documentation
            </button>
            <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition">
              API Reference
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

function FeatureCard({ icon, title, description, color }: any) {
  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
      <div className={`${color} text-white w-12 h-12 rounded-lg flex items-center justify-center mb-4`}>
        {icon}
      </div>
      <h3 className="font-bold text-lg mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  )
}
