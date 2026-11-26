"""Execute identical wire vectors through Python, Java and ESP32's portable C++ code."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab.packet import Packet,DATA,ACK,HELLO,payload_for

BUILD=ROOT/'.build/native_tests'
JAVA=Path(os.environ.get('JAVA_HOME',r'C:\Program Files\Java\jdk-21'))/'bin'
BUILD.mkdir(parents=True,exist_ok=True)
subprocess.run([str(JAVA/'javac.exe'),'-encoding','UTF-8','-d',str(BUILD),str(ROOT/'android/src/vn/relaylab/Packet.java'),str(ROOT/'tests/PacketProbe.java')],check=True)
subprocess.run([str(BUILD/'native_protocol.exe')],check=True)
vectors=[]
for size in (0,16,128,512,1024):
    p=Packet(DATA,123456,700,9876543210123456,payload_for(123456,700,size))
    vectors.append(('data_'+str(size),p.encode()))
vectors += [('ack',Packet(ACK,7,8,1234,hops=1).encode()),('hello',Packet(HELLO,0,0,0,b'{"id":"test"}').encode())]
base=bytearray(vectors[2][1])
for offset in (0,4,5,6,7,24,26,28,33):
    b=base.copy();b[offset]=255;vectors.append(('bad_byte_'+str(offset),bytes(b)))
for length in (0,1,31,32,50): vectors.append(('truncated_'+str(length),bytes(base[:length])))
vectors.append(('extra',bytes(base)+b'x'))
results=[]
for name,raw in vectors:
    try: expected=Packet.decode(raw).encode().hex()
    except ValueError: expected='INVALID'
    cpp=subprocess.check_output([str(BUILD/'native_protocol.exe'),raw.hex()],text=True).strip()
    java=subprocess.check_output([str(JAVA/'java.exe'),'-cp',str(BUILD),'vn.relaylab.PacketProbe',raw.hex()],text=True).strip()
    assert cpp==java==expected,(name,expected,cpp,java)
    results.append({'case':name,'accepted':expected!='INVALID','all_three_agree':True})
out=ROOT/'results/validation_v2';out.mkdir(parents=True,exist_ok=True)
(out/'protocol_interop.json').write_text(json.dumps({'cases':results,'scope':'Host execution of the same ESP32 headers; not a radio/board test.'},indent=2),encoding='utf-8')
print(f'{len(results)} wire vectors matched across Python, Java and C++')
