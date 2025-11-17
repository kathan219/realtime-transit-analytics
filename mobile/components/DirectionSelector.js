import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const DirectionSelector = ({ selectedDirection, onDirectionChange }) => {
  const directions = [
    { label: "Both", value: "both" },
    { label: "Inbound (→)", value: "inbound" },
    { label: "Outbound (←)", value: "outbound" },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Direction</Text>
      <View style={styles.buttonGroup}>
        {directions.map((dir) => (
          <TouchableOpacity
            key={dir.value}
            style={[
              styles.button,
              selectedDirection === dir.value && styles.buttonActive,
            ]}
            onPress={() => onDirectionChange(dir.value)}
          >
            <Text
              style={[
                styles.buttonText,
                selectedDirection === dir.value && styles.buttonTextActive,
              ]}
            >
              {dir.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
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
  buttonGroup: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
    alignItems: 'center',
  },
  buttonActive: {
    backgroundColor: '#0066cc',
    borderColor: '#0066cc',
  },
  buttonText: {
    fontSize: 14,
    color: '#333',
  },
  buttonTextActive: {
    color: '#fff',
    fontWeight: 'bold',
  },
});

export default DirectionSelector;

