import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import "./Home_Admin.css";
import "./Danh_gia_nang_luc_Admin.css";

import background from "./SQL.jpg";
import logo from "./logo1.png";

const MAJORS = [
  "Kỹ thuật Phần mềm",
  "Khoa học Máy tính",
  "Hệ thống Thông tin Quản lý",
  "An ninh Mạng",
  "Công nghệ Phần mềm",
];

const YEARS = [
  "2024-2025",
  "2025-2026",
  "2026-2027",
];

const PAGE_SIZE = 5;

const BASE_STUDENTS = [
  {
    id: "SV21020412",
    name: "Nguyễn Hoàng Long",
    email: "long.nh23@dtu.edu.vn",
    major: MAJORS[0],
    score: 9.5,
    cloCount: 3,
    strong: "CLO 1: CTE, Window Functions",
    weak: "CLO 3: Chuẩn hóa 3NF/BCNF",
  },
  {
    id: "SV21020389",
    name: "Trần Minh Thư",
    email: "thu.tm23@dtu.edu.vn",
    major: MAJORS[2],
    score: 9.0,
    cloCount: 3,
    strong: "CLO 1: Subqueries & JOIN",
    weak: "CLO 3: Ràng buộc FK & CHECK",
  },
  {
    id: "SV21020511",
    name: "Lê Quang Dũng",
    email: "dung.lq23@dtu.edu.vn",
    major: MAJORS[1],
    score: 7.5,
    cloCount: 2,
    strong: "CLO 2: INSERT, UPDATE",
    weak: "CLO 1: Window Functions & CTE",
  },
  {
    id: "SV21020294",
    name: "Phạm Thị Mai Anh",
    email: "anh.ptm23@dtu.edu.vn",
    major: MAJORS[3],
    score: 4.9,
    cloCount: 1,
    strong: "CLO 2: Cú pháp DDL cơ bản",
    weak: "CLO 1: Truy vấn đa bảng; CLO 3: PK/FK",
  },
  {
    id: "SV21020911",
    name: "Hoàng Đức Huy",
    email: "huy.hd23@dtu.edu.vn",
    major: MAJORS[0],
    score: 8.9,
    cloCount: 3,
    strong: "CLO 1: Truy vấn đa bảng",
    weak: "CLO 3: ERD và chuẩn hóa",
  },
];

// Dữ liệu minh họa để thử giao diện, không phải sinh viên thật.
const DEMO_STUDENTS = Array.from({ length: 60 }, (_, index) => {
  const base = BASE_STUDENTS[index % BASE_STUDENTS.length];

  if (index < BASE_STUDENTS.length) {
    return { ...base, year: "2024-2025" };
  }

  return {
    ...base,
    id: `DEMO${String(index + 1).padStart(5, "0")}`,
    name: `Sinh viên mẫu ${String(index + 1).padStart(2, "0")}`,
    email: `demo${index + 1}@example.com`,
    major: MAJORS[index % MAJORS.length],
    score: [9.5, 8.4, 7.2, 5.3, 9.0, 8.8, 6.5][index % 7],
    cloCount: [3, 2, 1][index % 3],
    year: YEARS[index % YEARS.length],
  };
});

function normalizeText(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

function scoreLevel(value) {
  if (value >= 9) return { name: "Xuất sắc", color: "green" };
  if (value >= 8) return { name: "Giỏi", color: "cyan" };
  if (value >= 6) return { name: "Khá", color: "slate" };
  return { name: "Cần ôn tập", color: "rose" };
}

function cloStatus(count) {
  if (count === 3) {
    return { name: "Đạt chuẩn (3/3 CLO)", color: "green" };
  }

  if (count === 2) {
    return { name: "Cần bồi dưỡng (2/3 CLO)", color: "amber" };
  }

  if (count === 1) {
    return { name: "Chưa đạt (1/3 CLO)", color: "rose" };
  }

  return { name: "Chưa đạt (0/3 CLO)", color: "rose" };
}

function matchesScore(value, filter) {
  if (!filter) return true;
  if (filter === "excellent") return value >= 9;
  if (filter === "good") return value >= 8 && value < 9;
  if (filter === "fair") return value >= 6 && value < 8;
  if (filter === "review") return value < 6;
  return false;
}

function getPageNumbers(current, total) {
  const items = [];

  for (let page = 1; page <= total; page += 1) {
    if (page === 1 || page === total || Math.abs(page - current) <= 1) {
      const previous = items[items.length - 1];

      if (typeof previous === "number" && page - previous > 1) {
        items.push(`gap-${page}`);
      }

      items.push(page);
    }
  }

  return items;
}

// Hàm giả lập API. Khi nối BE, thay bằng fetchStudents.
async function fetchDemoStudents(params) {
  const filtered = DEMO_STUDENTS.filter((student) => {
    const text = normalizeText(
      `${student.name} ${student.email} ${student.id} ${student.major}`
    );

    return (
      text.includes(normalizeText(params.query)) &&
      (!params.year || student.year === params.year) &&
      (!params.major || student.major === params.major) &&
      (!params.cloCount || student.cloCount === Number(params.cloCount)) &&
      matchesScore(student.score, params.scoreLevel)
    );
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / params.pageSize));
  const page = Math.min(params.page, totalPages);
  const start = (page - 1) * params.pageSize;

  return {
    items: filtered.slice(start, start + params.pageSize),
    total: filtered.length,
  };
}

function Icon({ name }) {
  const paths = {
    plus: "M12 5v14M5 12h14",
    home: "m3 10 9-7 9 7v10H3zM9 20v-7h6v7",
    users:
      "M12 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5",
    cap: "m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v7",
    document: "M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6",
    robot:
      "M5 7h14v13H5zM12 3v4M2 11v5M22 11v5M8 12h1M15 12h1M9 16h6",
    chart: "M4 3v17h17M8 16v-5M13 16V7M18 16V4",
    settings:
      "m9 3-1 3-3 1v4l-2 1 2 1v4l3 1 1 3h6l1-3 3-1v-4l2-1-2-1V7l-3-1-1-3zM15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0",
    logout: "M10 4H4v16h6M9 12h12M17 8l4 4-4 4",
    search: "M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0m-2 5 6 6",
    help:
      "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 2-2.5 3.5M12 16h.01",
    bell:
      "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
    chevron: "m8 5 7 7-7 7",
    calendar: "M3 5h18v16H3zM7 3v4M17 3v4M3 11h18",
    medal:
      "M17 8a5 5 0 1 1-10 0 5 5 0 0 1 10 0m-9 4-1 9 5-3 5 3-1-9",
    reset: "M3 11a9 9 0 1 1 2.6 7M3 4v7h7",
  };

  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[name] ?? paths.document} />
    </svg>
  );
}

const CLO_DATA = [
  {
    name: "CLO 1",
    title: "SQL Querying",
    weight: "40%",
    description: "Truy vấn dữ liệu.",
    value: 85.2,
  },
  {
    name: "CLO 2",
    title: "DML / DDL",
    weight: "30%",
    description: "Thao tác và định nghĩa dữ liệu.",
    value: 86.8,
  },
  {
    name: "CLO 3",
    title: "Ràng buộc & Thiết kế",
    weight: "30%",
    description: "Ràng buộc và thiết kế CSDL.",
    value: 78.3,
  },
];

/*
  Khi nối BE:
  fetchStudents({
    page, pageSize, query, year, major, cloCount, scoreLevel, signal
  }) phải trả về:
  {
    items: [{ id, name, email, major, score, cloCount, strong, weak }],
    total: tổng số sinh viên phù hợp với bộ lọc
  }

  BE xử lý bộ lọc và phân trang trước khi trả dữ liệu.
  summary và cloData dùng để truyền chỉ số tổng quan thật.
*/
export default function DanhGiaNangLucAdmin({
  onLogout,
  fetchStudents,
  onViewStudent,
  summary,
  cloData,
}) {
  const navigate = useNavigate();
  const isDemo = !fetchStudents;

  const [query, setQuery] = useState("");
  const [year, setYear] = useState("");
  const [major, setMajor] = useState("");
  const [status, setStatus] = useState("");
  const [score, setScore] = useState("");
  const [page, setPage] = useState(1);

  const [result, setResult] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);

  const totalPages = Math.max(1, Math.ceil(result.total / PAGE_SIZE));
  const pageNumbers = getPageNumbers(page, totalPages);

  const firstRecord = result.total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const lastRecord =
    result.total === 0 ? 0 : Math.min(page * PAGE_SIZE, result.total);

  const overview =
    summary ??
    (isDemo
      ? {
          averagePercent: 78.4,
          passed: 2412,
          notPassed: 433,
          passedPercent: 84.8,
          notPassedPercent: 15.2,
        }
      : null);

  const pillars = cloData ?? (isDemo ? CLO_DATA : null);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    // Chờ một chút để tránh gọi API liên tục khi gõ tìm kiếm.
    const timer = setTimeout(async () => {
      setLoading(true);
      setError("");

      try {
        const load = fetchStudents ?? fetchDemoStudents;

        const response = await load({
          page,
          pageSize: PAGE_SIZE,
          query: query.trim(),
          year,
          major,
          cloCount: status,
          scoreLevel: score,
          signal: controller.signal,
        });

        if (!active) return;

        if (
          !response ||
          !Array.isArray(response.items) ||
          !Number.isInteger(response.total) ||
          response.total < 0
        ) {
          throw new Error("Dữ liệu danh sách sinh viên không hợp lệ.");
        }

        const maxPage = Math.max(
          1,
          Math.ceil(response.total / PAGE_SIZE)
        );

        if (page > maxPage) {
          setPage(maxPage);
          return;
        }

        setResult(response);
      } catch (requestError) {
        if (!active || requestError.name === "AbortError") return;

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Không thể tải danh sách sinh viên."
        );
      } finally {
        if (active) setLoading(false);
      }
    }, 250);

    return () => {
      active = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [fetchStudents, page, query, year, major, status, score, retry]);

  function changeFilter(setter, value) {
    setter(value);
    setPage(1);
    setLoading(true);
  }

  function resetFilters() {
    setQuery("");
    setYear("");
    setMajor("");
    setStatus("");
    setScore("");
    setPage(1);
    setLoading(true);
  }

  function goToPage(next) {
    const nextPage = Math.max(1, Math.min(next, totalPages));

    if (nextPage !== page) {
      setLoading(true);
      setPage(nextPage);
    }
  }

  async function handleLogout() {
    if (loggingOut) return;

    setLoggingOut(true);

    try {
      if (onLogout) await onLogout();
      navigate("/Dang_nhap");
    } catch (logoutError) {
      setNotice(
        logoutError instanceof Error
          ? logoutError.message
          : "Không thể đăng xuất."
      );
    } finally {
      setLoggingOut(false);
    }
  }

  function viewStudent(student) {
    if (onViewStudent) {
      onViewStudent(student);
    } else {
      setNotice(`Trang chi tiết của ${student.name} đang được hoàn thiện.`);
    }
  }

  function radarPoint(index, percent) {
    const value = Math.max(0, Math.min(100, Number(percent))) / 100;
    const vertices = [
      [160, 30],
      [246.6, 180],
      [73.4, 180],
    ];

    return [
      160 + (vertices[index][0] - 160) * value,
      130 + (vertices[index][1] - 130) * value,
    ];
  }

  const radarPoints = pillars
    ? [
        radarPoint(0, pillars[0].value),
        radarPoint(1, pillars[1].value),
        radarPoint(2, pillars[2].value),
      ]
    : [];

  return (
    <div
      className="dbcas-admin-home dbcas-competency-page"
      style={{
        backgroundImage: `linear-gradient(
          rgba(7,11,20,.85), rgba(7,11,20,.85)
        ), url(${background})`,
      }}
    >
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

            <Link
              className="nav-link active"
              to="/Danh_gia_nang_luc_Admin"
              aria-current="page"
            >
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

            <a
              className="nav-link"
              href="#"
              onClick={(event) => {
                event.preventDefault();
                setNotice("Trang báo cáo đang được hoàn thiện.");
              }}
            >
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
          <button
            className="btn-logout"
            type="button"
            disabled={loggingOut}
            onClick={handleLogout}
          >
            <Icon name="logout" />
            <span>{loggingOut ? "Đang đăng xuất..." : "Đăng xuất"}</span>
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
            <input
              type="search"
              aria-label="Tìm kiếm sinh viên"
              placeholder="Tìm kiếm sinh viên..."
              value={query}
              onChange={(event) =>
                changeFilter(setQuery, event.target.value)
              }
            />
          </label>

          <button
            className="icon-button"
            type="button"
            aria-label="Trợ giúp"
            onClick={() =>
              setNotice("Chọn bộ lọc và số trang để xem kết quả sinh viên.")
            }
          >
            <Icon name="help" />
          </button>

          <button
            className="icon-button notification"
            type="button"
            aria-label="Thông báo"
            onClick={() => setNotice("Chưa có thông báo mới.")}
          >
            <Icon name="bell" />
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
        <section className="card page-banner">
          <div>
            <h1>Đánh giá năng lực sinh viên</h1>
            <p>
              Theo dõi 3 chuẩn đầu ra môn Cơ sở dữ liệu, phân tích
              năng lực và xác định kỹ năng cần bồi dưỡng.
            </p>
          </div>

          <label className="year-filter">
            <Icon name="calendar" />
            <select
              aria-label="Khóa học"
              value={year}
              onChange={(event) =>
                changeFilter(setYear, event.target.value)
              }
            >
              <option value="">Tất cả khóa</option>
              {YEARS.map((item) => (
                <option key={item} value={item}>
                  Khoá {item.replace("-", " - ")}
                </option>
              ))}
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
              {overview
                ? `Điểm trung bình ${(overview.averagePercent / 10).toFixed(2)}/10`
                : "Chưa có dữ liệu tổng quan"}
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
                {overview ? overview.passed.toLocaleString("en-US") : "—"}
              </strong>
              <span>SV</span>
            </div>
            <p>
              {overview
                ? `${overview.passedPercent}% tổng sinh viên · đạt 3/3 CLO`
                : "Chưa có dữ liệu tổng quan"}
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
                {overview
                  ? overview.notPassed.toLocaleString("en-US")
                  : "—"}
              </strong>
              <span>SV</span>
            </div>
            <p>
              {overview
                ? `${overview.notPassedPercent}% tổng sinh viên · cần bồi dưỡng`
                : "Chưa có dữ liệu tổng quan"}
            </p>
          </article>
        </section>

        <div className="insight-row">
          <section className="card radar-card">
            <div className="card-head">
              <h2>Biểu đồ radar 3 trụ cột chuẩn đầu ra</h2>
              <p>So sánh năng lực thực tế với mục tiêu 80%.</p>
            </div>

            {pillars ? (
              <>
                <div className="radar-stage">
                  <div className="axis-pill cyan">
                    CLO 1: SQL Querying
                    <strong>{pillars[0].value}%</strong>
                  </div>

                  <svg
                    viewBox="0 0 320 220"
                    role="img"
                    aria-label={`Radar: CLO 1 ${pillars[0].value}%, CLO 2 ${pillars[1].value}%, CLO 3 ${pillars[2].value}%`}
                  >
                    {[100, 80, 60, 40, 20].map((level) => (
                      <polygon
                        key={level}
                        points={[0, 1, 2]
                          .map((index) => radarPoint(index, level).join(","))
                          .join(" ")}
                        fill="none"
                        stroke={level === 80 ? "#94a3b8" : "#334155"}
                        strokeDasharray={level === 80 ? "5 4" : undefined}
                      />
                    ))}

                    {[0, 1, 2].map((index) => {
                      const point = radarPoint(index, 100);

                      return (
                        <line
                          key={index}
                          x1="160"
                          y1="130"
                          x2={point[0]}
                          y2={point[1]}
                          stroke="#334155"
                        />
                      );
                    })}

                    <polygon
                      points={radarPoints.map((point) => point.join(",")).join(" ")}
                      fill="#22d3ee33"
                      stroke="#22d3ee"
                      strokeWidth="2"
                    />

                    {radarPoints.map((point, index) => (
                      <circle
                        key={index}
                        cx={point[0]}
                        cy={point[1]}
                        r="4"
                        fill="#e2e8f0"
                        stroke={pillars[index].value < 80 ? "#fb7185" : "#22d3ee"}
                        strokeWidth="2"
                      />
                    ))}
                  </svg>

                  <div className="axis-row">
                    {[2, 1].map((index) => (
                      <div
                        key={pillars[index].name}
                        className={`axis-pill ${
                          pillars[index].value >= 80 ? "cyan" : "rose"
                        }`}
                      >
                        <span>
                          {pillars[index].name}: {pillars[index].title}
                          <strong>{pillars[index].value}%</strong>
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="radar-legend">
                    <span><i /> Năng lực thực tế</span>
                    <span><i className="target" /> Mục tiêu 80%</span>
                  </div>
                </div>

                <div className="radar-callouts">
                  <div className="callout green">
                    <span>CLO có điểm cao nhất</span>
                    <strong>
                      {[...pillars].sort((a, b) => b.value - a.value)[0].name}
                      {" · "}
                      {Math.max(...pillars.map((item) => item.value))}%
                    </strong>
                  </div>
                  <div className="callout rose">
                    <span>CLO có điểm thấp nhất</span>
                    <strong>
                      {[...pillars].sort((a, b) => a.value - b.value)[0].name}
                      {" · "}
                      {Math.min(...pillars.map((item) => item.value))}%
                    </strong>
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-panel">Chưa có dữ liệu radar.</div>
            )}
          </section>

          <section className="card matrix-card">
            <div className="card-head">
              <h2>Ma trận phân tích 3 chuẩn đầu ra</h2>
              <p>Mục tiêu đạt chuẩn: ≥80% cho từng CLO.</p>
            </div>

            <div className="clo-stack">
              {pillars ? pillars.map((item, index) => (
                <article className="clo-card" key={item.name}>
                  <header>
                    <h3>
                      Trục {index + 1} · {item.name} · {item.title}
                      {" "}({item.weight})
                    </h3>
                    <span className={`badge ${
                      item.value >= 80 ? "green" : "rose"
                    }`}>
                      {item.value >= 80 ? "Đạt chuẩn" : "Cần bồi dưỡng"}
                    </span>
                  </header>
                  <p>{item.description}</p>
                  <strong className={item.value >= 80 ? "text-cyan" : "text-rose"}>
                    {item.value}%
                  </strong>
                </article>
              )) : (
                <div className="empty-panel">Chưa có dữ liệu CLO.</div>
              )}

              <Link className="btn-detail" to="/CLO_Ky_nang_Admin">
                Xem chi tiết ma trận ánh xạ CLO &amp; Kỹ năng
              </Link>
            </div>
          </section>
        </div>

        <section className="card results">
          <div className="card-head">
            <h2>Danh sách sinh viên &amp; kết quả chi tiết</h2>
            <p>
              Tìm kiếm và lọc theo khóa, ngành, trạng thái CLO hoặc mức điểm.
              {isDemo && " Danh sách hiện sử dụng dữ liệu mẫu."}
            </p>
          </div>

          <div className="filter-row">
            <label className="search">
              <Icon name="search" />
              <input
                type="search"
                aria-label="Tìm sinh viên"
                placeholder="Tìm theo tên sinh viên, MSSV, email..."
                value={query}
                onChange={(event) =>
                  changeFilter(setQuery, event.target.value)
                }
              />
            </label>

            <label className="year-filter">
              <select
                aria-label="Ngành"
                value={major}
                onChange={(event) =>
                  changeFilter(setMajor, event.target.value)
                }
              >
                <option value="">Tất cả ngành</option>
                {MAJORS.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>

            <label className="year-filter">
              <select
                aria-label="Trạng thái CLO"
                value={status}
                onChange={(event) =>
                  changeFilter(setStatus, event.target.value)
                }
              >
                <option value="">Tất cả trạng thái CLO</option>
                <option value="3">Đạt chuẩn (3/3 CLO)</option>
                <option value="2">Cần bồi dưỡng (2/3 CLO)</option>
                <option value="1">Chưa đạt (1/3 CLO)</option>
              </select>
            </label>

            <label className="year-filter">
              <select
                aria-label="Mức điểm"
                value={score}
                onChange={(event) =>
                  changeFilter(setScore, event.target.value)
                }
              >
                <option value="">Tất cả mức điểm</option>
                <option value="excellent">Xuất sắc ≥9.0</option>
                <option value="good">Giỏi 8.0–8.9</option>
                <option value="fair">Khá 6.0–7.9</option>
                <option value="review">Cần ôn tập &lt;6.0</option>
              </select>
            </label>

            <button className="btn-detail reset-button" onClick={resetFilters} type="button">
              <Icon name="reset" />
              Đặt lại
            </button>
          </div>

          <div className="table-wrap" aria-busy={loading}>
            <table>
              <thead>
                <tr>
                  <th>Sinh viên</th>
                  <th>Mã SV &amp; ngành</th>
                  <th>Competency score</th>
                  <th>Điểm mạnh</th>
                  <th>Điểm yếu</th>
                  <th>Chuẩn CLO</th>
                  <th>Thao tác</th>
                </tr>
              </thead>

              <tbody>
                {loading ? (
                  <tr>
                    <td className="empty-state" colSpan={7} role="status">
                      Đang tải danh sách sinh viên...
                    </td>
                  </tr>
                ) : error ? (
                  <tr>
                    <td className="empty-state" colSpan={7}>
                      <p role="alert">{error}</p>
                      <button
                        type="button"
                        className="btn-detail"
                        onClick={() => {
                          setLoading(true);
                          setRetry((value) => value + 1);
                        }}
                      >
                        Thử lại
                      </button>
                    </td>
                  </tr>
                ) : result.items.length === 0 ? (
                  <tr>
                    <td className="empty-state" colSpan={7}>
                      Không có sinh viên phù hợp với bộ lọc.
                    </td>
                  </tr>
                ) : result.items.map((student) => {
                  const value = Number(student.score);
                  const level = scoreLevel(value);
                  const clo = cloStatus(Number(student.cloCount));
                  const initials = student.name
                    .split(" ")
                    .slice(-2)
                    .map((word) => word[0])
                    .join("");

                  return (
                    <tr key={student.id}>
                      <td>
                        <div className="student">
                          <span className="student-avatar">{initials}</span>
                          <div>
                            <strong>{student.name}</strong>
                            <small>{student.email}</small>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="student-id">{student.id}</span>
                        <small>{student.major}</small>
                      </td>
                      <td>
                        <div className="total-score">
                          <b>{value.toFixed(1)}</b>
                          <span>/10</span>
                          <span className={`badge ${level.color}`}>
                            {level.name}
                          </span>
                        </div>
                        <div className={`score-track ${level.color}`}>
                          <span style={{
                            width: `${Math.max(0, Math.min(100, value * 10))}%`,
                          }} />
                        </div>
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
                        <button
                          type="button"
                          className="btn-detail"
                          onClick={() => viewStudent(student)}
                        >
                          Xem chi tiết
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="pager">
            <p>
              {loading ? "Đang tải..." : error ? "Chưa tải được danh sách" : (
                <>
                  Hiển thị <strong>{firstRecord}–{lastRecord}</strong>
                  {" "}trên <strong>{result.total}</strong> sinh viên
                  <span className="pager-divider">·</span>
                  Trang <strong>{page}</strong> / <strong>{totalPages}</strong>
                </>
              )}
            </p>

            <nav className="pagination" aria-label="Phân trang sinh viên">
              <button
                type="button"
                className="page-button"
                disabled={loading || !!error || page === 1}
                onClick={() => goToPage(page - 1)}
              >
                Trước
              </button>

              {pageNumbers.map((item) =>
                typeof item === "number" ? (
                  <button
                    key={item}
                    type="button"
                    className={`page-button ${item === page ? "active" : ""}`}
                    aria-label={`Trang ${item}`}
                    aria-current={item === page ? "page" : undefined}
                    disabled={loading || !!error}
                    onClick={() => goToPage(item)}
                  >
                    {item}
                  </button>
                ) : (
                  <span key={item} className="page-ellipsis">…</span>
                )
              )}

              <button
                type="button"
                className="page-button"
                disabled={loading || !!error || page >= totalPages}
                onClick={() => goToPage(page + 1)}
              >
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

      {notice && (
        <div className="admin-notice" role="status">
          <span>{notice}</span>
          <button type="button" aria-label="Đóng thông báo" onClick={() => setNotice("")}>
            ×
          </button>
        </div>
      )}
    </div>
  );
}