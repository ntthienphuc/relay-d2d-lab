using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

[assembly: AssemblyTitle("Relay Lab")]
[assembly: AssemblyProduct("Relay Lab")]
[assembly: AssemblyVersion("2.6.0.1")]
[assembly: AssemblyFileVersion("2.6.0.1")]

internal static class Program
{
    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr handle);
    [DllImport("user32.dll")] private static extern bool ShowWindowAsync(IntPtr handle, int command);
    [DllImport("user32.dll")] private static extern bool IsIconic(IntPtr handle);
    [DllImport("user32.dll")] private static extern bool SetProcessDPIAware();

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)] private static extern int SetCurrentProcessExplicitAppUserModelID(string id);
    [STAThread]
    private static void Main(string[] args)
    {
        bool practice = Array.IndexOf(args, "--practice") >= 0;
        string caption = practice ? "Relay Lab · Phòng tập" : "Relay Lab · Phòng đo";
        bool first;
        using (var instance = new Mutex(true, @"Local\RelayLab.Desktop." + (practice ? "Practice" : "Live"), out first))
        {
            if (!first)
            {
                foreach (var p in Process.GetProcessesByName("RelayLab"))
                using (p)
                {
                    if (p.MainWindowTitle != caption) continue;
                    if (IsIconic(p.MainWindowHandle)) ShowWindowAsync(p.MainWindowHandle, 9);
                    SetForegroundWindow(p.MainWindowHandle);
                    break;
                }
                return;
            }
            SetCurrentProcessExplicitAppUserModelID(practice ? "RelayLab.Desktop.Practice" : "RelayLab.Desktop");
            SetProcessDPIAware();
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new LabWindow(practice, caption));
        }
    }
}

internal sealed class LabWindow : Form
{
    private readonly bool practice;
    private readonly string home;
    private readonly string dataDir;
    private readonly Uri address;
    private readonly WebView2 view = new WebView2();
    private readonly Label message = new Label();
    private readonly CancellationTokenSource closing = new CancellationTokenSource();
    private Process server;
    private bool ready;
    private bool exitApproved;
    private bool requestingClose;

    public LabWindow(bool practice, string caption)
    {
        this.practice = practice;
        home = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Demo");
        dataDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Relay Lab");
        address = new Uri("http://127.0.0.1:" + (practice ? "8877" : "8765") + "/");
        Text = caption;
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(700, 480);
        Size = new Size(1240, 820);
        WindowState = FormWindowState.Maximized;
        BackColor = Color.FromArgb(246, 245, 240);
        message.Dock = DockStyle.Fill;
        message.TextAlign = ContentAlignment.MiddleCenter;
        message.Font = new Font("Segoe UI", 14);
        message.ForeColor = Color.FromArgb(51, 53, 45);
        message.Text = practice ? "Đang mở phòng tập…" : "Đang mở phòng đo…";
        view.Dock = DockStyle.Fill;
        Controls.Add(view);
        Controls.Add(message);
        Shown += async (sender, e) => await StartRoom();
        FormClosing += ConfirmClose;
    }

    private async Task<Dictionary<string, object>> GetStatus()
    {
        var request = (HttpWebRequest)WebRequest.Create(new Uri(address, "api/status"));
        request.Proxy = null;
        using (var timeout = CancellationTokenSource.CreateLinkedTokenSource(closing.Token))
        {
            timeout.CancelAfter(1400);
            using (timeout.Token.Register(request.Abort))
            {
                try
                {
                    using (var response = await request.GetResponseAsync())
                    using (var reader = new StreamReader(response.GetResponseStream()))
                        return new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(await reader.ReadToEndAsync());
                }
                catch (WebException) { return null; }
            }
        }
    }

    private void StartController()
    {
        string python = Path.Combine(home, @".venv\Scripts\python.exe");
        var info = new ProcessStartInfo(python, @"desktop\desktop_server.py" + (practice ? " --practice" : ""));
        info.WorkingDirectory = home;
        info.UseShellExecute = false;
        info.CreateNoWindow = true;
        info.RedirectStandardInput = true;
        info.RedirectStandardError = true;
        info.EnvironmentVariables["PYTHONUTF8"] = "1";
        string log = Path.Combine(dataDir, practice ? "practice.log" : "hardware.log");
        File.WriteAllText(log, "");
        server = new Process { StartInfo = info };
        server.ErrorDataReceived += (sender, e) =>
        {
            if (String.IsNullOrWhiteSpace(e.Data)) return;
            try { File.AppendAllText(log, e.Data + Environment.NewLine); } catch (IOException) {}
        };
        server.Start();
        server.BeginErrorReadLine();
    }

    private static void OpenLink(string value)
    {
        if (value == "ms-settings:network-wifi")
        {
            Process.Start(new ProcessStartInfo(value) { UseShellExecute = true });
            return;
        }
        Uri uri;
        if (Uri.TryCreate(value, UriKind.Absolute, out uri) && (uri.Scheme == Uri.UriSchemeHttp || uri.Scheme == Uri.UriSchemeHttps))
            Process.Start(new ProcessStartInfo(uri.AbsoluteUri) { UseShellExecute = true });
    }

    private async Task StartRoom()
    {
        try
        {
            Directory.CreateDirectory(dataDir);
            var status = await GetStatus();
            closing.Token.ThrowIfCancellationRequested();
            if (status == null)
            {
                StartController();
                for (int i = 0; i < 100 && status == null; i++)
                {
                    await Task.Delay(175, closing.Token);
                    if (server.HasExited) throw new InvalidOperationException("Bộ điều khiển chưa khởi động được. Kiểm tra cổng mạng và nhật ký phòng đo.");
                    status = await GetStatus();
                }
            }
            if (status == null || !status.ContainsKey("version") || (string)status["version"] != "2.6.0"
                || !status.ContainsKey("practice") || !Equals(status["practice"], practice))
                throw new InvalidOperationException("Phòng đo chưa sẵn sàng. Kiểm tra ứng dụng đang dùng cổng " + address.Port + ".");
            var env = await CoreWebView2Environment.CreateAsync(null, Path.Combine(dataDir, "WebView"));
            closing.Token.ThrowIfCancellationRequested();
            await view.EnsureCoreWebView2Async(env);
            closing.Token.ThrowIfCancellationRequested();
            view.CoreWebView2.NewWindowRequested += (sender, e) => { e.Handled = true; OpenLink(e.Uri); };
            view.CoreWebView2.NavigationStarting += (sender, e) =>
            {
                Uri to;
                if (Uri.TryCreate(e.Uri, UriKind.Absolute, out to) && to.GetLeftPart(UriPartial.Authority) == address.GetLeftPart(UriPartial.Authority)) return;
                e.Cancel = true;
                OpenLink(e.Uri);
            };
            view.CoreWebView2.NavigationCompleted += (sender, e) =>
            {
                if (e.IsSuccess) { ready = true; message.Visible = false; view.Focus(); }
                else if (!closing.IsCancellationRequested) { message.Visible = true; message.Text = "Không mở được dashboard. Hãy đóng cửa sổ và thử lại."; }
            };
            view.Source = address;
        }
        catch (Exception ex)
        {
            if (closing.IsCancellationRequested || IsDisposed) return;
            string detail = ex is WebView2RuntimeNotFoundException ? "Cần Microsoft Edge WebView2 Runtime để mở cửa sổ Relay Lab." : ex.Message;
            message.Text = detail + Environment.NewLine + "Nhật ký ứng dụng: " + dataDir;
        }
    }

    private async void ConfirmClose(object sender, FormClosingEventArgs e)
    {
        if (exitApproved || !ready || server == null || server.HasExited || e.CloseReason != CloseReason.UserClosing) return;
        e.Cancel = true;
        if (requestingClose) return;
        requestingClose = true;
        try
        {
            var state = await GetStatus();
            var run = state != null && state.ContainsKey("run") ? state["run"] as Dictionary<string, object> : null;
            if (run != null && run.ContainsKey("finished") && Equals(run["finished"], false))
            {
                MessageBox.Show(this, "Phiên đo đang chạy. Bạn có thể chờ lưu kết quả hoặc bấm Kết thúc trong dashboard rồi đóng cửa sổ.", "Relay Lab");
                return;
            }
            exitApproved = true;
            BeginInvoke(new Action(Close));
        }
        finally { requestingClose = false; }
    }

    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        closing.Cancel();
        if (server != null)
        {
            try { if (!server.HasExited) { server.StandardInput.Close(); server.WaitForExit(2500); } }
            catch (InvalidOperationException) {}
            server.Dispose();
        }
        base.OnFormClosed(e);
    }
}


