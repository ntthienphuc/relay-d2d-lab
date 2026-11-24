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
    private final String id, server, role;
    private final int port;
    private final File logFile;
    private final List<JSONObject> events=new ArrayList<>();
    private final Map<String,SocketAddress> origins=new ConcurrentHashMap<>();
    private final Set<Integer> seen=new HashSet<>();
    private DatagramSocket socket;
    private BufferedWriter log;
    private volatile boolean running=false, paused=false;
    private volatile InetSocketAddress target;
    private long received=0,forwarded=0,acknowledged=0,invalid=0,duplicates=0,queueLost=0;
    private long eventNumber=0;
    private int currentRun=0, controlVersion=-1;
    private String lastError="Chưa kết nối", localIp;

    public UdpNode(String id,String server,String role,int port,String targetIp,int targetPort,File dir,Listener listener) {
        this.id=id;this.server=server;this.role=role;this.port=port;this.listener=listener;
        this.target=new InetSocketAddress(targetIp,targetPort);
        logFile=new File(dir,"events.jsonl");localIp=findIp();
    }
    public void start() throws Exception {
        socket=new DatagramSocket(null);socket.setReuseAddress(true);socket.bind(new InetSocketAddress(port));
        socket.setSoTimeout(1000);log=new BufferedWriter(new FileWriter(logFile,true));running=true;
        new Thread(this::receiveLoop,"relay-udp").start();
        new Thread(this::managementLoop,"relay-management").start();
    }
    public void stop() { running=false;if(socket!=null)socket.close(); }
    public boolean isRunning(){return running;}
    public void togglePause(){paused=!paused;}

    private synchronized void event(String type,Packet p,Double processing) {
        try {
            JSONObject e=new JSONObject();e.put("event_id",id+":"+System.nanoTime()+":"+(eventNumber++));
            e.put("type",type);e.put("node",role.equals("relay")?"R":"D");
            e.put("device_id",id);e.put("run",p.run);e.put("seq",p.seq);
            e.put("bytes",p.payload.length);e.put("hops",p.hops);e.put("device_mono_ns",System.nanoTime());
            if(processing!=null)e.put("processing_ms",processing);
            log.write(e.toString());log.newLine();log.flush();
            synchronized(events){if(events.size()<10000)events.add(e);else queueLost++;}
        }catch(Exception e){lastError="Log: "+e.getMessage();}
    }
    private void send(Packet p,SocketAddress address)throws Exception {
        byte[] raw=p.encode();socket.send(new DatagramPacket(raw,raw.length,address));
    }
    private void receiveLoop() {
        byte[] buffer=new byte[1500];
        while(running) {
            try {
                DatagramPacket raw=new DatagramPacket(buffer,buffer.length);socket.receive(raw);
                long start=System.nanoTime();Packet p=Packet.decode(Arrays.copyOf(raw.getData(),raw.getLength()));
                if(p.kind==Packet.DATA) {
                    if(!p.expectedPayload()) { invalid++;event("invalid",p,null);continue; }
                    if(currentRun!=p.run){currentRun=p.run;seen.clear();received=forwarded=acknowledged=invalid=duplicates=0;origins.clear();}
                    received++;
                    if(!seen.add(p.seq))duplicates++;
                    if(role.equals("relay")) {
                        event("relay_receive",p,null);
                        if(paused){event("drop_paused",p,null);continue;}
                        if(p.hops>=1){invalid++;event("invalid",p,null);continue;}
                        origins.put(p.run+":"+p.seq,raw.getSocketAddress());
                        if(origins.size()>30000)origins.clear();
                        p.hops++;send(p,target);forwarded++;
                        event("forward",p,(System.nanoTime()-start)/1e6);
                    }else{
                        event("receive",p,null);send(p.ack(),raw.getSocketAddress());acknowledged++;
                    }
                }else if(p.kind==Packet.ACK && role.equals("relay")) {
                    SocketAddress origin=origins.remove(p.run+":"+p.seq);
                    if(origin!=null){send(p,origin);acknowledged++;event("ack_forward",p,null);}
                }
            }catch(SocketTimeoutException ignored){}catch(IllegalArgumentException e){invalid++;}
             catch(Exception e){if(running)lastError="UDP: "+e.getMessage();}
        }
        try { synchronized(this){if(log!=null)log.close();} }catch(Exception ignored){}
    }
    private JSONObject post(String path,JSONObject data)throws Exception {
        URL url=new URL("http://"+server+":8765"+path);
        HttpURLConnection c=(HttpURLConnection)url.openConnection();c.setRequestMethod("POST");
        c.setConnectTimeout(1200);c.setReadTimeout(1200);c.setDoOutput(true);
        c.setRequestProperty("Content-Type","application/json");
        try{
            try(OutputStream out=c.getOutputStream()){out.write(data.toString().getBytes(StandardCharsets.UTF_8));}
            if(c.getResponseCode()!=200)throw new IOException("HTTP "+c.getResponseCode());
            ByteArrayOutputStream b=new ByteArrayOutputStream();
            try(InputStream in=c.getInputStream()){byte[] chunk=new byte[4096];int n;while((n=in.read(chunk))>0)b.write(chunk,0,n);}
            return new JSONObject(b.toString("UTF-8"));
        }finally{c.disconnect();}
    }
    private JSONObject identity()throws Exception {
        JSONObject d=new JSONObject();d.put("id",id);d.put("model",Build.MODEL);d.put("role",role);
        d.put("local_ip",localIp);d.put("listen_port",port);d.put("running",running);d.put("version","1.0");d.put("control_version",controlVersion);
        synchronized(events){d.put("pending_events",events.size());}return d;
    }
    private void managementLoop() {
        while(running) {
            try {
                JSONObject d=identity();Packet hello=new Packet();hello.kind=Packet.HELLO;
                hello.payload=d.toString().getBytes(StandardCharsets.UTF_8);
                send(hello,new InetSocketAddress(server,39001));
                JSONObject control=post("/api/device",d);
                int v=control.optInt("version",-1);
                if(v!=controlVersion && v>=0){
                    target=new InetSocketAddress(control.optString("target_ip",target.getHostString()),control.optInt("target_port",target.getPort()));
                    paused=control.optBoolean("paused",false);controlVersion=v;
                }
                JSONArray batch=new JSONArray();int n;
                synchronized(events){n=Math.min(200,events.size());for(int i=0;i<n;i++)batch.put(events.get(i));}
                if(n>0){JSONObject body=new JSONObject();body.put("events",batch);post("/api/events",body);
                    synchronized(events){events.subList(0,n).clear();}}
                lastError="Đã kết nối laptop • dữ liệu qua UDP/Wi-Fi";
            }catch(Exception e){lastError="Kết nối: "+e.getMessage();}
            String status=(running?"ĐANG CHẠY":"ĐÃ DỪNG")+(paused?" · PAUSED":"")+"\n"+
                "IP máy: "+localIp+":"+port+"\nĐích tiếp theo: "+target.getHostString()+":"+target.getPort()+
                "\n\nNhận "+received+"    Chuyển "+forwarded+"    ACK "+acknowledged+
                "\nTrùng "+duplicates+"    Lỗi "+invalid+"    Log quá tải "+queueLost+"\n\n"+lastError;
            listener.update(status);
            try{Thread.sleep(500);}catch(InterruptedException ignored){}
        }
    }
    public static String findIp(){
        try{
            Enumeration<NetworkInterface> nets=NetworkInterface.getNetworkInterfaces();
            while(nets.hasMoreElements()){NetworkInterface n=nets.nextElement();if(!n.getName().startsWith("wlan"))continue;
                Enumeration<InetAddress> a=n.getInetAddresses();while(a.hasMoreElements()){InetAddress x=a.nextElement();if(x instanceof Inet4Address&&!x.isLoopbackAddress())return x.getHostAddress();}}
        }catch(Exception ignored){}return "0.0.0.0";
    }
}
