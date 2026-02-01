"""
Ethernet communication layer for SBFspot Python port.
Handles UDP socket operations for Speedwire protocol.
"""

import socket
import struct
from typing import List, Optional, Tuple

from .constants import DEFAULT_PORT, MULTICAST_ADDRESS, SOCKET_TIMEOUT, COMMBUFSIZE


class EthernetConnection:
    """
    UDP socket communication for SMA Speedwire protocol.
    
    The Speedwire protocol uses UDP on port 9522.
    Inverter discovery uses multicast address 239.12.255.254.
    """
    
    def __init__(self, port: int = DEFAULT_PORT, timeout: float = SOCKET_TIMEOUT):
        """
        Initialize UDP socket.
        
        Args:
            port: UDP port number (default 9522)
            timeout: Socket timeout in seconds
        """
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self.local_ip: Optional[str] = None
        
    def connect(self) -> bool:
        """
        Create and configure UDP socket.
        
        Returns:
            True if socket created successfully
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            
            # Allow address reuse
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to any address on the specified port
            self.sock.bind(('', self.port))
            
            # Set timeout
            self.sock.settimeout(self.timeout)
            
            # Enable multicast
            mreq = struct.pack('4sL', 
                              socket.inet_aton(MULTICAST_ADDRESS),
                              socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            # Disable multicast loopback
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
            
            # Get local IP
            self.local_ip = self._get_local_ip()
            
            return True
            
        except socket.error as e:
            print(f"Socket error: {e}")
            return False
    
    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def send(self, packet: bytes, ip_address: str) -> int:
        """
        Send packet to specified IP address.
        
        Args:
            packet: Packet data to send
            ip_address: Destination IP address
            
        Returns:
            Number of bytes sent
        """
        if not self.sock:
            raise RuntimeError("Socket not connected")
        
        return self.sock.sendto(packet, (ip_address, self.port))
    
    def send_multicast(self, packet: bytes) -> int:
        """
        Send packet to multicast address.
        
        Args:
            packet: Packet data to send
            
        Returns:
            Number of bytes sent
        """
        return self.send(packet, MULTICAST_ADDRESS)
    
    def receive(self, timeout: Optional[float] = None) -> Tuple[bytes, str]:
        """
        Receive packet from socket.
        
        Args:
            timeout: Optional override for socket timeout
            
        Returns:
            Tuple of (packet_data, sender_ip)
            
        Raises:
            socket.timeout: If no data received within timeout
        """
        if not self.sock:
            raise RuntimeError("Socket not connected")
        
        if timeout is not None:
            self.sock.settimeout(timeout)
        
        try:
            data, addr = self.sock.recvfrom(COMMBUFSIZE)
            return data, addr[0]
        finally:
            if timeout is not None:
                self.sock.settimeout(self.timeout)
    
    def receive_with_filter(self, 
                           expected_ip: Optional[str] = None,
                           max_attempts: int = 10,
                           ignore_sizes: List[int] = None) -> Tuple[Optional[bytes], str]:
        """
        Receive packet with optional filtering.
        
        Args:
            expected_ip: Only accept packets from this IP
            max_attempts: Maximum receive attempts
            ignore_sizes: List of packet sizes to ignore (e.g., energy meter packets)
            
        Returns:
            Tuple of (packet_data, sender_ip) or (None, '') on timeout
        """
        if ignore_sizes is None:
            ignore_sizes = [600, 608]  # Energy meter and Sunny Home Manager
        
        for _ in range(max_attempts):
            try:
                data, sender_ip = self.receive()
                
                # Skip ignored packet sizes  
                if len(data) in ignore_sizes:
                    continue
                
                # Check sender if filtering
                if expected_ip and sender_ip != expected_ip:
                    continue
                
                return data, sender_ip
                
            except socket.timeout:
                return None, ''
        
        return None, ''
    
    def discover_inverters(self, discovery_packet: bytes, 
                          timeout: float = 3.0) -> List[str]:
        """
        Discover SMA inverters on the network.
        
        Args:
            discovery_packet: Discovery packet to send
            timeout: Time to wait for responses
            
        Returns:
            List of discovered inverter IP addresses
        """
        if not self.sock:
            raise RuntimeError("Socket not connected")
        
        # Send discovery packet to multicast
        self.send_multicast(discovery_packet)
        
        inverters = []
        original_timeout = self.timeout
        self.sock.settimeout(timeout)
        
        try:
            while True:
                try:
                    data, sender_ip = self.sock.recvfrom(COMMBUFSIZE)
                    
                    # Check for SMA signature
                    if data[:3] == b'SMA':
                        # IP address is at offset 38-41 in discovery response
                        if len(data) >= 42:
                            ip = f"{data[38]}.{data[39]}.{data[40]}.{data[41]}"
                            if ip not in inverters:
                                inverters.append(ip)
                        else:
                            # Use sender IP if packet format is different
                            if sender_ip not in inverters and sender_ip != self.local_ip:
                                inverters.append(sender_ip)
                                
                except socket.timeout:
                    break
                    
        finally:
            self.sock.settimeout(original_timeout)
        
        return inverters
    
    def close(self):
        """Close socket connection."""
        if self.sock:
            try:
                # Leave multicast group
                mreq = struct.pack('4sL',
                                  socket.inet_aton(MULTICAST_ADDRESS),
                                  socket.INADDR_ANY)
                self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
            except:
                pass
            
            self.sock.close()
            self.sock = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
