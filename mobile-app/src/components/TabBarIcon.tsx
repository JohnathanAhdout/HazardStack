import React from 'react';
import { Text } from 'react-native';

interface TabBarIconProps {
  name: string;
  color: string;
  size: number;
}

export default function TabBarIcon({ name, color, size }: TabBarIconProps) {
  const icons: { [key: string]: string } = {
    home: '🏠',
    map: '🗺️',
    bell: '🔔',
    settings: '⚙️',
  };

  return (
    <Text style={{ fontSize: size, color }}>
      {icons[name] || '?'}
    </Text>
  );
}
