import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";

// TODO BE: các số liệu, radar và nhật ký dưới đây đang là dữ liệu mẫu.
export default function HomeAdmin({ onLogout, onViewDetail, onExport, onYearChange }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [year, setYear] = useState("2024 - 2025");
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const matches = text => text.toLocaleLowerCase("vi").includes(query.trim().toLocaleLowerCase("vi"));
  const visibleCount = ["Nguyễn Hoàng Long 21020412", "Trần Minh Thư 21020389", "Lê Quang Dũng 21020511", "Phạm Thị Mai Anh 21020294"].filter(matches).length;
  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      // TODO BE: onLogout thu hồi phiên và xóa trạng thái xác thực.
      if (onLogout) await onLogout();
      navigate("/Dang_nhap");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Không thể đăng xuất.");
    } finally { setLoggingOut(false); }
  }
  return (
    <div className="dbcas-admin-home" style={{ backgroundImage: `linear-gradient(rgba(7,11,20,.8), rgba(7,11,20,.8)), url(${background})` }}>

    {/* Icon SVG dùng chung */}
    <svg className="svg-definitions" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <defs>
      <symbol id="admin-i-plus" viewBox="0 0 24 24">
        <path d="M12 5v14M5 12h14"/>
      </symbol>
      <symbol id="admin-i-home" viewBox="0 0 24 24">
        <path d="m3 10 9-7 9 7v10H3zM9 20v-7h6v7"/>
      </symbol>
      <symbol id="admin-i-users" viewBox="0 0 24 24">
        <circle cx="9" cy="7" r="3"/>
        <path d="M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5.65"/>
      </symbol>
      <symbol id="admin-i-cap" viewBox="0 0 24 24">
        <path d="m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v7"/>
      </symbol>
      <symbol id="admin-i-document" viewBox="0 0 24 24">
        <path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6"/>
      </symbol>
      <symbol id="admin-i-robot" viewBox="0 0 24 24">
        <rect x="4" y="7" width="16" height="13" rx="3"/>
        <path d="M12 3v4M2 11v5M22 11v5M9 16h6"/>
        <circle cx="8.5" cy="12" r=".5"/>
        <circle cx="15.5" cy="12" r=".5"/>
      </symbol>
      <symbol id="admin-i-chart" viewBox="0 0 24 24">
        <path d="M4 3v17h17M8 16v-5M13 16V7M18 16V4"/>
      </symbol>
      <symbol id="admin-i-settings" viewBox="0 0 24 24">
        <path d="m9 3-1 3-3 1v4l-2 1 2 1v4l3 1 1 3h6l1-3 3-1v-4l2-1-2-1V7l-3-1-1-3z"/>
        <circle cx="12" cy="12" r="3"/>
      </symbol>
      <symbol id="admin-i-logout" viewBox="0 0 24 24">
        <path d="M10 4H4v16h6M9 12h12M17 8l4 4-4 4"/>
      </symbol>
      <symbol id="admin-i-search" viewBox="0 0 24 24">
        <circle cx="10.5" cy="10.5" r="6.5"/>
        <path d="m16 16 5 5"/>
      </symbol>
      <symbol id="admin-i-help" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="9"/>
        <path d="M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 2-2.5 3.5M12 16h.01"/>
      </symbol>
      <symbol id="admin-i-bell" viewBox="0 0 24 24">
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>
      </symbol>
      <symbol id="admin-i-calendar" viewBox="0 0 24 24">
        <rect x="3" y="5" width="18" height="16" rx="2"/>
        <path d="M7 3v4M17 3v4M3 11h18"/>
      </symbol>
      <symbol id="admin-i-chevron" viewBox="0 0 24 24">
        <path d="m8 5 7 7-7 7"/>
      </symbol>
      <symbol id="admin-i-medal" viewBox="0 0 24 24">
        <circle cx="12" cy="8" r="5"/>
        <path d="m8 12-1 9 5-3 5 3-1-9"/>
      </symbol>
      <symbol id="admin-i-sliders" viewBox="0 0 24 24">
        <path d="M4 7h3M11 7h9M4 17h9M17 17h3"/>
        <circle cx="9" cy="7" r="2"/>
        <circle cx="15" cy="17" r="2"/>
      </symbol>
      <symbol id="admin-i-radar" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="9"/>
        <circle cx="12" cy="12" r="5"/>
        <circle cx="12" cy="12" r="1"/>
        <path d="m12 12 7-7"/>
      </symbol>
      <symbol id="admin-i-shield" viewBox="0 0 24 24">
        <path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>
      </symbol>
      <symbol id="admin-i-terminal" viewBox="0 0 24 24">
        <rect x="3" y="4" width="18" height="16" rx="2"/>
        <path d="m7 9 3 3-3 3M13 15h4"/>
      </symbol>
      <symbol id="admin-i-alert" viewBox="0 0 24 24">
        <path d="m12 3 10 18H2zM12 9v5M12 17h.01"/>
      </symbol>
      <symbol id="admin-i-cpu" viewBox="0 0 24 24">
        <rect x="6" y="6" width="12" height="12" rx="2"/>
        <rect x="9" y="9" width="6" height="6" rx="1"/>
        <path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>
      </symbol>
      <symbol id="admin-i-sync" viewBox="0 0 24 24">
        <path d="M20 7a8 8 0 0 0-14-2L3 8M3 3v5h5M4 17a8 8 0 0 0 14 2l3-3M16 16h5v5"/>
      </symbol>
      <symbol id="admin-i-server" viewBox="0 0 24 24">
        <rect x="3" y="3" width="18" height="7" rx="2"/>
        <rect x="3" y="14" width="18" height="7" rx="2"/>
        <path d="M7 6.5h.01M7 17.5h.01M11 6.5h6M11 17.5h6"/>
      </symbol>
      <symbol id="admin-i-download" viewBox="0 0 24 24">
        <path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>
      </symbol>
      <symbol id="admin-i-activity" viewBox="0 0 24 24">
        <path d="M3 12h4l3-8 4 16 3-8h4"/>
      </symbol>
    </defs>
  </svg>
    {/* Sidebar */}
    <aside className="sidebar">
        <div className="sidebar-content">
            <div className="sidebar-brand">
                <img src={logo} alt="Logo DBCAS" draggable="false" />
            </div>
            <Link className="btn-new" to="/TN_Admin">
                <svg className="icon" aria-hidden="true">
        <use href="#admin-i-plus"></use>
    </svg>
                <span>Tạo bài kiểm tra</span>
            </Link>
            <nav className="sidebar-nav" aria-label="Menu quản trị">
                <Link className="nav-link active" to="/Home_Admin" aria-current="page">
                    <svg className="icon" aria-hidden="true"><use href="#admin-i-home"/></svg>
                    <span>Trang chủ</span>
                    <span className="nav-dot"></span>
                </Link>
                <a className="nav-link" href="#" onClick={event => { event.preventDefault(); setNotice("Trang này chưa được kết nối. Thêm route khi hoàn thành giao diện."); }}>
                    <svg className="icon" aria-hidden="true"><use href="#admin-i-users"/></svg>
                    <span>Đánh giá năng lực</span>
                </a>
                <a className="nav-link" href="#" onClick={event => { event.preventDefault(); setNotice("Trang này chưa được kết nối. Thêm route khi hoàn thành giao diện."); }}>
                    <svg className="icon" aria-hidden="true"><use href="#admin-i-cap"/></svg>
                    <span>CLO &amp; Kỹ năng</span>
                </a>
                <a className="nav-link" href="#" onClick={event => { event.preventDefault(); setNotice("Trang này chưa được kết nối. Thêm route khi hoàn thành giao diện."); }}>
                    <svg className="icon" aria-hidden="true"><use href="#admin-i-document"/></svg>
                    <span>Quản lý bài kiểm tra</span>
                </a>
                <a className="nav-link" href="#" onClick={event => { event.preventDefault(); setNotice("Trang này chưa được kết nối. Thêm route khi hoàn thành giao diện."); }}>
                    <svg className="icon" aria-hidden="true"><use href="#admin-i-robot"/></svg>
                    <span>Đánh giá bằng AI</span>
                </a>
                <a className="nav-link" href="#" onClick={event => { event.preventDefault(); setNotice("Trang này chưa được kết nối. Thêm route khi hoàn thành giao diện."); }}>
                    <svg className="icon" aria-hidden="true"><use href="#admin-i-chart"/></svg>
                    <span>Báo cáo</span>
                </a>
                <Link className="nav-link" to="/Cai_dat_Admin">
                    <svg className="icon" aria-hidden="true"><use href="#admin-i-settings"/></svg>
                    <span>Cài đặt</span>
                </Link>
            </nav>
        </div>
        <div className="sidebar-bottom">
            <button className="btn-logout" type="button" onClick={handleLogout} disabled={loggingOut}>
                <svg className="icon" aria-hidden="true">
      <use href="#admin-i-logout"/>
    </svg>
                <span>Đăng xuất</span>
            </button>
        </div>
    </aside>
    {/* Thanh phía trên */}
    <header className="topbar">
        <div className="breadcrumb">
            <span>DBCAS Admin</span>
            <svg className="icon" aria-hidden="true"><use href="#admin-i-chevron"/></svg>
            <strong>Trang chủ</strong>
        </div>
        <div className="topbar-actions">
            <label className="search top-search">
        <svg className="icon" aria-hidden="true"><use href="#admin-i-search"/></svg>
        <input type="search" placeholder="Tìm kiếm..."
               aria-label="Tìm kiếm hệ thống" value={query} onChange={event => setQuery(event.target.value)} />
      </label>
            <button className="icon-button" type="button" aria-label="Trợ giúp" onClick={() => setNotice("Liên hệ nhóm hỗ trợ DBCAS.")}>
        <svg className="icon" aria-hidden="true"><use href="#admin-i-help"/></svg>
      </button>
            <button className="icon-button notification" type="button" aria-label="Thông báo" onClick={() => setNotice("Chưa có thông báo mới trong bản giao diện mẫu.")}>
        <svg className="icon" aria-hidden="true"><use href="#admin-i-bell"/></svg>
        <span className="notification-dot"></span>
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
        {/* Tổng quan */}
        <section className="dashboard-overview" aria-label="Tổng quan hệ thống">
            <div className="hero card">
                <div className="hero-bar">
                    <label className="year-filter">
            <svg className="icon" aria-hidden="true"><use href="#admin-i-calendar"/></svg>
            <select aria-label="Năm học" value={year} onChange={event => { setYear(event.target.value); onYearChange?.(event.target.value); }}>
              <option>2024 - 2025</option>
              <option>2025 - 2026</option>
              <option>2026 - 2027</option>
            </select>
          </label>
                    <span className="live-update">
            <span className="live-dot"></span> Cập nhật 16:45:20
                    </span>
                </div>
                <h1>
                    Xin chào Admin!
                    <span>Hệ thống đang hoạt động tối ưu.</span>
                </h1>
                <p>
                    Theo dõi năng lực của <strong>2,845 sinh viên</strong> thông qua 10 câu hỏi trắc nghiệm, 3 bài thực hành SQL Sandbox và 1 bài tự luận thiết kế CSDL được hỗ trợ đánh giá bằng AI.
                </p>
            </div>
            <div className="stats">
                <article className="stat-card card">
                    <div className="stat-heading">
                        <span>Tổng sinh viên</span>
                        <span className="stat-icon cyan">
              <svg className="icon" aria-hidden="true"><use href="#admin-i-users"/></svg>
            </span>
                    </div>
                    <div className="stat-value">
                        <strong>2,845</strong>
                        <span className="growth">+12.4%</span>
                    </div>
                    <p>So với học kỳ trước</p>
                    <div className="progress">
                        <span style={{ width: "88%" }}></span>
                    </div>
                </article>
                <article className="stat-card card">
                    <div className="stat-heading">
                        <span>Bài kiểm tra</span>
                        <span className="stat-icon green">
              <svg className="icon" aria-hidden="true"><use href="#admin-i-document"/></svg>
            </span>
                    </div>
                    <div className="stat-value">
                        <strong>18</strong>
                        <span className="stat-unit">đợt thi</span>
                    </div>
                    <p><span className="live-dot"></span> 3 đợt đang diễn ra</p>
                    <div className="progress green-progress">
                        <span style={{ width: "65%" }}></span>
                    </div>
                </article>
                <article className="stat-card stat-wide card">
                    <span className="score-icon">
            <svg className="icon" aria-hidden="true"><use href="#admin-i-medal"/></svg>
          </span>
                    <div className="score-content">
                        <p>Điểm năng lực trung bình</p>
                        <div className="stat-value">
                            <strong>7.84</strong>
                            <span className="stat-unit">/ 10</span>
                        </div>
                    </div>
                    <div className="clo-tag">
                        <span>ĐẠT CLO</span>
                        <strong>92.4%</strong>
                        <small>Mục tiêu ≥ 85%</small>
                    </div>
                </article>
            </div>
        </section>
        {/* Ma trận và Nhật ký */}
        <section className="analytics-grid">
            <section className="card competency-card">
                <div className="analytics-heading">
                    <span className="heading-icon">
            <svg className="icon" aria-hidden="true"><use href="#admin-i-chart"/></svg>
          </span>
                    <div className="heading-content">
                        <h2>Ma Trận &amp; Đánh Giá Năng Lực CSDL</h2>
                        <p>
                            Phân tích Concept Breakdown, biểu đồ Radar và khoảng cách năng lực
                        </p>
                    </div>
                    <span className="cohort-badge">
            <span className="live-dot"></span> 2,845 Học viên
                    </span>
                </div>
                <div className="competency-panels">
                    {/* Concept Breakdown */}
                    <div className="analytics-panel concept-panel">
                        <div className="panel-heading">
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-sliders"/></svg>
                            <h3>CONCEPT BREAKDOWN</h3>
                            <span className="benchmark">Benchmark: ĐHQGHN</span>
                        </div>
                        <article className="skill-box">
                            <div className="skill-heading">
                                <div className="skill-name">
                                    <h4>Truy vấn SQL</h4>
                                    <span className="skill-status cyan-status">Đạt chuẩn</span>
                                </div>
                                <div className="skill-rate">
                                    <span>Tỷ lệ đạt</span>
                                    <b className="text-cyan">85.2%</b>
                                </div>
                            </div>
                            <div className="progress">
                                <span style={{ width: "85.2%" }}></span>
                            </div>
                            <p>Trọng tâm: JOIN, Gom nhóm &amp; Truy vấn nâng cao</p>
                        </article>
                        <article className="skill-box">
                            <div className="skill-heading">
                                <div className="skill-name">
                                    <h4>DML/DDL</h4>
                                    <span className="skill-status green-status">Xuất sắc</span>
                                </div>
                                <div className="skill-rate">
                                    <span>Tỷ lệ đạt</span>
                                    <b className="text-green">86.8%</b>
                                </div>
                            </div>
                            <div className="progress green-progress">
                                <span style={{ width: "86.8%" }}></span>
                            </div>
                            <p>Trọng tâm: Cú pháp DML/DDL, Schema &amp; Views</p>
                        </article>
                        <article className="skill-box">
                            <div className="skill-heading">
                                <div className="skill-name">
                                    <h4>Thiết kế &amp; Ràng buộc</h4>
                                    <span className="skill-status amber-status">Cận chuẩn</span>
                                </div>
                                <div className="skill-rate">
                                    <span>Tỷ lệ đạt</span>
                                    <b className="text-amber">78.3%</b>
                                </div>
                            </div>
                            <div className="progress amber-progress">
                                <span style={{ width: "78.3%" }}></span>
                            </div>
                            <p>Trọng tâm: Ràng buộc toàn vẹn, Chuẩn hóa dữ liệu</p>
                        </article>
                    </div>
                    {/* Radar */}
                    <div className="analytics-panel radar-panel">
                        <div className="panel-heading">
                            <svg className="icon text-purple" aria-hidden="true">
                <use href="#admin-i-radar"/>
              </svg>
                            <h3>COMPETENCY RADAR</h3>
                        </div>
                        <div className="radar-legend">
                            <span><i className="legend-line"></i>Thực tế</span>
                            <span><i className="legend-line target"></i>Mục tiêu 80%</span>
                        </div>
                        <svg className="radar-chart" viewBox="0 0 300 245" role="img" aria-label="Năng lực SQL 85.2%, DML DDL 86.8%, Thiết kế 78.3%">
              <g className="radar-grid">
                <polygon points="150,45 245,210 55,210"/>
                <polygon points="150,67 226,199 74,199"/>
                <polygon points="150,89 207,188 93,188"/>
                <polygon points="150,111 188,177 112,177"/>
                <polygon points="150,133 169,166 131,166"/>
                <path d="M150 155V45M150 155L245 210M150 155L55 210"/>
              </g>
              <polygon className="radar-target"
                       points="150,67 226,199 74,199"/>
              <polygon className="radar-data"
                       points="150,61.3 232.5,202.7 75.6,198.1"/>
              <circle cx="150" cy="61.3" r="3" fill="#22d3ee"/>
              <circle cx="232.5" cy="202.7" r="3" fill="#34d399"/>
              <circle cx="75.6" cy="198.1" r="3" fill="#fbbf24"/>
              <g className="radar-labels">
                <text x="150" y="25" textAnchor="middle">Truy vấn SQL</text>
                <text x="20" y="232">Thiết kế &amp; Ràng buộc</text>
                <text x="280" y="232" textAnchor="end">DML/DDL</text>
              </g>
            </svg>
                        <div className="radar-verdict">
                            <div>
                                <svg className="icon text-green" aria-hidden="true">
                  <use href="#admin-i-shield"/>
                </svg>
                                <span>Đạt chuẩn đầu ra<br /><b>2/3 trụ cột</b></span>
                            </div>
                            <p>Điểm đồng thuận:<br /><strong>83.4%</strong></p>
                        </div>
                    </div>
                </div>
                {/* Learner Analytics */}
                <div className="learner-panel">
                    <div className="learner-heading">
                        <h3>
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-users"/></svg> LEARNER ANALYTICS
                        </h3>
                        <span className="cohort-badge">2,845 Học viên</span>
                    </div>
                    <div className="learner-kpis">
                        <div className="learner-kpi">
                            <p>Tỉ lệ đạt chuẩn</p>
                            <div className="kpi-value">
                                <b className="text-green">91.8%</b>
                                <small className="text-green">+3.2% ↑</small>
                            </div>
                        </div>
                        <div className="learner-kpi">
                            <p>Điểm Trung Bình Khóa</p>
                            <div className="kpi-value stacked">
                                <b>7.84 / 10</b>
                                <small className="text-cyan">Trung vị 8.0</small>
                            </div>
                        </div>
                        <div className="learner-kpi">
                            <p>Thủ Khoa Đợt Thi</p>
                            <div className="kpi-value">
                                <b className="text-purple">9.90 (A+)</b>
                                <small>100% Pass</small>
                            </div>
                        </div>
                        <div className="learner-kpi">
                            <p>Tỉ Lệ Giỏi / Xuất sắc</p>
                            <div className="kpi-value">
                                <b className="text-purple">48.2%</b>
                                <small>1,371 SV</small>
                            </div>
                        </div>
                    </div>
                    <div className="learner-bottom">
                        <div className="top-learner">
                            <svg className="icon" aria-hidden="true"><use href="#admin-i-medal"/></svg>
                            <p>
                                <strong>Top 1: Nguyễn Hoàng Long</strong>
                                <small>(MSSV: 21020412 • Kỹ thuật phần mềm)</small>
                            </p>
                        </div>
                        <button className="ranking-button" type="button" onClick={() => setNotice("Bảng xếp hạng chưa được kết nối.")}>
              Xem bảng xếp hạng đầy đủ &amp; phân tích phổ điểm →
            </button>
                    </div>
                </div>
            </section>
            {/* Nhật ký hệ thống */}
            <aside className="card activity-card">
                <div className="activity-heading">
                    <svg className="icon text-cyan" aria-hidden="true">
            <use href="#admin-i-activity"/>
          </svg>
                    <h2>Nhật Ký &amp; Cảnh Báo Trực Tiếp</h2>
                    <span className="live-dot"></span>
                </div>
                <ul className="activity-list">
                    <li>
                        <span className="activity-icon green">
              <svg className="icon" aria-hidden="true"><use href="#admin-i-terminal"/></svg>
            </span>
                        <div className="activity-content">
                            <p>
                                <b>SV 21020412</b> hoàn thành 3 bài thực hành SQL, đạt toàn bộ test case.
                            </p>
                            <time>1 phút trước</time>
                        </div>
                    </li>
                    <li>
                        <span className="activity-icon cyan">
              <svg className="icon" aria-hidden="true"><use href="#admin-i-robot"/></svg>
            </span>
                        <div className="activity-content">
                            <p>AI đã đánh giá <b>18 bài tự luận</b> thiết kế Schema &amp; ERD.</p>
                            <time>5 phút trước</time>
                        </div>
                    </li>
                    <li className="activity-warning">
                        <span className="activity-icon amber">
              <svg className="icon" aria-hidden="true"><use href="#admin-i-alert"/></svg>
            </span>
                        <div className="activity-content">
                            <p>
                                Phát hiện <b>14 sinh viên</b> cần củng cố kiến thức Transaction &amp; Concurrency.
                            </p>
                            <time>18 phút trước</time>
                        </div>
                    </li>
                    <li>
                        <span className="activity-icon">
              <svg className="icon" aria-hidden="true"><use href="#admin-i-cpu"/></svg>
            </span>
                        <div className="activity-content">
                            <p><b>Docker Sandbox 04</b> đã giải phóng tài nguyên sau đợt thi.</p>
                            <time>25 phút trước</time>
                        </div>
                    </li>
                    <li>
                        <span className="activity-icon">
              <svg className="icon" aria-hidden="true"><use href="#admin-i-document"/></svg>
            </span>
                        <div className="activity-content">
                            <p>Bài tự luận của <b>SV 21020389</b> đã được chấm theo rubric AI.</p>
                            <time>31 phút trước</time>
                        </div>
                    </li>
                    <li>
                        <span className="activity-icon green">
              <svg className="icon" aria-hidden="true"><use href="#admin-i-sync"/></svg>
            </span>
                        <div className="activity-content">
                            <p>Đã đồng bộ kết quả của <b>2,845 sinh viên</b>.</p>
                            <time>42 phút trước</time>
                        </div>
                    </li>
                    <li>
                        <span className="activity-icon">
              <svg className="icon" aria-hidden="true"><use href="#admin-i-server"/></svg>
            </span>
                        <div className="activity-content">
                            <p>
                                Khởi tạo <b>45 containers MySQL/PostgreSQL</b> phục vụ ca thi chiều.
                            </p>
                            <time>50 phút trước</time>
                        </div>
                    </li>
                </ul>
                <button className="activity-more" type="button" onClick={() => setNotice("Nhật ký hiện là dữ liệu mẫu. TODO BE: tải nhật ký hệ thống.")}>
          <span>Xem toàn bộ nhật ký hệ thống</span>
          <svg className="icon" aria-hidden="true"><use href="#admin-i-chevron"/></svg>
        </button>
            </aside>
        </section>
        {/* Bảng kết quả */}
        <section className="card results">
            <div className="card-head">
                <div>
                    <h2>Kết quả đánh giá sinh viên gần đây</h2>
                    <p>Trọng số: Trắc nghiệm 40% • SQL 30% • Tự luận 30%</p>
                </div>
                <div className="result-tools">
                    <label className="search result-search">
            <svg className="icon" aria-hidden="true"><use href="#admin-i-search"/></svg>
            <input type="search" placeholder="Tìm tên hoặc MSSV..."
                   aria-label="Tìm sinh viên" value={query} onChange={event => setQuery(event.target.value)} />
          </label>
                    <button className="btn-export" type="button" onClick={() => onExport ? onExport() : setNotice("TODO BE: kết nối chức năng xuất báo cáo.")}>
            <svg className="icon" aria-hidden="true"><use href="#admin-i-download"/></svg>
            <span>Xuất báo cáo</span>
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
                            <th scope="col">SINH VIÊN</th>
                            <th scope="col">BÀI KIỂM TRA</th>
                            <th scope="col">TRẮC NGHIỆM</th>
                            <th scope="col">SQL SANDBOX</th>
                            <th scope="col">TỰ LUẬN AI</th>
                            <th scope="col">TỔNG ĐIỂM</th>
                            <th scope="col">THAO TÁC</th>
                        </tr>
                    </thead>
                    <tbody>
                        {matches("Nguyễn Hoàng Long 21020412") && (
<tr>
                            <td>
                                <div className="student">
                                    <span className="student-avatar av-blue">NL</span>
                                    <div>
                                        <strong>Nguyễn Hoàng Long</strong>
                                        <small>21020412 • Kỹ thuật phần mềm</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span>KT CSDL Nâng Cao</span>
                                <small>10:41 • 28/02/2026</small>
                            </td>
                            <td>10/10<small>4.00 điểm</small></td>
                            <td className="text-green">3/3 Pass<small>3.00 điểm</small></td>
                            <td className="text-cyan">8.5/10<small>2.55 điểm</small></td>
                            <td>
                                <div className="total-score">
                                    <b>9.55</b><span className="grade grade-green">A+</span>
                                </div>
                            </td>
                            <td><button className="btn-detail" type="button" onClick={() => onViewDetail ? onViewDetail("21020412") : setNotice("Chi tiết sinh viên 21020412 chưa được kết nối.")}>Xem chi tiết</button></td>
                        </tr>
)}
                        {matches("Trần Minh Thư 21020389") && (
<tr>
                            <td>
                                <div className="student">
                                    <span className="student-avatar av-green">TT</span>
                                    <div>
                                        <strong>Trần Minh Thư</strong>
                                        <small>21020389 • Hệ thống thông tin</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span>KT CSDL Cơ Bản</span>
                                <small>10:35 • 28/02/2026</small>
                            </td>
                            <td>9/10<small>3.60 điểm</small></td>
                            <td className="text-green">3/3 Pass<small>3.00 điểm</small></td>
                            <td className="text-cyan">8.0/10<small>2.40 điểm</small></td>
                            <td>
                                <div className="total-score">
                                    <b>9.00</b><span className="grade grade-cyan">A</span>
                                </div>
                            </td>
                            <td><button className="btn-detail" type="button" onClick={() => onViewDetail ? onViewDetail("21020389") : setNotice("Chi tiết sinh viên 21020389 chưa được kết nối.")}>Xem chi tiết</button></td>
                        </tr>
)}
                        {matches("Lê Quang Dũng 21020511") && (
<tr>
                            <td>
                                <div className="student">
                                    <span className="student-avatar av-purple">LD</span>
                                    <div>
                                        <strong>Lê Quang Dũng</strong>
                                        <small>21020511 • Khoa học máy tính</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span>ACID &amp; CSDL Phân Tán</span>
                                <small>08:50 • 28/02/2026</small>
                            </td>
                            <td>8/10<small>3.20 điểm</small></td>
                            <td className="text-amber">2/3 Pass<small>2.00 điểm</small></td>
                            <td className="text-cyan">7.5/10<small>2.25 điểm</small></td>
                            <td>
                                <div className="total-score">
                                    <b>7.45</b><span className="grade grade-slate">B+</span>
                                </div>
                            </td>
                            <td><button className="btn-detail" type="button" onClick={() => onViewDetail ? onViewDetail("21020511") : setNotice("Chi tiết sinh viên 21020511 chưa được kết nối.")}>Xem chi tiết</button></td>
                        </tr>
)}
                        {matches("Phạm Thị Mai Anh 21020294") && (
<tr>
                            <td>
                                <div className="student">
                                    <span className="student-avatar av-orange">MA</span>
                                    <div>
                                        <strong>Phạm Thị Mai Anh</strong>
                                        <small>21020294 • An toàn thông tin</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span>SQL &amp; Indexing Lab 02</span>
                                <small>10:10 • 28/02/2026</small>
                            </td>
                            <td>6/10<small>2.40 điểm</small></td>
                            <td className="text-rose">1/3 Pass<small>1.00 điểm</small></td>
                            <td className="text-cyan">5.0/10<small>1.50 điểm</small></td>
                            <td>
                                <div className="total-score">
                                    <b>4.90</b>
                                    <span className="grade grade-rose">Cần ôn luyện</span>
                                </div>
                            </td>
                            <td><button className="btn-detail" type="button" onClick={() => onViewDetail ? onViewDetail("21020294") : setNotice("Chi tiết sinh viên 21020294 chưa được kết nối.")}>Xem chi tiết</button></td>
                        </tr>
)}
                    {visibleCount === 0 && <tr><td colSpan={7}>Không tìm thấy sinh viên phù hợp.</td></tr>}
</tbody>
                </table>
            </div>
            <div className="pager">
                <p>Hiển thị <strong>{visibleCount}</strong> kết quả trong <strong>4</strong> bản ghi mẫu</p>
                <nav className="pagination" aria-label="Phân trang">
                    <button className="page-button active" type="button" aria-current="page">1</button>
                    <button className="page-button" type="button" onClick={() => setNotice("Chưa có dữ liệu cho trang tiếp theo. TODO BE: phân trang API.")}>2</button>
                    <button className="page-button" type="button" onClick={() => setNotice("Chưa có dữ liệu cho trang tiếp theo. TODO BE: phân trang API.")}>3</button>
                    <span>…</span>
                    <button className="page-button next" type="button" onClick={() => setNotice("Chưa có dữ liệu cho trang tiếp theo. TODO BE: phân trang API.")}>
            Tiếp
            <svg className="icon" aria-hidden="true"><use href="#admin-i-chevron"/></svg>
          </button>
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
