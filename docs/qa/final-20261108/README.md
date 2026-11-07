# Final gate — 2026-11-08

Tổng hợp số thực đo của đợt gate cuối cùng trên branch `develop2`.

## Bảng gate

| Gate | Kết quả |
| --- | --- |
| Backend full | **1430/1430, 1453,52s** tại `c1da7d6` (`_review/audit-20261108/backend-full.log`) |
| Backend lint/build | pass |
| Frontend unit | **347/347, 54,16s** |
| Frontend lint/format/build | pass (build 773ms) |
| Frontend audit | 0 vulnerabilities |
| Root npm audit | 2 low / 0 high |
| OpenAPI | 82 paths; `export_openapi.py --check` khớp runtime |
| Root inventory | `api-routes.json` và `frontend-routes.json` khớp nguồn |
| Browser default | **3/3, 221,0s** (local-smoke × 3) |
| Browser fake × 3 | **39/39, 1116,35s** — trích từ `_review/audit-20261107/fake-gate-2.log`, không đổi code fake provider |
| Live targeted | **1/1, 39,7s** dùng 2 call #[77], #[78]; ledger **78/80**, còn **2 reserve** |
| Fresh clone không `.env` | kh có xuất, `git clone --local`, `npm ci` root+frontend, `npm start`, 4 lượt demo login ok, 80 concepts; `npm run stop` với data còn nguyên |

## Điều đã trích dẫn chứ không chạy lại

- Browser fake × 3 đã chạy tại `e51dd59`; từ đó đến giờ không thay đổi code
  fake provider nên không chạy lại một lần nữa.
- Backend full đã có `1429/1429` tại `700f19a`; lượt mới tại `c1da7d6` là
  **1430/1430** vì thêm một test.
- `diagrams:check` **không chạy** ở gate này: `docs/diagrams/schema-catalog.json`
  cần regenerate sau thay đổi schema, việc này được tách khỏi gate ngữ hiện
  tại để không ảnh hưởng tới final gate khác.

## Live / run cap

- Từ 70/80 trước, chạy 4 call trong ngày (#71–#78), giữ 2 call cuối làm reserve.
- Không chạy kịch bản 16 lượt vì ngân sách không đủ; chỉ có targeted 1 bài
  thực + 1 evaluation thực.

## Nguồn dẫn

- `_review/audit-20261108/backend-full.log`
- `_review/audit-20261108/browser-default.log`
- `_review/audit-20261108/live-confirmation.json`
- `_review/audit-20261108/fresh-clone-probe.json`
- `_review/audit-20261107/fake-gate-2.log`
