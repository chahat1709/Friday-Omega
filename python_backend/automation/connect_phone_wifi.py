#!/usr/bin/env python3
"""
WiFi ADB Auto-Connector
Automatically finds and connects to Android devices on the same network.
"""

import subprocess
import re
import socket

def find_android_devices():
    """Scan local network for devices with ADB port open (5555)"""
    print("[WiFi ADB] Scanning local network for Android devices...")
    
    # Get local IP range
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    
    network_prefix = ".".join(local_ip.split(".")[:3])
    
    # Quick scan of common IPs (you can expand this)
    potential_devices = []
    for i in range(1, 255):
        ip = f"{network_prefix}.{i}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        result = sock.connect_ex((ip, 5555))
        if result == 0:
            potential_devices.append(ip)
            print(f"  Found: {ip}")
        sock.close()
    
    return potential_devices

def connect_adb_wifi(ip):
    """Connect to device via ADB over WiFi"""
    try:
        result = subprocess.run(
            ["adb", "connect", f"{ip}:5555"],
            capture_output=True,
            text=True
        )
        
        if "connected" in result.stdout.lower():
            print(f"✓ Connected to {ip}")
            return True
        else:
            print(f"✗ Failed to connect to {ip}")
            return False
    except FileNotFoundError:
        print("✗ ADB not found. Install Android SDK Platform-Tools")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("FRIDAY - WiFi ADB Auto-Connector")
    print("=" * 60)
    
    # Option 1: Manual IP entry
    manual_ip = input("\nEnter phone IP (or press Enter to auto-scan): ").strip()
    
    if manual_ip:
        connect_adb_wifi(manual_ip)
    else:
        # Option 2: Auto-scan
        devices = find_android_devices()
        
        if not devices:
            print("\nNo devices found.")
            print("Make sure:")
            print("  1. Phone has 'ADB over WiFi' enabled")
            print("  2. Phone is on same WiFi network")
            print("  3. Run 'adb tcpip 5555' first (requires USB once)")
        else:
            print(f"\nFound {len(devices)} device(s).")
            for device in devices:
                connect_adb_wifi(device)
    
    # Verify connection
    print("\n" + "=" * 60)
    print("Connected Devices:")
    subprocess.run(["adb", "devices"])
    print("=" * 60)
    print("\nYou can now control your phone via FRIDAY!")
    print("Try: 'Open YouTube on my phone'")
