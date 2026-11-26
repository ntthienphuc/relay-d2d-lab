package vn.relaylab;
public class PacketProbe {
    public static void main(String[] args){
        try{
            String s=args[0];byte[] raw=new byte[s.length()/2];
            for(int i=0;i<raw.length;i++)raw[i]=(byte)Integer.parseInt(s.substring(i*2,i*2+2),16);
            byte[] result=Packet.decode(raw).encode();StringBuilder out=new StringBuilder();
            for(byte b:result)out.append(String.format("%02x",b&255));System.out.print(out);
        }catch(IllegalArgumentException e){System.out.print("INVALID");}
    }
}
