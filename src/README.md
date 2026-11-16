# Code Day 7

| File | Chức năng |
|---|---|
| `prepare.py` | Nhập snapshot Day 6, kiểm tra schema/evidence, tạo benchmark 24 câu |
| `provider.py` | HTTP OpenRouter, embeddings và chat, retry và usage; không in secret |
| `retrieval.py` | TF-IDF, dense Qdrant collection C, hybrid RRF |
| `agent.py` | Model gọi native search/finish; quản lý context và citation |
| `experiments.py` | Bốn cấu hình dev, chốt theo tiêu chí, chạy baseline/selected test |
| `audit.py` | Kiểm tra và tổng hợp nhãn đã đọc/chấm, không tự sinh điểm |
| `ask.py` | Hỏi một câu ngoài benchmark, lưu trace |
| `rebuild.py` | Khôi phục vector snapshot offline hoặc tái tạo bằng embedding thật |
| `common.py` | JSON, hash và chuẩn hóa evidence |
| `bonus_ingest.py` | Text/ảnh/caption toàn bộ 232 trang FPT, embedding và Qdrant riêng |
| `bonus.py` | Agent đọc ảnh sau hybrid retrieval; dev/freeze/test và audit bonus |

Hướng dẫn: [LAB_RUN.md](../LAB_RUN.md). Mã starter gốc được giữ để đối chiếu. Bài triển khai dùng `python -m src.experiments`, không chạy trực tiếp file module bằng đường dẫn.

Bonus: [BONUS_RUN.md](../BONUS_RUN.md). `scripts/restore_bonus_assets.py` khôi phục ảnh từ PDF có đúng SHA và snapshot vector; không thay metadata đã chốt. `scripts/finalize_lab.py` kiểm chứng kết quả/nhãn đã có và tạo báo cáo, không tự chấm điểm câu trả lời.
