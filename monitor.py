#!/usr/bin/env python3
"""
Simple SMA Inverter Monitor
Discovers and displays data from SMA inverters on the network.
"""

import sys
import time
from datetime import datetime

# Adjust path for direct execution
sys.path.insert(0, '/Users/Giove/Progetti/SBFspot port')

from sbfspot_python import SBFspot


def print_header():
    """Print application header."""
    print("\n" + "═" * 70)
    print(" " * 20 + "SMA Inverter Monitor")
    print("═" * 70 + "\n")


def print_section(title):
    """Print section header."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print('─' * 70)


def format_value(value, unit="", decimals=2):
    """Format a numeric value with unit."""
    if value == 0:
        return f"{'---':>10} {unit}"
    if isinstance(value, float):
        return f"{value:>10.{decimals}f} {unit}"
    return f"{value:>10} {unit}"


def display_inverter_data(data):
    """Display inverter data in a formatted way."""
    
    # Device Information
    print_section("DEVICE INFORMATION")
    print(f"  Name:          {data.device_name or 'N/A'}")
    print(f"  Type:          {data.device_type or 'N/A'}")
    print(f"  Class:         {data.device_class or 'N/A'}")
    print(f"  Serial:        {data.serial}")
    print(f"  IP Address:    {data.ip_address}")
    if data.sw_version:
        print(f"  SW Version:    {data.sw_version}")
    
    # Current Production
    print_section("CURRENT PRODUCTION")
    print(f"  AC Power:      {format_value(data.power_kw, 'kW', 3)}")
    
    if data.pac1 or data.pac2 or data.pac3:
        print(f"    Phase 1:     {format_value(data.pac1, 'W')}")
        if data.pac2:
            print(f"    Phase 2:     {format_value(data.pac2, 'W')}")
        if data.pac3:
            print(f"    Phase 3:     {format_value(data.pac3, 'W')}")
    
    # DC Inputs
    if data.mpp:
        print(f"\n  DC Inputs:")
        for idx, mpp_data in sorted(data.mpp.items()):
            if mpp_data.pdc > 0 or mpp_data.udc > 0:
                print(f"    String {idx}:   {format_value(mpp_data.power_kw, 'kW', 3)} " +
                      f"@ {format_value(mpp_data.voltage, 'V', 1)} / " +
                      f"{format_value(mpp_data.current, 'A', 2)}")
    
    # Grid Parameters
    print_section("GRID PARAMETERS")
    print(f"  Frequency:     {format_value(data.frequency, 'Hz', 2)}")
    if data.uac1:
        print(f"  Voltage L1:    {format_value(data.voltage_l1, 'V', 1)}")
    if data.uac2:
        print(f"  Voltage L2:    {format_value(data.voltage_l2, 'V', 1)}")
    if data.uac3:
        print(f"  Voltage L3:    {format_value(data.voltage_l3, 'V', 1)}")
    
    # Energy Counters
    print_section("ENERGY PRODUCTION")
    print(f"  Today:         {format_value(data.energy_today_kwh, 'kWh', 2)}")
    print(f"  Total:         {format_value(data.energy_total_kwh, 'kWh', 0)}")
    
    # Battery (if present)
    if data.has_battery:
        print_section("BATTERY STATUS")
        print(f"  Charge:        {format_value(data.bat_charge_status, '%')}")
        if data.bat_voltage:
            print(f"  Voltage:       {format_value(data.bat_voltage / 100, 'V', 1)}")
        if data.bat_current:
            direction = "Charging" if data.bat_current > 0 else "Discharging"
            print(f"  Current:       {format_value(abs(data.bat_current) / 1000, 'A', 2)} ({direction})")
        if data.bat_temperature:
            print(f"  Temperature:   {format_value(data.bat_temperature / 100, '°C', 1)}")
    
    # Additional Info
    if data.temperature:
        print_section("INVERTER STATUS")
        print(f"  Temperature:   {format_value(data.temp_celsius, '°C', 1)}")
    
    if data.inverter_datetime:
        print(f"  Time:          {data.inverter_datetime.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main application loop."""
    print_header()
    
    # Create SBFspot instance
    spot = SBFspot(password="0000")
    
    try:
        print("Initializing network...")
        spot.eth.connect()
        print("✓ Network initialized\n")
        
        # Discovery
        print("Searching for SMA inverters (3 sec timeout)...")
        inverters = spot.discover(timeout=3.0)
        
        if not inverters:
            print("\n❌ No inverters found on the network.")
            print("\nTroubleshooting:")
            print("  • Make sure you're on the same network as the inverter")
            print("  • Check if the inverter is powered on and awake")
            print("  • Verify firewall settings (UDP port 9522)")
            print("  • Try specifying IP directly: python monitor.py <IP_ADDRESS>\n")
            return 1
        
        print(f"✓ Found {len(inverters)} inverter(s):\n")
        for i, inv in enumerate(inverters, 1):
            print(f"  {i}. {inv.ip_address}")
        
        # Connect to first inverter
        target_ip = inverters[0].ip_address
        print(f"\nConnecting to {target_ip}...")
        spot.connect(target_ip)
        print(f"✓ Connected (SUSyID: {spot.inverter.susy_id}, Serial: {spot.inverter.serial})")
        
        # Login
        print("Logging in...")
        spot.login()
        print("✓ Authenticated\n")
        
        # Read data
        print("Reading inverter data...")
        data = spot.read_all()
        print("✓ Data received\n")
        
        # Display
        display_inverter_data(data)
        
        print("\n" + "═" * 70)
        print(f"  Data retrieved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 70 + "\n")
        
        # Cleanup
        spot.logout()
        spot.close()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        spot.close()
        return 130
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        if '--debug' in sys.argv:
            traceback.print_exc()
        spot.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
