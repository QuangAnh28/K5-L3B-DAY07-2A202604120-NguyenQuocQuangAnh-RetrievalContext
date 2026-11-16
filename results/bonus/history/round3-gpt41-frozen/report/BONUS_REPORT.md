# Báo cáo bonus — FPT 2025

## Tài liệu, index và nguồn

Tài liệu: FPT Báo cáo thường niên 2025 — Làm chủ công nghệ chiến lược. PDF có 232 trang vật lý, index đủ 232 trang; không có trang bị bỏ. SHA256: `9449a7251d126b635988974dbc72c2773c7fff39f4e5e858b5f7d3928b4e0e6c`. Nguồn: https://fpt.com/vi/tin-tuc/fpt-cong-bo-bao-cao-thuong-nien-2025. PDF người dùng cung cấp được giữ local, không khẳng định giấy phép mở và không đưa bản PDF/ảnh đầy đủ vào ZIP nộp.

PDFium trích body text bỏ sidebar lặp từ trang 3, ảnh nguyên trang 1600px giữ cả sơ đồ và bảng. GPT-4.1-mini mô tả trực quan mọi trang; text + caption dùng embedding thật, Qdrant cosine/RRF kết hợp dense và lexical. Mọi trang đều tham gia index, kể cả bìa/trang ít text qua caption; không chỉ index gold pages. Model trả lời cấu hình vision nhìn ảnh gốc được retrieval chọn; gold không tham gia tool/query/ảnh đầu vào.

Giới hạn extraction: sidebar bị bỏ trong text nhưng còn ở ảnh; text bảng có thể bị dàn phẳng theo cột; caption là AI, không tự bảo đảm đúng. Cần dùng bản gốc để chấm, đặc biệt hàng/cột/đơn vị và nhãn chữ xoay. Schema evidence gồm page/region/bbox/image hash; bảng ghi hàng/cột, biểu đồ ghi nhãn/chú giải, multi-hop giữ nhiều nguồn bắt buộc và phép tính nếu có.

## Dev và lựa chọn

| Cấu hình | Đạt / tổng dev | Lỗi hệ thống | Median ms | Chat USD |
|---|---|---:|---:|---:|
| text | 14/18 | 0 | 22315.4 | 0.05285320 |
| vision | 15/18 | 0 | 30367.1 | 0.89891400 |

Text dùng GPT-4.1-mini, top-k4, tối đa 6 trang context, không ảnh gốc. Vision dùng GPT-4.1, top-k8, tối đa 12 trang, có ảnh gốc, tối đa 3 lượt search. Đây là thay đổi kết hợp model/context/ảnh, không phải ablation chỉ một yếu tố. Mỗi trang context tối đa 3200 ký tự + visual descriptors và ảnh khi bật vision; token thực tế lưu usage.

Lỗi dev đã đọc và thử lại: text dàn phẳng đọc EBITDA thay lợi nhuận hoạt động; mini vision đọc nhãn xoay sai; câu đối chiếu bảng/sơ đồ chỉ dẫn một nguồn; số kế hoạch bị gọi là thực tế. Sửa giao thức bắt buộc tool trước; sau đó thử model vision mạnh hơn với yêu cầu trả lời ngắn, giữ nhãn đúng và kiểm đủ nguồn/plan-actual. Hai lượt pilot được giữ tại results/bonus/history, kể cả chi phí và lỗi, không ghi đè. Tất cả diễn ra trước test.

Chốt vision tại 2026-11-16T04:30:22.459987+00:00.

Đã sửa fd-i3 và giữ nguyên 30 câu test trước khi chạy test. Tái sử dụng 32 output dev có đầu vào/config/source không đổi; bốn query còn lại đã chạy sau khi người dùng yêu cầu. Bốn query hết 10 chat request, 0,16389 USD theo usage. Mọi nhãn giữ AI/student_confirmed=false. HTTP 402 và các lỗi mạng sandbox trước đó được giữ lịch sử, không sửa thành thành công. Các lượt thử lại có trace riêng.

Lỗi dev mới còn lại: text đọc sai hàng EBITDA và thay nhãn hình bằng diễn giải; vision đọc Nhân rộng hơn thành Mạnh mẽ hơn; cả hai trả thêm quan hệ nhánh Ban kiểm soát vào đường chính; câu đối chiếu sơ đồ/bảng chỉ dẫn bảng. Đã chốt pipeline sau đánh giá dev, chưa chỉnh theo test.

Tiêu chí lựa chọn: số dev đạt cao hơn, rồi chi phí chat, latency, tên cấu hình. Chỉ chốt sau khi đủ dev và nhãn; test chỉ chạy sau chốt.

## Toàn bộ test

**Chưa chạy 30 câu test; chưa có tỷ lệ test và chưa đủ điều kiện nhận bonus. Không gọi thêm API trong lượt hoàn tất offline.**

Ngưỡng bonus: ít nhất 27/30 test đạt, không làm tròn; mẫu số gồm cả lỗi/timeout.

| Nhóm | Đạt / tổng | Tỷ lệ |
|---|---|---:|

## Kiểm chứng từng câu

Nhãn dưới đây do Codex AI đọc câu trả lời/citation và đối chiếu trang gốc; không tự gọi là human audit hoặc xác nhận của học viên. Ảnh/trang tham chiếu được xác định bằng hash nguồn; giữ raw model response/tool/context/usage trong JSON. Người chấm có thể mở đúng trang/vùng trong PDF gốc.

## Giới hạn và tái lập

Xem BONUS_RUN.md. Kết quả là số đo trên benchmark do AI hỗ trợ thiết kế/chấm, không bảo đảm tổng quát. Chưa có xác nhận học viên hoặc chấm độc lập. Không phát sinh xác nhận giả. Để nhận bonus, giảng viên cần chấp nhận đủ nguồn/quyền/index/benchmark/evidence ngoài việc đạt tỷ lệ.
