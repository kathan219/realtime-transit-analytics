import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { TTC_ROUTES } from '../constants/routes';

const RouteInfo = ({ routeId, direction }) => {
  const routeInfo = TTC_ROUTES[routeId];
  
  if (!routeInfo) {
    return null;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.routeName}>
        Route {routeId} - {routeInfo.name}
      </Text>
      <Text style={styles.description}>{routeInfo.description}</Text>
      <Text style={styles.direction}>
        Direction: {direction.charAt(0).toUpperCase() + direction.slice(1)}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#f0f8ff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 15,
  },
  routeName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  description: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  direction: {
    fontSize: 12,
    color: '#0066cc',
    fontWeight: '500',
  },
});

export default RouteInfo;

