import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useMemo, useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";
// TODO BE: các số liệu, radar và nhật ký dưới đây đang là dữ liệu mẫu.
// Dữ liệu giả lập ổn định; thay bằng API qua props của từng trang.
const DEMO_MAJORS = ["Kỹ thuật Phần mềm", "Khoa học Máy tính", "Hệ thống Thông tin Quản lý", "An ninh Mạng", "Công nghệ Phần mềm"];
const BASE_DEMO_STUDENTS = Array.from({
  length: 100
}, (_, index) => {
  const surnames = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Võ", "Đặng", "Bùi"];
  const middles = ["Hoàng", "Minh", "Ngọc", "Thanh", "Gia", "Quang", "Thị", "Anh", "Đức", "Hải"];
  const names = ["Long", "Thư", "Dũng", "Anh", "Linh", "Huy", "Trang", "Nam", "Vy", "Khoa", "Hân", "Bảo", "Phúc", "Châu", "Tuấn"];
  const mcqCorrect = 4 + index * 3 % 7;
  const sqlPassed = index * 5 % 4;
  const essayRaw = (40 + index * 13 % 61) / 10;
  const mcq = Number((mcqCorrect * 0.4).toFixed(2));
  const sql = sqlPassed;
  const essay = Number((essayRaw * 0.3).toFixed(2));
  const skills = [mcqCorrect, Number((sqlPassed / 3 * 10).toFixed(2)), essayRaw];
  const clos = skills.map(value => value >= 6);
  const labels = ["Truy vấn SQL", "DML & DDL", "Thiết kế & Ràng buộc"];
  const exams = ["KT CSDL Cơ Bản", "KT CSDL Nâng Cao", "SQL & Indexing Lab", "Thiết kế và Chuẩn hóa CSDL", "Transaction & ACID"];
  const id = String(21200000001 + index);
  return {
    id,
    studentId: id,
    name: `${surnames[index % 10]} ${middles[Math.floor(index / 10) % 10]} ${names[Math.floor(index / 100) % 15]}`,
    email: `sv${id}@example.com`,
    major: DEMO_MAJORS[index % DEMO_MAJORS.length],
    year: "2026-2027",
    attempts: 1,
    examId: `DEMO-EXAM-${String(index % 27 + 1).padStart(3, "0")}`,
    examTitle: exams[index % 27 % exams.length],
    submittedAt: `${String(8 + index % 9).padStart(2, "0")}:${String(index * 7 % 60).padStart(2, "0")} • ${String(1 + index % 12).padStart(2, "0")}/10/2026`,
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
    strong: labels[skills.indexOf(Math.max(...skills))],
    weak: labels[skills.indexOf(Math.min(...skills))]
  };
});
const DEMO_CLO_STUDENTS = BASE_DEMO_STUDENTS.map(student => ({
  ...student,
  clos: student.clos.map(passed => passed ? "pass" : "weak")
}));
const DEMO_OVERVIEW = (() => {
  const passed = BASE_DEMO_STUDENTS.filter(s => s.cloCount === 3).length;
  return {
    averagePercent: Number((BASE_DEMO_STUDENTS.reduce((sum, s) => sum + s.score, 0) / BASE_DEMO_STUDENTS.length * 10).toFixed(1)),
    passed,
    notPassed: BASE_DEMO_STUDENTS.length - passed,
    passedPercent: Number((passed / BASE_DEMO_STUDENTS.length * 100).toFixed(1)),
    notPassedPercent: Number(((BASE_DEMO_STUDENTS.length - passed) / BASE_DEMO_STUDENTS.length * 100).toFixed(1))
  };
})();
const DEMO_CLO_RATES = [0, 1, 2].map(index => Number((BASE_DEMO_STUDENTS.filter(s => s.clos[index]).length / BASE_DEMO_STUDENTS.length * 100).toFixed(1)));
const DEMO_STUDENTS = BASE_DEMO_STUDENTS;
const PAGE_SIZE = 10;
// Khi có API, truyền students={data} với điểm thành phần theo thang 4/3/3.
export default function HomeAdmin({
  onLogout,
  onViewDetail,
  onExport,
  onYearChange,
  students: sourceStudents = DEMO_STUDENTS,
  createTestHref = "/TN_Admin",
  managementHref = "/Quan_ly_bai_kiem_tra_Admin"
}) {
  useAdminLanguage();

  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [year, setYear] = useState("2026 - 2027");
  const [page, setPage] = useState(1);
  const [exporting, setExporting] = useState(false);
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const students = useMemo(() => (Array.isArray(sourceStudents) ? sourceStudents : []).map(student => ({
    ...student,
    id: String(student.id ?? ""),
    name: String(student.name ?? ""),
    mcq: Math.max(0, Math.min(4, Number(student.mcq) || 0)),
    sql: Math.max(0, Math.min(3, Number(student.sql) || 0)),
    essay: Math.max(0, Math.min(3, Number(student.essay) || 0))
  })), [sourceStudents]);
  const summary = useMemo(() => {
    const scores = students.map(s => s.mcq + s.sql + s.essay).sort((a, b) => a - b);
    const best = students.reduce((winner, s) => !winner || s.mcq + s.sql + s.essay > winner.mcq + winner.sql + winner.essay ? s : winner, null);
    return {
      average: scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2) : "0.00",
      passRate: scores.length ? (scores.filter(x => x >= 5).length / scores.length * 100).toFixed(1) : "0.0",
      highCount: scores.filter(x => x >= 8).length,
      highRate: scores.length ? (scores.filter(x => x >= 8).length / scores.length * 100).toFixed(1) : "0.0",
      median: scores.length ? ((scores[Math.floor((scores.length - 1) / 2)] + scores[Math.floor(scores.length / 2)]) / 2).toFixed(2) : "0.00",
      best
    };
  }, [students]);
  const cloRates = [0, 1, 2].map(i => students.length ? Number((students.filter(student => student.clos?.[i]).length / students.length * 100).toFixed(1)) : 0);
  const radarPoints = `150,${155 - 110 * cloRates[0] / 100} ${150 + 95 * cloRates[1] / 100},${155 + 55 * cloRates[1] / 100} ${150 - 95 * cloRates[2] / 100},${155 + 55 * cloRates[2] / 100}`;
  const totalStudents = students.length.toLocaleString("vi-VN");
  const normalize = value => String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d").toLowerCase().trim();
  const filteredStudents = students.filter(student => normalize(`${student.name} ${student.id}`).includes(normalize(query)));
  const pageSize = PAGE_SIZE;
  const totalPages = Math.max(1, Math.ceil(filteredStudents.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const visibleStudents = filteredStudents.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const visibleCount = filteredStudents.length;
  const pageNumbers = [...new Set([1, currentPage - 1, currentPage, currentPage + 1, totalPages])].filter(number => number >= 1 && number <= totalPages).sort((a, b) => a - b);
  function changeQuery(value) {
    setQuery(value);
    setPage(1);
  }
  async function handleViewDetail(id) {
    try {
      if (onViewDetail) await onViewDetail(id);else navigate("/Danh_gia_nang_luc_Admin", {
        state: {
          studentId: id
        }
      });
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Không thể mở chi tiết sinh viên.");
    }
  }
  async function handleYearChange(value) {
    setYear(value);
    try {
      if (onYearChange) await onYearChange(value);else setNotice(adminText("Chưa có dữ liệu theo năm học. Các số liệu hiện tại chưa thay đổi."));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Không thể tải dữ liệu năm học.");
    }
  }
  async function handleExport() {
    if (exporting) return;
    setExporting(true);
    try {
      if (onExport) {
        await onExport();
      } else {
        const cell = value => `"${String(value).replace(/"/g, '""')}"`;
        const rows = [["Họ tên", "MSSV", "Trắc nghiệm (4đ)", "SQL (3đ)", "Tự luận (3đ)", "Tổng điểm (10đ)"], ...filteredStudents.map(s => [s.name, `="${s.id}"`, s.mcq.toFixed(2), s.sql.toFixed(2), s.essay.toFixed(2), (s.mcq + s.sql + s.essay).toFixed(2)])];
        const csv = "\uFEFF" + rows.map(row => row.map(cell).join(",")).join("\r\n");
        const url = URL.createObjectURL(new Blob([csv], {
          type: "text/csv;charset=utf-8;"
        }));
        const link = document.createElement("a");
        link.href = url;
        link.download = "DBCAS_Ket_qua_sinh_vien.csv";
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        setNotice(adminText(`Đã xuất ${filteredStudents.length} kết quả theo bộ lọc tìm kiếm.`));
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Không thể xuất báo cáo.");
    } finally {
      setExporting(false);
    }
  }
  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      // TODO BE: onLogout thu hồi phiên và xóa trạng thái xác thực.
      if (onLogout) await onLogout();
      navigate("/Dang_nhap");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Không thể đăng xuất.");
    } finally {
      setLoggingOut(false);
    }
  }
  return <div className="dbcas-admin-home" style={{
    backgroundImage: `linear-gradient(rgba(7,11,20,.8), rgba(7,11,20,.8)), url(${background})`
  }}>
            {/* Icon SVG dùng chung */}
            <svg className="svg-definitions" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <defs>
                    <symbol id="admin-i-plus" viewBox="0 0 24 24">
                        <path d="M12 5v14M5 12h14" />
                    </symbol>
                    <symbol id="admin-i-home" viewBox="0 0 24 24">
                        <path d="m3 10 9-7 9 7v10H3zM9 20v-7h6v7" />
                    </symbol>
                    <symbol id="admin-i-users" viewBox="0 0 24 24">
                        <circle cx="9" cy="7" r="3" />
                        <path d="M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5.65" />
                    </symbol>
                    <symbol id="admin-i-cap" viewBox="0 0 24 24">
                        <path d="m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v7" />
                    </symbol>
                    <symbol id="admin-i-document" viewBox="0 0 24 24">
                        <path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6" />
                    </symbol>
                    <symbol id="admin-i-robot" viewBox="0 0 24 24">
                        <rect x="4" y="7" width="16" height="13" rx="3" />
                        <path d="M12 3v4M2 11v5M22 11v5M9 16h6" />
                        <circle cx="8.5" cy="12" r=".5" />
                        <circle cx="15.5" cy="12" r=".5" />
                    </symbol>
                    <symbol id="admin-i-chart" viewBox="0 0 24 24">
                        <path d="M4 3v17h17M8 16v-5M13 16V7M18 16V4" />
                    </symbol>
                    <symbol id="admin-i-settings" viewBox="0 0 24 24">
                        <path d="m9 3-1 3-3 1v4l-2 1 2 1v4l3 1 1 3h6l1-3 3-1v-4l2-1-2-1V7l-3-1-1-3z" />
                        <circle cx="12" cy="12" r="3" />
                    </symbol>
                    <symbol id="admin-i-logout" viewBox="0 0 24 24">
                        <path d="M10 4H4v16h6M9 12h12M17 8l4 4-4 4" />
                    </symbol>
                    <symbol id="admin-i-search" viewBox="0 0 24 24">
                        <circle cx="10.5" cy="10.5" r="6.5" />
                        <path d="m16 16 5 5" />
                    </symbol>
                    <symbol id="admin-i-help" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="9" />
                        <path d="M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 2-2.5 3.5M12 16h.01" />
                    </symbol>
                    <symbol id="admin-i-bell" viewBox="0 0 24 24">
                        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
                    </symbol>
                    <symbol id="admin-i-calendar" viewBox="0 0 24 24">
                        <rect x="3" y="5" width="18" height="16" rx="2" />
                        <path d="M7 3v4M17 3v4M3 11h18" />
                    </symbol>
                    <symbol id="admin-i-chevron" viewBox="0 0 24 24">
                        <path d="m8 5 7 7-7 7" />
                    </symbol>
                    <symbol id="admin-i-medal" viewBox="0 0 24 24">
                        <circle cx="12" cy="8" r="5" />
                        <path d="m8 12-1 9 5-3 5 3-1-9" />
                    </symbol>
                    <symbol id="admin-i-sliders" viewBox="0 0 24 24">
                        <path d="M4 7h3M11 7h9M4 17h9M17 17h3" />
                        <circle cx="9" cy="7" r="2" />
                        <circle cx="15" cy="17" r="2" />
                    </symbol>
                    <symbol id="admin-i-radar" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="9" />
                        <circle cx="12" cy="12" r="5" />
                        <circle cx="12" cy="12" r="1" />
                        <path d="m12 12 7-7" />
                    </symbol>
                    <symbol id="admin-i-shield" viewBox="0 0 24 24">
                        <path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6" />
                    </symbol>
                    <symbol id="admin-i-terminal" viewBox="0 0 24 24">
                        <rect x="3" y="4" width="18" height="16" rx="2" />
                        <path d="m7 9 3 3-3 3M13 15h4" />
                    </symbol>
                    <symbol id="admin-i-alert" viewBox="0 0 24 24">
                        <path d="m12 3 10 18H2zM12 9v5M12 17h.01" />
                    </symbol>
                    <symbol id="admin-i-cpu" viewBox="0 0 24 24">
                        <rect x="6" y="6" width="12" height="12" rx="2" />
                        <rect x="9" y="9" width="6" height="6" rx="1" />
                        <path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4" />
                    </symbol>
                    <symbol id="admin-i-sync" viewBox="0 0 24 24">
                        <path d="M20 7a8 8 0 0 0-14-2L3 8M3 3v5h5M4 17a8 8 0 0 0 14 2l3-3M16 16h5v5" />
                    </symbol>
                    <symbol id="admin-i-server" viewBox="0 0 24 24">
                        <rect x="3" y="3" width="18" height="7" rx="2" />
                        <rect x="3" y="14" width="18" height="7" rx="2" />
                        <path d="M7 6.5h.01M7 17.5h.01M11 6.5h6M11 17.5h6" />
                    </symbol>
                    <symbol id="admin-i-download" viewBox="0 0 24 24">
                        <path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5" />
                    </symbol>
                    <symbol id="admin-i-activity" viewBox="0 0 24 24">
                        <path d="M3 12h4l3-8 4 16 3-8h4" />
                    </symbol>
                </defs>
            </svg>
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-content">
                    <div className="sidebar-brand">
                        <img src={logo} alt="Logo DBCAS" draggable="false" />
                    </div>
                    <Link className="btn-new" to={createTestHref}>
                        <svg className="icon" aria-hidden="true">
                            <use href="#admin-i-plus"></use>
                        </svg>
                        <span>{adminText("Tạo bài kiểm tra")}</span>
                    </Link>
                    <nav className="sidebar-nav" aria-label={adminText("Menu quản trị")}>
                        <Link className="nav-link active" to="/Home_Admin" aria-current="page">
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-home" /></svg>
                            <span>{adminText("Trang chủ")}</span>
                            <span className="nav-dot"></span>
                        </Link>
                        <Link className="nav-link" to="/Danh_gia_nang_luc_Admin">
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-users" /></svg>
                            <span>{adminText("Đánh giá năng lực")}</span>
                        </Link>
                        <Link className="nav-link" to="/CLO_Ky_nang_Admin">
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-cap" /></svg>
                            <span>{adminText("CLO & Kỹ năng")}</span>
                        </Link>
                        <Link className="nav-link" to={managementHref}>
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-document" /></svg>
                            <span>{adminText("Quản lý bài kiểm tra")}</span>
                        </Link>
                        <Link className="nav-link" to="/Danh_gia_AI_Admin">
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-robot" /></svg>
                            <span>{adminText("Đánh giá bằng AI")}</span>
                        </Link>
                        <Link className="nav-link" to="/Bao_cao_Admin">
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-chart" /></svg>
                            <span>{adminText("Báo cáo")}</span>
                        </Link>
                        <Link className="nav-link" to="/Cai_dat_Admin">
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-settings" /></svg>
                            <span>{adminText("Cài đặt")}</span>
                        </Link>
                    </nav>
                </div>
                <div className="sidebar-bottom">
                    <button className="btn-logout" type="button" onClick={handleLogout} disabled={loggingOut}>
                        <svg className="icon" aria-hidden="true">
                            <use href="#admin-i-logout" />
                        </svg>
                        <span>{adminRender(loggingOut ? "Đang đăng xuất..." : "Đăng xuất")}</span>
                    </button>
                </div>
            </aside>
            {/* Thanh phía trên */}
            <header className="topbar admin-unified-topbar">
                <div className="breadcrumb">
                    <span>DBCAS Admin</span>
                    <svg className="icon" aria-hidden="true"><use href="#admin-i-chevron" /></svg>
                    <strong>{adminText("Trang chủ")}</strong>
                </div>
                <div className="topbar-actions">
                    
                    <button className="icon-button" type="button" aria-label={adminText("Trợ giúp")} onClick={() => setNotice(adminText("Liên hệ nhóm hỗ trợ DBCAS."))}>
                        <svg className="icon" aria-hidden="true"><use href="#admin-i-help" /></svg>
                    </button>
                    <NotificationMenu role="admin" className="icon-button notification" />
                    <AdminAccountMenu onLogout={handleLogout} />
                </div>
            </header>
            <main className="main">
                {/* Tổng quan */}
                <section className="dashboard-overview" aria-label={adminText("Tổng quan hệ thống")}>
                    <div className="hero card">
                        <div className="hero-bar">
                            <label className="year-filter">
                                <svg className="icon" aria-hidden="true"><use href="#admin-i-calendar" /></svg>
                                <select aria-label={adminText("Năm học")} value={year} onChange={event => handleYearChange(event.target.value)}>
                                    <option>2024 - 2025</option>
                                    <option>2025 - 2026</option>
                                    <option>2026 - 2027</option>
                                </select>
                            </label>
                            <span className="live-update">
                                <span className="live-dot"></span>{adminText(" Cập nhật 16:45:20 ")}</span>
                        </div>
                        <h1>{adminText(" Xin chào Admin! ")}<span>{adminText("Hệ thống đang hoạt động tối ưu.")}</span>
                        </h1>
                        <p>{adminText(" Theo dõi năng lực của ")}<strong>{adminRender(totalStudents)}{adminText(" sinh viên")}</strong>{adminText(" thông qua 10 câu hỏi trắc nghiệm, 3 bài thực hành SQL Sandbox và 1 bài tự luận thiết kế CSDL được hỗ trợ đánh giá bằng AI. ")}</p>
                    </div>
                    <div className="stats">
                        <article className="stat-card card">
                            <div className="stat-heading">
                                <span>{adminText("Tổng sinh viên")}</span>
                                <span className="stat-icon cyan">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-users" /></svg>
                                </span>
                            </div>
                            <div className="stat-value">
                                <strong>{adminRender(totalStudents)}</strong>
                                <span className="growth">+12.4%</span>
                            </div>
                            <p>{adminText("So với học kỳ trước")}</p>
                            <div className="progress">
                                <span style={{
                width: "88%"
              }}></span>
                            </div>
                        </article>
                        <article className="stat-card card">
                            <div className="stat-heading">
                                <span>{adminText("Bài kiểm tra")}</span>
                                <span className="stat-icon green">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-document" /></svg>
                                </span>
                            </div>
                            <div className="stat-value">
                                <strong>27</strong>
                                <span className="stat-unit">{adminText("đợt thi")}</span>
                            </div>
                            <p><span className="live-dot"></span>{adminText(" 13 đề đang soạn")}</p>
                            <div className="progress green-progress">
                                <span style={{
                width: "65%"
              }}></span>
                            </div>
                        </article>
                        <article className="stat-card stat-wide card">
                            <span className="score-icon">
                                <svg className="icon" aria-hidden="true"><use href="#admin-i-medal" /></svg>
                            </span>
                            <div className="score-content">
                                <p>{adminText("Điểm năng lực trung bình")}</p>
                                <div className="stat-value">
                                    <strong>{adminRender(summary.average)}</strong>
                                    <span className="stat-unit">/ 10</span>
                                </div>
                            </div>
                            <div className="clo-tag">
                                <span>{adminText("ĐẠT CLO")}</span>
                                <strong>{adminRender(students.length ? (students.filter(student => student.clos?.every(Boolean)).length / students.length * 100).toFixed(1) : "0.0")}%</strong>
                                <small>{adminText("Mục tiêu ≥ 85%")}</small>
                            </div>
                        </article>
                    </div>
                </section>
                {/* Ma trận và Nhật ký */}
                <section className="analytics-grid">
                    <section className="card competency-card">
                        <div className="analytics-heading">
                            <span className="heading-icon">
                                <svg className="icon" aria-hidden="true"><use href="#admin-i-chart" /></svg>
                            </span>
                            <div className="heading-content">
                                <h2>{adminText("Ma Trận & Đánh Giá Năng Lực CSDL")}</h2>
                                <p>{adminText(" Phân tích Concept Breakdown, biểu đồ Radar và khoảng cách năng lực ")}</p>
                            </div>
                            <span className="cohort-badge">
                                <span className="live-dot"></span> {adminRender(totalStudents)}{adminText(" Học viên ")}</span>
                        </div>
                        <div className="competency-panels">
                            {/* Concept Breakdown */}
                            <div className="analytics-panel concept-panel">
                                <div className="panel-heading">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-sliders" /></svg>
                                    <h3>CONCEPT BREAKDOWN</h3>
                                    <span className="benchmark">{adminText("Benchmark: ĐHQGHN")}</span>
                                </div>
                                <article className="skill-box">
                                    <div className="skill-heading">
                                        <div className="skill-name">
                                            <h4>{adminText("Truy vấn SQL")}</h4>
                                            <span className="skill-status cyan-status">{adminRender(cloRates[0] >= 80 ? "Đạt chuẩn" : "Cần bồi dưỡng")}</span>
                                        </div>
                                        <div className="skill-rate">
                                            <span>{adminText("Tỷ lệ đạt")}</span>
                                            <b className="text-cyan">{adminRender(cloRates[0])}%</b>
                                        </div>
                                    </div>
                                    <div className="progress">
                                        <span style={{
                    width: `${cloRates[0]}%`
                  }}></span>
                                    </div>
                                    <p>{adminText("Trọng tâm: JOIN, Gom nhóm & Truy vấn nâng cao")}</p>
                                </article>
                                <article className="skill-box">
                                    <div className="skill-heading">
                                        <div className="skill-name">
                                            <h4>DML/DDL</h4>
                                            <span className={`skill-status ${cloRates[1] >= 80 ? "green-status" : "amber-status"}`}>{adminRender(cloRates[1] >= 80 ? "Đạt chuẩn" : "Cần bồi dưỡng")}</span>
                                        </div>
                                        <div className="skill-rate">
                                            <span>{adminText("Tỷ lệ đạt")}</span>
                                            <b className="text-green">{adminRender(cloRates[1])}%</b>
                                        </div>
                                    </div>
                                    <div className="progress green-progress">
                                        <span style={{
                    width: `${cloRates[1]}%`
                  }}></span>
                                    </div>
                                    <p>{adminText("Trọng tâm: Cú pháp DML/DDL, Schema & Views")}</p>
                                </article>
                                <article className="skill-box">
                                    <div className="skill-heading">
                                        <div className="skill-name">
                                            <h4>{adminText("Thiết kế & Ràng buộc")}</h4>
                                            <span className="skill-status amber-status">{adminRender(cloRates[2] >= 80 ? "Đạt chuẩn" : "Cần bồi dưỡng")}</span>
                                        </div>
                                        <div className="skill-rate">
                                            <span>{adminText("Tỷ lệ đạt")}</span>
                                            <b className="text-amber">{adminRender(cloRates[2])}%</b>
                                        </div>
                                    </div>
                                    <div className="progress amber-progress">
                                        <span style={{
                    width: `${cloRates[2]}%`
                  }}></span>
                                    </div>
                                    <p>{adminText("Trọng tâm: Ràng buộc toàn vẹn, Chuẩn hóa dữ liệu")}</p>
                                </article>
                            </div>
                            {/* Radar */}
                            <div className="analytics-panel radar-panel">
                                <div className="panel-heading">
                                    <svg className="icon text-purple" aria-hidden="true">
                                        <use href="#admin-i-radar" />
                                    </svg>
                                    <h3>COMPETENCY RADAR</h3>
                                </div>
                                <div className="radar-legend">
                                    <span><i className="legend-line"></i>{adminText("Thực tế")}</span>
                                    <span><i className="legend-line target"></i>{adminText("Mục tiêu 80%")}</span>
                                </div>
                                <svg className="radar-chart" viewBox="0 0 300 245" role="img" aria-label={`Năng lực SQL ${cloRates[0]}%, DML DDL ${cloRates[1]}%, Thiết kế ${cloRates[2]}%`}>
                                    <g className="radar-grid">
                                        <polygon points="150,45 245,210 55,210" />
                                        <polygon points="150,67 226,199 74,199" />
                                        <polygon points="150,89 207,188 93,188" />
                                        <polygon points="150,111 188,177 112,177" />
                                        <polygon points="150,133 169,166 131,166" />
                                        <path d="M150 155V45M150 155L245 210M150 155L55 210" />
                                    </g>
                                    <polygon className="radar-target" points="150,67 226,199 74,199" />
                                    <polygon className="radar-data" points={radarPoints} />
                                    <circle cx="150" cy={155 - 110 * cloRates[0] / 100} r="3" fill="#22d3ee" />
                                    <circle cx={150 + 95 * cloRates[1] / 100} cy={155 + 55 * cloRates[1] / 100} r="3" fill="#34d399" />
                                    <circle cx={150 - 95 * cloRates[2] / 100} cy={155 + 55 * cloRates[2] / 100} r="3" fill="#fbbf24" />
                                    <g className="radar-labels">
                                        <text x="150" y="25" textAnchor="middle">{adminText("Truy vấn SQL")}</text>
                                        <text x="20" y="232">{adminText("Thiết kế & Ràng buộc")}</text>
                                        <text x="280" y="232" textAnchor="end">DML/DDL</text>
                                    </g>
                                </svg>
                                <div className="radar-verdict">
                                    <div>
                                        <svg className="icon text-green" aria-hidden="true">
                                            <use href="#admin-i-shield" />
                                        </svg>
                                        <span>{adminText("Trụ cột đạt mục tiêu")}<br /><b>{adminRender(cloRates.filter(value => value >= 80).length)}{adminText("/3 trụ cột")}</b></span>
                                    </div>
                                    <p>{adminText("Tỷ lệ đạt trung bình:")}<br /><strong>{adminRender((cloRates.reduce((sum, value) => sum + value, 0) / 3).toFixed(1))}%</strong></p>
                                </div>
                            </div>
                        </div>
                        {/* Learner Analytics */}
                        <div className="learner-panel">
                            <div className="learner-heading">
                                <h3>
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-users" /></svg> LEARNER ANALYTICS
                                </h3>
                                <span className="cohort-badge">{adminRender(totalStudents)}{adminText(" Học viên")}</span>
                            </div>
                            <div className="learner-kpis">
                                <div className="learner-kpi">
                                    <p>{adminText("Tỉ lệ đạt chuẩn")}</p>
                                    <div className="kpi-value">
                                        <b className="text-green">{adminRender(summary.passRate)}%</b>
                                        <small className="text-green">+3.2% ↑</small>
                                    </div>
                                </div>
                                <div className="learner-kpi">
                                    <p>{adminText("Điểm Trung Bình Khóa")}</p>
                                    <div className="kpi-value stacked">
                                        <b>{adminRender(summary.average)} / 10</b>
                                        <small className="text-cyan">{adminText("Trung vị ")}{adminRender(summary.median)}</small>
                                    </div>
                                </div>
                                <div className="learner-kpi">
                                    <p>{adminText("Thủ Khoa Đợt Thi")}</p>
                                    <div className="kpi-value">
                                        <b className="text-purple">{adminRender(summary.best ? (summary.best.mcq + summary.best.sql + summary.best.essay).toFixed(2) : "—")}</b>
                                        <small>{adminText("Điểm cao nhất")}</small>
                                    </div>
                                </div>
                                <div className="learner-kpi">
                                    <p>{adminText("Tỉ Lệ Giỏi / Xuất sắc")}</p>
                                    <div className="kpi-value">
                                        <b className="text-purple">{adminRender(summary.highRate)}%</b>
                                        <small>{adminRender(summary.highCount.toLocaleString("vi-VN"))} SV</small>
                                    </div>
                                </div>
                            </div>
                            <div className="learner-bottom">
                                <div className="top-learner">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-medal" /></svg>
                                    <p>
                                        <strong>Top 1: {adminRender(summary.best?.name || "Chưa có dữ liệu")}</strong>
                                        <small>MSSV: {adminRender(summary.best?.id || "—")}</small>
                                    </p>
                                </div>
                                <button className="ranking-button" type="button" onClick={() => navigate("/Xep_hang_Admin", {
                state: {
                  students
                }
              })}>{adminText(" Xem bảng xếp hạng đầy đủ → ")}</button>
                            </div>
                        </div>
                    </section>
                    {/* Nhật ký hệ thống */}
                    <aside className="card activity-card">
                        <div className="activity-heading">
                            <svg className="icon text-cyan" aria-hidden="true">
                                <use href="#admin-i-activity" />
                            </svg>
                            <h2>{adminText("Nhật Ký & Cảnh Báo Trực Tiếp")}</h2>
                            <span className="live-dot"></span>
                        </div>
                        <ul className="activity-list">
                            <li>
                                <span className="activity-icon green">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-terminal" /></svg>
                                </span>
                                <div className="activity-content">
                                    <p>
                                        <b>SV 21200000001</b>{adminText(" hoàn thành 3 bài thực hành SQL, đạt toàn bộ test case. ")}</p>
                                    <time>{adminText("1 phút trước")}</time>
                                </div>
                            </li>
                            <li>
                                <span className="activity-icon cyan">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-robot" /></svg>
                                </span>
                                <div className="activity-content">
                                    <p>{adminText("AI đã đánh giá ")}<b>{adminText("18 bài tự luận")}</b>{adminText(" thiết kế Schema & ERD.")}</p>
                                    <time>{adminText("5 phút trước")}</time>
                                </div>
                            </li>
                            <li className="activity-warning">
                                <span className="activity-icon amber">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-alert" /></svg>
                                </span>
                                <div className="activity-content">
                                    <p>{adminText(" Phát hiện ")}<b>{adminText("14 sinh viên")}</b>{adminText(" cần củng cố kiến thức Transaction & Concurrency. ")}</p>
                                    <time>{adminText("18 phút trước")}</time>
                                </div>
                            </li>
                            <li>
                                <span className="activity-icon">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-cpu" /></svg>
                                </span>
                                <div className="activity-content">
                                    <p><b>Docker Sandbox 04</b>{adminText(" đã giải phóng tài nguyên sau đợt thi.")}</p>
                                    <time>{adminText("25 phút trước")}</time>
                                </div>
                            </li>
                            <li>
                                <span className="activity-icon">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-document" /></svg>
                                </span>
                                <div className="activity-content">
                                    <p>{adminText("Bài tự luận của ")}<b>SV 21200000002</b>{adminText(" đã được chấm theo rubric AI.")}</p>
                                    <time>{adminText("31 phút trước")}</time>
                                </div>
                            </li>
                            <li>
                                <span className="activity-icon green">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-sync" /></svg>
                                </span>
                                <div className="activity-content">
                                    <p>{adminText("Đã đồng bộ kết quả của ")}<b>{adminRender(totalStudents)}{adminText(" sinh viên")}</b>.</p>
                                    <time>{adminText("42 phút trước")}</time>
                                </div>
                            </li>
                            <li>
                                <span className="activity-icon">
                                    <svg className="icon" aria-hidden="true"><use href="#admin-i-server" /></svg>
                                </span>
                                <div className="activity-content">
                                    <p>{adminText(" Khởi tạo ")}<b>45 containers MySQL/PostgreSQL</b>{adminText(" phục vụ ca thi chiều. ")}</p>
                                    <time>{adminText("50 phút trước")}</time>
                                </div>
                            </li>
                        </ul>
                        <button
  className="activity-more"
  type="button"
  onClick={() => navigate("/Nhat_ky_he_thong_Admin")}
>
  <span>{adminText("Xem toàn bộ nhật ký hệ thống")}</span>

  <svg className="icon" aria-hidden="true">
    <use href="#admin-i-chevron" />
  </svg>
</button>
                    </aside>
                </section>
                {/* Bảng kết quả */}
                <section className="card results">
                    <div className="card-head">
                        <div>
                            <h2>{adminText("Kết quả đánh giá sinh viên gần đây")}</h2>
                            <p>{adminText("Trọng số: Trắc nghiệm 40% • SQL 30% • Tự luận 30%")}</p>
                        </div>
                        <div className="result-tools">
                            
                            <button className="btn-export" type="button" onClick={handleExport} disabled={exporting}>
                                <svg className="icon" aria-hidden="true"><use href="#admin-i-download" /></svg>
                                <span>{adminRender(exporting ? "Đang xuất..." : "Xuất báo cáo")}</span>
                            </button>
                        </div>
                    </div>
                    <div className="table-wrap">
                        <table>
                            <colgroup>
                                <col className="col-student" />
                                <col className="col-exam" />
                                <col className="col-score" />
                                <col className="col-score" />
                                <col className="col-score" />
                                <col className="col-total" />
                                <col className="col-action" />
                            </colgroup>
                            <thead>
                                <tr>
                                    <th scope="col">{adminText("SINH VIÊN")}</th>
                                    <th scope="col">{adminText("BÀI KIỂM TRA")}</th>
                                    <th scope="col">{adminText("TRẮC NGHIỆM")}</th>
                                    <th scope="col">SQL SANDBOX</th>
                                    <th scope="col">{adminText("TỰ LUẬN AI")}</th>
                                    <th scope="col">{adminText("TỔNG ĐIỂM")}</th>
                                    <th scope="col">{adminText("THAO TÁC")}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {adminRender(visibleStudents.map(student => {
                const total = student.mcq + student.sql + student.essay;
                const grade = total >= 9 ? "A+" : total >= 8 ? "A" : total >= 7 ? "B+" : total >= 5 ? "Đạt" : "Cần ôn luyện";
                const color = total >= 9 ? "grade-green" : total >= 8 ? "grade-cyan" : total >= 5 ? "grade-slate" : "grade-rose";
                return <tr key={student.id}>
                                            <td><div className="student">
                                                <span className="student-avatar av-blue">{adminRender(student.name.trim().split(/\s+/).slice(-2).map(word => word[0]).join(""))}</span>
                                                <div><strong>{adminRender(student.name)}</strong><small>{adminRender(student.id)}</small></div>
                                            </div></td>
                                            <td><span>{adminRender(student.examTitle || "Bài kiểm tra CSDL")}</span><small>{adminRender(student.submittedAt || "")}</small></td>
                                            <td>{adminRender(student.mcqCorrect != null ? `${student.mcqCorrect}/10` : "Trắc nghiệm")}<small>{adminRender(student.mcq.toFixed(2))}{adminText(" điểm")}</small></td>
                                            <td className="text-green">{adminRender(student.sqlPassed != null ? `${student.sqlPassed}/3 Pass` : "SQL")}<small>{adminRender(student.sql.toFixed(2))}{adminText(" điểm")}</small></td>
                                            <td className="text-cyan">{adminRender(student.essayRaw != null ? `${student.essayRaw}/10` : "Tự luận")}<small>{adminRender(student.essay.toFixed(2))}{adminText(" điểm")}</small></td>
                                            <td><div className="total-score"><b>{adminRender(total.toFixed(2))}</b><span className={`grade ${color}`}>{adminRender(grade)}</span></div></td>
                                            <td><button className="btn-detail" type="button" onClick={() => handleViewDetail(student.id)}>{adminText("Xem chi tiết")}</button></td>
                                        </tr>;
              }))}
                                {adminRender(visibleCount === 0 && <tr><td colSpan={7}>{adminText("Không tìm thấy sinh viên phù hợp.")}</td></tr>)}
                            </tbody>
                        </table>
                    </div>
                    <div className="pager">
                        <p>{adminText("Hiển thị ")}<strong>{adminRender(visibleCount ? (currentPage - 1) * pageSize + 1 : 0)}–{adminRender(Math.min(currentPage * pageSize, visibleCount))}</strong> trong <strong>{adminRender(visibleCount)}</strong>{adminText(" kết quả")}</p>
                        <nav className="pagination" aria-label={adminText("Phân trang kết quả sinh viên")}>
                            <button className="page-button" type="button" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>{adminText("Trước")}</button>
                            {adminRender(pageNumbers.map((number, index) => <span key={number} style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6
            }}>
                                    {adminRender(index > 0 && number - pageNumbers[index - 1] > 1 && <span aria-hidden="true">…</span>)}
                                    <button className={`page-button${number === currentPage ? " active" : ""}`} type="button" aria-current={number === currentPage ? "page" : undefined} onClick={() => setPage(number)}>{adminRender(number)}</button></span>))}
                            <button className="page-button next" type="button" disabled={currentPage === totalPages} onClick={() => setPage(currentPage + 1)}>{adminText(" Tiếp ")}<svg className="icon" aria-hidden="true"><use href="#admin-i-chevron" /></svg>
                            </button>
                        </nav>
                    </div>
                </section>
            </main>
            <footer className="footer">
                <span>{adminText("DBCAS • Nền tảng đánh giá năng lực CSDL")}</span>
                <span>© 2026 Duy Tan University</span>
            </footer>
            {adminRender(notice && <div className="admin-notice" role="status">{adminRender(notice)}<button type="button" aria-label={adminText("Đóng thông báo")} onClick={() => setNotice(adminText(""))}>{adminText("×")}</button></div>)}
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