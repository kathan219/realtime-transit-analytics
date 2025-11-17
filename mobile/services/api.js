import axios from 'axios';
import API_BASE from '../config/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Get hot (real-time) metrics for a TTC route
 * @param {string} routeId - Route ID (e.g., '504')
 * @param {string} direction - 'inbound', 'outbound', or 'both'
 * @returns {Promise<Array>} Array of metric objects
 */
export const getHotMetrics = async (routeId, direction = 'both') => {
  try {
    const response = await api.get(`/hot/ttc/${routeId}`, {
      params: { direction },
    });
    return response.data || [];
  } catch (error) {
    console.error('Error fetching hot metrics:', error);
    throw error;
  }
};

/**
 * Get historical metrics for a TTC route
 * @param {string} routeId - Route ID (e.g., '504')
 * @param {number} minutes - Time window in minutes (default: 60)
 * @param {string} direction - 'inbound', 'outbound', or 'both' (default: 'both')
 * @returns {Promise<Array>} Array of metric objects
 */
export const getHistoryMetrics = async (routeId, minutes = 60, direction = 'both') => {
  try {
    const response = await api.get(`/history/ttc/${routeId}`, {
      params: { minutes, direction },
    });
    return response.data || [];
  } catch (error) {
    console.error('Error fetching history metrics:', error);
    throw error;
  }
};

/**
 * Get top late routes
 * @param {number} minutes - Time window in minutes (default: 60)
 * @param {number} limit - Maximum number of routes (default: 10)
 * @returns {Promise<Array>} Array of route objects with delay stats
 */
export const getTopLateRoutes = async (minutes = 60, limit = 10) => {
  try {
    const response = await api.get('/top/late/ttc', {
      params: { minutes, limit },
    });
    return response.data || [];
  } catch (error) {
    console.error('Error fetching top late routes:', error);
    throw error;
  }
};

/**
 * Get AI insights
 * @returns {Promise<Object>} Insights object
 */
export const getInsights = async () => {
  try {
    const response = await api.get('/insights');
    return response.data || {};
  } catch (error) {
    console.error('Error fetching insights:', error);
    return {};
  }
};

/**
 * Health check
 * @returns {Promise<Object>} Health status
 */
export const healthCheck = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};
