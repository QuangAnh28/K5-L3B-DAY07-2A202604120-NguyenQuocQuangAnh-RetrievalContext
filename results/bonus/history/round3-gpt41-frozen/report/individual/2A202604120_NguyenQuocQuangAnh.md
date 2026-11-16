# Báo cáo Day 7 — Agentic RAG

Nguyễn Quốc Quang Anh · MSSV 2A202604120 · L3B.

Code, benchmark và phần đọc/chấm có Codex AI hỗ trợ. Nhãn giữ reviewer_kind=AI, student_confirmed=false; không coi là xác nhận của học viên hoặc đánh giá độc lập. Người triển khai đồng thời thiết kế benchmark/chấm nên có nguy cơ thiên lệch. Không dùng kết quả mock làm benchmark.

## Dữ liệu và benchmark cơ bản

Dùng nguyên snapshot Luật Thương mại 36/2005/QH11 từ Day 6: 84 trang vật lý, index 83 trang nội dung, 245 chunk C. Giữ ID/text/source/page/metadata/vector. Nguồn/quyền/ngày truy cập/SHA256 ở data/day6/manifest.json. Đây là snapshot năm 2005, không xác nhận luật hiện hành. Embedding OpenRouter openai/text-embedding-3-small 1536 chiều; Qdrant local cosine exact. Model agent openai/gpt-4.1-mini, temperature=0; không có revision cố định từ provider.

Benchmark v2 tại benchmark/cases.json có 15+2 dev và 5+2 test. Dev giữ câu hỏi để so sánh thí nghiệm; test mới về các Điều 23, 26, 28, 56, 309 và hai câu thiếu mức phí/mức phạt trong snapshot. Test Day 6 và test Day 7 v1 đã thấy nên không dùng để đánh giá v2. Benchmark/source/kết quả/báo cáo v1 được giữ tại results/history/base-v1. Không đưa gold vào model hay filter.

Câu có đáp án ghi nguồn/trang/evidence. Một số gold v2 lấy cả chunk nguồn nên quote containment bảo thủ hơn đánh giá ngữ nghĩa, đặc biệt b2-t28: context có định nghĩa đúng nhưng không chứa toàn quote dài. Công bố sai khác, không đổi gold sau khi thấy điểm. Câu thiếu evidence đã đọc điều khoản liên quan và toàn văn; không suy vắng chỉ từ top-k.

## Phương pháp, context và thí nghiệm

| Cấu hình | Retrieval | top-k | Budget ký tự | Max search | Giả thuyết |
|---|---|---:|---:|---:|---|
| baseline | TF-IDF | 3 | 2400 | 1 | Lexical baseline |
| dense | Qdrant C | 3 | 2400 | 1 | Ngữ nghĩa giúp khác cách diễn đạt |
| hybrid — cải thiện 1 | RRF dense + TF-IDF | 3 | 2400 | 1 | Bổ sung tín hiệu từ khóa/ngữ nghĩa |
| hybrid_context — cải thiện 2 | Cùng hybrid | 6 | 6000 | 3 | Giữ nhiều evidence hơn, cho phép tìm tiếp |

RRF lấy 20 candidate mỗi nhánh, sum(1/(60+rank)). Không cộng trực tiếp score khác thang. Các phương pháp dùng cùng corpus C/query/nhãn. Filter chương chỉ theo phạm vi được nêu trong query dev, không từ gold. Query đầu luôn là query gốc; trace ghi riêng model_query. Budget gồm ID/source URL/trang/separator; là ký tự, không phải token. Dedup ID và ưu tiên evidence lượt mới; chunk không vừa bị bỏ. Model có thể tìm tiếp hoặc finish; không có số lượt chung bắt buộc của đề.

Citation ID phải có trong context; renderer gắn bracket từ ID có cấu trúc và giữ raw arguments. Không chứng minh semantic grounding chỉ bằng membership. Abstain dùng lời từ chối chuẩn, không trả nguyên khẳng định tự do. Lỗi retrieval chẩn đoán trước agent cũng được lưu status:error rồi tiếp tục query khác. Provider chỉ đòi key khi gửi request, cho phép replay cache offline. Ba lỗi này được kiểm thử hồi quy, giữ kết quả trước sửa.

Cải thiện 2 thay k/budget/max_searches cùng lúc, không quy lợi ích cho một yếu tố. Thực tế các lượt cơ bản cuối đều tìm một lần; không tuyên bố đã đo lợi ích multi-hop.

## Kết quả cơ bản

| Cấu hình / split | Hit@1 | Hit@3 | Context đủ quote cuối | Mean answer /2 | Citation hỗ trợ | Abstention đúng | Từ chối nhầm | Median ms | Chat USD |
|---|---|---|---|---:|---|---|---|---:|---:|
| baseline/dev | 8/15 (53.3%) | 14/15 (93.3%) | 12/15 (80.0%) | 1.533 | 13/14 (92.9%) | 2/2 (100.0%) | 2/15 (13.3%) | 5888.6 | 0.01064480 |
| dense/dev | 7/15 (46.7%) | 10/15 (66.7%) | 9/15 (60.0%) | 1.267 | 12/16 (75.0%) | 2/2 (100.0%) | 2/15 (13.3%) | 26985.7 | 0.01095200 |
| hybrid/dev | 8/15 (53.3%) | 14/15 (93.3%) | 12/15 (80.0%) | 1.600 | 14/16 (87.5%) | 2/2 (100.0%) | 0/15 (0.0%) | 24078.8 | 0.01098880 |
| hybrid_context/dev | 8/15 (53.3%) | 14/15 (93.3%) | 15/15 (100.0%) | 1.733 | 14/15 (93.3%) | 2/2 (100.0%) | 1/15 (6.7%) | 4574.2 | 0.01487040 |
| baseline/test | 3/5 (60.0%) | 4/5 (80.0%) | 4/5 (80.0%) | 1.600 | 4/5 (80.0%) | 2/2 (100.0%) | 0/5 (0.0%) | 3892.5 | 0.00534600 |
| hybrid_context/test | 4/5 (80.0%) | 4/5 (80.0%) | 4/5 (80.0%) | 1.800 | 5/5 (100.0%) | 2/2 (100.0%) | 0/5 (0.0%) | 3828.5 | 0.01299480 |

Chi tiết phân bố answer 0/1/2, context 0/1/2, tool use, số lượt gọi, số câu có citation, lỗi và mẫu số ở audit_summary.json/summary.json. Đã đọc toàn bộ 17 câu dev mỗi cấu hình và 7 câu test cho baseline/selected. Nhãn và lý do từng câu/citation ở reviews.json, giữ hash trace/benchmark. Retrieval metrics không tính câu thiếu evidence; lỗi cơ bản báo riêng. Median là thời gian agent gồm chat/search, không gồm mở index và pass ranking chẩn đoán; cache ấm và concurrency khiến không thể suy tốc độ API lạnh. Chi phí bảng chỉ chat; embedding dùng cache chia sẻ và được tính tổng riêng trong cost_summary.

Chọn hybrid_context trên dev tại 2026-11-16T03:59:53.133664+00:00: ưu tiên mean answer đã đọc/chấm, sau đó Context Evidence Rate gốc, Hit@3, Hit@1, latency, tên cấu hình. Hash code/provider/corpus/benchmark lưu trong selection; test chỉ chạy sau chốt.

## Phân tích lỗi và trước/sau

- Lượt đầu thiếu bracket citation dù có structured IDs: giữ lịch sử round0-citation-rendering, sửa renderer và chạy dev lại. Không sửa trace cũ.

- d7-q07: baseline bỏ evidence Điều 35 khi đóng context nên từ chối nhầm. Context lớn giữ đủ nhưng model dẫn đoạn Điều 36/trường hợp không có thỏa thuận thay khoản 1 Điều 35; chấm 1 và citation không hỗ trợ.

- d7-q11: baseline/dense/hybrid nhầm hàng cho thuê Điều 274 thành mua bán Điều 57. Context lớn dẫn đúng Điều 57 nhưng bỏ điều kiện về giữ chứng từ; chấm 1.

- d7-q06/d7-q10: hybrid nhỏ vẫn trả quy định chung/giá hàng thừa thay hình thức mua bán quốc tế/thời hạn thanh toán. Context lớn giúp giữ đúng đoạn. RRF không luôn tăng điểm; báo cả kết quả không cải thiện.

- d7-q09 v2: context lớn đủ evidence nhưng validator từ chối raw citation không phù hợp; chấm 0, không chữa đáp án để làm đẹp điểm.

- b2-t28 trên test mới: baseline phủ định sai điều mà chính nguồn xác nhận. Selected kết luận đúng nhưng nói nhầm Điều 29 thay Điều 28, chấm 1. Không điều chỉnh pipeline theo lỗi test này.

## Ví dụ trình bày

**b2-t23 / hybrid_context:** Trước khi chấm dứt hoạt động tại Việt Nam, thương nhân nước ngoài phải thực hiện nghĩa vụ gì với Nhà nước, tổ chức và cá nhân liên quan?

Trước khi chấm dứt hoạt động tại Việt Nam, thương nhân nước ngoài có nghĩa vụ thanh toán các khoản nợ và các nghĩa vụ khác với Nhà nước, tổ chức, cá nhân có liên quan tại Việt Nam. [luat-thuong-mai-36-2005-qh11-p8-paragraph-1000-a28a8840d2541c86]

Trace: results/test/hybrid_context/queries/b2-t23.json

**b2-u1 / hybrid_context:** Theo tài liệu, lệ phí cấp giấy phép thành lập Văn phòng đại diện của thương nhân nước ngoài là bao nhiêu đồng?

Không đủ bằng chứng để trả lời.

Trace: results/test/hybrid_context/queries/b2-u1.json

**b2-t28 / baseline:** Theo tài liệu, đưa hàng hóa từ nội địa Việt Nam vào khu vực hải quan riêng nằm trên lãnh thổ Việt Nam có thuộc định nghĩa xuất khẩu không?

Theo tài liệu, đưa hàng hóa từ nội địa Việt Nam vào khu vực hải quan riêng nằm trên lãnh thổ Việt Nam không thuộc định nghĩa xuất khẩu. Xuất khẩu hàng hóa là việc hàng hóa được đưa ra khỏi lãnh thổ Việt Nam hoặc đưa vào khu vực đặc biệt nằm trên lãnh thổ Việt Nam được coi là khu vực hải quan riêng theo quy định của pháp luật, không phải từ nội địa vào khu vực hải quan riêng. [luat-thuong-mai-36-2005-qh11-p9-paragraph-1000-912c69a76dd1acdb]

Trace: results/test/baseline/queries/b2-t28.json

## Thử thách nâng cao

Bổ sung một corpus riêng: báo cáo thường niên FPT 2025, 232 trang PDF. Index mọi trang với text và mô tả trực quan, giữ ảnh gốc; Qdrant riêng FPT2025 dùng cùng họ embedding 1536 chiều. Manifest, quyền/nguồn và hash ở data/bonus/manifest.json; coverage toàn bộ ở data/bonus/coverage.json. Không gộp số liệu của FPT vào corpus luật Day 6.

Benchmark bonus riêng có 18 dev, 30 test, đủ nhóm bảng/ảnh-sơ đồ/biểu đồ/multi-hop/text/thiếu evidence. Quy trình yêu cầu chốt trên dev trước test, đối chiếu ảnh gốc và chấm từng câu đúng/đủ/citation trang-vùng/đơn vị/phép tính; lỗi tính không đạt.

**CHƯA CHẠY TEST BONUS, CHƯA NHẬN 15 ĐIỂM.** Đã sửa câu dev fd-i3 theo ảnh gốc: năm nhãn, không phải ba và không có “Thông minh hơn”. Giữ toàn bộ benchmark/trace/nhãn/code pilot cũ; tái sử dụng 17 câu text và 15 câu vision có đầu vào/cấu hình không đổi. Sau khi người dùng yêu cầu chạy nốt bốn câu dev, cả bốn đã có kết quả thật, được đối chiếu nguồn và ghi nhãn. Dev mới text 14/18, vision 15/18, không lỗi hệ thống; chọn vision. Bốn câu gọi 10 chat request, 0,16389 USD theo usage. Dừng trước 30 câu test để giữ phạm vi chi phí đã yêu cầu. Nếu đổi model phải làm lại dev cho cấu hình đó.

| Nhóm bonus test | Đạt / tổng |
|---|---|

Báo cáo đầy đủ: [BONUS_REPORT.md](../BONUS_REPORT.md). Cách chạy: [BONUS_RUN.md](../../BONUS_RUN.md). Nhãn từng câu: results/bonus/test/<selected>/reviews.json.

## Tái lập, chi phí và giới hạn

Kiểm thử offline không có API key: 28 tests qua. Fingerprint code/corpus/benchmark khớp; 232 hash ảnh gốc được kiểm tra. Tổng Day 7 (mọi lượt cơ bản/bonus, pilot lỗi, caption, embedding): 1005 request thành công có ID, **1.94801708 USD** theo usage provider; 0 request thành công thiếu cost. Failed attempt records=23; không tự đoán phí request lỗi không có usage. Không cộng chi phí Day 6 vào tổng mới.

Lệnh setup/run/test/audit/freeze ở LAB_RUN.md và BONUS_RUN.md. requirements-lock.txt ghi môi trường thực tế Windows CPython 3.14. Snapshot vectors sạch key ở artifacts/day6-reuse.zip và bonus-reuse.zip. PDF/ảnh FPT giữ local; để tái lập cần đúng PDF nguồn được phép truy cập, SHA trong manifest. Không tự gán giấy phép mở cho tài liệu FPT.

Giới hạn: corpus nhỏ và cùng tài liệu giữa dev/test, nhãn AI cùng người xây hệ thống, chưa có chấm độc lập/học viên xác nhận. Caption toàn trang tự sinh có thể sai; chỉ những evidence/citation khi chấm được đọc lại ảnh gốc, không tuyên bố mọi caption đều đúng. Chưa có red-team prompt injection riêng; chỉ có instruction tách tài liệu khỏi chỉ dẫn. Tái chạy API có thể khác dù temperature=0.

Chưa push/nộp repo cá nhân. Học viên cần đọc lại nhãn/evidence, cấp quyền repo và nộp link theo SUBMISSION.md. Không thay student_confirmed thành true nếu chưa kiểm tra thực tế.
