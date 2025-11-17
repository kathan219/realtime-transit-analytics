# TTC Real-Time Analytics - React Native App

Mobile app for viewing real-time TTC transit analytics with route delay and on-time percentage metrics.

## Features

- 🚌 **Route Selection**: Choose from TTC streetcar routes (501, 504, 505, 506, 509, 510, 511, 512)
- 🔄 **Direction Filtering**: View inbound, outbound, or both directions
- 📊 **Real-Time Charts**: 
  - Average delay (seconds)
  - On-time percentage
- 🔥 **Data Sources**: 
  - Hot data from Redis (real-time, last 60 seconds)
  - Historical data from Postgres (last 60 minutes)
- 🔄 **Auto-Refresh**: Updates every 15 seconds
- 📱 **Cross-Platform**: Works on iOS, Android, and Web

## Prerequisites

1. **Node.js** (v16 or higher)
2. **Expo CLI**: `npm install -g expo-cli` or `npm install -g @expo/cli`
3. **FastAPI Backend**: The backend must be running (see main README.md)
4. **iOS Simulator** (for iOS) or **Android Emulator** (for Android), or use Expo Go app on physical device

## Setup

1. **Install dependencies:**
   ```bash
   cd mobile
   npm install
   ```

2. **Configure API URL:**
   
   Edit `config/api.js` and set the correct API base URL:
   
   - **iOS Simulator**: `http://localhost:8000`
   - **Android Emulator**: `http://10.0.2.2:8000`
   - **Physical Device**: `http://<your-computer-ip>:8000`
   
   To find your IP address:
   - **macOS/Linux**: `ifconfig | grep "inet " | grep -v 127.0.0.1`
   - **Windows**: `ipconfig` (look for IPv4 Address)

3. **Start the FastAPI backend:**
   ```bash
   # From project root
   make api
   # Or manually:
   # source .venv/bin/activate
   # uvicorn analytics.api.main:app --host 0.0.0.0 --port 8000
   ```

4. **Start the React Native app:**
   ```bash
   cd mobile
   npm start
   # Or
   expo start
   ```

5. **Run on device/simulator:**
   - Press `i` for iOS Simulator
   - Press `a` for Android Emulator
   - Scan QR code with Expo Go app (physical device)

## Project Structure

```
mobile/
├── App.js                 # Main app component
├── package.json           # Dependencies
├── app.json              # Expo configuration
├── babel.config.js       # Babel configuration
├── config/
│   └── api.js           # API base URL configuration
├── constants/
│   └── routes.js        # TTC route definitions
├── services/
│   └── api.js          # API service functions
└── components/
    ├── RouteSelector.js      # Route dropdown
    ├── DirectionSelector.js  # Direction radio buttons
    ├── DataSourceSelector.js # Hot/History selector
    ├── RouteInfo.js          # Route information banner
    ├── DelayChart.js         # Delay line chart
    └── OnTimeChart.js        # On-time percentage chart
```

## API Endpoints Used

- `GET /hot/ttc/{route_id}?direction={direction}` - Hot metrics from Redis
- `GET /history/ttc/{route_id}?minutes=60` - Historical metrics from Postgres
- `GET /top/late/ttc?minutes=60&limit=10` - Top late routes (not yet used in UI)
- `GET /insights` - AI insights (not yet used in UI)

## Troubleshooting

### "Network Error" or "Connection Refused"

1. **Check API URL**: Make sure `config/api.js` has the correct URL for your platform
2. **Check Backend**: Ensure FastAPI is running: `curl http://localhost:8000/health`
3. **Check Firewall**: On physical devices, ensure your computer's firewall allows connections on port 8000
4. **Check Network**: Physical device must be on the same Wi-Fi network as your computer

### "No data available"

1. **Check ETL Pipeline**: Ensure producer and consumer are running:
   ```bash
   make producer
   make consumer
   ```
2. **Wait 60-90 seconds**: Hot data needs time for the first 60-second window to close
3. **Check History**: Try switching to "History (Postgres)" data source
4. **Check API**: Test directly: `curl http://localhost:8000/hot/ttc/504`

### Charts Not Displaying

1. **Check Data Format**: Ensure API returns data with `ts`, `avg_delay_seconds`, `ontime_pct` fields
2. **Check Direction Filter**: If filtering by direction, ensure data has `direction` field
3. **Check Logs**: Look for errors in Expo console

### Expo Installation Issues

```bash
# Clear Expo cache
expo start -c

# Reinstall dependencies
rm -rf node_modules
npm install
```

## Development

### Adding New Routes

Edit `constants/routes.js` and add route information:

```javascript
"XXX": {
  name: "Route Name",
  description: "Route description",
  directions: ["inbound", "outbound"]
}
```

### Adding New Charts

1. Create a new component in `components/`
2. Use `react-native-chart-kit` for charting
3. Import and add to `App.js`

### Customizing Styles

Edit the `StyleSheet` objects in each component file.

## Production Build

To create production builds:

```bash
# iOS
expo build:ios

# Android
expo build:android
```

Or use EAS Build (recommended):

```bash
npm install -g eas-cli
eas build --platform ios
eas build --platform android
```

## License

Same as main project.

