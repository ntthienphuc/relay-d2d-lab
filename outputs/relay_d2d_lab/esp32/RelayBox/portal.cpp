#include "state.h"
#include "compare.h"
#include <WebServer.h>
#include <Preferences.h>

static WebServer portal(80),proxy(8765);
static uint32_t rebootAt=0;
static bool apClient(IPAddress ip){return ip[0]==192&&ip[1]==168&&ip[2]==50&&ip[3]>1;}
#include "portal_page.h"

void portalBegin(){
    portal.on("/",HTTP_GET,[]{portal.send_P(200,"text/html; charset=utf-8",PAGE);});
    portal.on("/status",HTTP_GET,[]{JsonDocument d;identity(d);{Guard g;d["received"]=lab.received;d["forwarded"]=lab.forwarded;d["acks"]=lab.acks;d["invalid"]=lab.invalid;d["send_errors"]=lab.sendErrors;}d["heap_free"]=ESP.getFreeHeap();String s;serializeJson(d,s);portal.send(200,"application/json",s);});
    portal.on("/compare",HTTP_GET,[]{
        JsonDocument result; comparisonStatus(result); String body; serializeJson(result,body);
        portal.sendHeader("Cache-Control","no-store"); portal.send(200,"application/json",body);
    });
    portal.on("/save",HTTP_POST,[]{
        if(!apClient(portal.client().remoteIP())){portal.send(403,"text/plain","Connect to RelayBox Wi-Fi to configure");return;}
        String ssid=portal.arg("ssid"),pass=portal.arg("password"),server=portal.arg("server");IPAddress ip;
        if(ssid.isEmpty()||ssid.length()>32||pass.length()>64||(server.length()&&(!ip.fromString(server)||ip==IPAddress(0,0,0,0)||ip==IPAddress(192,168,50,1)))){
            portal.send(400,"text/plain","Invalid SSID or laptop IPv4");return;
        }
        Preferences p;p.begin("relaylab",false);p.putString("ssid",ssid);p.putString("pass",pass);p.putString("server",server);p.end();
        portal.send(200,"text/html; charset=utf-8","Đã lưu. ESP32 sẽ khởi động lại; chờ khoảng 15 giây rồi mở lại trang.");rebootAt=millis()+2000;
    });
    portal.begin();
    // This is an allowlisted management proxy, not general Internet routing/NAT.
    for(const char* path:{"/api/device","/api/events"})proxy.on(path,HTTP_POST,[]{
        if(!apClient(proxy.client().remoteIP())){proxy.send(403,"application/json","{}");return;}
        String body=proxy.arg("plain");if(body.length()>48000){proxy.send(413,"application/json","{}");return;}
        if(proxy.uri()=="/api/device"){
            JsonDocument d;if(deserializeJson(d,body)){proxy.send(400,"application/json","{}");return;}
            d["bridge_id"]=lab.id;d["local_ip"]=proxy.client().remoteIP().toString();body="";serializeJson(d,body);
        }
        int code;String response=postPC(proxy.uri(),body,code);proxy.send(code,"application/json",response);
    });
    proxy.onNotFound([]{proxy.send(404,"application/json","{\"error\":\"RelayBox management gateway only\"}");});proxy.begin();
}
void portalTick(){comparisonTick();portal.handleClient();proxy.handleClient();if(rebootAt&&int32_t(millis()-rebootAt)>=0)ESP.restart();}
