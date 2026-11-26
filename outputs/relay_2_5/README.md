# Relay Lab 2.6

Mã chạy, APK và hướng dẫn PDF nằm trong `../relay_d2d_lab`. Bộ cài Windows, thư viện ngoại tuyến và các tài liệu được đóng chung trong bộ bàn giao tại Downloads.

- `python -m pytest tests -q` chạy các bài kiểm thử từ gốc demo.
- `python scripts/reproduce_final.py` tính lại kết quả mô phỏng và đối chiếu các phiên thiết bị.
- `python scripts/check_phone_room.py` khớp DATA và ACK theo phiên, số thứ tự và dấu thời gian. Thư mục `Nghiem_thu` giữ log Android và kết quả phép thử qua ESP.


ESP32-CAM là RelayBox. Mở trang của board để cấu hình Wi-Fi, tra DATA/ACK và đối chiếu Direct, DF, AF-FG, AF-VG. Các phép thử của bản này ở `../relay_d2d_lab/results/internet_26`.
