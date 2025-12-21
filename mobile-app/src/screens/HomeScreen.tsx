import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useLocation } from '../context/LocationContext';
import { fetchRiskData, fetchRecentEvents } from '../services/api';
import RiskCard from '../components/RiskCard';
import StatCard from '../components/StatCard';
import EventCard from '../components/EventCard';

export default function HomeScreen() {
  const { location } = useLocation();
  const [riskData, setRiskData] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [location]);

  const loadData = async () => {
    if (!location) return;

    setLoading(true);
    try {
      const [risk, recentEvents] = await Promise.all([
        fetchRiskData(location.coords.latitude, location.coords.longitude),
        fetchRecentEvents(24, 3.0),
      ]);
      setRiskData(risk);
      setEvents(recentEvents);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const mainCell = riskData?.cells?.[0];
  const risk6h = mainCell?.risk?.['6h'];
  const components = mainCell?.components;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Multi-Hazard Prediction</Text>
        <Text style={styles.headerSubtitle}>
          {location
            ? `${location.coords.latitude.toFixed(2)}°N, ${location.coords.longitude.toFixed(2)}°E`
            : 'Location unavailable'}
        </Text>
      </View>

      {/* Current Risk */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Current Risk Level</Text>
        <RiskCard level={risk6h?.level || 'LOW'} score={risk6h?.score || 0} />
      </View>

      {/* Statistics */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>System Status</Text>
        <View style={styles.statsGrid}>
          <StatCard
            title="Active Cells"
            value={riskData?.cells?.length || 0}
            color="#0066CC"
          />
          <StatCard
            title="Recent Events"
            value={events.length}
            color="#F59E0B"
          />
          <StatCard
            title="GW Features"
            value="24"
            color="#06B6D4"
          />
          <StatCard
            title="Accuracy"
            value="94.5%"
            color="#22C55E"
          />
        </View>
      </View>

      {/* Hazard Components */}
      {components && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Hazard Components</Text>
          <View style={styles.componentsContainer}>
            {components.rain_extreme_6h && (
              <ComponentBar
                label="Extreme Rain (6h)"
                value={components.rain_extreme_6h}
                color="#3B82F6"
              />
            )}
            {components.flood_12h && (
              <ComponentBar
                label="Flood (12h)"
                value={components.flood_12h}
                color="#06B6D4"
              />
            )}
            {components.mmi_mean && (
              <ComponentBar
                label="Earthquake MMI"
                value={components.mmi_mean / 10}
                color="#EF4444"
              />
            )}
          </View>
        </View>
      )}

      {/* Recent Events */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Events</Text>
          <Text style={styles.sectionSubtitle}>Last 24 hours</Text>
        </View>
        {events.slice(0, 5).map((event, idx) => (
          <EventCard key={idx} event={event} />
        ))}
        {events.length === 0 && (
          <Text style={styles.emptyText}>No recent events</Text>
        )}
      </View>
    </ScrollView>
  );
}

function ComponentBar({ label, value, color }: any) {
  return (
    <View style={styles.componentBar}>
      <Text style={styles.componentLabel}>{label}</Text>
      <View style={styles.barContainer}>
        <View style={[styles.barFill, { width: `${value * 100}%`, backgroundColor: color }]} />
      </View>
      <Text style={styles.componentValue}>{(value * 100).toFixed(0)}%</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    backgroundColor: '#0066CC',
    padding: 20,
    paddingTop: 10,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#BFDBFE',
  },
  section: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#6B7280',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  componentsContainer: {
    gap: 12,
  },
  componentBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    gap: 12,
  },
  componentLabel: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
  },
  barContainer: {
    flex: 2,
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
  },
  componentValue: {
    width: 50,
    textAlign: 'right',
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  emptyText: {
    textAlign: 'center',
    color: '#9CA3AF',
    padding: 20,
  },
});
