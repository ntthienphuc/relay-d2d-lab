#include "state.h"
#include "relay_core.h"
#include <WiFiUdp.h>

static WiFiUDP dataUDP,discoveryUDP;
static rly::RelayCore core;
static uint8_t buffer[rly::MAX_PACKET],encoded[rly::MAX_PACKET];
static uint32_t lastHello=0;

static bool sendTo(const uint8_t* raw,size_t n,IPAddress ip,uint16_t port){
    bool ok=dataUDP.beginPacket(ip,port)&&dataUDP.write(raw,n)==n&&dataUDP.endPacket();
    if(!ok){Guard guard;lab.sendErrors++;}return ok;
}
void relayBegin(){dataUDP.begin(39010);discoveryUDP.begin(39001);}
void relayTick(){
    String server;IPAddress target;unsigned drop;bool paused;uint16_t port;
    {Guard guard;server=lab.server;target=lab.targetIP;port=lab.targetPort;drop=lab.dropEvery;paused=lab.paused;}
    if(WiFi.status()==WL_CONNECTED&&server.length()&&uint32_t(millis()-lastHello)>1000){
        lastHello=millis();JsonDocument doc;identity(doc);String body;serializeJson(doc,body);
        rly::Packet hello;hello.kind=rly::HELLO;hello.size=body.length();hello.payload=(const uint8_t*)body.c_str();
        size_t n=rly::encode(hello,encoded);IPAddress pc;if(n&&pc.fromString(server))sendTo(encoded,n,pc,39001);
    }
    // Forward only discovery from clients of this SoftAP. Their local IP stays visible to the PC.
    int n=discoveryUDP.parsePacket();
    if(n>0){
        IPAddress peer=discoveryUDP.remoteIP();uint16_t peerPort=discoveryUDP.remotePort();
        if(n>(int)sizeof(buffer)){discoveryUDP.clear();return;}
        int got=discoveryUDP.read(buffer,sizeof(buffer));rly::Packet p;
        if(peer[0]==192&&peer[1]==168&&peer[2]==50&&rly::decode(buffer,got,p)&&p.kind==rly::HELLO){
            JsonDocument d;if(!deserializeJson(d,p.payload,p.size)){
                d["bridge_id"]=lab.id;d["local_ip"]=peer.toString();d["listen_port"]=peerPort;
                String body;serializeJson(d,body);p.payload=(const uint8_t*)body.c_str();p.size=body.length();
                size_t size=rly::encode(p,encoded);IPAddress pc;if(size&&pc.fromString(server))sendTo(encoded,size,pc,39001);
            }
        }
    }
    for(int budget=0;budget<8;budget++){
        n=dataUDP.parsePacket();if(n<=0)break;
        rly::Address from{uint32_t(dataUDP.remoteIP()),dataUDP.remotePort()},to{uint32_t(target),port};
        if(n>(int)sizeof(buffer)){dataUDP.clear();Guard guard;lab.invalid++;continue;}
        int got=dataUDP.read(buffer,sizeof(buffer));uint32_t begin=micros();
        auto d=core.handle(buffer,got,from,to,millis(),paused,drop);
        if(d.packet.kind==rly::DATA&&d.outcome!=rly::Outcome::INVALID){
            {Guard guard;lab.received++;}queueEvent("relay_receive",d.packet);
        }
        switch(d.outcome){
            case rly::Outcome::FORWARD:
                if(sendTo(buffer,got,IPAddress(d.destination.ip),d.destination.port)){
                    {Guard guard;lab.forwarded++;}d.packet.hops++;queueEvent("forward",d.packet,uint32_t(micros()-begin)/1000.f);
                }else queueEvent("drop_capacity",d.packet);
                break;
            case rly::Outcome::ACK_FORWARD:
                if(sendTo(buffer,got,IPAddress(d.destination.ip),d.destination.port)){{Guard guard;lab.acks++;}queueEvent("ack_forward",d.packet);}
                break;
            case rly::Outcome::DROP_PAUSED:queueEvent("drop_paused",d.packet);break;
            case rly::Outcome::DROP_INJECTED:queueEvent("drop_injected",d.packet);break;
            case rly::Outcome::DROP_CAPACITY:queueEvent("drop_capacity",d.packet);break;
            case rly::Outcome::INVALID:
                {Guard guard;lab.invalid++;}
                if(got>=32&&!memcmp(buffer,"RLY1",4)){
                    rly::Packet p;p.run=rly::u32(buffer+8);p.seq=rly::u32(buffer+12);queueEvent("invalid",p);
                }break;
            default:break;
        }
    }
}
