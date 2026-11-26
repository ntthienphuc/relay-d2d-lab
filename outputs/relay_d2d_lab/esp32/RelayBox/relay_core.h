#pragma once
#include "protocol.h"

namespace rly {
struct Address {uint32_t ip=0;uint16_t port=0;bool operator==(const Address& b)const{return ip==b.ip&&port==b.port;}};
enum class Outcome {INVALID, FORWARD, ACK_FORWARD, DROP_PAUSED, DROP_INJECTED, DROP_CAPACITY, IGNORE};
struct Decision {Outcome outcome=Outcome::IGNORE;Packet packet;Address destination;};
/** Fixed-size cache: no heap allocation in the packet path. */
class RelayCore {
    struct Origin {bool used=false;uint32_t run=0,seq=0,created=0;uint64_t stamp=0;Address address;};
    Origin origins[512];
public:
    static constexpr uint32_t TTL_MS=5000;
    Decision handle(uint8_t* raw,size_t n,Address from,Address target,uint32_t now,bool paused,unsigned dropEvery){
        Decision d;if(!decode(raw,n,d.packet)){d.outcome=Outcome::INVALID;return d;}
        const Packet& p=d.packet;
        if(p.kind==DATA){
            if(p.hops>=1||!expected(p)){d.outcome=Outcome::INVALID;return d;}
            if(paused){d.outcome=Outcome::DROP_PAUSED;return d;}
            if(dropEvery&&(p.seq+1)%dropEvery==0){d.outcome=Outcome::DROP_INJECTED;return d;}
            Origin* freeSlot=nullptr;
            for(auto& o:origins){
                if(o.used&&uint32_t(now-o.created)>TTL_MS)o.used=false;
                if(o.used&&o.run==p.run&&o.seq==p.seq&&o.stamp==p.stamp){freeSlot=&o;break;}
                if(!o.used&&!freeSlot)freeSlot=&o;
            }
            if(!freeSlot){d.outcome=Outcome::DROP_CAPACITY;return d;}
            *freeSlot={true,p.run,p.seq,now,p.stamp,from};raw[6]++;
            d.outcome=Outcome::FORWARD;d.destination=target;
        }else if(p.kind==ACK&&from==target){
            for(auto& o:origins)if(o.used&&o.run==p.run&&o.seq==p.seq&&o.stamp==p.stamp){
                if(uint32_t(now-o.created)<=TTL_MS){d.outcome=Outcome::ACK_FORWARD;d.destination=o.address;}
                o.used=false;break;
            }
        }
        return d;
    }
};
}
