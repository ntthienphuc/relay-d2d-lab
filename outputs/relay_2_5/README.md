# Relay Lab 2.5.1

Mã chạy, APK và hướng dẫn PDF nằm trong `../relay_d2d_lab`. Bộ cài Windows, thư viện ngoại tuyến và các tài liệu được đóng chung trong bộ bàn giao tại Downloads.

- `python -m pytest tests -q` chạy các bài kiểm thử từ gốc demo.
- `python scripts/reproduce_final.py` tính lại kết quả mô phỏng và đối chiếu các phiên thiết bị.
- `python scripts/check_phone_room.py` khớp DATA và ACK theo phiên, số thứ tự và dấu thời gian. Thư mục `Nghiem_thu` giữ log Android và kết quả phép thử qua ESP.
