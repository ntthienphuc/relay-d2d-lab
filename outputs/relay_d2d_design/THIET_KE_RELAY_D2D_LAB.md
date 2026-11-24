# Thiết kế Relay/D2D Lab — phương án chốt

Ngày 14/11/2026. Thiết bị: laptop, router, ESP32 thường, Galaxy Note9, Galaxy S9, iPhone 14 và iPhone 13. Hạn báo cáo trong ảnh: chiều 28/11/2026.

**Tên đề tài đề xuất:** Phân tích AF/DF và lựa chọn giao thức tiết kiệm năng lượng trong mạng Relay/D2D, kết hợp mô phỏng và thực nghiệm ESP32.

Đây là bản thiết kế, chưa phải phần mềm đã triển khai. Khả năng nền tảng đã được đối chiếu tài liệu Android/Espressif; chưa kết nối, nạp firmware hoặc đo trên thiết bị của người dùng. Không có kết quả cải thiện hiệu năng thực đo được khẳng định trong tài liệu này.

## 1. Sản phẩm và phân vai

Sản phẩm gồm mô phỏng khoa học AF/DF, demo truyền gói qua thiết bị thật, và giao diện 3D hiển thị kết quả/log. D2D trực tiếp cần hai thiết bị; thiết bị thứ ba xuất hiện trong cấu hình D2D có relay. Trong demo, ESP32 đại diện nút IoT cộng tác. Phạm vi thực nghiệm là Wi-Fi giữa thiết bị, không phải phép đo sidelink LTE/5G.

| Thiết bị | Vai trò | Phần mềm/kết nối |
|---|---|---|
| Note9 | Nguồn phát, tạo nhóm Wi-Fi Direct ở 2,4 GHz | Ứng dụng Android; Group Owner (GO) |
| S9 | Đích nhận, đếm gói duy nhất, trả ACK | Cùng ứng dụng Android, chọn vai trò DESTINATION |
| ESP32 | Relay nhận và gửi lại UDP; cầu thu số liệu | ESP-IDF, STA + SoftAP, USB với laptop |
| Laptop | Monte Carlo, backend, lưu kết quả và dashboard | Python + Three.js/WebGL; Wi-Fi vào router |
| Router | Mạng quản trị của laptop và iPhone | Không chở payload thử Note9–S9 |
| iPhone 14 | Màn hình cho người xem | Safari mở dashboard trong mạng router |
| iPhone 13 | Màn hình điều khiển hoặc quay demo | Không bắt buộc sử dụng đồng thời |

Hai Android cần ứng dụng native để điều khiển kết nối và gửi UDP. iPhone chỉ cần trình duyệt. Không cần thêm board hay dây LAN; cần dây USB phù hợp cho ESP32. Phần mềm, thư viện và tài nguyên 3D được lưu cục bộ để demo không phụ thuộc Internet.

## 2. Đường đi của dữ liệu

**Lượt D — truyền trực tiếp:**

```text
Note9 (nguồn, Wi-Fi Direct GO) ---- UDP DATA ----> S9 (đích, client)
                              <------ ACK ------
```

**Lượt R — truyền qua relay:**

```text
Note9 (nguồn, GO) -- UDP --> ESP32 [STA | xử lý gói | SoftAP] -- UDP --> S9
                 <-- ACK --                               <-- ACK --
```

ESP32 tham gia nhóm Note9 như một Wi-Fi station thông thường bằng SSID/password của nhóm. ESP32 đồng thời tạo SoftAP riêng cho S9. Ứng dụng relay nhận datagram ở một interface, kiểm tra rồi gửi datagram mới qua interface còn lại; không cần NAT. Hai subnet của ESP32 phải khác nhau. Địa chỉ đầu cuối được đăng ký bằng HELLO, không hard-code địa chỉ P2P của Samsung.

Android hỗ trợ GO tiếp nhận thiết bị legacy không có Wi-Fi Direct [1,2]. ESP32 hỗ trợ STA/AP đồng thời, nhưng hai interface phải dùng cùng kênh; kênh STA có ưu tiên [4]. Đây là cơ sở kỹ thuật của thiết kế, chưa bảo đảm tương thích cụ thể trên hai máy Samsung đang có.

Lượt D và R là hai phiên riêng: dừng phát, đổi kết nối S9, xác nhận HELLO rồi mới đo. Ghi thời gian tái kết nối riêng. Không gọi thao tác này là chuyển đường liền mạch. Giữ Note9 và S9 ở cùng vị trí khi so sánh; đặt ESP32 ở vị trí trung gian.

Ưu tiên nhóm P2P 2,4 GHz. API chọn băng tần có từ API 29; phải đọc Android hiện tại trên máy trước khi dùng [3]. Nếu GO trên Samsung không tương thích ổn định với ESP32, dùng hotspot 2,4 GHz của Note9, giữ nguyên hai topology và giao thức UDP. Khi đó ghi cấu hình là **relay Wi-Fi qua hotspot của thiết bị**. Không gọi kết nối fallback là Wi-Fi Direct.

**Mạng giám sát:**

```text
iPhone 13/14 -- Wi-Fi --> Router <-- Wi-Fi -- Laptop <-- USB --> ESP32
```

USB chỉ chuyển lệnh/log, không vận chuyển payload Note9–S9. Trong lượt D, ESP32 có thể vẫn nối nhóm Note9 để nhận thống kê, nhưng không chuyển tiếp DATA/ACK thử. Note9 gửi tổng hợp thống kê tới ESP32 khoảng 1 lần/giây ở cả hai lượt; ESP32 đẩy qua USB. Tính lượng byte quản trị riêng và giữ nhịp giống nhau giữa các lượt.

S9 lưu bộ đếm nhận tại đích và báo lại qua đường điều khiển. Note9 lưu log gửi/ACK; ESP32 lưu log nhận/chuyển. Khi mất báo cáo, dashboard hiện STALE thay vì 0. Log cục bộ Android được xuất sau phiên để đối chiếu. Không lấy số ACK nguồn nhận làm số gói đích nhận vì ACK cũng có thể mất.

Nếu router có 5 GHz, dùng băng tần đó cho dashboard. Nếu chỉ có 2,4 GHz, ghi lại kênh và giữ tải hiển thị thấp. Laptop có thể đặt gần ESP32 vì dây USB; hai điện thoại được di chuyển độc lập.

## 3. Giao thức và chỉ số đo

Khung gói đề xuất: version, type, run_id, sequence, source_id, destination_id, route_mode, hop_count, attempt, payload_length, checksum và payload. Loại gói: HELLO, START, DATA, ACK, STATS, END. START/END/STATS phải có xác nhận hoặc đối chiếu từ log sau phiên.

Luồng relay: nhận -> kiểm tra độ dài/run_id/checksum -> kiểm tra hop_count và gói trùng -> đưa vào hàng đợi hữu hạn -> gửi -> ghi kết quả. ACK đi ngược cùng topology. Gói thử dùng nội dung tạo tất định để kiểm tra byte đầu cuối.

Đo cơ sở với UDP không retry ở ứng dụng; Wi-Fi vẫn có ACK/retry ở MAC. Sau đó mới chạy chế độ tối đa 1 hoặc 2 lần gửi lại ở ứng dụng, báo riêng số lần gửi và số gói hữu ích. Không gọi việc bỏ retry ứng dụng là đã tắt retry Wi-Fi.

| Chỉ số | Định nghĩa |
|---|---|
| PDR | Số sequence hợp lệ duy nhất tại S9 / số sequence tạo ở Note9 |
| Goodput | Số bit payload hữu ích duy nhất nhận trong cửa sổ đo / thời lượng cửa sổ |
| RTT và p95 RTT | Note9 đo từ lúc gửi đến nhận ACK bằng cùng đồng hồ monotonic; ghi rõ chỉ trên gói có ACK |
| Timeout | Tỷ lệ không có ACK trước hạn; không thay thế PDR |
| Trễ trong relay | Thời gian giữa nhận và gọi gửi tại ESP32, đo cùng đồng hồ; không phải thời gian phát xong qua sóng |
| Chi phí | Số lần gửi, byte DATA/ACK/STATS, gói trùng, hàng đợi đầy, thời gian tái kết nối |

Không trừ timestamp Note9 và S9 để tính trễ một chiều khi chưa đồng bộ đồng hồ. RSSI chỉ hiển thị ở interface thực sự lấy được, kèm thời điểm đo; không đổi RSSI thành SNR bằng hằng số tùy ý.

Checksum ứng dụng giúp kiểm tra dữ liệu/phần mềm. Các khung Wi-Fi lỗi thường bị loại bên dưới ứng dụng; không coi log checksum ứng dụng là đo BER vô tuyến. DF cũng có thể giải mã thất bại; cơ chế kiểm tra lỗi không bảo đảm tuyệt đối mọi gói đều đúng.

## 4. Mô phỏng khoa học

Mô hình cơ sở: SISO, một nguồn S, một relay R, một đích D, Rayleigh độc lập và AWGN. Chế độ relay dùng HD hai khe bằng nhau; không gộp tín hiệu đường S-D trong mô hình cơ sở. So sánh direct, DF, AF fixed gain (FG), AF variable gain (VG). Các nút và môi trường 3D chỉ trực quan hóa mô hình; không mặc định hình học 3D đã giải bài toán lan truyền điện từ.

Với symbol x có công suất trung bình 1:

\[
y_R=\sqrt{P_S}h_{SR}x+n_R,\quad y_D=h_{RD}G y_R+n_D.
\]

\[
G_{FG}^{2}=\frac{P_R}{P_S\mathbb{E}|h_{SR}|^2+N_R},\quad
G_{VG}^{2}=\frac{P_R}{P_S|h_{SR}|^2+N_R}.
\]

\[
\gamma_{AF}=\frac{P_S|h_{SR}|^2|h_{RD}|^2G^2}{|h_{RD}|^2G^2N_R+N_D},\quad
C_{AF}=\frac12\log_2(1+\gamma_{AF}).
\]

AF khuếch đại cả tín hiệu và nhiễu nhận được. FG đáp ứng công suất relay theo trung bình; VG chuẩn hóa theo trạng thái kênh tức thời. Cần ghi rõ ràng buộc công suất trung bình và công suất đỉnh khi so sánh. Công thức VG trên giả định CSI lý tưởng; khảo sát sai số CSI là phần mở rộng tùy chọn.

DF lý tưởng có tốc độ đầu cuối:

\[
C_{DF}=\frac12\min\{\log_2(1+\gamma_{SR}),\log_2(1+\gamma_{RD})\}.
\]

Với tốc độ đích r tính trên toàn khung, đặt \(\tau=2^{2r}-1\). Dạng đóng để kiểm chứng độc lập, với hai chặng Rayleigh độc lập:

\[
p_{out,DF}=1-\exp[-\tau(1/\bar\gamma_{SR}+1/\bar\gamma_{RD})].
\]

Direct sử dụng cả khung: \(C_D=\log_2(1+\gamma_{SD})\). Ví dụ cùng năng lượng phát RF trong khung T: \(P_DT=(P_S+P_R)T/2\). Năng lượng mạch/CSI được cộng riêng. Với FG, đẳng thức công suất được hiểu theo trung bình thống kê.

Mô phỏng sinh mẫu kênh phức rồi tính SNR và đếm sự kiện C < r; đối chiếu đường DF với dạng đóng trên. Bắt đầu 10^5 mẫu/điểm khi phát triển; dùng khoảng 10^6 mẫu/điểm cho hình cuối nếu phù hợp. Báo khoảng tin cậy 95%; nếu sự kiện hiếm thì tăng mẫu hoặc chỉ báo cận, không coi không thấy outage là xác suất đúng bằng 0. Dùng chung mẫu kênh giữa phương án để so sánh; dùng seed khác cho phần đánh giá sau khi chọn tham số.

Sáu hình chính: outage–SNR; thông lượng hữu ích–SNR; bit/J theo mô hình; ảnh hưởng vị trí relay; bản đồ chọn giao thức; độ nhạy theo chi phí CSI/xử lý. Sơ đồ kênh và một công thức kiểm chứng quan trọng hơn việc thêm nhiều chế độ chưa kiểm soát được.

ESP32 demo nhận/gửi lại gói số, minh họa chuyển tiếp kiểu decode/check/forward. AF waveform, FD cùng tần số, NOMA và SIC trong bài tham khảo không được thực hiện bằng chương trình UDP này. Outage lý thuyết và tỷ lệ mất gói ứng dụng là hai chỉ số khác nhau; dữ liệu đo giúp thảo luận các ảnh hưởng MAC, hàng đợi, ACK/retry mà mô hình lý tưởng chưa bao gồm.

## 5. Mở rộng nhỏ theo hướng bài của giảng viên

Bài Tran–Voznak 2019 khảo sát sáu tổ hợp HD/FD với DF/AF-FG/AF-VG trong cooperative NOMA, có outage, throughput, energy efficiency và lựa chọn giao thức [5]. Từ đó có thể suy luận giảng viên quan tâm mô hình, công thức, đối chứng và vùng tham số làm thay đổi quyết định. Đây là suy luận từ công trình, không phải thông tin chắc chắn về cách chấm.

Mở rộng vừa sức: **chọn DF/AF-FG/AF-VG có xét năng lượng xử lý và CSI, dưới ràng buộc outage**. Với cùng số bit đích B trong một khung:

\[
\eta_m=\frac{B(1-p_{out,m})}{E_{RF,m}+E_{circuit,m}+E_{proc,m}+E_{CSI,m}},\quad
m^*=\arg\max_{m:p_{out,m}\le\epsilon}\eta_m.
\]

Các E tính bằng joule/khung, cùng phạm vi toàn hệ thống và bao gồm năng lượng của các lần thất bại. Các hạng mục không chồng lặp: circuit là mạch nền, proc là xử lý bổ sung, CSI là thu/ước lượng thông tin kênh chưa tính ở các hạng mục khác. Chọn ràng buộc công suất, thời lượng, băng thông trước khi chạy. Bộ chọn dùng thống kê kênh hoặc bảng tra theo kịch bản; không dùng trạng thái kênh tương lai. Nếu không chế độ nào đạt QoS, xuất INFEASIBLE. Chi phí thu thông tin để chọn chế độ cũng phải được tính.

Đối chứng: cố định DF, cố định FG, cố định VG, chọn theo outage, chọn theo bit/J có QoS. Hạch toán cùng mô hình năng lượng cho tất cả phương án. Khảo sát dải chi phí xử lý/CSI có dẫn nguồn hoặc ghi rõ là giả thiết; không chỉnh số để ép phương án đề xuất thắng. Không gắn số bit/J thực đo cho ESP32 khi chưa có thiết bị đo dòng/công suất.

Đây là đóng góp mở rộng ở mức bài môn học. Năng lượng mạch và lựa chọn AF/DF đã có nghiên cứu trước [6]; chưa có cơ sở tuyên bố thuật toán hoàn toàn mới. Có thể đặt câu hỏi nghiên cứu: "Khi chi phí CSI hoặc giải mã tăng, vùng chọn giao thức thay đổi thế nào dù chất lượng kênh không đổi?" Kết quả âm hoặc không đổi cũng được báo và giải thích.

## 6. Giao diện và kịch bản trình diễn

Viewport Three.js/WebGL: mô hình hai điện thoại, board ESP32, phòng/hành lang và vị trí các nút; HUD gọn chứa PDR, goodput, RTT/p95, hàng đợi và trạng thái kết nối. Hình học thể hiện bối cảnh và đường đi; các đường sóng chỉ có ý nghĩa minh họa. Biểu đồ khoa học cuối xuất bằng Matplotlib sang PDF/PNG.

Ba chế độ có nhãn cố định: SIMULATION dùng dữ liệu mô hình; LIVE dùng sự kiện/đếm gói thật; REPLAY phát lại log kèm run_id và ngày đo. Animation 3D khởi chạy khi mở trang; gói LIVE chỉ xuất hiện từ log thực. Khi tổng hợp nhiều gói thành một vệt, hiển thị hệ số gộp. Mất telemetry thì đánh dấu số liệu cũ.

Trong SIMULATION, di chuyển relay hoặc đổi mức nhiễu để xem đường cong và chế độ được chọn. Trong LIVE, bấm vào một sequence để xem nguồn gửi, ESP32 nhận/chuyển, đích nhận và ACK. Chế độ so sánh ghép hai run_id đã hoàn thành; thao tác đổi SSID ngoài đời có bước xác nhận kết nối trước khi chạy.

Chia dự án theo trách nhiệm:

```text
android/                 Kotlin: P2P, UDP source/sink, ACK, local log
firmware/                ESP-IDF: AP+STA, forwarding, queue, USB telemetry
sim/                     channel, protocols, energy, selector, experiments
backend/                 serial reader, run store, WebSocket, CSV export
frontend/src/state.js    trạng thái và schema sự kiện chung
frontend/src/nodes.js    mô hình điện thoại, board, điểm nối
frontend/src/world.js    môi trường, vật liệu, ánh sáng
frontend/src/cameras.js  camera tổng quan và theo gói
frontend/src/ui.js       HUD, trạng thái, nút điều khiển
frontend/src/main.js     khởi tạo và vòng render running=true
results/                 cấu hình, seed, raw logs, hình và bảng tổng hợp
```

Kịch bản thuyết trình 6–8 phút: giới thiệu ba nút; gửi một luồng gói trực tiếp; đổi S9 sang ESP32 và chỉ rõ hai chặng; tạm dừng chức năng chuyển tiếp để thấy payload ngừng tới đích; khôi phục; xem số liệu ở vị trí khó đã đo; mở mô phỏng AF/DF và bản đồ chọn giao thức; giải thích một đánh đổi độ tin cậy–trễ–năng lượng. Việc dừng relay là kiểm tra đường đi, không phải bằng chứng relay tăng vùng phủ.

Demo bàn học dùng luồng gói nhỏ dễ theo dõi. Demo vùng phủ dùng vị trí thực đã khảo sát, có log và video dự phòng ghi ngày đo. Nếu relay không tốt hơn direct tại một vị trí, giữ kết quả và giải thích. Khi tắt router, dự kiến payload vẫn chạy còn màn hình iPhone mất kết nối; chỉ trình diễn tình huống này sau khi đã xác nhận trên thiết bị.

## 7. Ma trận thực nghiệm và điều kiện nghiệm thu

Phép thử khả thi làm trước giao diện đầy đủ:

1. Đọc phiên bản Android; Note9 tạo GO 2,4 GHz, S9 nối và truyền UDP hai chiều.
2. ESP32 nối GO như STA; lấy IP, kiểm tra DATA/ACK.
3. ESP32 bật SoftAP cùng kênh; S9 đổi sang SoftAP; xác nhận Note9 -> ESP32 -> S9 và ACK quay lại.
4. Gửi 1.000 sequence ở khoảng cách ngắn, lưu log ba nút, đối chiếu sequence và checksum; báo các gói thiếu thực tế. Dừng forwarding phải ngừng payload trong lượt R; lượt D không phụ thuộc forwarding.
5. Chạy liên tục 10 phút, thử ngắt/nối lại và hàng đợi đầy; xác nhận không treo, không trộn run_id. Nếu P2P không tương thích, làm lại bằng hotspot 2,4 GHz và ghi đổi cấu hình.

Ma trận chính: hai topology × ba vị trí (gần, qua tường, gần giới hạn kết nối) × tối thiểu 5 lượt, mục tiêu 10 lượt/cấu hình. Mỗi lượt thử ban đầu 60 giây, 20 gói/giây, payload 128 byte, tức 1.200 sequence. Điều chỉnh tải sau pilot, đóng băng cấu hình trước lấy kết quả cuối. Dành khoảng cuối để thu gói đến muộn và log END; định nghĩa hạn nhận trước khi tính PDR/goodput.

Xen kẽ thứ tự D/R để giảm sai lệch môi trường theo thời gian; ghi vị trí, kênh, hướng thiết bị, app/firmware version, tải và chế độ tiết kiệm pin. Báo PDR, RTT và goodput từng lượt, trung bình cùng khoảng biến thiên/khoảng tin cậy. Wi-Fi có tương quan theo thời gian; dùng lượt chạy hoặc khối thời gian làm đơn vị thống kê, không mặc định hàng nghìn gói độc lập.

Phân biệt kết quả: outage từ mô hình kênh; PDR từ đích thật; RTT trên các ACK về được; điện năng theo mô hình khi chưa có đo dòng. Để chứng minh mã mô phỏng đúng cần kiểm tra công suất AF, các giới hạn SNR và DF Monte Carlo đối chiếu dạng đóng. Để chứng minh ứng dụng đúng cần đối chiếu log/byte và làm đứt đường forwarding có chủ đích.

## 8. Lộ trình đến 28/11/2026

| Ngày | Kết quả cần đạt |
|---|---|
| 14–15/11 | Probe kết nối, chốt P2P hoặc hotspot, một gói đi đủ đường |
| 16–18/11 | App Android, relay ESP32, ACK và log thống nhất |
| 19–21/11 | Mô phỏng AF/DF, công thức kiểm chứng, bộ chọn và đối chứng |
| 22–24/11 | Dashboard 3D, LIVE/REPLAY, xuất bảng và chạy khảo sát |
| 25–26/11 | Các lượt đo cuối, biểu đồ, phân tích, hoàn thiện báo cáo |
| 27/11 | Slide, diễn tập, quay video dự phòng và đóng gói |
| Sáng 28/11 | Kiểm tra thiết bị, pin và bản chạy cục bộ trước báo cáo chiều |

Báo cáo 30–40 trang theo yêu cầu ảnh: tổng quan và bài tham khảo; mô hình/công thức; thuật toán và giả mã; kiến trúc/giao thức testbed; kết quả mô phỏng; kết quả thực nghiệm; hạn chế và kết luận. Chuẩn bị slide khoảng 12–15 trang, mã nguồn, cấu hình/seed, raw log, kết quả xuất và video dự phòng. Phân bổ công sức đề xuất: 45% mô hình/kết quả, 35% thực nghiệm, 20% trình bày.

Phạm vi này khớp nội dung Relay/D2D người dùng đã chép. Ảnh hiện có là yêu cầu đầu ra; chưa đủ nguyên văn để khẳng định nhãn đánh số "chủ đề 3". Mô hình NOMA/FD chỉ mở rộng sau khi các mục cơ sở và báo cáo đã hoàn thành.

## 9. Nguồn kỹ thuật

1. [Android: Wi-Fi Direct và tạo nhóm có legacy client](https://developer.android.com/develop/connectivity/wifi/wifi-direct).
2. [Android: WifiP2pGroup, SSID và passphrase của nhóm](https://developer.android.com/reference/android/net/wifi/p2p/WifiP2pGroup).
3. [Android: WifiP2pConfig.Builder và chọn băng tần](https://developer.android.com/reference/android/net/wifi/p2p/WifiP2pConfig.Builder).
4. [Espressif: Wi-Fi STA/AP coexistence và ràng buộc home channel](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/wifi-driver/overview.html).
5. [Tran & Voznak (2019): HD/FD and DF/AF … Cooperative NOMA](https://www.mdpi.com/1424-8220/19/8/1845).
6. [Maaz et al. (2016): Energy efficiency analysis of hybrid-ARQ relay-assisted schemes in LTE-based systems](https://link.springer.com/article/10.1186/s13638-016-0520-9).

Trạng thái bàn giao: hoàn tất thiết kế và đối chiếu khả năng API trong tài liệu chính thức; chưa xây dựng ứng dụng, chưa có xác nhận phần cứng. Mốc đầu tiên khi triển khai là phép thử kết nối ở mục 7.
