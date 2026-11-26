#include "state.h"
#include <Preferences.h>
#include <esp_system.h>

LabState lab;
SemaphoreHandle_t stateMutex;
QueueHandle_t eventQueue;
static uint32_t nextRetry=0;
static uint8_t disconnectReason=0;

void maintainUpstream(){
    if(lab.ssid.isEmpty())return;
    uint32_t now=millis();
    if(WiFi.status()==WL_CONNECTED){nextRetry=now+20000;return;}
    if(int32_t(now-nextRetry)<0)return;
    nextRetry=now+20000;
    WiFi.reconnect();
}

static String privateApKey(){
    Preferences store;
    store.begin("relaylab", false);
    String key = store.getString("ap_key", "");
    if (key.length() < 8) {
        Serial.println("Set a private SoftAP passphrase over USB (8-63 ASCII characters, finish with newline).");
        for (;;) {
            if (!Serial.available()) { delay(25); continue; }
            key = Serial.readStringUntil('\n');
            if (key.endsWith("\r")) key.remove(key.length()-1);
            bool valid = key.length() >= 8 && key.length() <= 63;
            for (unsigned i=0; valid && i<key.length(); ++i)
                valid = key[i] >= 32 && key[i] <= 126;
            if (valid && store.putString("ap_key", key) == key.length()) break;
            Serial.println("Invalid length/characters or NVS write failure. Enter again.");
        }
    }
    store.end();
    return key;
}

void configureWiFi(){
    stateMutex=xSemaphoreCreateMutex();eventQueue=xQueueCreate(256,sizeof(Event));
    char id[24],session[12];snprintf(id,sizeof(id),"esp32-%06lx",(unsigned long)(ESP.getEfuseMac()&0xffffff));
    snprintf(session,sizeof(session),"%08lx",(unsigned long)esp_random());lab.id=id;lab.session=session;
    lab.apName="RelayBox-"+String(id+6);
    Preferences prefs;prefs.begin("relaylab",true);lab.ssid=prefs.getString("ssid","");lab.password=prefs.getString("pass","");lab.server=prefs.getString("server","");prefs.end();
    lab.targetIP.fromString(lab.server);
    WiFi.onEvent([](WiFiEvent_t,WiFiEventInfo_t info){
        Guard guard;disconnectReason=info.wifi_sta_disconnected.reason;
    },ARDUINO_EVENT_WIFI_STA_DISCONNECTED);
    WiFi.mode(WIFI_AP_STA);WiFi.setSleep(false);
    WiFi.softAPConfig(IPAddress(192,168,50,1),IPAddress(192,168,50,1),IPAddress(255,255,255,0));
    WiFi.softAP(lab.apName.c_str(),privateApKey().c_str(),1,false,3);
    WiFi.setAutoReconnect(true);
    if(lab.ssid.length()){WiFi.begin(lab.ssid.c_str(),lab.password.c_str());nextRetry=millis()+20000;}
    // Credentials deliberately never printed; they are stored only in device NVS.
    Serial.printf("RelayBox 2.0 | %s | AP http://192.168.50.1\n",lab.id.c_str());
}
void identity(JsonDocument& d){
    Guard guard;
    d["id"]=lab.id;d["model"]="ESP32 Classic RelayBox";d["platform"]="esp32";d["role"]="relay";
    d["version"]="2.5.0";d["session"]=lab.session;d["running"]=true;d["local_ip"]=WiFi.localIP().toString();
    d["listen_port"]=39010;d["ap_ip"]="192.168.50.1";d["ssid"]=lab.apName;
    d["rssi_dbm"]=WiFi.status()==WL_CONNECTED?WiFi.RSSI():0;
    d["pending_events"]=uxQueueMessagesWaiting(eventQueue)+lab.retryBatch;d["queue_lost"]=lab.queueLost;
    d["control_version"]=lab.controlVersion;d["paused"]=lab.paused;
    d["wifi_connected"]=WiFi.status()==WL_CONNECTED;d["uptime_ms"]=millis();
    d["flash_bytes"]=ESP.getFlashChipSize();d["psram_bytes"]=ESP.getPsramSize();
    d["reset_reason"]=int(esp_reset_reason());
    d["last_disconnect_reason"]=disconnectReason;d["channel"]=WiFi.channel();
    d["ap_clients"]=WiFi.softAPgetStationNum();d["forwarded"]=lab.forwarded;
    d["received"]=lab.received;d["acks"]=lab.acks;d["invalid"]=lab.invalid;
}
void queueEvent(const char* type,const rly::Packet& p,float processing){
    Event e{type,p.run,p.seq,p.stamp,p.size,p.hops,processing};
    if(xQueueSend(eventQueue,&e,0)!=pdTRUE){Guard guard;lab.queueLost++;}
}
