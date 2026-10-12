import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./Bao_cao_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";

// Dữ liệu giả lập ổn định; thay bằng API qua props của từng trang.
const DEMO_MAJORS = ["Kỹ thuật Phần mềm", "Khoa học Máy tính", "Hệ thống Thông tin Quản lý", "An ninh Mạng", "Công nghệ Phần mềm"];
const DEMO_STUDENTS = Array.from({
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
    year: ["2024-2025", "2025-2026", "2026-2027"][index % 3],
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
const PAGE_SIZE = 10;
const SKILLS = ["Truy vấn SQL", "DML & DDL", "Thiết kế & Ràng buộc"];
const LEVELS = [{
  key: "excellent",
  label: "Xuất sắc",
  range: "9.0–10.0",
  min: 9,
  color: "#34d399"
}, {
  key: "good",
  label: "Giỏi",
  range: "8.0–<9.0",
  min: 8,
  color: "#22d3ee"
}, {
  key: "fair",
  label: "Khá",
  range: "6.5–<8.0",
  min: 6.5,
  color: "#818cf8"
}, {
  key: "average",
  label: "Trung bình",
  range: "5.0–<6.5",
  min: 5,
  color: "#fbbf24"
}, {
  key: "review",
  label: "Cần bồi dưỡng",
  range: "<5.0",
  min: 0,
  color: "#fb7185"
}];
const NAV_ITEMS = [["home", "Trang chủ", "/Home_Admin"], ["users", "Đánh giá năng lực", "/Danh_gia_nang_luc_Admin"], ["cap", "CLO & Kỹ năng", "/CLO_Ky_nang_Admin"], ["document", "Quản lý bài kiểm tra", "/Quan_ly_bai_kiem_tra_Admin"], ["robot", "Đánh giá bằng AI", "/Danh_gia_AI_Admin"], ["chart", "Báo cáo", "/Bao_cao_Admin"], ["settings", "Cài đặt", "/Cai_dat_Admin"]];

// Dữ liệu tạm; sau này truyền dữ liệu từ BE qua prop students.
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
    download: "M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
    reset: "M3 10a9 9 0 1 1 2 8M3 4v6h6"
  };
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name] || paths.chart} />
      {adminRender(name === "users" && <circle cx="9" cy="7" r="3" />)}
      {adminRender(name === "search" && <circle cx="10.5" cy="10.5" r="6.5" />)}
      {adminRender(name === "help" && <circle cx="12" cy="12" r="9" />)}
      {adminRender(name === "settings" && <circle cx="12" cy="12" r="3" />)}
    </svg>;
}
function normalizeText(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase().trim();
}
function getLevel(score) {
  return LEVELS.find(level => score >= level.min);
}
function passedClos(student) {
  return (student.clos || []).filter(Boolean).length;
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
export default function BaoCaoAdmin({
  onLogout,
  students: sourceStudents = DEMO_STUDENTS
}) {
  useAdminLanguage();

  const navigate = useNavigate();
  const [year, setYear] = useState("");
  const [major, setMajor] = useState("");
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const students = (Array.isArray(sourceStudents) ? sourceStudents : []).filter(student => student && student.score != null && student.score !== "" && Number.isFinite(Number(student.score)) && Number(student.score) >= 0 && Number(student.score) <= 10);
  const majors = [...new Set(students.map(s => s.major).filter(Boolean))];
  const years = [...new Set(students.map(s => s.year).filter(Boolean))].sort().reverse();
  const scopeStudents = students.filter(student => (!year || student.year === year) && (!major || student.major === major) && normalizeText(`${student.name ?? ""} ${student.studentId ?? student.id ?? ""}`).includes(normalizeText(query)));
  const distribution = LEVELS.map(level => {
    const count = scopeStudents.filter(s => getLevel(Number(s.score)).key === level.key).length;
    return {
      ...level,
      count,
      percent: scopeStudents.length ? count / scopeStudents.length * 100 : 0
    };
  });
  const [levelFilter, setLevelFilter] = useState("");
  const [page, setPage] = useState(1);
  const rankedStudents = [...scopeStudents].sort((a, b) => Number(b.score) - Number(a.score) || String(a.studentId ?? a.id).localeCompare(String(b.studentId ?? b.id))).map((student, index) => ({
    ...student,
    score: Number(student.score),
    rank: index + 1
  }));
  const visible = rankedStudents.filter(student => !levelFilter || getLevel(student.score).key === levelFilter);
  const totalPages = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const pageStudents = visible.slice(startIndex, startIndex + PAGE_SIZE);
  const firstRecord = visible.length ? startIndex + 1 : 0;
  const lastRecord = Math.min(startIndex + PAGE_SIZE, visible.length);
  function resetTableFilters() {
    setQuery("");
    setLevelFilter("");
    setPage(1);
  }
  function skillValues(student) {
    return SKILLS.map((_, index) => Math.max(0, Math.min(10, Number(student.skills?.[index]) || 0)));
  }
  const maxCount = Math.max(1, ...distribution.map(item => item.count));
  const passRate = scopeStudents.length ? (scopeStudents.filter(s => Number(s.score) >= 5).length / scopeStudents.length * 100).toFixed(1) : "0.0";
  function resetFilters() {
    setQuery("");
    setMajor("");
    setYear("");
    setLevelFilter("");
    setPage(1);
  }
  function exportCsv() {
    if (!visible.length) {
      setNotice(adminText("Không có dữ liệu để xuất."));
      return;
    }
    const cell = value => {
      let text = String(value ?? "");
      if (/^[=+\-@\t\r]/.test(text)) text = "'" + text;
      return '"' + text.replace(/"/g, '""') + '"';
    };
    const rows = [["Sinh viên", "MSSV", "Ngành", "Năm học", "Điểm", "Xếp loại"], ...visible.map(s => [s.name, s.studentId ?? s.id, s.major, s.year, Number(s.score).toFixed(2), getLevel(Number(s.score)).label])];
    const blob = new Blob(["\uFEFF" + rows.map(row => row.map(cell).join(",")).join("\r\n")], {
      type: "text/csv;charset=utf-8"
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "Bao_cao_DBCAS.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      if (onLogout) await onLogout();
      navigate("/Dang_nhap");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Không thể đăng xuất.");
    } finally {
      setLoggingOut(false);
    }
  }
  return <div className="dbcas-admin-home dbcas-report-page" style={{
    backgroundImage: `linear-gradient(rgba(7,11,20,.82), rgba(7,11,20,.82)), url(${background})`
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
            {adminRender(NAV_ITEMS.map(([icon, label, path]) => {
            const active = path === "/Bao_cao_Admin";
            return <Link key={path} className={`nav-link${active ? " active" : ""}`} to={path} aria-current={active ? "page" : undefined}>
                  <Icon name={icon} />
                  <span>{adminRender(label)}</span>
                  {adminRender(active && <span className="nav-dot" />)}
                </Link>;
          }))}
          </nav>
        </div>

        <div className="sidebar-bottom">
          <button className="btn-logout" type="button" disabled={loggingOut} onClick={handleLogout}>
            <Icon name="logout" />
            <span>{adminRender(loggingOut ? "Đang đăng xuất..." : "Đăng xuất")}</span>
          </button>
        </div>
      </aside>

      <header className="topbar admin-unified-topbar">
        <div className="breadcrumb">
          <span>DBCAS Admin</span>
          <Icon name="chevron" />
          <strong>{adminText("Báo cáo")}</strong>
        </div>

        <div className="topbar-actions">
          <button className="icon-button" type="button" aria-label={adminText("Trợ giúp")} onClick={() => setNotice(adminText("Tìm tên hoặc MSSV, chọn ngành và năm học để lọc cả hai biểu đồ."))}>
            <Icon name="help" />
          </button>

          <NotificationMenu role="admin" className="icon-button" />

          <AdminAccountMenu onLogout={handleLogout} />
        </div>
      </header>

      <main className="main">
        <section className="report-scope" aria-label={adminText("Tìm kiếm và bộ lọc")}>
          <label className="report-search">
            <Icon name="search" />
            <input type="search" placeholder={adminText("Tìm tên sinh viên hoặc MSSV...")} aria-label={adminText("Tìm sinh viên hoặc MSSV")} value={query} onChange={event => {
            setQuery(event.target.value);
            setPage(1);
          }} />
          </label>
          <div className="report-filter-right">
            <span className="scope-label">{adminText("Bộ lọc phạm vi:")}</span>
            <select aria-label={adminText("Lọc ngành")} value={major} onChange={event => {
            setMajor(event.target.value);
            setPage(1);
          }}>
              <option value="">{adminText("Tất cả ngành")}</option>
              {adminRender(majors.map(item => <option key={item} value={item}>{adminRender(item)}</option>))}
            </select>
            <select aria-label={adminText("Lọc năm học")} value={year} onChange={event => {
            setYear(event.target.value);
            setPage(1);
          }}>
              <option value="">{adminText("Tất cả năm học")}</option>
              {adminRender(years.map(item => <option key={item} value={item}>{adminText("Năm học: ")}{adminRender(item)}</option>))}
            </select>
            <button className="report-button" type="button" onClick={resetFilters}>
              <Icon name="reset" />{adminText(" Đặt lại ")}</button>
          </div>
        </section>

        <section className="page-banner admin-unified-banner">
          <div className="report-banner-heading">
            <span className="report-banner-icon">
              <Icon name="chart" />
            </span>

            <div>
              <h1>{adminText("Báo cáo thống kê tổng quan")}</h1>
              <p>{adminText(" Phân bố điểm và mức xếp loại năng lực của sinh viên. ")}</p>
            </div>
          </div>

          <div className="report-export-actions">
            <button className="report-button export-csv" type="button" onClick={exportCsv}>
              <Icon name="download" />{adminText(" Xuất CSV ")}</button>

            <button className="report-button export-pdf" type="button" onClick={() => window.print()}>
              <Icon name="document" />{adminText(" Xuất PDF ")}</button>
          </div>
        </section>

        <section className="report-chart-row">
          <article className="card report-chart-card">
            <div className="report-card-heading">
              <h2>
                <Icon name="chart" />{adminText(" Biểu đồ phân bố điểm số trực quan (Score Distribution) ")}</h2>
              <p>{adminText("Mật độ phân bố phổ điểm của ")}{adminRender(scopeStudents.length)}{adminText(" sinh viên theo thang điểm 10")}</p>
            </div>

            <div className="report-bar-chart">
              {adminRender([...distribution].reverse().map(item => <div className="report-bar-column" key={item.key}>
                  <div className="report-bar-track">
                    <div className="report-bar" style={{
                  height: `${item.count / maxCount * 85}%`,
                  background: `${item.color}66`,
                  border: `1px solid ${item.color}99`
                }}>
                      <span style={{
                    color: item.color
                  }}>
                        {adminRender(item.count)} SV
                      </span>
                    </div>
                  </div>

                  <strong>{adminRender(item.range)}</strong>
                  <small>{adminRender(item.percent.toFixed(1))}%</small>
                </div>))}
            </div>

            {adminRender(!scopeStudents.length && <p className="report-empty-chart">{adminText("Chưa có dữ liệu.")}</p>)}
          </article>

          <article className="card report-level-card">
            <div className="report-card-heading">
              <h2>{adminText("Phân bố mức xếp loại năng lực")}</h2>
              <p>{adminRender(scopeStudents.length)}{adminText(" sinh viên")}</p>
            </div>

            <div className="report-level-list">
              {adminRender(distribution.map(item => <div className="report-level-item" key={item.key}>
                  <div className="report-level-meta">
                    <span>
                      <i style={{
                    background: item.color
                  }} />
                      {adminRender(item.label)} ({adminRender(item.range)})
                    </span>
                    <strong style={{
                  color: item.color
                }}>
                      {adminRender(item.count)} SV · {adminRender(item.percent.toFixed(1))}%
                    </strong>
                  </div>

                  <div className="report-progress">
                    <i style={{
                  width: `${item.percent}%`,
                  background: `${item.color}66`,
                  border: `1px solid ${item.color}99`
                }} />
                  </div>
                </div>))}
            </div>

            <div className="report-clo-summary">
              <span>{adminText("Tỷ lệ hoàn thành chuẩn năng lực")}</span>
              <strong>{adminRender(passRate)}{adminText("% · Vượt ngưỡng chuẩn (≥ 5.0)")}</strong>
            </div>
          </article>
        </section>

        <section className="card report-ranking">
          <div className="report-ranking-heading">
            <div>
              <h2>{adminText("Bảng xếp hạng sinh viên theo năng lực")}</h2>
              <p>{adminText(" Xếp theo điểm năng lực giảm dần · Trắc nghiệm 40%, truy vấn SQL 30%, tự luận 30% ")}</p>
            </div>
          </div>

          <div className="report-table-filters">
            <label className="report-search">
              <Icon name="search" />
              <input type="search" placeholder={adminText("Lọc theo tên hoặc MSSV...")} aria-label={adminText("Tìm sinh viên trong bảng")} value={query} onChange={event => {
              setQuery(event.target.value);
              setPage(1);
            }} />
            </label>

            <select aria-label={adminText("Lọc mức xếp loại")} value={levelFilter} onChange={event => {
            setLevelFilter(event.target.value);
            setPage(1);
          }}>
              <option value="">{adminText("Mọi mức xếp loại")}</option>
              {adminRender(LEVELS.map(level => <option key={level.key} value={level.key}>
                  {adminRender(level.label)} ({adminRender(level.range)})
                </option>))}
            </select>

            <button className="report-button" type="button" onClick={resetTableFilters}>
              <Icon name="reset" />{adminText(" Làm mới ")}</button>
          </div>

          <div className="report-table-wrap">
            <table className="report-table">
              <colgroup>
                <col className="col-rank" />
                <col className="col-student" />
                <col className="col-major" />
                <col className="col-attempts" />
                <col className="col-score" />
                <col className="col-skills" />
                <col className="col-clo" />
                <col className="col-level" />
              </colgroup>

              <thead>
                <tr>
                  <th scope="col">{adminText("Hạng")}</th>
                  <th scope="col">{adminText("Sinh viên / MSSV")}</th>
                  <th scope="col">{adminText("Ngành")}</th>
                  <th scope="col">{adminText("Số bài")}</th>
                  <th scope="col">{adminText("Điểm")}</th>
                  <th scope="col">{adminText("Năng lực từng kỹ năng")}</th>
                  <th scope="col">CLO</th>
                  <th scope="col">{adminText("Xếp loại")}</th>
                </tr>
              </thead>

              <tbody>
                {adminRender(!pageStudents.length && <tr>
                    <td colSpan={8} className="report-empty-state">{adminText(" Không có sinh viên phù hợp. ")}</td>
                  </tr>)}

                {adminRender(pageStudents.map(student => {
                const level = getLevel(student.score);
                const scores = skillValues(student);
                const strongestIndex = scores.indexOf(Math.max(...scores));
                const weakestIndex = scores.indexOf(Math.min(...scores));
                return <tr key={student.studentId ?? student.id}>
                      <td data-label="Hạng">
                        <span className={`report-rank ${student.rank <= 3 ? `rank-${student.rank}` : ""}`}>
                          {adminRender(student.rank <= 3 ? student.rank : `#${student.rank}`)}
                        </span>
                      </td>

                      <td data-label="Sinh viên / MSSV">
                        <div className="report-student">
                          <strong>{adminRender(student.name)}</strong>
                          <small>{adminRender(student.studentId)}</small>
                        </div>
                      </td>

                      <td data-label="Ngành">{adminRender(student.major)}</td>

                      <td data-label="Số bài" className="report-center">
                        {adminRender(student.attempts)}
                      </td>

                      <td data-label="Điểm" className="report-center">
                        <strong className="report-score" style={{
                      color: level.color
                    }}>
                          {adminRender(student.score.toFixed(2))}
                        </strong>
                        <small className="report-score-max">/ 10</small>
                      </td>

                      <td data-label="Năng lực từng kỹ năng">
                        <div className="report-skill-list">
                          {adminRender(SKILLS.map((skill, index) => <div key={skill} className="report-skill">
                              <div>
                                <span>{adminRender(skill)}</span>
                                <strong>{adminRender(scores[index].toFixed(1))}</strong>
                              </div>
                              <div className="report-progress">
                                <i style={{
                            width: `${Math.max(0, Math.min(100, scores[index] * 10))}%`,
                            background: scores[index] >= 6 ? "#22d3ee" : "#fb7185"
                          }} />
                              </div>
                            </div>))}
                          <div className="report-skill-notes">
                            <span>{adminText("Mạnh: ")}{adminRender(SKILLS[strongestIndex])}</span>
                            <span>{adminText("Cần cải thiện: ")}{adminRender(SKILLS[weakestIndex])}</span>
                          </div>
                        </div>
                      </td>

                      <td data-label="CLO" className="report-center">
                        <strong className={passedClos(student) === 3 ? "report-green" : "report-rose"}>
                          {adminRender(passedClos(student))}/3
                        </strong>
                        <small className="report-clo-label">
                          {adminRender(passedClos(student) === 3 ? "Đạt chuẩn" : "Chưa đủ")}
                        </small>
                      </td>

                      <td data-label="Xếp loại" className="report-center">
                        <span className="report-level-badge" style={{
                      color: level.color,
                      borderColor: `${level.color}44`,
                      background: `${level.color}12`
                    }}>
                          {adminRender(level.label)}
                        </span>
                      </td>
                    </tr>;
              }))}
              </tbody>
            </table>
          </div>

          <div className="report-pager">
            <p>{adminText(" Hiển thị ")}<strong>{adminRender(firstRecord)}–{adminRender(lastRecord)}</strong> trong{adminRender(" ")}
              <strong>{adminRender(visible.length)}</strong>{adminText(" sinh viên ")}</p>

            <nav className="report-pagination" aria-label={adminText("Phân trang")}>
              <button type="button" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>{adminText(" ‹ Trước ")}</button>

              {adminRender(getPageNumbers(currentPage, totalPages).map(number => typeof number === "string" ? <span key={number}>…</span> : <button key={number} type="button" className={number === currentPage ? "active" : ""} aria-label={`Trang ${number}`} aria-current={number === currentPage ? "page" : undefined} onClick={() => setPage(number)}>
                    {adminRender(number)}
                  </button>))}

              <button type="button" disabled={currentPage === totalPages} onClick={() => setPage(currentPage + 1)}>
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