#!/usr/bin/env python3
"""
Test script for real-time transit analytics pipeline.
"""

import os
import time
import subprocess
import requests
import json

def test_pipeline():
    """Test the complete real-time pipeline."""
    
    print("🚌 Testing Real-Time Transit Analytics Pipeline")
    print("=" * 50)
    
    # Set environment variables
    os.environ['KAFKA_BROKER'] = 'localhost:9094'
    os.environ['GTFS_VEHICLE_URL'] = 'https://bustime.ttc.ca/gtfsrt/vehicles'
    os.environ['GTFS_TRIPS_URL'] = 'https://bustime.ttc.ca/gtfsrt/trips'
    
    print("✅ Environment variables set")
    
    # Test 1: Check if services are running
    print("\n1. Checking running services...")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        services = ['etl.consumer', 'etl.producer', 'uvicorn']
        running = []
        for service in services:
            if service in result.stdout:
                running.append(service)
        print(f"   Running services: {running}")
    except Exception as e:
        print(f"   Error checking services: {e}")
    
    # Test 2: Check API health
    print("\n2. Testing API health...")
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print(f"   ✅ API healthy: {response.json()}")
        else:
            print(f"   ❌ API unhealthy: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API not responding: {e}")
    
    # Test 3: Check Kafka topics
    print("\n3. Checking Kafka topics...")
    try:
        result = subprocess.run([
            'docker', 'exec', 'kafka', 'kafka-topics.sh', 
            '--bootstrap-server', 'localhost:9092', '--list'
        ], capture_output=True, text=True)
        topics = result.stdout.strip().split('\n')
        ttc_topics = [t for t in topics if 'transit.ttc' in t]
        print(f"   TTC topics: {ttc_topics}")
    except Exception as e:
        print(f"   Error checking topics: {e}")
    
    # Test 4: Check for messages in Kafka
    print("\n4. Checking for messages in Kafka...")
    try:
        result = subprocess.run([
            'docker', 'exec', 'kafka', 'kafka-console-consumer.sh',
            '--bootstrap-server', 'localhost:9092',
            '--topic', 'transit.ttc.vehicle_positions',
            '--from-beginning', '--max-messages', '2', '--timeout-ms', '3000'
        ], capture_output=True, text=True)
        if 'Processed a total of 0 messages' in result.stderr:
            print("   ❌ No messages in Kafka topics")
        else:
            print("   ✅ Messages found in Kafka")
    except Exception as e:
        print(f"   Error checking messages: {e}")
    
    # Test 5: Check Redis data
    print("\n5. Checking Redis data...")
    try:
        result = subprocess.run([
            'docker', 'exec', 'redis', 'redis-cli', 'KEYS', 'route:ttc:*'
        ], capture_output=True, text=True)
        keys = result.stdout.strip().split('\n')
        if keys == ['']:
            print("   ❌ No data in Redis")
        else:
            print(f"   ✅ Redis keys found: {keys}")
    except Exception as e:
        print(f"   Error checking Redis: {e}")
    
    # Test 6: Test API endpoints
    print("\n6. Testing API endpoints...")
    routes = ['1208', '504', '501']
    for route in routes:
        try:
            response = requests.get(f'http://localhost:8000/hot/ttc/{route}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   Route {route}: {len(data)} records")
            else:
                print(f"   Route {route}: Error {response.status_code}")
        except Exception as e:
            print(f"   Route {route}: Error {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Next steps:")
    print("1. If no messages in Kafka: Restart producer with TTC env vars")
    print("2. If no data in Redis: Wait 60-90 seconds for first window")
    print("3. If API returns empty: Check consumer logs for errors")
    print("4. Open dashboard: http://localhost:8050 or http://localhost:8501")

if __name__ == "__main__":
    test_pipeline()
