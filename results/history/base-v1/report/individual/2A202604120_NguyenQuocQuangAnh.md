# Báo cáo Day 7 — Agentic RAG

Họ tên: Nguyễn Quốc Quang Anh · MSSV: 2A202604120 · Lớp: L3B.

Code, benchmark mới và nhãn được Codex hỗ trợ triển khai/đọc/chấm. Nhãn có `reviewer_kind: AI`, `student_confirmed: false`; không gọi đây là chấm mù, đánh giá độc lập hay xác nhận của học viên. Người triển khai đồng thời thiết kế benchmark và chấm kết quả nên có nguy cơ thiên lệch. Các kết quả dưới đây là số đo thực tế, không phải kết quả mock.

## Dữ liệu và benchmark

Dùng lại ZIP Day 6: snapshot Luật Thương mại 36/2005/QH11 của Cục SHTT, 84 trang vật lý, 83 trang có nội dung được index, 245 chunk theo cấu hình C. Giữ ID/text/source/page/metadata/vector gốc. Nguồn, quyền sử dụng do Day 6 khai báo, ngày truy cập và SHA256 PDF ở `data/day6/manifest.json`; archive hash và chuyển đổi schema ở `data/day6/provenance.json`. PDF gốc đã kiểm tra SHA và evidence từng câu bằng đối chiếu ký tự sau bỏ khoảng trắng; giới hạn kiểm tra này không thay việc đọc ngữ nghĩa.

Embedding OpenRouter `openai/text-embedding-3-small`, 1536 chiều; Qdrant local persistent collection C, cosine exact, qdrant-client 1.20.0. Model agent `openai/gpt-4.1-mini`, temperature=0; response lưu tên model/usage, không có revision cố định từ nhà cung cấp. API key được giữ local trong `.env`, không có trong bài nộp. `requirements-lock.txt` ghi môi trường chạy thực tế.

Benchmark `benchmark/cases.json`: dev có 15 câu có đáp án từ Day 6 và 2 câu thiếu evidence; test mới có 5 câu có đáp án về các Điều 53, 60, 129, 223, 323 và 2 câu thiếu evidence. Loại toàn bộ q16–q20 của test Day 6 vì đã xem báo cáo/kết quả. Câu test mới dùng điều khác, được tạo trước lượt dev Day 7; vẫn là cùng tài liệu và có thể chung trang với dev, không coi là test ngoài miền hay hoàn toàn độc lập.

Gold chứa nguồn, trang và quote; evidence thay thế được tính bằng OR. Khớp nguồn/trang/quote sau chuẩn hóa khoảng trắng; giữ cùng quy tắc giữa các phương pháp. Câu thiếu evidence là thông tin giao dịch/doanh thu/tài khoản/lịch công ty cụ thể không có trong snapshot luật, đã kiểm tra trên toàn text 84 trang và lưu `absence_check`; không kết luận vắng chỉ từ top-k. Nhóm này còn dễ do chứa tên/mốc thời gian không thuộc corpus; cần benchmark khó hơn về sau. Không đưa gold/expected answer/absence_reason vào agent hoặc retrieval.

## Retrieval, context và giả thuyết

| Cấu hình | Phương pháp | top-k | Budget ký tự | Max search | Giả thuyết |
|---|---|---:|---:|---:|---|
| baseline | TF-IDF | 3 | 2400 | 1 | Baseline lexical từ starter |
| dense | Qdrant C | 3 | 2400 | 1 | Ngữ nghĩa giúp câu hỏi khác cách diễn đạt |
| hybrid — cải thiện 1 | Dense + TF-IDF, RRF | 3 | 2400 | 1 | Kết hợp tín hiệu ngữ nghĩa và từ khóa |
| hybrid_context — cải thiện 2 | Cùng hybrid | 6 | 6000 | 3 | Thêm evidence qua k/budget và cho phép tìm tiếp |

Hybrid lấy top-20 mỗi nhánh, RRF sum(1/(60+rank)); không cộng score khác thang đo. Cả ba cùng corpus C, metadata và query gốc. Filter chương chỉ dùng input Day 6 được nêu trong câu q05/q13; không lấy từ gold. Query đầu giữ nguyên câu hỏi, ghi riêng `model_query` nếu model đề xuất khác. Các search sau cho phép rewrite nhưng lượt thực tế đều dừng sau một search; chưa có bằng chứng thực nghiệm về lợi ích nhiều lượt hay multi-hop.

Context khử trùng ID, ưu tiên kết quả mới, giữ source URL và trang; bỏ nguyên chunk nếu không vừa. Budget gồm ký tự nguồn/ID/separator, không tính system prompt và schema tool; không phải số token. Context tool trước được supersede để tránh nhân budget. Model dùng native function calling `search` rồi `finish`. Server kiểm tra ID có trong context và gắn citation có cấu trúc vào câu trả lời; giữ raw arguments trong events. Membership không bảo đảm semantic grounding.

## Kết quả retrieval và context

| Cấu hình / split | Hit@1 | Evidence Hit@3 | Context Evidence Rate gốc | Context cuối | Median agent ms | Chi phí chat USD |
|---|---|---|---|---|---:|---:|
| baseline / dev | 8/15 (53.3%) | 14/15 (93.3%) | 12/15 (80.0%) | 12/15 (80.0%) | 3355.7 | 0.01010120 |
| dense / dev | 7/15 (46.7%) | 10/15 (66.7%) | 9/15 (60.0%) | 9/15 (60.0%) | 3289.4 | 0.01194480 |
| hybrid / dev | 8/15 (53.3%) | 14/15 (93.3%) | 12/15 (80.0%) | 12/15 (80.0%) | 3250.9 | 0.01053120 |
| hybrid_context / dev | 8/15 (53.3%) | 14/15 (93.3%) | 15/15 (100.0%) | 15/15 (100.0%) | 3297.7 | 0.01742040 |
| baseline / test | 4/5 (80.0%) | 5/5 (100.0%) | 4/5 (80.0%) | 4/5 (80.0%) | 9243.2 | 0.00519280 |
| hybrid_context / test | 3/5 (60.0%) | 5/5 (100.0%) | 5/5 (100.0%) | 5/5 (100.0%) | 3895.6 | 0.00908720 |

Hit@3 vẫn dùng cutoff 3 kể cả cấu hình k=6. Mẫu số là câu có đáp án chạy thành công, không gồm câu thiếu evidence; lượt cuối không có lỗi. Context metric dùng quote containment, audit ngữ nghĩa riêng ở bảng sau. Median gồm hai lần gọi chat và search trong agent, không gồm mở index/chạy ranking chẩn đoán trước đó. Query embedding có thể đã cache ở lượt trước, nên là phép đo warm; concurrency=4 và biến thiên API khiến số này không chứng minh tốc độ tuyệt đối. Đổi nhiều tham số trong cải thiện 2 nên không quy lợi ích cho riêng k, budget hay max_searches.

## Agent và nhãn đọc đối chiếu

| Cấu hình / split | Tool use | Grounded 0/1/2 | Mean /2 | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm | Context 0/1/2 |
|---|---|---|---:|---|---|---|---|---|
| baseline / dev | 17/17 (100.0%) | 3/1/11 | 1.533 | 13/14 (92.9%) | 13/13 (100.0%) | 2/2 (100.0%) | 2/15 (13.3%) | 3/0/12 |
| dense / dev | 17/17 (100.0%) | 5/1/9 | 1.267 | 11/15 (73.3%) | 13/13 (100.0%) | 2/2 (100.0%) | 2/15 (13.3%) | 3/3/9 |
| hybrid / dev | 17/17 (100.0%) | 3/0/12 | 1.600 | 15/17 (88.2%) | 15/15 (100.0%) | 2/2 (100.0%) | 0/15 (0.0%) | 2/1/12 |
| hybrid_context / dev | 17/17 (100.0%) | 0/2/13 | 1.867 | 16/18 (88.9%) | 15/15 (100.0%) | 2/2 (100.0%) | 0/15 (0.0%) | 0/0/15 |
| baseline / test | 7/7 (100.0%) | 1/0/4 | 1.600 | 4/4 (100.0%) | 4/4 (100.0%) | 2/2 (100.0%) | 1/5 (20.0%) | 1/0/4 |
| hybrid_context / test | 7/7 (100.0%) | 0/0/5 | 2.000 | 5/5 (100.0%) | 5/5 (100.0%) | 2/2 (100.0%) | 0/5 (0.0%) | 0/0/5 |

Đã đọc 17/17 dev mỗi cấu hình và 7/7 test mỗi cấu hình (gồm đủ 5 câu có đáp án và 2 câu thiếu evidence). Mọi lượt cuối gọi search đúng một lần; không có provider/vector-store error. Citation hợp lệ tính từng citation có trong context và hỗ trợ khẳng định; citation thừa/nhầm bị loại dù câu chính đúng. Grounded 0=sai/thiếu evidence, 1=đúng một phần/thiếu điều kiện, 2=đúng và đủ. Context 0=không có evidence cần thiết, 1=liên quan nhưng thiếu điều kiện/nguồn, 2=đủ evidence/nguồn. Mỗi nhãn có lý do và hash trace/benchmark trong `reviews.json`; công cụ audit chỉ tổng hợp nhãn.

## Chọn cấu hình và phân tích lỗi dev

Chốt `hybrid_context` lúc 2026-11-16T02:57:23.781473+00:00 theo protocol công bố trước: ưu tiên mean grounded answer trên dev, sau đó Context Evidence Rate query gốc, Hit@3, Hit@1, median latency thấp hơn, tên cấu hình. `results/selection.json` giữ hash benchmark/corpus/code và audit dev. Test chạy sau khi chốt; không sửa pipeline theo kết quả test.

1. **Lỗi hiển thị citation ở lượt đầu:** model trả ID trong trường citations nhưng không gắn bracket vào answer. Validator cũ từ chối đáp án. Sửa renderer để chỉ gắn ID đã có trong context; giữ trace nguyên gốc. Lượt dev trước sửa lưu đầy đủ tại `results/history/round0-citation-rendering/`; cả 4 cấu hình đều có 15/15 câu answerable bị abstain. Lượt dev chạy lại cho phép đánh giá nội dung thực tế. Chi phí lượt lỗi vẫn được tính.

2. **d7-q07 — rơi evidence khi đóng context:** baseline có evidence trong ranking nhưng context 2400 chỉ giữ địa điểm thanh toán/thời hạn giao nên từ chối nhầm. Cấu hình hybrid_context giữ được Điều 35 nên câu trả lời đúng ý, nhưng lại dẫn chunk Điều 42 về chứng từ. Chấm answer=1, citation=false; không tuyên bố vấn đề đã được giải quyết hoàn toàn.

3. **d7-q11 — nhầm phạm vi cho thuê/mua bán:** baseline, dense và hybrid lấy Điều 274 trang 71 về cho thuê để nói về bên mua. Chấm 0 và citation=false. Cấu hình context lớn chứa Điều 57 trang 16 và dẫn đúng, nhưng bỏ điều kiện kể cả bên bán giữ chứng từ; chấm 1. Context đủ không đồng nghĩa trả lời đủ.

4. **d7-q06/d7-q10 — hybrid chưa luôn tốt:** hybrid context nhỏ áp dụng hình thức chung Điều 24 cho hợp đồng quốc tế thay Điều 27, và trả lời giá hàng thừa/ngừng thanh toán thay thời hạn Điều 55. Context lớn giữ được evidence đúng nên cả hai đạt 2. RRF nhỏ giữ Hit@3 14/15 như TF-IDF và thấp hơn baseline ở một số câu; báo cả kết quả không cải thiện.

Trên test, baseline có Hit@3=5/5 nhưng chỉ giữ context đủ 4/5; d7-t223 bị loại do budget nên từ chối nhầm. Cấu hình chọn giữ đủ cả hai khoản Điều 223, trả lời đủ với đúng citation. Test Hit@1 của cấu hình chọn chỉ 3/5, thấp hơn baseline 4/5; không đổi lựa chọn sau khi thấy test.

## Ví dụ trình bày

**d7-t53 / hybrid_context:** Nếu không có thỏa thuận khác, giá hàng hóa tính theo trọng lượng dùng trọng lượng nào?

Trừ trường hợp có thỏa thuận khác, nếu giá được xác định theo trọng lượng của hàng hóa thì trọng lượng đó là trọng lượng tịnh. [luat-thuong-mai-36-2005-qh11-p16-paragraph-1000-2a041e99beaed807]

Trace: `results/test/hybrid_context/queries/d7-t53.json`.

**d7-u3 / hybrid_context:** Số tài khoản ngân hàng để thanh toán hợp đồng số HD-2026-071 là gì?

Luật Thương mại 2005 không quy định số tài khoản ngân hàng để thanh toán hợp đồng số HD-2026-071.

Trace: `results/test/hybrid_context/queries/d7-u3.json`.

**d7-t223 / baseline:** Bên mời thầu và người liên quan phải bảo mật những thông tin nào trong đấu thầu?

Không đủ bằng chứng để trả lời.

Trace: `results/test/baseline/queries/d7-t223.json`.

## Chi phí, tái lập và giới hạn

Tổng Day 7 gồm cả lượt dev lỗi và lượt cuối: 309 request thành công (300 chat, 9 embedding), 267793 prompt tokens, 18170 completion tokens; cost từ provider usage **0.12458372 USD**, 0 request thiếu trường cost. Không cộng lại chi phí Day 6. GET kiểm tra model không có token ledger. Chi phí có thể thay đổi khi chạy lại.

Lệnh setup, nhập ZIP/khôi phục snapshot, unit tests, dev, audit, freeze, test và hỏi tự do ở `LAB_RUN.md`. Dữ liệu vector công khai được đóng gói tại `artifacts/day6-reuse.zip`, chỉ có collection C và cache cần thiết, không có API key. Code tái tạo bằng embedding thật ở `src/rebuild.py`; giữ vector Day 6 nếu dùng snapshot. Unit/integration checks, nguồn PDF và fingerprint ở `results/verification.json`; trace/review/summary từng cấu hình ở `results/`.

Giới hạn: corpus một văn bản, lỗi khoảng trắng font PDF được giữ nguyên; chưa sửa extraction, chưa có đánh giá đa tài liệu, multi-hop, reranker hoặc prompt-injection red-team. Các nhãn do AI hỗ trợ cần học viên đọc đối chiếu trước khi nộp; chưa có xác nhận của học viên và không gọi là human audit. Tái chạy API có thể khác dù temperature=0; dependency/native ABI cần đúng môi trường. Không thực hiện bonus vì tài liệu chỉ 84 trang và không có benchmark bảng/ảnh/biểu đồ đáp ứng ADVANCED.md.

Bài làm hiện ở repo local; chưa tạo remote cá nhân hay push/nộp link cho giảng viên. Học viên cần kiểm tra nhãn/nội dung, cấp quyền repo và nộp theo SUBMISSION.md. Không tự ước lượng điểm rubric.

Tham khảo giao thức function calling: [OpenRouter official documentation](https://openrouter.ai/docs/guides/features/tool-calling). Yêu cầu bài học lấy từ GUIDE.md, BENCHMARK.md, RUBRIC.md và RULES.md trong repo.
