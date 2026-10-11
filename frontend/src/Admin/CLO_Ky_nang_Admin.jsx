import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import "./Home_Admin.css";
import "./CLO_Ky_nang_Admin.css";

import background from "./SQL.jpg";
import logo from "./logo1.png";

const MAJORS = [
  "Kỹ thuật Phần mềm",
  "Khoa học Máy tính",
  "Hệ thống Thông tin Quản lý",
  "An ninh Mạng",
  "Công nghệ Phần mềm",
];

// Danh mục minh họa. Thay bằng dữ liệu BE khi kết nối.
const CLO_DATA = [
  {
    id: 1,
    title: "Kỹ năng truy vấn dữ liệu",
    subtitle: "SQL Querying",
    weight: 40,
    groups: [
      {
        title: "Thành phần 1: Truy vấn cơ bản",
        items: [
          { id: "select", name: "SELECT", hint: "Truy vấn các cột dữ liệu" },
          { id: "where", name: "WHERE", hint: "Lọc dòng theo điều kiện" },
          { id: "order", name: "ORDER BY", hint: "Sắp xếp ASC / DESC" },
          { id: "distinct", name: "DISTINCT", hint: "Loại bỏ kết quả trùng lặp" },
        ],
      },
      {
        title: "Thành phần 2: JOIN và gom nhóm",
        items: [
          { id: "join", name: "JOIN", hint: "INNER / LEFT / RIGHT JOIN" },
          { id: "group", name: "GROUP BY", hint: "Gom nhóm dữ liệu" },
          { id: "having", name: "HAVING", hint: "Lọc sau khi gom nhóm" },
          { id: "aggregate", name: "Aggregate", hint: "COUNT / SUM / AVG / MIN / MAX" },
        ],
      },
      {
        title: "Thành phần 3: Truy vấn nâng cao",
        items: [
          { id: "subquery", name: "Subqueries", hint: "Truy vấn lồng" },
          { id: "cte", name: "CTE", hint: "WITH / WITH RECURSIVE" },
          { id: "window", name: "Window Functions", hint: "OVER / PARTITION BY" },
          { id: "set", name: "Set Operations", hint: "UNION / INTERSECT / EXCEPT" },
        ],
      },
    ],
  },
  {
    id: 2,
    title: "Thao tác và định nghĩa dữ liệu",
    subtitle: "DML & DDL",
    weight: 30,
    groups: [
      {
        title: "Thành phần 1: Thao tác dữ liệu",
        items: [
          { id: "insert", name: "INSERT", hint: "Thêm bản ghi" },
          { id: "update", name: "UPDATE", hint: "Cập nhật dữ liệu" },
          { id: "delete", name: "DELETE", hint: "Xóa bản ghi theo điều kiện" },
          { id: "returning", name: "RETURNING", hint: "Trả về dữ liệu sau thao tác" },
        ],
      },
      {
        title: "Thành phần 2: Định nghĩa dữ liệu",
        items: [
          { id: "create", name: "CREATE TABLE", hint: "Tạo bảng dữ liệu" },
          { id: "alter", name: "ALTER TABLE", hint: "Thay đổi cấu trúc bảng" },
          { id: "drop", name: "DROP TABLE", hint: "Xóa bảng dữ liệu" },
          { id: "types", name: "Data Types", hint: "INTEGER / VARCHAR / DATE / NUMERIC" },
        ],
      },
      {
        title: "Thành phần 3: View và giao dịch",
        items: [
          { id: "view", name: "VIEW", hint: "Tạo và quản lý khung nhìn" },
          { id: "materialized", name: "Materialized View", hint: "Khung nhìn lưu kết quả" },
          { id: "transaction", name: "Transaction", hint: "BEGIN / COMMIT / ROLLBACK" },
          { id: "truncate", name: "TRUNCATE", hint: "Xóa toàn bộ dữ liệu trong bảng" },
        ],
      },
    ],
  },
  {
    id: 3,
    title: "Ràng buộc và thiết kế CSDL",
    subtitle: "Constraints & Design",
    weight: 30,
    groups: [
      {
        title: "Thành phần 1: Ràng buộc toàn vẹn",
        items: [
          { id: "pk", name: "PRIMARY KEY", hint: "Khóa chính của bảng" },
          { id: "fk", name: "FOREIGN KEY", hint: "Khóa ngoại liên kết các bảng" },
          { id: "unique", name: "UNIQUE", hint: "Đảm bảo giá trị không trùng lặp" },
          { id: "check", name: "CHECK / NOT NULL", hint: "Kiểm tra điều kiện và giá trị bắt buộc" },
        ],
      },
      {
        title: "Thành phần 2: Thiết kế dữ liệu",
        items: [
          { id: "entity", name: "Entity & Attribute", hint: "Xác định thực thể và thuộc tính" },
          { id: "relationship", name: "Relationships", hint: "Quan hệ 1–1 / 1–N / N–N" },
          { id: "erd", name: "ERD", hint: "Mô hình thực thể và liên kết" },
          { id: "schema", name: "Relational Schema", hint: "Chuyển mô hình ERD thành bảng" },
        ],
      },
      {
        title: "Thành phần 3: Chuẩn hóa và chỉ mục",
        items: [
          { id: "fd", name: "Functional Dependencies", hint: "Phụ thuộc hàm" },
          { id: "normal", name: "1NF / 2NF / 3NF", hint: "Các dạng chuẩn hóa dữ liệu" },
          { id: "bcnf", name: "BCNF", hint: "Dạng chuẩn Boyce–Codd" },
          { id: "index", name: "INDEX", hint: "Chỉ mục hỗ trợ truy xuất dữ liệu" },
        ],
      },
    ],
  },
];

const INITIAL_MAPPING = {
  1: [
    "select",
    "where",
    "order",
    "distinct",
    "join",
    "group",
    "having",
    "aggregate",
  ],
  2: [
    "insert",
    "update",
    "delete",
    "create",
    "alter",
    "drop",
    "types",
    "view",
  ],
  3: [
    "pk",
    "fk",
    "unique",
    "check",
    "entity",
    "relationship",
    "erd",
    "schema",
    "normal",
  ],
};

const DEMO_CLO_STATES = [
  ["pass", "pass", "pass"],
  ["pass", "pass", "weak"],
  ["weak", "pass", "weak"],
  ["pass", "weak", "pass"],
  ["weak", "weak", "weak"],
  ["weak", "pass", "pass"],
  ["pass", "weak", "weak"],
  ["weak", "weak", "pass"],
];

// Sinh viên giả để thử giao diện, không phải dữ liệu thật.
const DEMO_STUDENTS = Array.from({ length: 60 }, (_, index) => ({
  id: `DEMO${String(index + 1).padStart(5, "0")}`,
  name: `Sinh viên mẫu ${String(index + 1).padStart(2, "0")}`,
  email: `demo${index + 1}@example.com`,
  major: MAJORS[index % MAJORS.length],
  clos: [...DEMO_CLO_STATES[index % DEMO_CLO_STATES.length]],
}));

const PAGE_SIZE = 5;

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
    reset: "M3 11a9 9 0 1 1 2.6 7M3 4v7h7",
  };

  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[name] || paths.document} />
    </svg>
  );
}

function normalizeText(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

function getStudentStatus(student) {
  const states = student.clos ?? [];

  const hasCompleteResults =
    states.length >= 3 &&
    states.slice(0, 3).every(
      (state) => state === "pass" || state === "weak"
    );

  if (!hasCompleteResults) {
    return {
      key: "pending",
      label: "Chưa đủ kết quả",
      passedCount: null,
      className: "",
    };
  }

  const passedCount = states
    .slice(0, 3)
    .filter((state) => state === "pass").length;

  if (passedCount === 3) {
    return {
      key: "passed",
      label: "Đạt chuẩn (3/3 CLO)",
      passedCount,
      className: "status-pass",
    };
  }

  if (passedCount === 2) {
    return {
      key: "training",
      label: "Cần bồi dưỡng (2/3 CLO)",
      passedCount,
      className: "status-weak",
    };
  }

  return {
    key: "failed",
    label: `Chưa đạt (${passedCount}/3 CLO)`,
    passedCount,
    className: "status-weak",
  };
}

function getPageNumbers(current, total) {
  const items = [];

  for (let page = 1; page <= total; page += 1) {
    if (
      page === 1 ||
      page === total ||
      Math.abs(page - current) <= 1
    ) {
      const previous = items[items.length - 1];

      if (typeof previous === "number" && page - previous > 1) {
        items.push(`gap-${page}`);
      }

      items.push(page);
    }
  }

  return items;
}

/*
  Nối BE sau này:

  students: danh sách từ API, mỗi sinh viên có:
  { id, name, email, major, clos: ["pass", "weak", "pass"] }

  onSaveMapping({ cloId, conceptIds }): gọi API lưu ánh xạ.
  onViewStudent(student): mở chi tiết sinh viên.

  Hiện bộ lọc và phân trang chạy tại frontend.
*/
export default function CloKyNangAdmin({
  onLogout,
  onSaveMapping,
  onViewStudent,
  students = DEMO_STUDENTS,
}) {
  const navigate = useNavigate();

  const isDemo = students === DEMO_STUDENTS;
  const studentList = Array.isArray(students) ? students : [];

  const [selectedClo, setSelectedClo] = useState(3);
  const [draftMapping, setDraftMapping] = useState(INITIAL_MAPPING);
  const [savedMapping, setSavedMapping] = useState(INITIAL_MAPPING);

  const [query, setQuery] = useState("");
  const [major, setMajor] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const currentClo = CLO_DATA.find((clo) => clo.id === selectedClo);
  const concepts = currentClo.groups.flatMap((group) => group.items);
  const checkedIds = draftMapping[selectedClo];

  const hasChanges =
    [...checkedIds].sort().join("|") !==
    [...savedMapping[selectedClo]].sort().join("|");

  // Lọc tổng hợp cả 3 CLO, không phụ thuộc CLO đang chọn phía trên.
  const visible = studentList.filter((student) => {
    const text = normalizeText(
      `${student.name} ${student.id} ${student.email} ${student.major}`
    );

    const studentStatus = getStudentStatus(student);

    return (
      text.includes(normalizeText(query)) &&
      (!major || student.major === major) &&
      (!status || studentStatus.key === status)
    );
  });

  const totalPages = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);

  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const pageStudents = visible.slice(
    startIndex,
    startIndex + PAGE_SIZE
  );

  const firstRecord = visible.length === 0 ? 0 : startIndex + 1;
  const lastRecord = Math.min(
    startIndex + PAGE_SIZE,
    visible.length
  );

  const pageNumbers = getPageNumbers(currentPage, totalPages);

  function selectClo(id) {
    // Chỉ đổi phần ánh xạ; giữ nguyên bộ lọc và trang sinh viên.
    setSelectedClo(id);
  }

  function updateFilter(setter, value) {
    setter(value);
    setPage(1);
  }

  function toggleConcept(id, checked) {
    setDraftMapping((previous) => {
      const current = previous[selectedClo];

      return {
        ...previous,
        [selectedClo]: checked
          ? [...new Set([...current, id])]
          : current.filter((item) => item !== id),
      };
    });
  }

  function setAll(checked) {
    setDraftMapping((previous) => ({
      ...previous,
      [selectedClo]: checked
        ? concepts.map((item) => item.id)
        : [],
    }));
  }

  function restoreMapping() {
    setDraftMapping((previous) => ({
      ...previous,
      [selectedClo]: [...savedMapping[selectedClo]],
    }));
  }

  async function applyMapping() {
    if (saving || !hasChanges) return;

    const cloId = selectedClo;
    const conceptIds = [...checkedIds];

    setSaving(true);

    try {
      if (onSaveMapping) {
        await onSaveMapping({ cloId, conceptIds });
      }

      setSavedMapping((previous) => ({
        ...previous,
        [cloId]: conceptIds,
      }));

      setNotice(
        onSaveMapping
          ? `Đã lưu ánh xạ CLO ${cloId}.`
          : `Đã áp dụng CLO ${cloId} trong phiên hiện tại. Chưa lưu vào database.`
      );
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : "Không thể lưu ánh xạ."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    if (loggingOut) return;

    setLoggingOut(true);

    try {
      if (onLogout) await onLogout();
      navigate("/Dang_nhap");
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : "Không thể đăng xuất."
      );
    } finally {
      setLoggingOut(false);
    }
  }

  function resetFilters() {
    setQuery("");
    setMajor("");
    setStatus("");
    setPage(1);
  }

  function goToPage(nextPage) {
    setPage(Math.max(1, Math.min(nextPage, totalPages)));
  }

  function viewStudent(student) {
    if (onViewStudent) {
      onViewStudent(student);
    } else {
      setNotice(
        `Trang chi tiết của ${student.name} đang được hoàn thiện.`
      );
    }
  }

  return (
    <div
      className="dbcas-admin-home dbcas-clo-page"
      style={{
        backgroundImage: `linear-gradient(
          rgba(7,11,20,.85),
          rgba(7,11,20,.85)
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
              className="nav-link"
              to="/Danh_gia_nang_luc_Admin"
            >
              <Icon name="users" />
              <span>Đánh giá năng lực</span>
            </Link>

            <Link
              className="nav-link active"
              to="/CLO_Ky_nang_Admin"
              aria-current="page"
            >
              <Icon name="cap" />
              <span>CLO &amp; Kỹ năng</span>
              <span className="nav-dot" />
            </Link>

            <Link
              className="nav-link"
              to="/Quan_ly_bai_kiem_tra_Admin"
            >
              <Icon name="document" />
              <span>Quản lý bài kiểm tra</span>
            </Link>

            <Link
              className="nav-link"
              to="/Danh_gia_AI_Admin"
            >
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
            onClick={handleLogout}
            disabled={loggingOut}
          >
            <Icon name="logout" />
            <span>
              {loggingOut ? "Đang đăng xuất..." : "Đăng xuất"}
            </span>
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
            <input
              type="search"
              placeholder="Tìm kiếm sinh viên..."
              aria-label="Tìm kiếm sinh viên"
              value={query}
              onChange={(event) =>
                updateFilter(setQuery, event.target.value)
              }
            />
          </label>

          <button
            className="icon-button"
            type="button"
            aria-label="Trợ giúp"
            onClick={() =>
              setNotice(
                "Chọn CLO để chỉnh ánh xạ khái niệm. Bộ lọc trạng thái sinh viên xét tổng kết quả cả 3 CLO."
              )
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
        <section className="page-banner card">
          <h1>Quản lý Chuẩn đầu ra (CLO)</h1>
          <p>
            Thiết lập ma trận ánh xạ giữa chuẩn đầu ra học phần
            và khái niệm PostgreSQL để hỗ trợ chấm điểm,
            đánh giá năng lực.
          </p>
        </section>

        <div className="split-row">
          <section
            className="card"
            aria-labelledby="clo-list-title"
          >
            <div className="card-head clo-head">
              <div>
                <h2 id="clo-list-title">Danh sách CLO</h2>
                <p>Bấm vào một CLO để chỉnh ánh xạ bên phải.</p>
              </div>
              <span className="clo-badge cyan">3 CLO</span>
            </div>

            <div className="clo-list">
              {CLO_DATA.map((clo) => {
                const isSelected = selectedClo === clo.id;

                const savedConcepts = clo.groups
                  .flatMap((group) => group.items)
                  .filter((item) =>
                    savedMapping[clo.id].includes(item.id)
                  );

                return (
                  <button
                    key={clo.id}
                    type="button"
                    className={`clo-item ${
                      isSelected ? "is-selected" : ""
                    }`}
                    aria-pressed={isSelected}
                    aria-controls="clo-mapping-panel"
                    onClick={() => selectClo(clo.id)}
                    disabled={saving}
                  >
                    <span className="clo-meta">
                      <strong>CLO {clo.id}</strong>
                      <span
                        className={isSelected ? "text-cyan" : ""}
                      >
                        {isSelected
                          ? "Đang chọn"
                          : `Chiếm: ${clo.weight}%`}
                      </span>
                    </span>

                    <span className="clo-title">{clo.title}</span>
                    <span className="clo-subtitle">
                      {clo.subtitle}
                    </span>

                    <span className="chip-row">
                      {savedConcepts.slice(0, 5).map((item) => (
                        <span className="chip" key={item.id}>
                          {item.name}
                        </span>
                      ))}

                      {savedConcepts.length > 5 && (
                        <span className="chip">
                          +{savedConcepts.length - 5}
                        </span>
                      )}

                      {savedConcepts.length === 0 && (
                        <span className="chip">
                          Chưa có ánh xạ
                        </span>
                      )}
                    </span>

                    <span className="clo-foot">
                      Trọng số: {clo.weight}% ·{" "}
                      {savedConcepts.length} khái niệm đã áp dụng
                    </span>
                  </button>
                );
              })}
            </div>

            <p className="coverage">
              Tổng trọng số: <strong>100%</strong> · 3 CLO
            </p>
          </section>

          <section
            className="card"
            id="clo-mapping-panel"
            aria-labelledby="tree-title"
          >
            <div className="card-head tree-head">
              <div>
                <h2 id="tree-title">
                  Danh mục PostgreSQL &amp; Ánh xạ
                </h2>
                <p>
                  CLO {selectedClo} — {currentClo.title}.
                  {" "}Tích chọn khái niệm cần ánh xạ.
                </p>
              </div>

              <span className="clo-badge slate">
                {concepts.length} khái niệm
              </span>
            </div>

            {currentClo.groups.map((group) => {
              const linked = group.items.filter((item) =>
                checkedIds.includes(item.id)
              ).length;

              return (
                <div className="concept-group" key={group.title}>
                  <h3>
                    {group.title}
                    <span>
                      {linked}/{group.items.length} đã chọn
                    </span>
                  </h3>

                  {group.items.map((item) => (
                    <label className="concept" key={item.id}>
                      <input
                        type="checkbox"
                        checked={checkedIds.includes(item.id)}
                        disabled={saving}
                        onChange={(event) =>
                          toggleConcept(
                            item.id,
                            event.target.checked
                          )
                        }
                      />
                      <span>
                        {item.name}
                        <small>{item.hint}</small>
                      </span>
                    </label>
                  ))}
                </div>
              );
            })}

            <div className="map-bar">
              <div>
                <p>
                  Đã chọn: <strong>{checkedIds.length}</strong>
                  {" "}/ {concepts.length} khái niệm ·
                  {" "}CLO {selectedClo}
                </p>

                <small
                  className={
                    hasChanges ? "text-amber" : "text-muted"
                  }
                >
                  {hasChanges
                    ? "Có thay đổi chưa áp dụng"
                    : "Không có thay đổi mới"}
                </small>
              </div>

              <div className="map-actions">
                <button
                  className="btn-detail"
                  type="button"
                  onClick={() => setAll(true)}
                  disabled={saving}
                >
                  Chọn tất cả
                </button>

                <button
                  className="btn-detail"
                  type="button"
                  onClick={() => setAll(false)}
                  disabled={saving}
                >
                  Hủy chọn
                </button>

                <button
                  className="btn-detail"
                  type="button"
                  onClick={restoreMapping}
                  disabled={saving || !hasChanges}
                >
                  Khôi phục
                </button>

                <button
                  className="btn-detail btn-time"
                  type="button"
                  onClick={applyMapping}
                  disabled={saving || !hasChanges}
                >
                  {saving
                    ? "Đang lưu..."
                    : `Áp dụng CLO ${selectedClo}`}
                </button>
              </div>
            </div>
          </section>
        </div>

        <section
          className="card results"
          aria-labelledby="student-clo-title"
        >
          <div className="card-head">
            <h2 id="student-clo-title">
              Tra cứu Năng lực CLO theo Sinh viên
            </h2>
            <p>
              Theo dõi kết quả tổng hợp của cả 3 chuẩn đầu ra.
              {isDemo &&
                " Danh sách hiện sử dụng 60 sinh viên mẫu."}
            </p>
          </div>

          <div className="filter-row">
            <label className="search">
              <Icon name="search" />
              <input
                type="search"
                placeholder="Tìm họ tên, MSSV, email..."
                aria-label="Tìm sinh viên"
                value={query}
                onChange={(event) =>
                  updateFilter(setQuery, event.target.value)
                }
              />
            </label>

            <label className="year-filter">
              <select
                aria-label="Ngành đào tạo"
                value={major}
                onChange={(event) =>
                  updateFilter(setMajor, event.target.value)
                }
              >
                <option value="">Tất cả ngành</option>
                {MAJORS.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label className="year-filter">
              <select
                aria-label="Trạng thái tổng hợp CLO"
                value={status}
                onChange={(event) =>
                  updateFilter(setStatus, event.target.value)
                }
              >
                <option value="">Tất cả trạng thái</option>
                <option value="passed">
                  Đạt chuẩn (3/3 CLO)
                </option>
                <option value="training">
                  Cần bồi dưỡng (2/3 CLO)
                </option>
                <option value="failed">
                  Chưa đạt (0–1/3 CLO)
                </option>
              </select>
            </label>

            <button
              className="btn-detail reset-button"
              type="button"
              onClick={resetFilters}
            >
              <Icon name="reset" />
              Đặt lại
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Sinh viên / email</th>
                  <th scope="col">Mã SV</th>
                  <th scope="col">Ngành đào tạo</th>
                  <th scope="col">Trạng thái năng lực CLO</th>
                  <th scope="col">Thao tác</th>
                </tr>
              </thead>

              <tbody>
                {pageStudents.length === 0 && (
                  <tr>
                    <td colSpan={5} className="empty-state">
                      Không có sinh viên phù hợp với bộ lọc.
                    </td>
                  </tr>
                )}

                {pageStudents.map((student) => {
                  const studentStatus = getStudentStatus(student);

                  return (
                    <tr key={student.id}>
                      <td>
                        <div className="student">
                          <span className="student-avatar">
                            {String(student.name ?? "")
                              .split(" ")
                              .filter(Boolean)
                              .slice(-2)
                              .map((word) => word[0])
                              .join("")}
                          </span>
                          <div>
                            <strong>{student.name}</strong>
                            <small>{student.email}</small>
                          </div>
                        </div>
                      </td>

                      <td className="student-id">
                        {student.id}
                      </td>

                      <td>{student.major}</td>

                      <td>
                        <div className="clo-status">
                          {[0, 1, 2].map((index) => {
                            const state = student.clos?.[index];

                            return (
                              <span
                                key={index}
                                className={
                                  state === "pass"
                                    ? "status-pass"
                                    : state === "weak"
                                      ? "status-weak"
                                      : "chip"
                                }
                              >
                                CLO {index + 1}:{" "}
                                {state === "pass"
                                  ? "Đạt"
                                  : state === "weak"
                                    ? "Yếu"
                                    : "Chưa có"}
                              </span>
                            );
                          })}
                        </div>

                        <div style={{ marginTop: 8 }}>
                          <span
                            className={
                              studentStatus.className || "chip"
                            }
                          >
                            {studentStatus.label}
                          </span>
                        </div>
                      </td>

                      <td>
                        <button
                          className="btn-detail"
                          type="button"
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
              Hiển thị <strong>{firstRecord}–{lastRecord}</strong>
              {" "}trên <strong>{visible.length}</strong> sinh viên
              {" "}· Trang {currentPage}/{totalPages}
            </p>

            <nav
              className="pagination"
              aria-label="Phân trang sinh viên"
            >
              <button
                className="page-button"
                type="button"
                disabled={currentPage === 1}
                onClick={() => goToPage(currentPage - 1)}
              >
                Trước
              </button>

              {pageNumbers.map((item) =>
                typeof item === "number" ? (
                  <button
                    key={item}
                    className="page-button"
                    type="button"
                    aria-label={`Trang ${item}`}
                    aria-current={
                      item === currentPage ? "page" : undefined
                    }
                    onClick={() => goToPage(item)}
                    style={
                      item === currentPage
                        ? {
                            background: "#0891b2",
                            borderColor: "#22d3ee",
                            color: "#ffffff",
                          }
                        : undefined
                    }
                  >
                    {item}
                  </button>
                ) : (
                  <span
                    key={item}
                    className="page-info"
                    aria-hidden="true"
                  >
                    …
                  </span>
                )
              )}

              <button
                className="page-button"
                type="button"
                disabled={currentPage === totalPages}
                onClick={() => goToPage(currentPage + 1)}
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
          <button
            type="button"
            aria-label="Đóng thông báo"
            onClick={() => setNotice("")}
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}