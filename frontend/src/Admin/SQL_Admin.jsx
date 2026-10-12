import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./SQL_Admin.css";
const EXAM_DRAFT_KEY = "dbcas-exam-drafts-v1";
const SECTION_ROUTES = {
  tn: "/TN_Admin",
  sql: "/SQL_Admin",
  tl: "/TL_Admin"
};
const SECTION_STEPS = {
  tn: "mcq",
  sql: "sql",
  tl: "essay"
};
function readExamDrafts() {
  try {
    const data = JSON.parse(localStorage.getItem(EXAM_DRAFT_KEY) || "{}");
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      return {};
    }
    return Object.fromEntries(Object.entries(data).filter(([id, record]) => {
      return record && record.id === id && record.sections && typeof record.sections === "object" && ["draft", "published"].includes(record.status);
    }));
  } catch {
    return {};
  }
}
function readExamDraft(examId) {
  return readExamDrafts()[examId] || null;
}
function readExamSection(examId, section) {
  return readExamDraft(examId)?.sections?.[section] || null;
}
function draftCourse(examId, seed = {}, fallback = {}) {
  const saved = readExamDraft(examId)?.course;
  if (saved) {
    return {
      ...fallback,
      ...saved
    };
  }
  return {
    ...fallback,
    testName: seed.title || seed.testName || fallback.testName || "Bài kiểm tra mới",
    major: seed.major || fallback.major || "Ngành Công nghệ phần mềm",
    schoolYear: seed.year || seed.schoolYear || fallback.schoolYear || "2026 - 2027",
    duration: Number(seed.duration) > 0 ? Number(seed.duration) : fallback.duration || 60
  };
}
function saveExamSection(examId, section, draft, nextSection = section, seed = {}) {
  if (!examId || !SECTION_ROUTES[section]) {
    throw new Error("Mã đề hoặc phần thi không hợp lệ.");
  }
  const allDrafts = readExamDrafts();
  const previous = allDrafts[examId] || {
    id: examId,
    status: "draft",
    date: seed.date || "",
    startTime: seed.startTime || "",
    studentCount: Number(seed.studentCount) || 0,
    sections: {}
  };
  const source = draft.course || draft;
  const course = {
    ...draftCourse(examId, seed),
    testName: String(source.testName ?? ""),
    major: String(source.major ?? ""),
    schoolYear: String(source.schoolYear ?? ""),
    duration: Number(source.duration) || 60
  };
  const sections = {
    ...previous.sections,
    [section]: JSON.parse(JSON.stringify(draft))
  };
  for (const [type, value] of Object.entries(sections)) {
    sections[type] = type === "tl" ? {
      ...value,
      course: {
        ...course
      }
    } : {
      ...value,
      ...course
    };
  }
  const record = {
    ...previous,
    course,
    title: course.testName,
    major: course.major,
    year: course.schoolYear,
    duration: course.duration,
    sections,
    draftStep: SECTION_STEPS[nextSection] || SECTION_STEPS[section],
    updatedAt: new Date().toISOString()
  };
  allDrafts[examId] = record;
  localStorage.setItem(EXAM_DRAFT_KEY, JSON.stringify(allDrafts));
  return record;
}
function withExamId(href, examId) {
  const url = new URL(href, "http://dbcas.local");
  url.searchParams.set("examId", examId);
  return `${url.pathname}${url.search}${url.hash}`;
}
function sectionFromHref(href, fallback) {
  const pathname = new URL(href || "/", "http://dbcas.local").pathname;
  return Object.keys(SECTION_ROUTES).find(section => SECTION_ROUTES[section] === pathname) || fallback;
}
function useDraftIdentity() {
  const location = useLocation();
  const navigate = useNavigate();
  const [generatedId] = useState(() => `LOCAL-EXAM-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`);
  const queryId = new URLSearchParams(location.search).get("examId");
  const examId = queryId || location.state?.examId || generatedId;
  const seedExam = location.state?.exam?.id === examId ? location.state.exam : null;
  useEffect(() => {
    if (queryId) return;
    navigate(withExamId(location.pathname + location.search + location.hash, examId), {
      replace: true,
      state: location.state
    });
  }, [queryId, examId, location.pathname, location.search, location.hash, location.state, navigate]);
  return {
    examId,
    seedExam
  };
}
function pointValue(value, fallback = 0) {
  const number = Number(value ?? fallback);
  return Number.isFinite(number) && number >= 0 ? Math.round(number * 100) / 100 : 0;
}
function validPoints(value, fallback = 0) {
  const raw = value ?? fallback;
  return String(raw).trim() !== "" && Number.isFinite(Number(raw)) && Number(raw) > 0;
}
function questionScore(question, section) {
  if (section === "tl") {
    const criteria = Array.isArray(question?.criteria) ? question.criteria : [];
    return criteria.reduce((sum, item) => sum + Math.round(pointValue(item?.points) * 100), 0) / 100;
  }
  return pointValue(question?.points, section === "tn" ? 0.4 : 1);
}
function sectionSummary(draft, section) {
  const questions = Array.isArray(draft?.questions) ? draft.questions : [];
  return {
    count: questions.length,
    points: questions.reduce((sum, question) => sum + Math.round(questionScore(question, section) * 100), 0) / 100
  };
}
function examSummary(section, currentDraft, examId) {
  const result = {};
  for (const type of ["tn", "sql", "tl"]) {
    result[type] = sectionSummary(type === section ? currentDraft : readExamSection(examId, type), type);
  }
  result.total = (Math.round(result.tn.points * 100) + Math.round(result.sql.points * 100) + Math.round(result.tl.points * 100)) / 100;
  result.count = result.tn.count + result.sql.count + result.tl.count;
  return result;
}
function fmtPoints(value) {
  return pointValue(value).toFixed(2);
}
function emptyQuestion(title = "") {
  return {
    title,
    description: "",
    sql: "",
    keywords: [],
    points: "1.0"
  };
}
function createSampleQuestions() {
  return [emptyQuestion("Truy vấn JOIN & Phân nhóm Aggregation"), {
    title: "Tối ưu Window Functions & CTE",
    description: "Viết truy vấn tính tổng chi tiêu của từng khách hàng " + "theo quý trong năm 2023. Sử dụng CTE và DENSE_RANK() " + "để xếp hạng khách hàng theo tổng chi tiêu giảm dần " + "trong từng quý.",
    sql: `WITH quarterly_spending AS (
    SELECT
        c.customer_id,
        c.full_name,
        DATE_PART('quarter', o.order_date) AS qtr,
        SUM(oi.quantity * oi.unit_price) AS total_spent
    FROM customers c
    INNER JOIN orders o
        ON c.customer_id = o.customer_id
    INNER JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_date >= DATE '2023-01-01'
      AND o.order_date < DATE '2024-01-01'
    GROUP BY
        c.customer_id,
        c.full_name,
        DATE_PART('quarter', o.order_date)
)
SELECT
    qtr,
    customer_id,
    full_name,
    total_spent,
    DENSE_RANK() OVER (
        PARTITION BY qtr
        ORDER BY total_spent DESC
    ) AS rank_vip
FROM quarterly_spending
ORDER BY qtr ASC, rank_vip ASC;`,
    keywords: ["DENSE_RANK()", "PARTITION BY", "WITH", "INNER JOIN"],
    points: "1.0"
  }, emptyQuestion("Transaction & Isolation Level Testing")];
}
function validQuestion(question) {
  return question && ["title", "description", "sql"].every(key => typeof question[key] === "string") && Array.isArray(question.keywords) && question.keywords.every(word => typeof word === "string");
}
function initialDraft(examId) {
  const fallback = {
    testName: "Kiểm tra Cơ sở Dữ liệu Nâng cao",
    major: "Ngành Công nghệ phần mềm",
    schoolYear: "2024 - 2025",
    duration: 60,
    selectedIndex: 1,
    questions: createSampleQuestions()
  };
  const saved = readExamSection(examId, "sql");
  if (!saved || !Array.isArray(saved.questions) || saved.questions.length === 0 || !saved.questions.every(validQuestion)) {
    return fallback;
  }
  return {
    ...fallback,
    ...saved,
    selectedIndex: Math.max(0, Math.min(saved.questions.length - 1, Number.isInteger(saved.selectedIndex) ? saved.selectedIndex : 0))
  };
}
function completeQuestion(question) {
  return Boolean(question.title.trim() && question.description.trim() && question.sql.trim() && validPoints(question.points, 1));
}
const ICON_PATHS = {
  back: <path d="m12 19-7-7 7-7M5 12h14" />,
  next: <path d="m12 5 7 7-7 7M5 12h14" />,
  help: <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .7-1.5 1-1.5 2M12 16h.01" />
    </>,
  bell: <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />,
  user: <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21v-2a8 8 0 0 1 16 0v2" />
    </>,
  book: <path d="M12 5v15M12 5C8 2 4 3 2 4v15c3-1 7-1 10 1M12 5c4-3 8-2 10-1v15c-3-1-7-1-10 1" />,
  clock: <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>,
  list: <path d="M9 6h12M9 12h12M9 18h12M3 6h1M3 12h1M3 18h1" />,
  chart: <path d="M4 3v17h17M8 16v-5m5 5V7m5 9V4" />,
  edit: <path d="m16 3 5 5-12 12-6 1 1-6Zm-2 2 5 5" />,
  trash: <path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7" />,
  plus: <path d="M12 5v14M5 12h14" />,
  code: <path d="m8 5-7 7 7 7m8-14 7 7-7 7m-3-16-2 18" />,
  play: <path d="m8 4 12 8-12 8Z" />,
  copy: <>
      <rect x="8" y="8" width="12" height="13" rx="2" />
      <path d="M16 8V3H3v13h5" />
    </>,
  tag: <>
      <path d="M3 3h8l10 10-8 8L3 11Z" />
      <circle cx="7" cy="7" r="1" />
    </>,
  eye: <>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </>,
  save: <path d="M4 3h13l3 3v15H4ZM8 3v6h8V3M8 21v-8h8v8" />
};
function Icon({
  name,
  className = ""
}) {
  return <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {ICON_PATHS[name]}
    </svg>;
}
export default function SQLAdmin(props) {
  const {
    examId,
    seedExam
  } = useDraftIdentity();
  return <SQLAdminEditor key={examId} {...props} examId={examId} seedExam={seedExam} />;
}
function SQLAdminEditor({
  examId,
  seedExam,
  tnHref = "/TN_Admin",
  essayHref = "/TL_Admin",
  settingsHref = "/Cai_dat_Admin"
}) {
  const navigate = useNavigate();
  const [draft, setDraft] = useState(() => {
    const value = initialDraft(examId);
    return {
      ...value,
      ...draftCourse(examId, seedExam || {}, value)
    };
  });
  const [toast, setToast] = useState("");
  const [addingKeyword, setAddingKeyword] = useState(false);
  const [keyword, setKeyword] = useState("");
  const [renameIndex, setRenameIndex] = useState(null);
  const [renameTitle, setRenameTitle] = useState("");
  const [studentSQL, setStudentSQL] = useState("");
  const renameDialog = useRef(null);
  const previewDialog = useRef(null);
  const sqlInput = useRef(null);
  const toastTimer = useRef(null);
  const selectionFrame = useRef(null);
  const question = draft.questions[draft.selectedIndex];
  const scores = examSummary("sql", draft, examId);
  const majorOptions = [...new Set(["Ngành Công nghệ phần mềm", "Ngành Hệ thống Thông tin Quản lý", "Ngành Khoa học Máy tính", "Ngành Kỹ thuật Phần mềm", "An ninh Mạng", draft.major])];
  const yearOptions = [...new Set(["2024 - 2025", "2025 - 2026", "2026 - 2027", draft.schoolYear])];
  useEffect(() => {
    return () => {
      clearTimeout(toastTimer.current);
      if (selectionFrame.current !== null) {
        cancelAnimationFrame(selectionFrame.current);
      }
    };
  }, []);
  function notify(message) {
    clearTimeout(toastTimer.current);
    setToast(message);
    toastTimer.current = setTimeout(() => {
      setToast("");
    }, 3500);
  }
  function updateMeta(key, value) {
    setDraft(old => ({
      ...old,
      [key]: value
    }));
  }
  function updateDuration(value) {
    const number = Number(value);
    if (Number.isFinite(number) && String(value).trim() !== "") {
      updateMeta("duration", Math.max(10, Math.min(120, Math.round(number))));
    }
  }
  function updateQuestion(patch) {
    setDraft(old => ({
      ...old,
      questions: old.questions.map((item, index) => index === old.selectedIndex ? {
        ...item,
        ...patch
      } : item)
    }));
  }
  function selectQuestion(index) {
    setAddingKeyword(false);
    setKeyword("");
    updateMeta("selectedIndex", Math.max(0, Math.min(draft.questions.length - 1, index)));
  }
  function addQuestion() {
    setDraft(old => ({
      ...old,
      questions: [...old.questions, emptyQuestion("Câu SQL mới")],
      selectedIndex: old.questions.length
    }));
    setAddingKeyword(false);
    setKeyword("");
  }
  function deleteQuestion(index) {
    if (draft.questions.length === 1) {
      notify("Phải giữ ít nhất một câu SQL.");
      return;
    }
    setDraft(old => ({
      ...old,
      questions: old.questions.filter((_, itemIndex) => itemIndex !== index),
      selectedIndex: Math.max(0, Math.min(old.questions.length - 2, old.selectedIndex - (index < old.selectedIndex ? 1 : 0)))
    }));
    setAddingKeyword(false);
    setKeyword("");
  }
  function openRename(index) {
    setRenameIndex(index);
    setRenameTitle(draft.questions[index].title);
    renameDialog.current?.showModal();
  }
  function submitRename(event) {
    event.preventDefault();
    const title = renameTitle.trim();
    if (!title) return;
    setDraft(old => ({
      ...old,
      questions: old.questions.map((item, index) => index === renameIndex ? {
        ...item,
        title
      } : item)
    }));
    renameDialog.current?.close();
  }
  function submitKeyword(event) {
    event.preventDefault();
    const word = keyword.trim().replace(/\s+/g, " ").toUpperCase();
    if (!word) return;
    const exists = question.keywords.some(item => item.toUpperCase() === word);
    if (exists) {
      notify("Từ khóa này đã có.");
      return;
    }
    updateQuestion({
      keywords: [...question.keywords, word]
    });
    setKeyword("");
    setAddingKeyword(false);
  }
  function deleteKeyword(index) {
    updateQuestion({
      keywords: question.keywords.filter((_, itemIndex) => itemIndex !== index)
    });
  }
  function handleSQLTab(event) {
    if (event.key !== "Tab" || event.shiftKey) return;
    event.preventDefault();
    const {
      selectionStart: start,
      selectionEnd: end
    } = event.currentTarget;
    updateQuestion({
      sql: question.sql.slice(0, start) + "    " + question.sql.slice(end)
    });
    if (selectionFrame.current !== null) {
      cancelAnimationFrame(selectionFrame.current);
    }
    selectionFrame.current = requestAnimationFrame(() => {
      sqlInput.current?.setSelectionRange(start + 4, start + 4);
      selectionFrame.current = null;
    });
  }
  async function copySQL() {
    if (!question.sql.trim()) {
      notify("Chưa nhập nội dung SQL.");
      return;
    }
    try {
      await navigator.clipboard.writeText(question.sql);
      notify("Đã sao chép SQL.");
    } catch {
      sqlInput.current?.focus();
      sqlInput.current?.select();
      notify("SQL đã được chọn. Nhấn Ctrl+C để sao chép.");
    }
  }
  function saveDraft(nextSection = "sql") {
    try {
      saveExamSection(examId, "sql", {
        ...draft,
        questions: draft.questions.map(item => ({
          ...item,
          points: questionScore(item, "sql")
        }))
      }, nextSection, seedExam || {});
      return true;
    } catch {
      notify("Không lưu được bản nháp SQL trong trình duyệt.");
      return false;
    }
  }
  function beforeNavigate(event) {
    const nextSection = sectionFromHref(event.currentTarget.getAttribute("href"), "sql");
    if (!saveDraft(nextSection)) {
      event.preventDefault();
    }
  }
  useEffect(() => {
    saveDraft();
  }, [examId]);
  function previousQuestion() {
    if (draft.selectedIndex > 0) {
      selectQuestion(draft.selectedIndex - 1);
      return;
    }
    if (saveDraft("tn")) {
      navigate(withExamId(tnHref, examId));
    }
  }
  function nextQuestion() {
    if (draft.selectedIndex < draft.questions.length - 1) {
      selectQuestion(draft.selectedIndex + 1);
      return;
    }
    if (saveDraft("tl")) {
      navigate(withExamId(essayHref, examId));
    }
  }
  function openPreview() {
    setStudentSQL("");
    previewDialog.current?.showModal();
  }
  return <div className="dbcas-admin-sql">
      <header className="topbar admin-unified-topbar">
        <div className="topbar-left">
          <Link className="back-button" to={withExamId(tnHref, examId)} onClick={beforeNavigate}>
            <Icon name="back" />
            Quay lại
          </Link>

          <span className="divider" />

          <nav className="breadcrumb" aria-label="Đường dẫn">
            <span>Quản lý bài kiểm tra</span>
            <span>/</span>
            <strong>Soạn bài kiểm tra</strong>
          </nav>
        </div>

        <div className="topbar-right">
          <button className="icon-button" type="button" aria-label="Trợ giúp" onClick={() => notify("Soạn đề, nhập đáp án chuẩn, thêm từ khóa rồi lưu nháp.")}>
            <Icon name="help" />
          </button>

          <button className="icon-button notification-button" type="button" aria-label="Thông báo" onClick={() => notify("Bạn chưa có thông báo mới.")}>
            <Icon name="bell" />
            <span className="notification-dot" />
          </button>

          <span className="divider" />

          <AdminAccountMenu />
        </div>
      </header>

      <main className="page-layout">
        <aside className="sidebar">
          <section className="card course-card">
            <h2 className="section-title">
              <Icon name="book" />
              THÔNG TIN HỌC PHẦN
            </h2>

            <div className="form-field">
              <label htmlFor="test-name">
                TÊN BÀI KIỂM TRA
              </label>

              <input id="test-name" type="text" value={draft.testName} onChange={event => updateMeta("testName", event.target.value)} />
            </div>

            <div className="form-field">
              <label htmlFor="major">NGÀNH HỌC</label>

              <select id="major" value={draft.major} onChange={event => updateMeta("major", event.target.value)}>
                {majorOptions.map(value => <option key={value} value={value}>
                    {value}
                  </option>)}
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="school-year">NĂM HỌC</label>

              <select id="school-year" value={draft.schoolYear} onChange={event => updateMeta("schoolYear", event.target.value)}>
                {yearOptions.map(value => <option key={value} value={value}>
                    {value}
                  </option>)}
              </select>
            </div>

            <div className="form-field">
              <div className="field-heading">
                <label htmlFor="duration">
                  THỜI GIAN LÀM BÀI
                </label>
                <span>{draft.duration} phút</span>
              </div>

              <div className="duration-control">
                <button type="button" disabled={draft.duration <= 10} aria-label="Giảm 1 phút" onClick={() => updateDuration(draft.duration - 1)}>
                  −
                </button>

                <div className="duration-input">
                  <Icon name="clock" />

                  <input id="duration" type="number" min="10" max="120" step="1" value={draft.duration} onChange={event => updateDuration(event.target.value)} aria-label="Số phút làm bài" />

                  <span>phút</span>
                </div>

                <button type="button" disabled={draft.duration >= 120} aria-label="Tăng 1 phút" onClick={() => updateDuration(draft.duration + 1)}>
                  +
                </button>
              </div>

              <div className="duration-presets">
                {[45, 60, 90, 120].map(duration => <button key={duration} type="button" className={draft.duration === duration ? "active" : ""} aria-pressed={draft.duration === duration} onClick={() => updateDuration(duration)}>
                    {duration}m
                  </button>)}
              </div>
            </div>
          </section>

          <section className="card questions-card">
            <h2 className="section-title">
              <Icon name="list" />
              CÂU HỎI SQL
            </h2>

            <ol className="question-list">
              {draft.questions.map((item, index) => <li key={index} className={`question-item${draft.selectedIndex === index ? " selected" : ""}`}>
                  <button type="button" className="question-select" aria-pressed={draft.selectedIndex === index} onClick={() => selectQuestion(index)}>
                    <span className="question-number">
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    <span className="question-info">
                      <span className="question-title">
                        {item.title || "Chưa nhập tên câu hỏi"}
                      </span>

                      <span className="question-points">
                        {fmtPoints(questionScore(item, "sql"))}{" "}
                        điểm
                      </span>
                    </span>
                  </button>

                  <div className="question-actions">
                    <span className="question-status">
                      {draft.selectedIndex === index ? "ĐANG CHỌN" : completeQuestion(item) ? "Đã xong" : "Chưa soạn"}
                    </span>

                    <button type="button" className="small-button" aria-label={`Sửa tên câu ${index + 1}`} onClick={() => openRename(index)}>
                      <Icon name="edit" />
                    </button>

                    <button type="button" className="small-button delete-button" aria-label={`Xóa câu ${index + 1}`} onClick={() => deleteQuestion(index)}>
                      <Icon name="trash" />
                    </button>
                  </div>
                </li>)}
            </ol>

            <button className="add-button" type="button" onClick={addQuestion}>
              <Icon name="plus" />
              Thêm câu hỏi SQL
            </button>
          </section>
        </aside>

        <div className="main-content">
          <section className="card scoring-card">
            <div className="scoring-heading">
              <h2 className="section-title">
                <Icon name="chart" />
                CẤU TRÚC ĐIỂM THI &amp; PHÂN BỔ CÂU HỎI
              </h2>

              <div className="total-score">
                Tổng điểm:{" "}
                <strong>
                  {fmtPoints(scores.total)} Điểm •{" "}
                  {scores.count} câu
                </strong>
              </div>
            </div>

            <div className="score-grid">
              <div className="score-item">
                <div className="score-item-heading">
                  <strong>1. TRẮC NGHIỆM</strong>
                  <span className="score-points">
                    {fmtPoints(scores.tn.points)} đ
                  </span>
                </div>

                <p>
                  {scores.tn.count} câu • Tổng{" "}
                  {fmtPoints(scores.tn.points)} điểm
                </p>

                <span className="score-status">
                  {scores.tn.count ? "Đã lưu nháp" : "Chưa có nháp"}
                </span>
              </div>

              <div className="score-item active">
                <div className="score-item-heading">
                  <strong>2. TRUY VẤN SQL</strong>
                  <span className="score-points">
                    {fmtPoints(scores.sql.points)} đ
                  </span>
                </div>

                <p>
                  {scores.sql.count} câu • Tổng{" "}
                  {fmtPoints(scores.sql.points)} điểm
                </p>

                <span className="score-status">
                  ĐANG SOẠN
                </span>
              </div>

              <div className="score-item">
                <div className="score-item-heading">
                  <strong>3. TỰ LUẬN CSDL</strong>
                  <span className="score-points">
                    {fmtPoints(scores.tl.points)} đ
                  </span>
                </div>

                <p>
                  {scores.tl.count} câu • Tổng{" "}
                  {fmtPoints(scores.tl.points)} điểm
                </p>

                <span className="score-status">
                  {scores.tl.count ? "Đã lưu nháp" : "Chưa có nháp"}
                </span>
              </div>
            </div>
          </section>

          <section className="card editor-card">
            <header className="editor-heading">
              <div>
                <span className="question-badge">
                  CÂU SQL{" "}
                  {String(draft.selectedIndex + 1).padStart(2, "0")}{" "}
                  / {draft.questions.length}
                </span>

                <h1>
                  {question.title || "Câu hỏi chưa đặt tên"}
                </h1>
              </div>

              <label className="point-badge editable-point" style={{
              display: "flex",
              alignItems: "center",
              gap: 8
            }}>
                Điểm câu này

                <input type="number" min="0.01" step="0.01" aria-label="Điểm câu hỏi" value={question.points ?? 1} onChange={event => updateQuestion({
                points: event.target.value
              })} style={{
                width: 85,
                minWidth: 0,
                padding: "6px 8px",
                border: "1px solid #334155",
                borderRadius: 6,
                background: "#070c17",
                color: "#22d3ee",
                font: "inherit"
              }} />

                đ
              </label>
            </header>

            <div className="editor-body">
              <section className="editor-section">
                <h2 className="section-title">
                  <Icon name="edit" />

                  <label htmlFor="question-description">
                    MÔ TẢ YÊU CẦU ĐỀ BÀI
                  </label>
                </h2>

                <textarea id="question-description" className="description-input" rows="4" value={question.description} onChange={event => updateQuestion({
                description: event.target.value
              })} placeholder="Nhập mô tả yêu cầu đề bài..." />
              </section>

              <section className="editor-section">
                <div className="section-heading">
                  <h2 className="section-title">
                    <Icon name="code" />

                    <label htmlFor="sql-code">
                      ĐÁP ÁN TRUY VẤN CHUẨN
                    </label>
                  </h2>

                  <button className="button sandbox-button" type="button" onClick={() => notify("Chưa kết nối Docker Sandbox để chạy SQL.")}>
                    <Icon name="play" />
                    Chạy thử Sandbox
                  </button>
                </div>

                <div className="code-editor">
                  <div className="code-toolbar">
                    <div className="code-dots">
                      <span />
                      <span />
                      <span />
                    </div>

                    <span className="code-language">
                      SQL
                    </span>

                    <button className="copy-button" type="button" onClick={copySQL}>
                      <Icon name="copy" />
                      Copy
                    </button>
                  </div>

                  <textarea id="sql-code" ref={sqlInput} className="sql-input" rows="13" value={question.sql} onChange={event => updateQuestion({
                  sql: event.target.value
                })} onKeyDown={handleSQLTab} spellCheck={false} autoCapitalize="off" autoComplete="off" placeholder="Nhập đáp án truy vấn SQL..." />
                </div>
              </section>

              <section className="keywords-section">
                <div className="section-heading">
                  <h2 className="section-title">
                    <Icon name="tag" />
                    TỪ KHÓA BẮT BUỘC ĐỐI CHIẾU TRỌNG TÂM
                  </h2>

                  <span className="keyword-count">
                    {question.keywords.length} từ khóa
                  </span>
                </div>

                <div className="keyword-controls">
                  <div className="keyword-list">
                    {question.keywords.map((word, index) => <span className="keyword-tag" key={index}>
                          <span>{word}</span>

                          <button type="button" aria-label={`Xóa từ khóa ${word}`} onClick={() => deleteKeyword(index)}>
                            ×
                          </button>
                        </span>)}
                  </div>

                  <button className="add-keyword" type="button" onClick={() => {
                  setAddingKeyword(true);
                  setKeyword("");
                }}>
                    <Icon name="plus" />
                    Thêm từ khóa
                  </button>
                </div>

                {addingKeyword && <form className="keyword-form" onSubmit={submitKeyword}>
                    <input type="text" maxLength="100" value={keyword} onChange={event => setKeyword(event.target.value)} placeholder="Ví dụ: INNER JOIN" aria-label="Từ khóa SQL" required autoFocus />

                    <button className="button button-primary" type="submit">
                      Thêm
                    </button>

                    <button className="button" type="button" onClick={() => setAddingKeyword(false)}>
                      Hủy
                    </button>
                  </form>}
              </section>
            </div>
          </section>
        </div>
      </main>

      <footer className="bottom-toolbar">
        <div className="toolbar-actions">
          <button className="button" type="button" onClick={openPreview}>
            <Icon name="eye" />
            Xem trước giao diện sinh viên
          </button>

          <button className="button" type="button" onClick={() => {
          if (saveDraft()) {
            notify("Đã lưu nháp SQL trong trình duyệt.");
          }
        }}>
            <Icon name="save" />
            Lưu bản nháp
          </button>
        </div>

        <div className="question-navigation">
          <button className="button" type="button" onClick={previousQuestion}>
            <Icon name="back" />

            <span>
              {draft.selectedIndex === 0 ? "Về Trắc nghiệm" : "Câu trước"}
            </span>
          </button>

          <span>
            {draft.selectedIndex + 1} /{" "}
            {draft.questions.length}
          </span>

          <button className="button" type="button" onClick={nextQuestion}>
            <span>
              {draft.selectedIndex === draft.questions.length - 1 ? "Sang Tự luận" : "Câu tiếp theo"}
            </span>

            <Icon name="next" />
          </button>
        </div>

        <Link className="button button-primary" to={withExamId(essayHref, examId)} onClick={beforeNavigate}>
          Chuyển sang phần thi Tự luận
          <Icon name="next" />
        </Link>
      </footer>

      <dialog ref={renameDialog}>
        <form onSubmit={submitRename}>
          <h2>Sửa tên câu hỏi SQL</h2>

          <label htmlFor="rename-input">
            Tên câu hỏi
          </label>

          <input id="rename-input" type="text" maxLength="200" value={renameTitle} onChange={event => setRenameTitle(event.target.value)} placeholder="Nhập tên câu hỏi..." required />

          <div className="dialog-actions">
            <button className="button" type="button" onClick={() => renameDialog.current?.close()}>
              Hủy
            </button>

            <button className="button button-primary" type="submit">
              Cập nhật
            </button>
          </div>
        </form>
      </dialog>

      <dialog ref={previewDialog} className="preview-dialog">
        <h2>Xem trước giao diện sinh viên</h2>

        <h3>
          Câu SQL {draft.selectedIndex + 1}:{" "}
          {question.title}
        </h3>

        <p className="preview-description">
          {question.description || "Chưa nhập mô tả đề bài."}
        </p>

        <label htmlFor="student-sql">
          Bài làm SQL
        </label>

        <textarea id="student-sql" className="sql-input" rows="8" value={studentSQL} onChange={event => setStudentSQL(event.target.value)} placeholder="Sinh viên nhập truy vấn tại đây..." spellCheck={false} />

        <div className="dialog-actions">
          <button className="button" type="button" onClick={() => previewDialog.current?.close()}>
            Đóng
          </button>
        </div>
      </dialog>

      <div className={`toast${toast ? " show" : ""}`} role="status" aria-live="polite">
        {toast}
      </div>
    </div>;
}
function AdminAccountMenu({
  profile,
  onLogout
}) {
  const navigate = useNavigate();
  const root = useRef(null);
  const trigger = useRef(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [account, setAccount] = useState({
    name: "Admin System",
    email: "admin.dbcas@gmail.com",
    phone: ""
  });
  useEffect(() => {
    function refresh() {
      const email = profile?.email || "admin.dbcas@gmail.com";
      let saved = {};
      try {
        saved = JSON.parse(localStorage.getItem(`dbcas.admin.account.v1:${email}`) || "{}");
      } catch {}
      setAccount({
        name: saved.name || profile?.name || "Admin System",
        email,
        phone: saved.phone ?? profile?.phone ?? ""
      });
    }
    refresh();
    window.addEventListener("dbcas:account-changed", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("dbcas:account-changed", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, [profile?.name, profile?.email, profile?.phone]);
  useEffect(() => {
    if (!open) return;
    function outside(event) {
      if (!root.current?.contains(event.target)) setOpen(false);
    }
    function escape(event) {
      if (event.key === "Escape") {
        setOpen(false);
        trigger.current?.focus();
      }
    }
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);
  async function logout() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      if (onLogout) await onLogout();
      navigate("/Dang_nhap");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể đăng xuất.");
    } finally {
      setBusy(false);
    }
  }
  const initials = account.name.trim().split(/\s+/).slice(-2).map(word => word[0]).join("").toUpperCase() || "AD";
  return <div className="admin-account-menu" ref={root}>
    <button ref={trigger} type="button" className="admin-account-trigger" aria-expanded={open} aria-label="Thông tin tài khoản Admin" onClick={() => setOpen(value => !value)}>
      <span className="admin-account-avatar">{initials}</span>
      <span className="admin-account-caption"><strong>{account.name}</strong><small>{account.email}</small></span>
      <span aria-hidden="true" className="admin-account-chevron">⌄</span>
    </button>
    {open && <div className="admin-account-panel">
      <div className="admin-account-panel-head"><span className="admin-account-avatar">{initials}</span><div><strong>{account.name}</strong><small>Quản trị viên</small></div></div>
      <dl><div><dt>Email</dt><dd>{account.email}</dd></div><div><dt>Số điện thoại</dt><dd>{account.phone || "Chưa cập nhật"}</dd></div></dl>
      <Link to="/Cai_dat_Admin" onClick={() => setOpen(false)} className="admin-account-settings">Cài đặt tài khoản</Link>
      <button type="button" className="admin-account-logout" disabled={busy} onClick={logout}>{busy ? "Đang đăng xuất..." : "Đăng xuất"}</button>
      {error && <p role="alert" className="admin-account-error">{error}</p>}
    </div>}
  </div>;
}