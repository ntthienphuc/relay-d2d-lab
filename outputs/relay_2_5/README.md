# Bộ bảo vệ Relay Lab 2.7.0

[PowerPoint có ghi chú](Relay_D2D_Thuyet_trinh_cuoi_ky.pptx) · [Slide PDF](Slide_xem_nhanh.pdf) · [Tiểu luận](Bao_cao_Relay_D2D.pdf) · [Nguồn LaTeX](Bao_cao_Overleaf.zip) · [Hướng dẫn và kịch bản demo](../relay_d2d_lab/Huong_dan_va_kich_ban_demo.pdf)

ESP32 chuyển gói giữa hai đầu. Điện thoại hoặc laptop có thể gửi và nhận. Trong phép đối chứng Direct, hai đầu dùng cùng mạng gốc.

Slide 5 minh họa AF và DF, slide 8 dùng một ví dụ số để giải thích outage và slide 22 đối chiếu log DATA với log ACK của cùng một phiên. [Phim 3D có lời kể](Hanh_trinh_cua_mot_goi_tin.mp4) cũng được nhúng ở slide 1.

[Nghiệm thu bản 2.7](../relay_d2d_lab/results/final/release27.json) ghi hai phiên đo qua ESP32 với Samsung 2.7.0, firmware 2.6.0 và phòng điều phối Windows 2.6.1. Mỗi chiều ghi nhận 40/40 gói ở đích và 40 ACK tại nguồn. Giao diện Windows 2.7 được kiểm tra riêng. [Dữ liệu so sánh](Nghiem_thu/So_lieu_20_phien_ghep_cap.csv) và [manifest cho bộ bàn giao ở Downloads](Kiem_chung.json) cho phép đối chiếu lại kết quả.
