import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./Danh_gia_AI_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";

const ID = "ai-i";
// TODO BE: hàng đợi chấm AI và bảng điểm dưới đây đang là dữ liệu mẫu.
const SUBMISSIONS = [
  { name: "Nguyễn Văn An", meta: "SV20230142 • K27-DB01", initials: "NA", avatar: "av-blue", topic: "Thiết kế CSDL Phân tán", rubric: "1.0 · 1.0 · 0.8", score: "2.8", scoreClass: "", match: "Khớp 100%", matchClass: "", trust: "99.1%", status: "Đã duyệt AI", statusClass: "grade-green", action: "Xem" },
  { name: "Trần Thị Mai", meta: "SV20230891 • K27-DB01", initials: "TM", avatar: "av-green", topic: "Thiết kế CSDL Phân tán", rubric: "1.0 · 1.0 · 1.0", score: "3.0", scoreClass: "", match: "Khớp 100%", matchClass: "", trust: "98.4%", status: "Đã duyệt AI", statusClass: "grade-green", action: "Xem" },
  { name: "Lê Hoàng Nam", meta: "SV20230419 • K27-DB02", initials: "HN", avatar: "av-orange", topic: "Thiết kế CSDL Phân tán", rubric: "1.0 · 0.5 · 0.3", score: "1.8", scoreClass: "text-rose", match: "Chênh 0.85đ", matchClass: "text-rose", trust: "82.0%", status: "Chờ xem lại", statusClass: "grade-rose", action: "Đối chiếu ngay" },
  { name: "Phạm Quốc Bảo", meta: "SV20230233 • K27-DB01", initials: "QB", avatar: "av-purple", topic: "Thiết kế CSDL Phân tán", rubric: "1.0 · 0.9 · 0.7", score: "2.6", scoreClass: "", match: "Chênh 0.1đ", matchClass: "", trust: "97.5%", status: "Đã duyệt AI", statusClass: "grade-green", action: "Xem" },
];

function Icon({ name }) {
  return <svg className="icon" aria-hidden="true"><use href={`#${ID}-${name}`} /></svg>;
}

export default function DanhGiaAiAdmin({ onLogout }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [year, setYear] = useState("Năm học 2025 - 2026");
  const [aiStatus, setAiStatus] = useState("Lọc trạng thái AI: Tất cả (2,845)");
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const visible = SUBMISSIONS.filter(item => `${item.name} ${item.meta} ${item.topic}`.toLocaleLowerCase("vi").includes(query.trim().toLocaleLowerCase("vi")));
  const later = "Chưa có dữ liệu cho trang tiếp theo. TODO BE: phân trang API.";
  const detail = "TODO BE: mở bài chấm khi có API.";

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
          <symbol id={`${ID}-calendar`} viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M7 3v4M17 3v4M3 11h18" /></symbol>
          <symbol id={`${ID}-download`} viewBox="0 0 24 24"><path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5" /></symbol>
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
            <Link className="nav-link" to="/Quan_ly_bai_kiem_tra_Admin"><Icon name="document" /><span>Quản lý bài kiểm tra</span></Link>
            <Link className="nav-link active" to="/Danh_gia_AI_Admin" aria-current="page">
              <Icon name="robot" />
              <span>Đánh giá bằng AI</span>
              <span className="nav-dot" />
            </Link>
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
          <strong>Đánh giá bằng AI</strong>
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
            <h1>Đánh giá bằng AI</h1>
            <p>Hệ thống tự động chấm điểm và đánh giá chi tiết bài thi Tự luận Kiến trúc CSDL qua mô hình LLM API đối chiếu Barem Rubric (thang điểm: 3.0đ). Phân tích ngữ nghĩa CoT, rà soát từ khóa kỹ thuật và phát hiện sai lệch barem.</p>
          </div>
          <label className="year-filter">
            <Icon name="calendar" />
            <select aria-label="Năm học" value={year} onChange={event => setYear(event.target.value)}>
              <option>Năm học 2025 - 2026</option>
              <option>Năm học 2024 - 2025</option>
            </select>
          </label>
        </section>

        <section className="kpi-row" aria-label="Chỉ số chấm AI">
          <article className="stat-card card">
            <div className="stat-heading"><span>Bài thi tự luận đã chấm AI</span></div>
            <div className="stat-value"><strong>2,845</strong></div>
            <p>2,845 bài làm</p>
          </article>
          <article className="stat-card card">
            <div className="stat-heading"><span>Thời gian AI chấm trung bình</span></div>
            <div className="stat-value"><strong>1.4s</strong><span className="stat-unit">/ bài làm</span></div>
          </article>
          <article className="stat-card card">
            <div className="stat-heading"><span>Độ tương đồng GV &amp; AI</span></div>
            <div className="stat-value"><strong>94.2%</strong><span className="growth">+1.8%</span></div>
          </article>
          <article className="stat-card card">
            <div className="stat-heading"><span>Cảnh báo chênh lệch (&gt;0.75đ)</span></div>
            <div className="stat-value"><strong className="text-rose">28</strong><span className="stat-unit">bài thi</span></div>
          </article>
        </section>

        <section className="card" aria-labelledby="review-title">
          <div className="queue-bar">
            <p className="queue-badge">Hàng đợi duyệt: 28 bài cần thẩm định</p>
            <p className="queue-pager">
              <button className="page-button" type="button" aria-label="Bài trước trong hàng đợi" onClick={() => setNotice(detail)}>‹</button>
              <span>1/28</span>
              <button className="page-button" type="button" aria-label="Bài sau trong hàng đợi" onClick={() => setNotice(detail)}>›</button>
            </p>
          </div>
          <div className="card-head">
            <div className="student">
              <span className="student-avatar av-blue">NA</span>
              <div>
                <h2 id="review-title">Nguyễn Văn An</h2>
                <p>Chưa duyệt • Cần thẩm định · Nộp lúc 10:42 • Đề: Thiết kế CSDL Phân tán</p>
              </div>
            </div>
            <div className="stat-value">
              <strong>2.8</strong>
              <span className="stat-unit">/ 3.0</span>
            </div>
          </div>
          <h3 className="essay-label">Bài làm tự luận của sinh viên</h3>
          <div className="essay">
            <div className="essay-head">
              <p>Bài tự luận của sinh viên (Nguyễn Văn An - SV20230142)</p>
              <span>Độ dài: 486 từ • 1 câu tự luận</span>
            </div>
            <p>Để giải quyết bài toán thiết kế cơ sở dữ liệu phân tán chịu tải lớn cho hệ thống hàng chục triệu bản ghi, em xin trình bày phương án tổng thể như sau:</p>
            <p>Đầu tiên, về phần lưu trữ và truy vấn trên từng node: bảng dữ liệu lớn sẽ được cấu hình <code>Clustered Index</code> trên khóa chính <code>UserID</code> để tối ưu thứ tự ghi và đọc vật lý. Với các nghiệp vụ lọc thường xuyên theo tenant và mốc thời gian, em bổ sung <code>Composite B-Tree Index (TenantID, CreatedAt DESC)</code> giúp hệ quản trị thực hiện Index Seek, giảm Full Table Scan và tiết kiệm I/O đĩa.</p>
            <p>Tiếp theo, hệ thống áp dụng <code>Horizontal Sharding</code> dựa trên <code>TenantID</code>. Với Data Skew, em kết hợp Consistent Hashing với Virtual Nodes, đồng thời dùng <code>Salting Key (TenantID_Salt)</code> để tránh Hotspot Shard.</p>
            <p>Cuối cùng, em ưu tiên <code>Saga Pattern</code> thay vì Two-Phase Commit (2PC), vận hành theo Choreography bất đồng bộ, hướng tới Eventual Consistency và High Availability.</p>
          </div>
          <div className="rubric-row">
            <article className="rubric-card">
              <header><strong>1. B-Tree &amp; Index</strong><span className="text-cyan">1.0 / 1.0</span></header>
              <span className="score-bar"><i style={{ width: "100%" }} /></span>
              <small>Khớp từ khóa chuẩn</small>
            </article>
            <article className="rubric-card">
              <header><strong>2. I/O &amp; Sharding</strong><span className="text-cyan">1.0 / 1.0</span></header>
              <span className="score-bar"><i style={{ width: "100%" }} /></span>
              <small>Salting Key chính xác</small>
            </article>
            <article className="rubric-card">
              <header><strong>3. ACID &amp; Lock</strong><span className="text-amber">0.8 / 1.0</span></header>
              <span className="score-bar score-partial"><i style={{ width: "80%" }} /></span>
              <small>Trừ 0.2đ thiếu bù trừ Saga</small>
            </article>
          </div>
          <div className="note">
            <p><strong>Nhận xét định tính AI</strong></p>
            <p><span className="text-cyan">Điểm mạnh:</span> Tư duy phân tán tốt, kết hợp chuẩn xác Consistent Hashing và Salting Shard Key.</p>
            <p><span className="text-amber">Cần cải thiện:</span> Cần bổ sung cơ chế Compensating Transaction (Giao dịch bù) cho Saga Choreography.</p>
          </div>
          <div className="review-actions">
            <div>
              <button className="btn-detail" type="button" onClick={() => setNotice(detail)}>← Bài trước</button>
              <button className="btn-detail" type="button" onClick={() => setNotice(detail)}>Bài tiếp theo →</button>
            </div>
            <div>
              <button className="btn-detail" type="button" onClick={() => setNotice("TODO BE: sửa điểm khi có API.")}>Sửa điểm</button>
              <button className="btn-detail btn-approve" type="button" onClick={() => setNotice("TODO BE: duyệt điểm AI khi có API.")}>Duyệt điểm AI (2.8đ) &amp; Chuyển tiếp</button>
            </div>
          </div>
        </section>

        <section className="card results" aria-labelledby="ai-table-title">
          <div className="card-head">
            <div>
              <h2 id="ai-table-title">Danh sách bài thi tự luận đã qua AI thẩm định &amp; chấm rubric</h2>
              <p>Đánh giá chuyên sâu 3 tiêu chí: Kiến trúc B-Tree (1.0đ) • Tối ưu I/O &amp; Sharding (1.0đ) • ACID &amp; Khóa phân tán (1.0đ)</p>
            </div>
          </div>
          <div className="card-head filter-row">
            <label className="year-filter">
              <select aria-label="Lọc trạng thái AI" value={aiStatus} onChange={event => setAiStatus(event.target.value)}>
                <option>Lọc trạng thái AI: Tất cả (2,845)</option>
                <option>Đã duyệt AI</option>
                <option>Chờ xem lại</option>
              </select>
            </label>
            <button className="btn-export" type="button" onClick={() => setNotice("TODO BE: kết nối chức năng xuất báo cáo.")}>
              <Icon name="download" />
              <span>Xuất Excel bảng điểm</span>
            </button>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Sinh viên / MSSV</th>
                  <th scope="col">Đề bài tự luận</th>
                  <th scope="col">Tiêu chí rubric</th>
                  <th scope="col">Điểm AI (3.0)</th>
                  <th scope="col">Độ tương đồng GV &amp; AI</th>
                  <th scope="col">Độ tin cậy</th>
                  <th scope="col">Trạng thái AI</th>
                  <th scope="col">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 && (
                  <tr>
                    <td colSpan={8}>Không có bản ghi mẫu phù hợp.</td>
                  </tr>
                )}
                {visible.map(item => (
                  <tr key={item.meta}>
                    <td>
                      <div className="student">
                        <span className={`student-avatar ${item.avatar}`}>{item.initials}</span>
                        <div><strong>{item.name}</strong><small>{item.meta}</small></div>
                      </div>
                    </td>
                    <td>{item.topic}</td>
                    <td>{item.rubric}</td>
                    <td><b className={item.scoreClass}>{item.score}</b></td>
                    <td className={item.matchClass}>{item.match}</td>
                    <td>{item.trust}</td>
                    <td><span className={`grade ${item.statusClass}`}>{item.status}</span></td>
                    <td><button className="btn-detail" type="button" onClick={() => setNotice(detail)}>{item.action}</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pager">
            <p>Hiển thị <strong>1 - {visible.length}</strong> trong tổng số <strong>2,845</strong> bài thi đã thẩm định</p>
            <nav className="pagination" aria-label="Phân trang">
              <button className="page-button" type="button" onClick={() => setNotice(later)}>Trước</button>
              <button className="page-button active" type="button" aria-current="page">1</button>
              <button className="page-button" type="button" onClick={() => setNotice(later)}>2</button>
              <span>…</span>
              <button className="page-button" type="button" onClick={() => setNotice(later)}>712</button>
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
