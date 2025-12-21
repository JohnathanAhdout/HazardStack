import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Text, TouchableOpacity } from 'react-native';
import MapView, { Marker, Circle, PROVIDER_DEFAULT } from 'react-native-maps';
import { useLocation } from '../context/LocationContext';
import { fetchRiskData } from '../services/api';

export default function MapScreen() {
  const { location } = useLocation();
  const [riskData, setRiskData] = useState<any>(null);
  const [selectedCell, setSelectedCell] = useState<any>(null);

  const defaultRegion = {
    latitude: 20.5937,
    longitude: 78.9629,
    latitudeDelta: 15,
    longitudeDelta: 15,
  };

  useEffect(() => {
    if (location) {
      loadRiskData(location.coords.latitude, location.coords.longitude);
    }
  }, [location]);

  const loadRiskData = async (lat: number, lon: number) => {
    try {
      const data = await fetchRiskData(lat, lon, 50);
      setRiskData(data);
    } catch (error) {
      console.error('Error loading risk data:', error);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return '#22C55E';
      case 'MODERATE': return '#F59E0B';
      case 'HIGH': return '#EF4444';
      case 'EXTREME': return '#7C2D12';
      default: return '#6B7280';
    }
  };

  const handleMapPress = (event: any) => {
    const { latitude, longitude } = event.nativeEvent.coordinate;
    loadRiskData(latitude, longitude);
  };

  return (
    <View style={styles.container}>
      <MapView
        style={styles.map}
        provider={PROVIDER_DEFAULT}
        initialRegion={defaultRegion}
        onPress={handleMapPress}
      >
        {/* User location marker */}
        {location && (
          <Marker
            coordinate={{
              latitude: location.coords.latitude,
              longitude: location.coords.longitude,
            }}
            title="Your Location"
            pinColor="#0066CC"
          />
        )}

        {/* Risk circles */}
        {riskData?.cells?.map((cell: any, idx: number) => (
          <Circle
            key={idx}
            center={{
              latitude: cell.centroid[0],
              longitude: cell.centroid[1],
            }}
            radius={5000}
            fillColor={`${getRiskColor(cell.risk['6h']?.level)}40`}
            strokeColor={getRiskColor(cell.risk['6h']?.level)}
            strokeWidth={2}
            onPress={() => setSelectedCell(cell)}
          />
        ))}
      </MapView>

      {/* Info Card */}
      {selectedCell && (
        <View style={styles.infoCard}>
          <View style={styles.infoHeader}>
            <Text style={styles.infoTitle}>Risk Information</Text>
            <TouchableOpacity onPress={() => setSelectedCell(null)}>
              <Text style={styles.closeButton}>✕</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.infoContent}>
            <View style={[styles.riskBadge, { backgroundColor: getRiskColor(selectedCell.risk['6h']?.level) }]}>
              <Text style={styles.riskBadgeText}>{selectedCell.risk['6h']?.level}</Text>
            </View>
            <Text style={styles.infoText}>
              Score: {(selectedCell.risk['6h']?.score * 100).toFixed(1)}%
            </Text>
            <Text style={styles.infoCoords}>
              {selectedCell.centroid[0].toFixed(4)}°N, {selectedCell.centroid[1].toFixed(4)}°E
            </Text>
          </View>
        </View>
      )}

      {/* Legend */}
      <View style={styles.legend}>
        <Text style={styles.legendTitle}>Risk Levels</Text>
        <LegendItem color="#22C55E" label="Low" />
        <LegendItem color="#F59E0B" label="Moderate" />
        <LegendItem color="#EF4444" label="High" />
        <LegendItem color="#7C2D12" label="Extreme" />
      </View>
    </View>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <View style={styles.legendItem}>
      <View style={[styles.legendColor, { backgroundColor: color }]} />
      <Text style={styles.legendLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  infoCard: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  infoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  closeButton: {
    fontSize: 20,
    color: '#6B7280',
  },
  infoContent: {
    gap: 8,
  },
  riskBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  riskBadgeText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  infoText: {
    fontSize: 14,
    color: '#374151',
  },
  infoCoords: {
    fontSize: 12,
    color: '#6B7280',
  },
  legend: {
    position: 'absolute',
    top: 20,
    right: 20,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
    elevation: 3,
  },
  legendTitle: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
    color: '#111827',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  legendColor: {
    width: 16,
    height: 16,
    borderRadius: 3,
    marginRight: 8,
  },
  legendLabel: {
    fontSize: 11,
    color: '#374151',
  },
});
