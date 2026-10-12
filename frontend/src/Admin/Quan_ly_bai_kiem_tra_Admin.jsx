import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./Quan_ly_bai_kiem_tra_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";
const EXAM_DRAFT_KEY = "dbcas-exam-drafts-v1";
const STORAGE_KEY = "dbcas-exam-management-v1";
const CONTENT_STORAGE_KEY = "dbcas-exam-content-v1";
const PAGE_SIZE = 10;
const DRAFT_ROUTES = {
  mcq: "/TN_Admin",
  sql: "/SQL_Admin",
  essay: "/TL_Admin"
};
const NAV_ITEMS = [["home", "Trang chủ", "/Home_Admin"], ["users", "Đánh giá năng lực", "/Danh_gia_nang_luc_Admin"], ["cap", "CLO & Kỹ năng", "/CLO_Ky_nang_Admin"], ["document", "Quản lý bài kiểm tra", "/Quan_ly_bai_kiem_tra_Admin"], ["robot", "Đánh giá bằng AI", "/Danh_gia_AI_Admin"], ["chart", "Báo cáo", "/Bao_cao_Admin"], ["settings", "Cài đặt", "/Cai_dat_Admin"]];
const EXAM_TITLES = ["KT CSDL Cơ Bản", "KT CSDL Nâng Cao", "SQL & Indexing Lab", "Thiết kế và Chuẩn hóa CSDL", "Transaction & ACID"];
const START_TIMES = ["08:00", "09:30", "13:00", "14:30", "15:30"];
const DURATIONS = [45, 60, 75, 90];

// 100 sinh viên được phân vào 27 bài đã công bố.
const DEMO_STUDENTS = Array.from({
  length: 100
}, (_, index) => ({
  studentId: String(21200000001 + index),
  examId: `DEMO-EXAM-${String(index % 27 + 1).padStart(3, "0")}`
}));

// 27 bài đã công bố và 13 bản nháp.
const DEMO_EXAMS = Array.from({
  length: 40
}, (_, index) => {
  const number = index + 1;
  const isDraft = number > 27;
  const id = `DEMO-EXAM-${String(number).padStart(3, "0")}`;
  return {
    id,
    title: isDraft ? `Đề đang soạn ${number - 27}` : EXAM_TITLES[index % EXAM_TITLES.length],
    status: isDraft ? "draft" : "published",
    draftStep: "mcq",
    date: isDraft ? "" : `2026-10-${String(index % 28 + 1).padStart(2, "0")}`,
    startTime: isDraft ? "" : START_TIMES[index % START_TIMES.length],
    duration: DURATIONS[index % DURATIONS.length],
    studentCount: DEMO_STUDENTS.filter(student => student.examId === id).length,
    mcqCount: 10,
    sqlCount: 3,
    essayCount: 1
  };
});
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
function draftExamMetadata(record) {
  return {
    id: record.id,
    title: record.course?.testName || record.title || "Đề chưa đặt tên",
    status: record.status,
    draftStep: record.draftStep || "mcq",
    date: record.date || "",
    startTime: record.startTime || "",
    duration: Number(record.course?.duration || record.duration) || 60,
    major: record.course?.major || "",
    year: record.course?.schoolYear || "",
    studentCount: Number(record.studentCount) || 0,
    mcqCount: record.sections?.tn?.questions?.length || 0,
    sqlCount: record.sections?.sql?.questions?.length || 0,
    essayCount: record.sections?.tl?.questions?.length || 0
  };
}
function readExamContent() {
  try {
    const data = JSON.parse(localStorage.getItem(CONTENT_STORAGE_KEY) || "{}");
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      return {};
    }
    return Object.fromEntries(Object.entries(data).filter(([, record]) => {
      return record && Array.isArray(record.questions) && record.questions.every(question => question && ["mcq", "sql", "essay"].includes(question.type));
    }));
  } catch {
    return {};
  }
}
function normalizeText(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase().trim();
}
function isValidDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(0);
  date.setFullYear(year, month - 1, day);
  date.setHours(0, 0, 0, 0);
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
}
function formatDate(value) {
  if (!value || !isValidDate(value)) {
    return "Chưa chọn ngày";
  }
  const [year, month, day] = value.split("-");
  return `${day}/${month}/${year}`;
}
function getEndTime(startTime, duration) {
  if (!/^\d{2}:\d{2}$/.test(startTime)) {
    return null;
  }
  const minutes = Number(duration);
  const [hour, minute] = startTime.split(":").map(Number);
  if (!Number.isInteger(minutes) || minutes < 1 || minutes > 600 || hour > 23 || minute > 59) {
    return null;
  }
  const total = hour * 60 + minute + minutes;
  return {
    time: `${String(Math.floor(total % 1440 / 60)).padStart(2, "0")}:` + `${String(total % 60).padStart(2, "0")}`,
    nextDay: total >= 1440
  };
}
function validateSchedule(form) {
  if (!form.date || !form.startTime) {
    return "Vui lòng chọn ngày thi và giờ bắt đầu.";
  }
  if (!isValidDate(form.date)) {
    return "Ngày thi không hợp lệ.";
  }
  const duration = Number(form.duration);
  if (!Number.isInteger(duration) || duration < 1 || duration > 600) {
    return "Thời lượng phải là số nguyên từ 1 đến 600 phút.";
  }
  if (!getEndTime(form.startTime, duration)) {
    return "Giờ bắt đầu không hợp lệ.";
  }
  return "";
}
function readSchedules() {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    const schedules = data.schedules;
    if (!schedules || typeof schedules !== "object" || Array.isArray(schedules)) {
      return {};
    }
    return Object.fromEntries(Object.entries(schedules).filter(([, schedule]) => schedule && typeof schedule === "object" && !validateSchedule(schedule)));
  } catch {
    return {};
  }
}
function getPageNumbers(currentPage, totalPages) {
  const pages = [...new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1])].filter(number => number >= 1 && number <= totalPages).sort((a, b) => a - b);
  const result = [];
  pages.forEach((number, index) => {
    if (index > 0 && number - pages[index - 1] > 1) {
      result.push(`gap-${number}`);
    }
    result.push(number);
  });
  return result;
}
function Icon({
  name
}) {
  const paths = {
    plus: "M12 5v14M5 12h14",
    home: "m3 10 9-7 9 7v10H3zM9 20v-7h6v7",
    users: "M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5.65",
    cap: "m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v7",
    document: "M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6",
    robot: "M4 7h16v13H4zM12 3v4M2 11v5M22 11v5M8 12h1M15 12h1M9 16h6",
    chart: "M4 3v17h17M8 16v-5M13 16V7M18 16V4",
    settings: "m9 3-1 3-3 1v4l-2 1 2 1v4l3 1 1 3h6l1-3 3-1v-4l2-1-2-1V7l-3-1-1-3z",
    logout: "M10 4H4v16h6M9 12h12M17 8l4 4-4 4",
    search: "m16 16 5 5",
    help: "M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 2-2.5 3.5M12 16h.01",
    bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
    chevron: "m8 5 7 7-7 7",
    clock: "M12 7v5l3 2",
    close: "m6 6 12 12M18 6 6 18"
  };
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d={paths[name] || paths.document} />

    {adminRender(name === "users" && <circle cx="9" cy="7" r="3" />)}

    {adminRender(name === "search" && <circle cx="10.5" cy="10.5" r="6.5" />)}

    {adminRender(["help", "clock"].includes(name) && <circle cx="12" cy="12" r="9" />)}

    {adminRender(name === "settings" && <circle cx="12" cy="12" r="3" />)}
  </svg>;
}
export default function QuanLyBaiKiemTraAdmin({
  onLogout,
  onSaveSchedule,
  onViewExam,
  onEditExam,
  exams: sourceExams = DEMO_EXAMS
}) {
  useAdminLanguage();

  const navigate = useNavigate();
  const location = useLocation();
  const [storedDrafts, setStoredDrafts] = useState(readExamDrafts);
  const [localSchedules, setLocalSchedules] = useState(readSchedules);
  const [savedExamContent, setSavedExamContent] = useState(readExamContent);
  const [sessionSchedules, setSessionSchedules] = useState({});
  const [activeTab, setActiveTab] = useState(location.state?.activeTab === "draft" ? "draft" : "published");
  const [queries, setQueries] = useState({
    published: "",
    draft: ""
  });
  const [pages, setPages] = useState({
    published: 1,
    draft: 1
  });
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const [editingExam, setEditingExam] = useState(null);
  const [form, setForm] = useState({
    date: "",
    startTime: "",
    duration: 60
  });
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const dialogRef = useRef(null);
  const dateInputRef = useRef(null);
  const triggerRef = useRef(null);
  const savingRef = useRef(false);
  const publishedTabRef = useRef(null);
  const draftTabRef = useRef(null);
  const isDemo = sourceExams === DEMO_EXAMS;
  const query = queries[activeTab];
  const mergedExams = new Map((Array.isArray(sourceExams) ? sourceExams : []).map(exam => [exam.id, exam]));
  Object.values(storedDrafts).forEach(record => {
    mergedExams.set(record.id, {
      ...mergedExams.get(record.id),
      ...draftExamMetadata(record)
    });
  });
  const examList = [...mergedExams.values()].sort((a, b) => (Date.parse(storedDrafts[b.id]?.updatedAt || "") || 0) - (Date.parse(storedDrafts[a.id]?.updatedAt || "") || 0));
  const displayedExams = examList.map(sourceExam => {
    const content = savedExamContent[sourceExam.id];
    const exam = sourceExam.status === "published" && Array.isArray(content?.questions) ? {
      ...sourceExam,
      mcqCount: content.questions.filter(question => question.type === "mcq").length,
      sqlCount: content.questions.filter(question => question.type === "sql").length,
      essayCount: content.questions.filter(question => question.type === "essay").length
    } : sourceExam;
    const schedule = isDemo ? localSchedules[exam.id] : sessionSchedules[exam.id] || localSchedules[exam.id];
    return schedule ? {
      ...exam,
      date: schedule.date,
      startTime: schedule.startTime,
      duration: Number(schedule.duration)
    } : exam;
  });
  const publishedCount = displayedExams.filter(exam => exam.status === "published").length;
  const draftCount = displayedExams.filter(exam => exam.status === "draft").length;
  const currentTabCount = activeTab === "published" ? publishedCount : draftCount;
  const visible = displayedExams.filter((exam) => {
    return (
      exam.status === activeTab &&
      normalizeText(exam.title ?? "").includes(normalizeText(query))
    );
  });
  const totalPages = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const currentPage = Math.max(1, Math.min(pages[activeTab], totalPages));
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const paginatedExams = visible.slice(startIndex, startIndex + PAGE_SIZE);
  const firstRecord = visible.length === 0 ? 0 : startIndex + 1;
  const lastRecord = Math.min(startIndex + PAGE_SIZE, visible.length);
  const pageNumbers = getPageNumbers(currentPage, totalPages);
  const endTime = getEndTime(form.startTime, form.duration);
  useEffect(() => {
    function refreshData() {
      setSavedExamContent(readExamContent());
      setStoredDrafts(readExamDrafts());
      setLocalSchedules(readSchedules());
    }
    function syncStorage(event) {
      if (event.key === EXAM_DRAFT_KEY || event.key === CONTENT_STORAGE_KEY || event.key === STORAGE_KEY || event.key === null) {
        refreshData();
      }
    }
    window.addEventListener("focus", refreshData);
    window.addEventListener("storage", syncStorage);
    return () => {
      window.removeEventListener("focus", refreshData);
      window.removeEventListener("storage", syncStorage);
    };
  }, []);
  useEffect(() => {
    const tab = location.state?.activeTab;
    if (tab === "draft" || tab === "published") {
      setActiveTab(tab);
    }
    setStoredDrafts(readExamDrafts());
    setSavedExamContent(readExamContent());
  }, [location.key, location.state?.activeTab]);
  useEffect(() => {
    if (!editingExam) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dateInputRef.current?.focus();
    function handleKeyDown(event) {
      if (event.key === "Escape" && !savingRef.current) {
        setEditingExam(null);
        return;
      }
      if (event.key !== "Tab") return;
      const elements = Array.from(dialogRef.current?.querySelectorAll("button:not(:disabled), input:not(:disabled)") || []);
      const first = elements[0];
      const last = elements[elements.length - 1];
      if (!first) {
        event.preventDefault();
        dialogRef.current?.focus();
        return;
      }
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      triggerRef.current?.focus();
    };
  }, [editingExam]);
  function changeTab(tab, focusTab = false) {
    setActiveTab(tab);
    if (!focusTab) return;
    if (tab === "published") {
      publishedTabRef.current?.focus();
    } else {
      draftTabRef.current?.focus();
    }
  }
  function handleTabKeyDown(event, tab) {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      changeTab(tab === "published" ? "draft" : "published", true);
    } else if (event.key === "Home") {
      event.preventDefault();
      changeTab("published", true);
    } else if (event.key === "End") {
      event.preventDefault();
      changeTab("draft", true);
    }
  }
  function updateQuery(value) {
    setQueries(current => ({
      ...current,
      [activeTab]: value
    }));
    setPages(current => ({
      ...current,
      [activeTab]: 1
    }));
  }
  function goToPage(nextPage) {
    setPages(current => ({
      ...current,
      [activeTab]: Math.max(1, Math.min(nextPage, totalPages))
    }));
  }
  function openEditor(exam, event) {
    triggerRef.current = event.currentTarget;
    setForm({
      date: exam.date || "",
      startTime: exam.startTime || "",
      duration: exam.duration ?? 60
    });
    setFormError("");
    setEditingExam(exam);
  }
  function closeEditor() {
    if (!savingRef.current) {
      setEditingExam(null);
    }
  }
  function updateForm(field, value) {
    setForm(current => ({
      ...current,
      [field]: value
    }));
    setFormError("");
  }
  async function saveSchedule(event) {
    event.preventDefault();
    if (savingRef.current || !editingExam) return;
    const error = validateSchedule(form);
    if (error) {
      setFormError(error);
      return;
    }
    const examId = editingExam.id;
    const schedule = {
      date: form.date,
      startTime: form.startTime,
      duration: Number(form.duration)
    };
    savingRef.current = true;
    setSaving(true);
    setFormError("");
    try {
      if (onSaveSchedule) {
        await onSaveSchedule(examId, schedule);
      }
      const nextSchedules = {
        ...readSchedules(),
        [examId]: schedule
      };
      let storedLocally = true;
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
          schedules: nextSchedules
        }));
      } catch {
        storedLocally = false;
      }
      if (storedLocally) {
        setLocalSchedules(nextSchedules);
      } else {
        setSessionSchedules(current => ({
          ...current,
          [examId]: schedule
        }));

        // Bảo đảm giao diện hiện lịch vừa cập nhật.
        setLocalSchedules(current => ({
          ...current,
          [examId]: schedule
        }));
      }
      setEditingExam(null);
      setNotice(onSaveSchedule ? "Đã lưu thời gian thi." : storedLocally ? "Đã lưu thời gian thi trong trình duyệt." : "Đã cập nhật lịch trong phiên hiện tại. Không lưu được khi tải lại trang.");
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Không thể lưu thời gian thi.");
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  }
  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      if (onLogout) {
        await onLogout();
      }
      navigate("/Dang_nhap");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Không thể đăng xuất.");
    } finally {
      setLoggingOut(false);
    }
  }
  async function openExam(exam) {
    try {
      if (exam.status === "draft") {
        if (onEditExam) {
          await onEditExam(exam);
          return;
        }
        const saved = readExamDrafts()[exam.id];
        const draftStep = saved?.draftStep || exam.draftStep || "mcq";
        const path = DRAFT_ROUTES[draftStep] || DRAFT_ROUTES.mcq;
        navigate(`${path}?examId=${encodeURIComponent(exam.id)}`, {
          state: {
            mode: "edit",
            examId: exam.id,
            draftStep,
            exam
          }
        });
        return;
      }
      if (onViewExam) {
        await onViewExam(exam);
        return;
      }
      navigate(`/Xem_lai_bai_kiem_tra_Admin/${encodeURIComponent(exam.id)}`, {
        state: {
          exam
        }
      });
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Không thể mở bài kiểm tra.");
    }
  }
  return <div className="dbcas-admin-home dbcas-exam-page" style={{
    backgroundImage: `
          linear-gradient(
            rgba(7,11,20,.8),
            rgba(7,11,20,.8)
          ),
          url(${background})
        `
  }}>
    <aside className="sidebar">
      <div className="sidebar-content">
        <div className="sidebar-brand">
          <img src={logo} alt="Logo DBCAS" draggable="false" />
        </div>

        <Link className="btn-new" to="/TN_Admin">
          <Icon name="plus" />
          <span>{adminText("Tạo bài kiểm tra")}</span>
        </Link>

        <nav className="sidebar-nav" aria-label={adminText("Menu quản trị")}>
          {adminRender(NAV_ITEMS.map(([icon, label, path]) => {
            const active = path === "/Quan_ly_bai_kiem_tra_Admin";
            return <Link key={path} className={`nav-link${active ? " active" : ""}`} to={path} aria-current={active ? "page" : undefined}>
              <Icon name={icon} />
              <span>{adminRender(label)}</span>

              {adminRender(active && <span className="nav-dot" />)}
            </Link>;
          }))}
        </nav>
      </div>

      <div className="sidebar-bottom">
        <button className="btn-logout" type="button" disabled={loggingOut} onClick={handleLogout}>
          <Icon name="logout" />
          <span>
            {adminRender(loggingOut ? "Đang đăng xuất..." : "Đăng xuất")}
          </span>
        </button>
      </div>
    </aside>

    <header className="topbar admin-unified-topbar">
      <div className="breadcrumb">
        <span>DBCAS Admin</span>
        <Icon name="chevron" />
        <strong>{adminText("Quản lý bài kiểm tra")}</strong>
      </div>

      <div className="topbar-actions">


        <button className="icon-button" type="button" aria-label={adminText("Trợ giúp")} onClick={() => setNotice(adminText("Bài đã công bố và bản nháp nằm ở hai tab. " + "Bấm Soạn tiếp để mở phần đang soạn."))}>
          <Icon name="help" />
        </button>

        <NotificationMenu role="admin" className="icon-button notification" />

        <AdminAccountMenu onLogout={handleLogout} />
      </div>
    </header>

    <main className="main">
      <section className="page-banner card admin-unified-banner" aria-labelledby="exam-title">
        <div>
          <span className="banner-label">{adminText(" QUẢN TRỊ ĐÁNH GIÁ ")}</span>

          <h1 id="exam-title">{adminText(" Quản lý bài kiểm tra ")}</h1>

          <p>{adminText(" Quản lý bài kiểm tra đã công bố, điều chỉnh lịch thi và tiếp tục soạn các đề trong mục bản nháp. ")}</p>
        </div>

        <Link className="btn-banner" to="/TN_Admin">
          <Icon name="plus" />{adminText(" Tạo bài kiểm tra ")}</Link>
      </section>

      <section className="card results" aria-label={adminText("Quản lý danh sách bài kiểm tra")}>
        <div className="exam-tabs" role="tablist" aria-label={adminText("Loại danh sách bài kiểm tra")}>
          <button ref={publishedTabRef} id="published-tab" className={`exam-tab ${activeTab === "published" ? "is-active" : ""}`} type="button" role="tab" aria-selected={activeTab === "published"} aria-controls="exam-panel" tabIndex={activeTab === "published" ? 0 : -1} onClick={() => changeTab("published")} onKeyDown={event => handleTabKeyDown(event, "published")}>
            <Icon name="document" />{adminText(" Đã công bố ")}<span className="tab-count">
              {adminRender(publishedCount)}
            </span>
          </button>

          <button ref={draftTabRef} id="draft-tab" className={`exam-tab ${activeTab === "draft" ? "is-active" : ""}`} type="button" role="tab" aria-selected={activeTab === "draft"} aria-controls="exam-panel" tabIndex={activeTab === "draft" ? 0 : -1} onClick={() => changeTab("draft")} onKeyDown={event => handleTabKeyDown(event, "draft")}>
            <Icon name="document" />{adminText(" Bản nháp ")}<span className="tab-count">
              {adminRender(draftCount)}
            </span>
          </button>
        </div>

        <div id="exam-panel" role="tabpanel" aria-labelledby={activeTab === "published" ? "published-tab" : "draft-tab"} tabIndex={0}>
          <div className="exam-list-head">
            <div>
              <h2>
                {adminRender(activeTab === "published" ? "Bài kiểm tra đã công bố" : "Bản nháp bài kiểm tra")}
              </h2>

              <p>
                {adminRender(activeTab === "published" ? "Các đề đã công bố cho sinh viên." : "Các đề đang soạn, chưa công bố cho sinh viên.")}
              </p>
            </div>

            <span className="exam-count">
              <strong>
                {adminRender(currentTabCount)}
              </strong>{adminRender(" ")}{adminText(" bài kiểm tra ")}</span>
          </div>

          <div className="exam-toolbar">
            <label className="search result-search">
              <Icon name="search" />

              <input
                type="search"
                placeholder={adminText("Tìm tên bài kiểm tra...")}
                aria-label={adminText("Tìm tên bài kiểm tra")}
                value={query}
                onChange={(event) => updateQuery(event.target.value)}
              />
            </label>

            <span className="filter-count">
              {adminRender(visible.length)}{adminText(" kết quả ")}</span>
          </div>

          <div className="table-wrap exam-table">
            <table>
              <colgroup>
                <col className="col-title" />
                <col className="col-structure" />
                <col className="col-schedule" />
                <col className="col-actions" />
              </colgroup>

              <thead>
                <tr>
                  <th scope="col">
                    {adminRender(activeTab === "published" ? "Bài kiểm tra" : "Đề đang soạn")}
                  </th>

                  <th scope="col">{adminText(" Cấu trúc đề ")}</th>

                  <th scope="col">
                    {adminRender(activeTab === "published" ? "Thời gian & lịch thi" : "Lịch thi dự kiến")}
                  </th>

                  <th scope="col">{adminText(" Thao tác ")}</th>
                </tr>
              </thead>

              <tbody>
                {adminRender(visible.length === 0 && <tr>
                  <td colSpan={4} className="empty-state">
                    {adminRender(query.trim() ? "Không tìm thấy bài kiểm tra phù hợp." : activeTab === "published" ? "Chưa có bài kiểm tra đã công bố." : "Chưa có bản nháp bài kiểm tra.")}
                  </td>
                </tr>)}

                {adminRender(paginatedExams.map(exam => {
                  const end = getEndTime(exam.startTime, exam.duration);
                  const isDraft = exam.status === "draft";
                  return <tr key={exam.id}>
                    <td>
                      <strong className="exam-name">
                        {adminRender(exam.title)}
                      </strong>

                      <div className="exam-meta">
                        <span>{adminRender(exam.id)}</span>

                        <span>
                          {adminRender(exam.studentCount || 0)}{adminRender(" ")}{adminText(" sinh viên ")}</span>

                        <span className={`exam-badge ${isDraft ? "badge-draft" : "badge-published"}`}>
                          {adminRender(isDraft ? "Chưa công bố" : "Đã công bố")}
                        </span>
                      </div>
                    </td>

                    <td>
                      <div className="exam-structure">
                        <span>
                          {adminRender(exam.mcqCount ?? 0)}{adminRender(" ")}{adminText(" câu trắc nghiệm ")}</span>

                        <span className="part-sql">
                          {adminRender(exam.sqlCount ?? 0)}{adminRender(" ")}{adminText(" câu SQL ")}</span>

                        <span className="part-essay">
                          {adminRender(exam.essayCount ?? 0)}{adminRender(" ")}{adminText(" câu tự luận ")}</span>
                      </div>
                    </td>

                    <td>
                      <div className="exam-schedule">
                        <strong>
                          {adminRender(formatDate(exam.date))}
                        </strong>

                        <span>
                          {adminRender(exam.startTime && end ? `${exam.startTime} – ${end.time}${end.nextDay ? " (ngày hôm sau)" : ""}` : "Chưa xếp giờ")}
                        </span>

                        <small>
                          <Icon name="clock" />
                          {adminRender(exam.duration)}{adminText(" phút ")}</small>
                      </div>
                    </td>

                    <td>
                      <div className="exam-actions">
                        <button className="btn-detail" type="button" onClick={() => openExam(exam)}>
                          {adminRender(isDraft ? "Soạn tiếp" : "Xem lại")}
                        </button>

                        <button className="btn-detail btn-time" type="button" onClick={event => openEditor(exam, event)}>
                          <Icon name="clock" />{adminText(" Chỉnh thời gian ")}</button>
                      </div>
                    </td>
                  </tr>;
                }))}
              </tbody>
            </table>
          </div>

          <div className="exam-list-footer">
            <div className="exam-record-count">{adminText(" Hiển thị")}{adminRender(" ")}
              <strong>
                {adminRender(firstRecord)}–{adminRender(lastRecord)}
              </strong>{adminRender(" ")}
              trong{adminRender(" ")}
              <strong>
                {adminRender(visible.length)}
              </strong>{adminRender(" ")}
              {adminRender(activeTab === "published" ? "bài đã công bố" : "bản nháp")}

              {adminRender(query.trim() && <span className="exam-filter-total">
                {adminRender(" ")}{adminText(" · Tổng trong tab:")}{adminRender(" ")}
                {adminRender(currentTabCount)}
              </span>)}
            </div>

            <nav className="exam-pagination" aria-label={adminText("Phân trang bài kiểm tra")}>
              <button className="exam-page-button page-direction" type="button" disabled={currentPage === 1} onClick={() => goToPage(currentPage - 1)} aria-label={adminText("Trang trước")}>{adminText(" ‹ Trước ")}</button>

              {adminRender(pageNumbers.map(number => typeof number === "string" ? <span key={number} className="exam-page-gap" aria-hidden="true">
                …
              </span> : <button key={number} className={`exam-page-button ${number === currentPage ? "is-active" : ""}`} type="button" aria-label={`Trang ${number}`} aria-current={number === currentPage ? "page" : undefined} onClick={() => goToPage(number)}>
                {adminRender(number)}
              </button>))}

              <button className="exam-page-button page-direction" type="button" disabled={currentPage === totalPages} onClick={() => goToPage(currentPage + 1)} aria-label="Trang sau">
                Sau ›
              </button>
            </nav>
          </div>
        </div>
      </section>
    </main>

    <footer className="footer">
      <span>{adminText(" DBCAS • Nền tảng đánh giá năng lực CSDL ")}</span>

      <span>
        © 2026 Duy Tan University
      </span>
    </footer>

    {adminRender(editingExam && <div className="exam-modal-overlay" onClick={event => {
      if (event.target === event.currentTarget) {
        closeEditor();
      }
    }}>
      <section className="exam-modal" role="dialog" aria-modal="true" aria-labelledby="schedule-dialog-title" aria-describedby="schedule-dialog-description" aria-busy={saving} ref={dialogRef} tabIndex={-1}>
        <div className="exam-modal-head">
          <div>
            <span className="modal-label">{adminText(" LỊCH KIỂM TRA ")}</span>

            <h2 id="schedule-dialog-title">{adminText(" Chỉnh thời gian thi ")}</h2>
          </div>

          <button className="modal-close" type="button" aria-label={adminText("Đóng hộp chỉnh thời gian")} disabled={saving} onClick={closeEditor}>
            <Icon name="close" />
          </button>
        </div>

        <p className="modal-exam-title" id="schedule-dialog-description">
          {adminRender(editingExam.title)}
        </p>

        <form onSubmit={saveSchedule} noValidate>
          <fieldset className="schedule-fields" disabled={saving}>
            <label className="schedule-field field-full">
              <span>{adminText("Ngày thi")}</span>

              <input ref={dateInputRef} type="date" required value={form.date} onChange={event => updateForm("date", event.target.value)} />
            </label>

            <label className="schedule-field">
              <span>{adminText("Giờ bắt đầu")}</span>

              <input type="time" required value={form.startTime} onChange={event => updateForm("startTime", event.target.value)} />
            </label>

            <label className="schedule-field">
              <span>{adminText(" Thời lượng (phút) ")}</span>

              <input type="number" min="1" max="600" step="1" required value={form.duration} onChange={event => updateForm("duration", event.target.value)} />
            </label>
          </fieldset>

          <div className="schedule-preview" aria-live="polite">
            <Icon name="clock" />

            <div>
              <span>{adminText(" Giờ kết thúc dự kiến ")}</span>

              <strong>
                {adminRender(endTime ? `${endTime.time}${endTime.nextDay ? " · Ngày hôm sau" : ""}` : "Chưa đủ thông tin")}
              </strong>
            </div>
          </div>

          <p className="schedule-note">
            {adminRender(editingExam.status === "draft" ? "Đây là lịch dự kiến. Lưu thời gian không công bố đề cho sinh viên." : "Bấm Lưu thời gian để cập nhật lịch thi.")}
          </p>

          {adminRender(formError && <p className="schedule-error" role="alert">
            {adminRender(formError)}
          </p>)}

          <div className="exam-modal-actions">
            <button className="btn-detail" type="button" disabled={saving} onClick={closeEditor}>{adminText(" Hủy ")}</button>

            <button className="btn-apply" type="submit" disabled={saving}>
              {adminRender(saving ? "Đang lưu..." : "Lưu thời gian")}
            </button>
          </div>
        </form>
      </section>
    </div>)}

    {adminRender(notice && <div className="admin-notice" role="status">
      <span>{adminRender(notice)}</span>

      <button type="button" aria-label={adminText("Đóng thông báo")} onClick={() => setNotice(adminText(""))}>{adminText(" × ")}</button>
    </div>)}
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
      } catch { }
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