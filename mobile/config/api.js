/**
 * API Configuration
 * 
 * Set your FastAPI backend URL here.
 * 
 * For iOS Simulator: http://localhost:8000
 * For Android Emulator: http://10.0.2.2:8000
 * For Physical Device: http://<your-ip>:8000
 */

// Detect platform and set appropriate URL
import { Platform } from 'react-native';

const getApiBase = () => {
  if (__DEV__) {
    // For physical devices, use your computer's IP address
    // For simulators/emulators, use localhost or 10.0.2.2
    if (Platform.OS === 'android') {
      // Android emulator uses special IP
      return "http://10.0.2.2:8000";
    } else if (Platform.OS === 'ios') {
      // For iOS simulator: http://localhost:8000
      // For physical device: http://10.0.0.112:8000
      // Change this line based on where you're testing:
      return "http://10.0.0.112:8000";  // Change to "http://localhost:8000" for iOS Simulator
    } else {
      // Web or other platforms
      return "http://localhost:8000";
    }
  }
  return "https://your-api-domain.com";
};

const API_BASE = getApiBase();

export default API_BASE;
