import { useEffect, useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./Danh_gia_nang_luc_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";
const PAGE_SIZE = 10;
const MAJORS = ["Kỹ thuật Phần mềm", "Khoa học Máy tính", "Hệ thống Thông tin Quản lý", "An ninh Mạng", "Công nghệ Phần mềm"];
const YEARS = ["2024-2025", "2025-2026", "2026-2027"];
const SKILL_NAMES = ["Truy vấn SQL", "DML & DDL", "Thiết kế & Ràng buộc"];
const NAV_ITEMS = [["home", "Trang chủ", "/Home_Admin"], ["users", "Đánh giá năng lực", "/Danh_gia_nang_luc_Admin"], ["cap", "CLO & Kỹ năng", "/CLO_Ky_nang_Admin"], ["document", "Quản lý bài kiểm tra", "/Quan_ly_bai_kiem_tra_Admin"], ["robot", "Đánh giá bằng AI", "/Danh_gia_AI_Admin"], ["chart", "Báo cáo", "/Bao_cao_Admin"], ["settings", "Cài đặt", "/Cai_dat_Admin"]];
const DEMO_STUDENTS = Array.from({
  length: 100
}, (_, index) => {
  const surnames = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Võ", "Đặng", "Bùi"];
  const middles = ["Hoàng", "Minh", "Ngọc", "Thanh", "Gia", "Quang", "Thị", "Anh", "Đức", "Hải"];
  const names = ["Long", "Thư", "Dũng", "Anh", "Linh", "Huy", "Trang", "Nam", "Vy", "Khoa", "Hân", "Bảo", "Phúc", "Châu", "Tuấn"];
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
    major: MAJORS[index % MAJORS.length],
    year: "2026-2027",
    phone: "",
    completedTests: 50 + index % 31,
    mcq,
    sql,
    essay,
    score: Number((mcq + sql + essay).toFixed(2)),
    skills,
    clos,
    cloCount: clos.filter(Boolean).length,
    strong: SKILL_NAMES[skills.indexOf(Math.max(...skills))],
    weak: SKILL_NAMES[skills.indexOf(Math.min(...skills))]
  };
});
const DEMO_OVERVIEW = (() => {
  const count = DEMO_STUDENTS.length;
  const passed = DEMO_STUDENTS.filter(student => student.cloCount === 3).length;
  return {
    averagePercent: Number((DEMO_STUDENTS.reduce((sum, student) => sum + student.score, 0) / count * 10).toFixed(1)),
    passed,
    notPassed: count - passed,
    passedPercent: Number((passed / count * 100).toFixed(1)),
    notPassedPercent: Number(((count - passed) / count * 100).toFixed(1))
  };
})();
const CLO_DATA = SKILL_NAMES.map((title, index) => ({
  name: `CLO ${index + 1}`,
  title,
  weight: index === 0 ? "40%" : "30%",
  description: ["Kỹ năng truy vấn và khai thác dữ liệu.", "Thao tác và định nghĩa cấu trúc dữ liệu.", "Ràng buộc toàn vẹn và thiết kế cơ sở dữ liệu."][index],
  value: Number((DEMO_STUDENTS.filter(student => student.clos[index]).length / DEMO_STUDENTS.length * 100).toFixed(1))
}));
function normalizeText(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d").toLowerCase().trim();
}
function cloStatus(value) {
  if (value === null || value === undefined || value === "" || !Number.isInteger(Number(value)) || Number(value) < 0 || Number(value) > 3) {
    return {
      name: "Chưa có kết quả",
      color: "slate"
    };
  }
  const count = Number(value);
  if (count === 3) {
    return {
      name: "Đạt chuẩn (3/3 CLO)",
      color: "green"
    };
  }
  if (count === 2) {
    return {
      name: "Cần bồi dưỡng (2/3 CLO)",
      color: "amber"
    };
  }
  return {
    name: `Chưa đạt (${count}/3 CLO)`,
    color: "rose"
  };
}
function getPageNumbers(current, total) {
  const numbers = [];
  for (let number = 1; number <= total; number += 1) {
    if (number === 1 || number === total || Math.abs(number - current) <= 1) {
      const previous = numbers[numbers.length - 1];
      if (typeof previous === "number" && number - previous > 1) {
        numbers.push(`gap-${number}`);
      }
      numbers.push(number);
    }
  }
  return numbers;
}
async function fetchDemoStudents(params) {
  const filtered = DEMO_STUDENTS.filter(student => {
    const search = normalizeText(`${student.name ?? ""} ${student.studentId ?? student.id ?? ""}`);
    return search.includes(normalizeText(params.query)) && (!params.year || student.year === params.year) && (!params.major || student.major === params.major) && (params.cloCount === "" || student.cloCount === Number(params.cloCount));
  });
  const start = (params.page - 1) * params.pageSize;
  return {
    items: filtered.slice(start, start + params.pageSize),
    total: filtered.length
  };
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
    chevron: "m8 5 7 7-7 7",
    reset: "M3 11a9 9 0 1 1 2.6 7M3 4v7h7",
    calendar: "M3 5h18v16H3zM7 3v4M17 3v4M3 11h18",
    medal: "m8 12-1 9 5-3 5 3-1-9",
    help: "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 2-2.5 3.5M12 16h.01",
    bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"
  };
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name] || paths.document} />

      {name === "users" && <circle cx="9" cy="7" r="3" />}
      {name === "search" && <circle cx="10.5" cy="10.5" r="6.5" />}
      {name === "settings" && <circle cx="12" cy="12" r="3" />}
      {name === "medal" && <circle cx="12" cy="8" r="5" />}
    </svg>;
}
function radarPoint(index, percent) {
  const vertices = [[160, 30], [246.6, 180], [73.4, 180]];
  const ratio = Math.max(0, Math.min(100, Number(percent) || 0)) / 100;
  const [x, y] = vertices[index];
  return [160 + (x - 160) * ratio, 130 + (y - 130) * ratio];
}
export default function DanhGiaNangLucAdmin({
  onLogout,
  fetchStudents,
  summary,
  cloData
}) {
  const navigate = useNavigate();
  const isDemo = !fetchStudents;
  const [query, setQuery] = useState("");
  const [year, setYear] = useState("");
  const [major, setMajor] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [result, setResult] = useState({
    items: [],
    total: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const overview = summary ?? (isDemo ? DEMO_OVERVIEW : null);
  const sourcePillars = cloData ?? (isDemo ? CLO_DATA : null);
  const pillars = Array.isArray(sourcePillars) && sourcePillars.length === 3 ? sourcePillars : null;
  const totalPages = Math.max(1, Math.ceil(result.total / PAGE_SIZE));
  const pageNumbers = getPageNumbers(page, totalPages);
  const firstRecord = result.total ? (page - 1) * PAGE_SIZE + 1 : 0;
  const lastRecord = Math.min(page * PAGE_SIZE, result.total);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError("");
    const timer = setTimeout(async () => {
      try {
        const load = fetchStudents ?? fetchDemoStudents;
        const response = await load({
          page,
          pageSize: PAGE_SIZE,
          query: query.trim(),
          year,
          major,
          cloCount: status,
          signal: controller.signal
        });
        if (!active) return;
        if (!response || !Array.isArray(response.items) || !Number.isInteger(response.total) || response.total < 0) {
          throw new Error("Dữ liệu danh sách sinh viên không hợp lệ.");
        }
        const maxPage = Math.max(1, Math.ceil(response.total / PAGE_SIZE));
        if (page > maxPage) {
          setPage(maxPage);
          return;
        }
        setResult(response);
      } catch (requestError) {
        if (!active || requestError?.name === "AbortError") return;
        setError(requestError instanceof Error ? requestError.message : "Không thể tải danh sách sinh viên.");
      } finally {
        if (active) setLoading(false);
      }
    }, 250);
    return () => {
      active = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [fetchStudents, page, query, year, major, status, retry]);
  function changeFilter(setter, value) {
    setter(value);
    setPage(1);
  }
  function resetFilters() {
    setQuery("");
    setYear("");
    setMajor("");
    setStatus("");
    setPage(1);
    setRetry(value => value + 1);
  }
  function goToPage(next) {
    setPage(Math.max(1, Math.min(next, totalPages)));
  }
  function viewStudent(student) {
    const studentId = String(student.studentId ?? student.id ?? "");
    if (!studentId) {
      setNotice("Sinh viên chưa có mã số để mở hồ sơ.");
      return;
    }
    navigate(`/Ho_so_thanh_vien_Admin/${encodeURIComponent(studentId)}`, {
      state: {
        student
      }
    });
  }
  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      if (onLogout) await onLogout();
      navigate("/Dang_nhap");
    } catch (logoutError) {
      setNotice(logoutError instanceof Error ? logoutError.message : "Không thể đăng xuất.");
    } finally {
      setLoggingOut(false);
    }
  }
  const strongestPillar = pillars ? [...pillars].sort((a, b) => b.value - a.value)[0] : null;
  const weakestPillar = pillars ? [...pillars].sort((a, b) => a.value - b.value)[0] : null;
  return <div className="dbcas-admin-home dbcas-competency-page" style={{
    backgroundImage: `
          linear-gradient(
            rgba(7, 11, 20, .85),
            rgba(7, 11, 20, .85)
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
            <span>Tạo bài kiểm tra</span>
          </Link>

          <nav className="sidebar-nav" aria-label="Menu quản trị">
            {NAV_ITEMS.map(([icon, label, path]) => {
            const active = path === "/Danh_gia_nang_luc_Admin";
            return <Link key={path} className={`nav-link ${active ? "active" : ""}`} to={path} aria-current={active ? "page" : undefined}>
                  <Icon name={icon} />
                  <span>{label}</span>
                  {active && <span className="nav-dot" />}
                </Link>;
          })}
          </nav>
        </div>

        <div className="sidebar-bottom">
          <button className="btn-logout" type="button" disabled={loggingOut} onClick={handleLogout}>
            <Icon name="logout" />
            <span>
              {loggingOut ? "Đang đăng xuất..." : "Đăng xuất"}
            </span>
          </button>
        </div>
      </aside>

      <header className="topbar admin-unified-topbar">
        <div className="breadcrumb">
          <span>DBCAS Admin</span>
          <Icon name="chevron" />
          <strong>Đánh giá năng lực</strong>
        </div>

        <div className="topbar-actions">
          <label className="search top-search">
            <Icon name="search" />
            <input type="search" aria-label="Tìm kiếm sinh viên" placeholder="Tìm tên sinh viên hoặc MSSV..." value={query} onChange={event => changeFilter(setQuery, event.target.value)} />
          </label>

          <button className="icon-button" type="button" aria-label="Trợ giúp" onClick={() => setNotice("Tìm sinh viên và bấm Xem chi tiết để mở hồ sơ năng lực.")}>
            <Icon name="help" />
          </button>

          <button className="icon-button notification" type="button" aria-label="Thông báo" onClick={() => setNotice("Chưa có thông báo mới.")}>
            <Icon name="bell" />
          </button>

          <AdminAccountMenu onLogout={handleLogout} />
        </div>
      </header>

      <main className="main">
        <section className="card page-banner admin-unified-banner">
          <div>
            <h1>Đánh giá năng lực sinh viên</h1>
            <p>
              Theo dõi chuẩn đầu ra và xem hồ sơ năng lực
              của từng sinh viên.
            </p>
          </div>

          <label className="year-filter">
            <Icon name="calendar" />
            <select aria-label="Năm học" value={year} onChange={event => changeFilter(setYear, event.target.value)}>
              <option value="">Tất cả năm học</option>
              {YEARS.map(item => <option key={item} value={item}>
                  {item}
                </option>)}
            </select>
          </label>
        </section>

        <section className="kpi-row" aria-label="Chỉ số năng lực">
          <article className="card stat-card">
            <div className="stat-heading">
              <span>Năng lực trung bình</span>
              <span className="stat-icon cyan">
                <Icon name="medal" />
              </span>
            </div>
            <div className="stat-value">
              <strong>
                {overview ? `${overview.averagePercent}%` : "—"}
              </strong>
            </div>
            <p>
              {overview ? `Điểm trung bình ${(overview.averagePercent / 10).toFixed(2)}/10` : "Chưa có dữ liệu tổng quan"}
            </p>
          </article>

          <article className="card stat-card">
            <div className="stat-heading">
              <span>Sinh viên đạt chuẩn</span>
              <span className="stat-icon green">
                <Icon name="users" />
              </span>
            </div>
            <div className="stat-value">
              <strong>
                {overview ? Number(overview.passed).toLocaleString("vi-VN") : "—"}
              </strong>
              <span>SV</span>
            </div>
            <p>
              {overview ? `${overview.passedPercent}% tổng sinh viên · đạt 3/3 CLO` : "Chưa có dữ liệu tổng quan"}
            </p>
          </article>

          <article className="card stat-card">
            <div className="stat-heading">
              <span>Sinh viên chưa đạt</span>
              <span className="stat-icon amber">
                <Icon name="users" />
              </span>
            </div>
            <div className="stat-value">
              <strong>
                {overview ? Number(overview.notPassed).toLocaleString("vi-VN") : "—"}
              </strong>
              <span>SV</span>
            </div>
            <p>
              {overview ? `${overview.notPassedPercent}% tổng sinh viên · cần bồi dưỡng` : "Chưa có dữ liệu tổng quan"}
            </p>
          </article>
        </section>

        <div className="insight-row">
          <section className="card radar-card">
            <div className="card-head">
              <h2>Biểu đồ radar 3 chuẩn đầu ra</h2>
              <p>Tỷ lệ sinh viên đạt từng CLO so với mục tiêu 80%.</p>
            </div>

            {pillars ? <>
                <div className="radar-stage">
                  <div className="axis-pill cyan">
                    {pillars[0].name}: {pillars[0].title}
                    <strong>{pillars[0].value}%</strong>
                  </div>

                  <svg viewBox="0 0 320 220" role="img" aria-label={pillars.map(item => `${item.name}: ${item.value}%`).join(", ")}>
                    {[100, 80, 60, 40, 20].map(level => <polygon key={level} points={[0, 1, 2].map(index => radarPoint(index, level).join(",")).join(" ")} fill="none" stroke={level === 80 ? "#94a3b8" : "#334155"} strokeDasharray={level === 80 ? "5 4" : undefined} />)}

                    {[0, 1, 2].map(index => {
                  const [x, y] = radarPoint(index, 100);
                  return <line key={index} x1="160" y1="130" x2={x} y2={y} stroke="#334155" />;
                })}

                    <polygon points={pillars.map((item, index) => radarPoint(index, item.value).join(",")).join(" ")} fill="#22d3ee33" stroke="#22d3ee" strokeWidth="2" />

                    {pillars.map((item, index) => {
                  const [x, y] = radarPoint(index, item.value);
                  return <circle key={item.name} cx={x} cy={y} r="4" fill="#e2e8f0" stroke={item.value < 80 ? "#fb7185" : "#22d3ee"} strokeWidth="2" />;
                })}
                  </svg>

                  <div className="axis-row">
                    {[2, 1].map(index => <div key={pillars[index].name} className={`axis-pill ${pillars[index].value >= 80 ? "cyan" : "rose"}`}>
                        {pillars[index].name}: {pillars[index].title}
                        <strong>{pillars[index].value}%</strong>
                      </div>)}
                  </div>

                  <div className="radar-legend">
                    <span><i /> Tỷ lệ đạt thực tế</span>
                    <span><i className="target" /> Mục tiêu 80%</span>
                  </div>
                </div>

                <div className="radar-callouts">
                  <div className="callout green">
                    <span>CLO có tỷ lệ đạt cao nhất</span>
                    <strong>
                      {strongestPillar.name} · {strongestPillar.value}%
                    </strong>
                  </div>

                  <div className="callout rose">
                    <span>CLO có tỷ lệ đạt thấp nhất</span>
                    <strong>
                      {weakestPillar.name} · {weakestPillar.value}%
                    </strong>
                  </div>
                </div>
              </> : <div className="empty-panel">Chưa có dữ liệu radar.</div>}
          </section>

          <section className="card matrix-card">
            <div className="card-head">
              <h2>Ma trận phân tích chuẩn đầu ra</h2>
              <p>Mục tiêu: ít nhất 80% sinh viên đạt từng CLO.</p>
            </div>

            <div className="clo-stack">
              {pillars ? pillars.map(item => <article className="clo-card" key={item.name}>
                    <header>
                      <h3>
                        {item.name} · {item.title}
                        {" "}({item.weight})
                      </h3>
                      <span className={`badge ${item.value >= 80 ? "green" : "rose"}`}>
                        {item.value >= 80 ? "Đạt mục tiêu" : "Cần bồi dưỡng"}
                      </span>
                    </header>
                    <p>{item.description}</p>
                    <strong className={item.value >= 80 ? "text-cyan" : "text-rose"}>
                      {item.value}%
                    </strong>
                  </article>) : <div className="empty-panel">Chưa có dữ liệu CLO.</div>}

              <Link className="btn-detail" to="/CLO_Ky_nang_Admin">
                Xem ma trận ánh xạ CLO & Kỹ năng
              </Link>
            </div>
          </section>
        </div>

        <section className="card results">
          <div className="card-head">
            <h2>Danh sách sinh viên</h2>
            <p>
              Tra cứu sinh viên và xem hồ sơ phân tích năng lực cá nhân.
            </p>
          </div>

          <div className="filter-row">
            <label className="search">
              <Icon name="search" />
              <input type="search" aria-label="Tìm sinh viên" placeholder="Tìm tên sinh viên hoặc MSSV..." value={query} onChange={event => changeFilter(setQuery, event.target.value)} />
            </label>

            <label className="year-filter">
              <select aria-label="Ngành đào tạo" value={major} onChange={event => changeFilter(setMajor, event.target.value)}>
                <option value="">Tất cả ngành</option>
                {MAJORS.map(item => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>

            <label className="year-filter">
              <select aria-label="Trạng thái CLO" value={status} onChange={event => changeFilter(setStatus, event.target.value)}>
                <option value="">Tất cả trạng thái CLO</option>
                <option value="3">Đạt chuẩn (3/3 CLO)</option>
                <option value="2">Cần bồi dưỡng (2/3 CLO)</option>
                <option value="1">Chưa đạt (1/3 CLO)</option>
                <option value="0">Chưa đạt (0/3 CLO)</option>
              </select>
            </label>

            <button className="btn-detail reset-button" type="button" onClick={resetFilters}>
              <Icon name="reset" />
              Đặt lại
            </button>
          </div>

          <div className="table-wrap" aria-busy={loading}>
            <table>
              <thead>
                <tr>
                  <th scope="col">Sinh viên</th>
                  <th scope="col">MSSV</th>
                  <th scope="col">Điểm mạnh</th>
                  <th scope="col">Điểm yếu</th>
                  <th scope="col">Chuẩn CLO</th>
                  <th scope="col">Thao tác</th>
                </tr>
              </thead>

              <tbody>
                {loading ? <tr>
                    <td colSpan={6} className="empty-state" role="status">
                      Đang tải danh sách sinh viên...
                    </td>
                  </tr> : error ? <tr>
                    <td colSpan={6} className="empty-state">
                      <p role="alert">{error}</p>
                      <button type="button" className="btn-detail" onClick={() => setRetry(value => value + 1)}>
                        Thử lại
                      </button>
                    </td>
                  </tr> : result.items.length === 0 ? <tr>
                    <td colSpan={6} className="empty-state">
                      Không có sinh viên phù hợp với bộ lọc.
                    </td>
                  </tr> : result.items.map(student => {
                const studentId = String(student.studentId ?? student.id ?? "");
                const name = String(student.name ?? "Chưa cập nhật");
                const initials = name.trim().split(/\s+/).slice(-2).map(word => word[0] || "").join("");
                const clo = cloStatus(student.cloCount);
                return <tr key={student.id ?? studentId}>
                        <td>
                          <div className="student">
                            <span className="student-avatar">
                              {initials || "SV"}
                            </span>
                            <div>
                              <strong title={name}>{name}</strong>
                            </div>
                          </div>
                        </td>

                        <td>
                          <span className="student-id">{studentId}</span>
                        </td>

                        <td>
                          <span className="skill-label green">
                            {student.strong || "Chưa có phân tích"}
                          </span>
                        </td>

                        <td>
                          <span className="skill-label rose">
                            {student.weak || "Chưa có phân tích"}
                          </span>
                        </td>

                        <td>
                          <span className={`badge clo-status ${clo.color}`}>
                            {clo.name}
                          </span>
                        </td>

                        <td>
                          <button type="button" className="btn-detail" onClick={() => viewStudent(student)}>
                            Xem chi tiết
                          </button>
                        </td>
                      </tr>;
              })}
              </tbody>
            </table>
          </div>

          <div className="pager">
            <p>
              {loading ? "Đang tải..." : error ? "Chưa tải được danh sách" : <>
                  Hiển thị <strong>{firstRecord}–{lastRecord}</strong>
                  {" "}trên <strong>{result.total}</strong> sinh viên
                  <span className="pager-divider">·</span>
                  Trang <strong>{page}/{totalPages}</strong>
                </>}
            </p>

            <nav className="pagination" aria-label="Phân trang sinh viên">
              <button type="button" className="page-button" disabled={loading || !!error || page === 1} onClick={() => goToPage(page - 1)}>
                Trước
              </button>

              {pageNumbers.map(item => typeof item === "number" ? <button key={item} type="button" className={`page-button ${item === page ? "active" : ""}`} aria-label={`Trang ${item}`} aria-current={item === page ? "page" : undefined} disabled={loading || !!error} onClick={() => goToPage(item)}>
                    {item}
                  </button> : <span key={item} className="page-ellipsis">
                    …
                  </span>)}

              <button type="button" className="page-button" disabled={loading || !!error || page >= totalPages} onClick={() => goToPage(page + 1)}>
                Sau
              </button>
            </nav>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>DBCAS • Nền tảng đánh giá năng lực CSDL</span>
        <span>© 2026 Duy Tan University</span>
      </footer>

      {notice && <div className="admin-notice" role="status">
          <span>{notice}</span>
          <button type="button" aria-label="Đóng thông báo" onClick={() => setNotice("")}>
            ×
          </button>
        </div>}
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
    setError("");
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
    <button ref={trigger} type="button" className="admin-account-trigger" aria-expanded={open} aria-label="Thông tin tài khoản Admin" onClick={() => setOpen(value => !value)}>
      <span className="admin-account-avatar">{initials}</span>
      <span className="admin-account-caption"><strong>{account.name}</strong><small>{account.email}</small></span>
      <span aria-hidden="true" className="admin-account-chevron">⌄</span>
    </button>
    {open && <div className="admin-account-panel">
      <div className="admin-account-panel-head"><span className="admin-account-avatar">{initials}</span><div><strong>{account.name}</strong><small>Quản trị viên</small></div></div>
      <dl><div><dt>Email</dt><dd>{account.email}</dd></div><div><dt>Số điện thoại</dt><dd>{account.phone || "Chưa cập nhật"}</dd></div></dl>
      <Link to="/Cai_dat_Admin" onClick={() => setOpen(false)} className="admin-account-settings">Cài đặt tài khoản</Link>
      <button type="button" className="admin-account-logout" disabled={busy} onClick={logout}>{busy ? "Đang đăng xuất..." : "Đăng xuất"}</button>
      {error && <p role="alert" className="admin-account-error">{error}</p>}
    </div>}
  </div>;
}