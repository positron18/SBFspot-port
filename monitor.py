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
    print(f"  Class:         {data.device_class or 'N/A'} (ID: {data.device_class_id})")
    print(f"  Serial:        {data.serial}")
    print(f"  SUSyID:        {data.susy_id}")
    print(f"  NetID:         {data.net_id}")
    print(f"  IP Address:    {data.ip_address}")
    if data.sw_version:
        print(f"  SW Version:    {data.sw_version}")
    
    # Status Information
    print_section("DEVICE STATUS")
    print(f"  Device Status: {data.device_status:#010x}")
    print(f"  Grid Relay:    {data.grid_relay_status:#010x}")
    if data.inverter_datetime:
        print(f"  Inverter Time: {data.inverter_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    if data.wakeup_time:
        print(f"  Wakeup Time:   {data.wakeup_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if data.sleep_time:
        print(f"  Sleep Time:    {data.sleep_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Energy Flow Analysis - CRITICAL SECTION
    print_section("⚡ ENERGY FLOW ANALYSIS")
    
    # Calculate solar production (DC from panels)
    solar_production_w = sum(mpp.pdc for mpp in data.mpp.values()) if data.mpp else 0
    
    # Calculate battery contribution
    battery_power_w = 0
    if data.bat_voltage and data.bat_current:
        battery_power_w = (data.bat_voltage / 100.0) * (data.bat_current / 1000.0)
    
    # Show solar production
    print(f"\n  ☀️  SOLAR PRODUCTION (from panels):")
    if solar_production_w > 0:
        print(f"      {format_value(solar_production_w / 1000, 'kW', 3)} ← Real PV generation")
    else:
        print(f"      {'0.000':<10} kW ← ⚠️  Panels NOT producing (night/covered)")
    
    # Show battery contribution
    if data.has_battery or battery_power_w != 0:
        print(f"\n  🔋 BATTERY:")
        if battery_power_w > 0:
            print(f"      {format_value(battery_power_w / 1000, 'kW', 3)} (Charging - absorbing energy)")
        elif battery_power_w < 0:
            print(f"      {format_value(abs(battery_power_w) / 1000, 'kW', 3)} (Discharging - providing energy)")
        else:
            print(f"      {'0.000':<10} kW (Idle)")
        print(f"      Charge Level: {data.bat_charge_status}%")
    
    # Show inverter output
    print(f"\n  ⚡ INVERTER OUTPUT (to house/grid):")
    print(f"      {format_value(data.power_kw, 'kW', 3)}")
    
    # Energy balance check
    print(f"\n  📊 ENERGY BALANCE:")
    if solar_production_w > 0 or battery_power_w != 0:
        sources = []
        if solar_production_w > 0:
            sources.append(f"{solar_production_w/1000:.3f} kW (solar)")
        if battery_power_w < 0:
            sources.append(f"{abs(battery_power_w)/1000:.3f} kW (battery)")
        
        total_sources = (solar_production_w + abs(min(0, battery_power_w)))
        print(f"      Sources: {' + '.join(sources)}")
        print(f"      Output:  {data.total_pac/1000:.3f} kW (inverter)")
        
        # Check balance (allowing for conversion losses)
        if total_sources > 0:
            efficiency = (data.total_pac / total_sources) * 100 if total_sources > 0 else 0
            if 90 <= efficiency <= 100:
                print(f"      ✓ Balance OK (efficiency: {efficiency:.1f}%)")
            else:
                print(f"      ⚠️  Check: efficiency {efficiency:.1f}% (expected 95-98%)")
    else:
        print(f"      No active energy flow")
    
    # Warning if misinterpretation possible
    if solar_production_w == 0 and data.total_pac > 0:
        print(f"\n  ⚠️  IMPORTANT:")
        print(f"      Inverter is outputting {data.power_kw:.3f} kW but solar production is ZERO!")
        print(f"      → Energy is coming from BATTERY or GRID, NOT from solar panels")
    
    # Current Production
    print_section("CURRENT AC PRODUCTION")
    print(f"  Total Power:   {format_value(data.power_kw, 'kW', 3)} ({data.total_pac} W)")
    
    if data.pac1 or data.pac2 or data.pac3:
        print(f"\n  Per Phase:")
        print(f"    Phase 1:     {format_value(data.pac1, 'W'):>15}   " +
              f"{format_value(data.voltage_l1, 'V', 1):>12}   " +
              f"{format_value(data.current_l1, 'A', 2):>10}")
        if data.pac2 or data.uac2:
            print(f"    Phase 2:     {format_value(data.pac2, 'W'):>15}   " +
                  f"{format_value(data.voltage_l2, 'V', 1):>12}   " +
                  f"{format_value(data.current_l2, 'A', 2):>10}")
        if data.pac3 or data.uac3:
            print(f"    Phase 3:     {format_value(data.pac3, 'W'):>15}   " +
                  f"{format_value(data.voltage_l3, 'V', 1):>12}   " +
                  f"{format_value(data.current_l3, 'A', 2):>10}")
    
    # DC Inputs
    if data.mpp:
        print_section("DC INPUTS (MPPT)")
        total_dc = 0
        for idx, mpp_data in sorted(data.mpp.items()):
            if mpp_data.pdc > 0 or mpp_data.udc > 0:
                print(f"  String {idx}:")
                print(f"    Power:       {format_value(mpp_data.power_kw, 'kW', 3)} ({mpp_data.pdc} W)")
                print(f"    Voltage:     {format_value(mpp_data.voltage, 'V', 1)} ({mpp_data.udc/100:.0f} V)")
                print(f"    Current:     {format_value(mpp_data.current, 'A', 2)} ({mpp_data.idc} mA)")
                total_dc += mpp_data.pdc
        
        if total_dc > 0:
            print(f"\n  Total DC:      {format_value(total_dc / 1000, 'kW', 3)} ({total_dc} W)")
            if data.total_pac > 0:
                efficiency = (data.total_pac / total_dc) * 100
                print(f"  Efficiency:    {format_value(efficiency, '%', 1)}")
    
    # Grid Parameters
    print_section("GRID PARAMETERS")
    print(f"  Frequency:     {format_value(data.frequency, 'Hz', 2)} (raw: {data.grid_freq})")
    if data.metering_grid_w_out or data.metering_grid_w_in:
        print(f"\n  Grid Metering:")
        if data.metering_grid_w_out:
            print(f"    Power Out:   {format_value(data.metering_grid_w_out, 'W')}")
        if data.metering_grid_w_in:
            print(f"    Power In:    {format_value(data.metering_grid_w_in, 'W')}")
    
    # Energy Counters
    print_section("ENERGY PRODUCTION")
    print(f"  Today:         {format_value(data.energy_today_kwh, 'kWh', 2)} ({data.e_today} Wh)")
    print(f"  Total:         {format_value(data.energy_total_kwh, 'kWh', 0)} ({data.e_total} Wh)")
    
    # Operation Time
    if data.operation_time or data.feed_in_time:
        print_section("OPERATION TIME")
        if data.operation_time:
            hours = data.operation_time / 3600
            print(f"  Total:         {format_value(hours, 'h', 1)} ({data.operation_time} s)")
        if data.feed_in_time:
            hours = data.feed_in_time / 3600
            print(f"  Feed-in:       {format_value(hours, 'h', 1)} ({data.feed_in_time} s)")
    
    # Battery (if present)
    if data.has_battery:
        print_section("BATTERY STATUS")
        print(f"  Charge:        {format_value(data.bat_charge_status, '%')}")
        if data.bat_voltage:
            print(f"  Voltage:       {format_value(data.bat_voltage / 100, 'V', 1)} (raw: {data.bat_voltage})")
        if data.bat_current:
            direction = "Charging" if data.bat_current > 0 else "Discharging"
            print(f"  Current:       {format_value(abs(data.bat_current) / 1000, 'A', 2)} ({direction}) (raw: {data.bat_current} mA)")
        if data.bat_temperature:
            print(f"  Temperature:   {format_value(data.bat_temperature / 100, '°C', 1)} (raw: {data.bat_temperature})")
    
    # Inverter Temperature
    if data.temperature:
        print_section("INVERTER TEMPERATURE")
        print(f"  Temperature:   {format_value(data.temp_celsius, '°C', 1)} (raw: {data.temperature})")
    
    # Calculated Values
    if data.cal_pdc_tot or data.cal_efficiency:
        print_section("CALCULATED VALUES")
        if data.cal_pdc_tot:
            print(f"  DC Power Tot:  {format_value(data.cal_pdc_tot / 1000, 'kW', 3)}")
        if data.cal_efficiency:
            print(f"  Efficiency:    {format_value(data.cal_efficiency, '%', 2)}")


def main():
    """Main application loop."""
    print_header()
    
    # Target subnet for inverter discovery
    TARGET_SUBNET = "192.168.192"
    
    # Create SBFspot instance
    spot = SBFspot(password="0000")
    
    try:
        print("Initializing network...")
        spot.eth.connect()
        print("✓ Network initialized\n")
        
        # Discovery
        print(f"Searching for SMA inverters in {TARGET_SUBNET}.x subnet (3 sec timeout)...")
        all_inverters = spot.discover(timeout=3.0)
        
        # Filter by subnet
        inverters = [inv for inv in all_inverters if inv.ip_address.startswith(TARGET_SUBNET + ".")]
        
        if not all_inverters:
            print("\n❌ No inverters found on the network.")
            print("\nTroubleshooting:")
            print("  • Make sure you're on the same network as the inverter")
            print("  • Check if the inverter is powered on and awake")
            print("  • Verify firewall settings (UDP port 9522)")
            print("  • Try specifying IP directly: python monitor.py <IP_ADDRESS>\n")
            return 1
        elif not inverters:
            print(f"\n❌ Found {len(all_inverters)} inverter(s) but none in {TARGET_SUBNET}.x subnet:")
            for inv in all_inverters:
                print(f"  - {inv.ip_address}")
            print(f"\nPlease update TARGET_SUBNET in monitor.py to match your network.\n")
            return 1
        
        print(f"✓ Found {len(inverters)} inverter(s) in {TARGET_SUBNET}.x:\n")
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
