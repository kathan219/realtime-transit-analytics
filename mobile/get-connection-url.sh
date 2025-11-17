#!/bin/bash
# Get your computer's IP address for Expo connection

IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

if [ -z "$IP" ]; then
    echo "Could not find IP address"
    exit 1
fi

echo "==================================="
echo "Expo Connection URL for Physical Device:"
echo "==================================="
echo "exp://${IP}:8081"
echo ""
echo "To connect:"
echo "1. Open Expo Go app on your phone"
echo "2. Make sure phone and computer are on same Wi-Fi"
echo "3. Scan QR code or enter URL manually"
echo ""
echo "Or use this URL in Expo Go:"
echo "exp://${IP}:8081"
echo "==================================="

