"""
Main SBFspot class for SMA inverter communication.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional

from .constants import (
    COMMANDS, UG_USER, MAX_RETRY, LriDef, DataType, DeviceClass,
    ANY_SUSYID, ANY_SERIAL, NAN_S32, NAN_U32
)
from .models import InverterData, MPPTData, DayData
from .protocol import (
    PacketBuilder, get_short, get_long, get_longlong,
    get_long_signed, is_nan, parse_packet_header, version_to_string
)
from .ethernet import EthernetConnection


logger = logging.getLogger(__name__)


class SBFspotError(Exception):
    """Base exception for SBFspot errors."""
    pass


class ConnectionError(SBFspotError):
    """Connection-related errors."""
    pass


class AuthenticationError(SBFspotError):
    """Authentication-related errors."""
    pass


class SBFspot:
    """
    High-level interface for communicating with SMA solar inverters.
    
    Usage:
        # Auto-discover and connect
        with SBFspot() as spot:
            inverters = spot.discover()
            if inverters:
                spot.connect(inverters[0])
                spot.login()
                data = spot.read_all()
                print(data)
    
        # Direct connection
        with SBFspot("192.168.1.100") as spot:
            spot.login()
            data = spot.read_all()
            print(f"Power: {data.power_kw} kW")
    """
    
    def __init__(self, ip_address: Optional[str] = None, password: str = "0000"):
        """
        Initialize SBFspot connection.
        
        Args:
            ip_address: Inverter IP address (None for discovery mode)
            password: User password (default "0000")
        """
        self.ip_address = ip_address
        self.password = password
        self.eth = EthernetConnection()
        self.protocol = PacketBuilder()
        self.inverter = InverterData()
        self._connected = False
        self._logged_in = False
    
    def discover(self, timeout: float = 3.0) -> List[InverterData]:
        """
        Discover SMA inverters on the local network.
        
        Args:
            timeout: Time to wait for responses in seconds
            
        Returns:
            List of discovered inverters (with IP address populated)
        """
        if not self.eth.sock:
            self.eth.connect()
        
        discovery_packet = self.protocol.build_discovery_packet()
        ip_list = self.eth.discover_inverters(discovery_packet, timeout)
        
        inverters = []
        for ip in ip_list:
            inv = InverterData(ip_address=ip)
            inverters.append(inv)
            logger.info(f"Discovered inverter at {ip}")
        
        return inverters
    
    def connect(self, target: Optional[str] = None) -> bool:
        """
        Connect to inverter and retrieve SUSyID/Serial.
        
        Args:
            target: IP address or InverterData object
            
        Returns:
            True if connected successfully
        """
        if isinstance(target, InverterData):
            self.ip_address = target.ip_address
        elif isinstance(target, str):
            self.ip_address = target
        
        if not self.ip_address:
            raise ConnectionError("No IP address specified")
        
        if not self.eth.sock:
            self.eth.connect()
        
        # Send init packet
        init_packet = self.protocol.build_init_packet(ANY_SUSYID, ANY_SERIAL)
        self.eth.send(init_packet, self.ip_address)
        
        # Receive response
        data, sender = self.eth.receive_with_filter(expected_ip=self.ip_address)
        
        if not data:
            raise ConnectionError(f"No response from inverter at {self.ip_address}")
        
        # Parse response to get SUSyID and Serial
        susy_id, serial, error_code, _, packet_id = parse_packet_header(data)
        
        self.inverter = InverterData(
            ip_address=self.ip_address,
            susy_id=susy_id,
            serial=serial
        )
        
        self._connected = True
        logger.info(f"Connected to inverter: SUSyID={susy_id}, Serial={serial}")
        
        # Logoff any previous session
        self._send_logoff()
        
        return True
    
    def login(self, user_group: int = UG_USER) -> bool:
        """
        Authenticate with the inverter.
        
        Args:
            user_group: UG_USER (0x07) or UG_INSTALLER (0x0A)
            
        Returns:
            True if login successful
        """
        if not self._connected:
            raise ConnectionError("Not connected. Call connect() first.")
        
        login_packet = self.protocol.build_login_packet(
            self.inverter.susy_id,
            self.inverter.serial,
            self.password,
            user_group
        )
        
        self.eth.send(login_packet, self.ip_address)
        
        # Wait for response
        data, _ = self.eth.receive_with_filter(expected_ip=self.ip_address)
        
        if not data:
            raise AuthenticationError("No response to login request")
        
        # Check error code
        _, _, error_code, _, _ = parse_packet_header(data)
        
        if error_code == 0x0100:
            raise AuthenticationError("Invalid password")
        elif error_code != 0:
            raise AuthenticationError(f"Login failed with error code: {error_code:#x}")
        
        self._logged_in = True
        logger.info("Login successful")
        
        return True
    
    def logout(self):
        """Log off from the inverter."""
        if self._logged_in:
            self._send_logoff()
            self._logged_in = False
            logger.info("Logged out")
    
    def _send_logoff(self):
        """Send logoff packet."""
        logoff_packet = self.protocol.build_logoff_packet()
        self.eth.send(logoff_packet, self.ip_address)
    
    def close(self):
        """Close connection to inverter."""
        if self._logged_in:
            self.logout()
        self.eth.close()
        self._connected = False
        logger.info("Connection closed")
    
    def _request_data(self, command: int, first: int, last: int, ctrl: int = 0xA0) -> Optional[bytes]:
        """
        Send data request and receive response.
        
        Args:
            command: Command code
            first: First LRI code
            last: Last LRI code
            ctrl: Control byte (0xA0 for spot, 0xE0 for archive)
            
        Returns:
            Response packet data or None if failed
        """
        if not self._connected:
            raise ConnectionError("Not connected")
        
        for retry in range(MAX_RETRY):
            packet = self.protocol.build_data_request_packet(
                self.inverter.susy_id,
                self.inverter.serial,
                command, first, last,
                ctrl=ctrl
            )
            
            self.eth.send(packet, self.ip_address)
            
            data, _ = self.eth.receive_with_filter(expected_ip=self.ip_address)
            
            if data:
                return data
            
            logger.debug(f"Retry {retry + 1}/{MAX_RETRY}")
        
        return None

    def _parse_data_response(self, data: bytes):
        """
        Parse data response and update inverter data.
        
        Args:
            data: Response packet data
        """
        # Data starts at offset 41 in the packet
        # Each record has: code(4) + datetime(4) + data(variable)
        
        # Get record size from packet
        offset = 14 + 6 + 8 + 8 + 2 + 2 + 2  # L1 + L2 start + dest + src + err/frag/pkt
        longwords = data[14 + 4]  # longwords byte in L2 header
        
        # Calculate record size based on LRI range
        first_lri = get_long(data, offset + 4)
        last_lri = get_long(data, offset + 8)
        num_records = last_lri - first_lri + 1 if last_lri > first_lri else 1
        
        # Estimate record size (minimum is 12 bytes: code + datetime + value)
        payload_start = offset + 12  # After command params
        payload_len = len(data) - payload_start - 4  # Exclude trailer
        
        if num_records > 0 and payload_len > 0:
            record_size = max(12, payload_len // num_records)
        else:
            record_size = 28  # Default
        
        # Try different record sizes if parsing fails
        for try_size in [record_size, 28, 16, 40, 12]:
            try:
                self._parse_records(data, payload_start, try_size)
                break
            except (IndexError, struct.error):
                continue
    
    def _parse_records(self, data: bytes, start_offset: int, record_size: int):
        """Parse individual data records."""
        import struct
        
        pos = start_offset
        end = len(data) - 4  # Exclude trailer
        
        while pos + record_size <= end:
            code = get_long(data, pos)
            lri = LriDef(code & 0x00FFFF00) if (code & 0x00FFFF00) in [e.value for e in LriDef] else None
            cls = code & 0xFF
            data_type = (code >> 24) & 0xFF
            timestamp = get_long(data, pos + 4)
            
            if lri is None:
                pos += record_size
                continue
            
            # Read value based on record size
            if record_size == 16:
                value64 = get_longlong(data, pos + 8)
                if is_nan(value64, signed=False, bits=64):
                    value64 = 0
                value = value64
            else:
                value = get_long_signed(data, pos + 16) if record_size >= 20 else get_long_signed(data, pos + 8)
                if is_nan(value, signed=True, bits=32) or is_nan(value, signed=False, bits=32):
                    value = 0
            
            # Map LRI to inverter data fields
            self._map_lri_value(lri, cls, data_type, value, timestamp, data, pos, record_size)
            
            pos += record_size
    
    def _map_lri_value(self, lri: LriDef, cls: int, data_type: int, 
                       value: int, timestamp: int, data: bytes, pos: int, record_size: int):
        """Map LRI value to InverterData field."""
        
        dt = datetime.fromtimestamp(timestamp) if timestamp > 0 else None
        
        if lri == LriDef.GridMsTotW:
            self.inverter.total_pac = value
            self.inverter.sleep_time = dt
            
        elif lri == LriDef.GridMsWphsA:
            self.inverter.pac1 = value
            
        elif lri == LriDef.GridMsWphsB:
            self.inverter.pac2 = value
            
        elif lri == LriDef.GridMsWphsC:
            self.inverter.pac3 = value
            
        elif lri == LriDef.GridMsPhVphsA:
            self.inverter.uac1 = value
            
        elif lri == LriDef.GridMsPhVphsB:
            self.inverter.uac2 = value
            
        elif lri == LriDef.GridMsPhVphsC:
            self.inverter.uac3 = value
            
        elif lri in (LriDef.GridMsAphsA_1, LriDef.GridMsAphsA):
            self.inverter.iac1 = value
            
        elif lri in (LriDef.GridMsAphsB_1, LriDef.GridMsAphsB):
            self.inverter.iac2 = value
            
        elif lri in (LriDef.GridMsAphsC_1, LriDef.GridMsAphsC):
            self.inverter.iac3 = value
            
        elif lri == LriDef.GridMsHz:
            self.inverter.grid_freq = value
            
        elif lri == LriDef.DcMsWatt:
            if cls not in self.inverter.mpp:
                self.inverter.mpp[cls] = MPPTData()
            self.inverter.mpp[cls].pdc = value
            
        elif lri == LriDef.DcMsVol:
            if cls not in self.inverter.mpp:
                self.inverter.mpp[cls] = MPPTData()
            self.inverter.mpp[cls].udc = value
            
        elif lri == LriDef.DcMsAmp:
            if cls not in self.inverter.mpp:
                self.inverter.mpp[cls] = MPPTData()
            self.inverter.mpp[cls].idc = value
            
        elif lri == LriDef.MeteringTotWhOut:
            self.inverter.e_total = value
            self.inverter.inverter_datetime = dt
            
        elif lri == LriDef.MeteringDyWhOut:
            self.inverter.e_today = value
            self.inverter.inverter_datetime = dt
            
        elif lri == LriDef.MeteringTotOpTms:
            self.inverter.operation_time = value
            
        elif lri == LriDef.MeteringTotFeedTms:
            self.inverter.feed_in_time = value
            
        elif lri == LriDef.NameplateLocation:
            # String data
            if record_size > 8:
                try:
                    name_bytes = data[pos + 8:pos + record_size]
                    self.inverter.device_name = name_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')
                    self.inverter.wakeup_time = dt
                except:
                    pass
                    
        elif lri == LriDef.NameplatePkgRev:
            if record_size >= 28:
                version = get_long(data, pos + 24)
                self.inverter.sw_version = version_to_string(version)
                
        elif lri == LriDef.NameplateModel:
            if data_type == DataType.DT_STATUS and record_size >= 12:
                attr = get_long(data, pos + 8)
                self.inverter.device_type = f"Type_{attr}"  # Would need tag lookup
                
        elif lri == LriDef.NameplateMainModel:
            if data_type == DataType.DT_STATUS and record_size >= 12:
                attr = get_long(data, pos + 8)
                self.inverter.device_class_id = attr
                try:
                    self.inverter.device_class = DeviceClass(attr).name
                except ValueError:
                    self.inverter.device_class = f"Class_{attr}"
                    
        elif lri == LriDef.OperationHealth:
            if data_type == DataType.DT_STATUS and record_size >= 12:
                self.inverter.device_status = get_long(data, pos + 8)
                
        elif lri == LriDef.OperationGriSwStt:
            if data_type == DataType.DT_STATUS and record_size >= 12:
                self.inverter.grid_relay_status = get_long(data, pos + 8)
                
        elif lri == LriDef.CoolsysTmpNom:
            self.inverter.temperature = value
            
        elif lri == LriDef.BatChaStt:
            self.inverter.bat_charge_status = value
            self.inverter.has_battery = True
            
        elif lri == LriDef.BatVol:
            self.inverter.bat_voltage = value
            
        elif lri == LriDef.BatAmp:
            self.inverter.bat_current = value
            
        elif lri == LriDef.BatTmpVal:
            self.inverter.bat_temperature = value
            
        elif lri == LriDef.MeteringGridMsTotWOut:
            self.inverter.metering_grid_w_out = value
            
        elif lri == LriDef.MeteringGridMsTotWIn:
            self.inverter.metering_grid_w_in = value
    
    def get_spot_data(self) -> InverterData:
        """
        Get current spot data (power, voltage, frequency).
        
        Returns:
            Updated InverterData with spot values
        """
        # Get AC total power
        cmd, first, last = COMMANDS['SpotACTotalPower']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        # Get AC power per phase
        cmd, first, last = COMMANDS['SpotACPower']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        # Get AC voltage
        cmd, first, last = COMMANDS['SpotACVoltage']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        # Get grid frequency
        cmd, first, last = COMMANDS['SpotGridFrequency']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        # Get DC power and voltage
        cmd, first, last = COMMANDS['SpotDCPower']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        cmd, first, last = COMMANDS['SpotDCVoltage']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        return self.inverter
    
    def get_archive_day_data(self, date: Optional[datetime] = None) -> InverterData:
        """
        Get historical daily production records.
        
        Args:
            date: The date to retrieve (defaults to today)
            
        Returns:
            Updated InverterData with day_data populated
        """
        if date is None:
            date = datetime.now()
            
        # Set start of day in UTC (SBFspot style)
        start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        start_ts = int(start_of_day.timestamp())
        
        # SBFspot uses start_ts - 600 and start_ts + 86100
        # Use 0xE0 control byte for archive requests
        cmd, _, _ = COMMANDS['ArchiveDayData']
        data = self._request_data(cmd, start_ts - 600, start_ts + 86100, ctrl=0xE0)
        
        if data:
            self._parse_archive_response(data)
            
        return self.inverter

    def _parse_archive_response(self, data: bytes):
        """Parse archive response and update historical data."""
        # Archive data starts at the same offset as spot data
        offset = 14 + 6 + 8 + 8 + 2 + 2 + 2 
        payload_start = offset + 12
        end = len(data) - 4
        
        prev_total_wh = 0
        prev_ts = 0
        
        self.inverter.day_data = []
        
        # Record size for ArchiveDayData is strictly 12 bytes in Ethernet
        record_size = 12
        
        pos = payload_start
        while pos + record_size <= end:
            ts = get_long(data, pos)
            total_wh = get_longlong(data, pos + 4)
            
            if ts > 0 and not is_nan(total_wh, signed=False, bits=64):
                dt = datetime.fromtimestamp(ts)
                
                # Calculate power (W) if possible
                watt = 0.0
                if prev_ts > 0 and ts > prev_ts:
                    watt = (total_wh - prev_total_wh) * 3600.0 / (ts - prev_ts)
                
                self.inverter.day_data.append(DayData(
                    datetime=dt,
                    total_wh=total_wh,
                    watt=watt
                ))
                
                prev_total_wh = total_wh
                prev_ts = ts
                
            pos += record_size
            
        if self.inverter.day_data:
            self.inverter.has_day_data = True
            
        return self.inverter

    def get_energy_data(self) -> InverterData:
        """
        Get energy production (today, total).
        
        Returns:
            Updated InverterData with energy values
        """
        cmd, first, last = COMMANDS['EnergyProduction']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        return self.inverter
    
    def get_device_info(self) -> InverterData:
        """
        Get device identification and status.
        
        Returns:
            Updated InverterData with device info
        """
        # Type label (name, type, class)
        cmd, first, last = COMMANDS['TypeLabel']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        # Software version
        cmd, first, last = COMMANDS['SoftwareVersion']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        # Device status
        cmd, first, last = COMMANDS['DeviceStatus']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        # Grid relay status
        cmd, first, last = COMMANDS['GridRelayStatus']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        return self.inverter
    
    def get_temperature(self) -> InverterData:
        """
        Get inverter temperature.
        
        Returns:
            Updated InverterData with temperature
        """
        cmd, first, last = COMMANDS['InverterTemperature']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        return self.inverter
    
    def get_battery_data(self) -> InverterData:
        """
        Get battery information (for hybrid inverters with storage).
        
        Returns:
            Updated InverterData with battery values:
            - bat_charge_status: Current state of charge (%)
            - bat_voltage: Battery voltage (V * 100)
            - bat_current: Battery current (mA, positive=charging)
            - bat_temperature: Battery temperature (°C * 100)
            - has_battery: True if battery data was found
        """
        # Battery charge status
        cmd, first, last = COMMANDS['BatteryChargeStatus']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        # Battery detailed info (voltage, current, temperature, etc.)
        cmd, first, last = COMMANDS['BatteryInfo']
        data = self._request_data(cmd, first, last)
        if data:
            self._parse_data_response(data)
        
        return self.inverter
    
    def read_all(self) -> InverterData:
        """
        Read all available data from inverter.
        
        Convenience method that calls all data retrieval methods.
        
        Returns:
            Complete InverterData
        """
        self.get_device_info()
        self.get_spot_data()
        self.get_energy_data()
        self.get_temperature()
        self.get_battery_data()
        self.get_archive_day_data()
        
        return self.inverter
    
    def __enter__(self):
        """Context manager entry."""
        self.eth.connect()
        if self.ip_address:
            self.connect(self.ip_address)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
