# SBFspot Python Port

A Python library for communicating with SMA solar inverters via Speedwire (Ethernet/UDP).

Based on the original [SBFspot](https://github.com/SBFspot/SBFspot) C++ project.

## Installation

No external dependencies required - uses only Python standard library (3.8+).

```bash
cd "/Users/Giove/Progetti/SBFspot port"
```

## Quick Start

```python
from sbfspot_python import SBFspot

# Connect to inverter
with SBFspot("192.168.1.100") as spot:
    spot.login()
    data = spot.read_all()
    
    print(f"Power: {data.power_kw:.2f} kW")
    print(f"Today: {data.energy_today_kwh:.2f} kWh")
    print(f"Total: {data.energy_total_kwh:.2f} kWh")
```

## Auto-Discovery

```python
from sbfspot_python import SBFspot

spot = SBFspot()
spot.eth.connect()
inverters = spot.discover()

for inv in inverters:
    print(f"Found: {inv.ip_address}")
```

## API Reference

| Method | Description |
|--------|-------------|
| `SBFspot(ip, password)` | Create connection (password default: "0000") |
| `discover()` | Find inverters on network |
| `connect(ip)` | Connect to specific inverter |
| `login()` | Authenticate |
| `read_all()` | Get all data |
| `get_spot_data()` | Get current power/voltage |
| `get_energy_data()` | Get energy counters |
| `get_device_info()` | Get device identification |
| `get_battery_data()` | Get battery info (hybrid inverters) |
| `get_temperature()` | Get inverter temperature |
| `logout()` / `close()` | Disconnect |

## Available Data

| Property | Unit | Description |
|----------|------|-------------|
| `power_kw` | kW | Total AC power |
| `voltage_l1/l2/l3` | V | AC voltage per phase |
| `current_l1/l2/l3` | A | AC current per phase |
| `frequency` | Hz | Grid frequency |
| `energy_today_kwh` | kWh | Today's production |
| `energy_total_kwh` | kWh | Lifetime production |
| `temp_celsius` | °C | Inverter temperature |
| `mpp[n].power_kw` | kW | DC input per tracker |
| `bat_charge_status` | % | Battery state of charge |
| `bat_voltage` | V×100 | Battery voltage |
| `bat_current` | mA | Battery current (+charging) |
| `has_battery` | bool | True if battery present |

## Module Structure

```
sbfspot_python/
├── __init__.py      # Package exports
├── constants.py     # Protocol constants, LRI codes
├── models.py        # InverterData, MPPTData
├── protocol.py      # Packet building
├── ethernet.py      # UDP socket, multicast
├── sbfspot.py       # Main SBFspot class
└── example.py       # Usage demonstration
```

## Running the Example

```bash
python3 sbfspot_python/example.py [INVERTER_IP]
```

## Important: Standby Mode

> **Note:** This library cannot "wake up" an inverter from standby mode.

SMA inverters automatically enter standby at night when solar panels stop producing power. During standby:
- The inverter may disable its Speedwire network interface to save energy
- No remote command exists to force the inverter on (this is a safety feature)
- The inverter wakes automatically when DC voltage from panels reaches ~150-200V

The `WakeupTime` and `SleepTime` fields in `InverterData` are **read-only timestamps** indicating when the inverter last changed state - they cannot be used to control the inverter.

## License

Based on SBFspot - Attribution-NonCommercial-ShareAlike 3.0 (CC BY-NC-SA 3.0)
