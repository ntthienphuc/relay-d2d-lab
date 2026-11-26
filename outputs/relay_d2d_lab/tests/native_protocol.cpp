#include "../esp32/RelayBox/relay_core.h"
#include <assert.h>
#include <iostream>
#include <string>
#include <vector>
#include <iomanip>

using namespace rly;
int main(int argc,char** argv){
    if(argc==2){
        std::string h=argv[1];std::vector<uint8_t> raw;
        for(size_t i=0;i<h.size();i+=2)raw.push_back(uint8_t(std::stoul(h.substr(i,2),nullptr,16)));
        Packet p;if(!decode(raw.data(),raw.size(),p)){std::cout<<"INVALID";return 0;}
        uint8_t out[MAX_PACKET];size_t n=encode(p,out);
        for(size_t i=0;i<n;i++)std::cout<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(out[i]);
        return 0;
    }
    uint8_t payload[128],raw[MAX_PACKET],ack[HEADER];
    for(size_t i=0;i<sizeof(payload);i++)payload[i]=uint8_t(9+7*31+i*17);
    Packet p;p.kind=DATA;p.run=9;p.seq=7;p.stamp=1234567890123456ULL;p.size=128;p.payload=payload;
    size_t n=encode(p,raw);Packet parsed;assert(decode(raw,n,parsed)&&expected(parsed));
    assert(crc32((const uint8_t*)"123456789",9)==0xcbf43926U);
    Address source{1,39012},sink{2,39011};RelayCore core;
    auto d=core.handle(raw,n,source,sink,100,false,0);assert(d.outcome==Outcome::FORWARD&&raw[6]==1);
    Packet a;a.kind=ACK;a.run=p.run;a.seq=p.seq;a.stamp=p.stamp;a.hops=1;encode(a,ack);
    assert(core.handle(ack,HEADER,source,sink,101,false,0).outcome==Outcome::IGNORE); // wrong peer
    a.stamp++;encode(a,ack);assert(core.handle(ack,HEADER,sink,sink,102,false,0).outcome==Outcome::IGNORE);
    a.stamp--;encode(a,ack);assert(core.handle(ack,HEADER,sink,sink,103,false,0).outcome==Outcome::ACK_FORWARD);
    assert(core.handle(ack,HEADER,sink,sink,104,false,0).outcome==Outcome::IGNORE); // duplicate ACK
    encode(p,raw);assert(core.handle(raw,n,source,sink,200,true,0).outcome==Outcome::DROP_PAUSED);
    assert(core.handle(raw,n,source,sink,201,false,8).outcome==Outcome::DROP_INJECTED);
    raw[n-1]^=1;assert(core.handle(raw,n,source,sink,202,false,0).outcome==Outcome::INVALID);raw[n-1]^=1;
    raw[6]=1;assert(core.handle(raw,n,source,sink,203,false,0).outcome==Outcome::INVALID);
    encode(p,raw);assert(core.handle(raw,n,source,sink,300,false,0).outcome==Outcome::FORWARD);
    assert(core.handle(ack,HEADER,sink,sink,5301,false,0).outcome==Outcome::IGNORE); // TTL
    RelayCore full;
    for(unsigned i=0;i<512;i++){
        p.seq=i;for(unsigned j=0;j<p.size;j++)payload[j]=uint8_t(p.run+i*31+j*17);
        encode(p,raw);assert(full.handle(raw,n,source,sink,1000,false,0).outcome==Outcome::FORWARD);
    }
    p.seq=900;for(unsigned j=0;j<p.size;j++)payload[j]=uint8_t(p.run+p.seq*31+j*17);encode(p,raw);
    assert(full.handle(raw,n,source,sink,1001,false,0).outcome==Outcome::DROP_CAPACITY);
    assert(full.handle(raw,n,source,sink,6002,false,0).outcome==Outcome::FORWARD);
    std::cout<<"CRC, byte order, ACK peer/timestamp, duplicate ACK, pause, injection, hops, expiry and capacity PASS\n";
}
