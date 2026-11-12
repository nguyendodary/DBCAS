# W2 administrator screenshots — final 2026-11-13

All captures were produced by `../audit.mjs` against the running demo
(<http://localhost:18080>, API <http://localhost:18000>) with a real Chromium
viewport of **1280×900** or **390×900**. The PNG width was asserted to equal the
CSS viewport width. Every capture also asserted:

- `document.documentElement.scrollWidth <= window.innerWidth + 1` (no page-level
  horizontal overflow), and
- file size > 5 KB (non-blank capture).

Full-page captures have variable heights; the exact height is recorded below.
The DOM overflow and page-error checks are in `../results.json`.

## Required sets (4 each = 20)

| State | Files |
| --- | --- |
| Dashboard | `dashboard-vi-{light,dark}-{1280,390}.png` |
| Review detail (pending) | `review-detail-vi-{light,dark}-{1280,390}.png` |
| Accounts | `accounts-vi-{light,dark}-{1280,390}.png` |
| System | `system-vi-{light,dark}-{1280,390}.png` |
| CSV state | `csv-state-vi-{light,dark}-{1280,390}.png` |

## Complete index (37 files)

| File | State | Dimensions (px) | Theme | Bytes | Overflow |
| --- | --- | --- | --- | ---: | --- |
| `learner-review-waiting-vi-light-1280.png` | learner review waiting | 1280×900 | light | 58,933 | no |
| `learner-review-waiting-vi-light-390.png` | learner review waiting | 390×900 | light | 48,678 | no |
| `learner-review-waiting-vi-dark-1280.png` | learner review waiting | 1280×900 | dark | 59,742 | no |
| `learner-review-waiting-vi-dark-390.png` | learner review waiting | 390×900 | dark | 49,879 | no |
| `review-detail-vi-light-1280.png` | review detail | 1280×5405 | light | 845,796 | no |
| `review-detail-vi-light-390.png` | review detail | 390×8823 | light | 782,095 | no |
| `review-detail-vi-dark-1280.png` | review detail | 1280×5405 | dark | 986,054 | no |
| `review-detail-vi-dark-390.png` | review detail | 390×8823 | dark | 878,992 | no |
| `review-sql-check-vi-dark-390.png` | review sql check | 390×900 | dark | 148,219 | no |
| `review-detail-published-vi-light-1280.png` | review detail published | 1280×5454 | light | 857,874 | no |
| `review-detail-published-vi-light-390.png` | review detail published | 390×8784 | light | 791,834 | no |
| `review-detail-published-vi-dark-1280.png` | review detail published | 1280×5454 | dark | 998,834 | no |
| `review-detail-published-vi-dark-390.png` | review detail published | 390×8784 | dark | 889,424 | no |
| `learner-evaluation-approved-vi-light-1280.png` | learner evaluation approved | 1280×2454 | light | 202,929 | no |
| `learner-evaluation-approved-vi-light-390.png` | learner evaluation approved | 390×2940 | light | 183,989 | no |
| `learner-evaluation-approved-vi-dark-1280.png` | learner evaluation approved | 1280×2454 | dark | 208,814 | no |
| `learner-evaluation-approved-vi-dark-390.png` | learner evaluation approved | 390×2940 | dark | 191,211 | no |
| `learner-evidence-approved-vi-light-1280.png` | learner evidence approved | 1280×1493 | light | 553,922 | no |
| `learner-evidence-approved-vi-light-390.png` | learner evidence approved | 390×3025 | light | 455,111 | no |
| `learner-evidence-approved-vi-dark-1280.png` | learner evidence approved | 1280×1493 | dark | 651,156 | no |
| `learner-evidence-approved-vi-dark-390.png` | learner evidence approved | 390×3025 | dark | 511,135 | no |
| `accounts-vi-light-1280.png` | accounts | 1280×900 | light | 105,754 | no |
| `accounts-vi-light-390.png` | accounts | 390×1028 | light | 79,321 | no |
| `accounts-vi-dark-1280.png` | accounts | 1280×900 | dark | 285,975 | no |
| `accounts-vi-dark-390.png` | accounts | 390×1050 | dark | 169,097 | no |
| `system-vi-light-1280.png` | system | 1280×900 | light | 134,605 | no |
| `system-vi-light-390.png` | system | 390×1220 | light | 109,207 | no |
| `system-vi-dark-1280.png` | system | 1280×900 | dark | 294,013 | no |
| `system-vi-dark-390.png` | system | 390×1220 | dark | 164,788 | no |
| `dashboard-vi-light-1280.png` | dashboard | 1280×16646 | light | 2,357,093 | no |
| `dashboard-vi-light-390.png` | dashboard | 390×18794 | light | 1,543,873 | no |
| `dashboard-vi-dark-1280.png` | dashboard | 1280×17457 | dark | 2,541,429 | no |
| `dashboard-vi-dark-390.png` | dashboard | 390×18486 | dark | 1,649,372 | no |
| `csv-state-vi-light-1280.png` | csv state | 1280×900 | light | 103,613 | no |
| `csv-state-vi-light-390.png` | csv state | 390×900 | light | 65,443 | no |
| `csv-state-vi-dark-1280.png` | csv state | 1280×900 | dark | 372,692 | no |
| `csv-state-vi-dark-390.png` | csv state | 390×900 | dark | 192,600 | no |

## Notes

- `dashboard-*` and `review-detail-*` are full-page captures; the heights above
  are the full document heights. `csv-state-*` is a viewport capture scrolled to
  the **Thống kê và báo cáo** panel, with the CSV export control visible.
- `review-detail-published-*` is the same review after approval, showing the
  release audit and score-edit history.
- `learner-*` captures are supporting evidence for the Flow 2 waiting/approved
  states and the evidence page; they are not part of the required 20.
- `review-sql-check-vi-dark-390.png` is the post-success state of the
  read-only SQL check at the mobile viewport, captured before the page was
  scrolled to the SQL card. The success text and row/ms values are recorded in
  `../results.json` (checkpoint “admin SQL read-only check runs on a real
  pending SQL review”).
- No screenshot required an overflow waiver: all 37 have `overflow=false`.
