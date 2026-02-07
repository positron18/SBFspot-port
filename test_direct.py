import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sbfspot_python import SBFspot

def test_direct():
    target_ip = "192.168.192.100"
    print(f"Connecting directly to {target_ip}...")
    spot = SBFspot(password="0000")
    try:
        spot.eth.connect()
        spot.connect(target_ip)
        print(f"✓ Connected (SUSyID: {spot.inverter.susy_id}, Serial: {spot.inverter.serial})")
        spot.login()
        print("✓ Authenticated")
        data = spot.read_all()
        print(f"✓ Data received: Power = {data.power_kw} kW")
        spot.logout()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        spot.close()

if __name__ == "__main__":
    test_direct()
