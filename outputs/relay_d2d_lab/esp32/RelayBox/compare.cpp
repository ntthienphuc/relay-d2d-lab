#include "compare.h"
#include <algorithm>
#include <cmath>
#include <cstdint>

// Rayleigh power gains: independent exponential draws shared by all four modes.
// Half-duplex slots have equal duration. Direct uses the entire frame.
namespace {
constexpr unsigned samples = 32768;
constexpr int snrDb[] = {0, 8, 16};
constexpr const char* names[] = {"Direct","DF","AF-FG","AF-VG"};
constexpr uint32_t seed = 20261126;
uint32_t rng = seed;
unsigned done = 0, misses[3][4] = {};
float rho[3], meanHop[3];
bool requested = false;

float gain() {
    rng = (uint64_t(rng) * 48271) % 2147483647;
    return -logf(float(double(rng) / 2147483647.0));
}
}

void comparisonTick() {
    if (!requested || done == samples) return;
    // Bounded work in the management task keeps the UDP task independent.
    const auto until = std::min(samples, done + 128);
    for (; done < until; ++done) {
        const float u = gain(), v = gain(), w = gain();
        for (unsigned j=0;j<3;++j) {
            const float a = meanHop[j]*u, b = meanHop[j]*v;
            // R0 = 0.5. Direct threshold is sqrt(2)-1; two-slot threshold is 1.
            misses[j][0] += rho[j]*w < 0.41421356237f;
            misses[j][1] += std::min(a,b) < 1.f;
            misses[j][2] += a*b/(b+meanHop[j]+1.f) < 1.f;
            misses[j][3] += a*b/(a+b+1.f) < 1.f;
        }
    }
}

void comparisonStatus(JsonDocument& out) {
    if (!requested) {
        for (unsigned j=0;j<3;++j) {
            rho[j]=powf(10.f,snrDb[j]/10.f);
            meanHop[j]=rho[j]*powf(.5f,-2.2f);
        }
        requested=true;
    }
    out["model"]="HD Rayleigh";out["samples"]=samples;out["seed"]=seed;
    out["rate"]=.5;out["x"]=.5;out["alpha"]=2.2;out["done"]=done;
    if (done!=samples) return;
    auto rows=out["rows"].to<JsonArray>();
    for (unsigned j=0;j<3;++j) {
        auto row=rows.add<JsonObject>();row["snr_db"]=snrDb[j];
        row["df_closed"]=-expm1f(-2.f/meanHop[j]);
        for(unsigned k=0;k<4;++k) row["failures"][names[k]]=misses[j][k];
    }
}

