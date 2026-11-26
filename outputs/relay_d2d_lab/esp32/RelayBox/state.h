#pragma once
#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include "protocol.h"

// Leave disabled until the physical button wiring is confirmed. Active-low to GND.
#ifndef RELAY_BUTTON_PIN
#define RELAY_BUTTON_PIN -1
#endif

struct Event {
    const char* type;
    uint32_t run,seq;
    uint64_t stamp;
    uint16_t bytes;
    uint8_t hops;
    float processing;
};
struct LabState {
    String id,session,ssid,password,server,apName;
    IPAddress targetIP;
    uint16_t targetPort=39002;
    int controlVersion=-1;
    unsigned dropEvery=0;
    bool paused=false;
    uint32_t received=0,forwarded=0,acks=0,invalid=0,queueLost=0,sendErrors=0;
    unsigned retryBatch=0;
};
extern LabState lab;
extern SemaphoreHandle_t stateMutex;
extern QueueHandle_t eventQueue;
struct Guard {Guard(){xSemaphoreTake(stateMutex,portMAX_DELAY);}~Guard(){xSemaphoreGive(stateMutex);}};
void configureWiFi();
void maintainUpstream();
void identity(JsonDocument& doc);
void queueEvent(const char* type,const rly::Packet& p,float processing=0);
void relayBegin();
void relayTick();
void managementTask(void*);
void portalBegin();
void portalTick();
void panelBegin();
void panelTick();
String postPC(const String& path,const String& body,int& code);
