# Báo cáo bonus — FPT 2025

## Tài liệu, index và nguồn

Tài liệu: FPT Báo cáo thường niên 2025 — Làm chủ công nghệ chiến lược. PDF có 232 trang vật lý, index đủ 232 trang; không có trang bị bỏ. SHA256: `9449a7251d126b635988974dbc72c2773c7fff39f4e5e858b5f7d3928b4e0e6c`. Nguồn: https://fpt.com/vi/tin-tuc/fpt-cong-bo-bao-cao-thuong-nien-2025. PDF người dùng cung cấp được giữ local, không khẳng định giấy phép mở và không đưa bản PDF/ảnh đầy đủ vào ZIP nộp.

PDFium trích body text bỏ sidebar lặp từ trang 3, ảnh nguyên trang 1600px giữ cả sơ đồ và bảng. GPT-4.1-mini mô tả trực quan mọi trang; text + caption dùng embedding thật, Qdrant cosine/RRF kết hợp dense và lexical. Mọi trang đều tham gia index, kể cả bìa/trang ít text qua caption; không chỉ index gold pages. Model trả lời cấu hình vision nhìn ảnh gốc được retrieval chọn; gold không tham gia tool/query/ảnh đầu vào.

Giới hạn extraction: sidebar bị bỏ trong text nhưng còn ở ảnh; text bảng có thể bị dàn phẳng theo cột; caption là AI, không tự bảo đảm đúng. Cần dùng bản gốc để chấm, đặc biệt hàng/cột/đơn vị và nhãn chữ xoay. Schema evidence gồm page/region/bbox/image hash; bảng ghi hàng/cột, biểu đồ ghi nhãn/chú giải, multi-hop giữ nhiều nguồn bắt buộc và phép tính nếu có.

## Dev và lựa chọn

| Cấu hình | Đạt / tổng dev | Lỗi hệ thống | Median ms | Chat USD |
|---|---|---:|---:|---:|
| text | 14/18 | 0 | 22315.4 | 0.05285320 |
| vision | 15/18 | 0 | 8966.5 | 0.06658480 |

Text dùng openai/gpt-4.1-mini, top-k4, tối đa 6 trang context, không ảnh gốc. Vision dùng anthropic/claude-haiku-5.5, thinking tắt, top-k8, tối đa 12 trang, có ảnh gốc, tối đa 3 lượt search. Đây là thay đổi kết hợp model/context/ảnh, không phải ablation chỉ một yếu tố. Mỗi trang context tối đa 3200 ký tự + visual descriptors và ảnh khi bật vision; token thực tế lưu usage.

Lỗi dev đã đọc và thử lại: text dàn phẳng đọc EBITDA thay lợi nhuận hoạt động; mini vision đọc nhãn xoay sai; câu đối chiếu bảng/sơ đồ chỉ dẫn một nguồn; số kế hoạch bị gọi là thực tế. Sửa giao thức bắt buộc tool trước; sau đó thử model vision mạnh hơn với yêu cầu trả lời ngắn, giữ nhãn đúng và kiểm đủ nguồn/plan-actual. Các lượt pilot được giữ tại results/bonus/history, kể cả chi phí và lỗi, không ghi đè. Tất cả diễn ra trước test.

Chốt vision tại 2026-11-16T04:56:55.330463+00:00.

Đã sửa gold fd-i3 (năm nhãn vòng FleziPT) và ft-c5 (văn bản cứng màu cam cao nhất 2022=92,9%) bằng ảnh gốc trước khi chạy bất kỳ test bonus nào. Giữ benchmark cũ và lý do trong history/pretest-chart-gold-correction. Dev không đổi khi sửa ft-c5. Model không nhận gold khi chạy.

Tái sử dụng 18 câu text với cùng model/config/source/câu hỏi. Vision Haiku chạy mới toàn bộ 18 dev; không gắn điểm GPT-4.1 cho Haiku. Mọi nhãn giữ AI/student_confirmed=false. Lỗi HTTP 402/mạng lịch sử và chi phí pilot được giữ, không sửa trace cũ. Chi tiết lỗi dev hiện tại ở reviews.json; không chỉnh pipeline theo test.

Tiêu chí lựa chọn: số dev đạt cao hơn, rồi chi phí chat, latency, tên cấu hình. Chỉ chốt sau khi đủ dev và nhãn; test chỉ chạy sau chốt.

## Toàn bộ test

Kết quả: 27/30 (90.00%), lỗi hệ thống 0.

Ngưỡng bonus: ít nhất 27/30 test đạt, không làm tròn; mẫu số gồm cả lỗi/timeout.

| Nhóm | Đạt / tổng | Tỷ lệ |
|---|---|---:|
| chart | 5/5 | 100.0% |
| diagram | 3/5 | 60.0% |
| multi_hop | 4/4 | 100.0% |
| table | 5/6 | 83.3% |
| unanswerable | 6/6 | 100.0% |
| text | 4/4 | 100.0% |

## Chi phí lượt Haiku mới

18 dev: 0.06658480 USD. Test gồm chat và embedding query: 0.11598728 USD. Tổng mới **0.18257208 USD**, 97 chat request, 10 đợt. Không caption/embedding document lại. Chi phí lịch sử công bố riêng trong results/cost_summary.json, không nhập nhằng với tổng mới.

Chi tiết giá/dự toán so với thực tế: [MODEL_COST.md](MODEL_COST.md). Sau khi đủ 30 câu đã dừng API. Kết quả 27/30 là nhãn AI hỗ trợ đọc nguồn, chưa có học viên xác nhận/chấm độc lập; không tự coi là quyết định cộng điểm của giảng viên.

## Kiểm chứng từng câu

Nhãn dưới đây do Codex AI đọc câu trả lời/citation và đối chiếu trang gốc; không tự gọi là human audit hoặc xác nhận của học viên. Ảnh/trang tham chiếu được xác định bằng hash nguồn; giữ raw model response/tool/context/usage trong JSON. Người chấm có thể mở đúng trang/vùng trong PDF gốc.

### ft-c1 — Đạt

Trên đường ROA trong biểu đồ 2021–2025, mức cao nhất thuộc năm nào và năm 2025 giảm bao nhiêu điểm phần trăm so với năm 2024?

Trên biểu đồ đường ROA (trang 10 báo cáo, PDF trang 11), mức cao nhất là năm 2024 với 14,4%. Năm 2025 ROA là 14,1%, giảm 0,3 điểm phần trăm so với năm 2024 (14,4% − 14,1% = 0,3).
[FPT2025:p011 — Biểu đồ đường tỷ suất sinh lời ROE và ROA (góc dưới trái), dòng ROA (%) màu cam, các nhãn 2021–2025: 11,4%; 11,9%; 13,6%; 14,4%; 14,1%]

Lý do: Đúng ROA cao nhất 2024=14,4%, 2025=14,1%, giảm 0,3 điểm phần trăm; trích đúng đường màu cam.

Đối chiếu ảnh gốc: [{'page': 11, 'region': 'Bản đồ/đường/cột/thanh, nhãn và chú giải đã đối chiếu', 'image_sha256': '0e19afde5701cc691aa07845a514fe44bf075429b988a293296783a37d60fdc0'}]

Trace: results/bonus/test/vision/queries/ft-c1.json

### ft-c2 — Đạt

Trong biểu đồ doanh thu Dịch vụ CNTT cho thị trường nước ngoài theo khu vực, thị trường nào lớn nhất năm 2025, giá trị và tỷ trọng bao nhiêu?

Năm 2025, thị trường Nhật Bản là lớn nhất trong biểu đồ doanh thu Dịch vụ CNTT cho thị trường nước ngoài theo khu vực: 15.452 tỷ VNĐ, chiếm 43,7% trên tổng 35.382 tỷ VNĐ (tăng 25,4% so với năm trước). Theo ảnh gốc trang 62, các khu vực còn lại là Mỹ 8.163 tỷ VNĐ (23,1%), Châu Á-Thái Bình Dương 8.173 tỷ VNĐ (23,1%), Châu Âu 3.593 tỷ VNĐ (10,2%).
[FPT2025:p062 — Biểu đồ vòng "Doanh thu lĩnh vực dịch vụ CNTT cho thị trường nước ngoài" (bên phải trang), nhãn Nhật Bản 15.452 tỷ VNĐ, 43,7%, tăng 25,4%; tổng 35.382 tỷ VNĐ]

Lý do: Đúng Nhật Bản 15.452 tỷ VNĐ, 43,7%, tổng 35.382; các số khu vực bổ sung và 25,4% tăng trưởng đều có trên hình.

Đối chiếu ảnh gốc: [{'page': 62, 'region': 'Bản đồ/đường/cột/thanh, nhãn và chú giải đã đối chiếu', 'image_sha256': '8f61bfe49d08bcb6a87539042593d27af6b5f49a23a6d00560e0d381aaf97041'}]

Trace: results/bonus/test/vision/queries/ft-c2.json

### ft-c3 — Đạt

Đọc các cột màu xanh của biểu đồ doanh thu Dịch vụ Chuyển đổi số: giá trị năm 2024 và 2025 là bao nhiêu và tăng thêm bao nhiêu?

Biểu đồ "Doanh thu Dịch vụ Chuyển đổi số giai đoạn 2021-2025" (trang 62, PDF trang 63) có cột xanh dương (Doanh thu dịch vụ Chuyển đổi số): năm 2024 là 14.340 tỷ VNĐ; năm 2025 là 16.751 tỷ VNĐ.
Mức tăng: 16.751 − 14.340 = 2.411 tỷ VNĐ (tương ứng +16,8%, khớp với văn bản báo cáo).
[FPT2025:p063 — Biểu đồ cột "Doanh thu Dịch vụ Chuyển đổi số giai đoạn 2021-2025" (bên trái trang), các cột màu xanh dương (Doanh thu dịch vụ Chuyển đổi số), nhãn 2024 = 14.340 và 2025 = 16.751, đơn vị Tỷ VNĐ]

Lý do: Đúng hai cột xanh 14.340 và 16.751 tỷ VNĐ, chênh 2.411; 16,8% khớp phần văn bản trên biểu đồ.

Đối chiếu ảnh gốc: [{'page': 63, 'region': 'Bản đồ/đường/cột/thanh, nhãn và chú giải đã đối chiếu', 'image_sha256': '3833275b32129e130f798941edeaa494b184bc733edcee714d1b3ca1b29ca716'}]

Trace: results/bonus/test/vision/queries/ft-c3.json

### ft-c4 — Đạt

Theo biểu đồ họp trực tuyến/trực tiếp 2023–2025, tỷ lệ họp trực tuyến từ năm 2023 đến 2025 tăng bao nhiêu điểm phần trăm?

Theo biểu đồ "Tỷ lệ các cuộc họp trực tuyến và trực tiếp giai đoạn 2023-2025" (trang 152 của báo cáo, PDF 152): tỷ lệ họp trực tuyến năm 2023 là 67,8%, năm 2025 là 94,0%. Mức tăng = 94,0% − 67,8% = 26,2 điểm phần trăm.
[FPT2025:p152 — Biểu đồ thanh ngang 'Tỷ lệ các cuộc họp trực tuyến và trực tiếp giai đoạn 2023-2025' (phía dưới bên phải), hàng 2023 (họp trực tuyến 67,8%) và hàng 2025 (họp trực tuyến 94,0%), chú giải màu xanh là Họp trực tuyến]

Lý do: Đúng online 67,8% năm 2023 và 94,0% năm 2025, tăng 26,2 điểm phần trăm; chú giải và citation phù hợp.

Đối chiếu ảnh gốc: [{'page': 152, 'region': 'Bản đồ/đường/cột/thanh, nhãn và chú giải đã đối chiếu', 'image_sha256': '10b7f4e8034cca5de28a2bee685a6e23ad93e4ea7c4ed8759544c7c658e57b90'}]

Trace: results/bonus/test/vision/queries/ft-c4.json

### ft-c5 — Đạt

Trong biểu đồ số hóa tài liệu 2022–2025, tỷ lệ văn bản cứng cao nhất ở năm nào và tỷ lệ văn bản cứng năm 2025 là bao nhiêu?

Theo biểu đồ "Tỷ lệ số hoá tài liệu giai đoạn 2022-2025" (trang 152), tỷ lệ văn bản cứng cao nhất là năm 2022 với 92,9% (tỷ lệ văn bản phát hành điện tử là 7,1%). Tỷ lệ văn bản cứng năm 2025 là 4,58% (tỷ lệ phát hành điện tử 95,42%).
[FPT2025:p152 — Biểu đồ cột "Tỷ lệ số hoá tài liệu giai đoạn 2022-2025" (dưới bên trái), nhãn tỷ lệ văn bản cứng (màu cam) các năm 2022 = 92,9%, 2025 = 4,58%]

Lý do: Đúng văn bản cứng màu cam cao nhất 2022=92,9%, năm 2025=4,58%; hai tỷ lệ điện tử bổ sung 7,1/95,42 đúng. Gold đã được sửa bằng ảnh gốc trước bất kỳ test nào, không sửa theo output này.

Đối chiếu ảnh gốc: [{'page': 152, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': '10b7f4e8034cca5de28a2bee685a6e23ad93e4ea7c4ed8759544c7c658e57b90'}]

Trace: results/bonus/test/vision/queries/ft-c5.json

### ft-i1 — Đạt

Theo sơ đồ tổ chức, hai đơn vị nào nằm trong nhánh Công ty liên kết?

Theo sơ đồ tổ chức (trang 31), nhánh "CÔNG TY LIÊN KẾT" được nối với hai đơn vị: Synnex FPT (vốn điều lệ 1.188.400.000.000 VNĐ, tỷ lệ sở hữu 48,00%) và FPT Retail (vốn điều lệ 1.703.017.850.000 VNĐ, tỷ lệ sở hữu 46,54%).
[FPT2025:p031 — Sơ đồ tổ chức (trang 31): nhánh từ ô CÔNG TY LIÊN KẾT nối tới hai đơn vị ở cột bên phải dưới – Synnex FPT (48,00%) và FPT Retail (46,54%), kèm vốn điều lệ và tỷ lệ sở hữu tương ứng]

Lý do: Đúng Synnex FPT và FPT Retail trong nhánh liên kết; vốn điều lệ/tỷ lệ bổ sung đều khớp ảnh.

Đối chiếu ảnh gốc: [{'page': 31, 'region': 'Bảng hoặc nhánh/lớp/đường nối sơ đồ được hỏi và được trích', 'image_sha256': '4783edc630633806a16232560a0b8de0c6ca6f7c5f9aa143a1b14b37b154b2c3'}]

Trace: results/bonus/test/vision/queries/ft-i1.json

### ft-i2 — Không đạt

Theo các đường nối trong sơ đồ tổ chức, Khối Viễn thông gồm những đơn vị nào?

Theo sơ đồ tổ chức (trang 31, trang PDF 31), Khối Viễn thông được nối bằng đường nét đứt tới 3 đơn vị: FPT Online (vốn điều lệ 184.712.750.000 VNĐ, tỷ lệ sở hữu 49,52%), FPT Telecom (vốn điều lệ 7.387.634.630.000 VNĐ, tỷ lệ sở hữu 45,66%). Lưu ý: FPT Retail và Synnex FPT nằm ở nhánh công ty liên kết/nối với Tập đoàn, không thuộc Khối Viễn thông theo sơ đồ. Hai đơn vị Khối Viễn thông là FPT Online và FPT Telecom.
[FPT2025:p031 — Sơ đồ tổ chức (vùng phải trang), nhánh nối từ nhãn KHỐI VIỄN THÔNG bằng đường nét đứt tới các ô FPT Online và FPT Telecom, kèm thông tin vốn điều lệ và tỷ lệ sở hữu]

Lý do: Nêu đúng hai tên và cuối câu nói hai đơn vị, nhưng đầu câu khẳng định có 3 đơn vị; sơ đồ chỉ có hai, trả lời mâu thuẫn và thêm số không được nguồn hỗ trợ.

Đối chiếu ảnh gốc: [{'page': 31, 'region': 'Bảng hoặc nhánh/lớp/đường nối sơ đồ được hỏi và được trích', 'image_sha256': '4783edc630633806a16232560a0b8de0c6ca6f7c5f9aa143a1b14b37b154b2c3'}]

Trace: results/bonus/test/vision/queries/ft-i2.json

### ft-i3 — Đạt

Đọc sơ đồ tròn FleziPT: ba lớp có tên viết hoa được xếp từ tâm ra ngoài theo thứ tự nào?

Trang 63 (ảnh gốc trang PDF 62) có sơ đồ tròn FleziPT. Ba lớp có tên viết hoa, từ tâm ra ngoài: FLEZI FOUNDATION (trung tâm), FLEZI CREW (lớp giữa), FLEZI VERSE (lớp ngoài cùng).
[FPT2025:p063 — Sơ đồ vòng tròn "Nền tảng AI linh hoạt FleziPT" ở phía phải trang (trang PDF 63, hiển thị số trang 62): lớp trung tâm FLEZI FOUNDATION, lớp giữa FLEZI CREW, lớp ngoài cùng FLEZI VERSE]

Lý do: Đúng thứ tự ba lớp Foundation → Crew → Verse. Prose ban đầu trộn số trang in 62 với PDF; structured citation p063 ghi rõ PDF63/in62 và vùng hình, định vị evidence đúng.

Đối chiếu ảnh gốc: [{'page': 63, 'region': 'Bảng hoặc nhánh/lớp/đường nối sơ đồ được hỏi và được trích', 'image_sha256': '3833275b32129e130f798941edeaa494b184bc733edcee714d1b3ca1b29ca716'}]

Trace: results/bonus/test/vision/queries/ft-i3.json

### ft-i4 — Đạt

Trong hình quy trình xác định vấn đề trọng yếu ESG, ba bước được sắp theo thứ tự nào?

Theo sơ đồ "Quy trình xác định các vấn đề trọng yếu" ở vùng bên phải trang 125, ba bước được sắp theo thứ tự: Bước 01 – Xác định các vấn đề chính có ảnh hưởng lớn đến hoạt động kinh doanh của Tập đoàn và lợi ích của các bên liên quan; Bước 02 – Phân tích và xác định các vấn đề trọng yếu được các bên quan tâm; Bước 03 – Phân tích các vấn đề trọng yếu trong mối quan hệ với các bên liên quan.
[FPT2025:p125 — Vùng bên phải trang 125, cột "Quy trình xác định các vấn đề trọng yếu", gồm ba khối Bước 01, Bước 02, Bước 03 theo thứ tự từ trên xuống]

Lý do: Đúng đủ thứ tự và nội dung ba bước, citation đúng cột quy trình bên phải.

Đối chiếu ảnh gốc: [{'page': 125, 'region': 'Bảng hoặc nhánh/lớp/đường nối sơ đồ được hỏi và được trích', 'image_sha256': 'c4806555bbc90204da4b4a323a9b36c0b276dd92e70136d33a883613aabdcf1a'}]

Trace: results/bonus/test/vision/queries/ft-i4.json

### ft-i5 — Không đạt

Trên bản đồ hiện diện toàn cầu của FPT, Nhật Bản và Úc có được gắn nhãn địa điểm hiện diện không?

Có, nhưng chỉ gắn nhãn Nhật Bản và Úc. Trên bản đồ hiện diện toàn cầu (trang 27), các nhãn "Nhật Bản" (gần Hàn Quốc, phía đông) và "Úc" (phía dưới bên trái bản đồ châu Á–Thái Bình Dương) đều có ghim vị trí. Ngoài ra, trang 27 có nhãn quốc gia "Nhật Bản" trong phần danh sách các quốc gia/vùng lãnh thổ được liệt kê.
[FPT2025:p027 — Bản đồ phạm vi hoạt động toàn cầu ở giữa trang: ghim và nhãn "Nhật Bản" (phía đông, cạnh Hàn Quốc) và ghim, nhãn "Úc" (phía dưới bên phải, châu Úc)]

Lý do: Có nêu đúng cả Nhật Bản và Úc, nhưng thêm khẳng định chỉ gắn nhãn hai nước và mô tả Úc ở phía dưới bên trái; bản đồ còn nhiều nhãn khác và Úc ở phía dưới bên phải. Câu trả lời/citation tự mâu thuẫn vị trí nên chưa đạt toàn bộ được hỗ trợ.

Đối chiếu ảnh gốc: [{'page': 27, 'region': 'Bản đồ/đường/cột/thanh, nhãn và chú giải đã đối chiếu', 'image_sha256': '95e6ebcbc57b8fb739f6a2f6b5d6e87612f28ba4555bb9e12ed8c741ae37226d'}]

Trace: results/bonus/test/vision/queries/ft-i5.json

### ft-m1 — Đạt

Đối chiếu bảng chỉ tiêu kinh doanh toàn Tập đoàn với biểu đồ doanh thu Chuyển đổi số: năm 2025 hai giá trị LNTT và doanh thu Chuyển đổi số là bao nhiêu, chênh lệch số học bao nhiêu tỷ VNĐ?

Năm 2025: LNTT toàn Tập đoàn = 13.044 tỷ VNĐ (bảng chỉ tiêu, trang 58). Doanh thu Dịch vụ Chuyển đổi số = 16.751 tỷ VNĐ (biểu đồ, trang 63). Chênh lệch số học = 13.044 − 16.751 = −3.707 tỷ VNĐ (doanh thu Chuyển đổi số cao hơn LNTT 3.707 tỷ VNĐ). Lưu ý: hai chỉ tiêu thuộc hai phạm vi khác nhau (LNTT toàn Tập đoàn và doanh thu một mảng), nên phép so sánh chỉ mang tính số học.
[FPT2025:p058 — Bảng 'Một số chỉ tiêu hoạt động kinh doanh chính trong năm 2025', cột 2025, hàng LNTT = 13.044 (tỷ VNĐ)] [FPT2025:p063 — Biểu đồ cột 'Doanh thu Dịch vụ Chuyển đổi số giai đoạn 2021-2025' (trái), cột 2025 của doanh thu dịch vụ Chuyển đổi số (màu xanh) = 16.751 (tỷ VNĐ)]

Lý do: Đủ LNTT 13.044 và doanh thu DX 16.751 tỷ VNĐ, phép trừ -3.707 và giải thích chiều chênh lệch đúng; phân biệt hai chỉ tiêu, citation đủ hai nguồn.

Đối chiếu ảnh gốc: [{'page': 58, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': '519a9443321dba6592b6a8cc047f6aa73dcdbdd1f503bf311ef7eb3355730b27'}, {'page': 63, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': '3833275b32129e130f798941edeaa494b184bc733edcee714d1b3ca1b29ca716'}]

Trace: results/bonus/test/vision/queries/ft-m1.json

### ft-m2 — Đạt

So sánh ngân sách đầu tư Khối Công nghệ trong kế hoạch 2026 với số giải ngân Khối Công nghệ năm 2025: mỗi số là bao nhiêu và chênh lệch bao nhiêu tỷ VNĐ?

Kế hoạch đầu tư Khối Công nghệ năm 2026 là 4.200 tỷ VNĐ; giải ngân Khối Công nghệ năm 2025 là 2.823 tỷ VNĐ. Chênh lệch: 4.200 − 2.823 = 1.377 tỷ VNĐ (kế hoạch 2026 cao hơn giải ngân 2025 khoảng 1.377 tỷ VNĐ). Lưu ý: 4.200 là ngân sách đầu tư dự kiến 2026, không phải số thực tế.
[FPT2025:p055 — Bảng "Kế hoạch đầu tư dự kiến" (dưới), hàng Khối Công nghệ, cột Ngân sách đầu tư = 4.200 tỷ VNĐ] [FPT2025:p075 — Bảng "Tình hình thực hiện các dự án đầu tư" (trái trên), hàng Công nghệ, cột Giải ngân 2025 = 2.823 tỷ VNĐ]

Lý do: Đủ kế hoạch 2026=4.200 và giải ngân 2025=2.823 tỷ VNĐ; chênh 1.377, phân biệt kế hoạch/thực tế, trích cả hai bảng.

Đối chiếu ảnh gốc: [{'page': 55, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': '4ea10a7096459338737e8bc33afe27fee1effead69bb73acac0e54bd5b3ea1ef'}, {'page': 75, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': 'c32c818447bb70184214d41bbc53e019ac8c07565b5647db7eb15b4e8c7a228e'}]

Trace: results/bonus/test/vision/queries/ft-m2.json

### ft-m3 — Đạt

Kết hợp phần văn phòng không giấy tờ và phần kiểm kê khí nhà kính: tỷ lệ paperless năm 2025 và mốc mục tiêu Net Zero là gì? Tỷ lệ paperless có đồng nghĩa đã đạt Net Zero không?

Tỷ lệ paperless năm 2025 của FPT đạt 95,42%, và hợp đồng giao dịch điện tử chiếm khoảng 97% tổng số hợp đồng ký kết. Mục tiêu Net Zero (phát thải ròng bằng 0) được đặt vào năm 2040, với mốc trung hạn giảm 15,8% tổng lượng phát thải khí nhà kính đến năm 2030.

Tỷ lệ paperless KHÔNG đồng nghĩa đã đạt Net Zero. Paperless chỉ là tỷ lệ văn bản điện tử trong quản trị nội bộ; còn Net Zero là mục tiêu dài hạn đến 2040. Năm 2025, tổng phát thải khí nhà kính của FPT là 127.952 tấn CO2 (giảm so với 143.574 tấn năm 2024), nhưng đây chỉ là giảm phát thải, chưa phải trung hòa ròng bằng 0.
[FPT2025:p152 — Mục 'Văn phòng không giấy tờ', đoạn văn nêu tỷ lệ paperless 95,42% và hợp đồng điện tử ~97%; biểu đồ 'Tỷ lệ số hoá tài liệu giai đoạn 2022-2025' (dưới bên trái) cột 2025 với 95,42%] [FPT2025:p114 — Phần 'Lộ trình Net Zero 2040' (đầu trang), khung nổi bật: mục tiêu giảm 15,8% phát thải đến 2030 và Net Zero vào năm 2040] [FPT2025:p146 — Bảng 'Tổng hợp lượng phát thải khí nhà kính của FPT năm 2025' (bên phải), hàng Tổng: 143.574 (2024) và 127.952 (2025), đơn vị tấn CO2 tương đương]

Lý do: Đúng paperless 95,42%, mục tiêu Net Zero 2040 và không đồng nghĩa đạt Net Zero. Chi tiết bổ sung ~97% hợp đồng điện tử, mục tiêu giảm 15,8% đến 2030, tổng CO2 127.952/143.574 đều được các citation tương ứng hỗ trợ.

Đối chiếu ảnh gốc: [{'page': 114, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': 'e82df822ac7f11d3dd95502a689b7b79fd82f37729f2b4bc664a0459fd91a1b9'}, {'page': 146, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': 'b2c7e766c2de5a39783a7e9bf4ba6edce5ee721ff74ed71d14df2c16d4781ef6'}, {'page': 152, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': '10b7f4e8034cca5de28a2bee685a6e23ad93e4ea7c4ed8759544c7c658e57b90'}]

Trace: results/bonus/test/vision/queries/ft-m3.json

### ft-m4 — Đạt

Tổng hợp đối tượng và quy mô hưởng lợi của Trường Hy Vọng mới và dự án Bếp Xanh – Sống Lành: số nào là học sinh, số nào là người dân?

Trường Hy Vọng mới: hơn 300 học sinh thuộc 13 dân tộc (đối tượng là học sinh; quy mô trường rộng 6.500 m²). Dự án Bếp Xanh – Sống Lành: hơn 1.000 người dân tiếp cận giải pháp bếp cải tiến (đối tượng là người dân; không có số học sinh). Tổng hợp: học sinh = hơn 300 (Trường Hy Vọng); người dân = hơn 1.000 (Bếp Xanh – Sống Lành).
[FPT2025:p156 — Mục "Trường Hy Vọng – Hành trình nảy mầm", đoạn văn bên trái dưới ảnh (câu nêu hơn 300 học sinh thuộc 13 dân tộc, trường rộng 6.500 m²)] [FPT2025:p158 — Mục "Dự án 'Bếp Xanh – Sống Lành', mang sức khỏe đến với mọi nhà", đoạn văn bên trái dưới ảnh (câu nêu dự án giúp hơn 1.000 người dân tiếp cận giải pháp bếp cải tiến)]

Lý do: Đúng hơn 300 học sinh/13 dân tộc và hơn 1.000 người dân; 6.500 m² ở trang 156 cũng đúng. Phân biệt đối tượng, citation đầy đủ hai nguồn.

Đối chiếu ảnh gốc: [{'page': 156, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': 'a76cc7d64685f9b3118517deee6a418374db0dc7b519c3659d62f09ae0179d85'}, {'page': 158, 'region': 'Các ô/nhãn/đoạn và nguồn bổ sung được trích trong câu trả lời', 'image_sha256': '9accc73d22e2e6a849d356ec4bb82caf4ed1ed3ae163453a1e41b3db5e893869'}]

Trace: results/bonus/test/vision/queries/ft-m4.json

### ft-t1 — Đạt

Trong bảng tài chính giai đoạn 2021–2025, tổng tài sản và vốn chủ sở hữu cuối năm 2025 lần lượt là bao nhiêu? Ghi đúng đơn vị.

Cuối năm 2025: Tổng tài sản là 88.142 tỷ VNĐ (bảng tài chính 2021–2025, trang 12); Vốn chủ sở hữu là 43.748 tỷ VNĐ (cùng bảng). Đối chiếu: Bảng cân đối kế toán hợp nhất cho thấy vốn chủ sở hữu (mã 400) 43.748.040.747.539 VNĐ và tổng nguồn vốn 88.141.991.634.625 VNĐ, tương đương khoảng 43.748 tỷ VNĐ và 88.142 tỷ VNĐ.
[FPT2025:p012 — Bảng 'Tình hình tài chính và kết quả kinh doanh nổi bật giai đoạn 2021-2025', hàng 'Vốn chủ sở hữu' (STT 1) và 'Tổng tài sản' (STT 2), cột 2025; đơn vị Tỷ VNĐ] [FPT2025:p168 — Bảng cân đối kế toán hợp nhất (tiếp theo), mã số 400 'VỐN CHỦ SỞ HỮU' và mã số 440 'TỔNG NGUỒN VỐN', cột 2025; đơn vị VNĐ]

Lý do: Đúng tổng tài sản 88.142 và vốn chủ sở hữu 43.748 tỷ VNĐ. Số VNĐ gốc được dẫn bổ sung khớp mã 400/440 trang 168.

Đối chiếu ảnh gốc: [{'page': 12, 'region': 'Hàng/cột, ghi chú đơn vị và citation được kiểm tra trong ảnh gốc', 'image_sha256': '768854b828f12f330bc3912c517234b0a8ce08c6646824e304f742a0b59b1185'}, {'page': 168, 'region': 'Hàng/cột, ghi chú đơn vị và citation được kiểm tra trong ảnh gốc', 'image_sha256': '71de502f1a73da904667814efb8eff7db0f57915bf7961e7000cc1f764198222'}]

Trace: results/bonus/test/vision/queries/ft-t1.json

### ft-t2 — Không đạt

Theo bảng chỉ tiêu kinh doanh, lãi cơ bản trên cổ phiếu năm 2024 và 2025 là bao nhiêu? Đơn vị của hàng này có giống đơn vị chung của bảng không?

Không đủ bằng chứng để trả lời.

Lý do: Từ chối câu có đáp án. Bảng nguồn nêu EPS 4.292/5.216 và ghi chú riêng VNĐ, khác đơn vị tỷ VNĐ chung.

Đối chiếu ảnh gốc: [{'page': 58, 'region': 'Hàng/cột, ghi chú đơn vị và citation được kiểm tra trong ảnh gốc', 'image_sha256': '519a9443321dba6592b6a8cc047f6aa73dcdbdd1f503bf311ef7eb3355730b27'}]

Trace: results/bonus/test/vision/queries/ft-t2.json

### ft-t3 — Đạt

Trong kế hoạch đầu tư dự kiến năm 2026, hai khối được phân bổ bao nhiêu vốn, tổng bao nhiêu và Khối Công nghệ chiếm bao nhiêu phần trăm tổng ngân sách?

Theo bảng "Kế hoạch đầu tư dự kiến năm 2026" (đơn vị: tỷ VNĐ):
- Khối Công nghệ: 4.200 tỷ VNĐ
- Khối Giáo dục, Đầu tư và Khác: 3.000 tỷ VNĐ
- Tổng cộng: 7.200 tỷ VNĐ

Khối Công nghệ chiếm 4.200 / 7.200 = 58,33% (làm tròn 58,33%) tổng ngân sách đầu tư dự kiến. Đây là kế hoạch, không phải số thực tế.
[FPT2025:p055 — Bảng "Kế hoạch đầu tư dự kiến" (phía dưới trang), cột Khối, Ngân sách đầu tư và hàng Tổng cộng]

Lý do: Đúng 4.200, 3.000, tổng 7.200 tỷ VNĐ, 58,33%; phân biệt đúng kế hoạch với số thực tế và citation đúng bảng.

Đối chiếu ảnh gốc: [{'page': 55, 'region': 'Hàng/cột, ghi chú đơn vị và citation được kiểm tra trong ảnh gốc', 'image_sha256': '4ea10a7096459338737e8bc33afe27fee1effead69bb73acac0e54bd5b3ea1ef'}]

Trace: results/bonus/test/vision/queries/ft-t3.json

### ft-t4 — Đạt

Dựa vào hàng Tổng doanh thu trong bảng 2021–2025, doanh thu tăng thêm bao nhiêu tỷ VNĐ từ năm 2021 đến năm 2025?

Doanh thu tăng thêm 70.113 − 35.657 = 34.456 tỷ VNĐ từ năm 2021 đến năm 2025 (từ 35.657 tỷ VNĐ lên 70.113 tỷ VNĐ). Dữ liệu này khớp với bảng "Tình hình tài chính và kết quả kinh doanh nổi bật giai đoạn 2021-2025" và biểu đồ "Tổng doanh thu" ở trang 10 (đơn vị: tỷ VNĐ).
[FPT2025:p010 — Biểu đồ "Tổng doanh thu" (góc trên bên trái), nhãn giá trị 2021: 35.657 và 2025: 70.113, đơn vị Tỷ VNĐ] [FPT2025:p012 — Bảng "Tình hình tài chính và kết quả kinh doanh nổi bật giai đoạn 2021-2025", hàng 3 "Tổng doanh thu", cột 2021 (35.657) và cột 2025 (70.113), đơn vị Tỷ VNĐ]

Lý do: Đúng đầu vào 35.657 và 70.113 tỷ VNĐ, chênh 34.456; cả biểu đồ trang 10 và hàng doanh thu trang 12 đều hỗ trợ.

Đối chiếu ảnh gốc: [{'page': 10, 'region': 'Hàng/cột, ghi chú đơn vị và citation được kiểm tra trong ảnh gốc', 'image_sha256': '60ad91364203c175cfe2b42cb788ecc5b80f7d5aaf2e2e6002797a50b570cff5'}, {'page': 12, 'region': 'Hàng/cột, ghi chú đơn vị và citation được kiểm tra trong ảnh gốc', 'image_sha256': '768854b828f12f330bc3912c517234b0a8ce08c6646824e304f742a0b59b1185'}]

Trace: results/bonus/test/vision/queries/ft-t4.json

### ft-t5 — Đạt

Theo bảng chỉ tiêu kinh doanh năm 2025, cổ tức tiền mặt trả trong năm là bao nhiêu, tăng bao nhiêu phần trăm so với năm trước?

Theo bảng "Một số chỉ tiêu hoạt động kinh doanh chính trong năm 2025" (trang 58 báo cáo, ảnh gốc PDF trang 58), cổ tức tiền mặt trả trong năm 2025 là 3.185 tỷ VNĐ, tăng 16,2% so với năm 2024 (2.741 tỷ VNĐ). Phép tính: (3.185 − 2.741) / 2.741 ≈ 16,20%.
[FPT2025:p058 — Bảng "Một số chỉ tiêu hoạt động kinh doanh chính trong năm 2025" (cột phải), hàng "Cổ tức tiền mặt trả trong năm", cột 2024, 2025 và Tăng/Giảm]

Lý do: Đúng 3.185 tỷ VNĐ và 16,2%, đầu vào 2.741 năm 2024; phép tính và citation đúng hàng cổ tức tiền mặt.

Đối chiếu ảnh gốc: [{'page': 58, 'region': 'Hàng/cột, ghi chú đơn vị và citation được kiểm tra trong ảnh gốc', 'image_sha256': '519a9443321dba6592b6a8cc047f6aa73dcdbdd1f503bf311ef7eb3355730b27'}]

Trace: results/bonus/test/vision/queries/ft-t5.json

### ft-t6 — Đạt

Trong bảng tổng hợp tiêu thụ điện, điện tiêu thụ năm 2025, điện từ năng lượng tái tạo và tỷ lệ tái tạo lần lượt là bao nhiêu?

Theo bảng "So sánh kết quả tiêu thụ điện" (trang 146 PDF / báo cáo trang 146, đơn vị kWh), năm 2025: điện tiêu thụ 187.453.013 kWh; điện từ năng lượng tái tạo 842.749 kWh; tỷ lệ điện tái tạo so với điện tiêu thụ 0,45%.
[FPT2025:p147 — Bảng "Bảng tổng hợp so sánh kết quả tiêu thụ điện" (phía dưới bên trái trang), hàng "Tiêu thụ điện" cột Năm 2025 = 187.453.013; hàng "Điện từ năng lượng tái tạo" cột Năm 2025 = 842.749; hàng "Tỷ lệ điện từ năng lượng tái tạo so với điện tiêu thụ" cột Năm 2025 = 0,45%]

Lý do: Đúng ba giá trị 187.453.013 kWh, 842.749 kWh, 0,45%. Prose trộn số trang in/PDF 146; structured citation p147 và vùng/hàng/cột đúng, đủ định vị nguồn gốc nên không coi là mất citation.

Đối chiếu ảnh gốc: [{'page': 147, 'region': 'Bảng hoặc nhánh/lớp/đường nối sơ đồ được hỏi và được trích', 'image_sha256': '86baf2d9bdcb79f14d07358320970151432a8889b5185018be413c2323d3f36c'}]

Trace: results/bonus/test/vision/queries/ft-t6.json

### ft-u1 — Đạt

Báo cáo có số doanh thu năm 2025 riêng của từng khách hàng thuộc nhóm FPT Software không? Hãy liệt kê đầy đủ từng khách hàng và doanh thu.

Không đủ bằng chứng để trả lời.

Lý do: Từ chối đúng: báo cáo có doanh thu khu vực/mảng và thông tin khách hàng tổng hợp, không có danh sách đầy đủ doanh thu riêng từng khách hàng FPT Software; giữ kiểm tra thiếu bằng chứng toàn tài liệu trong benchmark.

Đối chiếu ảnh gốc: [{'page': 62, 'region': 'Đoạn văn/nguyên tắc hoặc phần chủ đề liên quan đã đối chiếu', 'image_sha256': '8f61bfe49d08bcb6a87539042593d27af6b5f49a23a6d00560e0d381aaf97041'}]

Trace: results/bonus/test/vision/queries/ft-u1.json

### ft-u2 — Đạt

Theo báo cáo, nêu chi tiết lượng phát thải CO2 toàn Tập đoàn của từng tháng trong năm 2025.

Không đủ bằng chứng để trả lời.

Lý do: Từ chối đúng: nguồn có tổng theo năm/phạm vi, không có đầy đủ từng tháng; không nội suy chia đều từ tổng năm.

Đối chiếu ảnh gốc: [{'page': 146, 'region': 'Phần chủ đề liên quan và các số tổng hợp; kiểm tra vắng dữ liệu chi tiết theo benchmark', 'image_sha256': 'b2c7e766c2de5a39783a7e9bf4ba6edce5ee721ff74ed71d14df2c16d4781ef6'}]

Trace: results/bonus/test/vision/queries/ft-u2.json

### ft-u3 — Đạt

Từ báo cáo, số serial của từng GPU đang hoạt động tại hai nhà máy AI là gì?

Không đủ bằng chứng để trả lời.

Lý do: Từ chối đúng: không có danh mục serial từng GPU, nguồn chỉ có năng lực và quy mô nhà máy AI.

Đối chiếu ảnh gốc: [{'page': 5, 'region': 'Phần chủ đề liên quan và các số tổng hợp; kiểm tra vắng dữ liệu chi tiết theo benchmark', 'image_sha256': 'c66b4c57dc2491b91aa60eb5ac8fcf277b8d710b376240639db7dd80d8f334b5'}]

Trace: results/bonus/test/vision/queries/ft-u3.json

### ft-u4 — Đạt

Trong báo cáo có tỷ lệ chính xác lỗi suy luận của từng mô hình ngôn ngữ lớn do FPT AI Factory phát triển không? Nêu từng mô hình và tỷ lệ.

Không đủ bằng chứng để trả lời.

Lý do: Từ chối đúng: số mô hình/năng lực không phải benchmark tỷ lệ lỗi riêng từng LLM; không tạo số suy đoán.

Đối chiếu ảnh gốc: [{'page': 5, 'region': 'Phần chủ đề liên quan và các số tổng hợp; kiểm tra vắng dữ liệu chi tiết theo benchmark', 'image_sha256': 'c66b4c57dc2491b91aa60eb5ac8fcf277b8d710b376240639db7dd80d8f334b5'}]

Trace: results/bonus/test/vision/queries/ft-u4.json

### ft-u5 — Đạt

Báo cáo có bảng chi phí điện năm 2025 theo từng máy chủ riêng lẻ ở các Data Center không? Nêu đầy đủ.

Không. Báo cáo không có bảng chi phí điện năm 2025 theo từng máy chủ riêng lẻ ở các Data Center. Trang 147 (ESG) chỉ công bố tổng tiêu thụ điện của Tập đoàn: 187.453.013 kWh năm 2025 so với 205.053.314 kWh năm 2024 (-8,58%), cùng 842.749 kWh điện mặt trời từ hệ thống tại Data Center (Tp.Hồ Chí Minh) và F-Complex (Đà Nẵng). Báo cáo không nêu chi phí điện theo từng máy chủ hay từng Data Center.
[FPT2025:p147 — Bảng "Bảng tổng hợp so sánh kết quả tiêu thụ điện" (dưới bên trái) và đoạn văn về hệ thống điện mặt trời tại Data Center]

Lý do: Nêu rõ không có chi phí điện theo máy chủ/Data Center. Các số kWh tổng hợp 187.453.013, 205.053.314, -8,58%, 842.749 được nguồn hỗ trợ; không dùng chúng để suy ra chi phí từng máy chủ. Status answered vẫn đạt hành vi thiếu evidence theo ADVANCED.

Đối chiếu ảnh gốc: [{'page': 147, 'region': 'Phần chủ đề liên quan và các số tổng hợp; kiểm tra vắng dữ liệu chi tiết theo benchmark', 'image_sha256': '86baf2d9bdcb79f14d07358320970151432a8889b5185018be413c2323d3f36c'}]

Trace: results/bonus/test/vision/queries/ft-u5.json

### ft-u6 — Đạt

Báo cáo có lịch sử chính xác từng giao dịch mua cổ phiếu FPT của từng cổ đông cá nhân trong năm 2025 không? Liệt kê toàn bộ.

Không đủ bằng chứng để trả lời.

Lý do: Từ chối đúng: nguồn chỉ có cơ cấu và tổng cổ phiếu, không có lịch sử đầy đủ giao dịch từng cổ đông cá nhân.

Đối chiếu ảnh gốc: [{'page': 32, 'region': 'Phần chủ đề liên quan và các số tổng hợp; kiểm tra vắng dữ liệu chi tiết theo benchmark', 'image_sha256': 'c287642128097416c18dfcd119132d4ba068f3439767dbbf61daffb2d61cb320'}]

Trace: results/bonus/test/vision/queries/ft-u6.json

### ft-x1 — Đạt

Theo thông điệp Chủ tịch, sau một năm các nhà máy AI đã khai thác khoảng bao nhiêu công suất và xử lý bao nhiêu token?

Theo thông điệp Chủ tịch HĐQT (trang 4 của báo cáo), sau một năm vận hành hai nhà máy AI tại Việt Nam và Nhật Bản đã khai thác khoảng 70% công suất và xử lý hơn 1.100 tỷ token. Ngoài ra, các nhà máy này đã tinh chỉnh 70 mô hình AI theo nhu cầu khách hàng và phát triển 10 mô hình ngôn ngữ lớn từ FPT AI Factory.
[FPT2025:p005 — Đoạn văn cột trái, giữa trang (đoạn bắt đầu "Lợi thế riêng có thứ hai..."), câu "Chỉ sau một năm, các nhà máy này đã được khai thác khoảng 70% công suất, xử lý hơn 1.100 tỷ token..."]

Lý do: Đúng khoảng 70% và hơn 1.100 tỷ token; 70 mô hình tinh chỉnh/10 LLM bổ sung đều có trong đoạn gốc. Trang 4 trong prose là trang in; citation p005 định vị đúng PDF.

Đối chiếu ảnh gốc: [{'page': 5, 'region': 'Đoạn văn/nguyên tắc hoặc phần chủ đề liên quan đã đối chiếu', 'image_sha256': 'c66b4c57dc2491b91aa60eb5ac8fcf277b8d710b376240639db7dd80d8f334b5'}]

Trace: results/bonus/test/vision/queries/ft-x1.json

### ft-x2 — Đạt

Công trình nào được báo cáo nêu là đầu tiên tại Việt Nam đạt EDGE, và những giải pháp nào được nhắc kèm?

Công trình được nêu là đầu tiên tại Việt Nam đạt chứng chỉ EDGE là FPT Complex Đà Nẵng. Báo cáo nêu chứng chỉ này nhờ các giải pháp: tiết kiệm năng lượng, thu hồi nước mưa, xử lý nước thải và hệ thống điều hòa, chiếu sáng hiệu suất cao.
[FPT2025:p153 — Cột phải, khối chữ trong thẻ màu xanh lá (dưới cùng bên phải) ảnh FPT Complex Đà Nẵng, dòng: "FPT Complex Đà Nẵng là công trình đầu tiên tại Việt Nam đạt chứng chỉ EDGE nhờ các giải pháp tiết kiệm năng lượng, thu hồi nước mưa, xử lý nước thải và hệ thống điều hòa, chiếu sáng hiệu suất cao."]

Lý do: Đúng FPT Complex Đà Nẵng và đủ giải pháp tiết kiệm năng lượng, thu hồi mưa, xử lý thải, điều hòa/chiếu sáng hiệu suất cao; citation đúng thẻ xanh.

Đối chiếu ảnh gốc: [{'page': 153, 'region': 'Đoạn văn/nguyên tắc hoặc phần chủ đề liên quan đã đối chiếu', 'image_sha256': 'addb6e03cc0a5cec065cf834798a533646a74a69f4ce105479ee60a0a5c1ecdf'}]

Trace: results/bonus/test/vision/queries/ft-x2.json

### ft-x3 — Đạt

Theo nguyên tắc an ninh dữ liệu, khi cần tiết lộ thông tin bảo mật ra ngoài vì yêu cầu công việc, phải thực hiện gì trước?

Theo nguyên tắc an ninh dữ liệu, khi cần tiết lộ thông tin bảo mật ra bên ngoài Công ty vì yêu cầu công việc, phải thực hiện các biện pháp bảo vệ phù hợp trước, như ký kết cam kết bảo mật thông tin với các bên liên quan trước khi tiết lộ.
[FPT2025:p129 — Trang 129 (PDF 129), cột giữa: mục "Nguyên tắc an ninh", đoạn cuối mục nguyên tắc (sau "Không tiết lộ các thông tin bảo mật cho bất kỳ ai bên ngoài Công ty...")]

Lý do: Đúng phải áp dụng biện pháp bảo vệ phù hợp trước tiết lộ, ký cam kết là ví dụ; không biến ví dụ thành điều kiện duy nhất.

Đối chiếu ảnh gốc: [{'page': 129, 'region': 'Đoạn văn/nguyên tắc hoặc phần chủ đề liên quan đã đối chiếu', 'image_sha256': 'f2dc748fb6c972ec1416572ea92f85db8a905c2e8b4f19310f6881fa160df611'}]

Trace: results/bonus/test/vision/queries/ft-x3.json

### ft-x4 — Đạt

Báo cáo liệt kê những nguyên tắc nào cho việc thu thập, xử lý, lưu trữ và sử dụng dữ liệu?

Theo Báo cáo thường niên FPT 2025, hoạt động thu thập, xử lý, lưu trữ và sử dụng dữ liệu được tuân theo 5 nguyên tắc:
1. Nguyên tắc hợp pháp: mọi hoạt động trong hệ thống quản trị dữ liệu phải tuân thủ pháp luật.
2. Nguyên tắc mục đích: dữ liệu chỉ được sử dụng đúng mục đích hợp pháp đã được cấp có thẩm quyền phê duyệt.
3. Nguyên tắc chất lượng dữ liệu: dữ liệu phải sẵn có, toàn vẹn và phù hợp mục đích sử dụng trong suốt vòng đời.
4. Nguyên tắc an ninh: đảm bảo an toàn thông tin xuyên suốt; không tiết lộ thông tin bảo mật ra bên ngoài trừ trường hợp có biện pháp bảo vệ phù hợp (như ký cam kết bảo mật).
5. Nguyên tắc quản trị: dữ liệu khách hàng của các công ty thành viên được Tập đoàn thu thập, khai thác, sử dụng và lưu trữ tập trung nhằm điều chỉnh, cập nhật, bảo mật và cải tiến sản phẩm, dịch vụ.
[FPT2025:p129 — Cột giữa, mục "Phương pháp quản trị và nguyên tắc chung": danh sách các nguyên tắc (hợp pháp, mục đích, chất lượng dữ liệu, an ninh, quản trị)]

Lý do: Đúng đủ năm nguyên tắc hợp pháp, mục đích, chất lượng, an ninh, quản trị. Các phần giải thích đều ở mục nguyên tắc nguồn.

Đối chiếu ảnh gốc: [{'page': 129, 'region': 'Đoạn văn/nguyên tắc hoặc phần chủ đề liên quan đã đối chiếu', 'image_sha256': 'f2dc748fb6c972ec1416572ea92f85db8a905c2e8b4f19310f6881fa160df611'}]

Trace: results/bonus/test/vision/queries/ft-x4.json

## Giới hạn và tái lập

Xem BONUS_RUN.md. Kết quả là số đo trên benchmark do AI hỗ trợ thiết kế/chấm, không bảo đảm tổng quát. Chưa có xác nhận học viên hoặc chấm độc lập. Không phát sinh xác nhận giả. Để nhận bonus, giảng viên cần chấp nhận đủ nguồn/quyền/index/benchmark/evidence ngoài việc đạt tỷ lệ.
