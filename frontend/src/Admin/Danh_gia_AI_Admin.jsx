import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./Danh_gia_AI_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";
const PAGE_SIZE = 10;
const DEMO_MAJORS = ["Kỹ thuật Phần mềm", "Khoa học Máy tính", "Hệ thống Thông tin Quản lý", "An ninh Mạng", "Công nghệ Phần mềm"];
const DEMO_STUDENTS = Array.from({
  length: 100
}, (_, index) => {
  const surnames = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Võ", "Đặng", "Bùi"];
  const middles = ["Hoàng", "Minh", "Ngọc", "Thanh", "Gia", "Quang", "Thị", "Anh", "Đức", "Hải"];
  const names = ["Long", "Thư", "Dũng", "Anh", "Linh", "Huy", "Trang", "Nam", "Vy", "Khoa", "Hân", "Bảo", "Phúc", "Châu", "Tuấn"];
  const examTitles = ["KT CSDL Cơ Bản", "KT CSDL Nâng Cao", "SQL & Indexing Lab", "Thiết kế và Chuẩn hóa CSDL", "Transaction & ACID"];
  const skillLabels = ["Truy vấn SQL", "DML & DDL", "Thiết kế & Ràng buộc"];
  const id = String(21200000001 + index);
  const mcqCorrect = 4 + index * 3 % 7;
  const sqlPassed = index * 5 % 4;
  const essayRaw = (40 + index * 13 % 61) / 10;
  const mcq = Number((mcqCorrect * 0.4).toFixed(2));
  const sql = sqlPassed;
  const essay = Number((essayRaw * 0.3).toFixed(2));
  const skills = [mcqCorrect, Number((sqlPassed / 3 * 10).toFixed(2)), essayRaw];
  const clos = skills.map(value => value >= 6);
  return {
    id,
    studentId: id,
    name: [surnames[index % 10], middles[Math.floor(index / 10) % 10], names[Math.floor(index / 100) % 15]].join(" "),
    email: `sv${id}@example.com`,
    major: DEMO_MAJORS[index % DEMO_MAJORS.length],
    year: "2026-2027",
    attempts: 1,
    examId: `DEMO-EXAM-${String(index % 27 + 1).padStart(3, "0")}`,
    examTitle: examTitles[index % 27 % examTitles.length],
    submittedAt: `${String(8 + index % 9).padStart(2, "0")}:` + `${String(index * 7 % 60).padStart(2, "0")}` + ` • ${String(1 + index % 12).padStart(2, "0")}/10/2026`,
    mcqCorrect,
    sqlPassed,
    essayRaw,
    mcq,
    sql,
    essay,
    score: Number((mcq + sql + essay).toFixed(2)),
    skills,
    clos,
    cloCount: clos.filter(Boolean).length,
    strong: skillLabels[skills.indexOf(Math.max(...skills))],
    weak: skillLabels[skills.indexOf(Math.min(...skills))]
  };
});
const RUBRIC_LABELS = ["B-Tree & Index", "I/O & Sharding", "ACID & Khóa phân tán"];

// 100 bài tự luận: 20 chưa duyệt, 80 đã duyệt.
const DEMO_SUBMISSIONS = DEMO_STUDENTS.map((student, index) => {
  const pending = (index + 1) % 5 === 0;
  const first = Math.floor(student.essay * 100 / 3) / 100;
  const aiRubric = [first, first, Number((student.essay - first * 2).toFixed(2))];
  return {
    id: `AI-${student.id}`,
    name: student.name,
    studentId: student.id,
    topic: student.examTitle,
    year: "2026-2027",
    aiRubric,
    teacherRubric: pending ? null : [...aiRubric],
    teacherComment: "",
    trust: pending ? 82 + index % 6 : 95 + index % 5,
    gradingSeconds: 1 + index % 9 * 0.1,
    status: pending ? "pending" : "approved",
    approvalMethod: pending ? null : "ai",
    essay: ["Em đề xuất kết hợp tối ưu truy vấn tại từng node với phân phối dữ liệu giữa các node.", "Với truy vấn lọc theo tenant và thời gian, cần xem xét chỉ mục ghép trên TenantID và CreatedAt. Thứ tự cột trong chỉ mục phải phù hợp điều kiện lọc và được kiểm tra bằng execution plan.", "Dữ liệu có thể phân mảnh ngang theo TenantID. Khi một tenant có lượng dữ liệu lớn, cần theo dõi tải và điều chỉnh cách phân phối để hạn chế hotspot.", pending ? "Các giao dịch giữa nhiều dịch vụ được phối hợp bằng Saga. Bài làm chưa giải thích rõ thao tác bù khi một bước thất bại." : "Các giao dịch giữa nhiều dịch vụ có thể phối hợp bằng Saga. Mỗi bước cần có thao tác bù, xử lý retry và bảo đảm idempotency."],
    strengths: "Trình bày được hướng lựa chọn chỉ mục và phân phối dữ liệu theo tenant.",
    improvements: pending ? "Cần kiểm tra phần giao dịch bù và xử lý khi một bước thất bại." : "Cần làm rõ điều kiện áp dụng và kiểm chứng bằng execution plan."
  };
});
const NAV_ITEMS = [["home", "Trang chủ", "/Home_Admin"], ["users", "Đánh giá năng lực", "/Danh_gia_nang_luc_Admin"], ["cap", "CLO & Kỹ năng", "/CLO_Ky_nang_Admin"], ["document", "Quản lý bài kiểm tra", "/Quan_ly_bai_kiem_tra_Admin"], ["robot", "Đánh giá bằng AI", "/Danh_gia_AI_Admin"]];
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
    calendar: "M3 5h18v16H3zM7 3v4M17 3v4M3 11h18",
    download: "M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
    lightning: "m13 2-8 12h6l-1 8 9-13h-6z",
    warning: "m12 3 10 18H2zM12 9v5M12 17h.01",
    close: "m6 6 12 12M18 6 6 18"
  };
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name] || paths.document} />

      {adminRender(name === "users" && <circle cx="9" cy="7" r="3" />)}

      {adminRender(name === "search" && <circle cx="10.5" cy="10.5" r="6.5" />)}

      {adminRender(name === "help" && <circle cx="12" cy="12" r="9" />)}

      {adminRender(name === "settings" && <circle cx="12" cy="12" r="3" />)}
    </svg>;
}
function normalizeText(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase().trim();
}
function sumScores(scores) {
  return Number((scores || []).reduce((total, value) => total + Number(value || 0), 0).toFixed(2));
}
function aiScore(item) {
  return sumScores(item.aiRubric);
}
function teacherScore(item) {
  return Array.isArray(item.teacherRubric) ? sumScores(item.teacherRubric) : null;
}
function finalScore(item) {
  if (item.status !== "approved") return null;
  return item.approvalMethod === "manual" ? teacherScore(item) : aiScore(item);
}
function scoreDifference(item) {
  const teacher = teacherScore(item);
  return teacher === null ? null : Number(Math.abs(aiScore(item) - teacher).toFixed(2));
}
function statusLabel(item) {
  if (item.status === "pending") return "Chưa duyệt";
  return item.approvalMethod === "manual" ? "Đã duyệt thủ công" : "Đã duyệt AI";
}
function formatScore(value) {
  return value === null ? "—" : Number(value).toFixed(2);
}
function average(items, field) {
  const values = items.map(item => item[field]).filter(value => typeof value === "number" && Number.isFinite(value));
  return values.length ? (values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1) : null;
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
export default function DanhGiaAiAdmin({
  onLogout,
  onApproveAI,
  onConfirmTeacherScore,
  submissions: sourceSubmissions = DEMO_SUBMISSIONS
}) {
  useAdminLanguage();

  const navigate = useNavigate();
  const reviewRef = useRef(null);
  const modalRef = useRef(null);
  const firstInputRef = useRef(null);
  const editTriggerRef = useRef(null);
  const savingRef = useRef(false);
  const isDemo = sourceSubmissions === DEMO_SUBMISSIONS;
  const sourceItems = Array.isArray(sourceSubmissions) ? sourceSubmissions : [];
  const [overrides, setOverrides] = useState({});
  const [query, setQuery] = useState("");
  const [year, setYear] = useState("2026-2027");
  const [aiStatus, setAiStatus] = useState("all");
  const [selectedPendingId, setSelectedPendingId] = useState(null);
  const [viewingApprovedId, setViewingApprovedId] = useState(null);
  const [page, setPage] = useState(1);
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const [approving, setApproving] = useState(false);
  const [scoreEditor, setScoreEditor] = useState(null);
  const [scoreForm, setScoreForm] = useState(["", "", ""]);
  const [teacherComment, setTeacherComment] = useState("");
  const [scoreError, setScoreError] = useState("");
  const [savingScore, setSavingScore] = useState(false);
  const items = sourceItems.map(item => ({
    ...item,
    ...overrides[item.id],
    aiRubric: item.aiRubric
  }));
  const yearItems = items.filter(item => item.year === year);
  const pendingItems = yearItems.filter(item => item.status === "pending");
  const viewedApproved = viewingApprovedId ? yearItems.find(item => item.id === viewingApprovedId && item.status === "approved") : null;
  const selectedPending = pendingItems.find(item => item.id === selectedPendingId) || pendingItems[0] || null;
  const selected = viewedApproved || selectedPending;
  const isViewingApproved = Boolean(viewedApproved);
  const pendingIndex = selectedPending ? pendingItems.findIndex(item => item.id === selectedPending.id) : -1;
  const visible = yearItems.filter(item => {
    const matchesSearch = normalizeText(`${item.name ?? ""} ${item.studentId ?? ""}`).includes(normalizeText(query));
    const matchesStatus = aiStatus === "all" || aiStatus === "pending" && item.status === "pending" || aiStatus === "approved" && item.status === "approved" || aiStatus === "manual" && item.status === "approved" && item.approvalMethod === "manual";
    return matchesSearch && matchesStatus;
  });
  const totalPages = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const pageItems = visible.slice(startIndex, startIndex + PAGE_SIZE);
  const firstRecord = visible.length ? startIndex + 1 : 0;
  const lastRecord = Math.min(startIndex + PAGE_SIZE, visible.length);
  const gradingAverage = average(yearItems, "gradingSeconds");
  const comparedItems = yearItems.filter(item => teacherScore(item) !== null);
  const similarityAverage = comparedItems.length ? (comparedItems.reduce((total, item) => {
    const similarity = Math.max(0, 100 - scoreDifference(item) / 3 * 100);
    return total + similarity;
  }, 0) / comparedItems.length).toFixed(1) : null;
  const warningCount = comparedItems.filter(item => scoreDifference(item) > 0.75).length;
  const formNumbers = scoreForm.map(value => value.trim() === "" ? NaN : Number(value));
  const validFormScores = formNumbers.every(value => Number.isFinite(value) && value >= 0 && value <= 1);
  const editedTotal = validFormScores ? sumScores(formNumbers) : null;
  useEffect(() => {
    if (!scoreEditor) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    firstInputRef.current?.focus();
    function handleKeyDown(event) {
      if (event.key === "Escape" && !savingRef.current) {
        setScoreEditor(null);
      }
      if (event.key !== "Tab") return;
      const elements = Array.from(modalRef.current?.querySelectorAll("button:not(:disabled), input:not(:disabled), textarea:not(:disabled)") || []);
      const first = elements[0];
      const last = elements[elements.length - 1];
      if (!first) {
        event.preventDefault();
        modalRef.current?.focus();
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
      editTriggerRef.current?.focus();
    };
  }, [scoreEditor]);
  function updateQuery(value) {
    setQuery(value);
    setPage(1);
  }
  function updateYear(value) {
    setYear(value);
    setSelectedPendingId(null);
    setViewingApprovedId(null);
    setPage(1);
  }
  function selectSubmission(item) {
    if (item.status === "approved") {
      setViewingApprovedId(item.id);
    } else {
      setViewingApprovedId(null);
      setSelectedPendingId(item.id);
    }
    reviewRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  }
  function movePending(direction) {
    const next = pendingItems[pendingIndex + direction];
    if (next) {
      setViewingApprovedId(null);
      setSelectedPendingId(next.id);
    }
  }
  function moveToNextPending(id) {
    const index = pendingItems.findIndex(item => item.id === id);
    const next = pendingItems[index + 1] || pendingItems.find(item => item.id !== id);
    setViewingApprovedId(null);
    setSelectedPendingId(next?.id || null);
  }
  async function approveAI() {
    if (!selected || isViewingApproved || approving) return;
    if (!isDemo && !onApproveAI) {
      setNotice(adminText("Chưa kết nối chức năng duyệt điểm."));
      return;
    }
    const id = selected.id;
    setApproving(true);
    try {
      if (onApproveAI) {
        await onApproveAI(id);
      }
      setOverrides(current => ({
        ...current,
        [id]: {
          ...current[id],
          status: "approved",
          approvalMethod: "ai"
        }
      }));
      moveToNextPending(id);
      setNotice(adminText("Đã xác nhận điểm AI làm điểm cuối cùng."));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Không thể duyệt điểm.");
    } finally {
      setApproving(false);
    }
  }
  function openScoreEditor(event) {
    if (!selected || isViewingApproved || approving) return;
    editTriggerRef.current = event.currentTarget;
    setScoreEditor(selected);
    setScoreForm(RUBRIC_LABELS.map((_, index) => String(selected.teacherRubric?.[index] ?? selected.aiRubric?.[index] ?? 0)));
    setTeacherComment(selected.teacherComment || "");
    setScoreError("");
  }
  function closeScoreEditor() {
    if (!savingRef.current) {
      setScoreEditor(null);
    }
  }
  function updateScore(index, value) {
    setScoreForm(current => current.map((score, position) => position === index ? value : score));
    setScoreError("");
  }
  async function confirmTeacherScore(event) {
    event.preventDefault();
    if (!scoreEditor || savingRef.current) return;
    if (!validFormScores) {
      setScoreError("Nhập đầy đủ điểm từ 0 đến 1 cho mỗi tiêu chí.");
      return;
    }
    if (!teacherComment.trim()) {
      setScoreError("Vui lòng nhập nhận xét.");
      return;
    }
    if (!isDemo && !onConfirmTeacherScore) {
      setScoreError("Chưa kết nối chức năng lưu điểm GV.");
      return;
    }
    const id = scoreEditor.id;
    const payload = {
      teacherRubric: formNumbers.map(value => Number(value.toFixed(2))),
      teacherComment: teacherComment.trim(),
      status: "approved",
      approvalMethod: "manual"
    };
    savingRef.current = true;
    setSavingScore(true);
    setScoreError("");
    try {
      if (onConfirmTeacherScore) {
        await onConfirmTeacherScore(id, payload);
      }
      setOverrides(current => ({
        ...current,
        [id]: {
          ...current[id],
          ...payload
        }
      }));
      setScoreEditor(null);
      moveToNextPending(id);
      setNotice(adminText(`Đã duyệt thủ công. Điểm cuối cùng: ${sumScores(payload.teacherRubric).toFixed(2)}/3.0.`));
    } catch (error) {
      setScoreError(error instanceof Error ? error.message : "Không thể xác nhận điểm GV.");
    } finally {
      savingRef.current = false;
      setSavingScore(false);
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
  return <div className="dbcas-admin-home dbcas-ai-page" style={{
    backgroundImage: `linear-gradient(
          rgba(7,11,20,.8),
          rgba(7,11,20,.8)
        ), url(${background})`
  }}>
      {/* Sidebar */}
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
            const active = path === "/Danh_gia_AI_Admin";
            return <Link key={path} className={`nav-link${active ? " active" : ""}`} to={path} aria-current={active ? "page" : undefined}>
                  <Icon name={icon} />
                  <span>{adminRender(label)}</span>
                  {adminRender(active && <span className="nav-dot" />)}
                </Link>;
          }))}

            <Link className="nav-link" to="/Bao_cao_Admin">
              <Icon name="chart" />
              <span>{adminText("Báo cáo")}</span>
            </Link>

            <Link className="nav-link" to="/Cai_dat_Admin">
              <Icon name="settings" />
              <span>{adminText("Cài đặt")}</span>
            </Link>
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

      {/* Thanh phía trên */}
      <header className="topbar admin-unified-topbar">
        <div className="breadcrumb">
          <span>DBCAS Admin</span>
          <Icon name="chevron" />
          <strong>{adminText("Đánh giá bằng AI")}</strong>
        </div>

        <div className="topbar-actions">
          <label className="search top-search">
            <Icon name="search" />

            <input type="search" placeholder={adminText("Tìm tên sinh viên hoặc MSSV...")} aria-label={adminText("Tìm tên sinh viên hoặc MSSV")} value={query} onChange={event => updateQuery(event.target.value)} />
          </label>

          <button className="icon-button" type="button" aria-label={adminText("Trợ giúp")} onClick={() => setNotice(adminText("Duyệt điểm AI để giữ kết quả AI. Sửa điểm để chấm và xác nhận kết quả thủ công."))}>
            <Icon name="help" />
          </button>

          <NotificationMenu role="admin" className="icon-button notification" />

          <AdminAccountMenu onLogout={handleLogout} />
        </div>
      </header>

      <main className="main">
        {/* Banner */}
        <section className="page-banner card admin-unified-banner">
          <div>
            <span className="ai-eyebrow">{adminText("THẨM ĐỊNH BÀI THI")}</span>
            <h1>{adminText("Đánh giá bằng AI")}</h1>
            <p>{adminText(" Đối chiếu kết quả AI, chấm lại thủ công theo rubric và xác nhận điểm cuối cùng cho sinh viên. ")}</p>
          </div>

          <label className="ai-year-filter">
            <Icon name="calendar" />

            <select aria-label={adminText("Năm học")} value={year} onChange={event => updateYear(event.target.value)}>
              <option value="2026-2027">{adminText("Năm học 2026–2027")}</option>
              <option value="2025-2026">{adminText("Năm học 2025–2026")}</option>
              <option value="2024-2025">{adminText("Năm học 2024–2025")}</option>
            </select>
          </label>
        </section>

        {/* Thống kê */}
        <section className="kpi-row" aria-label={adminText("Chỉ số chấm AI")}>
          <article className="card ai-kpi-card">
            <div className="ai-kpi-head">
              <span>{adminText("Bài thi tự luận đã chấm AI")}</span>
              <span className="ai-kpi-icon kpi-cyan">
                <Icon name="chart" />
              </span>
            </div>
            <div className="ai-kpi-value">
              <strong>{adminRender(yearItems.length)}</strong>
              <span>{adminText("bài làm")}</span>
            </div>
            <p>{adminText("Trong năm học đã chọn")}</p>
          </article>

          <article className="card ai-kpi-card">
            <div className="ai-kpi-head">
              <span>{adminText("Thời gian AI chấm trung bình")}</span>
              <span className="ai-kpi-icon kpi-blue">
                <Icon name="lightning" />
              </span>
            </div>
            <div className="ai-kpi-value">
              <strong>
                {adminRender(gradingAverage === null ? "—" : `${gradingAverage}s`)}
              </strong>
              <span>{adminText("/ bài làm")}</span>
            </div>
            <p>{adminText("Trung bình thời gian chấm")}</p>
          </article>

          <article className="card ai-kpi-card">
            <div className="ai-kpi-head">
              <span>{adminText("Độ tương đồng GV & AI")}</span>
              <span className="ai-kpi-icon kpi-green">
                <Icon name="robot" />
              </span>
            </div>
            <div className="ai-kpi-value">
              <strong>
                {adminRender(similarityAverage === null ? "—" : `${similarityAverage}%`)}
              </strong>
            </div>
            <p>{adminRender(comparedItems.length)}{adminText(" bài có điểm đối chiếu")}</p>
          </article>

          <article className="card ai-kpi-card">
            <div className="ai-kpi-head">
              <span>{adminText("Cảnh báo chênh lệch (>0.75đ)")}</span>
              <span className="ai-kpi-icon kpi-rose">
                <Icon name="warning" />
              </span>
            </div>
            <div className="ai-kpi-value">
              <strong className="text-rose">{adminRender(warningCount)}</strong>
              <span>{adminText("bài thi")}</span>
            </div>
            <p>{adminRender(pendingItems.length)}{adminText(" bài chưa duyệt")}</p>
          </article>
        </section>

        {/* Thẩm định */}
        <section className="card ai-review" aria-labelledby="review-title" ref={reviewRef}>
          <div className="ai-review-top">
            <div>
              <h2 id="review-title">
                {adminRender(isViewingApproved ? "Xem bài thi đã duyệt" : "Thẩm định lại điểm AI")}
              </h2>
              <p>
                {adminRender(isViewingApproved ? "Kết quả bài thi đã được xác nhận." : `${pendingItems.length} bài đang chờ duyệt`)}
              </p>
            </div>

            {adminRender(isViewingApproved ? <button className="ai-button" type="button" onClick={() => setViewingApprovedId(null)}>{adminText(" Quay lại thẩm định ")}</button> : <div className="queue-pager">
                <button className="ai-small-button" type="button" aria-label={adminText("Bài chưa duyệt trước")} disabled={pendingIndex <= 0 || approving} onClick={() => movePending(-1)}>
                  ‹
                </button>

                <span>
                  {adminRender(selectedPending ? pendingIndex + 1 : 0)}
                  /{adminRender(pendingItems.length)}
                </span>

                <button className="ai-small-button" type="button" aria-label={adminText("Bài chưa duyệt tiếp theo")} disabled={!selectedPending || pendingIndex >= pendingItems.length - 1 || approving} onClick={() => movePending(1)}>
                  ›
                </button>
              </div>)}
          </div>

          {adminRender(selected ? <>
              <div className="ai-review-heading">
                <div className="ai-review-student">
                  <h3>{adminRender(selected.name)}</h3>
                  <p className="ai-mssv">{adminRender(selected.studentId)}</p>
                  <p>{adminRender(selected.topic)}</p>

                  <span className={`ai-status-badge ${selected.status === "approved" ? "grade-green" : "grade-rose"}`}>
                    {adminRender(statusLabel(selected))}
                  </span>
                </div>
              </div>

              <div className="ai-score-summary">
                <div>
                  <span>{adminText("Điểm AI")}</span>
                  <strong>{adminRender(formatScore(aiScore(selected)))}</strong>
                  <small>/ 3.0</small>
                </div>

                <div>
                  <span>{adminText("Điểm GV")}</span>
                  <strong>{adminRender(formatScore(teacherScore(selected)))}</strong>
                  <small>/ 3.0</small>
                </div>

                <div className="ai-final-score">
                  <span>{adminText("Điểm cuối cùng")}</span>
                  <strong>{adminRender(formatScore(finalScore(selected)))}</strong>
                  <small>
                    {adminRender(selected.status === "approved" ? "/ 3.0" : "Chờ xác nhận")}
                  </small>
                </div>
              </div>

              <h3 className="essay-label">{adminText("Bài làm tự luận")}</h3>

              <div className="essay">
                {adminRender((selected.essay || []).length ? selected.essay.map((paragraph, index) => <p key={index}>{adminRender(paragraph)}</p>) : <p>{adminText("Chưa có nội dung bài làm.")}</p>)}
              </div>

              <div className="rubric-row">
                {adminRender(RUBRIC_LABELS.map((label, index) => {
              const score = Number(selected.aiRubric?.[index] || 0);
              const gv = selected.teacherRubric?.[index];
              return <article className="rubric-card" key={label}>
                      <h3>{adminRender(index + 1)}. {adminRender(label)}</h3>

                      <div className="rubric-score-line">
                        <span>AI</span>
                        <strong>{adminRender(score.toFixed(2))} / 1.0</strong>
                      </div>

                      <span className="score-bar">
                        <i style={{
                    width: `${Math.max(0, Math.min(100, score * 100))}%`
                  }} />
                      </span>

                      <div className="rubric-score-line">
                        <span>GV</span>
                        <strong className="text-amber">
                          {adminRender(gv == null ? "—" : `${Number(gv).toFixed(2)} / 1.0`)}
                        </strong>
                      </div>
                    </article>;
            }))}
              </div>

              <div className="note">
                <h3>{adminText("Nhận xét AI")}</h3>

                <p>
                  <span className="text-cyan">{adminText("Điểm mạnh:")}</span>{adminRender(" ")}
                  {adminRender(selected.strengths || "Chưa có nhận xét.")}
                </p>

                <p>
                  <span className="text-amber">{adminText("Cần cải thiện:")}</span>{adminRender(" ")}
                  {adminRender(selected.improvements || "Chưa có nhận xét.")}
                </p>
              </div>

              {adminRender(selected.teacherComment && <div className="note teacher-note">
                  <h3>{adminText("Nhận xét duyệt của GV")}</h3>
                  <p>{adminRender(selected.teacherComment)}</p>

                  <p>{adminText(" Điểm GV:")}{adminRender(" ")}
                    <strong>
                      {adminRender(formatScore(teacherScore(selected)))}/3.0
                    </strong>
                    {adminRender(" ")}{adminText("· Chênh lệch AI:")}{adminRender(" ")}
                    <strong>
                      {adminRender(formatScore(scoreDifference(selected)))}{adminText("đ ")}</strong>
                  </p>
                </div>)}

              {adminRender(!isViewingApproved && <div className="review-actions">
                  <div>
                    <button className="ai-button" type="button" disabled={pendingIndex <= 0 || approving} onClick={() => movePending(-1)}>{adminText(" ← Bài trước ")}</button>

                    <button className="ai-button" type="button" disabled={pendingIndex >= pendingItems.length - 1 || approving} onClick={() => movePending(1)}>{adminText(" Bài tiếp theo → ")}</button>
                  </div>

                  <div>
                    <button className="ai-button btn-manual" type="button" disabled={approving} onClick={openScoreEditor}>{adminText(" Sửa điểm ")}</button>

                    <button className="ai-button btn-approve" type="button" disabled={approving} onClick={approveAI}>
                      {adminRender(approving ? "Đang duyệt..." : "Duyệt điểm AI")}
                    </button>
                  </div>
                </div>)}
            </> : <div className="ai-review-empty">
              <Icon name="document" />
              <h3>{adminText("Không có bài thi chờ duyệt")}</h3>
              <p>{adminText("Bấm Xem trong danh sách để xem lại bài đã duyệt.")}</p>
            </div>)}
        </section>

        {/* Danh sách bài thi */}
        <section className="card ai-results" aria-labelledby="ai-table-title">
          <div className="ai-list-heading">
            <div>
              <h2 id="ai-table-title">{adminText("Danh sách bài thi chấm bằng AI")}</h2>
              <p>{adminText("Điểm AI, điểm GV và kết quả cuối cùng theo thang 3.0")}</p>
            </div>

            <span className="ai-record-badge">
              {adminRender(yearItems.length)}{adminText(" bài thi ")}</span>
          </div>

          <div className="ai-list-toolbar">
            <label className="search ai-list-search">
              <Icon name="search" />

              <input type="search" placeholder={adminText("Tìm tên sinh viên hoặc MSSV...")} aria-label={adminText("Tìm tên sinh viên hoặc MSSV")} value={query} onChange={event => updateQuery(event.target.value)} />
            </label>

            <select className="ai-status-filter" aria-label={adminText("Lọc trạng thái")} value={aiStatus} onChange={event => {
            setAiStatus(event.target.value);
            setPage(1);
          }}>
              <option value="all">{adminText("Tất cả trạng thái")}</option>
              <option value="pending">{adminText("Chưa duyệt")}</option>
              <option value="approved">{adminText("Đã duyệt")}</option>
              <option value="manual">{adminText("Duyệt thủ công")}</option>
            </select>

            <button className="ai-export-button" type="button" onClick={() => setNotice(adminText("Chưa kết nối chức năng xuất bảng điểm."))}>
              <Icon name="download" />{adminText(" Xuất bảng điểm ")}</button>
          </div>

          <div className="ai-table-wrap">
            <table className="ai-submission-table">
              <colgroup>
                <col className="col-student" />
                <col className="col-topic" />
                <col className="col-score" />
                <col className="col-score" />
                <col className="col-final" />
                <col className="col-difference" />
                <col className="col-status" />
                <col className="col-action" />
              </colgroup>

              <thead>
                <tr>
                  <th scope="col">{adminText("Sinh viên / MSSV")}</th>
                  <th scope="col">{adminText("Đề bài")}</th>
                  <th scope="col">{adminText("Điểm AI")}</th>
                  <th scope="col">{adminText("Điểm GV")}</th>
                  <th scope="col">{adminText("Điểm cuối")}</th>
                  <th scope="col">{adminText("Chênh lệch")}</th>
                  <th scope="col">{adminText("Trạng thái")}</th>
                  <th scope="col">{adminText("Thao tác")}</th>
                </tr>
              </thead>

              <tbody>
                {adminRender(visible.length === 0 && <tr>
                    <td colSpan={8} className="ai-empty-state">{adminText(" Không tìm thấy bài thi phù hợp. ")}</td>
                  </tr>)}

                {adminRender(pageItems.map(item => {
                const difference = scoreDifference(item);
                return <tr key={item.id}>
                      <td data-label="Sinh viên / MSSV">
                        <div className="ai-student-info">
                          <strong>{adminRender(item.name)}</strong>
                          <small className="ai-mssv">
                            {adminRender(item.studentId)}
                          </small>
                        </div>
                      </td>

                      <td data-label="Đề bài">{adminRender(item.topic)}</td>

                      <td data-label="Điểm AI" className="ai-center-cell">
                        <strong className="text-cyan">
                          {adminRender(formatScore(aiScore(item)))}
                        </strong>
                      </td>

                      <td data-label="Điểm GV" className="ai-center-cell">
                        <strong className="text-amber">
                          {adminRender(formatScore(teacherScore(item)))}
                        </strong>
                      </td>

                      <td data-label="Điểm cuối" className="ai-center-cell">
                        <strong className="text-green">
                          {adminRender(formatScore(finalScore(item)))}
                        </strong>
                      </td>

                      <td data-label="Chênh lệch" className="ai-center-cell">
                        <span className={difference > 0.75 ? "text-rose" : ""}>
                          {adminRender(difference === null ? "Chưa đối chiếu" : `${difference.toFixed(2)}đ`)}
                        </span>
                      </td>

                      <td data-label="Trạng thái" className="ai-center-cell">
                        <span className={`ai-status-badge ${item.status === "pending" ? "grade-rose" : item.approvalMethod === "manual" ? "grade-amber" : "grade-green"}`}>
                          {adminRender(statusLabel(item))}
                        </span>
                      </td>

                      <td data-label="Thao tác" className="ai-center-cell">
                        <button className="ai-view-button" type="button" disabled={approving} aria-label={`Xem bài thi của ${item.name}`} onClick={() => selectSubmission(item)}>
                          Xem
                        </button>
                      </td>
                    </tr>;
              }))}
              </tbody>
            </table>
          </div>

          {/* Phân trang */}
          <div className="ai-list-footer">
            <p>{adminText(" Hiển thị ")}<strong>{adminRender(firstRecord)}–{adminRender(lastRecord)}</strong>{adminRender(" ")}
              trong <strong>{adminRender(visible.length)}</strong>{adminText(" bài thi ")}</p>

            <nav className="ai-pagination" aria-label={adminText("Phân trang bài thi")}>
              <button className="ai-page-button" type="button" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>{adminText(" ‹ Trước ")}</button>

              {adminRender(getPageNumbers(currentPage, totalPages).map(number => typeof number === "string" ? <span key={number} className="ai-page-gap">…</span> : <button key={number} className={`ai-page-button ${number === currentPage ? "is-active" : ""}`} type="button" aria-label={`Trang ${number}`} aria-current={number === currentPage ? "page" : undefined} onClick={() => setPage(number)}>
                    {adminRender(number)}
                  </button>))}

              <button className="ai-page-button" type="button" disabled={currentPage === totalPages} onClick={() => setPage(currentPage + 1)}>
                Sau ›
              </button>
            </nav>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>{adminText("DBCAS • Nền tảng đánh giá năng lực CSDL")}</span>
        <span>© 2026 Duy Tan University</span>
      </footer>

      {/* Hộp sửa điểm */}
      {adminRender(scoreEditor && <div className="ai-score-overlay" onClick={event => {
      if (event.target === event.currentTarget) {
        closeScoreEditor();
      }
    }}>
          <section className="ai-score-modal" role="dialog" aria-modal="true" aria-labelledby="edit-score-title" aria-busy={savingScore} ref={modalRef} tabIndex={-1}>
            <div className="ai-score-modal-head">
              <div>
                <h2 id="edit-score-title">{adminText("Chấm lại thủ công")}</h2>
                <p>{adminRender(scoreEditor.name)} · {adminRender(scoreEditor.studentId)}</p>
              </div>

              <button className="ai-score-close" type="button" aria-label={adminText("Đóng hộp chấm thủ công")} disabled={savingScore} onClick={closeScoreEditor}>
                <Icon name="close" />
              </button>
            </div>

            <p className="manual-description">{adminText(" Nhập điểm theo đánh giá của GV. Điểm AI được giữ nguyên để đối chiếu. ")}</p>

            <form onSubmit={confirmTeacherScore} noValidate>
              <div className="manual-score-heading">
                <span>{adminText("Tiêu chí")}</span>
                <span>AI</span>
                <span>GV / 1.0</span>
              </div>

              <fieldset className="manual-fields" disabled={savingScore}>
                {adminRender(RUBRIC_LABELS.map((label, index) => <label className="manual-score-row" key={label}>
                    <span>{adminRender(index + 1)}. {adminRender(label)}</span>

                    <strong>
                      {adminRender(Number(scoreEditor.aiRubric?.[index] || 0).toFixed(2))}
                    </strong>

                    <input ref={index === 0 ? firstInputRef : undefined} type="number" min="0" max="1" step="0.01" required aria-label={`Điểm GV: ${label}`} value={scoreForm[index]} onChange={event => updateScore(index, event.target.value)} />
                  </label>))}
              </fieldset>

              <div className="manual-totals" aria-live="polite">
                <div>
                  <span>{adminText("Tổng điểm AI")}</span>
                  <strong>
                    {adminRender(formatScore(aiScore(scoreEditor)))} / 3.0
                  </strong>
                </div>

                <div>
                  <span>{adminText("Tổng điểm GV")}</span>
                  <strong className="text-amber">
                    {adminRender(formatScore(editedTotal))} / 3.0
                  </strong>
                </div>
              </div>

              <label className="ai-score-reason">
                <span>{adminText("Nhận xét duyệt của GV")}</span>

                <textarea rows={4} required disabled={savingScore} placeholder={adminText("Vui lòng nhận xét")} value={teacherComment} onChange={event => {
              setTeacherComment(event.target.value);
              setScoreError("");
            }} />
              </label>

              <p className="ai-score-help">{adminText(" Xác nhận sẽ lấy điểm GV làm điểm cuối cùng, chuyển bài sang Đã duyệt thủ công. ")}</p>

              {adminRender(scoreError && <p className="ai-score-error" role="alert">
                  {adminRender(scoreError)}
                </p>)}

              <div className="ai-score-modal-actions">
                <button className="ai-button" type="button" disabled={savingScore} onClick={closeScoreEditor}>{adminText(" Hủy ")}</button>

                <button className="ai-button btn-approve" type="submit" disabled={savingScore}>
                  {adminRender(savingScore ? "Đang xác nhận..." : "Xác nhận điểm GV")}
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