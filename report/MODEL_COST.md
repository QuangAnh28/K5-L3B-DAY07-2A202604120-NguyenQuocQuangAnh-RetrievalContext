# Đổi model bonus và dự toán chi phí

Kiểm tra giá ngày **16/11/2026**. Đã chạy model theo yêu cầu người dùng; giữ đơn giá tham chiếu và dự toán ban đầu bên dưới. Vision dùng **Claude Haiku 5.5**, thinking tắt; text và phần cơ bản giữ GPT-4.1-mini. Caption/vector/ảnh đã tạo được dùng lại, không ingestion lại tài liệu.

## Đơn giá chuẩn

USD trên một triệu token; chưa tính giảm giá cache, khác biệt routing hoặc phí mua credit:

| Model | Input | Output | Nguồn |
|---|---:|---:|---|
| Haiku 5.5, prompt ≤100.000 token | 0,10 | 0,50 | [OpenRouter](https://openrouter.ai/anthropic/claude-haiku-5.5) |
| Haiku 5.5, prompt >100.000 token | 0,50 | 2,50 | [Anthropic](https://platform.claude.com/docs/en/models/haiku-5-5/overview) |
| GPT-4.1-mini | 0,40 | 1,60 | [OpenRouter](https://openrouter.ai/openai/gpt-4.1-mini) |
| GPT-4.1 | 2,00 | 8,00 | [OpenRouter](https://openrouter.ai/openai/gpt-4.1) |
| Sonnet 5.5 | 2,00 | 10,00 | [OpenRouter](https://openrouter.ai/anthropic/claude-sonnet-5.5) |

Ở bậc prompt ≤100.000 token, Haiku có đơn giá input/output thấp hơn Sonnet 20 lần; thấp hơn mini lần lượt 4 và 3,2 lần. Đây là so sánh **đơn giá**, không phải bảo đảm tổng hóa đơn giảm theo tỷ lệ đó. Mỗi model có tokenizer/cách tính ảnh, số lượt tìm và độ dài output khác nhau. Sonnet không phải lựa chọn giảm đơn giá so với GPT-4.1-mini; chất lượng Sonnet/Haiku trên benchmark này chưa được đo.

## Dự toán cho bài này

Đã chạy mới 18 câu vision dev, chấm/chốt, sau đó 30 câu test. 18 câu text dev dùng cache. Không có phí caption/embedding document mới; embedding query chưa có cache vẫn có phí riêng.

Lấy lượng token của **hai lượt vision dev đã lưu** làm hai kịch bản giả định, quy đổi đơn giá mới, không tính giảm giá cache:

| Model | 18 dev + 30 test, giả sử cùng lượng token/câu với lượt cũ |
|---|---:|
| Haiku 5.5, bậc ≤100.000 token/prompt | khoảng 0,12–0,16 USD |
| GPT-4.1-mini | khoảng 0,48–0,61 USD |
| Sonnet 5.5 | khoảng 2,41–3,05 USD |

Công thức: cộng (prompt_tokens × giá input + completion_tokens × giá output)/1.000.000 của 18 dev tham chiếu, rồi nhân 48/18. Hai tham chiếu: round1-mini-vision/dev/vision (548.623 input, 4.835 output) và round3-gpt41-frozen/dev/vision (437.033 input, 3.106 output). Số token cũ gồm prompt ảnh theo cách đếm của model cũ; **không phải token đã đo trên Haiku/Sonnet**. Phí thực tế có thể nằm ngoài khoảng dự toán.

Để lập kế hoạch có thể dự phòng **0,50 USD cho Haiku**, nhưng đây **không phải trần chi tiêu được cưỡng chế trong code**. Dự toán này được lập trước khi chạy; chi phí thực tế đã được cập nhật ở phần dưới. Nếu tiếp tục, nên chạy vài câu dev trước và xem usage thực tế; không tự chạy cả bộ khi chỉ đang yêu cầu báo giá. Không thể dùng dự toán để bảo đảm chất lượng; kết quả thực tế được ghi riêng bên dưới.

Dữ liệu giá máy đọc được: data/bonus/model_prices.json. `python scripts/bonus_cost_plan.py` chỉ đọc file/cache và cập nhật cost_plan.json, không gửi request model. Báo cáo cost_plan dùng riêng lượng token lượt GPT-4.1 để có thể tái lập con số quy đổi; bảng ở đây bổ sung cả lượt mini làm kịch bản thứ hai.

## Truy vết khi đổi model

Source/selection/dev/báo cáo GPT-4.1 trước đổi được giữ tại results/bonus/history/round3-gpt41-frozen. Model mới đã có selection chốt sau dev, trước test; fingerprint được kiểm tra khi chạy test. Không sửa test, không đổi nhãn hoặc giả kết quả model mới. Các tests offline kiểm tra định dạng payload không thay thế kiểm tra API tương thích/thành công thực tế.

## Chi phí và kết quả thực tế sau khi chạy

- 18 dev Haiku: **0,06658480 USD** chat, kết quả 15/18.
- 30 test Haiku: **0,11595110 USD** chat + **0,00003618 USD** embedding query, tổng **0,11598728 USD**.
- Tổng mới: **0,18257208 USD**, 97 chat request thành công, 10 đợt; không có request lỗi mới. Caption/vector document không chạy lại.
- Test đạt **27/30 = 90%** theo nhãn AI hỗ trợ đối chiếu nguồn; chưa có học viên xác nhận hoặc quyết định cộng điểm chính thức.

Chi phí thực tế cao hơn khoảng quy đổi token cũ 0,12–0,16 USD, vẫn dưới khoản dự phòng 0,50 USD. Đây là minh họa rằng token ảnh, độ dài output và số lượt tìm thực tế khác kịch bản dự toán. Không đổi khoảng dự toán cũ sau khi thấy hóa đơn. Usage từng query và tổng mới nằm trong results/bonus/haiku_run_cost.json; tổng toàn lịch sử Day 7 nằm trong results/cost_summary.json. Sau khi hoàn tất đã dừng API.
