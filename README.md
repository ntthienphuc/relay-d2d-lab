# Relay D2D Lab

Đồ án **Chủ đề 3 — Mạng truyền thông cộng tác Relay, D2D**: demo truyền gói UDP bằng laptop và Android, mô phỏng AF/DF, dashboard 3D nền sáng và bộ slide thuyết trình tiếng Việt.

## Mở đúng phần cần dùng

| Nội dung | Đường dẫn |
| --- | --- |
| Demo, cách cài và quy trình đo | [outputs/relay_d2d_lab/README.md](outputs/relay_d2d_lab/README.md) |
| PowerPoint 30 slide, có speaker notes | [Relay_D2D_Thuyet_trinh.pptx](outputs/relay_presentation/Relay_D2D_Thuyet_trinh.pptx) |
| Lời thuyết trình, hình slide và câu hỏi bảo vệ | [Loi_thuyet_trinh_Relay_D2D.pdf](outputs/relay_presentation/Loi_thuyet_trinh_Relay_D2D.pdf) |
| Bộ tài liệu thuyết trình đóng gói | [Relay_D2D_Tron_bo.zip](outputs/relay_presentation/Relay_D2D_Tron_bo.zip) |
| Code minh họa tín hiệu AF/DF, NOMA/SIC và Monte Carlo | [outputs/relay_presentation/code](outputs/relay_presentation/code) |
| Số liệu mô phỏng, hình khoa học và log thí nghiệm | [outputs/relay_d2d_lab/results](outputs/relay_d2d_lab/results) |
| Đọc và kiểm tra bài báo tham khảo | [outputs/relay_paper_review](outputs/relay_paper_review) |
| Mã nguồn tạo slide và lời thuyết trình | [work/relay_slides](work/relay_slides) |

## Chạy demo sau khi clone

Trên Windows, cần Python 3.9 trở lên. Mở PowerShell tại thư mục repo:

```powershell
Set-Location outputs/relay_d2d_lab
.\scripts\setup.ps1
.\START_LAB.cmd
```

Mở **http://127.0.0.1:8765**. Thư viện Three.js dùng lúc chạy đã có trong `web/vendor`; môi trường Python được tạo lại bằng script setup.

Ứng dụng Android thử nghiệm: [relaylab.apk](outputs/relay_d2d_lab/android/build/relaylab.apk). Có thể cài qua USB/ADB hoặc tải từ dashboard. Cấu hình mục tiêu là **laptop nguồn → Android relay → Android đích**, các máy truy cập được nhau trong cùng LAN/Wi-Fi. USB dùng cài app và kiểm tra; dữ liệu UDP đi qua mạng.

Khi chưa có điện thoại, dùng chế độ **LOOPBACK** để kiểm tra phần mềm. Xem README của demo để cài máy thứ hai, xây dựng APK từ nguồn và đọc ý nghĩa từng chỉ số.

## Phạm vi và bằng chứng

- Android thực hiện nhận, kiểm tra và chuyển tiếp **gói tin ở tầng ứng dụng**. AF ở tầng tín hiệu được minh họa bằng mô phỏng riêng; ứng dụng điện thoại không khuếch đại sóng RF analog.
- Direct trong demo nghĩa là không qua chương trình relay; Wi-Fi vẫn có thể đi qua AP. Đây chưa phải thí nghiệm Wi-Fi Direct/sidelink, NOMA RF hay full-duplex cùng tần số.
- Pilot phần cứng đã kiểm tra với **một Android và laptop**. Cấu hình hai Android đồng thời cần đo lại khi đủ thiết bị. Không dùng kết quả một máy để khẳng định tăng vùng phủ hay ưu thế thực nghiệm của relay.
- Mô phỏng chính là SISO Rayleigh, HD hai khe bằng nhau, so sánh DF, AF fixed gain và AF variable gain. Có Monte Carlo, đối chiếu DF dạng đóng và khoảng tin cậy; chi phí năng lượng là giả định để khảo sát, chưa đo từ điện thoại.
- Log thử nghiệm, hình và biên bản kiểm tra được giữ trong repo. Kết quả cũ là bằng chứng của từng phiên, không phải cam kết mọi máy hoặc mọi cấu hình mạng đều cho cùng số đo.

## Kiểm tra và tái tạo

Từ thư mục `outputs/relay_d2d_lab` sau khi setup:

```powershell
.venv\Scripts\python -m pytest tests -q
.venv\Scripts\python scripts\export_science.py
```

Code mẫu cho thuyết trình có hướng dẫn riêng tại [HUONG_DAN.txt](outputs/relay_presentation/code/HUONG_DAN.txt). Có thể mở PowerPoint/PDF ngay, không cần chạy lại bộ tạo slide.

Các script trong `work/relay_slides` lưu lại quy trình dựng tài liệu trên máy phát triển; chúng có phụ thuộc runtime tạo slide đi kèm Codex, font Windows và PowerPoint cho bước kiểm tra hiển thị. Runtime đó không được đóng gói trong repo, nên việc dựng lại slide trên máy khác cần cấu hình đường dẫn/phụ thuộc tương ứng.

Thư mục `outputs/relay_d2d_design` giữ thiết kế ban đầu để tham khảo lịch sử. Khi có khác biệt, dùng README của demo hiện tại và bộ thuyết trình làm hướng dẫn cho cấu hình Android.

Repo không chứa môi trường ảo, `node_modules`, khóa ký APK, file tạm hay các ảnh render kiểm tra trùng lặp. APK đã build và các tài liệu cuối cùng được giữ để thuận tiện chạy demo và thuyết trình.
