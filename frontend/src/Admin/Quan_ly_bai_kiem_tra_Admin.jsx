import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./Quan_ly_bai_kiem_tra_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";

const ID = "ql-i";
// TODO BE: danh sách bài kiểm tra dưới đây đang là dữ liệu mẫu.
const EXAMS = [
  { title: "Kiểm tra Cơ sở Dữ liệu Nâng cao - Đợt 2", when: "60 phút | 14:00 - 15:00", date: "Hôm nay • 28/03/2026" },
  { title: "Kiểm tra Giữa kỳ: Thiết kế quan hệ & Chuẩn hoá 3NF", when: "45 phút | 09:00 - 09:45", date: "26/03/2026" },
  { title: "Bài kiểm tra Thực hành Truy vấn JOIN & Subquery", when: "50 phút | 08:00 - 08:50", date: "29/03/2026" },
  { title: "Đánh giá Tối ưu hóa Chỉ mục Index & Stored Procedure", when: "90 phút | Chưa xếp giờ", date: "Dự kiến 05/04/2026" },
  { title: "Đề thi Đánh giá Năng lực Phân tích Lược đồ ERD & BCNF", when: "60 phút | 15:30 - 16:30", date: "30/03/2026" },
];

function Icon({ name }) {
  return <svg className="icon" aria-hidden="true"><use href={`#${ID}-${name}`} /></svg>;
}

export default function QuanLyBaiKiemTraAdmin({ onLogout }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const visible = EXAMS.filter(exam => exam.title.toLocaleLowerCase("vi").includes(query.trim().toLocaleLowerCase("vi")));
  const later = "TODO BE: mở bài kiểm tra khi có API.";

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
            <Link className="nav-link" to="/Home_Admin"><Icon name="home" /><span>Trang chủ</span></Link>
            <Link className="nav-link" to="/Danh_gia_nang_luc_Admin"><Icon name="users" /><span>Đánh giá năng lực</span></Link>
            <Link className="nav-link" to="/CLO_Ky_nang_Admin"><Icon name="cap" /><span>CLO &amp; Kỹ năng</span></Link>
            <Link className="nav-link active" to="/Quan_ly_bai_kiem_tra_Admin" aria-current="page">
              <Icon name="document" />
              <span>Quản lý bài kiểm tra</span>
              <span className="nav-dot" />
            </Link>
            <Link className="nav-link" to="/Danh_gia_AI_Admin"><Icon name="robot" /><span>Đánh giá bằng AI</span></Link>
            <a className="nav-link" href="#" onClick={event => { event.preventDefault(); setNotice("Trang này chưa được kết nối. Thêm route khi hoàn thành giao diện."); }}>
              <Icon name="chart" />
              <span>Báo cáo</span>
            </a>
            <Link className="nav-link" to="/Cai_dat_Admin"><Icon name="settings" /><span>Cài đặt</span></Link>
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
          <strong>Quản lý bài kiểm tra</strong>
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
        <section className="page-banner card" aria-labelledby="exam-title">
          <div>
            <h1 id="exam-title">Quản lý bài kiểm tra</h1>
            <p>Danh sách các bài kiểm tra đã tạo. Bạn có thể xem lại chi tiết và điều chỉnh thời gian thi.</p>
          </div>
          <Link className="btn-banner" to="/TN_Admin">Tạo bài kiểm tra mới</Link>
        </section>

        <section className="card results" aria-label="Danh sách bài kiểm tra">
          <div className="card-head">
            <label className="search result-search">
              <Icon name="search" />
              <input type="search" placeholder="Tìm kiếm bài kiểm tra đã tạo..." aria-label="Tìm bài kiểm tra" value={query} onChange={event => setQuery(event.target.value)} />
            </label>
            <p className="exam-count">Tổng cộng: <strong>{visible.length} bài kiểm tra</strong></p>
          </div>
          <div className="table-wrap exam-table">
            <table>
              <thead>
                <tr>
                  <th scope="col">Tên bài kiểm tra</th>
                  <th scope="col">Cấu trúc đề</th>
                  <th scope="col">Thời gian &amp; lịch thi</th>
                  <th scope="col">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 && (
                  <tr>
                    <td colSpan={4}>Không có bản ghi mẫu phù hợp.</td>
                  </tr>
                )}
                {visible.map(exam => (
                  <tr key={exam.title}>
                    <td>{exam.title}</td>
                    <td className="exam-structure">
                      <span>10 câu trắc nghiệm (4.0đ)</span>
                      <span className="part-sep"> • </span>
                      <span className="part-sql">3 SQL (3.0đ)</span>
                      <span className="part-sep"> • </span>
                      <span className="part-essay">1 tự luận (3.0đ)</span>
                    </td>
                    <td>
                      <span className="exam-when">{exam.when}</span>
                      <small>{exam.date}</small>
                    </td>
                    <td className="exam-actions">
                      <button className="btn-detail" type="button" onClick={() => setNotice(later)}>Xem lại</button>
                      <button className="btn-detail btn-time" type="button" onClick={() => setNotice("TODO BE: chỉnh thời gian khi có API.")}>Chỉnh thời gian</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
