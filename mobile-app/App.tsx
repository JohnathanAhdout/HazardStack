import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import * as Location from 'expo-location';
import * as Notifications from 'expo-notifications';

import HomeScreen from './src/screens/HomeScreen';
import MapScreen from './src/screens/MapScreen';
import AlertsScreen from './src/screens/AlertsScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { LocationProvider } from './src/context/LocationContext';
import TabBarIcon from './src/components/TabBarIcon';

const Tab = createBottomTabNavigator();

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export default function App() {
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [permissionStatus, setPermissionStatus] = useState<string>('');

  useEffect(() => {
    (async () => {
      // Request location permissions
      const { status } = await Location.requestForegroundPermissionsAsync();
      setPermissionStatus(status);

      if (status === 'granted') {
        const currentLocation = await Location.getCurrentPositionAsync({});
        setLocation(currentLocation);
      }

      // Request notification permissions
      const { status: notificationStatus } = await Notifications.requestPermissionsAsync();
      if (notificationStatus === 'granted') {
        // Schedule demo notification
        await scheduleDemoNotification();
      }
    })();
  }, []);

  return (
    <LocationProvider>
      <NavigationContainer>
        <StatusBar style="auto" />
        <Tab.Navigator
          screenOptions={{
            tabBarActiveTintColor: '#0066CC',
            tabBarInactiveTintColor: '#6B7280',
            headerStyle: {
              backgroundColor: '#0066CC',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}
        >
          <Tab.Screen
            name="Home"
            component={HomeScreen}
            options={{
              title: 'SPIRAL',
              tabBarIcon: ({ color, size }) => (
                <TabBarIcon name="home" color={color} size={size} />
              ),
            }}
          />
          <Tab.Screen
            name="Map"
            component={MapScreen}
            options={{
              title: 'Risk Map',
              tabBarIcon: ({ color, size }) => (
                <TabBarIcon name="map" color={color} size={size} />
              ),
            }}
          />
          <Tab.Screen
            name="Alerts"
            component={AlertsScreen}
            options={{
              title: 'Alerts',
              tabBarIcon: ({ color, size }) => (
                <TabBarIcon name="bell" color={color} size={size} />
              ),
              tabBarBadge: 3,
            }}
          />
          <Tab.Screen
            name="Settings"
            component={SettingsScreen}
            options={{
              title: 'Settings',
              tabBarIcon: ({ color, size }) => (
                <TabBarIcon name="settings" color={color} size={size} />
              ),
            }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </LocationProvider>
  );
}

async function scheduleDemoNotification() {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: "SPIRAL Alert 🌀",
      body: 'Welcome to SPIRAL! You will receive real-time hazard alerts here.',
      data: { hazard: 'demo' },
    },
    trigger: { seconds: 5 },
  });
}
