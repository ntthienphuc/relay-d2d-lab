package vn.relaylab;

import android.app.Activity;
import android.content.Intent;
import android.net.*;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;
import static vn.relaylab.StationTheme.*;

/** Guide client C through the ESP setup and verify HTTPS on its Wi-Fi network. */
public final class InternetActivity extends Activity {
    private StationTheme ui;
    private Button test;
    private TextView result;
    private volatile boolean checking;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        ui=new StationTheme(this);
        ScrollView scroll=new ScrollView(this); scroll.setBackgroundColor(PAGE);
        LinearLayout body=ui.group(false); ui.pad(body,18,12); scroll.addView(body); setContentView(scroll);
        Button back=ui.button("‹  Relay Lab",false); ui.add(body,back,0); back.setOnClickListener(v->finish());
        ui.add(body,ui.label("Internet qua ESP32",28,INK,true),12);
        ui.add(body,ui.label("Điện thoại C nối vào RelayBox. ESP32 ở giữa đưa lưu lượng về Wi-Fi router.",15,TEXT,false),6);
        LinearLayout card=ui.card(body);
        state=ui.label("",17,INK,true);ui.add(card,state,0);
        Button join=ui.button("1 · Chọn Wi-Fi RelayBox",false);ui.add(card,join,12);
        join.setOnClickListener(v->startActivity(new Intent(Settings.ACTION_WIFI_SETTINGS)));
        portal=ui.button("2 · Cài Wi-Fi router cho ESP",false);ui.add(card,portal,8);
        portal.setOnClickListener(v->startActivity(new Intent(this,EspPortal.class)));
        ui.add(card,ui.label("Khi cài lần đầu, nhập Wi-Fi router 2,4 GHz. Nếu chỉ mở web, có thể để trống IP máy mở phòng. ESP nhớ cấu hình cho lần sau.",14,SOFT,false),8);
        LinearLayout c=ui.card(body);
        ui.add(c,ui.label("Kiểm tra ngay trên C",18,INK,true),0);
        ui.add(c,ui.label("Khi C đã nối RelayBox, bấm thử bên dưới hoặc mở trang web trong Chrome. Bạn có thể đóng phòng đo trên laptop.",15,TEXT,false),6);
        test=ui.button("3 · Thử Internet qua ESP",true);ui.add(c,test,10);
        result=ui.label("Kết quả HTTPS sẽ hiện ở đây và được lưu trên điện thoại.",14,SOFT,false);
        result.setTextIsSelectable(true);ui.add(c,result,10);test.setOnClickListener(v->probe());
    }
    private TextView state;
    private Button portal;
    private WifiLink relayLink() throws Exception {
        WifiLink wifi=WifiLink.choose(this);
        ConnectivityManager cm=(ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);
        LinkProperties lp=cm.getLinkProperties(wifi.network);
        if(lp!=null)for(RouteInfo route:lp.getRoutes())
            if(route.isDefaultRoute()&&route.getGateway()!=null&&"192.168.50.1".equals(route.getGateway().getHostAddress()))return wifi;
        throw new IOException("Hãy chọn Wi-Fi RelayBox ở bước 1.");
    }
    @Override protected void onResume(){
        super.onResume();
        try{
            WifiLink wifi=relayLink();
            state.setText("Wi-Fi qua gateway 192.168.50.1 · "+wifi.ip);
            portal.setEnabled(true);test.setEnabled(!checking);
        }catch(Exception e){
            state.setText("Bắt đầu bằng cách nối C vào Wi-Fi RelayBox.");
            portal.setEnabled(false);test.setEnabled(false);
        }
    }
    private void probe(){
        if(checking)return;checking=true;test.setEnabled(false);
        result.setText("Đang kiểm tra DNS và HTTPS qua Wi-Fi…");
        new Thread(()->{
            JSONObject entry=new JSONObject();
            String summary;
            try{
                entry.put("time_ms",System.currentTimeMillis());WifiLink wifi=relayLink();
                entry.put("wifi_ip",wifi.ip);
                ConnectivityManager cm=(ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);
                LinkProperties link=cm.getLinkProperties(wifi.network);String gw="";
                if(link!=null)for(RouteInfo route:link.getRoutes())
                    if(route.isDefaultRoute() && route.getGateway() instanceof Inet4Address)gw=route.getGateway().getHostAddress();
                entry.put("gateway",gw);
                HttpURLConnection portal=wifi.open(new URL("http://192.168.50.1/status"));
                try{
                    portal.setConnectTimeout(3000);portal.setReadTimeout(3000);portal.setInstanceFollowRedirects(false);
                    try(BufferedReader reader=new BufferedReader(new InputStreamReader(portal.getInputStream(),StandardCharsets.UTF_8))){
                        JSONObject board=new JSONObject(reader.readLine());String id=board.optString("id");
                        if(!id.startsWith("esp32-"))throw new IOException("Gateway hiện tại chưa được nhận diện là RelayBox.");
                        entry.put("relay",id);entry.put("firmware",board.optString("version"));
                        if(!board.optBoolean("ipv4_forwarding"))throw new IOException("ESP chưa bật định tuyến. Mở bước 2 để kiểm tra Wi-Fi router.");
                    }
                }finally{portal.disconnect();}
                String endpoint="https://www.google.com/generate_204";
                entry.put("endpoint",endpoint);
                HttpURLConnection c=wifi.open(new URL(endpoint+"?relaylab="+System.nanoTime()));
                int status;
                try{c.setConnectTimeout(6500);c.setReadTimeout(6500);c.setInstanceFollowRedirects(false);c.setUseCaches(false);
                    status=c.getResponseCode();}
                finally{c.disconnect();}
                entry.put("http_status",status);
                if(status!=204)throw new IOException("HTTP "+status+" (có thể cần đăng nhập Wi-Fi)");
                entry.put("ok",true);
                summary="Đã ra Internet qua ESP · HTTPS 204\nIP "+wifi.ip+" · Gateway "+gw;
            }catch(Exception e){
                try{entry.put("ok",false);entry.put("error",e.getClass().getSimpleName());}catch(Exception ignored){}
                summary="Chưa xác nhận được Internet. Kiểm tra mạng của B rồi thử lại.\n"+e.getMessage();
            }
            try(FileOutputStream out=openFileOutput("internet-checks.jsonl",MODE_APPEND)){
                out.write((entry.toString()+"\n").getBytes(StandardCharsets.UTF_8));
            }catch(IOException e){summary+="\nChưa lưu được nhật ký.";}
            final String message=summary;
            runOnUiThread(()->{if(!isDestroyed()){result.setText(message);checking=false;test.setEnabled(true);}});
        },"wifi-https").start();
    }
}
