#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>

namespace rly {
constexpr size_t HEADER=32, MAX_PAYLOAD=1024, MAX_PACKET=HEADER+MAX_PAYLOAD;
constexpr uint8_t DATA=1, ACK=2, HELLO=3;
inline uint16_t u16(const uint8_t* p){return uint16_t(p[0])<<8|p[1];}
inline uint32_t u32(const uint8_t* p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
inline uint64_t u64(const uint8_t* p){return uint64_t(u32(p))<<32|u32(p+4);}
inline void put16(uint8_t* p,uint16_t n){p[0]=uint8_t(n>>8);p[1]=uint8_t(n);}
inline void put32(uint8_t* p,uint32_t n){for(int i=3;i>=0;i--){p[i]=uint8_t(n);n>>=8;}}
inline void put64(uint8_t* p,uint64_t n){put32(p,uint32_t(n>>32));put32(p+4,uint32_t(n));}
inline uint32_t crc32(const uint8_t* p,size_t n){
    uint32_t crc=0xffffffffU;
    for(size_t i=0;i<n;i++){crc^=p[i];for(int j=0;j<8;j++)crc=(crc>>1)^((crc&1)?0xedb88320U:0U);}
    return crc^0xffffffffU;
}
struct Packet {uint8_t kind=0,hops=0;uint32_t run=0,seq=0;uint64_t stamp=0;uint16_t size=0;const uint8_t* payload=nullptr;};
inline bool decode(const uint8_t* raw,size_t n,Packet& p){
    if(n<HEADER||memcmp(raw,"RLY1",4)||raw[4]!=1||raw[5]<1||raw[5]>3||raw[6]>2||raw[7]||u16(raw+26))return false;
    p.kind=raw[5];p.hops=raw[6];p.run=u32(raw+8);p.seq=u32(raw+12);p.stamp=u64(raw+16);p.size=u16(raw+24);p.payload=raw+HEADER;
    return p.size<=MAX_PAYLOAD&&n==HEADER+p.size&&!(p.kind==ACK&&p.size)&&crc32(p.payload,p.size)==u32(raw+28);
}
inline bool expected(const Packet& p){for(uint16_t i=0;i<p.size;i++)if(p.payload[i]!=uint8_t(p.run+p.seq*31U+i*17U))return false;return true;}
inline size_t encode(const Packet& p,uint8_t* raw){
    if(p.size>MAX_PAYLOAD||p.hops>2||p.kind<1||p.kind>3||(p.kind==ACK&&p.size))return 0;
    memcpy(raw,"RLY1",4);raw[4]=1;raw[5]=p.kind;raw[6]=p.hops;raw[7]=0;
    put32(raw+8,p.run);put32(raw+12,p.seq);put64(raw+16,p.stamp);put16(raw+24,p.size);put16(raw+26,0);
    put32(raw+28,crc32(p.payload,p.size));if(p.size)memcpy(raw+HEADER,p.payload,p.size);return HEADER+p.size;
}
}
