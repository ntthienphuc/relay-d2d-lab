package vn.relaylab;

import org.json.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.locks.LockSupport;

/** All RTT measurements use System.nanoTime in this same source process. */
public final class SourceSession {
    private final DatagramSocket socket;
    private final Telemetry telemetry;
    private final Map<Integer,Long> stamps=new ConcurrentHashMap<>();
    private final Set<Integer> acks=Collections.newSetFromMap(new ConcurrentHashMap<Integer,Boolean>());
    private volatile boolean emitting=false;
    private volatile int run=0, sent=0;
    private volatile String error="";
    private InetSocketAddress target;
    public SourceSession(DatagramSocket socket,Telemetry telemetry){this.socket=socket;this.telemetry=telemetry;}
    public synchronized void start(JSONObject c)throws Exception{
        int next=c.getInt("run_id");if(next==run)return;
        if(emitting)throw new IllegalStateException("Previous source run still active");
        double duration=c.getDouble("duration");int rate=c.getInt("rate"),size=c.getInt("payload");
        if(duration<1||duration>120||rate<1||rate>200||size<16||size>1024)throw new IllegalArgumentException("Run limits");
        target=new InetSocketAddress(c.getString("target_ip"),c.getInt("target_port"));
        run=next;sent=0;stamps.clear();acks.clear();error="";emitting=true;
        int corrupt=c.optInt("corrupt_every",0);
        new Thread(()->emit(next,duration,rate,size,corrupt),"relay-source").start();
    }
    private void emit(int runId,double duration,int rate,int size,int corrupt){
        long begin=System.nanoTime();int count=(int)Math.round(duration*rate);
        try{
            for(int seq=0;seq<count&&emitting;seq++){
                long due=begin+(long)(seq*1e9/rate),left;
                while(emitting&&(left=due-System.nanoTime())>0)LockSupport.parkNanos(Math.min(left,10_000_000));
                if(!emitting)break;
                Packet p=Packet.data(runId,seq,size);byte[] raw=p.encode();
                boolean bad=corrupt>0&&(seq+1)%corrupt==0;if(bad)raw[raw.length-1]^=1;
                stamps.put(seq,p.stamp);
                socket.send(new DatagramPacket(raw,raw.length,target));sent++;
                JSONObject extra=new JSONObject();extra.put("corrupted_deliberately",bad);
                telemetry.event("send",p,null,null,extra);
            }
            long end=begin+(long)(duration*1e9)+2_000_000_000L;
            while(emitting&&System.nanoTime()<end)LockSupport.parkNanos(10_000_000);
        }catch(Exception e){error=e.toString();}
        finally{
            emitting=false;
            try{Packet p=new Packet();p.run=runId;p.seq=-1;
                JSONObject extra=new JSONObject();extra.put("source_sent",sent);extra.put("source_elapsed_s",(System.nanoTime()-begin)/1e9);
                extra.put("source_error",error);telemetry.event("source_done",p,null,null,extra);
            }catch(Exception ignored){}
        }
    }
    public void ack(Packet p,SocketAddress address){
        if(p.run!=run||target==null||!target.equals(address))return;
        Long stamp=stamps.get(p.seq);
        if(stamp==null||stamp.longValue()!=p.stamp||!acks.add(p.seq))return;
        telemetry.event("ack",p,null,(System.nanoTime()-p.stamp)/1e6,null);
    }
    public void stop(){emitting=false;}
    public int sentCount(){return sent;}
    public int ackCount(){return acks.size();}
    public boolean active(){return emitting;}
    public int runId(){return run;}
    public String status(){return "Nguồn: "+sent+" gửi · "+acks.size()+" ACK"+(emitting?" · ĐANG PHÁT":" · CHỜ LỆNH")+(error.isEmpty()?"":"\n"+error);}
}
