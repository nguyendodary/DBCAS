import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./CLO_Ky_nang_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";

const ID = "clo-i";
// TODO BE: CLO, khái niệm và danh sách sinh viên dưới đây đang là dữ liệu mẫu.
const GROUPS = [
  {
    title: "Thành phần 1: Core retrieval",
    items: [
      { name: "SELECT", hint: "Truy vấn cột" },
      { name: "WHERE", hint: "Điều kiện dòng" },
      { name: "ORDER BY", hint: "Sắp xếp ASC/DESC" },
      { name: "DISTINCT", hint: "Khử trùng lặp" },
    ],
  },
  {
    title: "Thành phần 2: Joins & Aggregation",
    items: [
      { name: "JOIN", hint: "INNER / LEFT / RIGHT" },
      { name: "GROUP BY", hint: "Gom nhóm bản ghi" },
      { name: "HAVING", hint: "Lọc sau gom nhóm" },
      { name: "Aggregate", hint: "COUNT/SUM/AVG" },
    ],
  },
  {
    title: "Thành phần 3: Advanced retrieval",
    items: [
      { name: "Subqueries", hint: "Truy vấn lồng" },
      { name: "CTE", hint: "WITH RECURSIVE" },
      { name: "Window Fn", hint: "OVER / PARTITION" },
      { name: "Set Ops", hint: "UNION / EXCEPT" },
    ],
  },
];
const INITIAL_CHECKED = [true, true, true, true, true, true, true, false, true, true, false, false];
const STUDENTS = [
  { name: "Nguyễn Văn An", email: "an.nv23@dtu.edu.vn", id: "SV20230142", major: "Kỹ thuật phần mềm", initials: "NA", avatar: "av-blue", clos: ["pass", "pass", "weak"] },
  { name: "Trần Thị Mai", email: "mai.tt23@dtu.edu.vn", id: "SV20230288", major: "Hệ thống thông tin", initials: "TM", avatar: "av-green", clos: ["pass", "pass", "pass"] },
  { name: "Lê Hoàng Nam", email: "nam.lh23@dtu.edu.vn", id: "SV20230509", major: "Khoa học máy tính", initials: "HN", avatar: "av-purple", clos: ["weak", "pass", "weak"] },
  { name: "Phạm Thị Hương", email: "huong.pt23@dtu.edu.vn", id: "SV20230617", major: "Kỹ thuật phần mềm", initials: "TH", avatar: "av-orange", clos: ["pass", "pass", "pass"] },
  { name: "Hoàng Đức Huy", email: "huy.hd23@dtu.edu.vn", id: "SV20230733", major: "An toàn thông tin", initials: "DH", avatar: "av-blue", clos: ["weak", "weak", "weak"] },
  { name: "Vũ Minh Quân", email: "quan.vm23@dtu.edu.vn", id: "SV20230891", major: "Hệ thống thông tin", initials: "MQ", avatar: "av-green", clos: ["pass", "weak", "pass"] },
];

function Icon({ name }) {
  return <svg className="icon" aria-hidden="true"><use href={`#${ID}-${name}`} /></svg>;
}

export default function CloKyNangAdmin({ onLogout }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [major, setMajor] = useState("Tất cả ngành");
  const [status, setStatus] = useState("Tất cả trạng thái");
  const [checked, setChecked] = useState(INITIAL_CHECKED);
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const visible = STUDENTS.filter(student => `${student.name} ${student.id} ${student.email}`.toLocaleLowerCase("vi").includes(query.trim().toLocaleLowerCase("vi")));
  const selected = checked.filter(Boolean).length;
  const later = "Chưa có dữ liệu cho trang tiếp theo. TODO BE: phân trang API.";

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

  function setAll(value) {
    setChecked(checked.map(() => value));
  }

  let cursor = 0;

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
            <Link className="nav-link active" to="/CLO_Ky_nang_Admin" aria-current="page">
              <Icon name="cap" />
              <span>CLO &amp; Kỹ năng</span>
              <span className="nav-dot" />
            </Link>
            <Link className="nav-link" to="/Quan_ly_bai_kiem_tra_Admin"><Icon name="document" /><span>Quản lý bài kiểm tra</span></Link>
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
          <strong>CLO &amp; Kỹ năng</strong>
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
            <h1>Quản lý Chuẩn đầu ra (CLO)</h1>
            <p>Thiết lập ma trận ánh xạ giữa Chuẩn đầu ra học phần với cây tri thức PostgreSQL để tự động chấm điểm và đánh giá năng lực.</p>
          </div>
        </section>

        <div className="split-row">
          <section className="card" aria-labelledby="clo-list-title">
            <div className="card-head clo-head">
              <div>
                <h2 id="clo-list-title">Danh sách CLO</h2>
                <p className="exam-note">Đề thi áp dụng: <strong>Kiểm tra CSDL Nâng cao - K27 CNTT (Đang hoạt động)</strong></p>
              </div>
              <span className="grade grade-cyan">3 CLO</span>
            </div>
            <div className="clo-list">
              <article className="clo-item">
                <div className="clo-meta"><strong>CLO 1</strong><span>Chiếm: 40%</span></div>
                <h3>Kỹ năng truy vấn dữ liệu (SQL Querying)</h3>
                <div className="chip-row">
                  {["SELECT", "WHERE", "ORDER BY", "JOIN", "GROUP BY", "HAVING", "DISTINCT", "Subqueries", "CTE", "Window Fns", "Aggregate"].map(chip => <span className="chip" key={chip}>{chip}</span>)}
                </div>
              </article>
              <article className="clo-item">
                <div className="clo-meta"><strong>CLO 2</strong><span>Chiếm: 30%</span></div>
                <h3>Thao tác &amp; Định nghĩa (DML &amp; DDL)</h3>
                <div className="chip-row">
                  {["DML", "DDL", "Kiểu dữ liệu", "View"].map(chip => <span className="chip" key={chip}>{chip}</span>)}
                </div>
              </article>
              <article className="clo-item is-selected">
                <div className="clo-meta"><strong>CLO 3</strong><span className="text-cyan">Đang chọn</span></div>
                <h3>Ràng buộc &amp; Thiết kế CSDL (Constraints &amp; Design)</h3>
                <div className="chip-row">
                  {["PK / FK / UNIQUE", "Mô hình ERD", "Chuẩn hóa 3NF", "Check/Index"].map(chip => <span className="chip" key={chip}>{chip}</span>)}
                </div>
                <p>Chiếm: 30%</p>
              </article>
            </div>
            <p className="coverage">Độ phủ chương trình: <strong>100%</strong> · Tổng: 3 CLO</p>
          </section>

          <section className="card" aria-labelledby="tree-title">
            <div className="card-head tree-head">
              <div>
                <h2 id="tree-title">Cây danh mục khái niệm PostgreSQL &amp; Ánh xạ</h2>
                <p>Ánh xạ: CLO 3 - Ràng buộc &amp; Thiết kế CSDL. Tích chọn khái niệm để gán vào ma trận chấm điểm.</p>
              </div>
              <span className="grade grade-slate">12 Khái niệm</span>
            </div>
            {GROUPS.map(group => {
              const start = cursor;
              cursor += group.items.length;
              const linked = checked.slice(start, cursor).filter(Boolean).length;
              return (
                <div className="concept-group" key={group.title}>
                  <h3>{group.title} <span>{linked}/{group.items.length} liên kết</span></h3>
                  {group.items.map((item, index) => {
                    const itemIndex = start + index;
                    return (
                      <label className="concept" key={item.name}>
                        <input
                          type="checkbox"
                          checked={checked[itemIndex]}
                          onChange={event => setChecked(checked.map((value, i) => i === itemIndex ? event.target.checked : value))}
                        />
                        <span>{item.name}<small>{item.hint}</small></span>
                      </label>
                    );
                  })}
                </div>
              );
            })}
            <div className="map-bar">
              <p>Đã chọn: {selected} / {checked.length} khái niệm (CLO 3)</p>
              <div className="map-actions">
                <button className="btn-detail" type="button" onClick={() => setAll(true)}>Chọn tất cả</button>
                <button className="btn-detail" type="button" onClick={() => setAll(false)}>Hủy chọn</button>
                <button className="btn-detail btn-time" type="button" onClick={() => setNotice("TODO BE: lưu ánh xạ CLO.")}>Áp dụng ánh xạ CLO 3</button>
              </div>
            </div>
          </section>
        </div>

        <section className="card results" aria-labelledby="student-clo-title">
          <div className="card-head">
            <div>
              <h2 id="student-clo-title">Tra cứu Năng lực CLO theo Sinh viên</h2>
              <p>Theo dõi và đánh giá chi tiết mức độ đáp ứng chuẩn đầu ra của từng sinh viên theo bài thi và học phần.</p>
            </div>
          </div>
          <div className="card-head filter-row">
            <label className="search">
              <Icon name="search" />
              <input type="search" placeholder="Tìm theo Họ tên hoặc MSSV..." aria-label="Tìm sinh viên" value={query} onChange={event => setQuery(event.target.value)} />
            </label>
            <label className="year-filter">
              <select aria-label="Ngành" value={major} onChange={event => setMajor(event.target.value)}>
                <option>Tất cả ngành</option>
                <option>Kỹ thuật phần mềm</option>
                <option>Hệ thống thông tin</option>
                <option>Khoa học máy tính</option>
                <option>An toàn thông tin</option>
              </select>
            </label>
            <label className="year-filter">
              <select aria-label="Trạng thái" value={status} onChange={event => setStatus(event.target.value)}>
                <option>Tất cả trạng thái</option>
                <option>Đạt</option>
                <option>Yếu</option>
              </select>
            </label>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Sinh viên / email</th>
                  <th scope="col">Mã SV (MSSV)</th>
                  <th scope="col">Ngành đào tạo</th>
                  <th scope="col">Trạng thái năng lực CLO</th>
                  <th scope="col">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 && (
                  <tr>
                    <td colSpan={5}>Không có bản ghi mẫu phù hợp.</td>
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
                    <td>{student.id}</td>
                    <td>{student.major}</td>
                    <td>
                      <div className="clo-status">
                        {student.clos.map((state, index) => (
                          <span className={state === "pass" ? "status-pass" : "status-weak"} key={index}>
                            CLO {index + 1}: {state === "pass" ? "Đạt" : "Yếu"}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td><button className="btn-detail" type="button" onClick={() => setNotice("TODO BE: mở chi tiết khi có API.")}>Xem chi tiết</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pager">
            <p>Hiển thị <strong>{visible.length}</strong> / <strong>2,845</strong> sinh viên</p>
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
