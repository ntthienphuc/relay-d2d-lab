package vn.relaylab;

import android.app.*;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;

/** Read the local append-only journal, including sessions from older installations. */
final class JournalView {
    static final int SAVE = 71;
    private final Activity activity;
    private final File file;
    int selected;
    JournalView(Activity context) {
        activity = context; file = new File(context.getFilesDir(), "events.jsonl");
    }
    private interface Entry { void read(String line, JSONObject event) throws Exception; }
    private void scan(Entry consumer) throws Exception {
        if (!file.exists()) return;
        try (BufferedReader input = new BufferedReader(new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8))) {
            String line;
            while ((line = input.readLine()) != null) {
                JSONObject event;
                try { event = new JSONObject(line); } catch (JSONException incomplete) { continue; }
                consumer.read(line, event);
            }
        }
    }
    void show() {
        new Thread(() -> {
            try {
                LinkedHashMap<Integer,int[]> runs = new LinkedHashMap<>();
                scan((line,e) -> {
                    int run = e.getInt("run");
                    int[] n = runs.get(run);
                    if (n == null) { n = new int[4]; runs.put(run,n); }
                    switch(e.optString("type")) {
                        case "send": n[0]++; break;
                        case "receive": n[1]++; break;
                        case "ack": n[2]++; break;
                        case "forward": n[3]++; break;
                    }
                });
                List<Integer> ids = new ArrayList<>(runs.keySet());
                Collections.reverse(ids);
                String[] rows = new String[ids.size()];
                for (int i=0; i<rows.length; i++) {
                    int[] n = runs.get(ids.get(i));
                    rows[i] = "Phiên " + ids.get(i) + "\n" +
                        (n[0]>0 ? n[0]+" phát · "+n[2]+" ACK về" : n[3]>0 ? n[3]+" đã chuyển" : n[1]+" lượt nhận DATA");
                }
                activity.runOnUiThread(() -> {
                    if (activity.isFinishing() || activity.isDestroyed()) return;
                    AlertDialog.Builder dialog = new AlertDialog.Builder(activity).setTitle("Nhật ký trên máy này");
                    if (rows.length == 0) dialog.setMessage("Sau lượt đo đầu tiên, phiên sẽ xuất hiện ở đây.");
                    else dialog.setItems(rows,(d,i) -> {
                        prepare(ids.get(i));
                    });
                    dialog.setNegativeButton("Đóng",null).show();
                });
            } catch (Exception e) { notice("Đọc log thất bại: " + e.getMessage()); }
        },"read-journal").start();
    }
    private File snapshot(int run) { return new File(activity.getCacheDir(),"export-"+run+".jsonl"); }
    private void prepare(int run) {
        selected = run;
        new Thread(() -> {
            File pending = snapshot(run);
            try {
                try (BufferedWriter out = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(pending),StandardCharsets.UTF_8))) {
                    scan((line,e) -> { if (e.optInt("run") == run) { out.write(line); out.newLine(); } });
                }
                if (pending.length()==0) throw new IOException("Phiên chưa có sự kiện.");
                activity.runOnUiThread(()->{
                    if(activity.isFinishing()||activity.isDestroyed())return;
                    Intent save = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                        .setType("application/octet-stream").putExtra(Intent.EXTRA_TITLE,"RelayLab-"+run+".jsonl");
                    activity.startActivityForResult(save,SAVE);
                });
            } catch (Exception e) { notice("Chuẩn bị log thất bại: "+e.getMessage()); }
        },"prepare-export").start();
    }
    void export(Uri uri) {
        File pending = snapshot(selected);
        try {
            if(pending.length()==0) throw new IOException("Mở lại phiên trong Nhật ký.");
            try (InputStream input=new FileInputStream(pending);
                 OutputStream out=activity.getContentResolver().openOutputStream(uri,"w")) {
                if(out==null)throw new IOException("Chưa mở được tệp.");
                byte[] buffer=new byte[8192]; int n;
                while ((n=input.read(buffer))!=-1) out.write(buffer,0,n);
            }
            pending.delete();
            notice("Đã xuất log phiên "+selected);
        } catch(Exception e){notice("Xuất log thất bại: "+e.getMessage());}
    }
    private void notice(String msg) { activity.runOnUiThread(() -> Toast.makeText(activity,msg,Toast.LENGTH_LONG).show()); }
}
