package vn.relaylab;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

/** Two small HTTP endpoints already spoken by the ESP and the Android nodes. */
final class RoomHttp implements Closeable {
    interface Handler { JSONObject post(String path, JSONObject body) throws Exception; }
    private final ServerSocket server;
    private final Handler handler;

    RoomHttp(String address, Handler handler) throws IOException {
        this.handler = handler;
        server = new ServerSocket();
        server.setReuseAddress(true);
        server.bind(new InetSocketAddress(address, 8765), 12);
        new Thread(this::listen, "room-http").start();
    }

    private void listen() {
        while (!server.isClosed()) {
            try (Socket client = server.accept()) {
                client.setSoTimeout(2200);
                handle(client);
            } catch (IOException ignored) { /* A reconnect opens a new request. */ }
        }
    }

    private static String line(InputStream in) throws IOException {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        for (int c; (c = in.read()) >= 0 && buffer.size() < 2048;) {
            if (c == '\n') return buffer.toString("US-ASCII").trim();
            buffer.write(c);
        }
        throw new IOException("Invalid HTTP header");
    }

    private void handle(Socket socket) throws IOException {
        InputStream in = new BufferedInputStream(socket.getInputStream());
        JSONObject reply = new JSONObject();
        String status = "200 OK";
        try {
            String[] request = line(in).split(" ");
            if (request.length != 3 || !"POST".equals(request[0])) throw new IOException();
            int length = -1;
            for (int n = 0; n < 40; n++) {
                String header = line(in);
                if (header.isEmpty()) break;
                if (header.regionMatches(true, 0, "Content-Length:", 0, 15))
                    length = Integer.parseInt(header.substring(15).trim());
                if (n == 39) throw new IOException();
            }
            if (length < 2 || length > 65536) throw new IOException();
            byte[] raw = new byte[length];
            new DataInputStream(in).readFully(raw);
            reply = handler.post(request[1], new JSONObject(new String(raw, StandardCharsets.UTF_8)));
        } catch (Exception malformed) { status = "400 Bad Request"; }
        byte[] data = reply.toString().getBytes(StandardCharsets.UTF_8);
        OutputStream out = socket.getOutputStream();
        out.write(("HTTP/1.1 " + status + "\r\nContent-Type: application/json\r\nContent-Length: " +
                   data.length + "\r\nConnection: close\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
        out.write(data);
        out.flush();
    }
    public void close() throws IOException { server.close(); }
}
