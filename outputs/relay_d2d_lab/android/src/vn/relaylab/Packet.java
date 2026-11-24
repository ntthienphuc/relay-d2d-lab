package vn.relaylab;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.zip.CRC32;

public final class Packet {
    public static final int DATA=1, ACK=2, HELLO=3, HEADER=32;
    public int kind, hops, flags, run, seq;
    public long stamp;
    public byte[] payload=new byte[0];
    public static Packet decode(byte[] raw) {
        if(raw.length<HEADER) throw new IllegalArgumentException("Short header");
        ByteBuffer b=ByteBuffer.wrap(raw).order(ByteOrder.BIG_ENDIAN);
        if(b.getInt()!=0x524c5931 || b.get()!=1) throw new IllegalArgumentException("Protocol");
        Packet p=new Packet(); p.kind=b.get()&255;p.hops=b.get()&255;p.flags=b.get()&255;
        p.run=b.getInt();p.seq=b.getInt();p.stamp=b.getLong();int len=b.getShort()&65535;
        b.getShort();long crc=b.getInt()&0xffffffffL;
        if(len!=raw.length-HEADER || len>1024 || p.hops>2 || p.kind<1 || p.kind>3) throw new IllegalArgumentException("Length/hops");
        p.payload=Arrays.copyOfRange(raw,HEADER,raw.length);
        CRC32 check=new CRC32();check.update(p.payload);
        if(check.getValue()!=crc) throw new IllegalArgumentException("CRC");
        return p;
    }
    public byte[] encode() {
        ByteBuffer b=ByteBuffer.allocate(HEADER+payload.length).order(ByteOrder.BIG_ENDIAN);
        CRC32 crc=new CRC32();crc.update(payload);
        b.putInt(0x524c5931).put((byte)1).put((byte)kind).put((byte)hops).put((byte)flags);
        b.putInt(run).putInt(seq).putLong(stamp).putShort((short)payload.length).putShort((short)0);
        b.putInt((int)crc.getValue()).put(payload);return b.array();
    }
    public boolean expectedPayload() {
        for(int i=0;i<payload.length;i++) if((payload[i]&255)!=((run+seq*31+i*17)&255)) return false;
        return true;
    }
    public Packet ack(){Packet a=new Packet();a.kind=ACK;a.hops=hops;a.run=run;a.seq=seq;a.stamp=stamp;return a;}
}
