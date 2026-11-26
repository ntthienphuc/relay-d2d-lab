package vn.relaylab;

import android.app.Activity;
import android.net.ConnectivityManager;
import android.net.Network;
import android.os.Bundle;
import android.webkit.*;
import android.widget.*;

public class EspPortal extends Activity {
    private ConnectivityManager manager;
    private Network previous;
    private WebView page;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        Button back = new Button(this); back.setText("‹  Quay về Relay Lab"); back.setOnClickListener(v -> finish());
        panel.addView(back); setContentView(panel);
        try {
            WifiLink wifi = WifiLink.choose(this);
            if (!wifi.ip.startsWith("192.168.50.")) throw new Exception("Hãy chọn Wi-Fi RelayBox trước khi mở trang ESP.");
            manager = (ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);
            previous = manager.getBoundNetworkForProcess();
            if (!manager.bindProcessToNetwork(wifi.network)) throw new Exception("Mất kết nối RelayBox.");
            page = new WebView(this); page.getSettings().setJavaScriptEnabled(true);
            page.getSettings().setAllowFileAccess(false); page.getSettings().setAllowContentAccess(false);
            page.setWebViewClient(new WebViewClient() {
                @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                    return !"http".equals(r.getUrl().getScheme()) || !"192.168.50.1".equals(r.getUrl().getHost());
                }
            });
            panel.addView(page); page.loadUrl("http://192.168.50.1/");
        } catch (Exception e) {
            TextView note = new TextView(this); note.setPadding(24,24,24,24); note.setText(e.getMessage()); panel.addView(note);
        }
    }
    @Override public void onDestroy() {
        if(page != null) page.destroy();
        if(manager != null) manager.bindProcessToNetwork(previous);
        super.onDestroy();
    }
}
