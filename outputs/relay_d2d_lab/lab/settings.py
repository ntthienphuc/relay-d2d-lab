"""Explicit local control address, independent of VPN/default Internet routing."""
import ipaddress
import json
import os
import socket
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / '.runtime/network.json'

def addresses():
    values = {'127.0.0.1'}
    try:
        values.update(row[4][0] for row in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    except OSError:
        pass
    return sorted(ip for ip in values if not ip.startswith('169.254.'))

def validate_address(value):
    ip = ipaddress.IPv4Address(value)
    if ip.is_unspecified or ip.is_multicast or ip.is_link_local:
        raise ValueError('Chọn IPv4 của laptop trên mạng lab')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try: probe.bind((str(ip), 0))
        except OSError: raise ValueError('Địa chỉ này không thuộc interface đang hoạt động trên laptop')
    return str(ip)

def select_address(value):
    value = validate_address(value)
    PATH.parent.mkdir(exist_ok=True)
    PATH.write_text(json.dumps({'server_ip': value}), encoding='utf-8')
    return value

def selected_address(peer_ip=None):
    configured = os.environ.get('RELAY_LAB_IP', '')
    if not configured and PATH.exists():
        try: configured = json.loads(PATH.read_text(encoding='utf-8')).get('server_ip', '')
        except (OSError, ValueError): pass
    if configured:
        try: return validate_address(configured), 'selected'
        except (ValueError, OSError): return '127.0.0.1', 'selected_unavailable'
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect((peer_ip or '192.0.2.1', 80))
            return probe.getsockname()[0], 'relay' if peer_ip else 'automatic'
        except OSError: return '127.0.0.1', 'unavailable'

def snapshot(peer_ip=None):
    ip, origin = selected_address(peer_ip)
    return {'server_ip': ip, 'origin': origin, 'addresses': addresses(),
            'hint': 'Chọn IP cùng mạng với nguồn và ESP. Không chọn VPN/WSL hoặc IP Ethernet khác subnet.'}
