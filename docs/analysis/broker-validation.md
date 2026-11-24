# PR #80 validation record (broker runtime)

**Ngày 2026-11-21.** Tài liệu ghi kết quả xác thực; không thay đổi code/flag. Production **HOLD**. #80 (`feat/broker-runtime`, head `2bd04170a206c3bdf9840274ffb6f3d11674d486`) vẫn MỞ.

> **Cập nhật 2026-11-24:** chủ sở hữu yêu cầu hợp nhất `feat/broker-runtime` vào `develop2` trong đợt dọn nhánh. Các kết luận và GAP bên dưới vẫn là kết quả xác thực tại thời điểm đó; flag `SANDBOX_BROKER` vẫn mặc định **OFF**, chưa có probe runtime thật được bật từ CI, và cutover B2 (tách broker thành service riêng, bỏ Docker CLI/socket khỏi API) cùng B3 (writable) vẫn là điều kiện trước khi cân nhắc bật. Production vẫn **HOLD**.

## 1. Static review (Phase 1)

| Hạng mục | Kết luận | Trích dẫn |
| --- | --- | --- |
| Flag OFF byte-identical; 2 slot / 5 s không đổi | Đạt | `backend/app/config.py:77,99`; `backend/app/services/ephemeral_sandbox.py:22-23,103`; `backend/app/worker.py:36-41` |
| Hash SQL/setup được tính lại trước runtime | Đạt | `backend/app/services/broker/service.py:147-150,160`; `client.py:63-64,70-71` |
| Replay ledger có giới hạn 1000 | Đạt | `service.py:115-116,125-128` |
| Reaper chỉ xóa lease hết hạn do broker tạo | Đạt | `backend/app/services/broker/runtime.py:76,79-81,91-101` |
| Dataset digest theo `dataset_id` | Đạt | `service.py:151-152`; `client.py:54-62` |
| Container flags (`none`, read-only+tmpfs, UID 10001, cap-drop ALL, no-new-privileges, pids/mem/cpu) | Đạt | `runtime.py:39,43-56`; `service.py:22-26` |
| Error message rò rỉ host path/tên container/SQL | Không có bằng chứng; có kênh latent (message truyền thẳng) | `runtime.py:72`; `ephemeral_sandbox.py:187-188`; `sql_service.py:50-51,59-60`; mọi message broker là literal tĩnh (`service.py:91,106,148,150,152,158,193,195,201,215`) |
| docker.sock/Compose/Dockerfile/CI không đổi trong #80; không có secret | Đạt | `git diff develop2...2bd0417 --name-only`; secret scan 0 finding |

## 2. Độ phủ test runtime thật (Phase 1)

| Probe | Docker thật trong CI? | Broker ON? | Trích dẫn |
| --- | --- | --- | --- |
| Escape/network probe của broker | **KHÔNG** (fake docker) | Không | `backend/tests/test_broker_runtime.py:122-149` (fake tại `:134`) |
| Resource abuse (memory/CPU/pids) của broker | **KHÔNG** (chỉ assert argv) | Không | `test_broker_runtime.py:144` |
| Cross-user lease isolation | **KHÔNG** | Không | chỉ admission semaphore `test_broker_runtime.py:51-63` |
| Reaper/crash recovery | **KHÔNG** (fake, lease chèn tay) | Không | `test_broker_runtime.py:147-149` |
| Probe legacy có Docker thật | Có | Không | `backend/tests/dn/test_ephemeral_sandbox.py:37-45,71-84` |
| Mọi test broker (`test_broker_*`) | Không — `FakeRuntime`/fake docker | Không | `test_broker_runtime.py:1,69,85,105,134,158`; `test_broker_skeleton.py:1,195-203` |

**GAP:** chưa có probe escape/abuse/isolation/reaper nào chạy với runtime thật; `SANDBOX_BROKER` chưa thể bật từ CI (xem `[broker README](../sql-sandbox/broker/README.md)` và `dn-backend.yml:102,104`).

## 3. CI validation broker ON (Phase 2)

Draft PR [#81](https://github.com/nguyendodary/DBCAS/pull/81) (đã đóng) bật `SANDBOX_BROKER=true`, `SANDBOX_BROKER_RUNTIME=docker` qua env workflow; head `cc966a5`; [run 44907556308](https://github.com/nguyendodary/DBCAS/actions/runs/44907556308) — **failure**.

| Chỉ số | OFF (baseline [run 44903786066](https://github.com/nguyendodary/DBCAS/actions/runs/44903786066)) | ON (run 44907556308) |
| --- | --- | --- |
| Jobs | 14/14 pass | 11 pass, backend + qa-3 + frontend-local fail |
| Backend | 1896 passed | 1888 passed, 8 failed |
| qa-1 `concurrent_sql` | 8 request / 8 success / 0 503; p50 3202.74 ms, p95 6309.65 ms; N=8 | 10 request / 8 success / 2 HTTP 503; p50 3382.31 ms (+5.6%), p95 5111.26 ms; N=10 |
| Diagnostics 503 | — | **Không có `sandbox_busy rejection` trong log** → 503 chưa giải thích được |
| Container leak | compose cleanup xóa network/volume | compose cleanup xóa network/volume; `docker ps` trực tiếp **UNKNOWN — owner must confirm** |
| Reaper evidence | — | Không có log reaper runtime thật |

Backend failures ON: 4 test `dn/test_ephemeral_sandbox.py` (legacy path đổi sang broker), `test_flag_off_is_byte_identical`, 2 test fail-closed/health của B1 (giả định flag OFF), `test_shared_auth.py` production startup. qa-3: Playwright `practice-flows.spec.js:55` timeout chờ heading “Nhận xét” (không phải #67/#63/#71). Log đã lưu tại `_review/merge-20261121/validation-on-*.log`.

## 4. Tiêu chí merge (Phase 3)

| Tiêu chí | Kết quả |
| --- | --- |
| a. CI xanh + job ON xanh, 503 được giải thích | **FAIL** |
| b. Probe escape/abuse/isolation/reaper chạy với broker ON | **FAIL** |
| c. Không leak container; p50 ON không quá +25% | p50 +5.6% đạt; leak/reaper **UNKNOWN** |
| d. #80 không đổi flag/socket/Compose/CI; không secret | **PASS** |
| e. Không còn MED/HIGH từ review tĩnh | **PASS** |

**Kết luận: KHÔNG merge #80.** Cần bổ sung probe runtime thật và giải thích 503 trước khi xét lại.
