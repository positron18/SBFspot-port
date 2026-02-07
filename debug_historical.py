import sys
from datetime import datetime
import binascii
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sbfspot_python import SBFspot
from sbfspot_python.constants import COMMANDS
from sbfspot_python.protocol import parse_packet_header, get_long, get_longlong

def debug_historical():
    target_ip = "192.168.192.100"
    print(f"Connecting to {target_ip}...")
    
    with SBFspot(target_ip, password="0000") as spot:
        print("Login success.")
        date = datetime.now()
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_ts = int(start_of_day.timestamp())
        
        print(f"Requesting data for {start_of_day} (TS: {start_ts})")
        
        cmd = 0x70100200  # ArchiveEventData (User)
        first = start_ts
        last = int(datetime.now().timestamp())
        
        print(f"Command: {cmd:#x}, First: {first}, Last: {last}")
        
        data = spot._request_data(cmd, first, last, ctrl=0xA0)
        
        if data:
            print(f"✓ Received {len(data)} bytes")
            print(f"Hex: {binascii.hexlify(data).decode()}")
            
            # Check packet header
            susy_id, serial, error_code, frag, pkt_id = parse_packet_header(data)
            print(f"Header: SUSY={susy_id}, Serial={serial}, Error={error_code:#x}, Frag={frag}, PktID={pkt_id}")
            
            if error_code != 0:
                print(f"⚠️  Inverter returned error code: {error_code:#x}")
                if error_code == 0x17:
                    print("Error 0x17 usually means 'Invalid arguments' or 'Data not available'")
            
            payload_start = 14 + 6 + 8 + 8 + 2 + 2 + 2 # 50
            if len(data) > payload_start + 12:
                cmd_ret = get_long(data, payload_start)
                f = get_long(data, payload_start + 4)
                l = get_long(data, payload_start + 8)
                print(f"Payload Header: Command={cmd_ret:#x}, First={f}, Last={l}")
        else:
            print("❌ No response to historical data request")

if __name__ == "__main__":
    debug_historical()
