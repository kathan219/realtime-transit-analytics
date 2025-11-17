# Testing the Expo App

## Quick Start Guide

### Step 1: Ensure Backend is Running

```bash
# From project root
make api

# Verify it's working
curl http://localhost:8000/health
```

### Step 2: Start the Expo App

```bash
cd mobile
npm start
```

You should see:
- Metro bundler starting
- QR code in terminal
- Options: `i` (iOS), `a` (Android), `w` (web)

### Step 3: Connect to the App

#### Option A: Physical Device (Recommended)

1. **Install Expo Go** on your phone:
   - iOS: App Store → Search "Expo Go"
   - Android: Play Store → Search "Expo Go"

2. **Update API URL** for physical device:
   - Edit `mobile/config/api.js`
   - Change to: `http://10.0.0.112:8000` (your computer's IP)

3. **Scan QR Code**:
   - iOS: Open Camera app → Scan QR code
   - Android: Open Expo Go app → Scan QR code
   - Or: Press `s` in terminal to send link via email/SMS

4. **Ensure same Wi-Fi**: Device and computer must be on the same network

#### Option B: iOS Simulator (macOS only)

1. **Press `i`** in the Expo terminal
2. **API URL**: Already set to `http://localhost:8000` (works for simulator)
3. Simulator will open automatically

#### Option C: Android Emulator

1. **Start Android Emulator** first (from Android Studio)
2. **Press `a`** in the Expo terminal
3. **Update API URL** to: `http://10.0.2.2:8000` (Android emulator special IP)

#### Option D: Web Browser

1. **Press `w`** in the Expo terminal
2. Browser will open automatically
3. **API URL**: Works with `http://localhost:8000`

### Step 4: Test the App

Once the app loads:

1. **Check Route Selection**: Select different routes (504, 501, etc.)
2. **Test Direction Filter**: Switch between "Both", "Inbound", "Outbound"
3. **Test Data Source**: Toggle between "Hot (Redis)" and "History (Postgres)"
4. **Verify Charts**: Should see delay and on-time percentage charts
5. **Check Auto-Refresh**: Data should update every 15 seconds

### Troubleshooting

#### "Network Error" or "Connection Refused"

**For Physical Device:**
- ✅ Update `mobile/config/api.js` to use your IP: `http://10.0.0.112:8000`
- ✅ Ensure device and computer are on same Wi-Fi
- ✅ Check firewall allows port 8000
- ✅ Verify API is running: `curl http://localhost:8000/health`

**For iOS Simulator:**
- ✅ Use `http://localhost:8000` (already set)
- ✅ Ensure API is running

**For Android Emulator:**
- ✅ Use `http://10.0.2.2:8000` (special emulator IP)
- ✅ Ensure API is running

#### "No data available"

1. **Check ETL Pipeline**: Ensure producer and consumer are running:
   ```bash
   make producer
   make consumer
   ```

2. **Wait 60-90 seconds**: Hot data needs time for first window to close

3. **Try History**: Switch to "History (Postgres)" data source

4. **Test API directly**:
   ```bash
   curl http://localhost:8000/hot/ttc/504
   ```

#### App Won't Load / Metro Bundler Errors

1. **Clear cache and restart**:
   ```bash
   cd mobile
   npx expo start -c
   ```

2. **Reinstall dependencies**:
   ```bash
   rm -rf node_modules
   npm install
   ```

#### Expo Go Can't Connect

1. **Check network**: Device and computer must be on same Wi-Fi
2. **Try tunnel mode**:
   ```bash
   npx expo start --tunnel
   ```
   (Slower but works across networks)

3. **Check firewall**: Allow Expo on your network

### Testing Checklist

- [ ] Backend API is running (`make api`)
- [ ] API URL configured correctly in `mobile/config/api.js`
- [ ] Expo app started (`npm start` in mobile/ directory)
- [ ] App connected (via Expo Go, simulator, or web)
- [ ] Route selection works
- [ ] Direction filtering works
- [ ] Data source switching works
- [ ] Charts display data
- [ ] Auto-refresh works (wait 15 seconds)
- [ ] Pull-to-refresh works

### Example Test Commands

```bash
# Test API health
curl http://localhost:8000/health

# Test hot metrics
curl http://localhost:8000/hot/ttc/504

# Test history
curl http://localhost:8000/history/ttc/504?minutes=60

# Test with direction
curl "http://localhost:8000/hot/ttc/504?direction=inbound"
```

### Next Steps

Once the app is working:
1. Test with real TTC data (ensure producer is using real GTFS feeds)
2. Try different routes
3. Compare Hot vs History data
4. Test on both iOS and Android if possible

