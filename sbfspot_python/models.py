"""
Data models for SBFspot Python port.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class MPPTData:
    """Maximum Power Point Tracker data."""
    pdc: int = 0       # DC Power in W
    udc: int = 0       # DC Voltage in V * 100
    idc: int = 0       # DC Current in mA
    
    @property
    def power_kw(self) -> float:
        """DC power in kW."""
        return self.pdc / 1000.0
    
    @property
    def voltage(self) -> float:
        """DC voltage in V."""
        return self.udc / 100.0
    
    @property
    def current(self) -> float:
        """DC current in A."""
        return self.idc / 1000.0


@dataclass
class DayData:
    """Historical data record for a specific point in time."""
    datetime: Optional[datetime] = None
    total_wh: int = 0  # Total energy produced since installation (Wh)
    watt: float = 0.0  # Average power during the interval (W)
    
    @property
    def energy_total_kwh(self) -> float:
        """Total energy in kWh."""
        return self.total_wh / 1000.0


@dataclass
class InverterData:
    """
    Data container for SMA inverter readings.
    
    All raw values are stored in their native format:
    - Voltages: V * 100
    - Currents: mA
    - Power: W
    - Energy: Wh
    - Frequency: Hz * 100
    - Temperature: °C * 100
    
    Use the property methods for human-readable values.
    """
    # Connection info
    ip_address: str = ""
    susy_id: int = 0
    serial: int = 0
    net_id: int = 0
    
    # Device info
    device_name: str = ""
    device_type: str = ""
    device_class: str = ""
    device_class_id: int = 0
    sw_version: str = ""
    
    # Status
    device_status: int = 0
    grid_relay_status: int = 0
    
    # AC Power readings (raw: W)
    total_pac: int = 0
    pac1: int = 0
    pac2: int = 0
    pac3: int = 0
    
    # AC Voltage readings (raw: V * 100)
    uac1: int = 0
    uac2: int = 0
    uac3: int = 0
    
    # AC Current readings (raw: mA)
    iac1: int = 0
    iac2: int = 0
    iac3: int = 0
    
    # Grid frequency (raw: Hz * 100)
    grid_freq: int = 0
    
    # DC inputs (MPP trackers)
    mpp: Dict[int, MPPTData] = field(default_factory=dict)
    
    # Energy (raw: Wh)
    e_today: int = 0
    e_total: int = 0
    
    # Operation time (raw: seconds)
    operation_time: int = 0
    feed_in_time: int = 0
    
    # Temperature (raw: °C * 100)
    temperature: int = 0
    
    # Battery info
    bat_charge_status: int = 0
    bat_voltage: int = 0
    bat_current: int = 0
    bat_temperature: int = 0
    has_battery: bool = False
    
    # Grid metering
    metering_grid_w_out: int = 0
    metering_grid_w_in: int = 0
    
    # Historical data
    day_data: List[DayData] = field(default_factory=list)
    has_day_data: bool = False
    
    # Timestamps
    inverter_datetime: Optional[datetime] = None
    wakeup_time: Optional[datetime] = None
    sleep_time: Optional[datetime] = None
    
    # Calculated values
    cal_pdc_tot: int = 0
    cal_efficiency: float = 0.0
    
    # --- Property methods for human-readable values ---
    
    @property
    def power_kw(self) -> float:
        """Total AC power in kW."""
        return self.total_pac / 1000.0
    
    @property
    def voltage_l1(self) -> float:
        """Phase 1 voltage in V."""
        return self.uac1 / 100.0
    
    @property
    def voltage_l2(self) -> float:
        """Phase 2 voltage in V."""
        return self.uac2 / 100.0
    
    @property
    def voltage_l3(self) -> float:
        """Phase 3 voltage in V."""
        return self.uac3 / 100.0
    
    @property
    def current_l1(self) -> float:
        """Phase 1 current in A."""
        return self.iac1 / 1000.0
    
    @property
    def current_l2(self) -> float:
        """Phase 2 current in A."""
        return self.iac2 / 1000.0
    
    @property
    def current_l3(self) -> float:
        """Phase 3 current in A."""
        return self.iac3 / 1000.0
    
    @property
    def frequency(self) -> float:
        """Grid frequency in Hz."""
        return self.grid_freq / 100.0
    
    @property
    def temp_celsius(self) -> float:
        """Temperature in °C."""
        return self.temperature / 100.0
    
    @property
    def energy_today_kwh(self) -> float:
        """Today's energy in kWh."""
        return self.e_today / 1000.0
    
    @property
    def energy_total_kwh(self) -> float:
        """Total energy in kWh."""
        return self.e_total / 1000.0
    
    @property
    def operation_hours(self) -> float:
        """Operation time in hours."""
        return self.operation_time / 3600.0
    
    @property
    def dc_power_total(self) -> int:
        """Total DC power from all MPP trackers in W."""
        return sum(m.pdc for m in self.mpp.values())
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        lines = [
            f"=== {self.device_name or 'SMA Inverter'} ===",
            f"Type: {self.device_type}",
            f"Serial: {self.serial}",
            f"IP: {self.ip_address}",
            "",
            f"AC Power: {self.power_kw:.3f} kW",
            f"  L1: {self.pac1}W @ {self.voltage_l1:.1f}V / {self.current_l1:.2f}A",
        ]
        if self.pac2 or self.uac2:
            lines.append(f"  L2: {self.pac2}W @ {self.voltage_l2:.1f}V / {self.current_l2:.2f}A")
        if self.pac3 or self.uac3:
            lines.append(f"  L3: {self.pac3}W @ {self.voltage_l3:.1f}V / {self.current_l3:.2f}A")
        
        lines.append(f"Grid Frequency: {self.frequency:.2f} Hz")
        lines.append("")
        
        for idx, mpp_data in self.mpp.items():
            if mpp_data.pdc > 0 or mpp_data.udc > 0:
                lines.append(f"DC Input {idx}: {mpp_data.power_kw:.3f} kW @ {mpp_data.voltage:.1f}V / {mpp_data.current:.2f}A")
        
        lines.extend([
            "",
            f"Energy Today: {self.energy_today_kwh:.2f} kWh",
            f"Energy Total: {self.energy_total_kwh:.2f} kWh",
        ])
        
        if self.temperature:
            lines.append(f"Temperature: {self.temp_celsius:.1f} °C")
        
        return "\n".join(lines)
