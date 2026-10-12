import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./TN_Admin.css";
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

  // Đồng bộ thông tin học phần giữa ba phần thi.
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
const SAMPLE_TITLES = ["Khái niệm ACID & Giao dịch CSDL", "Khóa ngoại & Ràng buộc toàn vẹn cơ sở dữ liệu", "Index B-Tree và tối ưu truy vấn", "Mức độ cô lập Isolation Levels", "Tối ưu hóa cây thực thi Query Plan", "Khóa bi quan vs Lạc quan", "Kỹ thuật Sharding & Replication", "Nguyên lý Chuẩn hóa BCNF & 3NF", "View và Materialized View", "Deadlock & Giải thuật phát hiện"];
function emptyQuestion(title = "") {
  return {
    title,
    content: "",
    answers: ["", "", "", ""],
    correct: null,
    explanation: "",
    points: "0.4"
  };
}
function createSampleQuestions() {
  const questions = SAMPLE_TITLES.map(emptyQuestion);
  questions[1] = {
    title: SAMPLE_TITLES[1],
    content: "Trong cơ sở dữ liệu quan hệ, cơ chế nào thiết lập " + "ràng buộc toàn vẹn tham chiếu giữa bảng cha và bảng con?",
    answers: ["Foreign Key Constraint", "Unique Index độc lập", "Clustered Index", "Check Constraint độc lập"],
    correct: 0,
    explanation: "Khóa ngoại thiết lập ràng buộc toàn vẹn tham chiếu " + "giữa hai bảng. Quy tắc ON DELETE CASCADE có thể " + "tự động xóa các bản ghi con khi bản ghi cha bị xóa.",
    points: "1.0"
  };
  return questions;
}
function validQuestion(question) {
  return question && ["title", "content", "explanation"].every(key => typeof question[key] === "string") && Array.isArray(question.answers) && question.answers.length >= 2 && question.answers.length <= 26 && question.answers.every(answer => typeof answer === "string") && (question.correct === null || Number.isInteger(question.correct) && question.correct >= 0 && question.correct < question.answers.length);
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
  const saved = readExamSection(examId, "tn");
  if (!saved || !Array.isArray(saved.questions) || saved.questions.length === 0 || !saved.questions.every(validQuestion)) {
    return fallback;
  }
  return {
    ...fallback,
    ...saved,
    testName: typeof saved.testName === "string" ? saved.testName : fallback.testName,
    major: typeof saved.major === "string" ? saved.major : fallback.major,
    schoolYear: typeof saved.schoolYear === "string" ? saved.schoolYear : fallback.schoolYear,
    duration: Number.isFinite(saved.duration) ? Math.max(10, Math.min(120, Math.round(saved.duration))) : 60,
    selectedIndex: Math.max(0, Math.min(saved.questions.length - 1, Number.isInteger(saved.selectedIndex) ? saved.selectedIndex : 0))
  };
}
function completeQuestion(question) {
  return Boolean(question.title.trim() && question.content.trim() && question.answers.every(answer => answer.trim()) && Number.isInteger(question.correct) && validPoints(question.points, 0.4));
}
const ICON_PATHS = {
  back: <path d="m12 19-7-7 7-7M5 12h14" />,
  next: <path d="m12 5 7 7-7 7M5 12h14" />,
  bell: <>
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
      <path d="M10 21h4" />
    </>,
  help: <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .7-1.5 1-1.5 2M12 16h.01" />
    </>,
  user: <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21v-2a8 8 0 0 1 16 0v2" />
    </>,
  book: <path d="M12 5v15M12 5C8 2 4 3 2 4v15c3-1 7-1 10 1M12 5c4-3 8-2 10-1v15c-3-1-7-1-10 1" />,
  clock: <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>,
  list: <path d="M9 6h12M9 12h12M9 18h12m-18-12 1 1 2-2m-3 7 1 1 2-2m-3 7 1 1 2-2" />,
  chart: <path d="M4 3v17h17M8 16v-5m5 5V7m5 9V4" />,
  edit: <path d="m16 3 5 5-12 12-6 1 1-6Zm-2 2 5 5" />,
  plus: <path d="M12 5v14M5 12h14" />,
  trash: <path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7" />,
  eye: <>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </>,
  save: <path d="M4 3h13l3 3v15H4ZM8 3v6h8V3M8 21v-8h8v8" />,
  light: <path d="M9 18h6M10 21h4M8 14a6 6 0 1 1 8 0c-1 1-1 2-1 4H9c0-2 0-3-1-4Z" />,
  down: <path d="m6 9 6 6 6-6" />
};
function Icon({
  name,
  className = ""
}) {
  return <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {adminRender(ICON_PATHS[name])}
    </svg>;
}
export default function TNAdmin(props) {
  useAdminLanguage();

  const {
    examId,
    seedExam
  } = useDraftIdentity();
  return <TNAdminEditor key={examId} {...props} examId={examId} seedExam={seedExam} />;
}
function TNAdminEditor({
  examId,
  seedExam,
  managementHref = "/Quan_ly_bai_kiem_tra_Admin",
  sqlHref = "/SQL_Admin"
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
  const [editingAnswer, setEditingAnswer] = useState(null);
  const [renameIndex, setRenameIndex] = useState(null);
  const [renameTitle, setRenameTitle] = useState("");
  const renameDialog = useRef(null);
  const previewDialog = useRef(null);
  const toastTimer = useRef(null);
  const question = draft.questions[draft.selectedIndex];
  const scores = examSummary("tn", draft, examId);
  const majorOptions = [...new Set(["Ngành Công nghệ phần mềm", "Ngành Hệ thống Thông tin Quản lý", "Ngành Khoa học Máy tính", "Ngành Kỹ thuật Phần mềm", "An ninh Mạng", draft.major])];
  const yearOptions = [...new Set(["2024 - 2025", "2025 - 2026", "2026 - 2027", draft.schoolYear])];
  useEffect(() => {
    return () => clearTimeout(toastTimer.current);
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
    if (Number.isFinite(number)) {
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
    setEditingAnswer(null);
    updateMeta("selectedIndex", Math.max(0, Math.min(draft.questions.length - 1, index)));
  }
  function addQuestion() {
    setDraft(old => ({
      ...old,
      questions: [...old.questions, emptyQuestion("Câu hỏi mới")],
      selectedIndex: old.questions.length
    }));
    setEditingAnswer(null);
  }
  function deleteQuestion(index) {
    if (draft.questions.length === 1) {
      notify(adminText("Phải giữ ít nhất một câu hỏi."));
      return;
    }
    setDraft(old => ({
      ...old,
      questions: old.questions.filter((_, itemIndex) => itemIndex !== index),
      selectedIndex: Math.max(0, Math.min(old.questions.length - 2, old.selectedIndex - (index < old.selectedIndex ? 1 : 0)))
    }));
    setEditingAnswer(null);
  }
  function updateAnswer(index, value) {
    updateQuestion({
      answers: question.answers.map((answer, itemIndex) => itemIndex === index ? value : answer)
    });
  }
  function addAnswer() {
    if (question.answers.length >= 26) {
      notify(adminText("Tối đa 26 phương án."));
      return;
    }
    updateQuestion({
      answers: [...question.answers, ""]
    });
    setEditingAnswer(question.answers.length);
  }
  function deleteAnswer(index) {
    if (question.answers.length <= 2) {
      notify(adminText("Phải giữ ít nhất hai phương án."));
      return;
    }
    let correct = question.correct;
    if (correct === index) {
      correct = null;
    } else if (Number.isInteger(correct) && correct > index) {
      correct -= 1;
    }
    updateQuestion({
      answers: question.answers.filter((_, itemIndex) => itemIndex !== index),
      correct
    });
    setEditingAnswer(null);
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
  function saveDraft(nextSection = "tn") {
    try {
      saveExamSection(examId, "tn", {
        ...draft,
        questions: draft.questions.map(item => ({
          ...item,
          points: questionScore(item, "tn")
        }))
      }, nextSection, seedExam || {});
      return true;
    } catch {
      notify(adminText("Không lưu được bản nháp trong trình duyệt."));
      return false;
    }
  }

  // Tạo bản nháp ngay khi mở trang lần đầu.
  useEffect(() => {
    saveDraft();
  }, [examId]);
  function returnToManagement(event) {
    if (!saveDraft()) {
      event.preventDefault();
    }
  }
  function goToSQL() {
    if (!saveDraft("sql")) return;
    navigate(withExamId(sqlHref, examId));
  }
  return <div className="dbcas-admin-mcq">
      <header className="topbar admin-unified-topbar">
        <div className="topbar-left">
          <Link className="back-button" to={managementHref} state={{
          activeTab: "draft"
        }} onClick={returnToManagement}>
            <Icon name="back" />
            <span>{adminText("Quay lại")}</span>
          </Link>

          <span className="divider" />

          <nav className="breadcrumb" aria-label={adminText("Đường dẫn")}>
            <span>{adminText("Quản lý đề thi")}</span>
            <span className="breadcrumb-slash">/</span>
            <span className="breadcrumb-current">{adminText(" Soạn bài kiểm tra ")}</span>
          </nav>
        </div>

        <div className="topbar-right">
          <button className="icon-button" type="button" aria-label={adminText("Trợ giúp")} onClick={() => notify(adminText("Soạn câu hỏi, chọn đáp án đúng rồi lưu bản nháp."))}>
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
              <span className="title-icon">
                <Icon name="book" />
              </span>{adminText(" THÔNG TIN HỌC PHẦN ")}</h2>

            <div className="form-field">
              <label htmlFor="test-name">{adminText(" TÊN BÀI KIỂM TRA ")}</label>

              <input id="test-name" type="text" value={draft.testName} onChange={event => updateMeta("testName", event.target.value)} />
            </div>

            <div className="form-field">
              <label htmlFor="major">{adminText("NGÀNH HỌC")}</label>

              <div className="select-wrapper">
                <select id="major" value={draft.major} onChange={event => updateMeta("major", event.target.value)}>
                  {adminRender(majorOptions.map(value => <option key={value} value={value}>
                      {adminRender(value)}
                    </option>))}
                </select>

                <Icon name="down" className="select-icon" />
              </div>
            </div>

            <div className="form-field">
              <label htmlFor="school-year">{adminText("NĂM HỌC")}</label>

              <div className="select-wrapper">
                <select id="school-year" value={draft.schoolYear} onChange={event => updateMeta("schoolYear", event.target.value)}>
                  {adminRender(yearOptions.map(value => <option key={value} value={value}>
                      {adminRender(value)}
                    </option>))}
                </select>

                <Icon name="down" className="select-icon" />
              </div>
            </div>

            <div className="form-field time-field">
              <div className="field-heading">
                <label htmlFor="duration">{adminText(" THỜI GIAN LÀM BÀI ")}</label>

                <span className="time-value">
                  {adminRender(draft.duration)}{adminText(" phút ")}</span>
              </div>

              <div className="duration-control">
                <button type="button" aria-label={adminText("Giảm 1 phút")} onClick={() => updateDuration(draft.duration - 1)}>
                  −
                </button>

                <div className="duration-input">
                  <Icon name="clock" />

                  <input id="duration" type="number" min="10" max="120" step="1" value={draft.duration} onChange={event => updateDuration(event.target.value)} aria-label={adminText("Số phút làm bài")} />

                  <span>{adminText("phút")}</span>
                </div>

                <button type="button" aria-label={adminText("Tăng 1 phút")} onClick={() => updateDuration(draft.duration + 1)}>
                  +
                </button>
              </div>

              <div className="duration-presets">
                {adminRender([45, 60, 90, 120].map(duration => <button key={duration} type="button" className={draft.duration === duration ? "active" : ""} onClick={() => updateDuration(duration)}>
                    {adminRender(duration)}m
                  </button>))}
              </div>
            </div>
          </section>

          <section className="card questions-card">
            <div className="card-heading">
              <h2 className="section-title">
                <Icon name="list" className="cyan" />{adminText(" CÂU HỎI TRẮC NGHIỆM ")}</h2>
            </div>

            <ol className="question-list">
              {adminRender(draft.questions.map((item, index) => {
              const completed = completeQuestion(item);
              return <li key={index} className={`question-item${index === draft.selectedIndex ? " selected" : ""}`}>
                    <span className="question-number">
                      {adminRender(String(index + 1).padStart(2, "0"))}
                    </span>

                    <button type="button" className="question-info question-select" onClick={() => selectQuestion(index)} aria-current={index === draft.selectedIndex ? "true" : undefined}>
                      <span className="question-title">
                        {adminRender(item.title || "Chưa đặt tên")}
                      </span>

                      <span className="question-points">
                        {adminRender(fmtPoints(questionScore(item, "tn")))}{adminText(" điểm ")}</span>
                    </button>

                    <div className="question-actions">
                      <span className={`question-status${completed ? " completed" : ""}`}>
                        {adminRender(completed ? "Đã soạn" : "Chưa hoàn tất")}
                      </span>

                      <button type="button" className="edit-question" aria-label={`Sửa tên câu ${index + 1}`} onClick={() => openRename(index)}>
                        <Icon name="edit" />
                      </button>

                      <button type="button" className="delete-question" aria-label={`Xóa câu ${index + 1}`} onClick={() => deleteQuestion(index)}>
                        <Icon name="trash" />
                      </button>
                    </div>
                  </li>;
            }))}
            </ol>

            <button className="add-question" type="button" onClick={addQuestion}>
              <Icon name="plus" />{adminText(" Thêm câu hỏi trắc nghiệm ")}</button>
          </section>
        </aside>

        <div className="main-content">
          <section className="card scoring-card">
            <div className="scoring-heading">
              <h2 className="section-title">
                <Icon name="chart" className="cyan" />{adminText(" CẤU TRÚC ĐIỂM THI & PHÂN BỔ CÂU HỎI ")}</h2>

              <div className="total-score">
                <span>{adminText("Tổng điểm:")}</span>
                <strong>
                  {adminRender(fmtPoints(scores.total))}{adminText(" Điểm •")}{adminRender(" ")}
                  {adminRender(scores.count)}{adminText(" câu ")}</strong>
              </div>
            </div>

            <div className="score-grid">
              <div className="score-item active">
                <div className="score-item-heading">
                  <strong>{adminText("1. TRẮC NGHIỆM")}</strong>

                  <span className="score-points">
                    {adminRender(fmtPoints(scores.tn.points))}{adminText(" đ ")}</span>
                </div>

                <p>
                  {adminRender(scores.tn.count)}{adminText(" câu • Tổng")}{adminRender(" ")}
                  {adminRender(fmtPoints(scores.tn.points))}{adminText(" điểm ")}</p>

                <span className="score-status">{adminText(" ĐANG SOẠN ")}</span>
              </div>

              <div className="score-item">
                <div className="score-item-heading">
                  <strong>{adminText("2. TRUY VẤN SQL")}</strong>

                  <span className="score-points">
                    {adminRender(fmtPoints(scores.sql.points))}{adminText(" đ ")}</span>
                </div>

                <p>
                  {adminRender(scores.sql.count)}{adminText(" câu • Tổng")}{adminRender(" ")}
                  {adminRender(fmtPoints(scores.sql.points))}{adminText(" điểm ")}</p>

                <span className="score-status">
                  {adminRender(scores.sql.count ? "Đã lưu nháp" : "Chưa có nháp")}
                </span>
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
                <span className="question-badge">{adminText(" CÂU")}{adminRender(" ")}
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
            }}>{adminText(" Điểm câu này ")}<input type="number" min="0.01" step="0.01" aria-label={adminText("Điểm câu hỏi")} value={question.points ?? 0.4} onChange={event => updateQuestion({
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
              <section className="question-section">
                <h2 className="section-title">
                  <Icon name="edit" className="cyan" />
                  <label htmlFor="question-content">{adminText(" CÂU HỎI ")}</label>
                </h2>

                <textarea id="question-content" className="question-textarea" rows="4" value={question.content} onChange={event => updateQuestion({
                content: event.target.value
              })} placeholder={adminText("Nhập nội dung câu hỏi...")} />
              </section>

              <section className="answers-section">
                <div className="answers-heading">
                  <h2 className="section-title">
                    <Icon name="list" className="cyan" />{adminText(" PHƯƠNG ÁN LỰA CHỌN (CHỌN 1 ĐÁP ÁN ĐÚNG) ")}</h2>

                  <span className="answer-count">
                    {adminRender(question.answers.length)}{adminText(" phương án ")}</span>
                </div>

                <div className="answer-list">
                  {adminRender(question.answers.map((answer, index) => {
                  const letter = String.fromCharCode(65 + index);
                  const isCorrect = question.correct === index;
                  const isEditing = editingAnswer === index;
                  return <div key={`${draft.selectedIndex}:${index}`} className={`answer-row${isCorrect ? " correct" : ""}`}>
                        <span className="answer-letter">
                          {adminRender(letter)}
                        </span>

                        <div className="answer-choice">
                          {adminRender(isEditing ? <input className="answer-edit-input" autoFocus value={answer} aria-label={`Nội dung phương án ${letter}`} onChange={event => updateAnswer(index, event.target.value)} onKeyDown={event => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          setEditingAnswer(null);
                        }
                      }} /> : <span className="answer-text">
                              {adminRender(answer || "Chưa nhập phương án")}
                            </span>)}

                          <label className="answer-action">
                            <span>
                              {adminRender(isCorrect ? "Đáp án đúng" : "Chọn đúng")}
                            </span>

                            <input type="radio" name="correct-answer" checked={isCorrect} onChange={() => updateQuestion({
                          correct: index
                        })} aria-label={`Chọn ${letter} là đáp án đúng`} />
                          </label>
                        </div>

                        <button type="button" className={`edit-answer${isEditing ? " editing" : ""}`} aria-label={isEditing ? "Hoàn tất sửa" : "Sửa phương án"} onClick={() => setEditingAnswer(isEditing ? null : index)}>
                          <Icon name="edit" />
                        </button>

                        <button type="button" className="delete-answer" aria-label={`Xóa phương án ${letter}`} onClick={() => deleteAnswer(index)}>
                          <Icon name="trash" />
                        </button>
                      </div>;
                }))}
                </div>

                <button type="button" className="add-answer" onClick={addAnswer}>
                  <Icon name="plus" />{adminText(" Thêm phương án lựa chọn ")}</button>
              </section>

              <section className="explanation-section">
                <h2 className="section-title">
                  <Icon name="light" />

                  <label htmlFor="explanation-text">{adminText(" GIẢI THÍCH ĐÁP ÁN & ĐỐI CHIẾU KIẾN THỨC ")}</label>
                </h2>

                <textarea id="explanation-text" className="explanation-textarea" rows="4" value={question.explanation} onChange={event => updateQuestion({
                explanation: event.target.value
              })} placeholder={adminText("Nhập giải thích đáp án và nội dung đối chiếu kiến thức...")} />
              </section>
            </div>
          </section>
        </div>
      </main>

      <footer className="bottom-toolbar">
        <div className="toolbar-actions">
          <button type="button" className="button button-secondary" onClick={() => previewDialog.current?.showModal()}>
            <Icon name="eye" />{adminText(" Xem trước giao diện sinh viên ")}</button>

          <button type="button" className="button button-secondary" onClick={() => {
          if (saveDraft()) {
            notify(adminText("Đã lưu bản nháp trong trình duyệt."));
          }
        }}>
            <Icon name="save" />{adminText(" Lưu bản nháp ")}</button>
        </div>

        <div className="question-navigation">
          <button type="button" className="button button-secondary" disabled={draft.selectedIndex === 0} onClick={() => selectQuestion(draft.selectedIndex - 1)}>
            <Icon name="back" />
            <span>{adminText("Câu trước")}</span>
          </button>

          <span className="page-indicator">
            {adminRender(draft.selectedIndex + 1)} /{adminRender(" ")}
            {adminRender(draft.questions.length)}
          </span>

          <button type="button" className="button button-secondary" disabled={draft.selectedIndex === draft.questions.length - 1} onClick={() => selectQuestion(draft.selectedIndex + 1)}>
            <span>{adminText("Câu tiếp theo")}</span>
            <Icon name="next" />
          </button>
        </div>

        <button type="button" className="button button-primary" onClick={goToSQL}>{adminText(" Chuyển sang phần thi SQL ")}<Icon name="next" />
        </button>
      </footer>

      <dialog ref={renameDialog} className="rename-dialog">
        <form onSubmit={submitRename}>
          <h2>{adminText("Sửa tên câu hỏi")}</h2>

          <label htmlFor="rename-input">{adminText(" Tên câu hỏi ")}</label>

          <input id="rename-input" type="text" maxLength="200" required value={renameTitle} onChange={event => setRenameTitle(event.target.value)} placeholder={adminText("Nhập tên câu hỏi...")} />

          <div className="dialog-actions">
            <button type="button" className="button button-secondary" onClick={() => renameDialog.current?.close()}>{adminText(" Hủy ")}</button>

            <button type="submit" className="button button-primary">{adminText(" Cập nhật ")}</button>
          </div>
        </form>
      </dialog>

      <dialog ref={previewDialog} className="rename-dialog preview-dialog">
        <h2>{adminText("Xem trước giao diện sinh viên")}</h2>

        <h3>{adminText(" Câu ")}{adminRender(draft.selectedIndex + 1)}: {adminRender(question.title)}
        </h3>

        <p className="preview-content">
          {adminRender(question.content || "Chưa nhập nội dung câu hỏi.")}
        </p>

        <ol>
          {adminRender(question.answers.map((answer, index) => <li key={index}>
              {adminRender(String.fromCharCode(65 + index))}.{adminRender(" ")}
              {adminRender(answer || "Chưa nhập phương án")}
            </li>))}
        </ol>

        <div className="dialog-actions">
          <button type="button" className="button button-secondary" onClick={() => previewDialog.current?.close()}>{adminText(" Đóng ")}</button>
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