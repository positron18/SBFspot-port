"""
Constants for SBFspot Python port.
Derived from the original SBFspot C++ source code.
"""

from enum import IntEnum

# Protocol signatures
SMA_SIGNATURE = b'SMA\x00'
ETH_L2SIGNATURE = 0x65601000
BTH_L2SIGNATURE = 0x656003FF

# Network settings
DEFAULT_PORT = 9522
MULTICAST_ADDRESS = "239.12.255.254"
SOCKET_TIMEOUT = 2.0

# User groups for login
UG_USER = 0x07
UG_INSTALLER = 0x0A

# Well-known SUSyIDs
SID_MULTIGATE = 175
SID_SB240 = 244

# Application identity
APP_SUSYID = 125

# Universal addresses
ANY_SUSYID = 0xFFFF
ANY_SERIAL = 0xFFFFFFFF

# Packet buffer size
COMMBUFSIZE = 2048

# Max inverters supported
MAX_INVERTERS = 10

# Max retry count
MAX_RETRY = 3


class LriDef(IntEnum):
    """Logical Record Identifier definitions for data queries."""
    OperationHealth = 0x00214800          # Device status
    CoolsysTmpNom = 0x00237700            # Temperature
    DcMsWatt = 0x00251E00                 # DC power input (PDC1/PDC2)
    MeteringTotWhOut = 0x00260100         # Total yield (ETOTAL)
    MeteringDyWhOut = 0x00262200          # Day yield (ETODAY)
    GridMsTotW = 0x00263F00               # Total AC power (PACTOT)
    BatChaStt = 0x00295A00                # Battery charge status
    OperationHealthSttOk = 0x00411E00     # Nominal power OK mode
    OperationHealthSttWrn = 0x00411F00    # Nominal power Warning mode
    OperationHealthSttAlm = 0x00412000    # Nominal power Fault mode
    OperationGriSwStt = 0x00416400        # Grid relay status
    OperationRmgTms = 0x00416600          # Wait time until feed-in
    DcMsVol = 0x00451F00                  # DC voltage (UDC1/UDC2)
    DcMsAmp = 0x00452100                  # DC current (IDC1/IDC2)
    MeteringPvMsTotWhOut = 0x00462300     # PV generation counter
    MeteringGridMsTotWhOut = 0x00462400   # Grid feed-in counter
    MeteringGridMsTotWhIn = 0x00462500    # Grid reference counter
    MeteringTotOpTms = 0x00462E00         # Operating time
    MeteringTotFeedTms = 0x00462F00       # Feed-in time
    MeteringGridMsTotWOut = 0x00463600    # Power grid feed-in
    MeteringGridMsTotWIn = 0x00463700     # Power grid reference
    GridMsWphsA = 0x00464000              # Power L1 (PAC1)
    GridMsWphsB = 0x00464100              # Power L2 (PAC2)
    GridMsWphsC = 0x00464200              # Power L3 (PAC3)
    GridMsPhVphsA = 0x00464800            # Voltage L1 (UAC1)
    GridMsPhVphsB = 0x00464900            # Voltage L2 (UAC2)
    GridMsPhVphsC = 0x00464A00            # Voltage L3 (UAC3)
    GridMsAphsA_1 = 0x00465000            # Current L1 (IAC1)
    GridMsAphsB_1 = 0x00465100            # Current L2 (IAC2)
    GridMsAphsC_1 = 0x00465200            # Current L3 (IAC3)
    GridMsAphsA = 0x00465300              # Current L1 alt
    GridMsAphsB = 0x00465400              # Current L2 alt
    GridMsAphsC = 0x00465500              # Current L3 alt
    GridMsHz = 0x00465700                 # Grid frequency
    BatDiagCapacThrpCnt = 0x00491E00      # Battery charge throughputs
    BatDiagTotAhIn = 0x00492600           # Battery charge Ah
    BatDiagTotAhOut = 0x00492700          # Battery discharge Ah
    BatTmpVal = 0x00495B00                # Battery temperature
    BatVol = 0x00495C00                   # Battery voltage
    BatAmp = 0x00495D00                   # Battery current
    NameplateLocation = 0x00821E00        # Device name
    NameplateMainModel = 0x00821F00       # Device class
    NameplateModel = 0x00822000           # Device type
    NameplatePkgRev = 0x00823400          # Software version


class DataType(IntEnum):
    """SMA data type identifiers."""
    DT_ULONG = 0
    DT_STATUS = 8
    DT_STRING = 16
    DT_FLOAT = 32
    DT_SLONG = 64


class DeviceClass(IntEnum):
    """Device class identifiers."""
    AllDevices = 8000
    SolarInverter = 8001
    WindTurbineInverter = 8002
    BatteryInverter = 8007
    ChargingStation = 8008
    HybridInverter = 8009
    Consumer = 8033
    SensorSystem = 8064
    ElectricityMeter = 8065


# Command definitions for getInverterData
# Format: (command, first_lri, last_lri)
COMMANDS = {
    'EnergyProduction': (0x54000200, 0x00260100, 0x002622FF),
    'SpotDCPower': (0x53800200, 0x00251E00, 0x00251EFF),
    'SpotDCVoltage': (0x53800200, 0x00451F00, 0x004521FF),
    'SpotACPower': (0x51000200, 0x00464000, 0x004642FF),
    'SpotACVoltage': (0x51000200, 0x00464800, 0x004655FF),
    'SpotGridFrequency': (0x51000200, 0x00465700, 0x004657FF),
    'SpotACTotalPower': (0x51000200, 0x00263F00, 0x00263FFF),
    'TypeLabel': (0x58000200, 0x00821E00, 0x008220FF),
    'SoftwareVersion': (0x58000200, 0x00823400, 0x008234FF),
    'DeviceStatus': (0x51800200, 0x00214800, 0x002148FF),
    'GridRelayStatus': (0x51800200, 0x00416400, 0x004164FF),
    'OperationTime': (0x54000200, 0x00462E00, 0x00462FFF),
    'BatteryChargeStatus': (0x51000200, 0x00295A00, 0x00295AFF),
    'BatteryInfo': (0x51000200, 0x00491E00, 0x00495DFF),
    'InverterTemperature': (0x52000200, 0x00237700, 0x002377FF),
    'MeteringGridMsTotW': (0x51000200, 0x00463600, 0x004637FF),
}

# FCS (Frame Check Sequence) lookup table for Bluetooth checksum
# Used for packet validation
FCS_TABLE = [
    0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,
    0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,
    0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,
    0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,
    0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,
    0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,
    0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,
    0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,
    0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,
    0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,
    0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,
    0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,
    0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,
    0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,
    0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,
    0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,
    0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,
    0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,
    0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,
    0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,
    0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,
    0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,
    0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,
    0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,
    0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,
    0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,
    0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,
    0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,
    0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,
    0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,
    0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,
    0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78,
]

# NaN values for detecting invalid data
NAN_S32 = 0x80000000
NAN_U32 = 0xFFFFFFFF
NAN_S64 = 0x8000000000000000
NAN_U64 = 0xFFFFFFFFFFFFFFFF
