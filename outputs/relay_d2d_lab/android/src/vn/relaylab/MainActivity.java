package vn.relaylab;
import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.WindowManager;
import android.view.View;
import android.widget.*;
import android.content.SharedPreferences;
import java.util.UUID;

public class MainActivity extends Activity {
    private EditText server,peer,peerPort;
    private Spinner role;
    private TextView status;
    private Button start;
    private UdpNode node;
    private android.net.wifi.WifiManager.WifiLock wifiLock;
    private String id;
    private SharedPreferences prefs;
    private final int fg=Color.rgb(39,57,69), muted=Color.rgb(113,132,144);
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private TextView text(String value,int size,int color){TextView v=new TextView(this);v.setText(value);v.setTextSize(size);v.setTextColor(color);v.setPadding(0,dp(8),0,dp(8));return v;}
    private EditText input(LinearLayout box,String label,String value){box.addView(text(label,13,muted));EditText e=new EditText(this);e.setSingleLine(true);e.setText(value);e.setTextColor(fg);e.setTextSize(17);e.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(202,218,225)));box.addView(e);return e;}

    @Override public void onCreate(Bundle state){
        super.onCreate(state);getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setStatusBarColor(Color.rgb(247,249,250));getWindow().setNavigationBarColor(Color.WHITE);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        prefs=getSharedPreferences("lab",MODE_PRIVATE);
        id=prefs.getString("id",null);if(id==null){id=UUID.randomUUID().toString().substring(0,8);prefs.edit().putString("id",id).apply();}
        ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(Color.rgb(247,249,250));
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(22),dp(16),dp(22),dp(30));scroll.addView(box);setContentView(scroll);
        box.addView(text("RELAY LAB  /  ANDROID NODE",12,Color.rgb(35,132,109)));
        box.addView(text("Thiết bị cộng tác",23,fg));
        box.addView(text(android.os.Build.MODEL+" · ID "+id+"\nUDP thật · CRC32 · ACK · log cục bộ",14,muted));
        String host=getIntent().getStringExtra("server");if(host==null)host=prefs.getString("server","192.168.1.6");
        server=input(box,"IP laptop (bảng điều khiển cổng 8765)",host);
        box.addView(text("Vai trò của điện thoại",13,muted));
        role=new Spinner(this);ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"RELAY — nhận và chuyển tiếp","DESTINATION — nhận và trả ACK"});role.setAdapter(adapter);box.addView(role);
        if("sink".equals(getIntent().getStringExtra("role")))role.setSelection(1);
        peer=input(box,"Đích ban đầu của relay (dashboard tự cập nhật)",host);
        peerPort=input(box,"Cổng đích",getIntent().getStringExtra("target_port")==null?"39002":getIntent().getStringExtra("target_port"));
        start=new Button(this);start.setText("BẮT ĐẦU NODE");start.setTextColor(Color.WHITE);start.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(10,128,106)));box.addView(start);
        start.setOnClickListener(v->{if(node!=null&&node.isRunning())stopNode();else startNode();});
        Button pause=new Button(this);pause.setText("Tạm dừng / tiếp tục chuyển tiếp");pause.setTextColor(Color.rgb(57,107,91));pause.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(230,240,235)));box.addView(pause);pause.setOnClickListener(v->{if(node!=null)node.togglePause();});
        status=text("Chưa chạy. Giữ ứng dụng ở màn hình trước khi đo.",15,fg);status.setTextIsSelectable(true);box.addView(status);
        box.addView(text("Phạm vi: chuyển tiếp gói ở tầng ứng dụng qua mạng Wi-Fi/LAN. AF/DF tầng tín hiệu được phân tích trong mô phỏng trên laptop. Không đo AF analog trên điện thoại.",12,muted));
        if(getIntent().getBooleanExtra("auto",false))start.postDelayed(this::startNode,400);
    }
    private void startNode(){
        try{
            String ip=server.getText().toString().trim();if(!ip.matches("[0-9.]+"))throw new IllegalArgumentException("Nhập IPv4 laptop");
            String r=role.getSelectedItemPosition()==0?"relay":"sink";
            node=new UdpNode(id,ip,r,r.equals("relay")?39010:39011,peer.getText().toString().trim(),Integer.parseInt(peerPort.getText().toString()),getFilesDir(),s->runOnUiThread(()->status.setText(s)));
            android.net.wifi.WifiManager wifi=(android.net.wifi.WifiManager)getApplicationContext().getSystemService(WIFI_SERVICE);
            wifiLock=wifi.createWifiLock(android.net.wifi.WifiManager.WIFI_MODE_FULL_HIGH_PERF,"RelayLab:measurement");wifiLock.acquire();
            node.start();prefs.edit().putString("server",ip).apply();start.setText("DỪNG NODE");
            server.setEnabled(false);role.setEnabled(false);peer.setEnabled(false);peerPort.setEnabled(false);
        }catch(Exception e){releaseWifi();status.setText("Không khởi động được: "+e.getMessage());}
    }
    private void releaseWifi(){if(wifiLock!=null&&wifiLock.isHeld())wifiLock.release();}
    private void stopNode(){if(node!=null)node.stop();releaseWifi();start.setText("BẮT ĐẦU NODE");server.setEnabled(true);role.setEnabled(true);peer.setEnabled(true);peerPort.setEnabled(true);status.setText("Đã dừng node. Log được giữ trên máy.");}
    @Override public void onDestroy(){if(node!=null)node.stop();releaseWifi();super.onDestroy();}
}
