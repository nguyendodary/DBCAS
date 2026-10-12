import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./Home_Learner.css";
import "./Xem_danh_gia_Learner.css";
import video from "./video1.mp4";
import poster from "./nen1.jpg";
const GROUPS = [
  {
    title: "Nhóm 1: SQL Querying", tone: "cyan", skills: [
      { title: "Truy vấn cơ bản: SELECT, WHERE, ORDER BY, DISTINCT", score: 9.5, label: "Tối ưu", description: "Nắm vững cú pháp chuẩn, lọc dữ liệu chính xác, tối ưu hóa mệnh đề lọc không gây table scan dư thừa." },
      { title: "Liên kết & Gom nhóm: JOIN, GROUP BY, HAVING, Aggregates", score: 9.2, label: "Thành thạo", description: "Tối ưu liên kết INNER/LEFT JOIN, kiểm soát chặt chẽ điều kiện HAVING so với WHERE, bảo đảm tính toàn vẹn thống kê." },
      { title: "Truy vấn nâng cao: Subqueries, CTE, Window Functions", score: 8.6, label: "Đạt chuẩn cao", description: "Tư duy tốt truy vấn phân tích bằng CTE, cấu trúc WITH RECURSIVE và các hàm phân tích cửa sổ OVER (PARTITION BY)." },
    ]
  },
  {
    title: "Nhóm 2: Data Manipulation & DDL", tone: "purple", skills: [
      { title: "Thao tác dữ liệu DML: INSERT, UPDATE, DELETE", score: 8.8, label: "Ổn định", description: "Thực thi giao tác dữ liệu an toàn, xử lý chuẩn điều kiện WHERE khi cập nhật, kiểm soát tốt tính nhất quán." },
      { title: "Định nghĩa DDL: CREATE, ALTER, DROP", score: 8.4, label: "Đạt chuẩn", description: "Nắm vững các thao tác định nghĩa bảng và lựa chọn kiểu dữ liệu phù hợp." },
      { title: "Khung nhìn & Đối tượng (Views)", score: 8.0, label: "Mức khá", description: "Cần tối ưu Materialized Views trong môi trường dữ liệu lớn và cơ chế cập nhật tự động (Refresh)." },
    ]
  },
  {
    title: "Nhóm 3: Constraints & Design", tone: "rose", skills: [
      { title: "Khóa & Ràng buộc toàn vẹn: PK, FK, CHECK, NOT NULL", score: 6.8, label: "Cần lưu ý", description: "Cần chú ý cascade và vi phạm khóa ngoại trong kịch bản quan hệ N-N và ràng buộc CHECK logic phức hợp." },
      { title: "Thiết kế lược đồ & Chuẩn hóa: 1NF, 2NF, 3NF, BCNF", score: 5.2, label: "Báo động", description: "Thường nhầm lẫn phân rã lược đồ bảo toàn phụ thuộc hàm F+, chưa nắm vững điều kiện tiên quyết chuẩn BCNF so với 3NF." },
      { title: "Lập luận thiết kế khái niệm", score: 5.4, label: "Cần ôn tập", description: "Cần rèn luyện giải thích trade-offs trong thiết kế thực tế và chuyển đổi chuẩn xác từ mô hình ERD sang lược đồ quan hệ." },
    ]
  },
];
const STRONG_TITLES = [GROUPS[0].skills[0].title, GROUPS[0].skills[1].title, GROUPS[1].skills[0].title, GROUPS[0].skills[2].title];
const GAP_TITLES = [GROUPS[2].skills[1].title, GROUPS[2].skills[2].title, GROUPS[2].skills[0].title, GROUPS[1].skills[2].title];
const GUIDANCE = [
  { title: "Thuật toán Chuẩn hóa Lược đồ (1NF → BCNF) & Tìm Bao đóng F+", text: "Ôn lại định nghĩa phụ thuộc hàm, công thức tính bao đóng thuộc tính X+, thuật toán tìm khóa tối thiểu và quy trình phân rã bảo toàn thông tin. Phân biệt rõ ràng điều kiện quyết định giữa 3NF và BCNF để tránh nhầm lẫn.", focus: "Bao đóng X+ & Thuật toán phân rã 3NF" },
  { title: "Biện luận Mô hình Khái niệm & Ràng buộc Thực tế", text: "Rèn luyện kỹ năng phân tích mối quan hệ Nhiều-Nhiều (N-N), chuẩn hóa bảng trung gian và lý giải các đánh đổi (trade-offs) về hiệu năng truy vấn so với độ dư thừa dữ liệu khi thiết kế mô hình trong thực tế sản xuất.", focus: "Bảng nối quan hệ N-N & Trade-offs" },
  { title: "Quy tắc Khóa ngoại (FK) & Hành vi Toàn vẹn Tham chiếu", text: "Phân biệt rõ ràng tác động giữa ON DELETE CASCADE, ON DELETE SET NULL và ON DELETE RESTRICT để tránh vô tình xóa lan dữ liệu liên đới hoặc gặp lỗi vi phạm tính toàn vẹn khóa ngoại khi cập nhật bảng cha/con.", focus: "Cơ chế Trigger & Cascade Constraints" },
];
// Dữ liệu FE tạm; thay scores/students/skillGroups bằng dữ liệu API khi có backend.
const DEMO_SCORES = (() => {
  const values = Array.from({ length: 42 }, (_, i) => 5.3 + 3.9 * (1 - Math.exp(-i / 8)) + Math.sin(i * 0.8) * 0.65);
  values[0] = 3;
  values[41] = 9.2;
  const correction = (7.8 * 42 - values.reduce((sum, v) => sum + v, 0)) / 40;
  return values.map((v, i) => i === 0 || i === 41 ? v : v + correction);
})();
const NAMES = ["Trần Đức Anh", "Lê Thu Hà", "Vũ Minh Quang", "Đỗ Hoàng Long", "Lý Bảo Ngọc", "Trịnh Quốc Đạt", "Hồ Tấn Minh"];
export const MAJORS = ["Kỹ thuật Phần mềm", "Khoa học Máy tính", "Hệ thống Thông tin Quản lý", "An ninh Mạng", "Công nghệ Phần mềm"];
export const DEMO_STUDENTS = Array.from({ length: 2241 }, (_, i) => ({
  id: String(20216000001 + i),
  name: i === 99 ? "Nguyễn Hoàng Long" : NAMES[i] || `${["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng"][i % 5]} ${["Minh Anh", "Quốc Bảo", "Gia Huy", "Ngọc Linh", "Thanh Tâm", "Tuấn Kiệt", "Khánh Vy"][i % 7]}`,
  major: MAJORS[i % MAJORS.length],
  rank: i + 1,
  completed: [48, 46, 44, 45, 44, 43, 44][i % 7],
  totalExams: 54,
  rate: i < 7 ? [96.8, 93.5, 91, 89.5, 88, 87.2, 86.5][i] : Math.max(25, 86.4 - (i - 7) * 0.027),
  score: i < 7 ? [9.4, 9.1, 8.9, 8.8, 8.7, 8.6, 8.5][i] : Math.max(2.5, 8.49 - (i - 7) * 0.00268),
}));
export function Icon({ name }) {
  const paths = {
    database: "M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7",
    file: "M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h8",
    chart: "M4 3v18h17M8 17v-5M13 17V7M18 17v-8",
    settings: "M3 6h18M3 12h18M3 18h18",
    bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
    trend: "m3 17 6-6 4 4 8-10M16 5h5v5",
    groups: "M4 4h6v6H4zM14 4h6v6h-6zM14 14h6v6h-6zM7 10v7h7",
    check: "m8 12 3 3 5-6",
    warning: "m12 3 10 18H2zM12 9v5M12 17h.01",
    search: "m16 16 5 5",
    arrow: "M4 12h16m-6-6 6 6-6 6",
    sparkles: "m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5ZM20 2v4M18 4h4",
    bulb: "M9 18h6M9 21h6M8 14a6 6 0 1 1 8 0c-1 1-1 2-1 3H9c0-1 0-2-1-3",
    list: "M8 5h13M8 12h13M8 19h13M3 4v2M3 11v2M3 18v2",
    users: "M3 21v-3a5 5 0 0 1 10 0v3M15 14a5 5 0 0 1 6 4v3",
  };
  return (
    <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {name === "home" ? <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></> : <path d={paths[name] || paths.chart} />}
      {name === "database" && <ellipse cx="12" cy="5" rx="8" ry="3" />}
      {name === "settings" && <><circle cx="8" cy="6" r="2" /><circle cx="16" cy="12" r="2" /><circle cx="10" cy="18" r="2" /></>}
      {name === "search" && <circle cx="10.5" cy="10.5" r="6.5" />}
      {name === "check" && <circle cx="12" cy="12" r="9" />}
      {name === "users" && <><circle cx="8" cy="7" r="4" /><path d="M15 3a4 4 0 0 1 0 8" /></>}
    </svg>
  );
}
export function normalize(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d").toLowerCase().trim();
}
function mean(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}
export function badge(rank, total) {
  const position = Number(rank);
  const studentCount = Number(total);

  if (!Number.isFinite(position) || position < 1) return "Chưa xếp hạng";
  if (position === 1) return "TOP 1 THỦ KHOA";
  if (position === 2) return "TOP 2 Á KHOA";
  if (position === 3) return "TOP 3";
  if (position <= 100) return `Top ${Math.ceil(position / 10) * 10}`;
  if (!Number.isFinite(studentCount) || studentCount < position) return `Hạng ${position}`;
  return `Top ${Math.ceil((position / studentCount) * 100)}%`;
}

export const DEMO_STUDENT_ID = "20216000100";

export function currentStudentId(user, fallback = DEMO_STUDENT_ID) {
  if (user === null || user === undefined) return fallback;
  return String(user.studentId ?? user.mssv ?? user.studentCode ?? "").trim();
}

export function rankStudents(students) {
  return (Array.isArray(students) ? students : [])
    .map(student => ({ ...student, id: String(student.id ?? student.studentId ?? student.mssv ?? "") }))
    .sort((a, b) => (Number(a.rank) || Infinity) - (Number(b.rank) || Infinity) || Number(b.score) - Number(a.score))
    .map((student, index) => ({ ...student, rank: Number(student.rank) > 0 ? Number(student.rank) : index + 1 }));
}

export function nearbyStudents(ranked, myId, count = 10) {
  const pool = ranked.slice(3);
  if (!ranked.some(student => student.id === myId)) return [];
  const index = pool.findIndex(student => student.id === myId);
  const start = Math.max(0, Math.min(index < 0 ? 0 : index - Math.floor(count / 2), pool.length - count));
  return pool.slice(start, start + count);
}

export function StudentRankRow({ student, myId, total, pinnedIndex }) {
  const mine = student.id === myId;
  return (
    <tr
      className={`${mine ? "de-my-row" : ""} ${pinnedIndex !== undefined ? "de-top-row" : ""}`}
      style={pinnedIndex !== undefined ? { "--pinned-index": pinnedIndex } : undefined}
      aria-current={mine ? "true" : undefined}
    >
      <td><span className={`de-rank ${student.rank <= 3 ? `medal-${student.rank}` : ""}`}>#{student.rank}</span></td>
      <td><strong className="de-student-name">{student.name}</strong><span className="de-student-id">MSSV: {student.id}</span></td>
      <td>{student.major}</td>
      <td className="de-numeric">{student.completed} / {student.totalExams}</td>
      <td className={`de-numeric ${student.rate >= 90 ? "de-green" : ""}`}>{Number(student.rate).toFixed(1)}%</td>
      <td className="de-numeric de-table-score">{Number(student.score).toFixed(1)}</td>
      <td><span className={`de-title-badge badge-${Math.min(student.rank, 4)}`}>{badge(student.rank, total)}</span></td>
    </tr>
  );
}
function ScoreChart({ scores }) {
  const [hovered, setHovered] = useState(null);
  const points = useMemo(() => {
    let sum = 0;
    return scores.map((score, i) => {
      sum += score;
      return { score, average: sum / (i + 1), number: i + 1 };
    });
  }, [scores]);
  const selected = points.length ? Math.min(hovered ?? points.length - 1, points.length - 1) : 0;
  const x = (i) => 48 + i / Math.max(1, points.length - 1) * 1104;
  const y = (score) => 228 - score / 10 * 188;
  const actual = points.map((p, i) => `${x(i)},${y(p.score)}`).join(" ");
  const average = points.map((p, i) => `${x(i)},${y(p.average)}`).join(" ");
  const active = points[selected];
  const labels = [...new Set([0, 9, 19, 29, points.length - 1].filter(i => i >= 0 && i < points.length))];
  return (
    <section className="de-chart-panel" aria-label="Biểu đồ điểm kiểm tra">
      <div className="de-panel-heading">
        <div><h2><Icon name="trend" />Biểu đồ Biến thiên Điểm số &amp; Điểm TB Tích lũy</h2><p>Chuỗi dữ liệu {points.length} bài kiểm tra đã nộp so với Mốc chuẩn Đạt (≥ 6.0 / 10)</p></div>
        <div className="de-chart-legend"><span><i className="dotted" />Điểm từng bài</span><span><i />TB tích lũy ({mean(scores).toFixed(1)} / 10)</span><span className="rose"><i />Chuẩn Đạt (≥ 6.0 / 10)</span></div>
      </div>
      {!points.length ? <p className="de-chart-empty">Chưa có kết quả bài kiểm tra.</p> : (
        <svg className="de-chart" viewBox="0 0 1200 300" role="img" aria-label={`Điểm ${points.length} bài, trung bình ${mean(scores).toFixed(1)} trên 10`}>
          <defs><linearGradient id="de-average-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22d3ee" stopOpacity=".22" /><stop offset="100%" stopColor="#22d3ee" stopOpacity="0" /></linearGradient></defs>
          {[0, 2, 4, 6, 8, 10].map(value => <g key={value}><line x1="48" y1={y(value)} x2="1152" y2={y(value)} className="de-grid-line" /><text x="35" y={y(value) + 4} textAnchor="end" className="de-axis-text">{value.toFixed(1)}</text></g>)}
          <polygon points={`48,228 ${average} ${x(points.length - 1)},228`} fill="url(#de-average-fill)" />
          <line x1="48" y1={y(6)} x2="1152" y2={y(6)} className="de-target-line" />
          <text x="1152" y={y(6) + 16} textAnchor="end" className="de-target-label">Mốc chuẩn Đạt (≥ 6.0 / 10)</text>
          <polyline points={actual} className="de-actual-line" />
          <polyline points={average} className="de-average-line" />
          {points.map((p, i) => <g key={i} onMouseEnter={() => setHovered(i)}><circle cx={x(i)} cy={y(p.score)} r="2.5" className="de-actual-dot" /><circle cx={x(i)} cy={y(p.average)} r={i === selected ? 5.5 : 2.8} className="de-average-dot" /><circle cx={x(i)} cy={y(p.average)} r="12" fill="transparent" tabIndex="0" role="button" aria-label={`Bài ${p.number}: ${p.score.toFixed(1)} điểm, trung bình ${p.average.toFixed(1)}`} onFocus={() => setHovered(i)} onClick={() => setHovered(i)} /></g>)}
          {labels.map(i => <text key={i} x={x(i)} y="273" textAnchor={i === 0 ? "start" : i === points.length - 1 ? "end" : "middle"} className="de-axis-text">Bài {String(i + 1).padStart(2, "0")}</text>)}
          {active && <g transform={`translate(${Math.min(Math.max(x(selected) - 118, 48), 916)},${Math.max(12, y(active.average) - 49)})`}><rect width="236" height="31" rx="5" className="de-tooltip-box" /><text x="118" y="20" textAnchor="middle" className="de-tooltip-text">Điểm TB: {active.average.toFixed(1)} / 10 • {(active.average * 10).toFixed(1)}%</text></g>}
        </svg>
      )}
    </section>
  );
}
function SkillCard({ skill }) {
  const tone = skill.score < 6 ? "danger" : skill.score < 7 ? "warning" : "normal";
  return <article className={`de-skill-card ${tone}`}><div><h4>{skill.title}{tone !== "normal" && <Icon name="warning" />}</h4><p>{skill.description}</p></div><div className="de-skill-score"><strong>{skill.score.toFixed(1)} / 10</strong><span>• {skill.label}</span></div></article>;
}
export default function XemDanhGiaLearner({ user, scores = DEMO_SCORES, students = DEMO_STUDENTS, skillGroups = GROUPS }) {
  const location = useLocation();
  const accountUser = user ?? location.state?.user;
  const learner = { name: accountUser?.name ?? "Nguyễn Hoàng Long", email: accountUser?.email ?? "long.nh20216049@sis.hust.edu.vn", initials: accountUser?.initials ?? "HL" };
  const sourceStudents = students === DEMO_STUDENTS && Array.isArray(location.state?.students)
    ? location.state.students : students;
  const timer = useRef(null);
  const [notice, setNotice] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => () => clearTimeout(timer.current), []);
  const validScores = useMemo(() => (Array.isArray(scores) ? scores : []).filter(v => v !== null && v !== "").map(Number).filter(v => Number.isFinite(v) && v >= 0 && v <= 10), [scores]);
  const studentList = useMemo(() => rankStudents(sourceStudents), [sourceStudents]);
  const myId = currentStudentId(accountUser);
  const myStudent = studentList.find(student => student.id === myId);
  const topStudents = studentList.slice(0, 3);
  const nearby = useMemo(() => nearbyStudents(studentList, myId), [studentList, myId]);
  const visibleNearby = nearby.filter(student => normalize(`${student.name} ${student.id}`).includes(normalize(query)));
  const rankingHref = myId ? `/Xep_hang_Learner?studentId=${encodeURIComponent(myId)}` : "/Xep_hang_Learner";
  const allSkills = skillGroups.flatMap(group => group.skills);
  const strengths = STRONG_TITLES.map(title => allSkills.find(s => s.title === title)).filter(Boolean);
  const gaps = GAP_TITLES.map(title => allSkills.find(s => s.title === title)).filter(Boolean);
  function showNotification() {
    clearTimeout(timer.current);
    setNotice("Bạn chưa có thông báo mới.");
    timer.current = setTimeout(() => setNotice(""), 3000);
  }
  return (
    <div className="dbcas-learner-home dbcas-learner-evaluation">
      <header className="topbar"><div className="topbar-inner">
        <div className="brand"><span className="brand-icon"><Icon name="database" /></span><div><strong>Datamaster</strong><span>ASSESSMENT ENGINE</span></div></div>
        <nav className="main-nav" aria-label="Menu người học">
          <Link className="nav-link" to="/Home_Learner"><Icon name="home" /><span>Trang chủ</span></Link>
          <Link className="nav-link" to="/Bai_kiem_tra_Learner"><Icon name="file" /><span>Bài kiểm tra</span></Link>
          <Link className="nav-link active" to="/Xem_danh_gia_Learner" aria-current="page"><Icon name="chart" /><span>Xem đánh giá</span></Link>
          <Link className="nav-link" to="/Cai_dat_Learner"><Icon name="settings" /><span>Cài đặt</span></Link>
        </nav>
        <div className="toolbar-actions"><button type="button" className="notification-button" aria-label="Thông báo" onClick={showNotification}><Icon name="bell" /><span className="notification-dot" /></button><Link className="profile" to="/Cai_dat_Learner"><span className="avatar">{learner.initials}</span><span className="profile-info"><strong>{learner.name}</strong><span>{learner.email}</span></span></Link></div>
      </div></header>
      <section className="de-hero">
        <video className="de-background-video" autoPlay muted loop playsInline poster={poster} aria-hidden="true"><source src={video} type="video/mp4" /></video>
        <div className="de-hero-overlay" />
        <div className="container de-hero-content">
          <span className="de-eyebrow"><Icon name="trend" />PHÂN TÍCH CHUYÊN SÂU NĂNG LỰC CSDL &amp; CHUẨN HÓA</span>
          <h1>Trung tâm Phân tích &amp; Báo cáo Năng lực Cơ sở dữ liệu</h1>
          <p className="de-hero-description">Đánh giá tổng hợp qua các bài kiểm tra.</p>
          <ScoreChart scores={validScores} />
          <section className="de-groups-panel">
            <div className="de-panel-heading"><h2><Icon name="groups" />3 Phân Nhóm &amp; {allSkills.length} Tiêu chí Năng lực CSDL</h2><span className="de-scale">Thang điểm 10</span></div>
            <div className="de-groups">{skillGroups.map(group => <article className={`de-group ${group.tone}`} key={group.title}><div className="de-group-heading"><h3>{group.tone === "rose" ? <Icon name="warning" /> : <i />}{group.title}</h3><strong>{mean(group.skills.map(s => s.score)).toFixed(1)} / 10</strong></div><div className="de-group-track"><span style={{ width: `${mean(group.skills.map(s => s.score)) * 10}%` }} /></div><ul>{group.skills.map(skill => <li key={skill.title}><span>{skill.title}</span><strong className={skill.score < 6 ? "danger" : skill.score < 7 ? "warning" : ""}>{skill.score.toFixed(1)} / 10{skill.score < 6 && " [Cảnh báo]"}</strong></li>)}</ul></article>)}</div>
          </section>
        </div>
      </section>
      <main className="container de-main">
        <div className="de-section-heading"><span className="de-eyebrow light"><Icon name="chart" />HỆ THỐNG PHÂN TÍCH NĂNG LỰC HỌC TẬP</span><h2>Phân tích Năng lực &amp; Đề xuất Cải thiện</h2><p>Bóc tách dữ liệu từ câu hỏi truy vấn và bài tập thiết kế lược đồ quan hệ. Hệ thống tự động phân loại điểm mạnh kỹ thuật và phát hiện các điểm nghẽn kiến thức cần củng cố ngay.</p></div>
        <div className="de-analysis-columns">
          <section className="de-white-panel"><div className="de-column-heading"><span className="de-status-icon good"><Icon name="check" /></span><div><h3>Điểm Mạnh Kỹ Thuật (Strengths)</h3><p>{strengths.length} kỹ năng đạt mức độ thành thạo cao</p></div><span className="de-success-badge">XUẤT SẮC</span></div><div className="de-skill-stack">{strengths.map(skill => <SkillCard key={skill.title} skill={skill} />)}</div></section>
          <section className="de-white-panel"><div className="de-column-heading"><span className="de-status-icon bad"><Icon name="warning" /></span><div><h3>Lỗ Hổng Kiến Thức Cốt Lõi</h3><p>{gaps.length} nội dung cần ưu tiên cải thiện và bù khuyết</p></div></div><div className="de-skill-stack">{gaps.map(skill => <SkillCard key={skill.title} skill={skill} />)}</div></section>
        </div>
        <section className="de-white-panel de-guidance"><div className="de-guidance-heading"><span className="de-ai-icon"><Icon name="sparkles" /></span><div><h3>Nhận xét &amp; Lời khuyên Học tập từ Trợ lý AI</h3><p>Hệ thống đối chiếu kết quả với lộ trình đào tạo: Bạn đã làm chủ tốt nhóm SQL Querying ({mean(skillGroups[0].skills.map(s => s.score)).toFixed(1)} / 10) và Data Manipulation &amp; DDL ({mean(skillGroups[1].skills.map(s => s.score)).toFixed(1)} / 10) với kỹ năng viết câu lệnh tối ưu. Tuy nhiên, nhóm Constraints &amp; Design ({mean(skillGroups[2].skills.map(s => s.score)).toFixed(1)} / 10) đang là lỗ hổng cốt lõi kéo giảm thành tích tổng thể. Dưới đây là các chủ điểm lý thuyết và kỹ năng tư duy CSDL bạn cần ưu tiên học lại và củng cố ngay:</p></div></div><div className="de-guidance-grid">{GUIDANCE.map((item, i) => <article className="de-guidance-card" key={item.title}><span className={`de-priority ${i === 2 ? "amber" : ""}`}><b>{i + 1}</b>CHỦ ĐIỂM CẦN HỌC LẠI</span><h4>{item.title}</h4><p>{item.text}</p><div className="de-focus"><Icon name="bulb" /><span>Trọng tâm: {item.focus}</span></div></article>)}</div><div className="de-study-tip"><Icon name="bulb" /><p><strong>Lời khuyên từ Trợ lý AI:</strong> Bạn nên dành khoảng 2–3 giờ xem lại giáo trình phần Lý thuyết Lược đồ quan hệ và lấy tay giải lại các ví dụ về phân rã 3NF/BCNF trước khi bước vào các bài kiểm tra thực hành tiếp theo. Khi vững phần phụ thuộc hàm, điểm số của bạn có thể cải thiện 1.5–2.0 điểm.</p></div></section>
        <section className="de-white-panel de-ranking de-ranking-summary">
          <div className="de-ranking-heading">
            <h2><Icon name="list" />Bảng Xếp Hạng</h2>
            <p>Top 3 luôn hiển thị khi cuộn trong bảng. Xem các sinh viên có thứ hạng gần bạn.</p>
          </div>
          <div className="de-ranking-toolbar">
            <div className="de-ranking-account">
              <span className="de-student-count"><Icon name="users" />Tổng số: {studentList.length.toLocaleString("en-US")} sinh viên</span>
              {myStudent ? <span className="de-my-rank-info">Hạng của bạn: <strong>#{myStudent.rank}</strong></span> : <span className="de-rank-unavailable">Chưa tìm thấy thứ hạng của tài khoản hiện tại.</span>}
            </div>
            <label className="de-ranking-search"><Icon name="search" /><input type="search" value={query} placeholder="Tìm trong nhóm xếp hạng gần bạn..." aria-label="Tìm sinh viên trong nhóm xếp hạng gần bạn" onChange={event => setQuery(event.target.value)} /></label>
          </div>
          <div className="de-table-scroll de-ranking-window" tabIndex="0" aria-label="Cuộn bảng xếp hạng, Top 3 được giữ cố định">
            <table className="de-ranking-table">
              <thead><tr><th>Hạng</th><th>Họ và tên sinh viên</th><th>Ngành học</th><th>Bài hoàn thành</th><th>Tỷ lệ chuẩn (%)</th><th>Điểm TB (thang 10)</th><th>Danh hiệu</th></tr></thead>
              <tbody>
                {topStudents.map((student, index) => <StudentRankRow key={student.id} student={student} myId={myId} total={studentList.length} pinnedIndex={index} />)}
                {visibleNearby.map(student => <StudentRankRow key={student.id} student={student} myId={myId} total={studentList.length} />)}
                {!visibleNearby.length && <tr><td colSpan="7" className="de-empty">{myStudent ? "Không tìm thấy sinh viên phù hợp trong nhóm xếp hạng gần bạn." : "Chưa có dữ liệu xếp hạng của tài khoản hiện tại."}</td></tr>}
              </tbody>
            </table>
          </div>
          <div className="de-ranking-more">
            <Link to={rankingHref} state={{ user: accountUser ?? { ...learner, studentId: myId }, students: studentList }}>Xem toàn bộ danh sách {studentList.length.toLocaleString("en-US")} sinh viên<Icon name="arrow" /></Link>
          </div>
        </section>
      </main>
      <footer className="footer"><div className="container footer-inner"><p><strong>DBCAS</strong><span>•</span>Nền tảng tự động Đánh giá Năng lực CSDL</p><nav aria-label="Liên kết hỗ trợ"><Link to="/Quy_che">Quy chế khảo thí</Link><Link to="/Tai_lieu#chuan-hoa">Chuẩn hóa 3NF</Link><Link to="/Tai_lieu#sql">Tài liệu SQL</Link><Link to="/Ho_tro">Hỗ trợ</Link></nav></div></footer>
      {notice && <div className="de-notice" role="status">{notice}<button type="button" aria-label="Đóng thông báo" onClick={() => setNotice("")}>×</button></div>}
    </div>
  );
}
