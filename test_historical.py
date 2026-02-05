import sys
import os
from datetime import datetime

# Adjust path
sys.path.insert(0, os.path.abspath('.'))

from sbfspot_python import SBFspot

def test_historical():
    target_ip = "192.168.192.100"
    print(f"Connecting to {target_ip} for historical data test...")
    
    with SBFspot(target_ip, password="0000") as spot:
        print("Login success. Fetching historical data for today...")
        data = spot.get_archive_day_data()
        
        if data.has_day_data:
            print(f"✓ Found {len(data.day_data)} historical records.")
            # Show last 10 records
            print("\nLast 10 records:")
            for rec in data.day_data[-10:]:
                print(f"  {rec.datetime.strftime('%H:%M:%S')} - {rec.total_wh} Wh ({rec.watt:.1f} W)")
        else:
            print("❌ No historical records found.")

if __name__ == "__main__":
    test_historical()
