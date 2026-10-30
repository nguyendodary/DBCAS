# Contributing — DBCAS

## Git Commit Convention

Repo này áp dụng **Conventional Commits**. Mọi commit phải theo format:

```
<type>(<scope>): <description>

<body>

<footer>
```

Ví dụ:

```
feat(auth): add login with email and JWT

- Add POST /api/v1/auth/login endpoint
- Issue JWT access token on valid credentials

Closes #12
```

### Type

| Type | Ý nghĩa | Ví dụ |
|---|---|---|
| `feat` | Tính năng mới | `feat(assessment): start adaptive session` |
| `fix` | Sửa lỗi | `fix(api): handle null response error` |
| `docs` | Chỉ đổi tài liệu/code comment | `docs(readme): update quickstart` |
| `style` | Định dạng code, không đổi logic | `style(frontend): format with prettier` |
| `refactor` | Tái cấu trúc, không thêm tính năng/sửa lỗi | `refactor(auth): simplify token logic` |
| `test` | Thêm/sửa test | `test(backend): add session tests` |
| `chore` | Việc lặt vặt: deps, config | `chore(deps): bump fastapi` |
| `perf` | Cải thiện hiệu năng | `perf(db): index selection_log` |
| `ci` | Thay đổi CI/CD | `ci(deps): pin tool versions` |
| `build` | Thay đổi build | `build(vite): add production config` |

### Scope

Scope là thư mục hoặc module bị ảnh hưởng. Dùng các scope của repo:

- `backend`, `frontend`, `db`, `sandbox` — theo thư mục gốc
- `auth`, `assessment`, `question`, `competency`, `admin`, `config`, `deps` — theo module
- Bỏ scope nếu thay đổi ảnh hưởng toàn repo (`docs: update README`)

### Description

- Tối đa 50–72 ký tự, viết thường, không chấm câu cuối.
- Dạng mệnh lệnh, bắt đầu bằng động từ: `add`, `fix`, `update`, `remove`.
- Tiếng Anh.

### Body & Footer

- Body: chỉ thêm khi description chưa đủ; mỗi dòng ≤72 ký tự, gạch đầu dòng `-`.
- Footer: `Closes #<id>`, `Fixes #<id>`, `BREAKING CHANGE: <mô tả>`.

### Quy tắc

1. Một commit = một việc. Không trộn fix + feat.
2. Chạy `git diff` trước khi commit; không commit `console.log`, secret, file rác.
3. Không commit file môi trường (`.env`) hay tài liệu dự án chung (docx/pdf) vào repo. Ngoại lệ: các tài liệu học thuật chính thức đã được duyệt trong `docs/academic/` — bốn tài liệu `.docx` theo quy ước `C1SE.70_<TênTàiLiệu>_DBCAS_ver<phiên bản>.docx` (`C1SE.70_ProposalDocument_DBCAS_ver1.1.docx`, `C1SE.70_UserStoryDocument_DBCAS_ver1.1.docx`, `C1SE.70_ArchitectureDesign_DBCAS_ver1.1.docx`, `C1SE.70_DatabaseDesign_DBCAS_ver1.1.docx`), các bản revision đã duyệt, PDF liên quan, diagram và tài liệu hỗ trợ đi kèm. Chỉ đặt các tệp này trong `docs/academic/`; không commit bản nháp, bản sao lưu, tài liệu cá nhân hoặc tệp ngoài thư mục đó.
4. Không thêm trailer credit của AI/tool vào commit (`Co-Authored-By`, `Generated with ...`). Commit chỉ ghi author là người trong team — trailer co-author làm bot xuất hiện trong danh sách Contributors trên GitHub.

## Commit Attribution Policy

Trước khi tạo BẤT KỲ commit nào, người commit và coding agent (tool hỗ trợ) PHẢI đọc file này.

Commit message PHẢI theo Conventional Commits ở trên và KHÔNG được chứa trailer credit của AI/tool. Cấm các dạng sau (không phân biệt hoa thường):

- `Co-Authored-By:` cho AI assistant / coding agent / bot
- `Generated with ...`
- `Generated-by:` / `Generated-By:`
- `AI-generated-by:` / `AI-assisted-by:`
- `Assisted-by:` trỏ tới AI/tool
- Credit cho Devin, ChatGPT, Claude, OpenAI, Cursor, Copilot hoặc tool tương tự

Commit chỉ ghi author/committer là người trong team. Không chèn branding hay quảng cáo tool vào commit message. Không chỉnh sửa author/committer date.

Repo có sẵn hook kiểm tra ở `.githooks/commit-msg`. Bật một lần sau khi clone:

```bash
git config core.hooksPath .githooks
```

## Diagrams and generated inventories

Updating an architecture figure means editing a small text source and re-running one command —
never redrawing an image by hand.

```
npm ci                     # pinned @mermaid-js/mermaid-cli 12.0.0 and @viz-js/viz 3.31.0
npm run diagrams:check     # every source parses, every committed SVG matches, ledgers + DDL validate
npm run diagrams:render    # rewrite the committed SVGs and docs/diagrams/rendered/manifest.json
npm run diagrams:setup     # report pinned versions, browser, Graphviz, Java and PlantUML status
npm run inventory:check    # docs/inventory/*.json still match routers/*.py and App.jsx
npm run inventory:write    # regenerate those two generated inventories
```

- Sources live in `docs/diagrams/*.dot`, Mermaid fences in project Markdown and
  `docs/diagrams/sources/*.{mmd,puml,iuml}`. `docs/diagrams/README.md` explains which artifacts are
  generated and which are authored; `docs/inventory/README.md` does the same for the route files.
- `docs/diagrams/physical-schema.dot` is **generated** from `db/schema.sql`; change
  `scripts/generate_schema_catalog.py` or the FK ledger instead of editing the DOT file by hand.
- Diagram ledgers keep every original element. Adding, changing or removing a flow requires its own
  `evidence` and `reason`; a removal also requires a justification, and `scripts/validate_diagrams.py`
  fails the gate without one. Never replace an existing diagram with an unrelated new one.
- Nothing downloads a browser, disables the Chromium sandbox, writes to a database or contacts a
  provider. Tooling failure is reported as a limitation; the gate is never weakened to pass.

## Branching

- `main` — bản ổn định, chỉ nhận merge từ `develop` qua Pull Request.
- `develop` — nhánh tích hợp chung; mọi nhánh công việc merge về đây trước.
- `frontend` — nhánh phát triển của team frontend.
- Nhánh công việc tạo từ `develop` (hoặc `frontend` cho việc frontend): `feat/<short-name>`, `fix/<short-name>` (vd. `feat/adaptive-session`).
- Xong việc → mở Pull Request về nhánh cha, không push trực tiếp lên `main`.

| Commit tệ | Commit chuẩn |
|---|---|
| `fix stuff` | `fix(ui): correct button alignment on mobile` |
| `update` | `feat(assessment): add question timer` |
| `add login` | `feat(auth): implement login with email` |
