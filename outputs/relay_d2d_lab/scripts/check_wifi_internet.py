"""Verify Windows client C using its Wi-Fi adapter for DNS and HTTPS (no proxy)."""
import argparse
import http.client
import ipaddress
import json
import os
import secrets
import socket
import ssl
import struct
import subprocess
from datetime import datetime, timezone

HOST = "www.google.com"

def interface(alias):
    query = """
    $ErrorActionPreference='Stop'
    $n=Get-NetIPConfiguration -InterfaceAlias $env:RELAY_TEST_INTERFACE
    [pscustomobject]@{ip=($n.IPv4Address|Select-Object -First 1).IPAddress;
    index=$n.InterfaceIndex;gateway=($n.IPv4DefaultGateway|Select-Object -First 1).NextHop;
    dns=@((Get-DnsClientServerAddress -InterfaceIndex $n.InterfaceIndex -AddressFamily IPv4).ServerAddresses)}|ConvertTo-Json -Compress
    """
    result=subprocess.check_output(["powershell.exe","-NoProfile","-Command",query],
                                   env={**os.environ,"RELAY_TEST_INTERFACE":alias})
    return json.loads(result)

def bound(kind, net):
    sock=socket.socket(socket.AF_INET,kind)
    try:
        sock.settimeout(8)
        # Windows expects the interface index in network byte order.
        sock.setsockopt(socket.IPPROTO_IP,31,struct.pack("!I",net["index"]))
        sock.bind((net["ip"],0))
        return sock
    except Exception:
        sock.close()
        raise

def after_name(packet,offset):
    while offset<len(packet):
        size=packet[offset];offset+=1
        if size==0:return offset
        if size&0xc0==0xc0 and offset<len(packet):return offset+1
        if size>63 or offset+size>len(packet):break
        offset+=size
    raise ValueError("Incomplete DNS name")

def resolve(net):
    key=secrets.randbits(16)
    qname=b"".join(bytes([len(s)])+s.encode("ascii") for s in HOST.split("."))+b"\0"
    request=struct.pack("!6H",key,0x0100,1,0,0,0)+qname+struct.pack("!2H",1,1)
    with bound(socket.SOCK_DGRAM,net) as udp:
        udp.connect((net["dns"][0],53));udp.send(request);packet=udp.recv(4096)
    ident,flags,questions,answers,_,_=struct.unpack_from("!6H",packet)
    if ident!=key or questions!=1 or not flags&0x8000 or flags&0x020f:
        raise ValueError("DNS answer missing, truncated or invalid")
    offset=after_name(packet,12)+4
    for _ in range(answers):
        offset=after_name(packet,offset)
        kind,cls,_,size=struct.unpack_from("!HHIH",packet,offset);offset+=10
        if kind==1 and cls==1 and size==4:return str(ipaddress.IPv4Address(packet[offset:offset+size]))
        offset+=size
    raise ValueError("DNS returned no IPv4 address")

def verify(alias,gateway):
    net=interface(alias)
    if not net["gateway"] or not net["dns"]:raise ValueError("Wi-Fi needs an IPv4 gateway and DNS")
    if gateway and net["gateway"]!=gateway:raise ValueError("C is connected to another gateway")
    address=resolve(net)
    with bound(socket.SOCK_STREAM,net) as raw:
        raw.connect((address,443))
        with ssl.create_default_context().wrap_socket(raw,server_hostname=HOST) as tls:
            tls.sendall((f"GET /generate_204?relaylab={secrets.token_hex(5)} HTTP/1.1\r\nHost: {HOST}\r\nConnection: close\r\n\r\n").encode("ascii"))
            response=http.client.HTTPResponse(tls);response.begin()
            if response.status!=204:raise RuntimeError(f"Expected 204, received {response.status}")
            return dict(time=datetime.now(timezone.utc).isoformat(),interface=alias,client=net["ip"],
                        gateway=net["gateway"],dns=net["dns"][0],host=HOST,http=response.status,tls=tls.version())

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface",default="Wi-Fi")
    parser.add_argument("--gateway",help="Require C's DHCP gateway to match this address")
    args=parser.parse_args();print(json.dumps(verify(args.interface,args.gateway)))

