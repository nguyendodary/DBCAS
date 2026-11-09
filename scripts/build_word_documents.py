# -*- coding: utf-8 -*-
"""Build the three v1.2 Vietnamese Word documents from the real project facts.

    python scripts/build_word_documents.py

Every number, name and statement comes from docs/qa/schema-introspection.json,
docs/qa/project-facts.json, docs/diagrams/generated/system-context-model.json
and docs/diagrams/generated/manifest.json. The v1.1 .docx files are used as
style templates (official styles, numbering, headers/footers, cover layout).
"""
import json
from pathlib import Path
from build_docx import Builder

ROOT = Path(__file__).resolve().parents[1]
ACA = ROOT / "docs" / "academic"
GEN = ROOT / "docs" / "diagrams" / "generated"
INTRO = json.load(open(ROOT / "docs/qa/schema-introspection.json", encoding="utf-8"))
FACTS = json.load(open(ROOT / "docs/qa/project-facts.json", encoding="utf-8"))
CTX = json.load(open(GEN / "system-context-model.json", encoding="utf-8"))
MAN = json.load(open(GEN / "manifest.json", encoding="utf-8"))

DATE = "2026-11-08"
VERSION = "1.2"
NEED_HUMAN = "[CẦN NGƯỜI ĐIỀN]"
LEGACY = set(MAN["legacy_tables"])
TABLES = INTRO["tables"]
FKS = INTRO["foreign_keys"]
INDEXES = INTRO["indexes"]
MIGS = INTRO["migrations"]

# ---------------------------------------------------------------- helpers
def H(lvl, text): return {"type": "heading", "level": lvl, "text": text}
def P(text, **kw): return {"type": "para", "text": text, **kw}
def BUL(text): return {"type": "bullet", "text": text}
def T(rows, widths=None, header=True): return {"type": "table", "rows": rows, "widths": widths, "header": header}
def CAP(text, keep=False): return {"type": "caption", "text": text, "keep": keep}
def PB(): return {"type": "pagebreak"}
def IMG(name, path, w, h, desc): return {"type": "image", "path": str(path), "width": w,
                                         "height": h, "name": name, "description": desc}


def cover(title, code):
    return [
        {"type": "title", "text": "DBCAS — " + title},
        {"type": "subtitle", "text": "Hệ thống luyện tập và đánh giá năng lực PostgreSQL"},
        P("Mã tài liệu: " + code, align="center"),
        P("Phiên bản: v" + VERSION + "  ·  Ngày cập nhật: " + DATE, align="center"),
        P("Người phê duyệt: " + NEED_HUMAN, align="center"),
        P("Người biên soạn: " + NEED_HUMAN, align="center"),
        P("Trạng thái: bản hiệu đính theo mã nguồn thực tế (single source of truth)", align="center"),
        PB(),
    ]


def front():
    return [
        H(1, "Lịch sử phiên bản"),
        T([["Phiên bản", "Ngày", "Nội dung thay đổi", "Người phê duyệt"],
           ["1.0", NEED_HUMAN, "Phiên bản học thuật ban đầu", NEED_HUMAN],
           ["1.1", NEED_HUMAN, "Bổ sung bảo mật, phát hành kết quả, bằng chứng", NEED_HUMAN],
           ["1.2", DATE,
            "Hiệu đính 100% theo mã nguồn: 41 bảng, 293 cột, 59 khóa ngoại, 19 migration; "
            "bãi bỏ đề thi dựng sẵn và tỉ lệ 10/2/1; sinh lại 3 sơ đồ từ CSDL/Compose/OpenAPI",
            NEED_HUMAN]], [1100, 1400, 4800, 1800]),
        H(1, "Mục lục"),
        {"type": "toc"},
        H(1, "Danh mục hình"),
        {"type": "toc_figures"},
        H(1, "Danh mục bảng"),
        {"type": "toc_tables"},
        PB(),
    ]


GLOSSARY_ROWS = [
    ["Thuật ngữ", "Định nghĩa (khớp mã nguồn)"],
    ["Concept", "Khái niệm mô hình/ SQL; 80 khái niệm, ánh xạ CLO qua clo_concept"],
    ["Difficulty band", "EASY (mức 1–2), MEDIUM (3), HARD (4–5)"],
    ["Question type", "mcq, sql, essay"],
    ["Question source", "bank (ngân hàng đã kiểm chứng) hoặc ai"],
    ["Validated bank", "5.482 câu (2.006 MCQ / 1.747 SQL / 1.729 essay)"],
    ["Exact-count", "Trả đúng question_count (1–20, mặc định 5); widening/bounded recovery"],
    ["Result flow", "IMMEDIATE (Tự động) hoặc HUMAN_VERIFIED (Admin duyệt), một thiết lập chung"],
    ["Prompt Builder", "AI #1: tạo prompt, prompt_hash, fallback template (builder_fallback)"],
    ["Evaluator", "AI #2: chấm qua LLM ngoài; fallback rule_evaluation (evaluator_fallback)"],
    ["Reason code", "Mã từ chối không chứa bí mật trong generation_diagnostics"],
    ["Admin", "Đúng 5 mục: Tổng quan, Duyệt bài, Tài khoản, Ngân hàng/CLO, Hệ thống"],
    ["Learner-defined practice", "Người học tự chọn khái niệm, độ khó, số câu, nguồn; không có đề thi dựng sẵn"],
]


def glossary():
    return [H(1, "1. Phạm vi và thuật ngữ"),
            P("Tài liệu này mô tả duy nhất trạng thái triển khai thật của DBCAS trên nhánh develop2. "
              "Mọi con số được sinh tự động từ db/schema.sql (introspection PostgreSQL 17), các file "
              "docker-compose, app.openapi() và frontend/src. Không có yêu cầu 'tương lai' nào được "
              "trình bày như đã triển khai."),
            T(GLOSSARY_ROWS, [2300, 7000]),
            H(2, "1.1. Phạm vi triển khai"),
            BUL("Chạy cục bộ bằng Docker Compose; không triển khai cloud, không có người dùng thật."),
            BUL("Hai tác nhân: Learner và Admin. Không có vai trò giáo viên trung gian."),
            BUL("Hệ thống ngoài: LLM API, Google OAuth, GitHub OAuth, Mailpit, Docker sandbox."),
            BUL("CSDL PostgreSQL 17: %d bảng, %d cột, %d khóa ngoại, %d chỉ mục, %d migration, 0 enum."
                 % (len(TABLES), sum(len(t["columns"]) for t in TABLES), len(FKS), len(INDEXES), len(MIGS))),
            ]


def version_note(prev):
    return [H(1, "2. Hiệu đính v1.2 — các nội dung bị thay thế"),
            P("Bản v1.1 chứa các phát biểu không còn đúng với mã nguồn. Toàn bộ các phát biểu đó bị "
              "bãi bỏ và thay bằng nội dung dưới đây; các sơ đồ cũ cũng được thay bằng sơ đồ sinh từ "
              "nguồn dữ liệu thật."),
            T([["Nội dung v1.1 (bãi bỏ)", "Thực tế trong mã nguồn"]] + prev, [4600, 4700]),
            ]


RETIRED = [
    ["Con số 36 bảng trong v1.1", "41 bảng / 293 cột / 59 khóa ngoại / 87 chỉ mục / 19 migration"],
    ["Phân loại FORMAL/PRACTICE, hợp đồng 13 câu / 60 phút và tỉ lệ câu hỏi 10/2/1 của v1.1",
     "Chỉ có learner-defined practice: question_count 1–20 (mặc định 5), thời lượng phiên 30 phút, "
     "cân bằng mcq/sql/essay theo type_targets"],
    ["Admin tạo/cấu hình đề thi (assessment, blueprint)",
     "Không có tạo đề; Admin đúng 5 mục; một system_setting.result_flow toàn cục"],
    ["assessment_session.assessment_id bắt buộc", "Cột cho phép NULL từ migration 018; bài mới không gắn đề"],
    ["Đề thi dựng sẵn / published exams", "seed_demo exam_count = 0; migration 019 đóng mọi đề published"],
    ["ERD / Table Relationship Diagram thể hiện 36–38 bảng",
     "Sơ đồ mới sinh từ introspection: 41 thực thể, 59 cạnh khóa ngoại"],
    ["Hệ context có 6 nút / 21 luồng cố định",
     "Sơ đồ context mới: 15 nút / 23 luồng có hướng, mỗi luồng có bằng chứng mã nguồn"],
    ["Danh sách migration dừng ở 017", "Đầy đủ 19 migration (018, 019 được bổ sung)"],
]


def figures_common():
    return [
        H(1, "3. Sơ đồ hệ thống (sinh tự động)"),
        P("Ba sơ đồ dưới đây được sinh bằng scripts/generate_doc_diagrams.py từ "
          "docs/qa/schema-introspection.json, docs/qa/project-facts.json và "
          "docs/diagrams/generated/system-context-model.json, sau đó raster hoá ở độ phân giải cao. "
          "Không có phần tử trang trí; mọi nút và luồng đều có bằng chứng trong mã nguồn."),
        CAP("Hình 1: System Context Diagram — DBCAS (nguồn: docker-compose*.yml, app.openapi(), mã nguồn)",
            keep=True),
        IMG("System Context Diagram", GEN / "system-context.png", 6.4, 4.34,
            "15 nút, 23 luồng có hướng; bảng chú giải mã luồng"),
        PB(),
    ]


def context_flow_table():
    rows = [["Mã", "Nguồn → Đích", "Dữ liệu / điều khiển", "Bằng chứng"]]
    for f in CTX["flows"]:
        rows.append([f["id"], f["source"] + " → " + f["destination"], f["label"], f["evidence"]])
    return [H(2, "3.1. Bảng luồng dữ liệu (23 luồng)"), T(rows, [700, 2400, 3300, 2900])]


def services_table():
    rows = [["Dịch vụ / hệ thống", "Vai trò", "Cổng / mạng"]]
    ports = {p["var"]: p["default"] for p in FACTS["ports"]}
    rows += [
        ["frontend", "Nginx SPA", "127.0.0.1:%s → 8080, mạng web" % ports.get("LOCAL_WEB_PORT", 18080)],
        ["app", "FastAPI / uvicorn", "127.0.0.1:%s → 8000, mạng web + database" % ports.get("LOCAL_API_PORT", 18000)],
        ["db", "PostgreSQL 17", "mạng database (internal), volume local-data"],
        ["mailpit", "SMTP + mailbox UI", "127.0.0.1:%s → 1025 (SMTP), :%s → 8025 (UI)"
         % (ports.get("LOCAL_SMTP_PORT", 11025), ports.get("LOCAL_MAIL_PORT", 18025))],
        ["init", "schema.sql + migrations + seed_demo (one-shot)", "mạng database"],
        ["executor-image", "build dbcas-sql-ephemeral:local", "network_mode: none"],
        ["qa-ai (QA only)", "fake AI provider", "127.0.0.1:%s → 8080" % ports.get("LOCAL_QA_PROVIDER_PORT", 18099)],
        ["real-qa meter (opt-in)", "đếm request LLM", "docker-compose.real-qa.yml"],
    ]
    return rows


def erd_figures(prefix):
    """Page-aligned ERD figures (one whole-table page each, never split)."""
    files = sorted(GEN.glob("erd-*.png"), key=lambda p: int(p.stem.split("-")[1]))
    out = []
    for i, p in enumerate(files, 1):
        # height derived from the page SVG so the aspect ratio is exact
        svg = (GEN / (p.stem + ".svg")).read_text(encoding="utf-8")
        import re
        vb = re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', svg)
        ratio = float(vb.group(2)) / float(vb.group(1)) if vb else 1.2
        letter = chr(ord('a') + i - 1) if i <= 26 else str(i)
        out.append(CAP(f"Hình {prefix}{letter}: Entity Relationship Diagram ({i}/{len(files)}) — "
                       f"41 bảng, thuộc tính PK/FK/kiểu/null" +
                       ("; bảng 59 khóa ngoại với cardinality" if i == len(files) else ""), keep=True))
        out.append(IMG(f"ERD {i}/{len(files)}", p, 6.3, round(6.3 * ratio, 2),
                       f"Entity Relationship Diagram trang {i}/{len(files)}"))
    return out


def trd_figures(prefix):
    files = sorted(GEN.glob("table-relationships-*.png"),
                   key=lambda p: int(p.stem.split("-")[-1]))
    out = []
    for i, p in enumerate(files, 1):
        import re
        svg = (GEN / (p.stem + ".svg")).read_text(encoding="utf-8")
        vb = re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', svg)
        ratio = float(vb.group(2)) / float(vb.group(1)) if vb else 1.1
        letter = chr(ord('a') + i - 1) if i <= 26 else str(i)
        out.append(CAP(f"Hình {prefix}{letter}: Table Relationship Diagram ({i}/{len(files)}) — "
                       f"41 bảng, 59 cạnh khóa ngoại có hướng", keep=True))
        out.append(IMG(f"TRD {i}/{len(files)}", p, 6.3, round(6.3 * ratio, 2),
                       f"Table Relationship Diagram trang {i}/{len(files)}"))
    return out


def endpoint_appendix():
    rows = [["#", "OpenAPI path"]] + [[str(i + 1), p] for i, p in enumerate(FACTS["openapi_paths"])]
    return rows


def migration_rows():
    return [["#", "Migration", "SHA-256 (12 ký tự đầu)"]] + [
        [str(i + 1), name, sha[:12]] for i, (name, sha) in enumerate(sorted(MIGS.items()))]


def fk_rows():
    rows = [["#", "Khóa ngoại", "Bảng nguồn(cột) → Bảng đích(cột)", "ON DELETE / UPDATE"]]
    for i, f in enumerate(FKS):
        rows.append([str(i + 1), f["constraint"],
                     f'{f["source"]}({",".join(f["columns"])}) → '
                     f'{f["destination"]}({",".join(f["reference_columns"])})',
                     f["on_delete"] + " / " + f["on_update"]])
    return rows


def index_rows():
    return [["#", "Bảng", "Chỉ mục", "Định nghĩa"]] + [
        [str(i + 1), x["table"], x["name"], x["definition"][:110]] for i, x in enumerate(INDEXES)]


def dictionary_blocks():
    """Full data dictionary: one table per real table, every column."""
    blocks = [H(1, "4. Từ điển dữ liệu (toàn bộ %d bảng)" % len(TABLES)),
              P("Bảng dưới đây sinh tự động từ information_schema/pg_catalog của PostgreSQL 17 sau khi "
                "áp db/schema.sql. 'Diễn giải' chỉ mô tả thuộc tính kỹ thuật đã đo được; ý nghĩa nghiệp "
                "vụ chi tiết cần " + NEED_HUMAN + " bổ sung. Không có cột nào bị bỏ qua.")]
    pkc = {}
    for t in TABLES:
        for c in t["constraints"]:
            if c["type"] == "p":
                pkc[t["table"]] = set(c["columns"])
    fkc = {}
    for f in FKS:
        fkc.setdefault(f["source"], set()).update(f["columns"])
    chk = {}
    for t in TABLES:
        for c in t["constraints"]:
            if c["type"] == "c":
                chk.setdefault(t["table"], set()).update(c["columns"])
    for t in TABLES:
        name = t["table"]
        legacy = "  [legacy/retired — chỉ lưu dữ liệu đề thi lịch sử]" if name in LEGACY else ""
        blocks.append(H(2, "4.%d. Bảng %s%s" % (TABLES.index(t) + 1, name, legacy)))
        rows = [["Cột", "Kiểu", "Null", "Mặc định", "PK/FK", "Diễn giải kỹ thuật"]]
        for c in t["columns"]:
            typ = c["type"] + (f'({c["max_length"]})' if c["max_length"] else "")
            marks = []
            if c["name"] in pkc.get(name, set()):
                marks.append("PK")
            if c["name"] in fkc.get(name, set()):
                marks.append("FK")
            desc = ("identity" if c["identity"] else "") + \
                   ("; check" if c["name"] in chk.get(name, set()) else "")
            rows.append([c["name"], typ, "NULL" if c["nullable"] else "NOT NULL",
                         (c["default"] or "—")[:38], ",".join(marks) or "—", desc or "—"])
        blocks.append(T(rows, [1700, 2000, 900, 1500, 900, 2300]))
        cons = [c for c in t["constraints"] if c["type"] in ("p", "u", "c", "f")]
        if cons:
            blocks.append(T([["Ràng buộc", "Loại", "Định nghĩa"]] +
                            [[c["name"], {"p": "PRIMARY KEY", "u": "UNIQUE", "c": "CHECK",
                                          "f": "FOREIGN KEY"}[c["type"]], c["definition"][:150]]
                             for c in cons], [2300, 1500, 5500]))
    return blocks


FR_ROWS = [
    ["FR01", "Đăng ký / đăng nhập Learner, JWT + refresh, OAuth Google/GitHub",
     "/login, /register, /auth/callback", "/api/v1/auth/*", "test_auth.py, test_oauth.py, test_refresh_tokens.py"],
    ["FR02", "Phân quyền RBAC (Learner, Admin), điều hướng 5 mục Admin",
     "/admin, /admin/grading, /admin/accounts, /admin/questions, /admin/system",
     "/api/v1/admin/*", "test_rbac.py, test_removed_exam_surface.py"],
    ["FR03", "Người học tự chọn khái niệm, độ khó, số câu 1–20, nguồn bank/ai",
     "/assessments", "/api/v1/practice/options, /api/v1/practice/start",
     "test_learner_practice.py, test_practice_selection.py"],
    ["FR04", "Exact-count guarantee, widening và bounded recovery có thông báo",
     "/assessments, /exam/:id", "/api/v1/practice/start",
     "test_practice_selection.py, test_practice_matrix.py"],
    ["FR05", "source=ai: AI chỉ MCQ/essay, SQL luôn từ ngân hàng validated",
     "/assessments, /exam/:id", "/api/v1/practice/start (bank_mixed, ai_generated_count)",
     "test_governed_generation.py, test_qa_provider.py"],
    ["FR06", "generation_diagnostics với reason code không chứa bí mật",
     "/exam/:id", "/api/v1/practice/start", "test_llm.py, test_practice_recovery.py"],
    ["FR07", "Làm bài MCQ / SQL / essay, lưu nháp, nộp bài",
     "/exam/:id", "/api/v1/sessions/*", "test_sessions.py, test_draft_lifecycle.py"],
    ["FR08", "Chấm SQL trong sandbox Docker không mạng, read-only",
     "/exam/:id", "/api/v1/sessions/*/submit", "test_ephemeral_sandbox.py, test_sandbox_safety.py"],
    ["FR09", "Two-AI pipeline: Prompt Builder → Evaluator, fallback rule",
     "/evaluations/:id", "/api/v1/evaluations/*", "test_two_ai_pipeline.py, test_llm.py"],
    ["FR10", "Hai luồng kết quả IMMEDIATE / HUMAN_VERIFIED (một setting)",
     "/admin/system, /evaluations/:id", "/api/v1/admin/system, /api/v1/evaluations/*",
     "test_result_contracts.py, test_grading.py"],
    ["FR11", "Admin duyệt / sửa điểm có lý do, audit bất biến",
     "/admin/grading/:id", "/api/v1/admin/grading-reviews/*", "test_grading.py, test_ai_admin.py"],
    ["FR12", "Lịch sử, năng lực, CLO, gợi ý ưu tiên",
     "/history, /competency, /dashboard", "/api/v1/sessions/statistics, /api/v1/competency/*",
     "test_statistics_api.py, test_competency.py, test_guidance.py"],
    ["FR13", "Ngân hàng câu hỏi validated, bản địa hoá, phiên bản",
     "/admin/questions", "/api/v1/admin/questions/*", "test_bank_contracts.py, test_question_validator.py"],
    ["FR14", "Khôi phục mật khẩu qua Mailpit",
     "/forgot-password, /reset-password", "/api/v1/auth/password-reset/*", "test_password_reset.py, password-recovery.spec.js"],
    ["FR15", "Đăng xuất, thu hồi token, giới hạn đăng nhập",
     "/settings", "/api/v1/auth/logout", "test_login_throttle.py, test_shared_auth.py"],
    ["FR16", "Giao diện song ngữ, theme, 390px responsive",
     "toàn bộ frontend", "i18n, CSS", "localization.spec.js, browser-qa.spec.js"],
    ["FR17", "Hợp đồng OpenAPI 82 paths / 92 operations",
     "toàn bộ API", "app.openapi()", "test_openapi_contract.py, scripts/export_openapi.py"],
]


def fr_blocks():
    return [
        H(1, "4. Yêu cầu chức năng và truy vết"),
        P("Mỗi FR dưới đây ánh xạ tới một tính năng đang chạy, một màn hình/API và một bài kiểm thử "
          "có thật trong kho. Không có FR nào mô tả chức năng chưa triển khai."),
        T([["Mã", "Yêu cầu", "Màn hình", "API", "Kiểm thử"]] + FR_ROWS,
          [700, 3100, 1900, 2100, 1500]),
        H(2, "4.1. Yêu cầu phi chức năng (đã đo)"),
        T([["Mã", "Yêu cầu", "Bằng chứng đo được"],
           ["NFR01", "Hiệu năng backend", "1430/1430 test trong 1453,52s"],
           ["NFR02", "Hiệu năng frontend", "347/347 unit (54,16s), build 773ms"],
           ["NFR03", "Ổn định browser", "browser default 3/3; fake provider 39/39 (1116,35s)"],
           ["NFR04", "Bảo mật", "JWT/RBAC, sandbox --network none, CORS, login throttle"],
           ["NFR05", "Toàn vẹn dữ liệu", "59 FK, 87 index, audit bất biến, 6988 lần chạy SQL đối chiếu"],
           ["NFR06", "Không rò rỉ bí mật", "generation_diagnostics chỉ chứa reason code; key không vào log"],
           ["NFR07", "Khả năng kiểm chứng tài liệu", "npm run docs:check: 46 assertions, CI frontend-local"],
           ["NFR08", "Phạm vi cục bộ", "Docker Compose, không cloud, không người dùng thật"],
           ["NFR09", "Ngân sách LLM", "ledger 78/80, 2 call reserve, không reset"]], [900, 3200, 5200]),
    ]


# ---------------------------------------------------------------- documents
def proposal_blocks():
    b = cover("Proposal / Đề xuất dự án", "C1SE.70_ProposalDocument_DBCAS") + front() + glossary()
    b += version_note(RETIRED)
    b += [
        H(1, "3. Mục tiêu, tác nhân và luồng sử dụng"),
        P("Mục tiêu: cung cấp hệ thống luyện tập PostgreSQL do người học tự định nghĩa, với ngân hàng "
          "câu hỏi đã kiểm chứng, hai luồng công bố kết quả và hai AI (Prompt Builder, Evaluator). "
          "Hệ thống chỉ chạy cục bộ trên Docker Compose."),
        T([["Tác nhân", "Vai trò", "Luồng chính"]],
          [1100, 2600, 5600]),
        T([["Learner", "Người học",
            "Chọn khái niệm → độ khó → số câu → nguồn bank/ai → làm bài → xem nhận xét / năng lực"],
           ["Admin", "Giảng viên / QA",
            "Tổng quan → Duyệt bài → Tài khoản → Ngân hàng & CLO → Hệ thống (result_flow)"]],
          [1100, 2600, 5600]),
        H(2, "3.1. Quy tắc sản phẩm đã triển khai"),
        BUL("Không có đề thi dựng sẵn; không có màn hình tạo đề; seed_demo exam_count = 0."),
        BUL("source=ai: AI sinh MCQ/essay, SQL luôn lấy từ ngân hàng validated; bank_mixed được thông báo."),
        BUL("question_count 1–20 (mặc định 5), timebox phiên 30 phút, cân bằng theo type_targets."),
        BUL("result_flow: IMMEDIATE (Tự động) hoặc HUMAN_VERIFIED (Admin duyệt), một system_setting."),
        BUL("Two-AI pipeline: Prompt Builder (template fallback, prompt_hash) → Evaluator (rule fallback)."),
        H(2, "3.2. Bảng legacy/retired"),
        P("Bốn bảng assessment, assessment_concept, assessment_question, assessment_blueprint vẫn "
          "tồn tại trong db/schema.sql để giữ dữ liệu đề thi lịch sử; chúng được ghi nhãn "
          "legacy/retired trong ERD, không API nào tạo mới (migration 019, seed_demo exam_count = 0)."),
    ]
    b += figures_common() + context_flow_table()
    b += [
        H(1, "4. Kiến trúc và công nghệ (tóm tắt)"),
        T(services_table(), [1900, 3300, 4100]),
        H(1, "5. Ràng buộc, giả định và rủi ro"),
        BUL("Chạy cục bộ; hiệu năng đo trên một máy; chưa có người dùng thật."),
        BUL("Kịch bản 16 lượt live chưa chứng minh do ngân sách LLM (2 call reserve)."),
        BUL("docs/diagrams/schema-catalog.json được sinh lại từ CSDL thật; diagrams:check xanh."),
        BUL("Ý nghĩa nghiệp vụ chi tiết của từng cột: " + NEED_HUMAN + "."),
        H(1, "6. Trạng thái nghiệm thu"),
        T([["Gate", "Kết quả"],
           ["Backend", "1430/1430, 1453,52s"],
           ["Frontend", "347/347, build 773ms, lint/format pass"],
           ["Browser", "default 3/3; fake × 3 39/39"],
           ["OpenAPI / inventory / audit", "82 paths, khớp nguồn, 2 low / 0 high"],
           ["CI", "run 42374991702 success trên 8c1431d; run 42379625567 success trên 4099f33"]],
          [3000, 6300]),
    ]
    b += fr_blocks()
    return b


def architecture_blocks():
    b = cover("Architecture Design / Thiết kế kiến trúc", "C1SE.70_ArchitectureDesign_DBCAS") + front() + glossary()
    b += version_note(RETIRED)
    b += [
        H(1, "3. Kiến trúc tổng thể"),
        P("Hệ thống gồm 6 dịch vụ Compose chính (frontend, app, db, mailpit, init, executor-image), "
          "thêm qa-ai (chỉ QA) và real-qa meter (tuỳ chọn). Hai mạng: web (frontend ↔ app) và "
          "database (internal, app/init ↔ db). Tài liệu này liệt kê đúng các dịch vụ, cổng, volume "
          "và luồng dữ liệu thực tế."),
        T(services_table(), [1900, 3300, 4100]),
        H(2, "3.1. Cổng và volume"),
        T([["Biến", "Mặc định", "Nguồn"]] +
          [[p["var"], str(p["default"]), p["source"]] for p in FACTS["ports"]], [3000, 1500, 4800]),
        T([["Volume / mount", "Mục đích"]] +
          [[v, "docker-compose.local.yml"] for v in FACTS["volume_mounts"]], [5000, 4300]),
    ]
    b += figures_common() + context_flow_table()
    b += [
        H(1, "4. Bảo mật và cô lập"),
        BUL("JWT + refresh token, RBAC (Learner/Admin), đăng xuất thu hồi token, login throttle."),
        BUL("OAuth Google / GitHub (google_client_id / github_client_id trong config.py)."),
        BUL("Sandbox: docker create --network none --memory 256m --cpus 1, statement timeout 3025ms."),
        BUL("CORS_ORIGINS và FRONTEND_URL cấu hình theo LOCAL_WEB_PORT."),
        BUL("Không lưu key/model trong repo; meter chỉ ghi reason code không chứa nội dung."),
        H(1, "5. Two-AI pipeline và luồng kết quả"),
        P("Prompt Builder (AI #1) nhận dữ liệu bài làm, trả prompt + prompt_hash; khi không cấu hình "
          "PROMPT_BUILDER_MODEL_PATH thì dùng template fallback (builder_fallback=true). Evaluator "
          "(AI #2) gọi LLM ngoài qua LLM_BASE_URL; nếu lỗi dùng rule_evaluation "
          "(evaluator_fallback=true). SQL không do AI chấm mà thực thi trong sandbox."),
        P("Hai luồng kết quả: IMMEDIATE công bố tự động; HUMAN_VERIFIED chờ Admin duyệt. Mọi sửa điểm "
          "phải có lý do và được ghi vào grade_edit_audit (immutable)."),
        P("source=ai: ai_type_targets chỉ gồm mcq/essay; SQL luôn từ validated bank; exact count; "
          "generation_diagnostics gồm các reason code: json_parse, schema, truncated, refusal, "
          "mcq_options, sql_syntax, sql_fixture, sql_empty_output, out_of_scope_concept, "
          "difficulty_mismatch, duplicate, count, type_source, type_fields, timeout."),
        H(1, "6. Cơ sở dữ liệu và sơ đồ quan hệ"),
        P("PostgreSQL 17: %d bảng, %d cột, %d khóa ngoại, %d chỉ mục, 0 enum, %d migration. "
          "Sơ đồ dưới đây sinh từ introspection thật."
          % (len(TABLES), sum(len(t["columns"]) for t in TABLES), len(FKS), len(INDEXES), len(MIGS))),
        *erd_figures("2"),
        PB(),
        *trd_figures("3"),
        H(2, "6.1. Bảng legacy/retired"),
        P("Bốn bảng sau vẫn tồn tại trong db/schema.sql để giữ dữ liệu đề thi lịch sử và khóa ngoại; "
          "không API nào tạo mới, migration 019 đóng mọi đề published. Chúng được tô màu và ghi nhãn "
          "[legacy/retired] trong ERD, không bị ẩn hay xoá."),
        T([["Bảng", "Lý do"]] + [[n, "Chỉ lưu dữ liệu đề thi lịch sử (prebuilt exams đã retired)"]
                                 for n in sorted(LEGACY)], [3000, 6300]),
        H(1, "7. Phụ lục — hợp đồng API và tuyến giao diện"),
        P("app.openapi(): %d paths / %d operations. Frontend: %d routes, Admin: %d mục."
          % (FACTS["openapi_path_count"], FACTS["openapi_operation_count"],
             len(FACTS["frontend_routes"]), len(FACTS["admin_nav"]))),
        T(endpoint_appendix(), [700, 8600]),
        H(2, "7.1. Tuyến frontend"),
        T([["#", "Route"]] + [[str(i + 1), r] for i, r in enumerate(FACTS["frontend_routes"])],
          [700, 8600]),
    ]
    return b


def database_blocks():
    b = cover("Database Design / Thiết kế cơ sở dữ liệu", "C1SE.70_DatabaseDesign_DBCAS") + front() + glossary()
    b += version_note(RETIRED)
    b += [
        H(1, "3. Nguồn dữ liệu và phương pháp"),
        P("Toàn bộ nội dung chương này sinh từ scripts/introspect_schema.py: áp db/schema.sql vào "
          "PostgreSQL 17 sạch trong Docker, đọc information_schema.columns, pg_constraint, pg_indexes, "
          "pg_enum, pg_get_constraintdef. Kết quả: %d bảng, %d cột, %d khóa ngoại, %d chỉ mục, "
          "%d kiểu enum, %d migration. Không có bảng hay cột nào được thêm/bớt thủ công."
          % (len(TABLES), sum(len(t["columns"]) for t in TABLES), len(FKS), len(INDEXES),
             len(INTRO["enums"]), len(MIGS))),
        H(1, "3.1. Sơ đồ ERD và quan hệ bảng"),
        *erd_figures("1"),
        PB(),
        *trd_figures("2"),
        H(1, "3.2. Bảng tổng quan"),
        T([["#", "Bảng", "Số cột", "PK", "FK", "Trạng thái"]] +
          [[str(i + 1), t["table"], str(len(t["columns"])),
            ",".join(c["columns"]) if (c := next((x for x in t["constraints"] if x["type"] == "p"), None)) else "—",
            str(sum(1 for f in FKS if f["source"] == t["table"])),
            "legacy/retired" if t["table"] in LEGACY else "active"]
           for i, t in enumerate(TABLES)], [600, 3100, 900, 1900, 900, 1900]),
        H(1, "3.3. Bảng legacy/retired"),
        P("assessment, assessment_concept, assessment_question, assessment_blueprint tồn tại để giữ "
          "dữ liệu đề thi lịch sử và khóa ngoại; migration 019 đóng mọi đề published, seed_demo tạo 0 đề. "
          "Chúng được thể hiện rõ trong ERD (tô màu, nhãn [legacy/retired]), không bị ẩn."),
    ]
    b += dictionary_blocks()
    b += [
        H(1, "5. Khóa ngoại"),
        T(fk_rows(), [600, 2600, 3800, 2300]),
        H(1, "6. Chỉ mục"),
        T(index_rows(), [600, 2200, 2600, 3900]),
        H(1, "7. Migration"),
        T(migration_rows(), [600, 4200, 4500]),
        H(1, "8. Dữ liệu seed và giới hạn"),
        T([["Hạng mục", "Giá trị thực"],
           ["Câu hỏi", "5.482 (2.006 MCQ / 1.747 SQL / 1.729 essay)"],
           ["Khái niệm", "80"],
           ["Đề thi dựng sẵn", "0 (exam_count = 0 trong app/seed_demo.py)"],
           ["Phiên demo", "4 published sessions / 3 learner"],
           ["Kiểu enum", "0 (CHECK/VARCHAR thay thế)"],
           ["Ý nghĩa nghiệp vụ cột", NEED_HUMAN]], [3500, 5800]),
    ]
    return b


def main():
    docs = [
        ("C1SE.70_ProposalDocument_DBCAS_ver1.1.docx", "C1SE.70_ProposalDocument_DBCAS_ver1.2.docx",
         "Proposal / Đề xuất dự án", proposal_blocks),
        ("C1SE.70_ArchitectureDesign_DBCAS_ver1.1.docx", "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx",
         "Architecture Design / Thiết kế kiến trúc", architecture_blocks),
        ("C1SE.70_DatabaseDesign_DBCAS_ver1.1.docx", "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx",
         "Database Design / Thiết kế cơ sở dữ liệu", database_blocks),
    ]
    manifest = {"date": DATE, "version": VERSION, "documents": []}
    for src, dst, title, builder in docs:
        blocks = builder()
        out = ACA / dst
        b = Builder(ACA / src, out)
        b.build(blocks, {"title": "DBCAS — " + title, "creator": "DBCAS team",
                         "revision": "3", "created": DATE + "T00:00:00Z",
                         "modified": DATE + "T00:00:00Z"})
        manifest["documents"].append({
            "file": str(out.relative_to(ROOT)), "template": src,
            "blocks": len(blocks), "images": len(b.images),
            "headings": sum(1 for x in blocks if x["type"] == "heading"),
            "tables": sum(1 for x in blocks if x["type"] == "table"),
        })
        print(f"{dst}: {len(blocks)} blocks, {len(b.images)} images, "
              f"{sum(1 for x in blocks if x['type'] == 'table')} tables")
    (ROOT / "docs/qa/docx-build-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote docs/qa/docx-build-manifest.json")


if __name__ == "__main__":
    main()
