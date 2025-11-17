import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { format } from 'date-fns';

const screenWidth = Dimensions.get('window').width;

const OnTimeChart = ({ data, routeName, direction }) => {
  if (!data || data.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No data available</Text>
      </View>
    );
  }

  // Filter by direction if specified
  let filteredData = data;
  if (direction !== 'both' && data[0]?.direction) {
    filteredData = data.filter(d => d.direction === direction);
  }

  if (filteredData.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No data for {direction} direction</Text>
      </View>
    );
  }

  // Sort by timestamp
  filteredData.sort((a, b) => new Date(a.ts) - new Date(b.ts));

  // Prepare chart data
  const labels = filteredData.map((item, index) => {
    if (filteredData.length <= 5) {
      return format(new Date(item.ts), 'HH:mm');
    }
    const step = Math.ceil(filteredData.length / 5);
    return index % step === 0 ? format(new Date(item.ts), 'HH:mm') : '';
  });

  const onTimeData = filteredData.map(item => 
    item.ontime_pct !== null && item.ontime_pct !== undefined
      ? item.ontime_pct * 100 // Convert to percentage
      : 0
  );

  const chartData = {
    labels: labels,
    datasets: [
      {
        data: onTimeData,
        color: (opacity = 1) => `rgba(34, 139, 34, ${opacity})`,
        strokeWidth: 2,
      },
    ],
  };

  const chartConfig = {
    backgroundColor: '#ffffff',
    backgroundGradientFrom: '#ffffff',
    backgroundGradientTo: '#ffffff',
    decimalPlaces: 1,
    color: (opacity = 1) => `rgba(34, 139, 34, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: '#228B22',
    },
  };

  const chartTitle = direction !== 'both' 
    ? `On-Time % - ${direction.charAt(0).toUpperCase() + direction.slice(1)}`
    : 'On-Time Percentage';

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{chartTitle}</Text>
      <LineChart
        data={chartData}
        width={screenWidth - 40}
        height={220}
        chartConfig={chartConfig}
        bezier
        style={styles.chart}
        yAxisLabel=""
        yAxisSuffix="%"
        fromZero
        yAxisInterval={10}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 10,
    padding: 10,
    backgroundColor: '#fff',
    borderRadius: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
});

export default OnTimeChart;

