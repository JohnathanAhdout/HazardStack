import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { formatDistanceToNow } from 'date-fns';

interface EventCardProps {
  event: any;
  detailed?: boolean;
}

export default function EventCard({ event, detailed = false }: EventCardProps) {
  const getMagnitudeColor = (mag: number) => {
    if (mag >= 7) return '#7C2D12';
    if (mag >= 6) return '#EF4444';
    if (mag >= 5) return '#F59E0B';
    return '#22C55E';
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={[styles.magnitudeBadge, { backgroundColor: getMagnitudeColor(event.magnitude) }]}>
          <Text style={styles.magnitudeText}>M {event.magnitude.toFixed(1)}</Text>
        </View>
        <Text style={styles.place} numberOfLines={1}>
          {event.place || 'Unknown Location'}
        </Text>
      </View>

      <View style={styles.details}>
        <DetailRow
          icon="📍"
          text={`${event.coordinates?.[1]?.toFixed(2)}°N, ${event.coordinates?.[0]?.toFixed(2)}°E`}
        />
        <DetailRow
          icon="⬇️"
          text={`Depth: ${event.depth?.toFixed(1)} km`}
        />
        <DetailRow
          icon="🕐"
          text={event.time ? formatDistanceToNow(new Date(event.time), { addSuffix: true }) : 'Unknown'}
        />
      </View>

      {detailed && event.mmi && (
        <View style={styles.mmiContainer}>
          <Text style={styles.mmiLabel}>Expected Intensity:</Text>
          <Text style={styles.mmiValue}>MMI {event.mmi.toFixed(1)}</Text>
        </View>
      )}
    </View>
  );
}

function DetailRow({ icon, text }: { icon: string; text: string }) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailIcon}>{icon}</Text>
      <Text style={styles.detailText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  magnitudeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  magnitudeText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
  },
  place: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  details: {
    gap: 4,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  detailIcon: {
    fontSize: 12,
  },
  detailText: {
    fontSize: 12,
    color: '#6B7280',
  },
  mmiContainer: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  mmiLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  mmiValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#EF4444',
  },
});
