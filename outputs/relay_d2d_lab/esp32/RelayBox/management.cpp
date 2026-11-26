#include "state.h"
#include <HTTPClient.h>

String postPC(const String& path,const String& body,int& code){
    String server;{Guard guard;server=lab.server;}
    if(!server.length()||WiFi.status()!=WL_CONNECTED){code=503;return "{\"error\":\"Upstream Wi-Fi not connected\"}";}
    // HTTPClient retains this transport until its destructor runs.
    WiFiClient client;
    HTTPClient http;
    http.setReuse(false);
    http.setConnectTimeout(1200);http.setTimeout(2000);
    http.begin(client,"http://"+server+":8765"+path);http.addHeader("Content-Type","application/json");
    code=http.POST(body);String response=http.getString();http.end();
    if(code<0){code=502;return "{\"error\":\"PC unreachable; check IP and firewall\"}";}
    return response;
}
static void updateControl(const String& response){
    JsonDocument c;if(deserializeJson(c,response))return;
    int v=c["version"]|-1;Guard guard;if(v<0||v==lab.controlVersion)return;
    IPAddress target;if(c["target_ip"].is<const char*>()&&target.fromString(c["target_ip"].as<String>()))lab.targetIP=target;
    lab.targetPort=c["target_port"]|lab.targetPort;lab.paused=c["paused"]|false;lab.dropEvery=c["drop_every"]|0;
    lab.controlVersion=v;
}
void managementTask(void*){
    portalBegin();String pending;uint32_t heartbeat=0,flush=0;uint64_t eventNo=0;
    for(;;){
        portalTick();
        if(WiFi.status()==WL_CONNECTED && lab.server.length()){
            int code;
            if(uint32_t(millis()-heartbeat)>700){
                heartbeat=millis();JsonDocument d;identity(d);String body;serializeJson(d,body);
                String response=postPC("/api/device",body,code);if(code==200)updateControl(response);
            }
            if(uint32_t(millis()-flush)>200){
                flush=millis();
                if(pending.isEmpty()){
                    JsonDocument doc;JsonArray batch=doc["events"].to<JsonArray>();Event e;
                    while(batch.size()<40&&xQueueReceive(eventQueue,&e,0)==pdTRUE){
                        JsonObject o=batch.add<JsonObject>();
                        o["event_id"]=lab.id+":"+lab.session+":"+String((unsigned long)(eventNo++));
                        o["device_id"]=lab.id;o["type"]=e.type;o["node"]="R";o["run"]=e.run;o["seq"]=e.seq;
                        o["bytes"]=e.bytes;o["hops"]=e.hops;o["sent_ns"]=e.stamp;o["processing_ms"]=e.processing;
                    }
                    {Guard guard;lab.retryBatch=batch.size();}
                    if(batch.size())serializeJson(doc,pending);
                }
                if(pending.length()){
                    postPC("/api/events",pending,code);
                    if(code==200){pending="";Guard guard;lab.retryBatch=0;}
                }
            }
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
}
