package vn.relaylab;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.*;
import java.util.UUID;
import static vn.relaylab.StationTheme.*;

public class MainActivity extends Activity {
    private static final String[] ROLES={"source","relay","sink"};
    private static final String[] NAMES={"Nguồn","Relay","Đích"};
    private static final String[] DESCRIPTIONS={"Phát DATA và đo thời gian chờ xác nhận (ACK).","Kiểm tra DATA, chuyển đến đích và đưa ACK về nguồn.","Nhận DATA, kiểm tra nội dung rồi gửi ACK về nguồn."};
    private static final String GATEWAY="192.168.50.1";
    private final Button[] roles=new Button[3];
    private final TextView[] values=new TextView[3], labels=new TextView[3];
    private StationTheme ui;
    private String id;
    private int role;
    private SharedPreferences prefs;
    private LinearLayout config,live,body;
    private TextView title,endpoint,state,hint,log;
    private EditText address;
    private Button action,pause,pc,esp;
    private UdpNode node;
    private PhoneRoom room;
    private JournalView history;
    private CheckBox hostRoom;
    private Button measure;
    private android.net.wifi.WifiManager.WifiLock wifiLock;
    private int generation;

    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);ui=new StationTheme(this);history=new JournalView(this);
        if(saved!=null)history.selected=saved.getInt("export_run");
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setStatusBarColor(PAGE);getWindow().setNavigationBarColor(WHITE);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR | View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
        prefs=getSharedPreferences("lab",MODE_PRIVATE);id=prefs.getString("id",null);
        if(id==null){id=UUID.randomUUID().toString().substring(0,8);prefs.edit().putString("id",id).apply();}
        LinearLayout root=ui.group(false);root.setBackgroundColor(PAGE);setContentView(root);
        LinearLayout bar=ui.group(true);ui.pad(bar,20,7);bar.setBackgroundColor(PAGE);root.addView(bar);
        TextView mark=ui.label("R",16,INK,true);
        mark.setGravity(Gravity.CENTER);
        mark.setBackground(ui.bg(0xffed794b,0xffed794b,10));
        bar.addView(mark,new LinearLayout.LayoutParams(ui.dp(34),ui.dp(34)));
        TextView brand=ui.label("Relay Lab",21,INK,true);
        brand.setLetterSpacing(-.045f);ui.flex(bar,brand,10);
        Button help=ui.button("Hướng dẫn",false);ui.paint(help,PAGE,EDGE,INK);bar.addView(help);
        help.setOnClickListener(v->help());
        ScrollView scroll=new ScrollView(this);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        body=ui.group(false);ui.pad(body,18,6);body.setFocusableInTouchMode(true);scroll.addView(body);
        LinearLayout hero=ui.group(false);ui.pad(hero,4,8);ui.add(body,hero,0);
        title=ui.label("Kết nối điện thoại",29,INK,true);title.setLetterSpacing(-.045f);ui.add(hero,title,0);
        endpoint=ui.label(android.os.Build.MODEL+" · "+id,12,SOFT,false);ui.mono(endpoint);ui.add(hero,endpoint,6);
        state=ui.label("Chọn vai trò và cách kết nối.",13,SOFT,false);ui.add(hero,state,10);
        config=ui.group(false);ui.add(body,config,0);
        LinearLayout choose=ui.card(config);ui.add(choose,ui.label("Vai trò của điện thoại",17,INK,true),0);
        LinearLayout row=ui.group(true);ui.pad(row,3,3);row.setBackground(ui.bg(PAGE,EDGE,10));ui.add(choose,row,9);
        for(int i=0;i<3;i++){
            final int index=i;roles[i]=ui.button(NAMES[i],false);ui.flex(row,roles[i],i==0?0:6);
            roles[i].setOnClickListener(v->selectRole(index));
        }
        hint=ui.label("",13,SOFT,false);ui.add(choose,hint,8);
        LinearLayout network=ui.card(config);ui.add(network,ui.label("Kết nối với phòng đo",17,INK,true),0);
        LinearLayout paths=ui.group(true);ui.pad(paths,3,3);paths.setBackground(ui.bg(PAGE,EDGE,10));ui.add(network,paths,9);
        pc=ui.button("Wi-Fi router",false);esp=ui.button("Gateway ESP",false);ui.flex(paths,pc,0);ui.flex(paths,esp,7);
        address=new EditText(this);address.setSingleLine();address.setTextColor(INK);address.setHintTextColor(SOFT);
        address.setHint("IP của máy mở phòng");address.setContentDescription("Địa chỉ IPv4 của bảng điều khiển");address.setTextSize(16);
        address.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        address.setBackground(ui.bg(PAGE,EDGE,9));ui.mono(address);ui.pad(address,12,12);ui.add(network,address,9);
        address.addTextChangedListener(new android.text.TextWatcher(){
            public void beforeTextChanged(CharSequence s,int start,int count,int after){}
            public void onTextChanged(CharSequence s,int start,int before,int count){updatePath();}
            public void afterTextChanged(android.text.Editable s){}
        });
        String host=getIntent().getStringExtra("server");address.setText(host==null?prefs.getString("server",""):host);updatePath();
        pc.setOnClickListener(v->{String savedIp=prefs.getString("lastLaptop","");address.setText(savedIp);if(savedIp.isEmpty())address.requestFocus();});
        esp.setOnClickListener(v->address.setText(GATEWAY));
        hostRoom=new CheckBox(this);hostRoom.setText("Mở phòng trên điện thoại này");ui.add(network,hostRoom,6);
        hostRoom.setOnCheckedChangeListener((v,on)->{
            address.setEnabled(!on);pc.setEnabled(!on);esp.setEnabled(!on&&role!=1);
            if(on)address.setText(UdpNode.findIp());else address.setText(prefs.getString("server",""));
        });
        Button wifi=ui.button("1 · Chọn Wi-Fi router hoặc RelayBox",false);ui.add(network,wifi,9);
        wifi.setOnClickListener(v->startActivity(new Intent(android.provider.Settings.ACTION_WIFI_SETTINGS)));
        Button portal=ui.button("2 · Cài Wi-Fi router cho ESP",false);ui.add(network,portal,6);
        portal.setOnClickListener(v->startActivity(new Intent(this,EspPortal.class)));
        if(checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)!=android.content.pm.PackageManager.PERMISSION_GRANTED){
            Button permission=ui.button("Cho phép ghi tên Wi-Fi",false);ui.add(network,permission,6);
            permission.setOnClickListener(v->requestPermissions(new String[]{android.Manifest.permission.ACCESS_COARSE_LOCATION,android.Manifest.permission.ACCESS_FINE_LOCATION},1));
        }
        live=ui.group(false);ui.add(body,live,0);
        LinearLayout stats=ui.card(live);stats.setBackground(ui.bg(INK,INK,15));ui.add(stats,ui.label("Gói tin của phiên",17,WHITE,true),0);
        LinearLayout nums=ui.group(true);ui.add(stats,nums,15);
        for(int i=0;i<3;i++){
            LinearLayout cell=ui.group(false);ui.flex(nums,cell,i==0?0:8);
            values[i]=ui.label("—",30,i==0?0xffffb18e:WHITE,true);ui.mono(values[i]);ui.add(cell,values[i],0);
            labels[i]=ui.label("",12,0xffdedacf,false);ui.add(cell,labels[i],3);
        }
        LinearLayout journal=ui.card(live);
        measure=ui.button("Đo 50 gói qua ESP",true);ui.add(journal,measure,0);
        measure.setOnClickListener(v->{try{room.startRun();measure.setEnabled(false);}catch(Exception e){state.setText(e.getMessage());}});
        Button details=ui.button("Xem chi tiết kết nối",false);ui.add(journal,details,0);
        log=ui.label("",13,TEXT,false);log.setTextIsSelectable(true);
        log.setVisibility(View.GONE);ui.add(journal,log,10);
        details.setOnClickListener(v->{
            boolean show=log.getVisibility()!=View.VISIBLE;
            log.setVisibility(show?View.VISIBLE:View.GONE);
            details.setText(show?"Thu gọn chi tiết":"Xem chi tiết kết nối");
        });
        pause=ui.button("Tạm dừng / tiếp tục relay",false);ui.add(live,pause,10);pause.setOnClickListener(v->{if(node!=null)node.togglePause();});
        LinearLayout dock=ui.group(false);dock.setBackgroundColor(WHITE);ui.pad(dock,18,10);root.addView(dock);
        Button savedLogs=ui.button("Nhật ký trên máy · Xem và xuất",false);ui.add(dock,savedLogs,0);
        savedLogs.setOnClickListener(v->history.show());
        action=ui.button("Kết nối trạm",true);ui.add(dock,action,0);
        action.setOnClickListener(v->{if(node!=null&&node.isRunning())stopNode();else startNode();});
        String r=getIntent().getStringExtra("role");if(r==null)r=prefs.getString("role","source");
        selectRole("sink".equals(r)?2:"relay".equals(r)?1:0);live.setVisibility(View.GONE);
        if(getIntent().getBooleanExtra("auto",false))action.postDelayed(this::startNode,400);
    }
    private void highlight(Button b,boolean active){ui.paint(b,active?LIGHT:PAGE,active?0xffda926f:PAGE,active?ACCENT:INK);b.setSelected(active);}
    private void updatePath(){boolean via=GATEWAY.contentEquals(address.getText());highlight(pc,!via);highlight(esp,via);}
    private void selectRole(int n){
        role=n;for(int i=0;i<3;i++)highlight(roles[i],i==n);
        hint.setText(DESCRIPTIONS[n]);hostRoom.setEnabled(n!=1);
        if(n==1)hostRoom.setChecked(false);
        esp.setEnabled(n!=1&&!hostRoom.isChecked());
        if(n==1&&GATEWAY.contentEquals(address.getText()))address.setText(prefs.getString("lastLaptop",""));
    }
    private void help(){new AlertDialog.Builder(this).setTitle("Ai mở phòng đo?").setMessage(
        "Có laptop · Giữ laptop ở Wi-Fi router. Điện thoại phía RelayBox chọn Gateway ESP. Chọn Nguồn trên máy gửi, Đích trên máy nhận, rồi bắt đầu đo trên laptop.\n\n"+
        "Hai điện thoại + ESP · Máy ở Wi-Fi router chọn Mở phòng trên điện thoại này. Dùng IP hiện trên máy đó cho ô IP máy chủ trong trang ESP. Máy ở xa nối RelayBox, chọn Gateway ESP và vai trò còn lại. Bấm Đo 50 gói trên máy mở phòng.\n\n"+
        "Qua Android làm relay · Ba trạm cùng Wi-Fi. Máy ở giữa chọn Relay, cả ba dùng IP của laptop.\n\n"+
        "Sau mỗi lượt, mở Nhật ký trên máy rồi chạm vào mã phiên để xuất file.").setPositiveButton("Đã hiểu",null).show();}
    private void showTelemetry(String message){
        if(node==null)return;
        org.json.JSONObject d=node.snapshot();boolean ok=d.optBoolean("management_ok");
        String active=d.optBoolean("paused")?"Tạm dừng chuyển tiếp":d.optBoolean("active")?"Đang phát DATA":"Sẵn sàng nhận lệnh";
        String now=ok?active:"Đang tìm phòng đo. Kiểm tra Wi-Fi và địa chỉ.";
        if(room!=null){now=room.status();measure.setEnabled(room.canStart());}
        if(!now.contentEquals(state.getText()))state.setText(now);
        String[] keys={role==0?"sent":"received",role==1?"forwarded":"acks","invalid"};
        for(int i=0;i<3;i++){String v=d.has(keys[i])?String.valueOf(d.optInt(keys[i])):"—";if(!v.contentEquals(values[i].getText()))values[i].setText(v);}
        if(!message.contentEquals(log.getText()))log.setText(message);
    }
    private void startNode(){
        String host=address.getText().toString().trim();
        if(!android.util.Patterns.IP_ADDRESS.matcher(host).matches()||host.indexOf(':')>=0||host.equals("0.0.0.0")){
            address.setError("Nhập địa chỉ IPv4 hợp lệ của laptop hoặc ESP32");address.requestFocus();return;
        }
        if (role == 1 && GATEWAY.equals(host)) {
            address.setError("Chọn Wi-Fi gốc và nhập địa chỉ laptop cho vai trò này.");
            address.requestFocus();
            return;
        }
        int epoch=++generation;String r=ROLES[role];int port=role==0?39012:role==1?39010:39011;
        try{
            WifiLink link=WifiLink.choose(this);
            if(hostRoom.isChecked()){
                if(link.ip.startsWith("192.168.50."))throw new Exception("Máy mở phòng cần nối Wi-Fi router.");
                host=link.ip;room=new PhoneRoom(host,id);
            }else if(GATEWAY.equals(host)!=link.ip.startsWith("192.168.50.")){
                throw new Exception("Kiểm tra Wi-Fi đã chọn: RelayBox dùng Gateway ESP, Wi-Fi router dùng IP máy mở phòng.");
            }
            node=new UdpNode(id,host,r,port,host,39002,getFilesDir(),link,s->runOnUiThread(()->{if(epoch==generation)showTelemetry(s);}));
            android.net.wifi.WifiManager wifi=(android.net.wifi.WifiManager)getApplicationContext().getSystemService(WIFI_SERVICE);
            wifiLock=wifi.createWifiLock(android.net.wifi.WifiManager.WIFI_MODE_FULL_HIGH_PERF,"RelayLab:measurement");wifiLock.acquire();node.start();
            SharedPreferences.Editor ed=prefs.edit().putString("server",host).putString("role",r);
            if(!GATEWAY.equals(host)&&room==null)ed.putString("lastLaptop",host);ed.apply();
            measure.setVisibility(room==null?View.GONE:View.VISIBLE);measure.setEnabled(false);
            config.setVisibility(View.GONE);live.setVisibility(View.VISIBLE);pause.setVisibility(role==1?View.VISIBLE:View.GONE);
            title.setText("Trạm "+NAMES[role].toLowerCase(java.util.Locale.ROOT));endpoint.setText(android.os.Build.MODEL+"  ·  "+host);
            labels[0].setText(role==0?"Đã phát":"Đã nhận");labels[1].setText(role==1?"Đã chuyển":role==0?"ACK nhận":"ACK gửi");labels[2].setText("Gói lỗi");
            state.setText("Đang kết nối");action.setText("Đổi kết nối");ui.paint(action,WHITE,EDGE,INK);
        }catch(Exception ex){stopNode();state.setText("Chưa khởi động · "+ex.getMessage());}
    }
    private void release(){generation++;if(node!=null){node.stop();node=null;}
        if(room!=null){try{room.close();}catch(java.io.IOException ignored){}room=null;}
        if(wifiLock!=null&&wifiLock.isHeld())wifiLock.release();}
    private void stopNode(){release();live.setVisibility(View.GONE);config.setVisibility(View.VISIBLE);title.setText("Kết nối điện thoại");endpoint.setText(android.os.Build.MODEL+"   /   "+id);state.setText("Đã dừng");action.setText("Kết nối trạm");ui.paint(action,INK,INK,WHITE);}
    @Override public void onDestroy(){release();super.onDestroy();}
    @Override protected void onSaveInstanceState(Bundle b){super.onSaveInstanceState(b);b.putInt("export_run",history.selected);}
    @Override protected void onActivityResult(int r,int result,Intent data){
        super.onActivityResult(r,result,data);
        if(r==JournalView.SAVE && result==RESULT_OK && data!=null && data.getData()!=null)history.export(data.getData());
    }
}

