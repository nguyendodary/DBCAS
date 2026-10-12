import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
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
      {adminRender(ICON_PATHS[name])}
    </svg>;
}
export default function SQLAdmin(props) {
  useAdminLanguage();

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
      notify(adminText("Phải giữ ít nhất một câu SQL."));
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
      notify(adminText("Từ khóa này đã có."));
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
      notify(adminText("Chưa nhập nội dung SQL."));
      return;
    }
    try {
      await navigator.clipboard.writeText(question.sql);
      notify(adminText("Đã sao chép SQL."));
    } catch {
      sqlInput.current?.focus();
      sqlInput.current?.select();
      notify(adminText("SQL đã được chọn. Nhấn Ctrl+C để sao chép."));
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
      notify(adminText("Không lưu được bản nháp SQL trong trình duyệt."));
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
            <Icon name="back" />{adminText(" Quay lại ")}</Link>

          <span className="divider" />

          <nav className="breadcrumb" aria-label={adminText("Đường dẫn")}>
            <span>{adminText("Quản lý bài kiểm tra")}</span>
            <span>/</span>
            <strong>{adminText("Soạn bài kiểm tra")}</strong>
          </nav>
        </div>

        <div className="topbar-right">
          <button className="icon-button" type="button" aria-label={adminText("Trợ giúp")} onClick={() => notify(adminText("Soạn đề, nhập đáp án chuẩn, thêm từ khóa rồi lưu nháp."))}>
            <Icon name="help" />
          </button>

          <NotificationMenu role="admin" className="icon-button notification-button" />

          <span className="divider" />

          <AdminAccountMenu />
        </div>
      </header>

      <main className="page-layout">
        <aside className="sidebar">
          <section className="card course-card">
            <h2 className="section-title">
              <Icon name="book" />{adminText(" THÔNG TIN HỌC PHẦN ")}</h2>

            <div className="form-field">
              <label htmlFor="test-name">{adminText(" TÊN BÀI KIỂM TRA ")}</label>

              <input id="test-name" type="text" value={draft.testName} onChange={event => updateMeta("testName", event.target.value)} />
            </div>

            <div className="form-field">
              <label htmlFor="major">{adminText("NGÀNH HỌC")}</label>

              <select id="major" value={draft.major} onChange={event => updateMeta("major", event.target.value)}>
                {adminRender(majorOptions.map(value => <option key={value} value={value}>
                    {adminRender(value)}
                  </option>))}
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="school-year">{adminText("NĂM HỌC")}</label>

              <select id="school-year" value={draft.schoolYear} onChange={event => updateMeta("schoolYear", event.target.value)}>
                {adminRender(yearOptions.map(value => <option key={value} value={value}>
                    {adminRender(value)}
                  </option>))}
              </select>
            </div>

            <div className="form-field">
              <div className="field-heading">
                <label htmlFor="duration">{adminText(" THỜI GIAN LÀM BÀI ")}</label>
                <span>{adminRender(draft.duration)}{adminText(" phút")}</span>
              </div>

              <div className="duration-control">
                <button type="button" disabled={draft.duration <= 10} aria-label={adminText("Giảm 1 phút")} onClick={() => updateDuration(draft.duration - 1)}>
                  −
                </button>

                <div className="duration-input">
                  <Icon name="clock" />

                  <input id="duration" type="number" min="10" max="120" step="1" value={draft.duration} onChange={event => updateDuration(event.target.value)} aria-label={adminText("Số phút làm bài")} />

                  <span>{adminText("phút")}</span>
                </div>

                <button type="button" disabled={draft.duration >= 120} aria-label={adminText("Tăng 1 phút")} onClick={() => updateDuration(draft.duration + 1)}>
                  +
                </button>
              </div>

              <div className="duration-presets">
                {adminRender([45, 60, 90, 120].map(duration => <button key={duration} type="button" className={draft.duration === duration ? "active" : ""} aria-pressed={draft.duration === duration} onClick={() => updateDuration(duration)}>
                    {adminRender(duration)}m
                  </button>))}
              </div>
            </div>
          </section>

          <section className="card questions-card">
            <h2 className="section-title">
              <Icon name="list" />{adminText(" CÂU HỎI SQL ")}</h2>

            <ol className="question-list">
              {adminRender(draft.questions.map((item, index) => <li key={index} className={`question-item${draft.selectedIndex === index ? " selected" : ""}`}>
                  <button type="button" className="question-select" aria-pressed={draft.selectedIndex === index} onClick={() => selectQuestion(index)}>
                    <span className="question-number">
                      {adminRender(String(index + 1).padStart(2, "0"))}
                    </span>

                    <span className="question-info">
                      <span className="question-title">
                        {adminRender(item.title || "Chưa nhập tên câu hỏi")}
                      </span>

                      <span className="question-points">
                        {adminRender(fmtPoints(questionScore(item, "sql")))}{adminRender(" ")}{adminText(" điểm ")}</span>
                    </span>
                  </button>

                  <div className="question-actions">
                    <span className="question-status">
                      {adminRender(draft.selectedIndex === index ? "ĐANG CHỌN" : completeQuestion(item) ? "Đã xong" : "Chưa soạn")}
                    </span>

                    <button type="button" className="small-button" aria-label={`Sửa tên câu ${index + 1}`} onClick={() => openRename(index)}>
                      <Icon name="edit" />
                    </button>

                    <button type="button" className="small-button delete-button" aria-label={`Xóa câu ${index + 1}`} onClick={() => deleteQuestion(index)}>
                      <Icon name="trash" />
                    </button>
                  </div>
                </li>))}
            </ol>

            <button className="add-button" type="button" onClick={addQuestion}>
              <Icon name="plus" />{adminText(" Thêm câu hỏi SQL ")}</button>
          </section>
        </aside>

        <div className="main-content">
          <section className="card scoring-card">
            <div className="scoring-heading">
              <h2 className="section-title">
                <Icon name="chart" />{adminText(" CẤU TRÚC ĐIỂM THI & PHÂN BỔ CÂU HỎI ")}</h2>

              <div className="total-score">{adminText(" Tổng điểm:")}{adminRender(" ")}
                <strong>
                  {adminRender(fmtPoints(scores.total))}{adminText(" Điểm •")}{adminRender(" ")}
                  {adminRender(scores.count)}{adminText(" câu ")}</strong>
              </div>
            </div>

            <div className="score-grid">
              <div className="score-item">
                <div className="score-item-heading">
                  <strong>{adminText("1. TRẮC NGHIỆM")}</strong>
                  <span className="score-points">
                    {adminRender(fmtPoints(scores.tn.points))}{adminText(" đ ")}</span>
                </div>

                <p>
                  {adminRender(scores.tn.count)}{adminText(" câu • Tổng")}{adminRender(" ")}
                  {adminRender(fmtPoints(scores.tn.points))}{adminText(" điểm ")}</p>

                <span className="score-status">
                  {adminRender(scores.tn.count ? "Đã lưu nháp" : "Chưa có nháp")}
                </span>
              </div>

              <div className="score-item active">
                <div className="score-item-heading">
                  <strong>{adminText("2. TRUY VẤN SQL")}</strong>
                  <span className="score-points">
                    {adminRender(fmtPoints(scores.sql.points))}{adminText(" đ ")}</span>
                </div>

                <p>
                  {adminRender(scores.sql.count)}{adminText(" câu • Tổng")}{adminRender(" ")}
                  {adminRender(fmtPoints(scores.sql.points))}{adminText(" điểm ")}</p>

                <span className="score-status">{adminText(" ĐANG SOẠN ")}</span>
              </div>

              <div className="score-item">
                <div className="score-item-heading">
                  <strong>{adminText("3. TỰ LUẬN CSDL")}</strong>
                  <span className="score-points">
                    {adminRender(fmtPoints(scores.tl.points))}{adminText(" đ ")}</span>
                </div>

                <p>
                  {adminRender(scores.tl.count)}{adminText(" câu • Tổng")}{adminRender(" ")}
                  {adminRender(fmtPoints(scores.tl.points))}{adminText(" điểm ")}</p>

                <span className="score-status">
                  {adminRender(scores.tl.count ? "Đã lưu nháp" : "Chưa có nháp")}
                </span>
              </div>
            </div>
          </section>

          <section className="card editor-card">
            <header className="editor-heading"><NotificationMenu role="admin" className="icon-button" />
              <div>
                <span className="question-badge">{adminText(" CÂU SQL")}{adminRender(" ")}
                  {adminRender(String(draft.selectedIndex + 1).padStart(2, "0"))}{adminRender(" ")}
                  / {adminRender(draft.questions.length)}
                </span>

                <h1>
                  {adminRender(question.title || "Câu hỏi chưa đặt tên")}
                </h1>
              </div>

              <label className="point-badge editable-point" style={{
              display: "flex",
              alignItems: "center",
              gap: 8
            }}>{adminText(" Điểm câu này ")}<input type="number" min="0.01" step="0.01" aria-label={adminText("Điểm câu hỏi")} value={question.points ?? 1} onChange={event => updateQuestion({
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
              }} />{adminText(" đ ")}</label>
            </header>

            <div className="editor-body">
              <section className="editor-section">
                <h2 className="section-title">
                  <Icon name="edit" />

                  <label htmlFor="question-description">{adminText(" MÔ TẢ YÊU CẦU ĐỀ BÀI ")}</label>
                </h2>

                <textarea id="question-description" className="description-input" rows="4" value={question.description} onChange={event => updateQuestion({
                description: event.target.value
              })} placeholder={adminText("Nhập mô tả yêu cầu đề bài...")} />
              </section>

              <section className="editor-section">
                <div className="section-heading">
                  <h2 className="section-title">
                    <Icon name="code" />

                    <label htmlFor="sql-code">{adminText(" ĐÁP ÁN TRUY VẤN CHUẨN ")}</label>
                  </h2>

                  <button className="button sandbox-button" type="button" onClick={() => notify(adminText("Chưa kết nối Docker Sandbox để chạy SQL."))}>
                    <Icon name="play" />{adminText(" Chạy thử Sandbox ")}</button>
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
                })} onKeyDown={handleSQLTab} spellCheck={false} autoCapitalize="off" autoComplete="off" placeholder={adminText("Nhập đáp án truy vấn SQL...")} />
                </div>
              </section>

              <section className="keywords-section">
                <div className="section-heading">
                  <h2 className="section-title">
                    <Icon name="tag" />{adminText(" TỪ KHÓA BẮT BUỘC ĐỐI CHIẾU TRỌNG TÂM ")}</h2>

                  <span className="keyword-count">
                    {adminRender(question.keywords.length)}{adminText(" từ khóa ")}</span>
                </div>

                <div className="keyword-controls">
                  <div className="keyword-list">
                    {adminRender(question.keywords.map((word, index) => <span className="keyword-tag" key={index}>
                          <span>{adminRender(word)}</span>

                          <button type="button" aria-label={`Xóa từ khóa ${word}`} onClick={() => deleteKeyword(index)}>{adminText(" × ")}</button>
                        </span>))}
                  </div>

                  <button className="add-keyword" type="button" onClick={() => {
                  setAddingKeyword(true);
                  setKeyword("");
                }}>
                    <Icon name="plus" />{adminText(" Thêm từ khóa ")}</button>
                </div>

                {adminRender(addingKeyword && <form className="keyword-form" onSubmit={submitKeyword}>
                    <input type="text" maxLength="100" value={keyword} onChange={event => setKeyword(event.target.value)} placeholder={adminText("Ví dụ: INNER JOIN")} aria-label={adminText("Từ khóa SQL")} required autoFocus />

                    <button className="button button-primary" type="submit">{adminText(" Thêm ")}</button>

                    <button className="button" type="button" onClick={() => setAddingKeyword(false)}>{adminText(" Hủy ")}</button>
                  </form>)}
              </section>
            </div>
          </section>
        </div>
      </main>

      <footer className="bottom-toolbar">
        <div className="toolbar-actions">
          <button className="button" type="button" onClick={openPreview}>
            <Icon name="eye" />{adminText(" Xem trước giao diện sinh viên ")}</button>

          <button className="button" type="button" onClick={() => {
          if (saveDraft()) {
            notify(adminText("Đã lưu nháp SQL trong trình duyệt."));
          }
        }}>
            <Icon name="save" />{adminText(" Lưu bản nháp ")}</button>
        </div>

        <div className="question-navigation">
          <button className="button" type="button" onClick={previousQuestion}>
            <Icon name="back" />

            <span>
              {adminRender(draft.selectedIndex === 0 ? "Về Trắc nghiệm" : "Câu trước")}
            </span>
          </button>

          <span>
            {adminRender(draft.selectedIndex + 1)} /{adminRender(" ")}
            {adminRender(draft.questions.length)}
          </span>

          <button className="button" type="button" onClick={nextQuestion}>
            <span>
              {adminRender(draft.selectedIndex === draft.questions.length - 1 ? "Sang Tự luận" : "Câu tiếp theo")}
            </span>

            <Icon name="next" />
          </button>
        </div>

        <Link className="button button-primary" to={withExamId(essayHref, examId)} onClick={beforeNavigate}>{adminText(" Chuyển sang phần thi Tự luận ")}<Icon name="next" />
        </Link>
      </footer>

      <dialog ref={renameDialog}>
        <form onSubmit={submitRename}>
          <h2>{adminText("Sửa tên câu hỏi SQL")}</h2>

          <label htmlFor="rename-input">{adminText(" Tên câu hỏi ")}</label>

          <input id="rename-input" type="text" maxLength="200" value={renameTitle} onChange={event => setRenameTitle(event.target.value)} placeholder={adminText("Nhập tên câu hỏi...")} required />

          <div className="dialog-actions">
            <button className="button" type="button" onClick={() => renameDialog.current?.close()}>{adminText(" Hủy ")}</button>

            <button className="button button-primary" type="submit">{adminText(" Cập nhật ")}</button>
          </div>
        </form>
      </dialog>

      <dialog ref={previewDialog} className="preview-dialog">
        <h2>{adminText("Xem trước giao diện sinh viên")}</h2>

        <h3>{adminText(" Câu SQL ")}{adminRender(draft.selectedIndex + 1)}:{adminRender(" ")}
          {adminRender(question.title)}
        </h3>

        <p className="preview-description">
          {adminRender(question.description || "Chưa nhập mô tả đề bài.")}
        </p>

        <label htmlFor="student-sql">{adminText(" Bài làm SQL ")}</label>

        <textarea id="student-sql" className="sql-input" rows="8" value={studentSQL} onChange={event => setStudentSQL(event.target.value)} placeholder={adminText("Sinh viên nhập truy vấn tại đây...")} spellCheck={false} />

        <div className="dialog-actions">
          <button className="button" type="button" onClick={() => previewDialog.current?.close()}>{adminText(" Đóng ")}</button>
        </div>
      </dialog>

      <div className={`toast${toast ? " show" : ""}`} role="status" aria-live="polite">
        {adminRender(toast)}
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
    setError(adminText(""));
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
    <button ref={trigger} type="button" className="admin-account-trigger" aria-expanded={open} aria-label={adminText("Thông tin tài khoản Admin")} onClick={() => setOpen(value => !value)}>
      <span className="admin-account-avatar">{adminRender(initials)}</span>
      <span className="admin-account-caption"><strong>{adminRender(account.name)}</strong><small>{adminRender(account.email)}</small></span>
      <span aria-hidden="true" className="admin-account-chevron">⌄</span>
    </button>
    {adminRender(open && <div className="admin-account-panel">
      <div className="admin-account-panel-head"><span className="admin-account-avatar">{adminRender(initials)}</span><div><strong>{adminRender(account.name)}</strong><small>{adminText("Quản trị viên")}</small></div></div>
      <dl><div><dt>Email</dt><dd>{adminRender(account.email)}</dd></div><div><dt>{adminText("Số điện thoại")}</dt><dd>{adminRender(account.phone || "Chưa cập nhật")}</dd></div></dl>
      <Link to="/Cai_dat_Admin" onClick={() => setOpen(false)} className="admin-account-settings">{adminText("Cài đặt tài khoản")}</Link>
      <button type="button" className="admin-account-logout" disabled={busy} onClick={logout}>{adminRender(busy ? "Đang đăng xuất..." : "Đăng xuất")}</button>
      {adminRender(error && <p role="alert" className="admin-account-error">{adminRender(error)}</p>)}
    </div>)}
  </div>;
}