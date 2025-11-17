import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import RNPickerSelect from 'react-native-picker-select';
import { ROUTE_IDS, TTC_ROUTES } from '../constants/routes';

const RouteSelector = ({ selectedRoute, onRouteChange }) => {
  const pickerItems = ROUTE_IDS.map(routeId => ({
    label: `${routeId} - ${TTC_ROUTES[routeId].name}`,
    value: routeId,
  }));

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Route</Text>
      <RNPickerSelect
        onValueChange={onRouteChange}
        items={pickerItems}
        value={selectedRoute}
        placeholder={{ label: "Select a route...", value: null }}
        style={pickerSelectStyles}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 15,
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
});

const pickerSelectStyles = StyleSheet.create({
  inputIOS: {
    fontSize: 16,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    color: 'black',
    paddingRight: 30,
    backgroundColor: 'white',
  },
  inputAndroid: {
    fontSize: 16,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    color: 'black',
    backgroundColor: 'white',
  },
});

export default RouteSelector;

