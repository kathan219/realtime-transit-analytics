import React, { useState, useEffect, useCallback } from 'react';
import {
  SafeAreaView,
  ScrollView,
  View,
  Text,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

import RouteSelector from './components/RouteSelector';
import DirectionSelector from './components/DirectionSelector';
import DataSourceSelector from './components/DataSourceSelector';
import RouteInfo from './components/RouteInfo';
import DelayChart from './components/DelayChart';
import OnTimeChart from './components/OnTimeChart';

import { getHotMetrics, getHistoryMetrics } from './services/api';
import { ROUTE_IDS, TTC_ROUTES } from './constants/routes';

const REFRESH_INTERVAL = 15000; // 15 seconds

export default function App() {
  const [selectedRoute, setSelectedRoute] = useState(ROUTE_IDS[0] || '504');
  const [selectedDirection, setSelectedDirection] = useState('both');
  const [dataSource, setDataSource] = useState('hot');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    if (!selectedRoute) return;

    setLoading(true);
    setError(null);

    try {
      let newData;
      if (dataSource === 'hot') {
        newData = await getHotMetrics(selectedRoute, selectedDirection);
      } else {
        newData = await getHistoryMetrics(selectedRoute, 60, selectedDirection);
      }

      setData(newData || []);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.message || 'Failed to fetch data');
      setData([]);
      
      // Show alert for network errors
      if (err.code === 'ECONNREFUSED' || err.message.includes('Network')) {
        Alert.alert(
          'Connection Error',
          'Could not connect to the API server. Make sure the FastAPI backend is running and the API URL is correct in config/api.js',
          [{ text: 'OK' }]
        );
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedRoute, selectedDirection, dataSource]);

  // Initial fetch and setup interval
  useEffect(() => {
    fetchData();
    
    const interval = setInterval(() => {
      fetchData();
    }, REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, [fetchData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchData();
  }, [fetchData]);

  const routeName = TTC_ROUTES[selectedRoute]?.name || 'Unknown';

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="auto" />
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <Text style={styles.header}>🚌 TTC Real-Time Analytics</Text>

        <View style={styles.controls}>
          <RouteSelector
            selectedRoute={selectedRoute}
            onRouteChange={setSelectedRoute}
          />
          
          <DirectionSelector
            selectedDirection={selectedDirection}
            onDirectionChange={setSelectedDirection}
          />
          
          <DataSourceSelector
            selectedSource={dataSource}
            onSourceChange={setDataSource}
          />
        </View>

        <RouteInfo routeId={selectedRoute} direction={selectedDirection} />

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>⚠️ {error}</Text>
          </View>
        )}

        {loading && !refreshing && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#0066cc" />
            <Text style={styles.loadingText}>Loading data...</Text>
          </View>
        )}

        {!loading && data.length === 0 && !error && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>
              No data available for Route {selectedRoute}
            </Text>
            <Text style={styles.emptySubtext}>
              Make sure the ETL pipeline is running and producing data.
            </Text>
          </View>
        )}

        {!loading && data.length > 0 && (
          <>
            <DelayChart
              data={data}
              routeName={routeName}
              direction={selectedDirection}
            />
            
            <OnTimeChart
              data={data}
              routeName={routeName}
              direction={selectedDirection}
            />
          </>
        )}

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Auto-refreshes every {REFRESH_INTERVAL / 1000} seconds
          </Text>
          <Text style={styles.footerText}>
            Pull down to refresh manually
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  controls: {
    marginBottom: 10,
  },
  errorContainer: {
    backgroundColor: '#ffe6e6',
    padding: 12,
    borderRadius: 8,
    marginBottom: 15,
  },
  errorText: {
    color: '#cc0000',
    fontSize: 14,
  },
  loadingContainer: {
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
    fontSize: 14,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    marginVertical: 20,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#bbb',
    textAlign: 'center',
  },
  footer: {
    marginTop: 30,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#999',
    marginTop: 5,
  },
});
