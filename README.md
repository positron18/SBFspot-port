# SBFspot Python

A Python port of [SBFspot](https://github.com/SBFspot/SBFspot) for reading data from SMA solar inverters via Speedwire (Ethernet/UDP).

## Features

- ✅ **Auto-discovery** of SMA inverters on local network
- ✅ **Complete protocol support** for Speedwire/Ethernet communication
- ✅ **All inverter data**: Power (AC/DC), Voltage, Current, Energy, Frequency
- ✅ **Battery support** for hybrid inverters (voltage, current, SoC)
- ✅ **Simple API** with context manager support
- ✅ **No dependencies** - uses only Python stdlib (3.8+)
- ✅ **CLI monitor** application included

## Quick Start

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/sbfspot-python.git
cd sbfspot-python
```

### Usage

```python
from sbfspot_python import SBFspot

# Auto-discover and connect
with SBFspot() as spot:
    inverters = spot.discover()
    if inverters:
        spot.connect(inverters[0])
        spot.login()
        data = spot.read_all()
        print(f"Power: {data.power_kw:.2f} kW")
```

Or connect directly:

```python
with SBFspot("192.168.1.100") as spot:
    spot.login()
    data = spot.read_all()
    print(data)
```

### CLI Monitor

Quick monitoring tool included:

```bash
python3 monitor.py
```

## Documentation

See [`sbfspot_python/README.md`](sbfspot_python/README.md) for full API documentation.

## Important Notes

### Standby Mode
This library **cannot wake up** an inverter from standby. SMA inverters automatically enter standby at night and wake when solar panels produce sufficient voltage (~150-200V). The Speedwire interface may be disabled during standby.

### Compatibility
- **Supported**: SMA inverters with Speedwire/Ethernet interface
- **Not supported**: Bluetooth-only models (use original SBFspot for BT)
- **Default password**: "0000" (user level)

## Project Structure

```
.
├── sbfspot_python/        # Main library
│   ├── __init__.py       # Package exports
│   ├── constants.py      # Protocol constants
│   ├── models.py         # Data models
│   ├── protocol.py       # Packet building
│   ├── ethernet.py       # UDP communication
│   ├── sbfspot.py        # Main class
│   └── example.py        # Usage example
└── monitor.py            # CLI monitor app
```

## License

Based on [SBFspot](https://github.com/SBFspot/SBFspot) - Attribution-NonCommercial-ShareAlike 3.0 (CC BY-NC-SA 3.0)

## Credits

Original SBFspot project by SBF: https://github.com/SBFspot/SBFspot

This Python port implements the Speedwire protocol based on analysis of the original C++ source code.
