import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import {
  DEMO_STUDENTS,
  DEMO_STUDENT_ID,
  Icon,
  normalize,
  currentStudentId,
  rankStudents,
} from "./Xem_danh_gia_Learner";
import "./Home_Learner.css";
import "./Xem_danh_gia_Learner.css";
import "./Xep_hang_Learner.css";

export default function XepHangLearner({ user, students }) {
  const location = useLocation();
  const [params] = useSearchParams();
  const accountUser = user ?? location.state?.user;
  const sourceStudents = students ?? location.state?.students ?? DEMO_STUDENTS;
  const ranked = useMemo(() => rankStudents(sourceStudents), [sourceStudents]);
  const myId = currentStudentId(accountUser, params.get("studentId") || DEMO_STUDENT_ID);
  const myStudent = ranked.find(student => student.id === myId);
  const learner = {
    ...accountUser,
    studentId: myId,
    name: accountUser?.name ?? myStudent?.name ?? "Nguyễn Hoàng Long",
    email: accountUser?.email ?? "long.nh20216049@sis.hust.edu.vn",
    initials: accountUser?.initials ?? "HL",
  };
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const [major, setMajor] = useState("");
  const [notice, setNotice] = useState("");
  const timer = useRef(null);
  const tableRef = useRef(null);
  useEffect(() => () => clearTimeout(timer.current), []);
  const filtered = useMemo(() => {
    const words = normalize(query).split(/\s+/).filter(Boolean);
    return ranked.filter(student => {
      const text = normalize(`${student.name} ${student.id}`);
      return words.every(word => text.includes(word)) && (!major || student.major === major);
    });
  }, [ranked, query, major]);
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const start = (currentPage - 1) * pageSize;
  const visible = filtered.slice(start, start + pageSize);
  function showNotification() {
    clearTimeout(timer.current);
    setNotice("Bạn chưa có thông báo mới.");
    timer.current = setTimeout(() => setNotice(""), 3000);
  }
  function changePage(value) {
    setPage(Math.max(1, Math.min(value, totalPages)));
    if (tableRef.current) tableRef.current.scrollTop = 0;
  }
  function goToMyRank() {
    const index = ranked.findIndex(student => student.id === myId);
    if (index < 0) return;
    setQuery("");
    setMajor("");
    setPage(Math.floor(index / pageSize) + 1);
    if (tableRef.current) tableRef.current.scrollTop = 0;
  }
  const pageNumbers = [...new Set([1, currentPage - 1, currentPage, currentPage + 1, totalPages].filter(n => n > 0 && n <= totalPages))].sort((a, b) => a - b);
  return (
    <div className="dbcas-learner-home dbcas-learner-evaluation learner-ranking-page">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand"><span className="brand-icon"><Icon name="database" /></span><div><strong>Datamaster</strong><span>ASSESSMENT ENGINE</span></div></div>
          <nav className="main-nav" aria-label="Menu người học">
            <Link className="nav-link" to="/Home_Learner"><Icon name="home" /><span>Trang chủ</span></Link>
            <Link className="nav-link" to="/Bai_kiem_tra_Learner"><Icon name="file" /><span>Bài kiểm tra</span></Link>
            <Link className="nav-link active" to="/Xem_danh_gia_Learner" aria-current="location"><Icon name="chart" /><span>Xem đánh giá</span></Link>
            <Link className="nav-link" to="/Cai_dat_Learner"><Icon name="settings" /><span>Cài đặt</span></Link>
          </nav>
          <div className="toolbar-actions">
            <button type="button" className="notification-button" aria-label="Thông báo" onClick={showNotification}><Icon name="bell" /><span className="notification-dot" /></button>
            <Link className="profile" to="/Cai_dat_Learner"><span className="avatar">{learner.initials}</span><span className="profile-info"><strong>{learner.name}</strong><span>{learner.email}</span></span></Link>
          </div>
        </div>
      </header>
      <section className="lr-hero">
        <div className="container lr-hero-inner">
          <nav className="lr-breadcrumb" aria-label="Đường dẫn">
            <Link to="/Home_Learner">Trang chủ</Link><span>/</span>
            <Link to="/Xem_danh_gia_Learner" state={{ user: learner, students: ranked }}>Xem đánh giá</Link><span>/</span><span>Bảng xếp hạng</span>
          </nav>
          <div className="lr-hero-heading">
            <div><h1>Bảng Xếp Hạng Toàn Ngành</h1><p>Tổng hợp điểm trung bình và kết quả học tập của sinh viên</p></div>
            <div className="lr-stats">
              <div><span>Tổng sinh viên</span><strong>{ranked.length.toLocaleString("en-US")}</strong></div>
              <div><span>Điểm trung bình</span><strong>{ranked.length ? (ranked.reduce((sum, student) => sum + (Number(student.score) || 0), 0) / ranked.length).toFixed(2) : "—"}</strong></div>
              <div><span>Vị trí của bạn</span><button type="button" onClick={goToMyRank} disabled={!myStudent}>{myStudent ? `#${myStudent.rank}` : "—"}</button></div>
            </div>
          </div>
        </div>
      </section>
      <main className="container lr-main">
        <section className="de-white-panel de-ranking lr-ranking">
          <div className="lr-toolbar">
            <label className="de-ranking-search"><Icon name="search" /><input type="search" aria-label="Tìm sinh viên theo tên hoặc MSSV" value={query} onChange={event => { setQuery(event.target.value); setPage(1); }} placeholder="Nhập tên sinh viên hoặc MSSV..." /></label>
            <label className="lr-major-filter"><Icon name="users" /><select aria-label="Lọc ngành đào tạo" value={major} onChange={event => { setMajor(event.target.value); setPage(1); }}><option value="">Tất cả ngành</option>{[...new Set(ranked.map(student => student.major).filter(Boolean))].map(name => <option key={name} value={name}>{name}</option>)}</select></label>
          </div>
          <div className="de-table-scroll lr-table-window" ref={tableRef} tabIndex="0" aria-label="Bảng xếp hạng đầy đủ">
            <table className="de-ranking-table">
              <thead><tr><th>Hạng</th><th>Họ và tên &amp; MSSV</th><th>Ngành đào tạo</th><th className="lr-score">Điểm TB</th><th className="lr-status">Trạng thái</th></tr></thead>
              <tbody>{visible.map(student => {
                const score = Number(student.score);
                const status = score >= 8.5 ? "Xuất sắc" : score >= 6 ? "Đạt chuẩn" : "Chưa đạt";
                return <tr key={student.id} className={student.id === myId ? "de-my-row" : ""}>
                  <td><span className={`de-rank ${student.rank <= 3 ? `medal-${student.rank}` : ""}`}>#{String(student.rank).padStart(2, "0")}</span></td>
                  <td><strong className="de-student-name">{student.name}</strong><span className="de-student-id">{student.id}</span></td>
                  <td>{student.major}</td><td className="lr-score">{Number.isFinite(score) ? score.toFixed(1) : "—"}</td>
                  <td className="lr-status"><span className={`lr-status-badge ${score < 6 ? "needs-work" : ""}`}>{Number.isFinite(score) ? status : "Chưa có điểm"}</span></td>
                </tr>;
              })}{!visible.length && <tr><td colSpan="5" className="de-empty">Không tìm thấy sinh viên phù hợp.</td></tr>}</tbody>
            </table>
          </div>
          <div className="de-pagination">
            <span>Hiển thị {filtered.length ? start + 1 : 0}–{Math.min(start + pageSize, filtered.length)} / {filtered.length.toLocaleString("en-US")} sinh viên</span>
            <nav className="lr-page-buttons" aria-label="Phân trang bảng xếp hạng">
              <button type="button" disabled={currentPage === 1} onClick={() => changePage(1)}>Đầu</button>
              <button type="button" disabled={currentPage === 1} onClick={() => changePage(currentPage - 1)}>‹ Trước</button>
              {pageNumbers.map((number, i) => <span key={number} className="lr-page-item">{i > 0 && number - pageNumbers[i - 1] > 1 && <span className="lr-gap">…</span>}<button type="button" className={number === currentPage ? "active" : ""} aria-current={number === currentPage ? "page" : undefined} onClick={() => changePage(number)}>{number}</button></span>)}
              <button type="button" disabled={currentPage === totalPages} onClick={() => changePage(currentPage + 1)}>Sau ›</button>
              <button type="button" disabled={currentPage === totalPages} onClick={() => changePage(totalPages)}>Cuối</button>
            </nav>
          </div>
        </section>
      </main>
      <footer className="footer"><div className="container footer-inner"><p><strong>DBCAS</strong><span>•</span>Nền tảng tự động Đánh giá Năng lực CSDL</p><nav aria-label="Liên kết hỗ trợ"><Link to="/Quy_che">Quy chế khảo thí</Link><Link to="/Tai_lieu#chuan-hoa">Chuẩn hóa 3NF</Link><Link to="/Tai_lieu#sql">Tài liệu SQL</Link><Link to="/Ho_tro">Hỗ trợ</Link></nav></div></footer>
      {notice && <div className="de-notice" role="status">{notice}<button type="button" aria-label="Đóng thông báo" onClick={() => setNotice("")}>×</button></div>}
    </div>
  );
}
