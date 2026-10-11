import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./Danh_gia_nang_luc_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";

const ID = "dgnl-i";
// TODO BE: chỉ số, radar và danh sách sinh viên dưới đây đang là dữ liệu mẫu.
const STUDENTS = [
  { name: "Nguyễn Hoàng Long", email: "long.nh23@dtu.edu.vn", id: "SV21020412", major: "Kỹ thuật phần mềm", initials: "NL", avatar: "av-blue", score: "9.5", grade: "A+", gradeClass: "grade-green", level: "Xuất sắc /10", strong: "CLO 1: CTE, Window Fns", weak: "CLO 3: Normalization 3NF/BCNF", clo: "Đạt 3/3 CLO", cloClass: "text-green" },
  { name: "Trần Minh Thư", email: "thu.tm23@dtu.edu.vn", id: "SV21020389", major: "Hệ thống thông tin", initials: "TT", avatar: "av-green", score: "9.0", grade: "A", gradeClass: "grade-cyan", level: "Giỏi /10", strong: "CLO 1: Subqueries & JOIN", weak: "CLO 3: Ràng buộc FK & CHECK", clo: "Đạt 3/3 CLO", cloClass: "text-green" },
  { name: "Lê Quang Dũng", email: "dung.lq23@dtu.edu.vn", id: "SV21020511", major: "Khoa học máy tính", initials: "LD", avatar: "av-purple", score: "7.5", grade: "B+", gradeClass: "grade-slate", level: "Khá /10", strong: "CLO 2: DML (INSERT, UPDATE)", weak: "CLO 1: Window Fns & CTE", clo: "Đạt 2/3 · thiếu CLO 1", cloClass: "text-amber" },
  { name: "Phạm Thị Mai Anh", email: "anh.ptm23@dtu.edu.vn", id: "SV21020294", major: "An toàn thông tin", initials: "MA", avatar: "av-orange", score: "4.9", grade: "Cần ôn", gradeClass: "grade-rose", level: "/10", strong: "CLO 2: Cú pháp DDL cơ bản", weak: "CLO 1 truy vấn đa bảng, CLO 3 Schema/PK-FK", clo: "Đạt 1/3 · hổng CLO 1, 3", cloClass: "text-rose" },
  { name: "Hoàng Đức Huy", email: "huy.hd23@dtu.edu.vn", id: "SV21020911", major: "Kỹ thuật phần mềm", initials: "HH", avatar: "av-blue", score: "8.9", grade: "A", gradeClass: "grade-cyan", level: "Giỏi /10", strong: "CLO 1: Querying đa bảng", weak: "CLO 3: Mô hình ERD chuẩn hóa", clo: "Đạt 3/3 CLO", cloClass: "text-green" },
];

function Icon({ name }) {
  return <svg className="icon" aria-hidden="true"><use href={`#${ID}-${name}`} /></svg>;
}

function matches(query, student) {
  const text = `${student.name} ${student.email} ${student.id} ${student.major}`.toLocaleLowerCase("vi");
  return text.includes(query.trim().toLocaleLowerCase("vi"));
}

export default function DanhGiaNangLucAdmin({ onLogout }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [year, setYear] = useState("Khoá 2024 - 2025");
  const [major, setMajor] = useState("Tất cả ngành");
  const [status, setStatus] = useState("Tất cả trạng thái CLO");
  const [score, setScore] = useState("Tất cả mức điểm");
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const visible = STUDENTS.filter(student => matches(query, student));
  const later = "Chưa có dữ liệu cho trang tiếp theo. TODO BE: phân trang API.";
  const detail = "TODO BE: mở chi tiết khi có API.";

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

  function resetFilters() {
    setQuery("");
    setMajor("Tất cả ngành");
    setStatus("Tất cả trạng thái CLO");
    setScore("Tất cả mức điểm");
  }

  return (
    <div className="dbcas-admin-home" style={{ backgroundImage: `linear-gradient(rgba(7,11,20,.8), rgba(7,11,20,.8)), url(${background})` }}>
      <svg className="svg-definitions" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <defs>
          <symbol id={`${ID}-plus`} viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" /></symbol>
          <symbol id={`${ID}-home`} viewBox="0 0 24 24"><path d="m3 10 9-7 9 7v10H3zM9 20v-7h6v7" /></symbol>
          <symbol id={`${ID}-users`} viewBox="0 0 24 24"><circle cx="9" cy="7" r="3" /><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5.65" /></symbol>
          <symbol id={`${ID}-cap`} viewBox="0 0 24 24"><path d="m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v7" /></symbol>
          <symbol id={`${ID}-document`} viewBox="0 0 24 24"><path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6" /></symbol>
          <symbol id={`${ID}-robot`} viewBox="0 0 24 24"><rect x="4" y="7" width="16" height="13" rx="3" /><path d="M12 3v4M2 11v5M22 11v5M9 16h6" /><circle cx="8.5" cy="12" r=".5" /><circle cx="15.5" cy="12" r=".5" /></symbol>
          <symbol id={`${ID}-chart`} viewBox="0 0 24 24"><path d="M4 3v17h17M8 16v-5M13 16V7M18 16V4" /></symbol>
          <symbol id={`${ID}-settings`} viewBox="0 0 24 24"><path d="m9 3-1 3-3 1v4l-2 1 2 1v4l3 1 1 3h6l1-3 3-1v-4l2-1-2-1V7l-3-1-1-3z" /><circle cx="12" cy="12" r="3" /></symbol>
          <symbol id={`${ID}-logout`} viewBox="0 0 24 24"><path d="M10 4H4v16h6M9 12h12M17 8l4 4-4 4" /></symbol>
          <symbol id={`${ID}-search`} viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></symbol>
          <symbol id={`${ID}-help`} viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 2-2.5 3.5M12 16h.01" /></symbol>
          <symbol id={`${ID}-bell`} viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></symbol>
          <symbol id={`${ID}-chevron`} viewBox="0 0 24 24"><path d="m8 5 7 7-7 7" /></symbol>
          <symbol id={`${ID}-calendar`} viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M7 3v4M17 3v4M3 11h18" /></symbol>
          <symbol id={`${ID}-medal`} viewBox="0 0 24 24"><circle cx="12" cy="8" r="5" /><path d="m8 12-1 9 5-3 5 3-1-9" /></symbol>
        </defs>
      </svg>

      <aside className="sidebar">
        <div className="sidebar-content">
          <div className="sidebar-brand">
            <img src={logo} alt="Logo DBCAS" draggable="false" />
          </div>
          <Link className="btn-new" to="/TN_Admin">
            <Icon name="plus" />
            <span>Tạo bài kiểm tra</span>
          </Link>
          <nav className="sidebar-nav" aria-label="Menu quản trị">
            <Link className="nav-link" to="/Home_Admin">
              <Icon name="home" />
              <span>Trang chủ</span>
            </Link>
            <Link className="nav-link active" to="/Danh_gia_nang_luc_Admin" aria-current="page">
              <Icon name="users" />
              <span>Đánh giá năng lực</span>
              <span className="nav-dot" />
            </Link>
            <Link className="nav-link" to="/CLO_Ky_nang_Admin">
              <Icon name="cap" />
              <span>CLO &amp; Kỹ năng</span>
            </Link>
            <Link className="nav-link" to="/Quan_ly_bai_kiem_tra_Admin">
              <Icon name="document" />
              <span>Quản lý bài kiểm tra</span>
            </Link>
            <Link className="nav-link" to="/Danh_gia_AI_Admin">
              <Icon name="robot" />
              <span>Đánh giá bằng AI</span>
            </Link>
            <a className="nav-link" href="#" onClick={event => { event.preventDefault(); setNotice("Trang này chưa được kết nối. Thêm route khi hoàn thành giao diện."); }}>
              <Icon name="chart" />
              <span>Báo cáo</span>
            </a>
            <Link className="nav-link" to="/Cai_dat_Admin">
              <Icon name="settings" />
              <span>Cài đặt</span>
            </Link>
          </nav>
        </div>
        <div className="sidebar-bottom">
          <button className="btn-logout" type="button" onClick={handleLogout} disabled={loggingOut}>
            <Icon name="logout" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      <header className="topbar">
        <div className="breadcrumb">
          <span>DBCAS Admin</span>
          <Icon name="chevron" />
          <strong>Đánh giá năng lực</strong>
        </div>
        <div className="topbar-actions">
          <label className="search top-search">
            <Icon name="search" />
            <input type="search" placeholder="Tìm kiếm sinh viên, rubric, bài thi..." aria-label="Tìm kiếm hệ thống" value={query} onChange={event => setQuery(event.target.value)} />
          </label>
          <button className="icon-button" type="button" aria-label="Trợ giúp" onClick={() => setNotice("TODO BE: mở trợ giúp.")}>
            <Icon name="help" />
          </button>
          <button className="icon-button notification" type="button" aria-label="Thông báo" onClick={() => setNotice("Chưa có thông báo mới. TODO BE: tải thông báo.")}>
            <Icon name="bell" />
            <span className="notification-dot" />
          </button>
          <Link className="profile" to="/Cai_dat_Admin">
            <span className="profile-avatar">AD</span>
            <span className="profile-text">
              <strong>Admin System</strong>
              <small>admin@dbcas.edu.vn</small>
            </span>
          </Link>
        </div>
      </header>

      <main className="main">
        <section className="page-banner card">
          <div>
            <h1>Đánh giá năng lực sinh viên</h1>
            <p>Hệ thống theo dõi chuẩn đầu ra môn Cơ sở dữ liệu (DBCAS). Đánh giá 3 Chuẩn đầu ra (CLO 1, CLO 2, CLO 3) và phân tích ma trận kỹ năng, đo lường Skill Gap.</p>
          </div>
          <label className="year-filter">
            <Icon name="calendar" />
            <select aria-label="Năm học" value={year} onChange={event => setYear(event.target.value)}>
              <option>Khoá 2024 - 2025</option>
              <option>Khoá 2025 - 2026</option>
            </select>
          </label>
        </section>

        <section className="kpi-row" aria-label="Chỉ số năng lực">
          <article className="stat-card card">
            <div className="stat-heading">
              <span>Năng lực trung bình</span>
              <span className="stat-icon cyan"><Icon name="medal" /></span>
            </div>
            <div className="stat-value">
              <strong>78.4%</strong>
              <span className="growth">+4.2%</span>
            </div>
            <p>so với kỳ trước (7.84/10)</p>
          </article>
          <article className="stat-card card">
            <div className="stat-heading">
              <span>Sinh viên đạt chuẩn</span>
              <span className="stat-icon green"><Icon name="users" /></span>
            </div>
            <div className="stat-value">
              <strong>2,412</strong>
              <span className="stat-unit">SV</span>
            </div>
            <p>84.8% tổng sinh viên</p>
          </article>
          <article className="stat-card card">
            <div className="stat-heading">
              <span>Sinh viên chưa đạt</span>
              <span className="stat-icon amber"><Icon name="users" /></span>
            </div>
            <div className="stat-value">
              <strong>433</strong>
              <span className="stat-unit">SV</span>
            </div>
            <p>15.2% cần bồi dưỡng thêm</p>
          </article>
        </section>

        <div className="insight-row">
          <section className="card" aria-labelledby="radar-title">
            <div className="card-head">
              <div>
                <h2 id="radar-title">Biểu đồ radar 3 trụ cột chuẩn đầu ra</h2>
                <p>So sánh năng lực thực tế cohort với chuẩn kỳ vọng theo 3 chuẩn đầu ra CSDL.</p>
              </div>
            </div>
            <div className="radar-stage">
              <p className="axis-pill axis-cyan">
                <span className="axis-dot" />
                CLO 1: SQL Querying
                <strong>85.2%</strong>
              </p>
              <svg viewBox="0 0 320 220" role="img" aria-label="Radar CLO 1 85.2%, CLO 2 86.8%, CLO 3 78.3%">
                <polygon points="160,30 246.6,180 73.4,180" fill="none" stroke="#1e293b" />
                <polygon points="160,54 229.3,168 90.7,168" fill="none" stroke="#334155" />
                <polygon points="160,78 212,156 108,156" fill="none" stroke="#1e293b" />
                <polygon points="160,102 194.6,144 125.4,144" fill="none" stroke="#1e293b" />
                <polygon points="160,50 232.6,170 87.4,170" fill="none" stroke="#64748b" strokeDasharray="4 3" />
                <polygon points="160,44.8 235.2,173.4 92.2,169.2" fill="#22d3ee33" stroke="#22d3ee" strokeWidth="2" />
                <line x1="160" y1="130" x2="160" y2="30" stroke="#334155" />
                <line x1="160" y1="130" x2="246.6" y2="180" stroke="#334155" />
                <line x1="160" y1="130" x2="73.4" y2="180" stroke="#334155" />
                <circle cx="160" cy="44.8" r="4" fill="#e2e8f0" stroke="#22d3ee" strokeWidth="2" />
                <circle cx="235.2" cy="173.4" r="4" fill="#e2e8f0" stroke="#22d3ee" strokeWidth="2" />
                <circle cx="92.2" cy="169.2" r="4" fill="#e2e8f0" stroke="#fb7185" strokeWidth="2" />
              </svg>
              <div className="axis-row">
                <p className="axis-pill axis-rose">
                  <span className="axis-dot" />
                  <span>CLO 3: Ràng buộc &amp; Thiết kế<strong>78.3% (Cần bồi dưỡng)</strong></span>
                </p>
                <p className="axis-pill axis-cyan">
                  <span className="axis-dot" />
                  <span>CLO 2: DML / DDL<strong>86.8% (Xuất sắc)</strong></span>
                </p>
              </div>
            </div>
            <div className="radar-callouts">
              <p className="callout">
                <span>Điểm mạnh nhất:</span>
                <strong className="callout-strong">CLO 2: Thao tác DML &amp; Views (86.8%)</strong>
              </p>
              <p className="callout">
                <span>Điểm trũng kiến thức (Skill Gap):</span>
                <strong className="callout-gap">CLO 3: Chuẩn hóa &amp; Ràng buộc (78.3%)</strong>
              </p>
            </div>
          </section>

          <section className="card" aria-labelledby="matrix-title">
            <div className="card-head">
              <div>
                <h2 id="matrix-title">Ma trận phân tích 3 chuẩn đầu ra</h2>
                <p>Mục tiêu: ≥ 80%</p>
              </div>
            </div>
            <div className="clo-stack">
              <article className="clo-card">
                <header>
                  <h3>Trục 1 · CLO 1 · SQL Querying (40%)</h3>
                  <span className="grade grade-green">Đạt chuẩn</span>
                </header>
                <p>Truy vấn dữ liệu</p>
                <strong className="text-cyan">85.2%</strong>
              </article>
              <article className="clo-card">
                <header>
                  <h3>Trục 2 · CLO 2 · DML / DDL (30%)</h3>
                  <span className="grade grade-cyan">Xuất sắc</span>
                </header>
                <p>Thao tác và định nghĩa dữ liệu.</p>
                <strong className="text-cyan">86.8%</strong>
              </article>
              <article className="clo-card">
                <header>
                  <h3>Trục 3 · CLO 3 · Ràng buộc &amp; Thiết kế (30%)</h3>
                  <span className="grade grade-rose">Cần bồi dưỡng</span>
                </header>
                <p>Ràng buộc và thiết kế CSDL.</p>
                <strong className="text-rose">78.3%</strong>
              </article>
              <Link className="btn-detail" to="/CLO_Ky_nang_Admin">Xem chi tiết ma trận ánh xạ CLO &amp; Kỹ năng</Link>
            </div>
          </section>
        </div>

        <section className="card results" aria-labelledby="learner-title">
          <div className="card-head">
            <div>
              <h2 id="learner-title">Danh sách sinh viên &amp; kết quả chi tiết</h2>
              <p>Hiển thị {visible.length} / {STUDENTS.length} sinh viên mẫu · Cập nhật: Học kỳ Spring 2025</p>
            </div>
          </div>
          <div className="card-head filter-row">
            <label className="search">
              <Icon name="search" />
              <input type="search" placeholder="Tìm theo tên sinh viên, mã SV (MSSV), email..." aria-label="Tìm sinh viên" value={query} onChange={event => setQuery(event.target.value)} />
            </label>
            <label className="year-filter">
              <select aria-label="Ngành" value={major} onChange={event => setMajor(event.target.value)}>
                <option>Tất cả ngành</option>
              </select>
            </label>
            <label className="year-filter">
              <select aria-label="Trạng thái CLO" value={status} onChange={event => setStatus(event.target.value)}>
                <option>Tất cả trạng thái CLO</option>
              </select>
            </label>
            <label className="year-filter">
              <select aria-label="Mức điểm" value={score} onChange={event => setScore(event.target.value)}>
                <option>Tất cả mức điểm</option>
              </select>
            </label>
            <button className="btn-detail" type="button" onClick={resetFilters}>Đặt lại</button>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Sinh viên</th>
                  <th scope="col">Mã SV &amp; ngành</th>
                  <th scope="col">Competency score</th>
                  <th scope="col">Điểm mạnh</th>
                  <th scope="col">Điểm yếu</th>
                  <th scope="col">Chuẩn CLO</th>
                  <th scope="col">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 && (
                  <tr>
                    <td colSpan={7}>Không có bản ghi mẫu phù hợp.</td>
                  </tr>
                )}
                {visible.map(student => (
                  <tr key={student.id}>
                    <td>
                      <div className="student">
                        <span className={`student-avatar ${student.avatar}`}>{student.initials}</span>
                        <div><strong>{student.name}</strong><small>{student.email}</small></div>
                      </div>
                    </td>
                    <td>{student.id}<small>{student.major}</small></td>
                    <td>
                      <div className="total-score"><b>{student.score}</b><span className={`grade ${student.gradeClass}`}>{student.grade}</span></div>
                      <small>{student.level}</small>
                    </td>
                    <td>{student.strong}</td>
                    <td>{student.weak}</td>
                    <td className={student.cloClass}>{student.clo}</td>
                    <td><button className="btn-detail" type="button" onClick={() => setNotice(detail)}>Xem chi tiết</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pager">
            <p>Hiển thị <strong>{visible.length}</strong> trên <strong>2,845</strong> sinh viên</p>
            <nav className="pagination" aria-label="Phân trang">
              <button className="page-button" type="button" onClick={() => setNotice(later)}>Trước</button>
              <button className="page-button active" type="button" aria-current="page">1</button>
              <button className="page-button" type="button" onClick={() => setNotice(later)}>2</button>
              <button className="page-button" type="button" onClick={() => setNotice(later)}>3</button>
              <span>…</span>
              <button className="page-button next" type="button" onClick={() => setNotice(later)}>Sau</button>
            </nav>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>DBCAS • Nền tảng đánh giá năng lực CSDL</span>
        <span>© 2026 Duy Tan University</span>
      </footer>
      {notice && <div className="admin-notice" role="status">{notice}<button type="button" aria-label="Đóng thông báo" onClick={() => setNotice("")}>×</button></div>}
    </div>
  );
}
