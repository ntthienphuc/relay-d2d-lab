package vn.relaylab;

import android.os.Build;
import org.json.*;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

public final class UdpNode {
    public interface Listener { void update(String text); }
    private final Listener listener;
    private final WifiLink wifi;
    private volatile boolean managementOk=false;
    private volatile String connectionMessage="Đang kết nối…";
    private final String id,server,role,session=UUID.randomUUID().toString().substring(0,8);
    private final int port;
    private final File directory;
    private final Set<Integer> seen=new HashSet<>();
    private DatagramSocket socket;
    private Telemetry telemetry;
    private SourceSession source;
    private volatile boolean running=false;
    private volatile long received=0,acknowledged=0,invalid=0,duplicates=0;
    private volatile int controlVersion=-1;
    private int currentRun=0;
    private String localIp;

    public UdpNode(String id,String server,String role,int port,File dir,WifiLink wifi,Listener listener){
        if (!"source".equals(role) && !"sink".equals(role)) throw new IllegalArgumentException("Chọn Nguồn hoặc Đích.");
        this.id=id;this.server=server;this.role=role;this.port=port;this.listener=listener;directory=dir;
        this.wifi=wifi;localIp=wifi.ip;
    }
    public void start()throws Exception{
        socket=new DatagramSocket(null);socket.setReuseAddress(true);socket.bind(new InetSocketAddress(port));socket.setSoTimeout(500);
        wifi.bind(socket);telemetry=new Telemetry(id,role,session,server,directory,wifi);source=new SourceSession(socket,telemetry);running=true;
        new Thread(this::receiveLoop,"relay-udp").start();new Thread(this::managementLoop,"relay-management").start();
    }
    public void stop(){running=false;if(source!=null)source.stop();if(socket!=null)socket.close();}
    public boolean isRunning(){return running;}
    private void event(String type,Packet p,Double processing){telemetry.event(type,p,processing,null,null);}
    private void send(Packet p,SocketAddress address)throws Exception{
        byte[] raw=p.encode();socket.send(new DatagramPacket(raw,raw.length,address));
    }
    private void receiveLoop(){
        byte[] buffer=new byte[1500];
        while(running){
            DatagramPacket raw=new DatagramPacket(buffer,buffer.length);
            try{
                socket.receive(raw);
                Packet p=Packet.decode(Arrays.copyOf(raw.getData(),raw.getLength()));
                if(role.equals("source")){if(p.kind==Packet.ACK)source.ack(p,raw.getSocketAddress());continue;}
                if(p.kind==Packet.DATA){
                    if(!p.expectedPayload()){invalid++;event("invalid",p,null);continue;}
                    if(currentRun!=p.run){currentRun=p.run;seen.clear();received=acknowledged=invalid=duplicates=0;}
                    received++;if(!seen.add(p.seq))duplicates++;
                    event("receive",p,null);send(p.ack(),raw.getSocketAddress());acknowledged++;event("ack_sent",p,null);
                }
            }catch(SocketTimeoutException ignored){}
             catch(IllegalArgumentException e){
                invalid++;
                // Only use header identity to label a rejected packet; never forward it.
                if(raw.getLength()>=32&&buffer[0]=='R'&&buffer[1]=='L'&&buffer[2]=='Y'&&buffer[3]=='1'){
                    java.nio.ByteBuffer b=java.nio.ByteBuffer.wrap(buffer);Packet p=new Packet();p.run=b.getInt(8);p.seq=b.getInt(12);event("invalid",p,null);
                }
             }catch(Exception e){if(running)listener.update("UDP: "+e.getMessage());}
        }
    }
    private JSONObject identity()throws Exception{
        JSONObject d=new JSONObject();d.put("id",id);d.put("model",Build.MODEL);d.put("role",role);
        d.put("local_ip",localIp);d.put("listen_port",port);d.put("running",running);d.put("version","2.7.0");
        d.put("platform","android");d.put("session",session);d.put("control_version",controlVersion);d.put("bridge_id","");
        d.put("pending_events",telemetry.pending());d.put("queue_lost",telemetry.lost());
        JSONObject info=wifi.describe();for(Iterator<String> it=info.keys();it.hasNext();){String key=it.next();d.put(key,info.get(key));}
        d.put("management_ok",managementOk);d.put("received",received);d.put("acks",acknowledged);d.put("invalid",invalid);
        return d;
    }
    private void apply(JSONObject control)throws Exception{
        int version=control.optInt("version",-1);if(version<0||version==controlVersion)return;
        if(role.equals("source")){
            if(control.optString("action").equals("start"))source.start(control);
            if(control.optString("action").equals("stop"))source.stop();
        }
        controlVersion=version;
    }
    private void managementLoop(){
        while(running){
            String connection;
            try{
                if(!wifi.available())throw new IOException("Wi-Fi đã đổi hoặc mất kết nối; dừng và bắt đầu node lại");
                JSONObject d=identity();Packet hello=new Packet();hello.kind=Packet.HELLO;
                hello.payload=d.toString().getBytes(StandardCharsets.UTF_8);send(hello,new InetSocketAddress(server,39001));
                apply(telemetry.post("/api/device",d));telemetry.flushBatch();connection="Đã kết nối bảng điều khiển";managementOk=true;
            }catch(Exception e){connection="Chờ PC / gateway: "+e.getMessage();managementOk=false;}
            connectionMessage=connection;
            listener.update("Đang kết nối với phòng đo"+"\n"+localIp+":"+port+
                "\n\n"+(role.equals("source")?source.status():"Nhận "+received+" · ACK "+acknowledged)+
                "\nLỗi "+invalid+" · Trùng "+duplicates+"\nLog chờ "+telemetry.pending()+" · Log bỏ "+telemetry.lost()+"\n\n"+connection);
            try{Thread.sleep(250);}catch(InterruptedException ignored){}
        }
        try{telemetry.close();}catch(Exception ignored){}
    }
    public JSONObject snapshot(){
        try{JSONObject d=identity();d.put("message",connectionMessage);d.put("duplicates",duplicates);
            if(role.equals("source")){d.put("sent",source.sentCount());d.put("acks",source.ackCount());d.put("active",source.active());d.put("run_id",source.runId());}
            else d.put("run_id",currentRun);
            return d;
        }catch(Exception e){return new JSONObject();}
    }
    public static String findIp(){
        try{Enumeration<NetworkInterface> nets=NetworkInterface.getNetworkInterfaces();
            while(nets.hasMoreElements()){NetworkInterface n=nets.nextElement();if(!n.getName().startsWith("wlan"))continue;
                Enumeration<InetAddress> addresses=n.getInetAddresses();while(addresses.hasMoreElements()){InetAddress a=addresses.nextElement();if(a instanceof Inet4Address&&!a.isLoopbackAddress())return a.getHostAddress();}}
        }catch(Exception ignored){}return "0.0.0.0";
    }
}
