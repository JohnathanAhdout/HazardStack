import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface RiskCardProps {
  level: string;
  score: number;
}

export default function RiskCard({ level, score }: RiskCardProps) {
  const getRiskColor = () => {
    switch (level) {
      case 'LOW': return '#22C55E';
      case 'MODERATE': return '#F59E0B';
      case 'HIGH': return '#EF4444';
      case 'EXTREME': return '#7C2D12';
      default: return '#6B7280';
    }
  };

  return (
    <View style={[styles.container, { borderLeftColor: getRiskColor() }]}>
      <View style={styles.header}>
        <View style={[styles.badge, { backgroundColor: getRiskColor() }]}>
          <Text style={styles.badgeText}>{level}</Text>
        </View>
        <Text style={styles.score}>{(score * 100).toFixed(1)}% Risk</Text>
      </View>
      <Text style={styles.description}>
        {getDescription(level)}
      </Text>
    </View>
  );
}

function getDescription(level: string): string {
  switch (level) {
    case 'LOW':
      return 'Normal conditions. Stay informed about weather updates.';
    case 'MODERATE':
      return 'Potential hazards possible. Monitor alerts and be prepared.';
    case 'HIGH':
      return 'Hazardous conditions likely. Take precautionary measures.';
    case 'EXTREME':
      return 'Severe hazards imminent. Follow official safety guidelines immediately.';
    default:
      return 'Risk assessment unavailable.';
  }
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  badgeText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  score: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  description: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
});
