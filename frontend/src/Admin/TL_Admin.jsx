import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./TL_Admin.css";
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
function flatExamQuestions(record) {
  const result = [];
  const mcqQuestions = record.sections?.tn?.questions || [];
  const sqlQuestions = record.sections?.sql?.questions || [];
  const essayQuestions = record.sections?.tl?.questions || [];
  mcqQuestions.forEach((question, index) => {
    result.push({
      id: `mcq-${index + 1}`,
      type: "mcq",
      topic: question.title,
      prompt: question.content,
      points: pointValue(question.points, 0.4),
      options: question.answers.map((text, optionIndex) => ({
        id: `option-${optionIndex}`,
        text
      })),
      correctId: `option-${question.correct}`,
      explanation: question.explanation || ""
    });
  });
  sqlQuestions.forEach((question, index) => {
    result.push({
      id: `sql-${index + 1}`,
      type: "sql",
      topic: question.title,
      prompt: question.description,
      points: pointValue(question.points, 1),
      answer: question.sql,
      keywords: question.keywords || []
    });
  });
  essayQuestions.forEach((question, index) => {
    const criteria = question.criteria || [];
    result.push({
      id: `essay-${index + 1}`,
      type: "essay",
      topic: question.title,
      prompt: question.description,
      answer: question.answer,
      points: questionScore(question, "tl"),
      rubricItems: criteria.map((item, criterionIndex) => ({
        id: `rubric-${criterionIndex}`,
        title: item.title,
        points: pointValue(item.points),
        description: ""
      })),
      rubric: criteria.map(item => `${item.title}: ${pointValue(item.points)} điểm`).join(". ")
    });
  });
  return result;
}
function completeExamDraft(examId) {
  const allDrafts = readExamDrafts();
  const previous = allDrafts[examId];
  if (!previous) {
    throw new Error("Không tìm thấy bản nháp của đề.");
  }
  const record = {
    ...previous,
    status: "published",
    questions: flatExamQuestions(previous),
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
const DEFAULT_QUESTIONS = [{
  title: "Kiến trúc Sharding & Phân tán CSDL",
  description: "Phân tích giải pháp mở rộng quy mô bằng " + "Horizontal Partitioning và Sharding cho hệ thống " + "thương mại điện tử có 50 triệu người dùng. " + "Đề xuất chiến lược chọn Shard Key, xử lý Data Skew " + "và đảm bảo giao dịch phân tán bằng " + "Two-Phase Commit hoặc Saga.",
  answer: "1. So sánh Partitioning và Sharding:\n" + "Partitioning chia dữ liệu thành các phần; Sharding " + "phân phối dữ liệu trên nhiều máy chủ để mở rộng.\n\n" + "2. Chọn Shard Key:\n" + "Chọn theo mẫu truy vấn và phân bố dữ liệu. " + "Có thể dùng User_ID, Virtual Shards hoặc Salting " + "để hạn chế dữ liệu phân bố không đều.\n\n" + "3. Giao dịch phân tán:\n" + "Phân tích ưu nhược điểm của Two-Phase Commit " + "và Saga; lựa chọn theo yêu cầu nhất quán " + "và khả năng chịu lỗi.",
  criteria: [{
    title: "So sánh Partitioning và Sharding",
    points: 1
  }, {
    title: "Chọn Shard Key và xử lý Data Skew",
    points: 1
  }, {
    title: "Phân tích giao dịch phân tán",
    points: 1
  }]
}];
function normalizeQuestion(source) {
  const question = source && typeof source === "object" ? source : {};
  return {
    title: String(question.title || ""),
    description: String(question.description || ""),
    answer: String(question.answer || ""),
    criteria: Array.isArray(question.criteria) ? question.criteria.map(item => ({
      title: String(item?.title || ""),
      points: pointValue(item?.points)
    })) : []
  };
}
function initialDraft(examId, seedExam) {
  const saved = readExamSection(examId, "tl");
  const fallbackCourse = {
    testName: "Kiểm tra Cơ sở Dữ liệu Nâng cao",
    major: "Ngành Công nghệ phần mềm",
    schoolYear: "2024 - 2025",
    duration: 60
  };
  const questions = (Array.isArray(saved?.questions) && saved.questions.length > 0 ? saved.questions : DEFAULT_QUESTIONS).map(normalizeQuestion);
  return {
    course: draftCourse(examId, seedExam || {}, fallbackCourse),
    questions,
    selectedIndex: Math.max(0, Math.min(questions.length - 1, Number.isInteger(saved?.selectedIndex) ? saved.selectedIndex : 0))
  };
}
function completeQuestion(question) {
  return Boolean(question.title.trim() && question.description.trim() && question.answer.trim() && question.criteria.length > 0 && question.criteria.every(item => item.title.trim() && validPoints(item.points)));
}
function mcqComplete(question) {
  return Boolean(question && typeof question.title === "string" && question.title.trim() && typeof question.content === "string" && question.content.trim() && Array.isArray(question.answers) && question.answers.length >= 2 && question.answers.every(answer => typeof answer === "string" && answer.trim()) && Number.isInteger(question.correct) && question.correct >= 0 && question.correct < question.answers.length && validPoints(question.points, 0.4));
}
function sqlComplete(question) {
  return Boolean(question && ["title", "description", "sql"].every(key => typeof question[key] === "string" && question[key].trim()) && validPoints(question.points, 1));
}
function validateExam(tn, sql, essay) {
  if (!Array.isArray(tn?.questions) || tn.questions.length === 0 || !tn.questions.every(mcqComplete)) {
    return "Phần trắc nghiệm chưa soạn đủ hoặc điểm câu " + "không hợp lệ. Quay lại TN để kiểm tra.";
  }
  if (!Array.isArray(sql?.questions) || sql.questions.length === 0 || !sql.questions.every(sqlComplete)) {
    return "Phần SQL chưa soạn đủ hoặc điểm câu không hợp lệ. " + "Quay lại SQL để kiểm tra.";
  }
  if (essay.questions.length === 0 || !essay.questions.every(completeQuestion)) {
    return "Nhập đủ tên, đề bài, đáp án mẫu và tiêu chí " + "có điểm lớn hơn 0 cho từng câu tự luận.";
  }
  return "";
}
const ICON_PATHS = {
  back: "M12 5 5 12l7 7M5 12h14",
  left: "m15 6-6 6 6 6",
  right: "m9 6 6 6-6 6",
  plus: "M12 5v14M5 12h14",
  clock: "M12 7v5l3 2",
  user: "M4 21v-2a8 8 0 0 1 16 0v2",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
  help: "M9.5 9a2.5 2.5 0 1 1 4 2c-1 .6-1.5 1-1.5 2M12 17h.01",
  book: "M12 5v15M12 5C8 2 4 3 2 4v15c3-1 6-1 10 1 4-2 7-2 10-1V4c-2-1-6-2-10 1Z",
  file: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8ZM14 2v6h6M8 12h8M8 16h6",
  chart: "M4 3v18h17M8 16v-5M13 16V7M18 16v-8",
  check: "m5 12 4 4L19 6",
  edit: "m16 3 5 5-12 12-6 1 1-6ZM14 5l5 5",
  trash: "M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7",
  list: "M9 6h12M9 12h12M9 18h12M3 6h.01M3 12h.01M3 18h.01",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z",
  save: "M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h12l4 4v12a2 2 0 0 1-2 2ZM7 3v6h10V3M7 21v-8h10v8"
};
function Icon({
  name
}) {
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {adminRender(["clock", "help"].includes(name) && <circle cx="12" cy="12" r="9" />)}

      {adminRender(name === "user" && <circle cx="12" cy="8" r="4" />)}

      {adminRender(name === "eye" && <circle cx="12" cy="12" r="3" />)}

      <path d={ICON_PATHS[name] || ICON_PATHS.file} />
    </svg>;
}
const MAJORS = ["Ngành Công nghệ phần mềm", "Ngành Hệ thống Thông tin Quản lý", "Ngành Khoa học Máy tính", "Ngành Kỹ thuật Phần mềm", "An ninh Mạng"];
const YEARS = ["2024 - 2025", "2025 - 2026", "2026 - 2027"];
export default function TLAdmin(props) {
  useAdminLanguage();

  const {
    examId,
    seedExam
  } = useDraftIdentity();
  return <TLAdminEditor key={examId} {...props} examId={examId} seedExam={seedExam} />;
}
function TLAdminEditor({
  examId,
  seedExam,
  sqlHref = "/SQL_Admin",
  managementHref = "/Quan_ly_bai_kiem_tra_Admin"
}) {
  const navigate = useNavigate();
  const [draft, setDraft] = useState(() => initialDraft(examId, seedExam));
  const [toast, setToast] = useState("");
  const [isError, setIsError] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);
  const [renameIndex, setRenameIndex] = useState(null);
  const [renameTitle, setRenameTitle] = useState("");
  const [studentAnswer, setStudentAnswer] = useState("");
  const [finishing, setFinishing] = useState(false);
  const renameDialog = useRef(null);
  const previewDialog = useRef(null);
  const toastTimer = useRef(null);
  const finishLock = useRef(false);
  const question = draft.questions[draft.selectedIndex];
  const scores = examSummary("tl", draft, examId);
  const majorOptions = [...new Set([...MAJORS, draft.course.major])];
  const yearOptions = [...new Set([...YEARS, draft.course.schoolYear])];
  useEffect(() => {
    return () => clearTimeout(toastTimer.current);
  }, []);
  function notify(message, error = false) {
    clearTimeout(toastTimer.current);
    setToast(message);
    setIsError(error);
    toastTimer.current = setTimeout(() => {
      setToast("");
    }, 4500);
  }
  function updateCourse(key, value) {
    setDraft(old => ({
      ...old,
      course: {
        ...old.course,
        [key]: value
      }
    }));
  }
  function updateDuration(value) {
    const number = Number(value);
    if (String(value).trim() !== "" && Number.isFinite(number)) {
      updateCourse("duration", Math.max(10, Math.min(120, Math.round(number))));
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
    setEditingIndex(null);
    setDraft(old => ({
      ...old,
      selectedIndex: Math.max(0, Math.min(old.questions.length - 1, index))
    }));
  }
  function addQuestion() {
    setDraft(old => ({
      ...old,
      questions: [...old.questions, normalizeQuestion({})],
      selectedIndex: old.questions.length
    }));
    setEditingIndex(null);
  }
  function deleteQuestion(index) {
    if (draft.questions.length === 1) {
      notify(adminText("Cần giữ ít nhất một câu tự luận."), true);
      return;
    }
    setDraft(old => ({
      ...old,
      questions: old.questions.filter((_, itemIndex) => itemIndex !== index),
      selectedIndex: Math.max(0, Math.min(old.questions.length - 2, old.selectedIndex - (index < old.selectedIndex ? 1 : 0)))
    }));
    setEditingIndex(null);
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
  function updateCriterion(index, patch) {
    updateQuestion({
      criteria: question.criteria.map((item, itemIndex) => itemIndex === index ? {
        ...item,
        ...patch
      } : item)
    });
  }
  function addCriterion() {
    updateQuestion({
      criteria: [...question.criteria, {
        title: "",
        points: 0
      }]
    });
    setEditingIndex(question.criteria.length);
  }
  function deleteCriterion(index) {
    updateQuestion({
      criteria: question.criteria.filter((_, itemIndex) => itemIndex !== index)
    });
    setEditingIndex(null);
  }
  function saveDraft(nextSection = "tl") {
    try {
      saveExamSection(examId, "tl", {
        ...draft,
        questions: draft.questions.map(normalizeQuestion)
      }, nextSection, seedExam || {});
      return true;
    } catch {
      notify(adminText("Không lưu được bản nháp tự luận trong trình duyệt."), true);
      return false;
    }
  }
  function beforeNavigate(event) {
    const nextSection = sectionFromHref(event.currentTarget.getAttribute("href"), "tl");
    if (!saveDraft(nextSection)) {
      event.preventDefault();
    }
  }
  useEffect(() => {
    saveDraft();
  }, [examId]);
  function finishExam() {
    if (finishLock.current) return;
    if (!draft.course.testName.trim()) {
      notify(adminText("Vui lòng nhập tên bài kiểm tra."), true);
      return;
    }
    const tn = readExamSection(examId, "tn");
    const sql = readExamSection(examId, "sql");
    const error = validateExam(tn, sql, draft);
    if (error) {
      const incompleteIndex = draft.questions.findIndex(item => !completeQuestion(item));
      if (incompleteIndex >= 0) {
        selectQuestion(incompleteIndex);
      }
      notify(error, true);
      return;
    }
    const confirmed = window.confirm(adminText("Bạn đã hoàn tất đề thi và muốn lưu rồi " + "quay lại danh sách chưa?\n\n" + "OK: Lưu bài và thoát.\n" + "Hủy: Tiếp tục chỉnh sửa."));
    if (!confirmed) return;
    finishLock.current = true;
    setFinishing(true);
    try {
      const finalDraft = {
        ...draft,
        course: {
          ...draft.course,
          testName: draft.course.testName.trim()
        },
        questions: draft.questions.map(normalizeQuestion)
      };
      saveExamSection(examId, "tl", finalDraft, "tl", seedExam || {});
      completeExamDraft(examId);
      navigate(managementHref, {
        state: {
          activeTab: "published"
        }
      });
    } catch (error) {
      notify(error instanceof Error ? error.message : "Chưa lưu được bộ đề.", true);
    } finally {
      finishLock.current = false;
      setFinishing(false);
    }
  }
  function openPreview() {
    setStudentAnswer("");
    previewDialog.current?.showModal();
  }
  return <div className="dbcas-admin-essay">
      <header className="topbar admin-unified-topbar">
        <div className="topbar-left">
          <Link className="back-button" to={withExamId(sqlHref, examId)} onClick={beforeNavigate}>
            <Icon name="back" />{adminText(" Quay lại ")}</Link>

          <span className="divider" />

          <nav className="breadcrumb" aria-label={adminText("Đường dẫn")}>
            <span>{adminText("Quản lý bài kiểm tra")}</span>
            <span>/</span>
            <strong>{adminText("Soạn bài kiểm tra")}</strong>
          </nav>
        </div>

        <div className="topbar-right">
          <button className="icon-button" type="button" aria-label={adminText("Trợ giúp")} onClick={() => notify(adminText("Soạn đề, đáp án mẫu và tiêu chí. " + "Điểm câu hỏi bằng tổng điểm các tiêu chí."))}>
            <Icon name="help" />
          </button>

          <NotificationMenu role="admin" className="icon-button notification-button" />

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
              <label htmlFor="tl-test-name">{adminText(" TÊN BÀI KIỂM TRA ")}</label>

              <input id="tl-test-name" value={draft.course.testName} onChange={event => updateCourse("testName", event.target.value)} />
            </div>

            <div className="form-field">
              <label htmlFor="tl-major">{adminText(" NGÀNH HỌC ")}</label>

              <select id="tl-major" value={draft.course.major} onChange={event => updateCourse("major", event.target.value)}>
                {adminRender(majorOptions.map(value => <option key={value} value={value}>
                    {adminRender(value)}
                  </option>))}
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="tl-year">{adminText(" NĂM HỌC ")}</label>

              <select id="tl-year" value={draft.course.schoolYear} onChange={event => updateCourse("schoolYear", event.target.value)}>
                {adminRender(yearOptions.map(value => <option key={value} value={value}>
                    {adminRender(value)}
                  </option>))}
              </select>
            </div>

            <div className="form-field">
              <div className="field-heading">
                <label htmlFor="tl-duration">{adminText(" THỜI GIAN LÀM BÀI ")}</label>

                <span className="time-value">
                  {adminRender(draft.course.duration)}{adminText(" phút ")}</span>
              </div>

              <div className="duration-control">
                <button className="duration-button" type="button" disabled={draft.course.duration <= 10} aria-label={adminText("Giảm thời gian")} onClick={() => updateDuration(draft.course.duration - 1)}>
                  −
                </button>

                <div className="duration-input">
                  <Icon name="clock" />

                  <input id="tl-duration" type="number" min="10" max="120" step="1" value={draft.course.duration} onChange={event => updateDuration(event.target.value)} />

                  <span>{adminText("phút")}</span>
                </div>

                <button className="duration-button" type="button" disabled={draft.course.duration >= 120} aria-label={adminText("Tăng thời gian")} onClick={() => updateDuration(draft.course.duration + 1)}>
                  +
                </button>
              </div>

              <div className="duration-presets">
                {adminRender([45, 60, 90, 120].map(value => <button key={value} type="button" className={draft.course.duration === value ? "active" : ""} aria-pressed={draft.course.duration === value} onClick={() => updateDuration(value)}>
                    {adminRender(value)}m
                  </button>))}
              </div>
            </div>
          </section>

          <section className="card questions-card">
            <h2 className="section-title questions-heading">
              <Icon name="file" />{adminText(" CÂU TỰ LUẬN ")}</h2>

            <ol className="question-list">
              {adminRender(draft.questions.map((item, index) => <li key={index} className={`question-item${draft.selectedIndex === index ? " selected" : ""}`}>
                  <button className="question-select" type="button" aria-pressed={draft.selectedIndex === index} onClick={() => selectQuestion(index)}>
                    <span className="question-number">
                      {adminRender(String(index + 1).padStart(2, "0"))}
                    </span>

                    <span className="question-info">
                      <span className={`question-title${item.title ? "" : " placeholder"}`}>
                        {adminRender(item.title || "Nhập tên câu hỏi...")}
                      </span>

                      <span className="question-points">
                        {adminRender(fmtPoints(questionScore(item, "tl")))}{adminRender(" ")}{adminText(" điểm ")}</span>
                    </span>
                  </button>

                  <div className="question-actions">
                    <button className="small-button" type="button" aria-label={`Sửa tên câu ${index + 1}`} onClick={() => openRename(index)}>
                      <Icon name="edit" />
                    </button>

                    <button className="small-button delete-button" type="button" aria-label={`Xóa câu ${index + 1}`} onClick={() => deleteQuestion(index)}>
                      <Icon name="trash" />
                    </button>

                    <span className={`question-status${completeQuestion(item) ? " completed" : ""}`}>
                      {adminRender(draft.selectedIndex === index ? "ĐANG CHỌN" : completeQuestion(item) ? "ĐÃ XONG" : "BẢN NHÁP")}
                    </span>
                  </div>
                </li>))}
            </ol>

            <button className="add-button" type="button" onClick={addQuestion}>
              <Icon name="plus" />{adminText(" Thêm câu hỏi tự luận ")}</button>
          </section>
        </aside>

        <div className="main-content">
          <section className="card score-card">
            <div className="score-card-heading">
              <h2 className="section-title">
                <Icon name="chart" />{adminText(" CẤU TRÚC ĐIỂM THI & PHÂN BỔ CÂU HỎI ")}</h2>

              <div className="total-score">{adminText(" Tổng điểm: ")}<strong>
                  {adminRender(fmtPoints(scores.total))}{adminText(" Điểm •")}{adminRender(" ")}
                  {adminRender(scores.count)}{adminText(" câu ")}</strong>
              </div>
            </div>

            <div className="score-grid">
              <div className="score-item">
                <div className="score-heading">
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

              <div className="score-item">
                <div className="score-heading">
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

              <div className="score-item active">
                <div className="score-heading">
                  <strong>{adminText("3. TỰ LUẬN CSDL")}</strong>

                  <span className="score-points">
                    {adminRender(fmtPoints(scores.tl.points))}{adminText(" đ ")}</span>
                </div>

                <p>
                  {adminRender(scores.tl.count)}{adminText(" câu • Tổng")}{adminRender(" ")}
                  {adminRender(fmtPoints(scores.tl.points))}{adminText(" điểm ")}</p>

                <span className="score-status">{adminText(" ĐANG SOẠN ")}</span>
              </div>
            </div>
          </section>

          <section className="card editor-card">
            <header className="editor-heading"><NotificationMenu role="admin" className="icon-button" />
              <div>
                <span className="question-badge">{adminText(" CÂU")}{adminRender(" ")}
                  {adminRender(String(draft.selectedIndex + 1).padStart(2, "0"))}{adminRender(" ")}
                  /{adminRender(" ")}
                  {adminRender(String(draft.questions.length).padStart(2, "0"))}
                </span>

                <h1>
                  {adminRender(question.title || "Chưa đặt tên câu hỏi")}
                </h1>
              </div>

              <span className="point-badge">{adminText(" Điểm số:")}{adminRender(" ")}
                {adminRender(fmtPoints(questionScore(question, "tl")))}{adminRender(" ")}{adminText(" điểm ")}</span>
            </header>

            <div className="editor-body">
              <section>
                <label className="section-title" htmlFor="tl-description">
                  <Icon name="file" />{adminText(" ĐỀ BÀI TỰ LUẬN ")}</label>

                <textarea id="tl-description" className="content-textarea" placeholder={adminText("Nhập đề bài tự luận...")} value={question.description} onChange={event => updateQuestion({
                description: event.target.value
              })} />
              </section>

              <section>
                <label className="section-title accent-title" htmlFor="tl-answer">
                  <Icon name="check" />{adminText(" ĐÁP ÁN MẪU & HƯỚNG DẪN CHẤM ")}</label>

                <textarea id="tl-answer" className="content-textarea answer-textarea" placeholder={adminText("Nhập đáp án mẫu và hướng dẫn chấm...")} value={question.answer} onChange={event => updateQuestion({
                answer: event.target.value
              })} />
              </section>

              <section className="criteria-section">
                <div className="section-heading">
                  <h2 className="section-title accent-title">
                    <Icon name="list" />{adminText(" TIÊU CHÍ CHẤM ĐIỂM ")}</h2>

                  <button className="small-add-button" type="button" onClick={addCriterion}>
                    <Icon name="plus" />{adminText(" Thêm tiêu chí ")}</button>
                </div>

                <div className="criteria-list">
                  {adminRender(question.criteria.length === 0 && <p className="empty-message">{adminText(" Chưa có tiêu chí. Bấm “Thêm tiêu chí” để bổ sung. ")}</p>)}

                  {adminRender(question.criteria.map((item, index) => {
                  const isEditing = editingIndex === index;
                  return <div key={`${draft.selectedIndex}:${index}`} className={`criterion-row${isEditing ? " editing" : ""}`}>
                        <span className="criterion-number">
                          {adminRender(index + 1)}
                        </span>

                        {adminRender(isEditing ? <>
                            <input className="criterion-title-input" autoFocus value={item.title} placeholder={adminText("Nhập tên tiêu chí...")} aria-label={adminText("Tên tiêu chí")} onChange={event => updateCriterion(index, {
                        title: event.target.value
                      })} onKeyDown={event => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          setEditingIndex(null);
                        }
                      }} />

                            <input className="criterion-points-input" type="number" min="0" step="0.01" value={item.points} aria-label={adminText("Điểm tiêu chí")} onChange={event => updateCriterion(index, {
                        points: event.target.value
                      })} />
                          </> : <>
                            <span className={`criterion-title${item.title ? "" : " placeholder"}`}>
                              {adminRender(item.title || "Nhập tên tiêu chí...")}
                            </span>

                            <span className="criterion-points">
                              {adminRender(fmtPoints(item.points))}{adminText(" đ ")}</span>
                          </>)}

                        <div className="criterion-actions">
                          <button className="small-button" type="button" aria-label={isEditing ? "Hoàn tất sửa tiêu chí" : "Sửa tiêu chí"} onClick={() => setEditingIndex(isEditing ? null : index)}>
                            <Icon name={isEditing ? "check" : "edit"} />
                          </button>

                          <button className="small-button delete-button" type="button" aria-label={adminText("Xóa tiêu chí")} onClick={() => deleteCriterion(index)}>
                            <Icon name="trash" />
                          </button>
                        </div>
                      </div>;
                }))}
                </div>

                <p className="criteria-note">{adminText(" Điểm câu hỏi bằng tổng điểm các tiêu chí. Tổng điểm đề được tự cộng từ trắc nghiệm, SQL và tự luận. ")}</p>
              </section>
            </div>
          </section>
        </div>
      </main>

      <footer className="page-footer">
        <div className="footer-tools">
          <button className="button" type="button" onClick={openPreview}>
            <Icon name="eye" />{adminText(" Xem trước giao diện sinh viên ")}</button>

          <button className="button" type="button" onClick={() => {
          if (saveDraft()) {
            notify(adminText("Đã lưu bản nháp tự luận trong trình duyệt."));
          }
        }}>
            <Icon name="save" />{adminText(" Lưu bản nháp ")}</button>
        </div>

        <div className="footer-navigation">
          <Link className="button" to={withExamId(sqlHref, examId)} onClick={beforeNavigate}>
            <Icon name="back" />{adminText(" Bài trước (SQL) ")}</Link>

          <button className="button" type="button" disabled={draft.selectedIndex === 0} onClick={() => selectQuestion(draft.selectedIndex - 1)}>
            <Icon name="left" />{adminText(" Câu trước ")}</button>

          <span className="page-indicator">
            {adminRender(draft.selectedIndex + 1)} /{adminRender(" ")}
            {adminRender(draft.questions.length)}
          </span>

          <button className="button" type="button" disabled={draft.selectedIndex === draft.questions.length - 1} onClick={() => selectQuestion(draft.selectedIndex + 1)}>{adminText(" Câu tiếp theo ")}<Icon name="right" />
          </button>

          <button className="button primary" type="button" disabled={finishing} onClick={finishExam}>
            <Icon name="check" />
            {adminRender(finishing ? "Đang lưu..." : "Lưu bài")}
          </button>
        </div>
      </footer>

      <dialog className="dialog" ref={renameDialog}>
        <form onSubmit={submitRename}>
          <h2>{adminText("Chỉnh sửa tên câu hỏi")}</h2>

          <label htmlFor="tl-rename">{adminText(" Tên câu hỏi ")}</label>

          <input id="tl-rename" required maxLength={200} value={renameTitle} onChange={event => setRenameTitle(event.target.value)} />

          <div className="dialog-actions">
            <button className="button" type="button" onClick={() => renameDialog.current?.close()}>{adminText(" Hủy ")}</button>

            <button className="button primary" type="submit">{adminText(" Cập nhật ")}</button>
          </div>
        </form>
      </dialog>

      <dialog className="dialog preview-dialog" ref={previewDialog}>
        <h2>{adminText(" Câu ")}{adminRender(draft.selectedIndex + 1)}:{adminRender(" ")}
          {adminRender(question.title || "Chưa đặt tên câu hỏi")}
        </h2>

        <p className="preview-description">
          {adminRender(question.description || "Chưa nhập đề bài.")}
        </p>

        <label htmlFor="tl-student-answer">{adminText(" Bài làm của sinh viên ")}</label>

        <textarea className="content-textarea" id="tl-student-answer" value={studentAnswer} onChange={event => setStudentAnswer(event.target.value)} placeholder={adminText("Nhập câu trả lời...")} />

        <div className="dialog-actions">
          <button className="button" type="button" onClick={() => previewDialog.current?.close()}>{adminText(" Đóng ")}</button>
        </div>
      </dialog>

      <div className={`toast${toast ? " show" : ""}${isError ? " error" : ""}`} role="status" aria-live="polite">
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