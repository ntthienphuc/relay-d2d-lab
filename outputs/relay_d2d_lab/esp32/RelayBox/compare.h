#pragma once
#include <ArduinoJson.h>

// The portal task calls both functions. Packet forwarding runs in the main loop.
void comparisonTick();
void comparisonStatus(JsonDocument& out);

