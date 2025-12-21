import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { fetchRecentEvents } from '../services/api';
import EventCard from '../components/EventCard';

export default function AlertsScreen() {
  const [events, setEvents] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'earthquake' | 'flood' | 'rain'>('all');

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const recentEvents = await fetchRecentEvents(168, 2.5); // Last week, M>=2.5
      setEvents(recentEvents);
    } catch (error) {
      console.error('Error loading events:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadEvents();
  };

  return (
    <View style={styles.container}>
      {/* Filter Buttons */}
      <View style={styles.filterContainer}>
        <FilterButton
          label="All"
          active={filter === 'all'}
          onPress={() => setFilter('all')}
        />
        <FilterButton
          label="Earthquake"
          active={filter === 'earthquake'}
          onPress={() => setFilter('earthquake')}
        />
        <FilterButton
          label="Flood"
          active={filter === 'flood'}
          onPress={() => setFilter('flood')}
        />
        <FilterButton
          label="Rain"
          active={filter === 'rain'}
          onPress={() => setFilter('rain')}
        />
      </View>

      {/* Events List */}
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.eventsList}>
          {events.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No alerts at this time</Text>
              <Text style={styles.emptySubtext}>
                You'll be notified when hazards are detected
              </Text>
            </View>
          ) : (
            events.map((event, idx) => (
              <EventCard key={idx} event={event} detailed />
            ))
          )}
        </View>
      </ScrollView>
    </View>
  );
}

function FilterButton({ label, active, onPress }: any) {
  return (
    <TouchableOpacity
      style={[styles.filterButton, active && styles.filterButtonActive]}
      onPress={onPress}
    >
      <Text style={[styles.filterButtonText, active && styles.filterButtonTextActive]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  filterContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  filterButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
  },
  filterButtonActive: {
    backgroundColor: '#0066CC',
  },
  filterButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
  filterButtonTextActive: {
    color: '#fff',
  },
  scrollView: {
    flex: 1,
  },
  eventsList: {
    padding: 16,
    gap: 12,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9CA3AF',
  },
});
