# Day 7 — Agentic RAG từ đầu ra Day 6

> Bản hiện tại là **base-v2**, đã sửa lỗi key offline, trace lỗi retrieval ban đầu và lời từ chối; test mới được tạo sau khi đã xem test v1. Lịch sử source/benchmark/kết quả v1 ở `results/history/base-v1/`. Bonus FPT 232 trang có hướng dẫn riêng tại [BONUS_RUN.md](BONUS_RUN.md).

Bài cá nhân: Nguyễn Quốc Quang Anh, MSSV 2A202604120, L3B. Triển khai và nhãn đánh giá có AI hỗ trợ; xem báo cáo cá nhân để biết số đo thực tế và giới hạn.

## Dữ liệu và kiến trúc

Dùng lại snapshot Luật Thương mại 36/2005/QH11 do Cục SHTT công bố trong ZIP Day 6: 84 trang vật lý, index 83 trang nội dung, 245 chunk C. ID, text, nguồn, trang, metadata và vector không thay đổi. Đây là tra cứu snapshot năm 2005; không xác nhận pháp luật hiện hành. Nguồn/quyền/SHA256 gốc ở `data/day6/manifest.json`; ánh xạ Day 7 ở `data/day6/provenance.json`.

Embedding `openai/text-embedding-3-small`, 1536 chiều; Qdrant local collection C, cosine exact, qdrant-client 1.20.0. Query dùng cùng model/dimension/cache Day 6. Không chạy lại ingestion hay gọi API embedding document. Nếu cache query chưa có thì gọi embedding thật và lưu cache; lỗi không fallback mock. Model agent mặc định `openai/gpt-4.1-mini` qua OpenRouter, temperature=0. Nhà cung cấp không trả revision model cố định; trace giữ model ID và usage thực tế.

Ba retrieval: TF-IDF từ starter; dense từ Qdrant Day 6; hybrid RRF lấy 20 candidate mỗi nhánh, score=sum(1/(60+rank)), không cộng trực tiếp cosine và TF-IDF. Filter chỉ nhận `chapter`, `year`, `section` từ input được cung cấp trước; benchmark chỉ dùng filter chương có trong câu hỏi Day 6. Không lấy filter từ gold. Mọi phương pháp dùng cùng corpus C.

Native function calling gồm `search(query)` và `finish(answer,citations,abstain)`. Search đầu luôn chạy query gốc và ghi riêng query model đề xuất; các search tiếp theo cho phép rewrite. Context khử trùng theo ID, ưu tiên kết quả mới, bỏ chunk không vừa budget, giữ source URL và trang. Budget tính bằng **ký tự**, gồm nguồn và separator; không phải token và không bao gồm system prompt/tool schema. Khi search tiếp, context cũ trong tool message bị thay bằng thông báo đã superseded để tránh nhân budget. Trace giữ đầy đủ các lần tìm trước đó.

ID citation phải có trong context cuối; server gắn `[chunk-id]` còn thiếu từ trường citations có cấu trúc vào câu trả lời hiển thị. Raw tool arguments vẫn giữ nguyên trong trace. Việc này chỉ đảm bảo truy nguồn, không chứng minh nội dung được nguồn hỗ trợ. Chấm ngữ nghĩa riêng. Câu không đủ evidence được model từ chối; citation không hợp lệ dẫn tới abstain, lỗi dịch vụ ghi status=error. Model phải gọi retrieval trước khi hoàn tất. Tài liệu được đặt là dữ liệu, không được dùng làm chỉ dẫn; chưa có benchmark red-team riêng cho prompt injection.

## Cài đặt

`.gitattributes` giữ nguyên byte và xuống dòng của file để fingerprint code, corpus, benchmark và trace khớp với lần chạy đã chốt trên các hệ điều hành. Không tự chuẩn hóa hoặc ghi lại JSON bằng formatter trước khi kiểm tra hash. Thay đổi xuống dòng cũng làm SHA256 khác dù nội dung đọc được giống nhau.

Python 3.11+ cho source; máy thực hiện dùng Windows CPython 3.14 và các dependency thực tế từ ZIP Day 6. Từ thư mục repo:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Điền `OPENROUTER_API_KEY` trong `.env`. Chạy thật gửi câu hỏi/context tới OpenRouter và phát sinh phí. Không commit `.env`.

Nếu có ZIP Day 6 gốc và dùng Windows CPython 3.14, có thể phục hồi dependencies offline thay cho pip. Lệnh này chỉ phục hồi thư viện; không nhập API key từ ZIP:

```powershell
$env:DAY6_ZIP = "<đường-dẫn-tới-ZIP-Day6-trên-máy-này>"
python scripts/bootstrap.py --zip $env:DAY6_ZIP --restore-deps
```

Bootstrap chỉ phục hồi `site-packages` vào venv cục bộ, không dùng executable cũ trong ZIP và không sửa `.env`. Với repo clone để kiểm tra, dùng snapshot đã lọc credential ở `artifacts/day6-reuse.zip`; chỉ cần tự cấu hình key trong `.env` nếu chạy model thật.

## Chuẩn bị và kiểm thử

```powershell
.venv\Scripts\python -m src.prepare --zip $env:DAY6_ZIP
.venv\Scripts\python -m unittest discover -s tests -v
```

Importer chỉ đọc các entry được chỉ định, giữ snapshot local tại `.day6/`; xuất corpus và benchmark có thể kiểm tra tại `data/day6/` và `benchmark/cases.json`. Không thực thi script pipeline từ ZIP. Qdrant là snapshot thật Day 6, không phải kết quả mock. Integration test mở Qdrant và chạy query cache gốc, không gọi API. Các test agent dùng stub chỉ kiểm tra hành vi phần mềm.

Nếu dùng bản bài nộp và chưa có `.day6/`, corpus/benchmark đã đi kèm nên chỉ cần khôi phục vector từ gói đã lọc secret, không cần ZIP Day 6 chứa key:

```powershell
.venv\Scripts\python -m src.rebuild --snapshot artifacts/day6-reuse.zip
.venv\Scripts\python -m unittest discover -s tests -v
```

Snapshot chứa nguyên collection C và cache cần thiết. Trường hợp không dùng snapshot, `python -m src.rebuild` tái tạo index bằng embedding thật theo lô; cần key/mạng và phát sinh phí. Lệnh rebuild từ chối ghi đè collection hiện có.

## Chạy dev → chốt → test

```powershell
.venv\Scripts\python -m src.experiments run --split dev --config all --workers 4
.venv\Scripts\python -m src.audit --split dev --config baseline --packet
```

Có bốn cấu hình trong `src/experiments.py`: baseline TF-IDF (k=3, budget=2400, 1 search); dense cùng budget; hybrid cùng budget (cải thiện 1); hybrid_context (k=6, budget=6000, tối đa 3 search, cải thiện 2). Cải thiện 2 thay nhiều tham số nên không quy tác dụng cho một tham số riêng. Không bắt buộc mọi thử nghiệm tăng điểm.

Đọc đáp án/context/nguồn và viết `results/dev/<config>/reviews.json`: một dòng mỗi query, có `query_id`, `citation_support` boolean ứng từng citation, `answer_grade` 0/1/2 và `context_grade` 0/1/2 cho câu có đáp án; `abstention_correct` boolean cho câu thiếu evidence; `reason`, `reviewer_kind`, `student_confirmed`, `trace_sha256`, `benchmark_sha256`. Các nhãn đã chấm đi kèm kết quả hiện tại; sửa nhãn chỉ sau khi đọc lại nguồn. Không tự đổi thành xác nhận của học viên.

```powershell
.venv\Scripts\python -m src.audit --split dev --config baseline
.venv\Scripts\python -m src.audit --split dev --config dense
.venv\Scripts\python -m src.audit --split dev --config hybrid
.venv\Scripts\python -m src.audit --split dev --config hybrid_context
.venv\Scripts\python -m src.experiments freeze
.venv\Scripts\python -m src.experiments run --split test --workers 4
```

Chọn trên dev theo thứ tự công bố trước: grounded answer mean được audit; Context Evidence Rate query gốc; Hit@3; Hit@1; median latency thấp hơn; tên cấu hình nếu hòa. `freeze` yêu cầu đủ dev/audit và không có lỗi. Test chỉ chạy baseline cùng cấu hình chọn, kiểm tra fingerprint benchmark/corpus/code/config đã chốt. Không dùng test để sửa pipeline. Mỗi query lưu riêng và tái sử dụng khi chạy lại; muốn thí nghiệm mới phải lưu thư mục kết quả cũ riêng và công bố protocol/test mới nếu đã chỉnh bằng test. Lệnh `freeze` chỉ chạy một lần cho mỗi thí nghiệm; bản hiện tại đã có selection thì không chốt lại.

Chấm từng query test như dev rồi tổng hợp bằng `src.audit`; công cụ không tự sinh nhãn. Các lỗi model/vector store báo riêng, không gán đáp án giả. `summary.json` retrieval chỉ lấy câu answerable chạy thành công; mẫu số thực tế và số lỗi luôn được báo. Câu thiếu evidence không thuộc mẫu số retrieval. Containment nguồn/trang/quote được chuẩn hóa khoảng trắng giống Day 6; gold là các evidence thay thế, chưa hỗ trợ tập evidence multi-hop bắt buộc. Context audit thủ công đọc nội dung bổ sung cho metric containment bảo thủ.

## Hỏi một câu

```powershell
.venv\Scripts\python -X utf8 -m src.ask "Nếu không có thỏa thuận khác, giá tính theo trọng lượng nào?" --config hybrid_context
```

Không đọc benchmark/gold; ghi trace tại `results/interactive/last.json`. File cùng tên được ghi đè, dùng `--output` để đổi đường dẫn.

## Đầu ra và nộp

`results/<split>/<config>/queries/` giữ trace từng câu; `traces.json`, `summary.json`, `reviews.json`, `audit_summary.json` để đối chiếu. `results/protocol.json`, `selection.json` giữ tiêu chí và cấu hình chốt; `results/embedding_usage.json` giữ usage embedding mới; `results/history/` giữ lượt dev phát hiện lỗi hiển thị citation. Chi phí lấy từ provider usage, không suy từ bảng giá; request thiếu cost báo riêng. Không cộng lại usage Day 6 vào chi phí Day 7.

Theo `SUBMISSION.md`, cần repo cá nhân có quyền xem cho người chấm, báo cáo đổi tên theo MSSV/họ tên, code/test/hướng dẫn chạy, benchmark và nhãn/trace. Dữ liệu/corpus JSON và kết quả Day 7 nằm ngoài đường dẫn starter bị ignore để có thể nộp. `.day6/`, `.bonus/`, `.venv/`, `.env` bị ignore; dùng snapshot sạch secret để khôi phục. Corpus luật 84 trang dùng cho phần cơ bản; phần nâng cao dùng corpus FPT 232 trang riêng theo [BONUS_RUN.md](BONUS_RUN.md).

Tạo báo cáo và gói nộp sau khi đã có đủ nhãn:

```powershell
.venv\Scripts\python scripts/finalize_lab.py
.venv\Scripts\python scripts/package_submission.py
```

Finalizer chỉ kiểm chứng/tổng hợp nhãn đã có, không tự tạo nhãn, không tự xác nhận học viên. Giữ nguyên kết quả cũ và báo cả chi phí pilot lỗi. Bản gói nộp không chứa credential, PDF FPT hay ảnh toàn bộ trang; người chấm cần PDF nguồn hợp lệ để khôi phục ảnh gốc theo SHA.
