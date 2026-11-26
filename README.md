# Relay Lab · ESP32 RelayBox

Đồ án *Mạng truyền thông cộng tác Relay, D2D* đặt router và nguồn ở tầng 1, RelayBox ở tầng 2 và đích ở tầng 3. Nhóm đã kiểm tra mô hình trên bàn. ESP32 kết nối Wi-Fi của router, phát mạng cho máy đích, chuyển DATA/ACK và chia sẻ Internet bằng IPv4 NAPT. Android có thể đóng vai nguồn, đích hoặc relay gói.

| Mở từ nhánh này | Nội dung |
| --- | --- |
| [Hướng dẫn và kịch bản demo](outputs/relay_d2d_lab/Huong_dan_va_kich_ban_demo.pdf) | Cách nối thiết bị và kịch bản 5 phút ở cuối |
| [Phim 3D có lời kể tiếng Việt](outputs/relay_2_5/Hanh_trinh_cua_mot_goi_tin.mp4) | 1 phút 45 giây về DATA/ACK, NAPT, AF, DF và hai lượt đo qua ESP |
| [PowerPoint](outputs/relay_2_5/Relay_D2D_Thuyet_trinh_cuoi_ky.pptx) · [PDF slide](outputs/relay_2_5/Slide_xem_nhanh.pdf) | 24 slide từ bài toán, lý thuyết đến mô phỏng và đo thật |
| [Tiểu luận](outputs/relay_2_5/Bao_cao_Relay_D2D.pdf) · [Nguồn LaTeX](outputs/relay_2_5/Bao_cao_Overleaf.zip) | 31 trang, hình dạng sóng AF/DF và kết quả thực nghiệm |
| [Mã nguồn](outputs/relay_d2d_lab) · [APK](outputs/relay_d2d_lab/android/build/relaylab.apk) | Windows 2.6.1, Android và firmware ESP32 2.6.0 |
| [Nghiệm thu PC](outputs/relay_d2d_lab/results/ux_261/acceptance.json) · [20 phiên ghép cặp](outputs/relay_2_5/Nghiem_thu/So_lieu_20_phien_ghep_cap.csv) | Kết quả theo từng mã phiên |
| [Bài báo và phương pháp](outputs/relay_d2d_lab/research/PAPER_REVIEW.html) | Các giả định và nguồn đối chiếu |

Trong bộ giao tại Downloads, mở **BAT_DAU.html** để tìm bộ cài Windows và tài liệu. Để chạy từ mã nguồn trên Windows, vào `outputs/relay_d2d_lab`, chạy `scripts/setup.ps1` rồi `START_READY.cmd`. Phòng đo mặc định ở cổng 8765.

Từ gốc demo với môi trường Python của dự án, chạy `python -m pytest tests -q` và `python scripts/reproduce_final.py` để đối chiếu các số đo và tính lại kết quả mô phỏng.

### Mã dựng phim

Cảnh nhà ba tầng, gói tin, máy hiện sóng và phụ đề nằm ở [work/relay_film](work/relay_film). Trong môi trường Python 3.11, cài `python -m pip install vieneu==3.8.5` rồi chạy `python audio.py` tại thư mục đó. Lần đầu chạy cần Internet để tải bộ tổng hợp tiếng Việt. Chương trình tạo `film-narration.wav` và ghi thời điểm từng câu vào `film/timeline.json`. Phần AF/DF trong hoạt họa chuyển trạng thái theo các mốc lời kể này.

Để xuất MP4, cài FFmpeg trên PATH, chạy `npm install --no-save playwright` rồi chạy `node render.cjs` trên Windows có Chrome. Hai biến `RELAY_CHROME` và `RELAY_FFMPEG` cho phép chọn đường dẫn chương trình.

Dạng sóng AF và DF minh họa mô hình tín hiệu. Kết quả hai chiều cuối phim lấy từ phiên 409270498 và 409351681 trên bàn đo. Giọng kể dùng mẫu Thiện Minh của [VieNeu-TTS v3 Turbo](https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo). Ảnh bo ESP32-CAM trong báo cáo và slide lấy từ [DFRobot, DFR0602](https://www.dfrobot.com/product-1879.html).
