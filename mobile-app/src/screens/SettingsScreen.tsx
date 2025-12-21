import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Switch,
  TouchableOpacity,
  Alert,
} from 'react-native';

export default function SettingsScreen() {
  const [notifications, setNotifications] = useState(true);
  const [earthquakeAlerts, setEarthquakeAlerts] = useState(true);
  const [floodAlerts, setFloodAlerts] = useState(true);
  const [rainAlerts, setRainAlerts] = useState(true);
  const [locationTracking, setLocationTracking] = useState(true);

  return (
    <ScrollView style={styles.container}>
      {/* App Info */}
      <View style={styles.section}>
        <Text style={styles.appTitle}>SPIRAL Mobile</Text>
        <Text style={styles.appSubtitle}>
          Structured Physics-Informed Representation-Augmented Learning
        </Text>
        <Text style={styles.versionText}>Version 0.1.0</Text>
      </View>

      {/* Notifications */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notifications</Text>
        <SettingRow
          label="Push Notifications"
          value={notifications}
          onChange={setNotifications}
        />
        <SettingRow
          label="Earthquake Alerts"
          value={earthquakeAlerts}
          onChange={setEarthquakeAlerts}
          disabled={!notifications}
        />
        <SettingRow
          label="Flood Alerts"
          value={floodAlerts}
          onChange={setFloodAlerts}
          disabled={!notifications}
        />
        <SettingRow
          label="Rain Alerts"
          value={rainAlerts}
          onChange={setRainAlerts}
          disabled={!notifications}
        />
      </View>

      {/* Location */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Location</Text>
        <SettingRow
          label="Location Tracking"
          value={locationTracking}
          onChange={setLocationTracking}
        />
        <Text style={styles.helperText}>
          Required for accurate hazard predictions in your area
        </Text>
      </View>

      {/* Data & Privacy */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data & Privacy</Text>
        <SettingButton
          label="Clear Cache"
          onPress={() => Alert.alert('Cache Cleared', 'App cache has been cleared')}
        />
        <SettingButton
          label="Privacy Policy"
          onPress={() => Alert.alert('Privacy Policy', 'Privacy policy would open here')}
        />
        <SettingButton
          label="Terms of Service"
          onPress={() => Alert.alert('Terms', 'Terms of service would open here')}
        />
      </View>

      {/* About */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <SettingButton
          label="How It Works"
          onPress={() => Alert.alert('Info', 'Educational content about SPIRAL')}
        />
        <SettingButton
          label="Data Sources"
          onPress={() => Alert.alert('Sources', 'USGS, IMD, MOSDAC, CWC, NCS')}
        />
        <SettingButton
          label="Send Feedback"
          onPress={() => Alert.alert('Feedback', 'Feedback form would open here')}
        />
      </View>

      {/* Credits */}
      <View style={styles.credits}>
        <Text style={styles.creditsText}>
          SPIRAL uses real-time data from USGS, IMD, MOSDAC, CWC, and NCS
        </Text>
        <Text style={styles.creditsText}>
          For official warnings, consult IMD, CWC, NCS, and INCOIS
        </Text>
      </View>
    </ScrollView>
  );
}

function SettingRow({ label, value, onChange, disabled }: any) {
  return (
    <View style={[styles.settingRow, disabled && styles.settingRowDisabled]}>
      <Text style={[styles.settingLabel, disabled && styles.settingLabelDisabled]}>
        {label}
      </Text>
      <Switch
        value={value}
        onValueChange={onChange}
        disabled={disabled}
        trackColor={{ false: '#D1D5DB', true: '#60A5FA' }}
        thumbColor={value ? '#0066CC' : '#F3F4F6'}
      />
    </View>
  );
}

function SettingButton({ label, onPress }: any) {
  return (
    <TouchableOpacity style={styles.settingButton} onPress={onPress}>
      <Text style={styles.settingButtonText}>{label}</Text>
      <Text style={styles.settingButtonArrow}>›</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  section: {
    backgroundColor: '#fff',
    marginTop: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  appTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    textAlign: 'center',
    marginTop: 20,
  },
  appSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 8,
    paddingHorizontal: 20,
  },
  versionText: {
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
    textTransform: 'uppercase',
    marginBottom: 12,
    marginTop: 8,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  settingRowDisabled: {
    opacity: 0.5,
  },
  settingLabel: {
    fontSize: 16,
    color: '#111827',
  },
  settingLabelDisabled: {
    color: '#9CA3AF',
  },
  settingButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  settingButtonText: {
    fontSize: 16,
    color: '#111827',
  },
  settingButtonArrow: {
    fontSize: 24,
    color: '#D1D5DB',
  },
  helperText: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 8,
  },
  credits: {
    padding: 20,
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 40,
  },
  creditsText: {
    fontSize: 11,
    color: '#9CA3AF',
    textAlign: 'center',
    marginBottom: 4,
  },
});
