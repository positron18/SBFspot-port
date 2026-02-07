#!/usr/bin/env python3
"""
Example usage of SBFspot Python library.

This script demonstrates how to:
1. Discover SMA inverters on the network
2. Connect and authenticate
3. Read power, energy, and device information
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path if running directly
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from sbfspot_python import SBFspot, InverterData


def main():
    """Main example function."""
    
    # Enable logging for debugging (optional)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("SBFspot Python - SMA Inverter Communication")
    print("=" * 60)
    print()
    
    # --- Method 1: Auto-discovery ---
    print("Searching for SMA inverters on the network...")
    
    spot = SBFspot()
    try:
        # Initialize connection
        spot.eth.connect()
        
        # Discover inverters
        inverters = spot.discover(timeout=3.0)
        
        if not inverters:
            print("No inverters found. Try specifying IP directly.")
            print()
            print("Usage: python example.py [IP_ADDRESS]")
            return 1
        
        print(f"Found {len(inverters)} inverter(s):")
        for i, inv in enumerate(inverters, 1):
            print(f"  {i}. {inv.ip_address}")
        print()
        
        # Connect to first inverter
        target_ip = inverters[0].ip_address
        
    except Exception as e:
        print(f"Discovery failed: {e}")
        
        # Fallback to command line argument
        if len(sys.argv) > 1:
            target_ip = sys.argv[1]
            print(f"Using specified IP: {target_ip}")
        else:
            print("Please specify inverter IP as command line argument")
            return 1
    
    # --- Method 2: Direct connection ---
    print(f"Connecting to inverter at {target_ip}...")
    
    try:
        with SBFspot(target_ip, password="0000") as spot:
            print(f"Connected! SUSyID: {spot.inverter.susy_id}, Serial: {spot.inverter.serial}")
            print()
            
            # Login
            print("Logging in...")
            spot.login()
            print("Login successful!")
            print()
            
            # Read all data
            print("Reading inverter data...")
            data = spot.read_all()
            print()
            
            # Display results
            print(data)
            print()
            
            # Additional formatted output
            print("-" * 40)
            print("Summary:")
            print(f"  AC Power:     {data.power_kw:.3f} kW")
            print(f"  DC Power:     {data.dc_power_total / 1000:.3f} kW")
            print(f"  Frequency:    {data.frequency:.2f} Hz")
            print(f"  Energy Today: {data.energy_today_kwh:.2f} kWh")
            print(f"  Energy Total: {data.energy_total_kwh:.2f} kWh")
            if data.temperature:
                print(f"  Temperature:  {data.temp_celsius:.1f} °C")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print()
    print("Done!")
    return 0


def read_single_inverter(ip_address: str, password: str = "0000") -> InverterData:
    """
    Simple function to read data from a single inverter.
    
    Args:
        ip_address: Inverter IP address
        password: User password (default "0000")
        
    Returns:
        InverterData with all readings
    """
    with SBFspot(ip_address, password) as spot:
        spot.login()
        return spot.read_all()


if __name__ == "__main__":
    sys.exit(main())
