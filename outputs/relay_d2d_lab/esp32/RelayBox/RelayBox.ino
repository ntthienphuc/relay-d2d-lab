#include "state.h"
#include "internet.h"

void setup(){
    Serial.begin(115200);configureWiFi();relayBegin();panelBegin();
    xTaskCreatePinnedToCore(managementTask,"lab-management",12288,nullptr,1,nullptr,0);
}
void loop(){maintainUpstream();internetTick();relayTick();panelTick();delay(1);}
