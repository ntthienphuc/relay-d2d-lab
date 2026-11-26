package vn.relaylab;

import android.content.Context;
import android.net.*;
import android.net.wifi.*;
import android.os.BatteryManager;
import org.json.JSONObject;
import java.net.*;

/** Bind DATA and management to the same real Wi-Fi, even without Internet. */
public final class WifiLink {
    private final Context context;
    public final Network network;
    public final String ip;
    private WifiLink(Context c,Network n,String address){context=c.getApplicationContext();network=n;ip=address;}
    public static WifiLink choose(Context c)throws Exception{
        ConnectivityManager cm=(ConnectivityManager)c.getSystemService(Context.CONNECTIVITY_SERVICE);
        for(Network n:cm.getAllNetworks()){
            NetworkCapabilities cap=cm.getNetworkCapabilities(n);LinkProperties props=cm.getLinkProperties(n);
            if(cap==null||!cap.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)||props==null)continue;
            for(LinkAddress a:props.getLinkAddresses())if(a.getAddress() instanceof Inet4Address&&!a.getAddress().isLinkLocalAddress())
                return new WifiLink(c,n,a.getAddress().getHostAddress());
        }
        throw new IllegalStateException("Chưa có Wi-Fi. Nối mạng lab hoặc RelayBox rồi bắt đầu lại.");
    }
    public void bind(DatagramSocket socket)throws Exception{network.bindSocket(socket);}
    public HttpURLConnection open(URL url)throws Exception{return (HttpURLConnection)network.openConnection(url,java.net.Proxy.NO_PROXY);}
    public boolean available(){
        ConnectivityManager cm=(ConnectivityManager)context.getSystemService(Context.CONNECTIVITY_SERVICE);
        LinkProperties props=cm.getLinkProperties(network);
        if(props==null)return false;
        for(LinkAddress a:props.getLinkAddresses())if(ip.equals(a.getAddress().getHostAddress()))return true;
        return false;
    }
    public JSONObject describe(){
        JSONObject out=new JSONObject();
        try{
            out.put("local_ip",ip);out.put("wifi_connected",available());
            WifiManager wm=(WifiManager)context.getSystemService(Context.WIFI_SERVICE);WifiInfo info=wm.getConnectionInfo();
            String ssid=info.getSSID();out.put("wifi_ssid",ssid==null||ssid.equals("<unknown ssid>")?"Wi-Fi (chưa cấp quyền tên mạng)":ssid.replace("\"",""));
            out.put("rssi_dbm",info.getRssi());out.put("wifi_frequency_mhz",info.getFrequency());
            BatteryManager battery=(BatteryManager)context.getSystemService(Context.BATTERY_SERVICE);
            out.put("battery_percent",battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY));
        }catch(Exception ignored){}
        return out;
    }
}
