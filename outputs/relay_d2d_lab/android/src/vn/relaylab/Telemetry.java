package vn.relaylab;

import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Durable local JSONL plus bounded retry queue. No data packets use HTTP. */
public final class Telemetry implements Closeable {
    private final String id, role, session, server;
    private final WifiLink wifi;
    private final BufferedWriter log;
    private final ArrayDeque<JSONObject> queue=new ArrayDeque<>();
    private long counter=0, lost=0;
    private boolean closed=false;
    public Telemetry(String id,String role,String session,String server,File dir,WifiLink wifi)throws IOException{
        this.id=id;this.role=role;this.session=session;this.server=server;
        this.wifi=wifi;
        log=new BufferedWriter(new OutputStreamWriter(new FileOutputStream(new File(dir,"events.jsonl"),true),StandardCharsets.UTF_8));
    }
    public synchronized void event(String type,Packet p,Double processing,Double rtt,JSONObject extra){
        if(closed)return;
        try{
            JSONObject e=extra==null?new JSONObject():extra;
            e.put("event_id",id+":"+session+":"+(counter++));e.put("type",type);
            e.put("device_id",id);e.put("node",role.equals("source")?"S":role.equals("relay")?"R":"D");
            e.put("run",p.run);e.put("seq",p.seq);e.put("bytes",p.payload.length);e.put("hops",p.hops);
            e.put("sent_ns",p.stamp);e.put("device_mono_ns",System.nanoTime());
            if(processing!=null)e.put("processing_ms",processing);
            if(rtt!=null)e.put("rtt_ms",rtt);
            log.write(e.toString());log.newLine();
            log.flush();
            if(queue.size()<10000)queue.add(e);else lost++;
        }catch(Exception e){lost++;}
    }
    public synchronized int pending(){return queue.size();}
    public synchronized long lost(){return lost;}
    public JSONObject post(String path,JSONObject body)throws Exception{
        HttpURLConnection c=wifi.open(new URL("http://"+server+":8765"+path));
        c.setRequestMethod("POST");c.setConnectTimeout(1800);c.setReadTimeout(2500);c.setDoOutput(true);
        c.setRequestProperty("Content-Type","application/json");
        try{
            try(OutputStream out=c.getOutputStream()){out.write(body.toString().getBytes(StandardCharsets.UTF_8));}
            if(c.getResponseCode()!=200)throw new IOException("HTTP "+c.getResponseCode());
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            try(InputStream in=c.getInputStream()){byte[] b=new byte[4096];int n;while((n=in.read(b))>0){bytes.write(b,0,n);if(bytes.size()>65536)throw new IOException("Response too large");}}
            return new JSONObject(bytes.toString("UTF-8"));
        }finally{c.disconnect();}
    }
    public void flushBatch()throws Exception{
        JSONArray batch=new JSONArray();
        synchronized(this){int n=0;for(JSONObject e:queue){if(n++==(server.equals("192.168.50.1")?32:128))break;batch.put(e);}}
        if(batch.length()==0)return;
        JSONObject body=new JSONObject();body.put("events",batch);post("/api/events",body);
        synchronized(this){for(int i=0;i<batch.length();i++)queue.removeFirst();log.flush();}
    }
    public synchronized void close()throws IOException{if(!closed){closed=true;log.close();}}
}
