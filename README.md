# Relay Lab · ESP32 RelayBox

Đồ án *Mạng truyền thông cộng tác Relay, D2D* đặt router và nguồn ở tầng 1, RelayBox ở tầng 2 và đích ở tầng 3. Nhóm đã kiểm tra mô hình trên bàn. ESP32 kết nối Wi-Fi của router, phát mạng cho máy đích, chuyển DATA/ACK và chia sẻ Internet bằng IPv4 NAPT. Android có thể đóng vai nguồn, đích hoặc relay gói.

| Mở từ nhánh này | Nội dung |
| --- | --- |
| [Hướng dẫn và kịch bản demo](outputs/relay_d2d_lab/Huong_dan_va_kich_ban_demo.pdf) | Cách nối thiết bị và kịch bản 5 phút ở cuối |
| [Phim 3D có lời kể tiếng Việt](outputs/relay_2_5/Hanh_trinh_cua_mot_goi_tin.mp4) | 1 phút 52 giây về DATA/ACK, NAPT, AF, DF và hai lượt đo qua ESP |
| [PowerPoint](outputs/relay_2_5/Relay_D2D_Thuyet_trinh_cuoi_ky.pptx) · [PDF slide](outputs/relay_2_5/Slide_xem_nhanh.pdf) | 24 slide từ bài toán, lý thuyết đến mô phỏng và đo thật |
| [Tiểu luận](outputs/relay_2_5/Bao_cao_Relay_D2D.pdf) · [Nguồn LaTeX](outputs/relay_2_5/Bao_cao_Overleaf.zip) | 40 trang, đồ thị trắng đen |
| [Mã nguồn](outputs/relay_d2d_lab) · [APK](outputs/relay_d2d_lab/android/build/relaylab.apk) | Windows 2.6.1, Android và firmware ESP32 2.6.0 |
| [Nghiệm thu PC](outputs/relay_d2d_lab/results/ux_261/acceptance.json) · [20 phiên ghép cặp](outputs/relay_2_5/Nghiem_thu/So_lieu_20_phien_ghep_cap.csv) | Kết quả theo từng mã phiên |
| [Bài báo và phương pháp](outputs/relay_d2d_lab/research/PAPER_REVIEW.html) | Các giả định và nguồn đối chiếu |

Trong bộ giao tại Downloads, mở **BAT_DAU.html** để tìm bộ cài Windows và tài liệu. Để chạy từ mã nguồn trên Windows, vào `outputs/relay_d2d_lab`, chạy `scripts/setup.ps1` rồi `START_READY.cmd`. Phòng đo mặc định ở cổng 8765.

Từ gốc demo với môi trường Python của dự án, chạy `python -m pytest tests -q` và `python scripts/reproduce_final.py` để đối chiếu các số đo và tính lại kết quả mô phỏng.

### Mã dựng phim

Cảnh nhà ba tầng, thiết bị, gói tin, máy hiện sóng, camera và phụ đề nằm ở [work/relay_film](work/relay_film). Trong thư mục đó, mở PowerShell và dùng `py -3.11 -m pip install --target film-tools piper-tts==1.8.0 imageio-ffmpeg==0.8.1`. Tải hai tệp của [giọng Piper VAIS-1000 medium](https://huggingface.co/rhasspy/piper-voices/tree/main/vi/vi_VN/vais1000/medium) vào `film-voice`. Chạy `py -3.11 audio.py` để tạo lời kể, nhạc nền và mốc phụ đề. Sau đó chạy `npm install --no-save playwright` rồi `node render.cjs` trên Windows có Chrome. Có thể đặt `RELAY_CHROME` và `RELAY_FFMPEG` để chỉ định chương trình đã cài ở đường dẫn khác.

Dạng sóng AF và DF trong phim dùng tín hiệu minh họa. Số liệu thực nghiệm ở cuối phim lấy từ phiên 409270498 và 409351681. Giọng tổng hợp dựa trên ngữ liệu [VAIS-1000](https://ieee-dataport.org/documents/vais-1000-vietnamese-speech-synthesis-corpus) theo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
