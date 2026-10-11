import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import "./Phan_tich_Learner.css";
import video from "./video1.mp4";
import poster from "./nen1.jpg";

// TODO BE:
// Thay dữ liệu mẫu bằng overview và tests lấy từ API.
const SAMPLE_OVERVIEW = {
  evaluation:
    "Sinh viên sở hữu tư duy giải thuật truy vấn SELECT rất xuất sắc " +
    "(92%), thành thạo thao tác DML và quản lý Transaction (88%). " +
    "Nền tảng lập trình SQL thực thi trên hệ quản trị RDBMS đạt chuẩn " +
    "kỹ sư cơ sở, phản xạ truy vấn logic nhạy bén.",

  diagnosis:
    "Điểm nghẽn nhận thức nghiêm trọng nằm ở phần lý thuyết quan hệ " +
    "đại số: thường xuyên bỏ sót phụ thuộc hàm trung gian trong " +
    "thuật toán phân rã 3NF/BCNF, thiết lập sai cơ chế cascade path, " +
    "và chưa phân biệt được bản chất giữa OLTP với đọc phân tích OLAP.",

  proposal:
    "Định hướng tự ôn tập: tập trung nghiên cứu lại tài liệu giải thuật " +
    "Bao đóng F+ và phân rã bảo toàn phụ thuộc hàm, quy tắc ràng buộc " +
    "tham chiếu vòng (Cyclic References), và mô hình Star Schema " +
    "để củng cố nền tảng lý thuyết.",
};

const SAMPLE_TESTS = [
  {
    id: "SQL-01",
    title: "Phân tích Query Execution Plan & Đánh chỉ mục Index Scan",
    date: "20/11/2024",
    type: "Thực hành SQL",
    topic: "Tối ưu truy vấn",
    score: 7.2,
    strength:
      "Viết đúng câu truy vấn và trả về dữ liệu theo yêu cầu. Biết sử dụng JOIN, WHERE và ORDER BY.",
    weakness:
      "Chưa phân tích đầy đủ sự khác nhau giữa Sequential Scan và Index Scan. Chỉ mục chưa phù hợp với điều kiện lọc.",
    suggestion:
      "Thực hành EXPLAIN ANALYZE, đối chiếu thời gian chạy trước và sau khi tạo chỉ mục.",
    resource: "Query Execution Plan & Index Scan",
  },
  {
    id: "SQL-02",
    title: "Truy vấn liên kết & Gom nhóm dữ liệu",
    date: "18/11/2024",
    type: "Thực hành SQL",
    topic: "JOIN và GROUP BY",
    score: 8.2,
    strength:
      "Sử dụng đúng INNER JOIN, GROUP BY và hàm tổng hợp để thống kê dữ liệu.",
    weakness:
      "Một số trường hợp LEFT JOIN chưa xử lý giá trị NULL đầy đủ.",
    suggestion:
      "Ôn COALESCE và phân biệt điều kiện đặt trong ON với WHERE khi dùng LEFT JOIN.",
    resource: "JOIN, GROUP BY & HAVING",
  },
  {
    id: "TN-03",
    title: "Chuẩn hóa lược đồ & Phụ thuộc hàm",
    date: "14/11/2024",
    type: "Trắc nghiệm",
    topic: "Chuẩn hóa CSDL",
    score: 6.5,
    strength:
      "Xác định tốt dạng chuẩn 1NF và 2NF cơ bản trong thời gian ngắn.",
    weakness:
      "Mất phụ thuộc hàm D → E khi phân rã. Thiếu khóa dự tuyển (Candidate Key) lồng ghép.",
    suggestion:
      "Kiểm tra bao đóng thuộc tính X+ và dùng bảng Tableau để đối chiếu Lossless Join.",
    resource: "Phân rã 3NF & Tableau",
  },
  {
    id: "SQL-04",
    title: "Ràng buộc toàn vẹn & Khóa ngoại CASCADE",
    date: "08/11/2024",
    type: "Thực hành SQL",
    topic: "Ràng buộc",
    score: 7.0,
    strength:
      "Khai báo khóa chính, khóa ngoại đơn và thuộc tính NOT NULL chính xác.",
    weakness:
      "Chưa xử lý đúng tham chiếu vòng. Nhầm thứ tự đánh giá ràng buộc CHECK phức hợp.",
    suggestion:
      "Xem lại quan hệ phụ thuộc vòng và lựa chọn CASCADE, SET NULL hoặc RESTRICT theo nghiệp vụ.",
    resource: "Cú pháp Trigger & Foreign Key",
  },
  {
    id: "TL-05",
    title: "Tối ưu hóa truy vấn & Kiến trúc OLAP",
    date: "01/11/2024",
    type: "Tự luận",
    topic: "Thiết kế hệ thống",
    score: 7.8,
    strength:
      "Áp dụng tốt kỹ thuật đánh Index B-Tree để giảm chi phí quét toàn bảng.",
    weakness:
      "Nhầm lẫn bảng Fact và Dimension trong Star Schema. Chưa khai thác Materialized Views.",
    suggestion:
      "Phân biệt mục tiêu giữa hệ tác nghiệp OLTP và kho dữ liệu OLAP.",
    resource: "Star Schema & Materialized Views",
  },
  {
    id: "SQL-06",
    title: "Thao tác DML & Quản lý Transaction",
    date: "28/10/2024",
    type: "Thực hành SQL",
    topic: "Thao tác dữ liệu",
    score: 8.8,
    strength:
      "Thực hiện tốt INSERT, UPDATE và DELETE. Sử dụng giao dịch để bảo đảm dữ liệu nhất quán.",
    weakness:
      "Một số tình huống lỗi chưa có phương án ROLLBACK rõ ràng.",
    suggestion:
      "Thêm tình huống kiểm thử giao dịch thất bại và thực hành SAVEPOINT.",
    resource: "Transaction & SAVEPOINT",
  },
  {
    id: "TN-07",
    title: "Truy vấn cơ bản & Điều kiện lọc",
    date: "25/10/2024",
    type: "Trắc nghiệm",
    topic: "SELECT và WHERE",
    score: 9.2,
    strength: "Nắm vững SELECT, WHERE, DISTINCT và ORDER BY.",
    weakness:
      "Còn nhầm lẫn khi kết hợp nhiều điều kiện AND và OR.",
    suggestion:
      "Dùng dấu ngoặc để thể hiện rõ thứ tự xử lý điều kiện.",
    resource: "SELECT & Biểu thức điều kiện",
  },
  {
    id: "SQL-08",
    title: "Truy vấn con & Common Table Expressions",
    date: "22/10/2024",
    type: "Thực hành SQL",
    topic: "Subquery và CTE",
    score: 7.6,
    strength: "Biết chia truy vấn thành các bước bằng CTE.",
    weakness:
      "Một số truy vấn con tương quan chạy lặp lại gây tốn thời gian.",
    suggestion: "So sánh phương án dùng JOIN, EXISTS và CTE.",
    resource: "Subqueries, EXISTS & CTE",
  },
  {
    id: "SQL-09",
    title: "Window Functions & Xếp hạng dữ liệu",
    date: "18/10/2024",
    type: "Thực hành SQL",
    topic: "Window Functions",
    score: 7.4,
    strength: "Sử dụng được ROW_NUMBER và RANK.",
    weakness: "Chưa phân biệt rõ RANK với DENSE_RANK.",
    suggestion:
      "Thử dữ liệu có điểm trùng nhau để đối chiếu các hàm xếp hạng.",
    resource: "Window Functions & Ranking",
  },
  {
    id: "TN-10",
    title: "Định nghĩa dữ liệu & Cấu trúc bảng",
    date: "15/10/2024",
    type: "Trắc nghiệm",
    topic: "DDL",
    score: 7.4,
    strength: "Nắm được CREATE TABLE và các kiểu dữ liệu cơ bản.",
    weakness: "Chưa đánh giá đầy đủ tác động của ALTER TABLE.",
    suggestion:
      "Ôn CREATE, ALTER và DROP trên cơ sở dữ liệu thử nghiệm.",
    resource: "DDL & Thiết kế bảng",
  },
  {
    id: "SQL-11",
    title: "Khung nhìn & Đối tượng cơ sở dữ liệu",
    date: "12/10/2024",
    type: "Thực hành SQL",
    topic: "Views",
    score: 7.0,
    strength: "Tạo được View để tái sử dụng truy vấn.",
    weakness: "Chưa xác định đúng các View có thể cập nhật.",
    suggestion:
      "So sánh View đơn giản với View có JOIN và tổng hợp.",
    resource: "Views & Quy tắc cập nhật",
  },
  {
    id: "TL-12",
    title: "Thiết kế mô hình thực thể & Quan hệ",
    date: "09/10/2024",
    type: "Tự luận",
    topic: "Thiết kế khái niệm",
    score: 5.6,
    strength: "Xác định được các thực thể chính trong bài toán.",
    weakness:
      "Chưa biểu diễn đúng một số quan hệ nhiều-nhiều.",
    suggestion:
      "Bổ sung thực thể liên kết và xác định khóa phù hợp.",
    resource: "Entity Relationship & Bảng liên kết",
  },
  {
    id: "TN-13",
    title: "Tính chất ACID & Mức cô lập giao dịch",
    date: "05/10/2024",
    type: "Trắc nghiệm",
    topic: "ACID",
    score: 7.5,
    strength: "Hiểu ý nghĩa Atomicity và Durability.",
    weakness:
      "Còn nhầm lẫn giữa các hiện tượng đọc dữ liệu trong giao dịch.",
    suggestion:
      "Ôn Dirty Read, Non-repeatable Read và Phantom Read.",
    resource: "ACID & Isolation Levels",
  },
  {
    id: "SQL-14",
    title: "Kiểm thử ràng buộc & Xử lý dữ liệu lỗi",
    date: "01/10/2024",
    type: "Thực hành SQL",
    topic: "Kiểm thử dữ liệu",
    score: 6.8,
    strength: "Kiểm tra được dữ liệu trùng khóa và dữ liệu thiếu.",
    weakness:
      "Thiếu trường hợp kiểm thử giới hạn và tham chiếu không tồn tại.",
    suggestion:
      "Lập bộ dữ liệu hợp lệ, không hợp lệ và dữ liệu biên.",
    resource: "Constraint Testing & Dữ liệu biên",
  },
];

function normalize(value) {
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

function Icon({ name }) {
  return (
    <svg className="icon" aria-hidden="true">
      <use href={`#analysis-i-${name}`} />
    </svg>
  );
}

function IconDefinitions() {
  return (
    <svg className="svg-definitions" aria-hidden="true">
      <defs>
        <symbol id="analysis-i-database" viewBox="0 0 24 24">
          <ellipse cx="12" cy="5" rx="8" ry="3" />
          <path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
          <path d="M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" />
        </symbol>

        <symbol id="analysis-i-home" viewBox="0 0 24 24">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </symbol>

        <symbol id="analysis-i-file" viewBox="0 0 24 24">
          <path d="M14 3H5v18h14V8z" />
          <path d="M14 3v5h5M8 12h8M8 16h8" />
        </symbol>

        <symbol id="analysis-i-chart" viewBox="0 0 24 24">
          <path d="M4 3v18h17M8 17v-5M13 17V7M18 17v-8" />
        </symbol>

        <symbol id="analysis-i-settings" viewBox="0 0 24 24">
          <path d="M3 6h18M3 12h18M3 18h18" />
          <circle cx="8" cy="6" r="2" />
          <circle cx="16" cy="12" r="2" />
          <circle cx="10" cy="18" r="2" />
        </symbol>

        <symbol id="analysis-i-bell" viewBox="0 0 24 24">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
        </symbol>

        <symbol id="analysis-i-search" viewBox="0 0 24 24">
          <circle cx="10.5" cy="10.5" r="6.5" />
          <path d="m16 16 5 5" />
        </symbol>

        <symbol id="analysis-i-check" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="9" />
          <path d="m8 12 3 3 5-6" />
        </symbol>

        <symbol id="analysis-i-diagnosis" viewBox="0 0 24 24">
          <circle cx="10" cy="10" r="6" />
          <path d="m15 15 6 6M10 7v4M10 13h.01" />
        </symbol>

        <symbol id="analysis-i-rocket" viewBox="0 0 24 24">
          <path d="M14 5c3-3 7-3 7-3s0 4-3 7l-7 7-4-4z" />
          <path d="m14 5-6-1-4 4 5 2M18 9l1 6-4 4-2-5" />
          <circle cx="16" cy="7" r="1" />
          <path d="M6 15c-3 0-4 3-4 7 4 0 7-1 7-4" />
        </symbol>

        <symbol id="analysis-i-ai" viewBox="0 0 24 24">
          <path d="M9 21v-4H6v-5H3l3-5a7 7 0 1 1 13 5v9" />
          <circle cx="13" cy="8" r="2" />
          <path d="M13 4v2M13 10v2M9 8h2M15 8h2" />
        </symbol>

        <symbol id="analysis-i-eye" viewBox="0 0 24 24">
          <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12" />
          <circle cx="12" cy="12" r="3" />
        </symbol>

        <symbol id="analysis-i-info" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 11v6M12 7h.01" />
        </symbol>
      </defs>
    </svg>
  );
}

function TestCard({ test }) {
  // Truyền thông tin bài thi sang trang xem lại.
  const query = new URLSearchParams({
    testId: test.id,
    title: test.title,
    date: test.date,
    score: test.score.toFixed(1),
  });

  return (
    <article className="test-analysis-card">
      <div className="test-analysis-heading">
        <div>
          <h3>
            {test.title}

            <span className="test-date">
              {" "}• {test.date}
            </span>
          </h3>
        </div>

        <span
          className={`test-score${
            test.score >= 8 ? " score-good" : ""
          }`}
        >
          Điểm: <strong>{test.score.toFixed(1)}</strong> / 10
        </span>
      </div>

      <div className="test-feedback-grid">
        <div className="test-feedback">
          <h4>
            <Icon name="check" />
            Điểm mạnh
          </h4>

          <p>{test.strength}</p>
        </div>

        <div className="test-feedback feedback-warning">
          <h4>
            <Icon name="diagnosis" />
            Điểm yếu
          </h4>

          <p>{test.weakness}</p>
        </div>

        <div className="test-feedback feedback-proposal">
          <h4>
            <Icon name="ai" />
            Gợi ý AI khắc phục
          </h4>

          <p>{test.suggestion}</p>

          <span className="resource-label">
            Tài liệu: {test.resource}
          </span>
        </div>
      </div>

      <div className="test-card-actions">
        <Link
          className="test-detail-button"
          to={`/Xem_lai_bai_Learner?${query.toString()}`}
        >
          <Icon name="eye" />
          Xem chi tiết bài thi &amp; lời giải
        </Link>
      </div>
    </article>
  );
}

export default function PhanTichLearner({
  user,
  overview = SAMPLE_OVERVIEW,
  tests = SAMPLE_TESTS,
}) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [toastVisible, setToastVisible] = useState(false);
  const [videoFailed, setVideoFailed] = useState(false);

  const toastTimer = useRef(null);
  const sectionRef = useRef(null);

  const pageSize = 5;

  useEffect(() => {
    return () => {
      clearTimeout(toastTimer.current);
    };
  }, []);

  const keywords = normalize(query)
    .split(/\s+/)
    .filter(Boolean);

  const filtered = tests.filter((test) => {
    const content = normalize(
      [test.id, test.title, test.topic, test.type].join(" "),
    );

    return keywords.every((word) => content.includes(word));
  });

  const totalPages = Math.max(
    1,
    Math.ceil(filtered.length / pageSize),
  );

  const currentPage = Math.min(page, totalPages);

  const visible = filtered.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );

  function changePage(number) {
    setPage(Math.max(1, Math.min(number, totalPages)));

    sectionRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  function handleSearch(event) {
    setQuery(event.target.value);
    setPage(1);
  }

  function showNotification() {
    clearTimeout(toastTimer.current);

    setToastVisible(true);

    toastTimer.current = setTimeout(() => {
      setToastVisible(false);
    }, 3000);
  }

  return (
    <div className="dbcas-learner-analysis">
      <IconDefinitions />

      {/* Toolbar */}
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

            <Link className="nav-link" to="/Bai_kiem_tra_Learner">
              <Icon name="file" />
              <span>Bài kiểm tra</span>
            </Link>

            <Link
              className="nav-link active"
              to="/Phan_tich_Learner"
              aria-current="page"
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
              onClick={showNotification}
            >
              <Icon name="bell" />
              <span className="notification-dot" />
            </button>

            <Link className="profile" to="/Cai_dat_Learner">
              <span className="avatar">
                {user?.initials ?? "HL"}
              </span>

              <span className="profile-info">
                <strong>
                  {user?.name ?? "Nguyễn Hoàng Long"}
                </strong>

                <span>
                  {user?.email ?? "long.nh20216049@sis.hust.edu.vn"}
                </span>
              </span>
            </Link>
          </div>
        </div>
      </header>

      {/* Banner video */}
      <section className="detail-banner">
        <video
          className="detail-video"
          autoPlay
          muted
          loop
          playsInline
          poster={poster}
          hidden={videoFailed}
          onError={() => setVideoFailed(true)}
          aria-hidden="true"
        >
          <source
            src={video}
            type="video/mp4"
            onError={() => setVideoFailed(true)}
          />
        </video>

        <div className="banner-overlay" />

        <div className="container detail-banner-content">
          <nav className="detail-breadcrumb" aria-label="Đường dẫn">
            <Link to="/Home_Learner">
              <Icon name="home" />
              Trang chủ
            </Link>

            <span>/</span>

            <span aria-current="page">
              Phân tích chi tiết
            </span>
          </nav>

          <h1>Chi Tiết Phân Tích Của AI</h1>

          <p>
            Báo cáo chuyên sâu giải mã năng lực CSDL cá nhân:
            Từ điểm mạnh, điểm yếu đến lộ trình khắc phục.
            Hệ thống nhận xét các lỗ hổng kiến thức và đề xuất
            hướng dẫn khắc phục bởi AI Engine.
          </p>
        </div>
      </section>

      <main className="container detail-main">
        {/* Tổng quan AI */}
        <section className="detail-panel">
          <div className="detail-section-heading">
            <span className="detail-heading-icon">
              <Icon name="ai" />
            </span>

            <div>
              <h2>Nhận Xét Tổng Quan &amp; Chẩn Đoán Của AI</h2>

              <p>
                Báo cáo phân tích chuyên sâu 3 chiều:
                Đánh giá thực thi – Bóc tách nguyên nhân –
                Lộ trình bứt phá
              </p>
            </div>
          </div>

          <div className="overview-grid">
            <article className="overview-card evaluation-card">
              <span className="overview-label">
                PHẦN 1 • NĂNG LỰC THỰC TẾ
              </span>

              <h3>
                <Icon name="check" />
                AI Đánh Giá
              </h3>

              <p>{overview.evaluation}</p>
            </article>

            <article className="overview-card diagnosis-card">
              <span className="overview-label">
                PHẦN 2 • LỖ HỔNG CỐT LÕI
              </span>

              <h3>
                <Icon name="diagnosis" />
                AI Chẩn Đoán
              </h3>

              <p>{overview.diagnosis}</p>
            </article>

            <article className="overview-card proposal-card">
              <span className="overview-label">
                PHẦN 3 • KẾ HOẠCH BỨT PHÁ
              </span>

              <h3>
                <Icon name="rocket" />
                AI Đề Xuất
              </h3>

              <p>{overview.proposal}</p>
            </article>
          </div>
        </section>

        {/* Danh sách bài kiểm tra */}
        <section className="detail-panel" ref={sectionRef}>
          <div className="detail-section-heading">
            <span className="detail-heading-icon">
              <Icon name="chart" />
            </span>

            <div>
              <h2>
                Chẩn Đoán Lỗi Sai &amp; Nhận Xét Chi Tiết
                Theo Từng Bài Kiểm Tra Đã Làm
              </h2>
            </div>
          </div>

          <div className="test-filter">
            <label
              className="test-search"
              htmlFor="test-search-input"
            >
              <Icon name="search" />

              <input
                type="search"
                id="test-search-input"
                value={query}
                onChange={handleSearch}
                placeholder="Tìm theo mã bài, chủ đề CSDL..."
                autoComplete="off"
              />
            </label>

            <span className="test-count" role="status">
              Hiển thị: {visible.length} / {filtered.length} bài
            </span>
          </div>

          <div className="test-analysis-list">
            {visible.map((test) => (
              <TestCard key={test.id} test={test} />
            ))}
          </div>

          <p
            className="search-empty"
            hidden={filtered.length > 0}
          >
            Không tìm thấy bài kiểm tra phù hợp.
          </p>

          <div
            className="pagination-bar"
            hidden={filtered.length === 0}
          >
            <p className="pagination-info">
              <Icon name="info" />

              <span>
                Đang hiển thị {visible.length} trong tổng số{" "}
                {filtered.length} bài kiểm tra
              </span>
            </p>

            <nav
              className="pagination-buttons"
              aria-label="Phân trang bài kiểm tra"
            >
              <button
                type="button"
                className="page-button"
                disabled={currentPage === 1}
                onClick={() => changePage(currentPage - 1)}
              >
                Trang trước
              </button>

              {Array.from(
                { length: totalPages },
                (_, index) => index + 1,
              ).map((number) => (
                <button
                  key={number}
                  type="button"
                  className={`page-button${
                    number === currentPage ? " active" : ""
                  }`}
                  aria-current={
                    number === currentPage ? "page" : undefined
                  }
                  onClick={() => changePage(number)}
                >
                  {number}
                </button>
              ))}

              <button
                type="button"
                className="page-button"
                disabled={currentPage === totalPages}
                onClick={() => changePage(currentPage + 1)}
              >
                Trang tiếp
              </button>
            </nav>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="container footer-inner">
          <p>
            <strong>DBCAS</strong>
            <span>•</span>
            Nền tảng tự động Đánh giá Năng lực CSDL
          </p>

          <nav aria-label="Liên kết hỗ trợ">
            <Link to="/Quy_che">Quy chế khảo thí</Link>
            <Link to="/Tai_lieu#chuan-hoa">Chuẩn hóa 3NF</Link>
            <Link to="/Tai_lieu#sql">Tài liệu SQL</Link>
            <Link to="/Ho_tro">Hỗ trợ</Link>
          </nav>
        </div>
      </footer>

      <div
        className={`toast${toastVisible ? " show" : ""}`}
        role="status"
      >
        Bạn chưa có thông báo mới.
      </div>
    </div>
  );
}