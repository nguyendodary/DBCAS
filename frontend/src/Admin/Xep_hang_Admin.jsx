import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useMemo, useState, useEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./Xep_hang_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";
const DEMO_STUDENTS = Array.from({
  length: 100
}, (_, index) => {
  const surnames = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Võ", "Đặng", "Bùi"];
  const middles = ["Hoàng", "Minh", "Ngọc", "Thanh", "Gia", "Quang", "Thị", "Anh", "Đức", "Hải"];
  const names = ["Long", "Thư", "Dũng", "Anh", "Linh", "Huy", "Trang", "Nam", "Vy", "Khoa", "Hân", "Bảo", "Phúc", "Châu", "Tuấn"];
  const studentId = String(21200000001 + index);
  const mcqCorrect = 4 + index * 3 % 7;
  const sqlPassed = index * 5 % 4;
  const essayRaw = (40 + index * 13 % 61) / 10;
  return {
    id: studentId,
    studentId,
    name: [surnames[index % 10], middles[Math.floor(index / 10) % 10], names[Math.floor(index / 100) % 15]].join(" "),
    mcq: Number((mcqCorrect * 0.4).toFixed(2)),
    sql: sqlPassed,
    essay: Number((essayRaw * 0.3).toFixed(2))
  };
});
const NAV_ITEMS = [["home", "Trang chủ", "/Home_Admin"], ["users", "Đánh giá năng lực", "/Danh_gia_nang_luc_Admin"], ["cap", "CLO & Kỹ năng", "/CLO_Ky_nang_Admin"], ["document", "Quản lý bài kiểm tra", "/Quan_ly_bai_kiem_tra_Admin"], ["robot", "Đánh giá bằng AI", "/Danh_gia_AI_Admin"], ["chart", "Báo cáo", "/Bao_cao_Admin"], ["settings", "Cài đặt", "/Cai_dat_Admin"]];
function normalizeText(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d").toLowerCase().trim().replace(/\s+/g, " ");
}
function normalizeScore(value, maximum) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.round(Math.max(0, Math.min(maximum, number)) * 100) / 100 : 0;
}
function getGrade(score) {
  if (score >= 9) {
    return {
      label: "Xuất sắc",
      className: "excellent"
    };
  }
  if (score >= 8) {
    return {
      label: "Giỏi",
      className: "good"
    };
  }
  if (score >= 7) {
    return {
      label: "Khá",
      className: "fair"
    };
  }
  if (score >= 5) {
    return {
      label: "Đạt",
      className: "passed"
    };
  }
  return {
    label: "Cần ôn luyện",
    className: "weak"
  };
}
function initials(name) {
  return String(name).trim().split(/\s+/).slice(-2).map(word => word[0] || "").join("");
}
function Icon({
  name
}) {
  const paths = {
    home: "m3 10 9-7 9 7v10H3zM9 20v-7h6v7",
    users: "M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5.65",
    cap: "m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v7",
    document: "M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6",
    robot: "M4 7h16v13H4zM12 3v4M2 11v5M22 11v5M8 12h1M15 12h1M9 16h6",
    chart: "M4 3v17h17M8 16v-5M13 16V7M18 16V4",
    settings: "m9 3-1 3-3 1v4l-2 1 2 1v4l3 1 1 3h6l1-3 3-1v-4l2-1-2-1V7l-3-1-1-3z",
    plus: "M12 5v14M5 12h14",
    logout: "M10 4H4v16h6M9 12h12M17 8l4 4-4 4",
    back: "m12 19-7-7 7-7M5 12h14",
    search: "m16 16 5 5",
    chevron: "m8 5 7 7-7 7",
    medal: "m8 12-1 9 5-3 5 3-1-9",
    trophy: "M8 3h8v7a4 4 0 0 1-8 0ZM8 5H4v3a4 4 0 0 0 4 4M16 5h4v3a4 4 0 0 1-4 4M12 14v6M8 21h8"
  };
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name] || paths.document} />

      {adminRender(name === "users" && <circle cx="9" cy="7" r="3" />)}
      {adminRender(name === "search" && <circle cx="10.5" cy="10.5" r="6.5" />)}
      {adminRender(name === "settings" && <circle cx="12" cy="12" r="3" />)}
      {adminRender(name === "medal" && <circle cx="12" cy="8" r="5" />)}
    </svg>;
}
export default function XepHang({
  students: sourceStudents,
  onLogout
}) {
  useAdminLanguage();

  const location = useLocation();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const inputStudents = sourceStudents ?? location.state?.students ?? DEMO_STUDENTS;
  const rankedStudents = useMemo(() => {
    const data = Array.isArray(inputStudents) ? inputStudents : [];
    const normalized = data.map((student, index) => {
      const studentId = String(student.studentId ?? student.id ?? "");
      const mcq = normalizeScore(student.mcq, 4);
      const sql = normalizeScore(student.sql, 3);
      const essay = normalizeScore(student.essay, 3);
      return {
        ...student,
        studentId,
        name: String(student.name ?? ""),
        mcq,
        sql,
        essay,
        totalCents: Math.round(mcq * 100) + Math.round(sql * 100) + Math.round(essay * 100),
        rowKey: `${studentId}-${index}`
      };
    });
    normalized.sort((a, b) => b.totalCents - a.totalCents || a.studentId.localeCompare(b.studentId) || a.name.localeCompare(b.name, "vi"));
    let previousScore = null;
    let rank = 0;
    return normalized.map((student, index) => {
      if (student.totalCents !== previousScore) {
        rank = index + 1;
      }
      previousScore = student.totalCents;
      return {
        ...student,
        rank,
        total: student.totalCents / 100
      };
    });
  }, [inputStudents]);
  const topThreeKeys = useMemo(() => new Set(rankedStudents.slice(0, 3).map(student => student.rowKey)), [rankedStudents]);
  const filteredStudents = useMemo(() => {
    const search = normalizeText(query);
    return rankedStudents.filter(student => normalizeText(`${student.name ?? ""} ${student.studentId ?? student.id ?? ""}`).includes(search));
  }, [rankedStudents, query]);
  const pinnedIndexes = useMemo(() => {
    const indexes = new Map();
    let index = 0;
    filteredStudents.forEach(student => {
      if (topThreeKeys.has(student.rowKey)) {
        indexes.set(student.rowKey, index);
        index += 1;
      }
    });
    return indexes;
  }, [filteredStudents, topThreeKeys]);
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
  return <div className="dbcas-admin-home dbcas-ranking-page" style={{
    backgroundImage: `
          linear-gradient(
            rgba(7, 11, 20, .8),
            rgba(7, 11, 20, .8)
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
            {adminRender(NAV_ITEMS.map(([icon, label, path]) => <Link key={path} className="nav-link" to={path}>
                <Icon name={icon} />
                <span>{adminRender(label)}</span>
              </Link>))}
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

      <header className="topbar admin-unified-topbar"><NotificationMenu role="admin" className="icon-button" />
        <div className="breadcrumb">
          <Link to="/Home_Admin">DBCAS Admin</Link>
          <Icon name="chevron" />
          <strong>{adminText("Bảng xếp hạng")}</strong>
        </div>

        <div className="topbar-actions">
          <AdminAccountMenu onLogout={handleLogout} />
        </div>
      </header>

      <main className="main">
        <section className="card ranking-results" aria-labelledby="ranking-title">
          <div className="ranking-card-head">
            <h1 id="ranking-title">
              <Icon name="trophy" />{adminText(" Bảng xếp hạng ")}</h1>

            <Link className="ranking-back" to="/Home_Admin">
              <Icon name="back" />
              <span>{adminText("Quay lại")}</span>
            </Link>
          </div>

          <div className="ranking-toolbar">
            <label className="ranking-search">
              <Icon name="search" />

              <input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder={adminText("Tìm tên sinh viên hoặc MSSV...")} aria-label={adminText("Tìm tên sinh viên hoặc MSSV")} />
            </label>

            <span className="ranking-found" role="status">
              {adminRender(filteredStudents.length)}{adminText(" sinh viên ")}</span>
          </div>

          <div key={query} className="ranking-table-wrap" tabIndex={0} role="region" aria-label={adminText("Bảng xếp hạng sinh viên có thể cuộn")}>
            <table className="ranking-table">
              <colgroup>
                <col className="ranking-col-rank" />
                <col className="ranking-col-student" />
                <col className="ranking-col-score" />
                <col className="ranking-col-score" />
                <col className="ranking-col-score" />
                <col className="ranking-col-total" />
              </colgroup>

              <thead>
                <tr>
                  <th scope="col">{adminText("HẠNG")}</th>
                  <th scope="col">{adminText("SINH VIÊN")}</th>

                  <th scope="col">{adminText(" TRẮC NGHIỆM ")}<small>{adminText("Tối đa 4 điểm")}</small>
                  </th>

                  <th scope="col">
                    SQL
                    <small>{adminText("Tối đa 3 điểm")}</small>
                  </th>

                  <th scope="col">{adminText(" TỰ LUẬN ")}<small>{adminText("Tối đa 3 điểm")}</small>
                  </th>

                  <th scope="col">{adminText(" TỔNG ĐIỂM ")}<small>{adminText("Thang điểm 10")}</small>
                  </th>
                </tr>
              </thead>

              <tbody>
                {adminRender(filteredStudents.map(student => {
                const grade = getGrade(student.total);
                const pinnedIndex = pinnedIndexes.get(student.rowKey);
                const isPinned = pinnedIndex !== undefined;
                return <tr key={student.rowKey} className={isPinned ? "ranking-pinned-row" : ""} style={isPinned ? {
                  "--pinned-index": pinnedIndex,
                  "--pinned-z": 5 - pinnedIndex
                } : undefined}>
                      <td>
                        <span className={`ranking-position ${student.rank <= 3 ? `rank-${student.rank}` : ""}`} aria-label={`Hạng ${student.rank}`}>
                          {adminRender(student.rank <= 3 && <Icon name="medal" />)}

                          {adminRender(student.rank)}
                        </span>
                      </td>

                      <td>
                        <div className="ranking-student">
                          <span className="ranking-avatar">
                            {adminRender(initials(student.name))}
                          </span>

                          <div className="ranking-student-info">
                            <strong title={student.name || "Chưa có tên"}>
                              {adminRender(student.name || "Chưa có tên")}
                            </strong>

                            <small>{adminRender(student.studentId)}</small>
                          </div>
                        </div>
                      </td>

                      <td>{adminRender(student.mcq.toFixed(2))}</td>
                      <td>{adminRender(student.sql.toFixed(2))}</td>
                      <td>{adminRender(student.essay.toFixed(2))}</td>

                      <td>
                        <div className="ranking-total">
                          <strong>
                            {adminRender(student.total.toFixed(2))}
                          </strong>

                          <span className={`ranking-grade ${grade.className}`}>
                            {adminRender(grade.label)}
                          </span>
                        </div>
                      </td>
                    </tr>;
              }))}

                {adminRender(filteredStudents.length === 0 && <tr>
                    <td colSpan={6} className="ranking-empty">
                      {adminRender(query.trim() ? "Không tìm thấy sinh viên phù hợp." : "Chưa có dữ liệu sinh viên.")}
                    </td>
                  </tr>)}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>{adminText("DBCAS • Nền tảng đánh giá năng lực CSDL")}</span>
        <span>© 2026 Duy Tan University</span>
      </footer>

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