# Chạy Relay Lab từ mã nguồn

**Đo trên thiết bị** mở sẵn tuyến qua ESP32. Chọn nguồn, relay, đích và bắt đầu đo. Khi laptop làm máy điều phối, đặt laptop trong vùng Wi-Fi của router. Hai Android có thể tự vận hành một phòng đo và lưu nhật ký trên từng máy. **Mô phỏng** có mô hình kênh và bài tập UDP nội bộ. **Nhật ký** cho phép tra một gói theo mã phiên và số thứ tự.

[Hướng dẫn và kịch bản demo](Huong_dan_va_kich_ban_demo.pdf) · [Tiểu luận và PowerPoint](../relay_2_5) · [Kết quả nghiệm thu](results/ux_261/acceptance.json)

| Thư mục | Chức năng |
| --- | --- |
| `esp32` | Firmware RelayBox, cấu hình Wi-Fi, chuyển gói, NAPT và so sánh giao thức theo mô hình |
| `android` | Nguồn hoặc đích; ghi và xuất nhật ký trên máy |
| `lab`, `desktop`, `web` | Điều phối phiên, cửa sổ Windows và giao diện Three.js |
| `sim`, `research`, `results` | Mô hình kênh, bài báo và dữ liệu thí nghiệm |
| `tests`, `scripts` | Kiểm thử, tái lập và đóng gói |

Trên Windows, dùng Python 3.9 x64. Mở PowerShell tại thư mục này, chạy `.\scripts\setup.ps1` và `.\START_READY.cmd`. Để mở phòng tập riêng chỉ trên laptop, chạy `.\TAP_TREN_LAPTOP.cmd`. Bộ cài Windows trong thư mục bàn giao Downloads đã có môi trường Python.

Chạy `.venv\Scripts\python.exe -m pytest tests -q` và `.venv\Scripts\python.exe scripts/reproduce_final.py` để kiểm tra mô hình kênh, nhật ký phần cứng và kết quả do ESP tính.
