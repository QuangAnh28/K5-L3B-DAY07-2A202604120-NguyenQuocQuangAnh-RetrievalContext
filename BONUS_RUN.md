# Bonus — FPT Báo cáo thường niên 2025

## Trạng thái đã hoàn tất đánh giá

Vision dùng `anthropic/claude-haiku-5.5`, thinking tắt, không gửi temperature; k=8, tối đa 12 trang context và 3 lượt search. Đã chạy mới đủ 18 dev, đạt 15/18; text GPT-4.1-mini dùng lại 18 output có đầu vào/config/source không đổi, đạt 14/18. Đã chốt vision bằng tiêu chí công bố trước, rồi chạy đủ 30 test.

**Test: 27/30 = 90%, không lỗi hệ thống.** Đây là nhãn AI hỗ trợ đối chiếu ảnh gốc, giữ `student_confirmed=false`; không tự coi là điểm chính thức hoặc chấm độc lập. Cần giảng viên chấp nhận đủ các điều kiện ADVANCED.md ngoài ngưỡng số học. Ba câu không đạt: ft-t2 từ chối; ft-i2 trả lời tự mâu thuẫn 3/hai đơn vị; ft-i5 thêm mô tả vị trí không đúng. Không gọi lại câu sai để chọn đáp án tốt hơn.

Tổng mới cho **18 dev + 30 test**: **0,18257208 USD** theo usage provider, gồm 0,06658480 USD chat dev và 0,11598728 USD chat/embedding query test. Có 97 chat request thành công, chạy 10 đợt nhỏ. Không caption/embedding document lại, không gọi model để chấm hay đóng gói. Tổng này không gồm chi phí lịch sử/caption/vector trước đó. Xem `results/bonus/haiku_run_cost.json` và `results/cost_summary.json` để phân biệt.

Mọi API đã dừng; kết quả đã có nên không cần chạy lại để nộp. `src.bonus run` dùng lại từng file query đã tồn tại, kể cả lỗi; không tự retry. Không chạy freeze lần nữa vì selection đã tồn tại. Nếu đổi model/config/source cần thí nghiệm mới; nếu dùng test để chỉnh phải tạo test mới, không báo lại bộ test này là độc lập.

Lịch sử GPT-4.1 cũ giữ tại `results/bonus/history/round3-gpt41-frozen`. Gold dev fd-i3 và gold test ft-c5 đã được sửa bằng ảnh gốc **trước bất kỳ test bonus nào**; lịch sử và lý do được giữ. Ft-c5: tỷ lệ văn bản cứng màu cam cao nhất năm 2022 là 92,9%; 2025 là 4,58%. Dev không đổi khi sửa gold test.

Lệnh chỉ đọc file/cache và usage, không gọi API:

```powershell
.venv\Scripts\python -X utf8 scripts/bonus_cost_plan.py
.venv\Scripts\python -X utf8 -m src.bonus audit --split dev --config all
.venv\Scripts\python -X utf8 -m src.bonus audit --split test --config vision
.venv\Scripts\python -X utf8 scripts/finalize_lab.py
.venv\Scripts\python -X utf8 scripts/package_submission.py
```

Công cụ chia đợt `scripts/run_bonus_batch.py --split test --config vision --count 5` chỉ gọi API cho câu chưa có kết quả. `--stop-after-usd` kiểm tra giữa các câu, **không phải trần chi phí cứng của request đang chạy**. Không cần thực thi lệnh này với bộ test đã hoàn tất. Đơn giá/dự toán và chi phí thực tế ở [MODEL_COST.md](report/MODEL_COST.md).

## Kiến trúc

1. PDFium lấy text vùng nội dung, bỏ sidebar lặp từ trang 3; render ảnh gốc đủ 232 trang, bao gồm bìa/trang ít text.
2. GPT-4.1-mini mô tả hình/bảng/biểu đồ ở **mọi trang** để giúp truy xuất. Caption là dữ liệu sinh bởi model, có thể sai, không phải gold.
3. Embedding thật `openai/text-embedding-3-small` 1536 chiều cho text + caption, Qdrant collection `FPT2025` riêng. Đây là index mới cho corpus bonus; index C Day 6 vẫn được dùng trong phần cơ bản.
4. Retrieval hybrid hợp nhất top-24 dense và lexical bằng RRF k=60. Model gọi `search` với query gốc, rồi có thể viết lại/tách query để lấy thêm trang. Không đưa số trang/vùng gold vào tool khi chạy.
5. Agent cấu hình `vision` đọc **ảnh trang gốc** sau retrieval để tra hàng/cột, màu/chú giải và đường nối sơ đồ. Citation có ID trang PDF vật lý và mô tả vùng/bảng/hình cụ thể. Cấu hình `text` chỉ có text + caption để so sánh ảnh hưởng khi thiếu hình gốc.
6. Kết quả được đọc đối chiếu nguồn, chấm đạt/không đạt. Lỗi/timeout tính không đạt, không loại khỏi mẫu số. Không tự suy ra đạt từ ID citation hay từ khớp đáp án bằng chuỗi.

Context được giới hạn bằng số trang và độ dài text: `text` tối đa 6 trang (k=4, 2 lượt search), `vision` tối đa 12 trang (k=8, 3 lượt search). Mỗi trang giữ tối đa 3200 ký tự text cộng mô tả visuals và một ảnh 1600 pixel ngang khi bật vision. Giới hạn này không phải token budget; usage token thực tế ở từng request. Khi tìm tiếp, thay các ảnh/context cũ bằng tập context mới để tránh nhân bản ảnh trong request. Trace giữ lịch sử đầy đủ các tập context cũ.

Native tool choice bắt buộc sau retrieval để model chỉ tìm tiếp hoặc gọi finish. Lượt dev pilot dùng auto có trường hợp trả text thường, đã được ghi lỗi và lưu tại `results/bonus/history/round0-tool-choice`. Không có test bonus nào chạy trong lượt pilot đó.

## Khôi phục để kiểm tra trên máy khác

Cài Python 3.11+ và `requirements.txt` (môi trường thực tế CPython 3.14, lock tại requirements-lock.txt). Chuẩn bị key OpenRouter trong `.env` nếu chạy model thật. Các tests offline/cache không cần key.

Khôi phục ảnh và vector từ đúng PDF đã dùng:

```powershell
.venv\Scripts\python scripts/restore_bonus_assets.py --pdf "C:\Users\Think Pad\Downloads\BCTN-2025.pdf" --snapshot artifacts/bonus-reuse.zip
.venv\Scripts\python -m unittest discover -s tests -v
```

Chỉ dùng `--snapshot` khi các file vector local chưa tồn tại. Nếu đã có ảnh/vector, chạy không có `--snapshot` để đối chiếu PDF/ảnh, không ghi đè corpus metadata. SHA256 ảnh có thể phụ thuộc phiên bản renderer/Pillow nên cần dùng đúng lock; báo lỗi rõ nếu khác, không bỏ kiểm tra.

## Tạo index từ đầu

Các lệnh dưới dùng cho thí nghiệm mới; cần lưu kết quả cũ riêng. Không dùng để ghi đè một corpus/selection đã chốt rồi gọi đó là cùng lượt đánh giá:

```powershell
.venv\Scripts\python -m src.bonus_ingest render --pdf "C:\Users\Think Pad\Downloads\BCTN-2025.pdf"
.venv\Scripts\python -m src.bonus_ingest caption --workers 6
.venv\Scripts\python -m src.bonus_ingest embed
```

Caption và embedding gọi OpenRouter, gửi ảnh/text tài liệu và phát sinh phí. Lỗi không fallback mock. Mọi trang được index; coverage và các giới hạn extraction ở `data/bonus/coverage.json` và manifest. Nhãn evidence/ảnh được kiểm chứng từ bản gốc, không coi caption tự sinh là đúng mặc định.

## Dev, audit, chốt và test

Benchmark cố định `benchmark/bonus_cases.json`: dev 15 câu có đáp án + 3 câu thiếu evidence; test 24 + 6. Nhóm test: bảng 6, ảnh/sơ đồ 5, biểu đồ 5, multi-hop 4, text 4; mỗi câu đúng một nhóm chính. Nhiều câu có thể cùng trang nhưng yêu cầu thông tin khác; cùng corpus, không coi là test ngoài miền. Schema evidence giữ page, page_id, region, bbox chuẩn hóa, quote, image hash và phép tính. Với multi-hop cần đủ các thành phần evidence; cho phép nguồn thay thế thực sự tương đương, người chấm phải ghi lý do.

```powershell
.venv\Scripts\python -m src.bonus run --split dev --config all --workers 4
```

Đọc từng câu, đối chiếu ảnh gốc và ghi `results/bonus/dev/<config>/reviews.json`. Mỗi record có `query_id`, `passed` boolean, `reason`, `original_page_check` (các trang/vùng đã đọc), `trace_sha256`, `benchmark_sha256`, `reviewer_kind`, `student_confirmed`. Không tự sinh nhãn từ score hay ID. Bản hiện tại có nhãn AI hỗ trợ, chưa tự coi là xác nhận của học viên.

```powershell
.venv\Scripts\python -m src.bonus audit --split dev --config all
.venv\Scripts\python -m src.bonus freeze
.venv\Scripts\python -m src.bonus run --split test --workers 4
```

Tiêu chí chốt: số câu dev được audit đạt cao hơn; sau đó chi phí chat thấp hơn, median latency thấp hơn, rồi tên cấu hình. Protocol lưu trước dev; test kiểm tra hash source/corpus/benchmark và chỉ chạy cấu hình chọn. Lệnh freeze chỉ dùng một lần cho mỗi thí nghiệm. Không sửa pipeline theo test; nếu làm vậy phải tạo test mới.

Sau khi đọc toàn bộ test, ghi nhãn cùng schema và chạy audit cho cấu hình đã chọn, ví dụ:

```powershell
.venv\Scripts\python -m src.bonus audit --split test --config vision
```

Đạt bonus khi có ít nhất 27/30 câu đạt và hoàn thành các điều kiện tài liệu/index/benchmark/tái lập của ADVANCED.md. Status `answered` hay `abstain` không tự quyết định đạt: câu thiếu evidence có thể nêu rõ không có thông tin, nhưng không được kèm khẳng định thiếu căn cứ. Không làm tròn tỷ lệ để qua 90%.

## Phạm vi kiểm chứng

Caption toàn bộ trang được tạo tự động; tính đúng đắn ngữ nghĩa toàn bộ 232 caption không được bảo đảm. Các trang evidence của benchmark và citation khi chấm được đọc ảnh gốc; ảnh hình người/trang trí không dùng thay cho nhóm sơ đồ. PDF nguồn 232 trang có text/bảng/sơ đồ/biểu đồ hữu ích; không chỉ lấy các trang benchmark để index. Các thành phần chưa được kiểm tra độc lập được công bố trong báo cáo; không ghi `student_confirmed=true` nếu học viên chưa đọc.
