package vn.relaylab;

import android.os.SystemClock;
import java.io.Closeable;
import java.io.IOException;
import java.util.*;
import org.json.*;

/** One Android on the router manages the same DATA/ACK protocol as the PC. */
final class PhoneRoom implements Closeable {
    private static final long ONLINE_MS = 8000;
    private final Map<String, JSONObject> devices = new HashMap<>();
    private final Map<String, Long> seen = new HashMap<>();
    private final RoomHttp http;
    private final String owner;
    private JSONObject relayCommand, sourceCommand;
    private String relayId, sourceId;
    private long armedUntil, busyUntil;
    private boolean readyToSend;
    private int run;
    private String message = "Chờ ESP và điện thoại còn lại.";

    PhoneRoom(String ip, String owner) throws IOException {
        this.owner = owner;
        http = new RoomHttp(ip, this::post);
    }

    private synchronized JSONObject post(String path, JSONObject body) throws Exception {
        if (path.equals("/api/events")) {
            body.getJSONArray("events"); // Each phone already keeps its own durable trace.
            return new JSONObject();
        }
        if (!path.equals("/api/device")) throw new IOException("Unknown endpoint");
        String id = body.getString("id");
        if (id.length() > 64 || id.isEmpty()) throw new IOException("Invalid device");
        devices.put(id, body);
        long now = SystemClock.elapsedRealtime();
        seen.put(id, now);
        if (armedUntil != 0 && now >= armedUntil) {
            armedUntil = 0; busyUntil = 0; sourceCommand = null; relayCommand = null;
            message = "Hết thời gian chờ xác nhận. Kiểm tra ESP và thử lại.";
        }
        if (id.equals(relayId) && relayCommand != null) {
            if (armedUntil != 0 && body.optInt("control_version", -1) == relayCommand.getInt("version"))
                readyToSend = true;
            return relayCommand;
        }
        if (id.equals(sourceId) && readyToSend && sourceCommand != null) {
            if (armedUntil != 0) {
                armedUntil = 0; busyUntil = now + 9000;
                message = "Phiên " + run + " · 50 gói trong 5 giây.";
            }
            if (now < busyUntil) return sourceCommand;
        }
        return new JSONObject();
    }

    private JSONObject online(String role) {
        JSONObject found = null;
        for (JSONObject d : devices.values()) {
            if (SystemClock.elapsedRealtime() - seen.get(d.optString("id")) >= ONLINE_MS ||
                !d.optBoolean("running") || !role.equals(d.optString("role"))) continue;
            if (found != null) return null;
            found = d;
        }
        return found;
    }

    synchronized boolean canStart() {
        return armedUntil == 0 && SystemClock.elapsedRealtime() >= busyUntil &&
               online("source") != null && online("sink") != null && online("relay") != null;
    }

    synchronized String status() {
        if (armedUntil != 0 || SystemClock.elapsedRealtime() < busyUntil) return message;
        if (online("relay") == null) return "Chờ ESP. Trong trang ESP, đặt IP máy mở phòng là IP điện thoại này.";
        if (online("sink") == null || online("source") == null) return "Đã thấy ESP. Trên máy còn lại, nối RelayBox rồi chọn vai trò và Gateway ESP.";
        return run == 0 ? "Đã đủ ba trạm. Bạn có thể bắt đầu đo." : message + " Xem Nhật ký trên mỗi điện thoại.";
    }

    synchronized void startRun() throws Exception {
        if (!canStart()) throw new IOException("Chờ đủ ba trạm sẵn sàng.");
        JSONObject src = online("source"), sink = online("sink"), relay = online("relay");
        relayId = relay.getString("id"); sourceId = src.getString("id");
        boolean hostSends = owner.equals(sourceId);
        JSONObject remote = hostSends ? sink : src;
        if (!"esp32".equals(relay.optString("platform")) || !relayId.equals(remote.optString("bridge_id")) ||
            !(hostSends || owner.equals(sink.optString("id"))))
            throw new IOException("Máy mở phòng ở Wi-Fi router. Máy còn lại phải nối RelayBox và chọn Gateway ESP.");
        run = (int)(System.currentTimeMillis() % Integer.MAX_VALUE);
        relayCommand = new JSONObject().put("version", relay.optInt("control_version", 0) + 1)
            .put("target_ip", sink.getString("local_ip")).put("target_port", sink.getInt("listen_port"))
            .put("paused", false).put("drop_every", 0);
        sourceCommand = new JSONObject().put("version", src.optInt("control_version", 0) + 1)
            .put("action", "start").put("run_id", run).put("duration", 5).put("rate", 10).put("payload", 128)
            .put("target_ip", relay.getString(hostSends ? "local_ip" : "ap_ip")).put("target_port", relay.getInt("listen_port"));
        readyToSend = false; armedUntil = SystemClock.elapsedRealtime() + 9000;
        message = "Đang chờ ESP xác nhận đường đến đích.";
    }
    public void close() throws IOException { http.close(); }
}
