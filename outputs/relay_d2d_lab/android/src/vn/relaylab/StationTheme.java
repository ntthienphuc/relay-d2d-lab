package vn.relaylab;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Native controls share sizes, typography, and states across the station screens. */
final class StationTheme {
    static final int INK=0xff252620, TEXT=0xff44443b, SOFT=0xff5c5d53, ACCENT=0xff993713,
        LIGHT=0xfffae6d8, PAGE=0xfff6f5f0, WHITE=0xfffffef9, EDGE=0xffdedbcf;
    private final Context ctx;

    StationTheme(Context context){ctx=context;}
    int dp(int v){return Math.round(v*ctx.getResources().getDisplayMetrics().density);}
    LinearLayout group(boolean horizontal){
        LinearLayout v=new LinearLayout(ctx);
        v.setOrientation(horizontal?LinearLayout.HORIZONTAL:LinearLayout.VERTICAL);
        if(horizontal)v.setGravity(Gravity.CENTER_VERTICAL);
        return v;
    }
    void pad(View v,int x,int y){v.setPadding(dp(x),dp(y),dp(x),dp(y));}
    GradientDrawable bg(int fill,int edge,int radius){
        GradientDrawable d=new GradientDrawable();d.setColor(fill);d.setCornerRadius(dp(radius));
        if(edge!=fill)d.setStroke(dp(1),edge);
        return d;
    }
    TextView label(String value,int size,int color,boolean bold){
        TextView t=new TextView(ctx);t.setText(value);t.setTextSize(size);t.setTextColor(color);
        t.setTypeface(Typeface.create(bold?"sans-serif-medium":"sans-serif",Typeface.NORMAL));
        t.setIncludeFontPadding(false);t.setLineSpacing(dp(2),1);return t;
    }
    void mono(TextView v){v.setTypeface(Typeface.create("monospace",Typeface.NORMAL));}
    void add(LinearLayout parent,View v,int top){
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.topMargin=dp(top);parent.addView(v,lp);
    }
    void flex(LinearLayout row,View v,int gap){
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,-2,1);
        lp.leftMargin=dp(gap);row.addView(v,lp);
    }
    LinearLayout card(LinearLayout parent){
        LinearLayout v=group(false);pad(v,16,16);v.setBackground(bg(WHITE,EDGE,15));add(parent,v,13);return v;
    }
    Button button(String text,boolean main){
        Button b=new Button(ctx);b.setText(text);b.setAllCaps(false);b.setTextSize(14);
        b.setMinimumHeight(dp(46));b.setMinHeight(dp(46));b.setMinimumWidth(0);b.setMinWidth(0);
        b.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));
        b.setStateListAnimator(null);pad(b,8,7);paint(b,main?INK:WHITE,main?INK:EDGE,main?WHITE:INK);
        return b;
    }
    void paint(Button b,int fill,int edge,int color){
        b.setTextColor(color);b.setBackgroundTintList(null);
        b.setBackground(new RippleDrawable(ColorStateList.valueOf(0x33d35c31),bg(fill,edge,9),null));
    }
}

