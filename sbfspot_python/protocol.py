"""
Protocol layer for SBFspot Python port.
Handles packet building, parsing, and checksum validation.
"""

import struct
import time
import random
from typing import Tuple, Optional

from .constants import (
    SMA_SIGNATURE, ETH_L2SIGNATURE, APP_SUSYID, ANY_SUSYID, ANY_SERIAL,
    FCS_TABLE, UG_USER, NAN_S32, NAN_U32, NAN_S64, NAN_U64, LriDef, DataType
)


class PacketBuilder:
    """
    Builds SMA Speedwire protocol packets.
    
    Packet structure (Ethernet/Speedwire):
    - L1 Header (14 bytes):
      - Magic: 'SMA\0' (4 bytes)
      - Unknown1: 0xA0020400 (4 bytes)  
      - Unknown2: 0xFFFFFFFF (4 bytes)
      - Length: 2 bytes (big-endian, payload only)
    - L2 Header (6 bytes):
      - Magic: 0x65601000 (4 bytes)
      - LongWords: 1 byte
      - Control: 1 byte
    - Endpoint data:
      - Destination: SUSyID (2) + Serial (4) + Ctrl (2)
      - Source: SUSyID (2) + Serial (4) + Ctrl (2)
      - ErrorCode (2), FragmentID (2), PacketID (2)
    - Payload data
    - Trailer (4 bytes of zeros)
    """
    
    def __init__(self):
        self.buffer = bytearray()
        self.packet_id = 1
        self.app_serial = self._generate_session_id()
    
    def _generate_session_id(self) -> int:
        """Generate a unique session ID."""
        random.seed(int(time.time()))
        return 900000000 + (random.randint(0, 0xFFFF) << 16 | random.randint(0, 0xFFFF)) % 100000000
    
    def reset(self):
        """Reset buffer for new packet."""
        self.buffer = bytearray()
    
    def write_byte(self, value: int):
        """Write a single byte."""
        self.buffer.append(value & 0xFF)
    
    def write_short(self, value: int):
        """Write a 16-bit little-endian value."""
        self.buffer.extend(struct.pack('<H', value & 0xFFFF))
    
    def write_long(self, value: int):
        """Write a 32-bit little-endian value."""
        self.buffer.extend(struct.pack('<I', value & 0xFFFFFFFF))
    
    def write_longlong(self, value: int):
        """Write a 64-bit little-endian value."""
        self.buffer.extend(struct.pack('<Q', value & 0xFFFFFFFFFFFFFFFF))
    
    def write_array(self, data: bytes):
        """Write a byte array."""
        self.buffer.extend(data)
    
    def build_eth_header(self):
        """Build Ethernet L1 header."""
        self.reset()
        # L1 Header
        self.buffer.extend(SMA_SIGNATURE)  # 'SMA\0'
        self.write_long(0xA0020400)         # Unknown1
        self.write_long(0xFFFFFFFF)         # Unknown2
        self.write_byte(0)                   # Length placeholder (hi)
        self.write_byte(0)                   # Length placeholder (lo)
    
    def build_packet(self, longwords: int, ctrl: int, ctrl2: int,
                     dst_susy_id: int, dst_serial: int):
        """Build L2 packet structure."""
        self.write_long(ETH_L2SIGNATURE)
        self.write_byte(longwords)
        self.write_byte(ctrl)
        # Destination endpoint
        self.write_short(dst_susy_id)
        self.write_long(dst_serial)
        self.write_short(ctrl2)
        # Source endpoint
        self.write_short(APP_SUSYID)
        self.write_long(self.app_serial)
        self.write_short(ctrl2)
        # Error code, Fragment ID
        self.write_short(0)
        self.write_short(0)
        # Packet ID with high bit set
        self.write_short(self.packet_id | 0x8000)
    
    def build_packet_trailer(self):
        """Add packet trailer (4 bytes of zeros)."""
        self.write_long(0)
    
    def finalize_packet_length(self):
        """Update the packet length field in L1 header."""
        # L1 header is 14 bytes, L2 starts at offset 14
        # Length field is at offset 12-13 (big-endian)
        data_length = len(self.buffer) - 14  # Exclude L1 header
        self.buffer[12] = (data_length >> 8) & 0xFF  # Hi byte
        self.buffer[13] = data_length & 0xFF          # Lo byte
    
    def get_packet(self) -> bytes:
        """Get the complete packet."""
        return bytes(self.buffer)
    
    def next_packet_id(self):
        """Increment packet ID for next request."""
        self.packet_id += 1
        if self.packet_id > 0x7FFF:
            self.packet_id = 1
    
    def build_discovery_packet(self) -> bytes:
        """Build inverter discovery packet."""
        self.reset()
        self.write_long(0x00414D53)  # 'SMA\0' reversed
        self.write_long(0xA0020400)
        self.write_long(0xFFFFFFFF)
        self.write_long(0x20000000)
        self.write_long(0x00000000)
        return self.get_packet()
    
    def build_init_packet(self, dst_susy_id: int, dst_serial: int) -> bytes:
        """Build initialization/identification packet."""
        self.next_packet_id()
        self.build_eth_header()
        self.build_packet(0x09, 0xA0, 0, dst_susy_id, dst_serial)
        self.write_long(0x00000200)
        self.write_long(0)
        self.write_long(0)
        self.write_long(0)
        self.build_packet_trailer()
        self.finalize_packet_length()
        return self.get_packet()
    
    def build_login_packet(self, dst_susy_id: int, dst_serial: int,
                           password: str, user_group: int = UG_USER) -> bytes:
        """Build login packet with encoded password."""
        self.next_packet_id()
        
        # Encode password
        enc_char = 0x88 if user_group == UG_USER else 0xBB
        pw = bytearray(12)
        for i, char in enumerate(password[:12]):
            pw[i] = (ord(char) + enc_char) & 0xFF
        for i in range(len(password), 12):
            pw[i] = enc_char
        
        now = int(time.time())
        
        self.build_eth_header()
        self.build_packet(0x0E, 0xA0, 0x0100, dst_susy_id, dst_serial)
        self.write_long(0xFFFD040C)
        self.write_long(user_group)
        self.write_long(0x00000384)  # Timeout = 900sec
        self.write_long(now)
        self.write_long(0)
        self.write_array(pw)
        self.build_packet_trailer()
        self.finalize_packet_length()
        return self.get_packet()
    
    def build_logoff_packet(self) -> bytes:
        """Build logoff packet."""
        self.next_packet_id()
        self.build_eth_header()
        self.build_packet(0x08, 0xA0, 0x0300, ANY_SUSYID, ANY_SERIAL)
        self.write_long(0xFFFD010E)
        self.write_long(0xFFFFFFFF)
        self.build_packet_trailer()
        self.finalize_packet_length()
        return self.get_packet()
    
    def build_data_request_packet(self, dst_susy_id: int, dst_serial: int,
                                   command: int, first: int, last: int) -> bytes:
        """Build data request packet."""
        self.next_packet_id()
        self.build_eth_header()
        self.build_packet(0x09, 0xA0, 0, dst_susy_id, dst_serial)
        self.write_long(command)
        self.write_long(first)
        self.write_long(last)
        self.build_packet_trailer()
        self.finalize_packet_length()
        return self.get_packet()


def get_short(buf: bytes, offset: int = 0) -> int:
    """Read 16-bit little-endian unsigned integer."""
    return struct.unpack_from('<H', buf, offset)[0]


def get_short_signed(buf: bytes, offset: int = 0) -> int:
    """Read 16-bit little-endian signed integer."""
    return struct.unpack_from('<h', buf, offset)[0]


def get_long(buf: bytes, offset: int = 0) -> int:
    """Read 32-bit little-endian unsigned integer."""
    return struct.unpack_from('<I', buf, offset)[0]


def get_long_signed(buf: bytes, offset: int = 0) -> int:
    """Read 32-bit little-endian signed integer."""
    return struct.unpack_from('<i', buf, offset)[0]


def get_longlong(buf: bytes, offset: int = 0) -> int:
    """Read 64-bit little-endian unsigned integer."""
    return struct.unpack_from('<Q', buf, offset)[0]


def get_longlong_signed(buf: bytes, offset: int = 0) -> int:
    """Read 64-bit little-endian signed integer."""
    return struct.unpack_from('<q', buf, offset)[0]


def is_nan(value: int, signed: bool = True, bits: int = 32) -> bool:
    """Check if value is NaN (Not a Number) marker."""
    if bits == 32:
        return value == NAN_S32 if signed else value == NAN_U32
    else:  # 64 bits
        return value == NAN_S64 if signed else value == NAN_U64


def parse_packet_header(packet: bytes) -> Tuple[int, int, int, int, int]:
    """
    Parse packet header and return key fields.
    
    Returns:
        Tuple of (susy_id, serial, error_code, fragment_id, packet_id)
    """
    # Skip L1 header (14 bytes) + L2 header start
    # Structure at offset 14+:
    # L2 signature (4) + longwords (1) + ctrl (1) = 6 bytes
    # Then: dest_susy(2) + dest_serial(4) + ctrl2(2) + 
    #       src_susy(2) + src_serial(4) + ctrl2(2) +
    #       error(2) + fragment(2) + packet_id(2)
    
    offset = 14 + 6  # After L1 and L2 header start
    
    # Skip to source endpoint (after destination)
    offset += 8  # dest_susy(2) + dest_serial(4) + ctrl2(2)
    
    src_susy_id = get_short(packet, offset)
    src_serial = get_long(packet, offset + 2)
    # ctrl2 at offset+6
    error_code = get_short(packet, offset + 8)
    fragment_id = get_short(packet, offset + 10)
    packet_id = get_short(packet, offset + 12) & 0x7FFF
    
    return src_susy_id, src_serial, error_code, fragment_id, packet_id


def version_to_string(version: int) -> str:
    """Convert version integer to string format."""
    major = (version >> 24) & 0xFF
    minor = (version >> 16) & 0xFF
    build = (version >> 8) & 0xFF
    revision = chr(version & 0xFF) if version & 0xFF else ''
    return f"{major}.{minor}.{build}.{revision}"
