# RelayBox ESP32 · firmware 2.6

Board ESP32-CAM đã chạy IPv4 NAPT trên SoftAP. C lấy IP, gateway và DNS qua DHCP. Khi STA có địa chỉ, ESP cho phép chuyển tiếp IP sang router. Khi mạng gốc mất, ESP ngừng chia sẻ và tiếp tục thử kết nối. Nếu mạng router cũng dùng dải 192.168.50.0/24, đổi dải trên router trước khi thử. Trang 192.168.50.1 hiển thị trạng thái định tuyến. Kiểm tra HTTPS trên C để xác nhận đường ra Internet.

Trên máy mới, đặt khóa riêng cho RelayBox qua cổng nối tiếp theo lời nhắc. Khi chỉ cần duyệt web, để trống IP máy mở phòng trong trang cấu hình. DATA/ACK của phép đo vẫn dùng UDP cổng 39010. Các bộ đếm DATA/ACK chỉ dành cho gói RLY1.

Trong trang RelayBox, mở **So sánh Direct, DF và AF trên ESP** để chạy mô hình cố định trên vi xử lý. Direct, DF, AF-FG và AF-VG dùng cùng 32.768 mẫu ở từng SNR. Firmware sinh mẫu theo từng nhóm nhỏ trong tác vụ quản lý. USB và laptop có thể ngắt sau khi cấp nguồn ngoài. Số đếm thô nằm ở `/compare`. Dữ liệu Wi-Fi thật chạy ở `relay_core.h`: kiểm CRC, xử lý DATA, tra ACK và cập nhật số chặng.

## Mốc thử nghiệm trước 2.6

# RelayBox ESP32 Classic — firmware 2.1

Bản CAM 2.1 đã nạp qua đế COM17. Trong phép đo hai Android, ESP32 kết nối điểm phát ở vai trò STA và cấp SoftAP cho OPPO. [Hướng dẫn chạy và đổi Wi-Fi](../docs/READY.html) · [Phép đo thực tế](../results/paired_20261126_112923/REPORT.html). Biên bản kiểm tra SoftAP dưới đây thuộc lần nạp trước.

Firmware cho ESP32 Dev Module hoặc ESP32-CAM dùng Arduino-ESP32 **3.3.0**, ArduinoJson **7.4.2**. Mặc định không cần linh kiện ngoài: cấp nguồn/nạp qua USB/đế nạp. Đây là relay gói tin AP+STA một chặng; **không phải AF analog, Wi-Fi mesh tự phục hồi hoặc NAT Internet tổng quát**.

**Kiểm tra board thật ngày 26/11/2026:** ESP32-CAM trên COM17 (CH340), chip ESP32-D0WD-V3 rev 3.1, flash 4 MB và PSRAM 4 MB. Đã backup flash, kiểm digest, build/nạp profile CAM, chạy SoftAP và portal qua Wi-Fi thật, loại bỏ 6/6 gói sai CRC. Xem [biên bản phần cứng](../results/hardware_20261126/HARDWARE_REPORT.html). Lần kiểm tra SoftAP ban đầu chưa bao gồm chặng upstream. Đo xuyên tầng và xác nhận đường anten ngoài trên PCB còn là công việc hiện trường.

## Build và nạp

Cài Arduino CLI, rồi chuẩn bị các phụ thuộc:

```powershell
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.0 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli lib install ArduinoJson@7.4.2
```

Từ thư mục `relay_d2d_lab`:

```powershell
.\scripts\build_esp32.ps1 -ArduinoCli 'C:\duong-dan\arduino-cli.exe'
.\scripts\build_esp32.ps1 -ArduinoCli 'C:\duong-dan\arduino-cli.exe' -Port COM4 -Upload
```

Với ESP32-CAM đang dùng, chọn profile riêng (giữ nguyên bộ binary DevKit cũ):

```powershell
.\scripts\build_esp32.ps1 -Board cam
.\scripts\build_esp32.ps1 -Board cam -Port COM17 -Upload
```

COM17 là cổng đã nhận diện trong phiên 26/11; kiểm lại khi đổi cổng USB. Profile CAM dùng `esp32:esp32:esp32cam:FlashMode=dio,FlashFreq=40`, flash 4 MB, phân vùng huge_app; binary ở `build/cam/`. Backup riêng nằm ngoài Git.

Thay COM4 bằng **đúng cổng của ESP32**. Lệnh có `-Upload` ghi firmware vào board; chỉ dùng khi đã xác định board/cổng và sao lưu chương trình cần giữ. Không chọn cổng Bluetooth hoặc modem Samsung. Arduino IDE có thể mở `RelayBox/RelayBox.ino`; chọn ESP32 Dev Module cho DevKit hoặc AI Thinker ESP32-CAM cho board CAM tương thích. Không dùng cấu hình DevKit như bằng chứng đã kiểm CAM.

`build/RelayBox.ino.bin` là application image; **không ghi riêng file này vào offset 0**. Arduino CLI upload dùng bộ bootloader/partition/app đúng offset. `RelayBox.ino.merged.bin` là bộ ảnh gộp được compiler tạo cho cấu hình đã build. Các file `.elf` và `.map` chỉ dùng debug, không cần để chạy.

## Kết nối sau khi nạp

1. Mở Serial Monitor 115200 nếu cần đọc trạng thái. Board phát Wi-Fi `RelayBox-xxxxxx`, mật khẩu demo `(khóa riêng do người giữ board cung cấp)`.
2. Điện thoại vào Wi-Fi đó, chọn **giữ kết nối dù không có Internet**, mở `http://192.168.50.1`.
3. Nhập SSID/mật khẩu Wi-Fi **2,4 GHz** của hotspot iPhone/Android hoặc router và IPv4 của laptop. Mật khẩu lưu trong NVS trên board, không đưa vào mã nguồn hay log. Với iPhone 12 trở lên, bật Maximize Compatibility. Không giả định IP laptop cố định khi đổi mạng.
4. Laptop chạy Relay Lab. Chờ ESP32 xuất hiện online trên dashboard.
5. Android A ở Wi-Fi router, chọn **Nguồn**, nhập IP laptop. Android B vào Wi-Fi RelayBox, chọn **Đích**, dùng gateway `192.168.50.1`.
6. Trên PC chọn nguồn A, relay ESP32, đích B. Thử 10 giây × 20 gói/giây × 128 bytes trước. Firmware giới hạn cấu hình đo từ PC ở 50 gói/giây.

Gói DATA đi từ A → router → STA ESP32 → SoftAP → B. ACK đi ngược. UDP HELLO của B và HTTP `/api/device`, `/api/events` được ESP32 chuyển tới PC để giám sát. Proxy này chỉ phục vụ quản lý lab; không phải bộ phát Internet. Tránh router dùng dải `192.168.50.0/24` vì dải đó được dành cho SoftAP.

Muốn đo Direct, chuyển B sang Wi-Fi router, đổi địa chỉ quản lý trong app sang IP laptop, dừng/bật lại node, rồi chọn Direct. Nếu B vẫn ở SoftAP, server từ chối Direct để tránh so sánh sai topology.

## Module

- `protocol.h`: đúng header 32 byte, big-endian, CRC32, payload pattern của Python/Java.
- `relay_core.h`: logic chuyển tiếp thuần C++; cache 512 nguồn, timeout 5 s, kiểm peer/run/seq/timestamp của ACK.
- `transport.cpp`: socket UDP và chuyển HELLO qua SoftAP.
- `management.cpp`: heartbeat/control và log theo lô, chạy task riêng để HTTP không chặn vòng nhận UDP.
- `portal.cpp`: nhập Wi-Fi và proxy quản lý có danh sách endpoint cho phép.
- `config.cpp`: state có mutex, queue sự kiện hữu hạn, Preferences/NVS.
- `panel.cpp`: nút tạm ngừng có debounce và trạng thái Serial.

Nếu telemetry bị tắc, queue tối đa 256 sự kiện sẽ ghi bộ đếm `queue_lost`; không giả vờ log đầy đủ. DATA không retry ở ứng dụng; Wi-Fi vẫn có retry MAC. Heap, số gói, lỗi và RSSI có thể xem ở `/status` trên cổng 80.

## Nút và màn hình

`RELAY_BUTTON_PIN` mặc định `-1` (tắt). Sau khi xác định board/pin, có thể đặt GPIO phù hợp trong `state.h`, nút nối pin đó với GND; tránh chân boot/flash. Các màn hình số chưa rõ module, driver, anode/cathode và điện áp nên firmware **chưa kích hoạt chân màn hình**. Cần ảnh/mã linh kiện trước khi đấu. Không nối 5 V vào GPIO ESP32; anten rời chỉ dùng khi board có đầu nối RF phù hợp.

## Mức kiểm chứng

Firmware được biên dịch cho ESP32 classic và profile CAM. Cùng `protocol.h` và `relay_core.h` được chạy trên máy tính để kiểm CRC, byte order, hop, pause, ACK, timeout và cache đầy. Biên bản CAM 26/11 bổ sung bằng chứng USB/flash/boot/SoftAP/portal và loại gói sai CRC trên board thật; chưa chứng minh đường nhận từ hotspot rồi chuyển tới Android đích hoặc hiệu quả vùng phủ.

Firmware 2.5 mới cần cấp khóa SoftAP lần đầu qua USB Serial 115200, gửi 8–63 ký tự ASCII in được và kết thúc dòng LF. Khóa lưu trong NVS, không được in lại. Tắt ghi phiên terminal. Board đang dùng 2.1 vẫn hoạt động cùng PC và APK 2.5.
