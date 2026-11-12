# Task 3.3 — Tích hợp chấm tự luận AI

Trạng thái đầu: **Đã có đầy đủ luồng chính**. Review: REST provider, rubric/JSON,
timeout/retry, cache, lưu attempt/job/review và trần 2048 token đạt; chất lượng
provider boundary/PII/strict domain đạt; test transport/persistence đầy đủ.
Thiếu validation giới hạn cấu hình retry/timeout và OpenAPI mã 502; tài liệu
tiếng Việt cần mô tả giới hạn/review rõ hơn.

Kế hoạch/thực hiện: thêm Field bounds hữu hạn cho timeout/retry/backoff, bổ sung
502 vào schema lỗi, test DN cho cấu hình và trần token/cache thay rubric; tạo
`docs/essay-ai-dn.md` và export contract. Không đổi prompt/rubric hoặc nới kiểm
định để chấp nhận model trả sai. Phụ thuộc LLMService/cache/review hiện hữu.

Kiểm tra: lint/build/OpenAPI/diff check đạt; **132 passed** llm/release/essay/
provider compatibility/DN. Có retry 429/5xx/timeout, deterministic 4xx, JSON sai,
NaN/điểm ngoài band, evidence giả/nhóm sai, PII, missing provider, cache và lưu DB.
Chạy: `python backend/manage.py test tests/test_llm.py tests/test_llm_release.py tests/test_essay_grading.py tests/test_provider_compatibility.py tests/dn/test_essay_contracts.py`.

Giả định: provider tương thích chat completions, key qua env. Không gọi LLM thật
hoặc phát sinh chi phí; chất lượng mô hình/khả dụng thực tế cần gate live riêng.
Giới hạn Retry-After chưa hỗ trợ được ghi rõ, không cản hợp đồng retry hữu hạn.
Không còn thiếu hụt Task 3.3. Commit: `Task 3.3: bound AI grading policy and verify rubric-aware caching`.
