import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import "./Home_Admin.css";
import "./Quan_ly_bai_kiem_tra_Admin.css";

import background from "./SQL.jpg";
import logo from "./logo1.png";

const STORAGE_KEY = "dbcas-exam-management-v1";
const PAGE_SIZE = 5;

const EXAM_TOPICS = [
  "Cơ sở dữ liệu và mô hình quan hệ",
  "Truy vấn SELECT, WHERE và ORDER BY",
  "Truy vấn JOIN nhiều bảng",
  "Gom nhóm GROUP BY và HAVING",
  "Truy vấn con và CTE",
  "Thao tác dữ liệu INSERT, UPDATE, DELETE",
  "Định nghĩa bảng và kiểu dữ liệu",
  "Ràng buộc PRIMARY KEY và FOREIGN KEY",
  "Thiết kế lược đồ ERD",
  "Chuẩn hóa dữ liệu 1NF, 2NF, 3NF",
  "Phụ thuộc hàm và chuẩn BCNF",
  "Chỉ mục và tối ưu truy vấn",
  "View và Stored Procedure",
  "Transaction và tính toàn vẹn dữ liệu",
  "Hàm tổng hợp và Window Function",
];

const EXAM_TYPES = [
  "Kiểm tra kiến thức",
  "Kiểm tra thực hành",
  "Đánh giá năng lực",
  "Kiểm tra giữa kỳ",
];

const START_TIMES = ["08:00", "09:30", "13:00", "14:30", "15:30"];
const DURATIONS = [45, 60, 75, 90];

// Dữ liệu mẫu: 27 bài đã công bố và 13 bản nháp.
const DEMO_EXAMS = Array.from({ length: 40 }, (_, index) => {
  const number = index + 1;
  const isDraft = number % 3 === 0;
  const day = String((index % 28) + 1).padStart(2, "0");
  const month = index < 28 ? "10" : "11";

  return {
    id: `DEMO-EXAM-${String(number).padStart(3, "0")}`,
    title: `${EXAM_TYPES[index % EXAM_TYPES.length]}: ${
      EXAM_TOPICS[index % EXAM_TOPICS.length]
    } — Đợt ${Math.floor(index / EXAM_TOPICS.length) + 1}`,
    status: isDraft ? "draft" : "published",
    date: isDraft ? "" : `2026-${month}-${day}`,
    startTime: isDraft ? "" : START_TIMES[index % START_TIMES.length],
    duration: DURATIONS[index % DURATIONS.length],
    mcqCount: 10,
    sqlCount: 3,
    essayCount: 1,
  };
});

const NAV_ITEMS = [
  ["home", "Trang chủ", "/Home_Admin"],
  ["users", "Đánh giá năng lực", "/Danh_gia_nang_luc_Admin"],
  ["cap", "CLO & Kỹ năng", "/CLO_Ky_nang_Admin"],
  ["document", "Quản lý bài kiểm tra", "/Quan_ly_bai_kiem_tra_Admin"],
  ["robot", "Đánh giá bằng AI", "/Danh_gia_AI_Admin"],
];

function Icon({ name }) {
  const paths = {
    plus: "M12 5v14M5 12h14",
    home: "m3 10 9-7 9 7v10H3zM9 20v-7h6v7",
    users:
      "M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5.65",
    cap: "m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v7",
    document: "M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6",
    robot:
      "M4 7h16v13H4zM12 3v4M2 11v5M22 11v5M8 12h1M15 12h1M9 16h6",
    chart: "M4 3v17h17M8 16v-5M13 16V7M18 16V4",
    settings:
      "m9 3-1 3-3 1v4l-2 1 2 1v4l3 1 1 3h6l1-3 3-1v-4l2-1-2-1V7l-3-1-1-3z",
    logout: "M10 4H4v16h6M9 12h12M17 8l4 4-4 4",
    search: "m16 16 5 5",
    help: "M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 2-2.5 3.5M12 16h.01",
    bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
    chevron: "m8 5 7 7-7 7",
    clock: "M12 7v5l3 2",
    close: "m6 6 12 12M18 6 6 18",
  };

  return (
    <svg
      className="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name] || paths.document} />

      {name === "users" && <circle cx="9" cy="7" r="3" />}
      {name === "search" && <circle cx="10.5" cy="10.5" r="6.5" />}
      {["help", "clock"].includes(name) && (
        <circle cx="12" cy="12" r="9" />
      )}
      {name === "settings" && <circle cx="12" cy="12" r="3" />}
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

function isValidDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;

  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(0);

  date.setFullYear(year, month - 1, day);
  date.setHours(0, 0, 0, 0);

  return (
    date.getFullYear() === year &&
    date.getMonth() === month - 1 &&
    date.getDate() === day
  );
}

function formatDate(value) {
  if (!value || !isValidDate(value)) return "Chưa chọn ngày";

  const [year, month, day] = value.split("-");
  return `${day}/${month}/${year}`;
}

function getEndTime(startTime, duration) {
  if (!/^\d{2}:\d{2}$/.test(startTime)) return null;

  const minutes = Number(duration);
  const [hour, minute] = startTime.split(":").map(Number);

  if (
    !Number.isInteger(minutes) ||
    minutes < 1 ||
    minutes > 600 ||
    hour > 23 ||
    minute > 59
  ) {
    return null;
  }

  const total = hour * 60 + minute + minutes;
  const endHour = Math.floor((total % 1440) / 60);
  const endMinute = total % 60;

  return {
    time: `${String(endHour).padStart(2, "0")}:${String(
      endMinute
    ).padStart(2, "0")}`,
    nextDay: total >= 1440,
  };
}

function validateSchedule(form) {
  if (!form.date || !form.startTime) {
    return "Vui lòng chọn ngày thi và giờ bắt đầu.";
  }

  if (!isValidDate(form.date)) {
    return "Ngày thi không hợp lệ.";
  }

  const duration = Number(form.duration);

  if (!Number.isInteger(duration) || duration < 1 || duration > 600) {
    return "Thời lượng phải là số nguyên từ 1 đến 600 phút.";
  }

  if (!getEndTime(form.startTime, duration)) {
    return "Giờ bắt đầu không hợp lệ.";
  }

  return "";
}

function readSchedules() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    const schedules = parsed?.schedules;

    if (
      !schedules ||
      typeof schedules !== "object" ||
      Array.isArray(schedules)
    ) {
      return {};
    }

    return Object.fromEntries(
      Object.entries(schedules).filter(
        ([, schedule]) =>
          schedule &&
          typeof schedule === "object" &&
          !validateSchedule(schedule)
      )
    );
  } catch {
    return {};
  }
}

function persistSchedules(schedules) {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ schedules })
  );
}

function getPageNumbers(currentPage, totalPages) {
  const pages = Array.from(
    new Set([
      1,
      totalPages,
      currentPage - 1,
      currentPage,
      currentPage + 1,
    ])
  )
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((a, b) => a - b);

  const result = [];

  pages.forEach((page, index) => {
    if (index > 0 && page - pages[index - 1] > 1) {
      result.push(`gap-${page}`);
    }

    result.push(page);
  });

  return result;
}

export default function QuanLyBaiKiemTraAdmin({
  onLogout,
  onSaveSchedule,
  onViewExam,
  onEditExam,
  exams: sourceExams = DEMO_EXAMS,
}) {
  const navigate = useNavigate();

  const isDemo = sourceExams === DEMO_EXAMS;
  const examList = Array.isArray(sourceExams) ? sourceExams : [];

  const [localSchedules, setLocalSchedules] = useState(readSchedules);
  const [sessionSchedules, setSessionSchedules] = useState({});

  const [activeTab, setActiveTab] = useState("published");
  const [queries, setQueries] = useState({
    published: "",
    draft: "",
  });
  const [pages, setPages] = useState({
    published: 1,
    draft: 1,
  });

  const [notice, setNotice] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);

  const [editingExam, setEditingExam] = useState(null);
  const [form, setForm] = useState({
    date: "",
    startTime: "",
    duration: 60,
  });
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const dialogRef = useRef(null);
  const dateInputRef = useRef(null);
  const triggerRef = useRef(null);
  const savingRef = useRef(false);

  const publishedTabRef = useRef(null);
  const draftTabRef = useRef(null);

  const query = queries[activeTab];

  const displayedExams = examList.map((exam) => {
    const schedule = isDemo
      ? localSchedules[exam.id]
      : sessionSchedules[exam.id];

    return schedule
      ? {
          ...exam,
          date: schedule.date,
          startTime: schedule.startTime,
          duration: Number(schedule.duration),
        }
      : exam;
  });

  const publishedCount = displayedExams.filter(
    (exam) => exam.status === "published"
  ).length;

  const draftCount = displayedExams.filter(
    (exam) => exam.status === "draft"
  ).length;

  const currentTabCount =
    activeTab === "published" ? publishedCount : draftCount;

  const visible = displayedExams.filter((exam) => {
    const matchesSearch = normalizeText(
      `${exam.title} ${exam.id}`
    ).includes(normalizeText(query));

    return exam.status === activeTab && matchesSearch;
  });

  const totalPages = Math.max(
    1,
    Math.ceil(visible.length / PAGE_SIZE)
  );

  const currentPage = Math.min(
    pages[activeTab],
    totalPages
  );

  const startIndex = (currentPage - 1) * PAGE_SIZE;

  const paginatedExams = visible.slice(
    startIndex,
    startIndex + PAGE_SIZE
  );

  const firstRecord =
    visible.length === 0 ? 0 : startIndex + 1;

  const lastRecord = Math.min(
    startIndex + PAGE_SIZE,
    visible.length
  );

  const pageNumbers = getPageNumbers(
    currentPage,
    totalPages
  );

  const endTime = getEndTime(
    form.startTime,
    form.duration
  );

  useEffect(() => {
    if (!editingExam) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dateInputRef.current?.focus();

    function handleKeyDown(event) {
      if (event.key === "Escape" && !savingRef.current) {
        setEditingExam(null);
        return;
      }

      if (event.key !== "Tab") return;

      const elements = Array.from(
        dialogRef.current?.querySelectorAll(
          "button:not(:disabled), input:not(:disabled)"
        ) || []
      );

      const first = elements[0];
      const last = elements[elements.length - 1];

      if (!first) {
        event.preventDefault();
        dialogRef.current?.focus();
        return;
      }

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      triggerRef.current?.focus();
    };
  }, [editingExam]);

  function changeTab(tab, focusTab = false) {
    setActiveTab(tab);

    if (focusTab) {
      if (tab === "published") {
        publishedTabRef.current?.focus();
      } else {
        draftTabRef.current?.focus();
      }
    }
  }

  function handleTabKeyDown(event, tab) {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();

      changeTab(
        tab === "published" ? "draft" : "published",
        true
      );
    } else if (event.key === "Home") {
      event.preventDefault();
      changeTab("published", true);
    } else if (event.key === "End") {
      event.preventDefault();
      changeTab("draft", true);
    }
  }

  function updateQuery(value) {
    setQueries((current) => ({
      ...current,
      [activeTab]: value,
    }));

    setPages((current) => ({
      ...current,
      [activeTab]: 1,
    }));
  }

  function goToPage(page) {
    const nextPage = Math.max(
      1,
      Math.min(page, totalPages)
    );

    setPages((current) => ({
      ...current,
      [activeTab]: nextPage,
    }));
  }

  function openEditor(exam, event) {
    triggerRef.current = event.currentTarget;

    setForm({
      date: exam.date || "",
      startTime: exam.startTime || "",
      duration: exam.duration ?? 60,
    });

    setFormError("");
    setEditingExam(exam);
  }

  function closeEditor() {
    if (!savingRef.current) {
      setEditingExam(null);
    }
  }

  function updateForm(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));

    setFormError("");
  }

  async function saveSchedule(event) {
    event.preventDefault();

    if (savingRef.current || !editingExam) return;

    const error = validateSchedule(form);

    if (error) {
      setFormError(error);
      return;
    }

    if (!isDemo && !onSaveSchedule) {
      setFormError("Chưa kết nối API lưu thời gian thi.");
      return;
    }

    const examId = editingExam.id;

    const schedule = {
      date: form.date,
      startTime: form.startTime,
      duration: Number(form.duration),
    };

    savingRef.current = true;
    setSaving(true);
    setFormError("");

    try {
      if (onSaveSchedule) {
        await onSaveSchedule(examId, schedule);
      }

      let storedLocally = true;

      if (isDemo) {
        const nextSchedules = {
          ...localSchedules,
          [examId]: schedule,
        };

        try {
          persistSchedules(nextSchedules);
        } catch {
          storedLocally = false;
        }

        setLocalSchedules(nextSchedules);
      } else {
        setSessionSchedules((current) => ({
          ...current,
          [examId]: schedule,
        }));
      }

      setEditingExam(null);

      setNotice(
        onSaveSchedule
          ? "Đã lưu thời gian thi."
          : storedLocally
            ? "Đã lưu thời gian thi trong trình duyệt."
            : "Đã cập nhật trong phiên hiện tại, nhưng không lưu được khi tải lại trang."
      );
    } catch (error) {
      setFormError(
        error instanceof Error
          ? error.message
          : "Không thể lưu thời gian thi."
      );
    } finally {
      savingRef.current = false;
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

  async function openExam(exam) {
    try {
      if (exam.status === "draft") {
        if (onEditExam) {
          await onEditExam(exam);
        } else {
          setNotice(
            "Chưa kết nối chức năng mở lại nội dung đề đang soạn."
          );
        }
      } else if (onViewExam) {
        await onViewExam(exam);
      } else {
        setNotice(
          "Chưa kết nối trang xem chi tiết bài kiểm tra."
        );
      }
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : "Không thể mở bài kiểm tra."
      );
    }
  }

  return (
    <div
      className="dbcas-admin-home dbcas-exam-page"
      style={{
        backgroundImage: `linear-gradient(rgba(7,11,20,.8), rgba(7,11,20,.8)), url(${background})`,
      }}
    >
      <aside className="sidebar">
        <div className="sidebar-content">
          <div className="sidebar-brand">
            <img
              src={logo}
              alt="Logo DBCAS"
              draggable="false"
            />
          </div>

          <Link className="btn-new" to="/TN_Admin">
            <Icon name="plus" />
            <span>Tạo bài kiểm tra</span>
          </Link>

          <nav
            className="sidebar-nav"
            aria-label="Menu quản trị"
          >
            {NAV_ITEMS.map(([icon, label, path]) => {
              const active =
                path === "/Quan_ly_bai_kiem_tra_Admin";

              return (
                <Link
                  key={path}
                  className={`nav-link${active ? " active" : ""}`}
                  to={path}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon name={icon} />
                  <span>{label}</span>
                  {active && <span className="nav-dot" />}
                </Link>
              );
            })}

            <button
              className="nav-link"
              type="button"
              onClick={() =>
                setNotice("Trang báo cáo chưa được kết nối.")
              }
            >
              <Icon name="chart" />
              <span>Báo cáo</span>
            </button>

            <Link
              className="nav-link"
              to="/Cai_dat_Admin"
            >
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
          <strong>Quản lý bài kiểm tra</strong>
        </div>

        <div className="topbar-actions">
          <label className="search top-search">
            <Icon name="search" />

            <input
              type="search"
              placeholder="Tìm bài kiểm tra..."
              aria-label="Tìm bài kiểm tra trong tab hiện tại"
              value={query}
              onChange={(event) =>
                updateQuery(event.target.value)
              }
            />
          </label>

          <button
            className="icon-button"
            type="button"
            aria-label="Trợ giúp"
            onClick={() =>
              setNotice(
                "Đề đã công bố và bản nháp nằm ở hai tab riêng. Mỗi trang hiển thị 5 bài kiểm tra."
              )
            }
          >
            <Icon name="help" />
          </button>

          <button
            className="icon-button notification"
            type="button"
            aria-label="Thông báo"
            onClick={() =>
              setNotice("Chưa có thông báo mới.")
            }
          >
            <Icon name="bell" />
          </button>

          <Link
            className="profile"
            to="/Cai_dat_Admin"
          >
            <span className="profile-avatar">AD</span>

            <span className="profile-text">
              <strong>Admin System</strong>
              <small>admin@dbcas.edu.vn</small>
            </span>
          </Link>
        </div>
      </header>

      <main className="main">
        <section
          className="page-banner card"
          aria-labelledby="exam-title"
        >
          <div>
            <span className="banner-label">
              QUẢN TRỊ ĐÁNH GIÁ
            </span>

            <h1 id="exam-title">
              Quản lý bài kiểm tra
            </h1>

            <p>
              Quản lý bài kiểm tra đã công bố, điều chỉnh lịch thi
              và tiếp tục soạn các đề trong mục bản nháp.
            </p>
          </div>

          <Link
            className="btn-banner"
            to="/TN_Admin"
          >
            <Icon name="plus" />
            Tạo bài kiểm tra
          </Link>
        </section>

        <section
          className="card results"
          aria-label="Quản lý danh sách bài kiểm tra"
        >
          <div
            className="exam-tabs"
            role="tablist"
            aria-label="Loại danh sách bài kiểm tra"
          >
            <button
              ref={publishedTabRef}
              id="published-tab"
              className={`exam-tab ${
                activeTab === "published"
                  ? "is-active"
                  : ""
              }`}
              type="button"
              role="tab"
              aria-selected={activeTab === "published"}
              aria-controls="exam-panel"
              tabIndex={activeTab === "published" ? 0 : -1}
              onClick={() => changeTab("published")}
              onKeyDown={(event) =>
                handleTabKeyDown(event, "published")
              }
            >
              <Icon name="document" />
              Đã công bố
              <span className="tab-count">
                {publishedCount}
              </span>
            </button>

            <button
              ref={draftTabRef}
              id="draft-tab"
              className={`exam-tab ${
                activeTab === "draft"
                  ? "is-active"
                  : ""
              }`}
              type="button"
              role="tab"
              aria-selected={activeTab === "draft"}
              aria-controls="exam-panel"
              tabIndex={activeTab === "draft" ? 0 : -1}
              onClick={() => changeTab("draft")}
              onKeyDown={(event) =>
                handleTabKeyDown(event, "draft")
              }
            >
              <Icon name="document" />
              Bản nháp
              <span className="tab-count">
                {draftCount}
              </span>
            </button>
          </div>

          <div
            id="exam-panel"
            role="tabpanel"
            aria-labelledby={
              activeTab === "published"
                ? "published-tab"
                : "draft-tab"
            }
            tabIndex={0}
          >
            <div className="exam-list-head">
              <div>
                <h2>
                  {activeTab === "published"
                    ? "Bài kiểm tra đã công bố"
                    : "Bản nháp bài kiểm tra"}
                </h2>

                <p>
                  {isDemo ? "Dữ liệu mẫu • " : ""}
                  {activeTab === "published"
                    ? "Các đề đã công bố cho sinh viên."
                    : "Các đề đang soạn, chưa công bố cho sinh viên."}
                </p>
              </div>

              <span className="exam-count">
                <strong>{currentTabCount}</strong>
                {" "}bài kiểm tra
              </span>
            </div>

            <div className="exam-toolbar">
              <label className="search result-search">
                <Icon name="search" />

                <input
                  type="search"
                  placeholder={
                    activeTab === "published"
                      ? "Tìm bài kiểm tra đã công bố..."
                      : "Tìm bản nháp..."
                  }
                  aria-label="Tìm tên hoặc mã bài kiểm tra"
                  value={query}
                  onChange={(event) =>
                    updateQuery(event.target.value)
                  }
                />
              </label>

              <span className="filter-count">
                {visible.length} kết quả
              </span>
            </div>

            <div className="table-wrap exam-table">
              <table>
                <colgroup>
                  <col className="col-title" />
                  <col className="col-structure" />
                  <col className="col-schedule" />
                  <col className="col-actions" />
                </colgroup>

                <thead>
                  <tr>
                    <th scope="col">
                      {activeTab === "published"
                        ? "Bài kiểm tra"
                        : "Đề đang soạn"}
                    </th>

                    <th scope="col">
                      Cấu trúc đề
                    </th>

                    <th scope="col">
                      {activeTab === "published"
                        ? "Thời gian & lịch thi"
                        : "Lịch thi dự kiến"}
                    </th>

                    <th scope="col">
                      Thao tác
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {visible.length === 0 && (
                    <tr>
                      <td
                        colSpan={4}
                        className="empty-state"
                      >
                        {query.trim()
                          ? "Không tìm thấy bài kiểm tra phù hợp."
                          : activeTab === "published"
                            ? "Chưa có bài kiểm tra đã công bố."
                            : "Chưa có bản nháp bài kiểm tra."}
                      </td>
                    </tr>
                  )}

                  {paginatedExams.map((exam) => {
                    const end = getEndTime(
                      exam.startTime,
                      exam.duration
                    );

                    const isDraft =
                      exam.status === "draft";

                    return (
                      <tr key={exam.id}>
                        <td>
                          <strong className="exam-name">
                            {exam.title}
                          </strong>

                          <div className="exam-meta">
                            <span>{exam.id}</span>

                            <span
                              className={`exam-badge ${
                                isDraft
                                  ? "badge-draft"
                                  : "badge-published"
                              }`}
                            >
                              {isDraft
                                ? "Chưa công bố"
                                : "Đã công bố"}
                            </span>
                          </div>
                        </td>

                        <td>
                          <div className="exam-structure">
                            <span>
                              {exam.mcqCount ?? 0}
                              {" "}câu trắc nghiệm
                            </span>

                            <span className="part-sql">
                              {exam.sqlCount ?? 0}
                              {" "}câu SQL
                            </span>

                            <span className="part-essay">
                              {exam.essayCount ?? 0}
                              {" "}câu tự luận
                            </span>
                          </div>
                        </td>

                        <td>
                          <div className="exam-schedule">
                            <strong>
                              {formatDate(exam.date)}
                            </strong>

                            <span>
                              {exam.startTime && end
                                ? `${exam.startTime} – ${end.time}${
                                    end.nextDay
                                      ? " (ngày hôm sau)"
                                      : ""
                                  }`
                                : "Chưa xếp giờ"}
                            </span>

                            <small>
                              <Icon name="clock" />
                              {exam.duration} phút
                            </small>
                          </div>
                        </td>

                        <td>
                          <div className="exam-actions">
                            <button
                              className="btn-detail"
                              type="button"
                              onClick={() => openExam(exam)}
                            >
                              {isDraft
                                ? "Soạn tiếp"
                                : "Xem lại"}
                            </button>

                            <button
                              className="btn-detail btn-time"
                              type="button"
                              onClick={(event) =>
                                openEditor(exam, event)
                              }
                            >
                              <Icon name="clock" />
                              Chỉnh thời gian
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="exam-list-footer">
              <div className="exam-record-count">
                Hiển thị{" "}
                <strong>
                  {firstRecord}–{lastRecord}
                </strong>
                {" "}trong{" "}
                <strong>{visible.length}</strong>
                {" "}
                {activeTab === "published"
                  ? "bài đã công bố"
                  : "bản nháp"}

                {query.trim() && (
                  <span className="exam-filter-total">
                    {" "}· Tổng trong tab: {currentTabCount}
                  </span>
                )}
              </div>

              <nav
                className="exam-pagination"
                aria-label={
                  activeTab === "published"
                    ? "Phân trang bài đã công bố"
                    : "Phân trang bản nháp"
                }
              >
                <button
                  className="exam-page-button page-direction"
                  type="button"
                  disabled={currentPage === 1}
                  onClick={() =>
                    goToPage(currentPage - 1)
                  }
                  aria-label="Trang trước"
                >
                  ‹ Trước
                </button>

                {pageNumbers.map((page) =>
                  typeof page === "string" ? (
                    <span
                      key={page}
                      className="exam-page-gap"
                      aria-hidden="true"
                    >
                      …
                    </span>
                  ) : (
                    <button
                      key={page}
                      className={`exam-page-button ${
                        page === currentPage
                          ? "is-active"
                          : ""
                      }`}
                      type="button"
                      aria-label={`Trang ${page}`}
                      aria-current={
                        page === currentPage
                          ? "page"
                          : undefined
                      }
                      onClick={() => goToPage(page)}
                    >
                      {page}
                    </button>
                  )
                )}

                <button
                  className="exam-page-button page-direction"
                  type="button"
                  disabled={currentPage === totalPages}
                  onClick={() =>
                    goToPage(currentPage + 1)
                  }
                  aria-label="Trang sau"
                >
                  Sau ›
                </button>
              </nav>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>
          DBCAS • Nền tảng đánh giá năng lực CSDL
        </span>
        <span>© 2026 Duy Tan University</span>
      </footer>

      {editingExam && (
        <div
          className="exam-modal-overlay"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              closeEditor();
            }
          }}
        >
          <section
            className="exam-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="schedule-dialog-title"
            aria-describedby="schedule-dialog-description"
            aria-busy={saving}
            ref={dialogRef}
            tabIndex={-1}
          >
            <div className="exam-modal-head">
              <div>
                <span className="modal-label">
                  LỊCH KIỂM TRA
                </span>

                <h2 id="schedule-dialog-title">
                  Chỉnh thời gian thi
                </h2>
              </div>

              <button
                className="modal-close"
                type="button"
                aria-label="Đóng hộp chỉnh thời gian"
                disabled={saving}
                onClick={closeEditor}
              >
                <Icon name="close" />
              </button>
            </div>

            <p
              className="modal-exam-title"
              id="schedule-dialog-description"
            >
              {editingExam.title}
            </p>

            <form
              onSubmit={saveSchedule}
              noValidate
            >
              <fieldset
                className="schedule-fields"
                disabled={saving}
              >
                <label className="schedule-field field-full">
                  <span>Ngày thi</span>

                  <input
                    ref={dateInputRef}
                    type="date"
                    required
                    value={form.date}
                    onChange={(event) =>
                      updateForm(
                        "date",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label className="schedule-field">
                  <span>Giờ bắt đầu</span>

                  <input
                    type="time"
                    required
                    value={form.startTime}
                    onChange={(event) =>
                      updateForm(
                        "startTime",
                        event.target.value
                      )
                    }
                  />
                </label>

                <label className="schedule-field">
                  <span>Thời lượng (phút)</span>

                  <input
                    type="number"
                    min="1"
                    max="600"
                    step="1"
                    required
                    value={form.duration}
                    onChange={(event) =>
                      updateForm(
                        "duration",
                        event.target.value
                      )
                    }
                  />
                </label>
              </fieldset>

              <div
                className="schedule-preview"
                aria-live="polite"
              >
                <Icon name="clock" />

                <div>
                  <span>
                    Giờ kết thúc dự kiến
                  </span>

                  <strong>
                    {endTime
                      ? `${endTime.time}${
                          endTime.nextDay
                            ? " · Ngày hôm sau"
                            : ""
                        }`
                      : "Chưa đủ thông tin"}
                  </strong>
                </div>
              </div>

              <p className="schedule-note">
                {editingExam.status === "draft"
                  ? "Đây là lịch dự kiến. Lưu thời gian không công bố đề cho sinh viên."
                  : "Bấm Lưu thời gian để cập nhật lịch thi."}
              </p>

              {formError && (
                <p
                  className="schedule-error"
                  role="alert"
                >
                  {formError}
                </p>
              )}

              <div className="exam-modal-actions">
                <button
                  className="btn-detail"
                  type="button"
                  disabled={saving}
                  onClick={closeEditor}
                >
                  Hủy
                </button>

                <button
                  className="btn-apply"
                  type="submit"
                  disabled={saving}
                >
                  {saving
                    ? "Đang lưu..."
                    : "Lưu thời gian"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}

      {notice && (
        <div
          className="admin-notice"
          role="status"
        >
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