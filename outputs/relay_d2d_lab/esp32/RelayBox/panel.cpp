#include "state.h"
static bool previous=true,stable=true;
static uint32_t changed=0,lastStatus=0;
void panelBegin(){if(RELAY_BUTTON_PIN>=0)pinMode(RELAY_BUTTON_PIN,INPUT_PULLUP);}
void panelTick(){
    if(RELAY_BUTTON_PIN>=0){
        bool now=digitalRead(RELAY_BUTTON_PIN);if(now!=previous){previous=now;changed=millis();}
        if(uint32_t(millis()-changed)>40&&now!=stable){stable=now;if(!now){Guard guard;lab.paused=!lab.paused;}}
    }
    if(uint32_t(millis()-lastStatus)>3000){
        lastStatus=millis();JsonDocument d;identity(d);{Guard g;d["rx"]=lab.received;d["tx"]=lab.forwarded;d["acks"]=lab.acks;d["invalid"]=lab.invalid;}
        serializeJson(d,Serial);Serial.println();
    }
    // External seven-segment displays intentionally remain electrically disabled:
    // their driver, common anode/cathode and pinout have not been identified.
}
