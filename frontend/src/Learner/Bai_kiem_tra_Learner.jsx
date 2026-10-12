import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Learner.css";
import "./Bai_kiem_tra_Learner.css";
import video from "./video1.mp4";
import poster from "./nen1.jpg";
const TOPICS = [
    {
        title: "Đánh giá thực hành CSDL: Chuẩn hóa 3NF, BCNF & Khóa ngoại",
        description: "Tập trung vào thiết kế dữ liệu và ràng buộc toàn vẹn.",
        skill: "Thiết kế & Ràng buộc",
        tags: ["Chuẩn hóa 3NF/BCNF", "Khóa ngoại"],
    },
    {
        title: "Khảo thí định kỳ: SQL & Kỹ năng viết truy vấn",
        description: "JOIN, GROUP BY, HAVING và truy vấn lồng.",
        skill: "Truy vấn SQL",
        tags: ["SQL Querying", "JOIN & GROUP BY"],
    },
    {
        title: "Đánh giá năng lực tổng thể CSDL",
        description: "Kiểm tra kiến thức, truy vấn SQL và thiết kế dữ liệu.",
        skill: "Tổng hợp",
        tags: ["SQL", "Thiết kế CSDL"],
    },
    {
        title: "Kiểm tra lập trình CSDL: View và Transaction",
        description: "Thực hành khung nhìn và quản lý giao dịch.",
        skill: "DML & DDL",
        tags: ["VIEW", "Transaction"],
    },
    {
        title: "Khởi tạo Schema & Ràng buộc toàn vẹn",
        description: "CREATE, ALTER, CHECK, DEFAULT và kiểu dữ liệu.",
        skill: "DML & DDL",
        tags: ["DDL Schema", "Data Types"],
    },
];
const STATUS_LABELS = {
    available: "Chưa làm",
    completed: "Đã hoàn thành",
    upcoming: "Chưa mở",
    expired: "Đã hết hạn",
};
// Khi có backend, truyền exams thực tế vào component.
const DEMO_EXAMS = Array.from({ length: 54 }, (_, index) => {
    const topic = TOPICS[index % TOPICS.length];
    const status = [
        "available",
        "completed",
        "completed",
        "upcoming",
        "completed",
        "expired",
    ][index % 6];
    return {
        ...topic,
        id: `EXAM-${String(index + 1).padStart(3, "0")}`,
        title:
            index < TOPICS.length
                ? topic.title
                : `${topic.title} — Đợt ${Math.floor(index / 5) + 1}`,
        duration: [60, 45, 90, 75, 30][index % 5],
        mcqCount: 10,
        sqlCount: 3,
        essayCount: 1,
        opensAt: `${String(13 + (index % 16)).padStart(2, "0")}/10/2026`,
        closesAt: `${String(14 + (index % 16)).padStart(2, "0")}/10/2026`,
        status,
        score:
            status === "completed"
                ? Number((5 + ((index * 7) % 51) / 10).toFixed(1))
                : null,
    };
});
function normalizeText(value) {
    return String(value ?? "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/gi, "d")
        .toLowerCase()
        .trim();
}
function formatScore(value) {
    if (value === null || value === undefined || value === "") {
        return null;
    }
    const score = Number(value);
    return Number.isFinite(score) && score >= 0 && score <= 10
        ? score.toFixed(1)
        : null;
}
function Icon({ name }) {
    const paths = {
        home: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
        file: "M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h8",
        chart: "M4 3v18h17M8 17v-5M13 17V7M18 17v-8",
        settings: "M3 6h18M3 12h18M3 18h18",
        bell:
            "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
        search: "m16 16 5 5",
        clock: "M12 7v5l3 2",
        reset: "M3 10a9 9 0 1 1 2 8M3 4v6h6",
        arrow: "M5 12h14M14 7l5 5-5 5",
        lock: "M6 10h12v11H6zM8 10V7a4 4 0 0 1 8 0v3",
        database:
            "M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7",
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
            <path d={paths[name] || paths.file} />
            {name === "search" && (
                <circle cx="10.5" cy="10.5" r="6.5" />
            )}
            {name === "clock" && (
                <circle cx="12" cy="12" r="9" />
            )}
            {name === "settings" && (
                <>
                    <circle cx="8" cy="6" r="2" />
                    <circle cx="16" cy="12" r="2" />
                    <circle cx="10" cy="18" r="2" />
                </>
            )}
            {name === "database" && (
                <ellipse cx="12" cy="5" rx="8" ry="3" />
            )}
        </svg>
    );
}
function pageNumbers(current, total) {
    const result = [];
    for (let number = 1; number <= total; number += 1) {
        if (
            number === 1 ||
            number === total ||
            Math.abs(number - current) <= 1
        ) {
            const previous = result[result.length - 1];
            if (typeof previous === "number" && number - previous > 1) {
                result.push(`gap-${number}`);
            }
            result.push(number);
        }
    }
    return result;
}
export default function BaiKiemTraLearner({
    user,
    exams = DEMO_EXAMS,
    onStartExam,
    onViewResult,
}) {
    const navigate = useNavigate();
    const learner = {
        name: user?.name ?? "Nguyễn Hoàng Long",
        email: user?.email ?? "long.nh20216049@sis.hust.edu.vn",
        initials: user?.initials ?? "HL",
    };
    const [query, setQuery] = useState("");
    const [duration, setDuration] = useState("");
    const [status, setStatus] = useState("");
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [notice, setNotice] = useState("");
    const [busyId, setBusyId] = useState(null);
    const examList = Array.isArray(exams) ? exams : [];
    const filtered = useMemo(() => {
        const list = Array.isArray(exams) ? exams : [];
        return list.filter((exam) => {
            const minutes = Number(exam.duration);
            const matchesDuration =
                !duration ||
                (duration === "short" && minutes <= 45) ||
                (duration === "medium" && minutes > 45 && minutes <= 60) ||
                (duration === "long" && minutes > 60);
            return (
                normalizeText(exam.title).includes(normalizeText(query)) &&
                matchesDuration &&
                (!status || exam.status === status)
            );
        });
    }, [exams, query, duration, status]);
    const totalPages = Math.max(
        1,
        Math.ceil(filtered.length / pageSize)
    );
    const currentPage = Math.min(page, totalPages);
    const startIndex = (currentPage - 1) * pageSize;
    const visibleExams = filtered.slice(
        startIndex,
        startIndex + pageSize
    );
    const completedCount = examList.filter(
        (exam) => exam.status === "completed"
    ).length;
    const availableCount = examList.filter(
        (exam) => exam.status === "available"
    ).length;
    const validScores = examList
        .filter((exam) => exam.status === "completed")
        .map((exam) => formatScore(exam.score))
        .filter((score) => score !== null)
        .map(Number);
    const average = validScores.length
        ? (
            validScores.reduce((sum, score) => sum + score, 0) /
            validScores.length
        ).toFixed(1)
        : "—";
    function changeFilter(setter, value) {
        setter(value);
        setPage(1);
    }
    function resetFilters() {
        setQuery("");
        setDuration("");
        setStatus("");
        setPage(1);
    }
    async function startExam(exam) {
        if (busyId !== null || exam.status !== "available") return;
        setBusyId(exam.id);
        try {
            if (onStartExam) {
                await onStartExam(exam);
            } else {
                navigate(
                    `/TN_Learner?examId=${encodeURIComponent(exam.id)}`,
                    {
                        state: {
                            exam,
                            examId: exam.id,
                        },
                    }
                );
            }
        } catch (error) {
            setNotice(
                error instanceof Error
                    ? error.message
                    : "Không thể mở bài kiểm tra."
            );
        } finally {
            setBusyId(null);
        }
    }
    async function viewResult(exam) {
        if (busyId !== null) return;
        setBusyId(exam.id);
        try {
            if (onViewResult) {
                await onViewResult(exam);
            } else {
                const params = new URLSearchParams({
                    examId: exam.id,
                    from: "exams",
                    title: exam.title,
                    date: exam.submittedAt || exam.closesAt || "",
                });
                const score = formatScore(exam.score);
                if (score !== null) {
                    params.set("score", score);
                }
                navigate(
                    `/Bai_kiem_tra_Learner/Xem_lai_bai_Learner?${params.toString()}`,
                    {
                        state: {
                            exam,
                            examId: exam.id,
                            attemptId: exam.attemptId,
                            from: "exams",
                        },
                    }
                );
            }
        } catch (error) {
            setNotice(
                error instanceof Error
                    ? error.message
                    : "Không thể xem kết quả."
            );
        } finally {
            setBusyId(null);
        }
    }
    return (
        <div className="dbcas-learner-home learner-exams">
            <header className="topbar">
                <div className="topbar-inner">
                    <div className="brand">
                        <span className="brand-icon">
                            <Icon name="database" />
                        </span>
                        <div>
                            <strong>Datamaster</strong>
                            <span>ASSESSMENT ENGINE</span>
                        </div>
                    </div>
                    <nav className="main-nav" aria-label="Menu người học">
                        <Link className="nav-link" to="/Home_Learner">
                            <Icon name="home" />
                            <span>Trang chủ</span>
                        </Link>
                        <Link
                            className="nav-link active"
                            to="/Bai_kiem_tra_Learner"
                            aria-current="page"
                        >
                            <Icon name="file" />
                            <span>Bài kiểm tra</span>
                        </Link>
                        <Link
  className="nav-link"
  to="/Xem_danh_gia_Learner"
>
  <Icon name="chart" />
  <span>Xem đánh giá</span>
</Link>
                        <Link className="nav-link" to="/Cai_dat_Learner">
                            <Icon name="settings" />
                            <span>Cài đặt</span>
                        </Link>
                    </nav>
                    <div className="toolbar-actions">
                        <button
                            className="notification-button"
                            type="button"
                            aria-label="Thông báo"
                            onClick={() => setNotice("Chưa có thông báo mới.")}
                        >
                            <Icon name="bell" />
                            <span className="notification-dot" />
                        </button>
                        <Link className="profile" to="/Cai_dat_Learner">
                            <span className="avatar">{learner.initials}</span>
                            <span className="profile-info">
                                <strong>{learner.name}</strong>
                                <span>{learner.email}</span>
                            </span>
                        </Link>
                    </div>
                </div>
            </header>
            <section className="le-hero">
                <video
                    className="le-hero-video"
                    autoPlay
                    muted
                    loop
                    playsInline
                    poster={poster}
                    aria-hidden="true"
                >
                    <source src={video} type="video/mp4" />
                </video>
                <div className="le-hero-inner">
                    <div className="le-intro">
                        <span className="le-eyebrow">
                            KHẢO THÍ NĂNG LỰC CƠ SỞ DỮ LIỆU
                        </span>
                        <h1>Trung tâm Quản trị &amp; Làm bài kiểm tra</h1>
                        <p>
                            Theo dõi lịch kiểm tra, thực hành SQL và xem kết quả
                            đánh giá.
                        </p>
                    </div>
                    <div className="le-hero-stats">
                        <div>
                            <span>Đã hoàn thành</span>
                            <strong>
                                {completedCount}
                                <small> bài</small>
                            </strong>
                        </div>
                        <div>
                            <span>Điểm trung bình</span>
                            <strong className="le-green">
                                {average}
                                <small>/10</small>
                            </strong>
                        </div>
                        <div>
                            <span>Có thể làm</span>
                            <strong>
                                {availableCount}
                                <small> bài</small>
                            </strong>
                        </div>
                    </div>
                </div>
            </section>
            <section
                className="le-filter-bar"
                aria-label="Bộ lọc bài kiểm tra"
            >
                <div className="le-filters">
                    <label className="le-search">
                        <Icon name="search" />
                        <input
                            type="search"
                            value={query}
                            onChange={(event) =>
                                changeFilter(setQuery, event.target.value)
                            }
                            placeholder="Tìm kiếm theo tên bài kiểm tra..."
                            aria-label="Tìm tên bài kiểm tra"
                        />
                    </label>
                    <select
                        aria-label="Lọc thời lượng"
                        value={duration}
                        onChange={(event) =>
                            changeFilter(setDuration, event.target.value)
                        }
                    >
                        <option value="">Thời lượng: Tất cả</option>
                        <option value="short">Tối đa 45 phút</option>
                        <option value="medium">Trên 45 đến 60 phút</option>
                        <option value="long">Trên 60 phút</option>
                    </select>
                    <select
                        aria-label="Lọc trạng thái"
                        value={status}
                        onChange={(event) =>
                            changeFilter(setStatus, event.target.value)
                        }
                    >
                        <option value="">Trạng thái: Tất cả</option>
                        {Object.entries(STATUS_LABELS).map(([value, label]) => (
                            <option key={value} value={value}>
                                {label}
                            </option>
                        ))}
                    </select>
                    <button
                        type="button"
                        className="le-reset"
                        onClick={resetFilters}
                    >
                        <Icon name="reset" />
                        Đặt lại
                    </button>
                </div>
            </section>
            <main className="le-main">
                <div className="le-list-heading">
                    <h2>Danh sách Bài kiểm tra Khảo thí</h2>
                    <div className="le-legend">
                        <span>
                            <i className="cyan" />
                            Có thể làm: {availableCount}
                        </span>
                        <span>
                            <i className="green" />
                            Đã hoàn thành: {completedCount}
                        </span>
                    </div>
                </div>
                <section className="le-table-card">
                    <div className="le-table-wrap">
                        <table className="le-table">
                            <colgroup>
                                <col className="le-col-title" />
                                <col className="le-col-structure" />
                                <col className="le-col-duration" />
                                <col className="le-col-schedule" />
                                <col className="le-col-skills" />
                                <col className="le-col-result" />
                                <col className="le-col-action" />
                            </colgroup>
                            <thead>
                                <tr>
                                    <th scope="col">Tên bài kiểm tra</th>
                                    <th scope="col">Cấu trúc đề</th>
                                    <th scope="col">Thời lượng</th>
                                    <th scope="col">Thời gian mở &amp; đóng</th>
                                    <th scope="col">Chủ đề &amp; Kỹ năng</th>
                                    <th scope="col">Kết quả / Trạng thái</th>
                                    <th scope="col">Thao tác</th>
                                </tr>
                            </thead>
                            <tbody>
                                {visibleExams.map((exam) => {
                                    const score = formatScore(exam.score);
                                    const completed = exam.status === "completed";
                                    const available = exam.status === "available";
                                    return (
                                        <tr
                                            key={exam.id}
                                            className={
                                                available ? "le-available-row" : ""
                                            }
                                        >
                                            <td>
                                                <div className="le-exam-name">
                                                    <span
                                                        className={`le-exam-icon ${exam.status}`}
                                                    >
                                                        <Icon name="file" />
                                                    </span>
                                                    <div>
                                                        <span
                                                            className={`le-status-label ${exam.status}`}
                                                        >
                                                            {STATUS_LABELS[exam.status] ||
                                                                "Chưa có trạng thái"}
                                                        </span>
                                                        <h3>{exam.title}</h3>
                                                        <p>{exam.description}</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td>
                                                <span className="le-structure">
                                                    {exam.mcqCount ?? 0} TN ·{" "}
                                                    {exam.sqlCount ?? 0} SQL ·{" "}
                                                    {exam.essayCount ?? 0} TL
                                                </span>
                                            </td>
                                            <td>
                                                <span className="le-duration">
                                                    <Icon name="clock" />
                                                    {exam.duration} phút
                                                </span>
                                            </td>
                                            <td>
                                                <div className="le-schedule">
                                                    <span>
                                                        Mở: {exam.opensAt || "Chưa cập nhật"}
                                                    </span>
                                                    <span>
                                                        Đóng: {exam.closesAt || "Chưa cập nhật"}
                                                    </span>
                                                </div>
                                            </td>
                                            <td>
                                                <div className="le-tags">
                                                    <strong>{exam.skill}</strong>
                                                    {(Array.isArray(exam.tags)
                                                        ? exam.tags
                                                        : []
                                                    ).map((tag) => (
                                                        <span key={tag}>{tag}</span>
                                                    ))}
                                                </div>
                                            </td>
                                            <td>
                                                {completed ? (
                                                    <div
                                                        className={`le-result ${score !== null && Number(score) >= 6
                                                                ? "passed"
                                                                : "weak"
                                                            }`}
                                                    >
                                                        <strong>
                                                            {score ?? "—"}
                                                            <small>/10</small>
                                                        </strong>
                                                        <span>
                                                            {score === null
                                                                ? "Chưa có điểm"
                                                                : Number(score) >= 6
                                                                    ? "Đạt"
                                                                    : "Cần ôn tập"}
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <span
                                                        className={`le-status-pill ${exam.status}`}
                                                    >
                                                        {STATUS_LABELS[exam.status] ||
                                                            "Chưa có trạng thái"}
                                                    </span>
                                                )}
                                            </td>
                                            <td>
                                                {available ? (
                                                    <button
                                                        type="button"
                                                        className="le-action primary"
                                                        disabled={busyId !== null}
                                                        onClick={() => startExam(exam)}
                                                    >
                                                        {busyId === exam.id
                                                            ? "Đang mở..."
                                                            : "Vào thi"}
                                                        <Icon name="arrow" />
                                                    </button>
                                                ) : completed ? (
                                                    <button
                                                        type="button"
                                                        className="le-action"
                                                        disabled={busyId !== null}
                                                        onClick={() => viewResult(exam)}
                                                    >
                                                        Xem kết quả
                                                    </button>
                                                ) : (
                                                    <button
                                                        type="button"
                                                        className="le-action"
                                                        disabled
                                                    >
                                                        <Icon name="lock" />
                                                        {exam.status === "upcoming"
                                                            ? "Chưa mở"
                                                            : "Hết hạn"}
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                                {visibleExams.length === 0 && (
                                    <tr>
                                        <td colSpan={7} className="le-empty">
                                            Không có bài kiểm tra phù hợp với bộ lọc.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                    <div className="le-pager">
                        <div className="le-pager-info">
                            <span>
                                Hiển thị {filtered.length ? startIndex + 1 : 0}
                                –{Math.min(startIndex + pageSize, filtered.length)}
                                {" "}trong tổng số {filtered.length} bài kiểm tra
                            </span>
                            <label>
                                Số bài mỗi trang:
                                <select
                                    value={pageSize}
                                    onChange={(event) => {
                                        setPageSize(Number(event.target.value));
                                        setPage(1);
                                    }}
                                >
                                    <option value={5}>5</option>
                                    <option value={10}>10</option>
                                    <option value={20}>20</option>
                                </select>
                            </label>
                        </div>
                        <nav
                            className="le-pagination"
                            aria-label="Phân trang bài kiểm tra"
                        >
                            <button
                                type="button"
                                disabled={currentPage === 1}
                                onClick={() => setPage(currentPage - 1)}
                            >
                                ‹ Trước
                            </button>
                            {pageNumbers(currentPage, totalPages).map((item) =>
                                typeof item === "number" ? (
                                    <button
                                        key={item}
                                        type="button"
                                        className={
                                            item === currentPage ? "active" : ""
                                        }
                                        aria-current={
                                            item === currentPage ? "page" : undefined
                                        }
                                        aria-label={`Trang ${item}`}
                                        onClick={() => setPage(item)}
                                    >
                                        {item}
                                    </button>
                                ) : (
                                    <span key={item}>…</span>
                                )
                            )}
                            <button
                                type="button"
                                disabled={currentPage === totalPages}
                                onClick={() => setPage(currentPage + 1)}
                            >
                                Sau ›
                            </button>
                        </nav>
                    </div>
                </section>
            </main>
            <footer className="footer">
                <div className="container footer-inner">
                    <p>
                        <strong>DBCAS</strong>
                        <span>•</span>
                        <span>
                            Nền tảng tự động Đánh giá Năng lực CSDL
                        </span>
                    </p>
                    <nav aria-label="Liên kết hỗ trợ">
                        <Link to="/Quy_che">Quy chế khảo thí</Link>
                        <Link to="/Tai_lieu#chuan-hoa">Chuẩn hóa 3NF</Link>
                        <Link to="/Tai_lieu#sql">Tài liệu SQL</Link>
                        <Link to="/Ho_tro">Hỗ trợ</Link>
                    </nav>
                </div>
            </footer>
            {notice && (
                <div className="le-notice" role="status">
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