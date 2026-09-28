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
| `ci` | Thay đổi CI/CD | `ci(github): add lint workflow` |
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
3. Không commit file môi trường (`.env`) hay tài liệu dự án (docx/pdf) vào repo.

## Branching

- `main` — baseline ổn định. Không push trực tiếp WIP.
- Nhánh công việc: `feat/<short-name>`, `fix/<short-name>` (vd. `feat/adaptive-session`).
- Merge về `main` qua Pull Request.

| Commit tệ | Commit chuẩn |
|---|---|
| `fix stuff` | `fix(ui): correct button alignment on mobile` |
| `update` | `feat(assessment): add question timer` |
| `add login` | `feat(auth): implement login with email` |
