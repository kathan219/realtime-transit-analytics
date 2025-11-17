import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const DataSourceSelector = ({ selectedSource, onSourceChange }) => {
  const sources = [
    { label: "Hot (Redis)", value: "hot" },
    { label: "History (Postgres)", value: "history" },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Data Source</Text>
      <View style={styles.buttonGroup}>
        {sources.map((source) => (
          <TouchableOpacity
            key={source.value}
            style={[
              styles.button,
              selectedSource === source.value && styles.buttonActive,
            ]}
            onPress={() => onSourceChange(source.value)}
          >
            <Text
              style={[
                styles.buttonText,
                selectedSource === source.value && styles.buttonTextActive,
              ]}
            >
              {source.label}
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

export default DataSourceSelector;

