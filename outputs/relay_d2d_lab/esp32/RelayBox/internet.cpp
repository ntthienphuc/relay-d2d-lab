#include "internet.h"
#include "state.h"
#include <esp_netif.h>

// IPv4 traffic goes through lwIP; the RLY1 experiment keeps its own UDP port.
static bool forwarding = false;
static const char* state = "waiting_upstream";
static IPAddress offeredDns(1, 1, 1, 1);

void internetTick() {
    static uint32_t lastPoll = 0;
    static IPAddress upstream;
    if (millis() - lastPoll < 500) return;
    lastPoll = millis();
    const IPAddress ip = WiFi.localIP();
    const uint32_t mask = uint32_t(WiFi.subnetMask());
    const uint32_t ap = uint32_t(WiFi.softAPIP());
    const bool connected = WiFi.status() == WL_CONNECTED && uint32_t(ip) && mask;
    const bool overlap = connected && ((uint32_t(ip) & mask) == (ap & mask) ||
        (ip[0] == 192 && ip[1] == 168 && ip[2] == 50));
    const bool usable = connected && !overlap;
    bool enabled = forwarding;
    if (enabled && (!usable || upstream != ip)) {
        WiFi.AP.enableNAPT(false);
        enabled = false;
    }
    if (usable && !enabled) enabled = WiFi.AP.enableNAPT(true);
    upstream = ip;
    IPAddress dns = offeredDns;
    if (usable) {
        esp_netif_dns_info_t info{};
        auto sta = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
        auto softap = esp_netif_get_handle_from_ifkey("WIFI_AP_DEF");
        if (sta && softap && esp_netif_get_dns_info(sta, ESP_NETIF_DNS_MAIN, &info) == ESP_OK &&
            info.ip.type == ESP_IPADDR_TYPE_V4 && info.ip.u_addr.ip4.addr &&
            IPAddress(info.ip.u_addr.ip4.addr) != dns &&
            esp_netif_set_dns_info(softap, ESP_NETIF_DNS_MAIN, &info) == ESP_OK)
            dns = IPAddress(info.ip.u_addr.ip4.addr);
    }
    Guard guard;
    forwarding = enabled;
    offeredDns = dns;
    state = overlap ? "subnet_overlap" : !connected ? "waiting_upstream" :
            enabled ? "routing_ipv4" : "napt_failed";
}

// Caller holds the lab status mutex. A client HTTPS test proves actual reachability.
void internetStatus(JsonDocument& doc) {
    doc["ipv4_forwarding"] = forwarding;
    doc["internet_mode"] = state;
    doc["dhcp_dns"] = offeredDns.toString();
}

