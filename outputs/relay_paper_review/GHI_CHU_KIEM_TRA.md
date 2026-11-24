# Ghi chú đọc bài và hướng mở rộng cho đề tài Relay/D2D

Ngày kiểm tra: 14/11/2026.

Nguồn chính: Thanh-Nam Tran và Miroslav Voznak, *HD/FD and DF/AF with Fixed-Gain or Variable-Gain Protocol Switching Mechanism over Cooperative NOMA for Green-Wireless Networks*, Sensors 2019, 19(8), 1845. DOI: https://doi.org/10.3390/s19081845.

Bản PDF gốc trong thư mục này được tải từ https://mdpi-res.com/sensors/sensors-19-01845/article_deploy/sensors-19-01845.pdf. Bài công bố theo CC BY 4.0. PDF được giữ nguyên, không chỉnh sửa. Đây là ghi chú phân tích độc lập, không phải đính chính của tác giả.

## 1. Nhận định về phương pháp nghiên cứu

Bài kết hợp mô hình cooperative NOMA hai người dùng, sáu tổ hợp HD/FD với DF/AF-FG/AF-VG, phân tích xác suất outage, throughput và energy efficiency, rồi xây dựng cơ chế lựa chọn giao thức. Bảng 1 và Algorithm 1 dùng 10^6 mẫu kênh Monte Carlo. Phần nhận xét về ưu tiên của giảng viên chỉ là suy luận từ công trình và yêu cầu môn học, không phải bằng chứng về cách chấm điểm.

Những yếu tố nên học theo: mô hình có giả thiết rõ; định nghĩa sự kiện outage trước khi suy ra xác suất; kiểm chứng công thức bằng sinh kênh và đếm sự kiện; so sánh nhiều đường cơ sở dưới cùng tài nguyên; giải thích vùng tham số làm thay đổi lựa chọn giao thức.

Một công trình tiếp theo của cùng hai tác giả tiếp tục dùng phân tích dạng đóng và Monte Carlo độc lập: https://www.mdpi.com/1424-8220/21/4/1101.

## 2. Hướng mở rộng vừa sức

Đề xuất: lựa chọn DF/AF-FG/AF-VG có xét năng lượng xử lý và thu thập CSI, dưới ràng buộc xác suất outage. Bắt đầu với HD, một relay, một đích; nghiên cứu NOMA hai người dùng là phạm vi mở rộng nếu cần bám sát mô hình bài gốc. Không cần triển khai đồng thời cả sáu chế độ để chứng minh hiểu bài.

Với một khung có thời lượng xác định, có thể đánh giá:

\[
\eta_m=\frac{B_m(1-p_{out,m})}{E_{RF,m}+E_{proc,m}+E_{CSI,m}}.
\]

B_m là số bit hữu ích mục tiêu trong khung; các E đều tính bằng joule và bao gồm năng lượng tiêu thụ cả khi truyền thất bại. Cần thống nhất phạm vi năng lượng: chỉ relay hay toàn hệ thống. Với NOMA, tử số có thể là tổng số bit kỳ vọng đến từng người dùng, kèm ràng buộc QoS cho từng người dùng.

Chọn m tối đa hóa eta trong tập chế độ đáp ứng QoS. Nếu tập rỗng, ghi nhận không đáp ứng; chỉ tăng công suất nếu bài toán cho phép và còn trong giới hạn. Chi phí CSI/xử lý phải lấy từ tài liệu hoặc khảo sát một dải giả thiết, không chọn số để tạo lợi thế cho phương pháp đề xuất.

Ý nghĩa: một chế độ có outage thấp hơn chưa chắc có số bit hữu ích trên mỗi joule cao hơn. Phương trình (26) của bài gốc dùng tổng SNR chuẩn hóa ở mẫu số; với cùng cặp công suất/SNR, mẫu số giống nhau giữa các chế độ, nên xếp hạng theo EE và throughput tương ứng trùng nhau. Khi thêm chi phí phụ thuộc chế độ, hai mục tiêu có thể tách ra. Không diễn giải SNR chuẩn hóa trực tiếp thành điện năng phần cứng.

Tính mới chỉ nên phát biểu ở mức mở rộng và kiểm chứng cho bài môn học. Mô hình năng lượng mạch trong relay AF/DF đã có nghiên cứu trước: https://link.springer.com/article/10.1186/s13638-016-0520-9. Hysteresis giữa AF và DF cũng đã được mô tả trong tài liệu công khai: https://patents.google.com/patent/US8724495B2/en. Cơ chế thích nghi IoT có hysteresis và xét chi phí chuyển giao thức cũng đã xuất hiện, ở lớp ứng dụng: https://www.mdpi.com/2227-9709/12/4/125. Tra cứu này không đủ để xác lập tính mới toàn diện cho một bài báo.

Thiết kế đánh giá tối thiểu:

- Cố định DF, cố định AF-FG, cố định AF-VG.
- Lựa chọn chỉ theo outage/throughput làm đối chứng; ghi rõ nếu là bản đơn giản hóa theo tinh thần PSM, không gọi là tái lập toàn bộ PSM.
- Lựa chọn theo năng lượng và QoS.
- Dùng chung mẫu kênh cho các phương án, hạch toán cùng loại chi phí cho tất cả phương án.
- Đồ thị outage theo SNR; bit/J theo SNR; tỷ lệ vi phạm QoS; bản đồ lựa chọn chế độ theo chất lượng kênh và chi phí xử lý.
- Khoảng tin cậy và đánh giá trên seed/kịch bản khác với phần chọn tham số.

Nếu thêm hysteresis, cần kênh biến thiên theo thời gian, năng lượng/thời gian chuyển chế độ, số lần chuyển và các đối chứng bỏ từng thành phần. Đây là phần tùy chọn, tránh làm tăng phạm vi trước khi mô hình cơ sở đúng.

## 3. Kiểm tra riêng sự kiện outage của U1

Đây là điểm cần làm rõ trước khi tái lập; không phải đánh giá toàn bộ chất lượng bài báo.

Trong phương trình (3)-(4), hai SINR giải mã tại U1 cùng phụ thuộc vào một mẫu h_0,1 và, ở FD, một mẫu h_1,1. Theo cách hiểu fading theo khối, hai sự kiện thành công A và B không độc lập. Phương trình (16) in cả tích Pr(A)Pr(B) và xác suất giao Pr(A giao B); phương trình (17) dùng tích hai xác suất biên.

Với X=|h_0,1|^2, Y=|h_1,1|^2, X và Y độc lập và có phân bố mũ với trung bình mu_X và mu_Y; đặt tau_i=2^(2r_i)-1. Khi alpha_2-alpha_1*tau_2>0:

\[
c_1=\frac{\tau_1}{\alpha_1\rho_0},\qquad
c_2=\frac{\tau_2}{(\alpha_2-\alpha_1\tau_2)\rho_0},\qquad c=\max(c_1,c_2).
\]

Hai bước thành công đồng thời khi:

\[
X\ge c(1+\epsilon\rho_1Y).
\]

Do đó, với cùng mẫu kênh cho hai bước:

\[
p_{out,U1}=1-\frac{\exp(-c/\mu_X)}{1+c\epsilon\rho_1\mu_Y/\mu_X}.
\]

Nếu alpha_2-alpha_1*tau_2<=0, thông điệp x2 không đạt ngưỡng trong mô hình này và outage bằng 1. Kiểm tra số dưới đây dùng trường hợp mẫu số dương.

Thông số: alpha_1=0.25, alpha_2=0.75, r_1=r_2=0.2, rho_0=rho_1=1 (0 dB), mu_X=5, mu_Y=0.01. Sinh 1,000,000 cặp mẫu, seed 20261114. Mô phỏng tính trực tiếp SINR từ (3)-(4), rồi đếm phép OR của hai sự kiện không đạt ngưỡng; không lấy mẫu từ công thức outage.

| Chế độ | Monte Carlo sự kiện đồng thời | Khoảng tin cậy Wilson 95% | Dạng đóng theo giao sự kiện | Tích xác suất biên như (17) |
|---|---:|---|---:|---:|
| HD | 0.225332 | [0.224514, 0.226152] | 0.225553 | 0.295991 |
| FD | 0.227293 | [0.226473, 0.228115] | 0.227528 | 0.298455 |

Chênh lệch lớn hơn sai số Monte Carlo. Kết luận hẹp: biểu thức tích không khớp với mô hình hai sự kiện dùng chung fading block. Nếu tác giả có giả thiết hai hiện thực kênh độc lập giữa các bước, cần xác nhận rõ giả thiết đó trước khi kết luận thêm. Chưa tái lập đầy đủ các kết quả AF, các hình hay PSM trong bài.

Cách trao đổi trung tính: “Ở hai bước SIC tại U1, mình dùng chung một mẫu kênh hay sinh kênh độc lập? Nếu chung mẫu thì em đang tính xác suất giao bằng ngưỡng lớn nhất.” Không nên dùng phát hiện này làm tuyên bố novelty chính trước khi trao đổi và kiểm tra sâu hơn.

Mã chạy: [check_joint_event.py](check_joint_event.py). Kết quả máy đọc được: [joint_event_check.json](joint_event_check.json). Cần Python và NumPy; chạy `python check_joint_event.py` trong thư mục chứa mã.

## 4. Vai trò của ESP32

Một ESP32 thường cùng router, laptop và điện thoại phù hợp để đo chuyển tiếp gói Wi-Fi: số thứ tự gói, mất gói, RTT, goodput. Đây là phần thực nghiệm gói tin, không phải phép đo NOMA/SIC, AF hay full-duplex cùng tần số ở tầng vô tuyến.

Có thể thêm khảo sát giới hạn công suất phát bằng API esp_wifi_set_max_tx_power. API đặt giới hạn công suất, không cung cấp điện năng thực đo: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/network/esp_wifi.html#_CPPv425esp_wifi_set_max_tx_power6int8_t.

Nếu chưa có thiết bị đo dòng/công suất, chỉ ghi năng lượng ước tính theo mô hình và nguồn tham số. Không suy ra bit/J thực đo từ RSSI hoặc mức công suất phát cấu hình. Không lấy điện năng board ESP32 làm số đo trực tiếp cho phần cứng AF giả định.

Mốc hoàn thành hợp lý: mô hình và một công thức được kiểm chứng; ba chế độ relay có đối chứng công bằng; một mở rộng năng lượng/QoS; một demo Wi-Fi có log. Không có kết quả cải thiện hiệu năng hay đo phần cứng nào được khẳng định trong lần đọc bài này.
