import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import "./Home_Learner.css";
import video from "./video1.mp4";
import poster from "./nen1.jpg";

// TODO BE: thay thống kê, điểm kỹ năng và nội dung AI mẫu bằng dữ liệu API.
// user nhận thông tin người học đã được backend xác thực.
export default function HomeLearner({ user }) {
  const learner = {
    name: user?.name ?? "Nguyễn Hoàng Long",
    email: user?.email ?? "long.nh20216049@sis.hust.edu.vn",
    major: user?.major ?? "Kỹ thuật Phần mềm",
    initials: user?.initials ?? "HL",
  };
  const [toastVisible, setToastVisible] = useState(false);
  const toastTimer = useRef(null);
  useEffect(() => () => clearTimeout(toastTimer.current), []);
  function showNotification() {
    clearTimeout(toastTimer.current);
    setToastVisible(true);
    toastTimer.current = setTimeout(() => setToastVisible(false), 3000);
  }
  return (
    <div className="dbcas-learner-home">

    {/* Các vector dùng chung */}
    <svg className="svg-definitions" aria-hidden="true">
        <defs>
            <symbol id="learner-i-database" viewBox="0 0 24 24">
                <ellipse cx="12" cy="5" rx="8" ry="3"></ellipse>
                <path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5"></path>
                <path d="M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"></path>
            </symbol>
            <symbol id="learner-i-home" viewBox="0 0 24 24">
                <rect x="3" y="3" width="7" height="7" rx="1"></rect>
                <rect x="14" y="3" width="7" height="7" rx="1"></rect>
                <rect x="3" y="14" width="7" height="7" rx="1"></rect>
                <rect x="14" y="14" width="7" height="7" rx="1"></rect>
            </symbol>
            <symbol id="learner-i-file" viewBox="0 0 24 24">
                <path d="M14 3H5v18h14V8z"></path>
                <path d="M14 3v5h5M8 12h8M8 16h8"></path>
            </symbol>
            <symbol id="learner-i-chart" viewBox="0 0 24 24">
                <path d="M4 3v18h17"></path>
                <path d="M8 17v-5M13 17V7M18 17v-8"></path>
            </symbol>
            <symbol id="learner-i-settings" viewBox="0 0 24 24">
                <path d="M3 6h18M3 12h18M3 18h18"></path>
                <circle cx="8" cy="6" r="2"></circle>
                <circle cx="16" cy="12" r="2"></circle>
                <circle cx="10" cy="18" r="2"></circle>
            </symbol>
            <symbol id="learner-i-bell" viewBox="0 0 24 24">
                <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path>
                <path d="M10 21h4"></path>
            </symbol>
            <symbol id="learner-i-check" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="m8 12 3 3 5-6"></path>
            </symbol>
            <symbol id="learner-i-trophy" viewBox="0 0 24 24">
                <path d="M8 3h8v7a4 4 0 0 1-8 0z"></path>
                <path d="M8 5H4v3a4 4 0 0 0 4 4M16 5h4v3a4 4 0 0 1-4 4"></path>
                <path d="M12 14v6M8 21h8"></path>
            </symbol>
            <symbol id="learner-i-cap" viewBox="0 0 24 24">
                <path d="m2 9 10-5 10 5-10 5z"></path>
                <path d="M6 11v6c4 3 8 3 12 0v-6M22 9v7"></path>
            </symbol>
            <symbol id="learner-i-arrow" viewBox="0 0 24 24">
                <path d="M4 12h16m-6-6 6 6-6 6"></path>
            </symbol>
            <symbol id="learner-i-sparkles" viewBox="0 0 24 24">
                <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z"></path>
                <path d="M20 2v4M18 4h4"></path>
            </symbol>
            <symbol id="learner-i-shield" viewBox="0 0 24 24">
                <path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z"></path>
                <path d="m8 12 3 3 5-6"></path>
            </symbol>
            <symbol id="learner-i-warning" viewBox="0 0 24 24">
                <path d="m12 3 10 18H2z"></path>
                <path d="M12 9v5M12 17h.01"></path>
            </symbol>
            <symbol id="learner-i-target" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9"></circle>
                <circle cx="12" cy="12" r="5"></circle>
                <circle cx="12" cy="12" r="1"></circle>
            </symbol>
        </defs>
    </svg>
    {/* Toolbar */}
    <header className="topbar">
        <div className="topbar-inner">
            {/* Logo chỉ hiển thị */}
            <div className="brand">
                <span className="brand-icon">
                    <svg className="icon">
                        <use href="#learner-i-database"></use>
                    </svg>
                </span>
                <div>
                    <strong>Datamaster</strong>
                    <span>ASSESSMENT ENGINE</span>
                </div>
            </div>
            <nav className="main-nav" aria-label="Menu người học">
                <Link className="nav-link active" to="/Home_Learner" aria-current="page">
                    <svg className="icon"><use href="#learner-i-home"></use></svg>
                    <span>Trang chủ</span>
                </Link>
                <Link className="nav-link" to="/Bai_kiem_tra_Learner">
                    <svg className="icon"><use href="#learner-i-file"></use></svg>
                    <span>Bài kiểm tra</span>
                </Link>
                <Link className="nav-link" to="/Danh_gia_Learner">
                    <svg className="icon"><use href="#learner-i-chart"></use></svg>
                    <span>Xem đánh giá</span>
                </Link>
                <Link className="nav-link" to="/Cai_dat_Learner">
                    <svg className="icon"><use href="#learner-i-settings"></use></svg>
                    <span>Cài đặt</span>
                </Link>
            </nav>
            <div className="toolbar-actions">
                <button className="notification-button" onClick={showNotification} type="button" aria-label="Thông báo">
                    <svg className="icon"><use href="#learner-i-bell"></use></svg>
                    <span className="notification-dot"></span>
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
    {/* Lời chào và thống kê */}
    <section className="hero">
        <video className="hero-video" autoPlay muted loop playsInline poster={poster} aria-hidden="true">
        <source src={video} type="video/mp4" />
    </video>
        <div className="container">
            <div className="hero-heading">
                <div>
                    <h1>Xin chào, {learner.name} <span>👋</span></h1>
                    <p>
                        Kiểm tra và củng cố các lỗ hổng kiến thức để sẵn sàng cho bài thi kết thúc môn.
                    </p>
                </div>
                <div className="hero-tags">
                    <span className="hero-tag">
                        <svg className="icon"><use href="#learner-i-cap"></use></svg>
                        Ngành: <strong>{learner.major}</strong>
                    </span>
                    <span className="hero-tag">
                        <svg className="icon"><use href="#learner-i-trophy"></use></svg>
                        Hạng #14 <span className="muted">/ 2,845 SV</span>
                    </span>
                </div>
            </div>
            <div className="stats-grid">
                <article className="stat-card">
                    <div className="stat-heading">
                        <span>SỐ LƯỢT THI</span>
                        <svg className="icon"><use href="#learner-i-check"></use></svg>
                    </div>
                    <div className="stat-bottom">
                        <div className="stat-value">
                            <strong>05</strong>
                            <span>bài hoàn thành</span>
                        </div>
                        <span className="tag tag-green">+2 tuần này</span>
                    </div>
                </article>
                <article className="stat-card">
                    <div className="stat-heading">
                        <span>ĐIỂM NĂNG LỰC CHUNG</span>
                        <svg className="icon"><use href="#learner-i-chart"></use></svg>
                    </div>
                    <div className="stat-bottom">
                        <div className="stat-value">
                            <strong className="cyan">7.5</strong>
                            <span>/ 10</span>
                        </div>
                        <span className="tag">Xếp loại Khá giỏi</span>
                    </div>
                </article>
                <article className="stat-card">
                    <div className="stat-heading">
                        <span>XẾP HẠNG TOÀN KHÓA</span>
                        <svg className="icon cyan"><use href="#learner-i-trophy"></use></svg>
                    </div>
                    <div className="stat-bottom">
                        <div className="stat-value">
                            <strong>#14</strong>
                            <span>/ 2,845 SV</span>
                        </div>
                    </div>
                </article>
                <article className="stat-card">
                    <div className="stat-heading">
                        <span>TIẾN ĐỘ CHUẨN ĐẦU RA</span>
                        <span className="mono">Còn lại 32%</span>
                    </div>
                    <div className="stat-bottom">
                        <div className="stat-value">
                            <strong>68%</strong>
                            <span>CLO đã đạt</span>
                        </div>
                        <span className="stat-target">Mục tiêu 100%</span>
                    </div>
                    <div className="hero-progress" role="progressbar" aria-label="Tiến độ chuẩn đầu ra" aria-valuemin="0" aria-valuemax="100" aria-valuenow="68">
                        <span style={{ width: "68%" }}></span>
                    </div>
                </article>
            </div>
        </div>
    </section>
    <main className="container main-content">
        {/* Đồ thị năng lực */}
        <section className="panel competency-panel">
            <div className="panel-heading">
                <div>
                    <h2>Đồ thị năng lực PostgreSQL cá nhân</h2>
                    <p>Phân tích đa chiều dựa trên các bài thực hành và trắc nghiệm</p>
                </div>
                <div className="legend">
                    <span><i className="legend-dot"></i>Năng lực đạt</span>
                    <span className="rose">
                        <i className="legend-dot rose-dot"></i>
                        Dưới chuẩn (&lt;60%)
                    </span>
                </div>
            </div>
            <div className="competency-layout">
                <div className="radar-card">
                    <div className="radar-heading">
                        <strong>3 TRỤ CỘT NĂNG LỰC</strong>
                        <span>Mốc chuẩn: 70%</span>
                    </div>
                    <svg className="radar-chart" viewBox="0 0 360 300" role="img" aria-labelledby="learner-radar-title learner-radar-description">
                        <title id="learner-radar-title">Đồ thị ba nhóm năng lực</title>
                        <desc id="learner-radar-description">
                            SQL Querying 85 phần trăm,
                            Data Manipulation 78 phần trăm,
                            Constraints và Design 54 phần trăm.
                            Mốc chuẩn 70 phần trăm.
                        </desc>
                        {/* Lưới */}
                        <g className="radar-grid">
                            <polygon points="180,58 63.1,260.5 296.9,260.5"></polygon>
                            <polygon points="180,85 86.5,247 273.5,247"></polygon>
                            <polygon points="180,112 109.9,233.5 250.1,233.5"></polygon>
                            <polygon points="180,139 133.2,220 226.8,220"></polygon>
                            <polygon points="180,166 156.6,206.5 203.4,206.5"></polygon>
                            <path d="M180 193V58M180 193 63.1 260.5M180 193 296.9 260.5"></path>
                        </g>
                        {/* Mốc chuẩn 70% */}
                        <polygon className="radar-standard"
                                 points="180,98.5 98.2,240.3 261.8,240.3"></polygon>
                        {/* Giá trị 85%, 54%, 78% */}
                        <polygon className="radar-value"
                                 points="180,78.3 116.9,229.5 271.2,245.7"></polygon>
                        <g className="radar-dots">
                            <circle cx="180" cy="78.3" r="3.5"></circle>
                            <circle className="weak-dot" cx="116.9" cy="229.5" r="3.5"></circle>
                            <circle cx="271.2" cy="245.7" r="3.5"></circle>
                        </g>
                        <text x="180" y="20" textAnchor="middle">SQL Querying</text>
                        <text className="radar-percent" x="180" y="37" textAnchor="middle">85%</text>
                        <text className="weak-label" x="6" y="279">Constraints &amp; Design</text>
                        <text className="weak-label" x="6" y="295">54% (Cần bù)</text>
                        <text x="354" y="279" textAnchor="end">Data Manipulation</text>
                        <text className="radar-percent" x="354" y="295" textAnchor="end">78%</text>
                        <text className="standard-label" x="194" y="105">70% Chuẩn</text>
                    </svg>
                    <p className="radar-note">
                        Trọng số tính trên toàn bộ 9 kỹ năng chuyên môn CSDL
                    </p>
                </div>
                <div className="skill-groups">
                    <section className="skill-group">
                        <div className="skill-group-heading">
                            <h3><i></i>NHÓM I. SQL QUERYING (TRUY VẤN)</h3>
                            <span>TB: 85%</span>
                        </div>
                        <div className="skill">
                            <div className="skill-label">
                                <span>Truy vấn cơ bản (SELECT, WHERE, ORDER BY, DISTINCT)</span>
                                <strong>92%</strong>
                            </div>
                            <div className="skill-track"><span style={{ width: "92%" }}></span></div>
                        </div>
                        <div className="skill">
                            <div className="skill-label">
                                <span>Liên kết &amp; Gom nhóm (JOIN, GROUP BY, HAVING, Aggregates)</span>
                                <strong>82%</strong>
                            </div>
                            <div className="skill-track"><span style={{ width: "82%" }}></span></div>
                        </div>
                        <div className="skill">
                            <div className="skill-label">
                                <span>Truy vấn nâng cao (Subqueries, CTE, Window Functions)</span>
                                <strong>76%</strong>
                            </div>
                            <div className="skill-track"><span style={{ width: "76%" }}></span></div>
                        </div>
                    </section>
                    <section className="skill-group">
                        <div className="skill-group-heading">
                            <h3><i></i>NHÓM II. DATA MANIPULATION &amp; DEFINITION</h3>
                            <span>TB: 78%</span>
                        </div>
                        <div className="skill">
                            <div className="skill-label">
                                <span>Thao tác dữ liệu DML (INSERT, UPDATE, DELETE)</span>
                                <strong>88%</strong>
                            </div>
                            <div className="skill-track"><span style={{ width: "88%" }}></span></div>
                        </div>
                        <div className="skill">
                            <div className="skill-label">
                                <span>Định nghĩa dữ liệu DDL (CREATE, ALTER, DROP)</span>
                                <strong>74%</strong>
                            </div>
                            <div className="skill-track"><span style={{ width: "74%" }}></span></div>
                        </div>
                        <div className="skill">
                            <div className="skill-label">
                                <span>Khung nhìn &amp; Đối tượng (Views)</span>
                                <strong>70%</strong>
                            </div>
                            <div className="skill-track"><span style={{ width: "70%" }}></span></div>
                        </div>
                    </section>
                    <section className="skill-group weak-group">
                        <div className="skill-group-heading">
                            <h3><i></i>NHÓM III. CONSTRAINTS &amp; DESIGN (DƯỚI CHUẨN)</h3>
                            <span>TB: 54% ⚠</span>
                        </div>
                        <div className="skill">
                            <div className="skill-label">
                                <span>Khóa &amp; Ràng buộc toàn vẹn (PK, FK, UNIQUE, CHECK)</span>
                                <strong>58%</strong>
                            </div>
                            <div className="skill-track"><span style={{ width: "58%" }}></span></div>
                        </div>
                        <div className="skill">
                            <div className="skill-label">
                                <span>Thiết kế lược đồ &amp; Chuẩn hóa (1NF, 2NF, 3NF, BCNF)</span>
                                <strong>48%</strong>
                            </div>
                            <div className="skill-track"><span style={{ width: "48%" }}></span></div>
                        </div>
                        <div className="skill">
                            <div className="skill-label">
                                <span>Lập luận thiết kế khái niệm (Entity &amp; Trade-offs)</span>
                                <strong>42%</strong>
                            </div>
                            <div className="skill-track"><span style={{ width: "42%" }}></span></div>
                        </div>
                    </section>
                </div>
            </div>
        </section>
        {/* Phân tích */}
        <section className="panel analysis-panel">
            <div className="analysis-heading">
                <span className="analysis-icon">
                    <svg className="icon"><use href="#learner-i-sparkles"></use></svg>
                </span>
                <div>
                    <h2>Chẩn đoán lỗ hổng &amp; Đề xuất từ AI</h2>
                    <p>
                        Phân tích năng lực chuyên sâu &amp; cá nhân hóa lộ trình bù khuyết theo chuẩn kiểm định CLO
                    </p>
                </div>
            </div>
            <div className="analysis-grid">
                <article className="analysis-card strengths">
                    <div className="analysis-card-heading">
                        <h3>
                            <svg className="icon"><use href="#learner-i-shield"></use></svg> 1. ĐIỂM MẠNH
                        </h3>
                        <span className="badge badge-green">Đạt chuẩn môn học</span>
                    </div>
                    <p className="analysis-intro">
                        Nắm vững kỹ năng thao tác và truy xuất dữ liệu với tư duy cú pháp chặt chẽ và tốc độ xử lý câu lệnh tốt:
                    </p>
                    <div className="finding">
                        <div className="finding-heading">
                            <h4>SQL Querying (Truy vấn quan hệ)</h4>
                            <span>85%</span>
                        </div>
                        <p>
                            Thao tác thành thạo cú pháp lệnh SELECT, mệnh đề điều kiện WHERE, sắp xếp ORDER BY, khử trùng lặp DISTINCT cùng các kỹ thuật nối JOIN và gom nhóm GROUP BY / HAVING.
                        </p>
                    </div>
                    <div className="finding">
                        <div className="finding-heading">
                            <h4>DML Data Manipulation (Thao tác dữ liệu)</h4>
                            <span>88%</span>
                        </div>
                        <p>
                            Đảm bảo tính nhất quán và kiểm soát dữ liệu chính xác khi thực thi các thao tác cập nhật bảng
                            <code>INSERT</code>, <code>UPDATE</code>,
                            <code>DELETE</code> theo đúng logic nghiệp vụ.
                        </p>
                    </div>
                </article>
                <article className="analysis-card weaknesses">
                    <div className="analysis-card-heading">
                        <h3>
                            <svg className="icon"><use href="#learner-i-warning"></use></svg> 2. ĐIỂM YẾU
                        </h3>
                        <span className="badge badge-rose">Dưới chuẩn: 54% / 60%</span>
                    </div>
                    <p className="analysis-intro">
                        Toàn bộ kỹ năng thuộc Nhóm III (Ràng buộc &amp; Thiết kế) chưa đạt ngưỡng yêu cầu môn học, tiềm ẩn rủi ro sai lệch cơ sở dữ liệu:
                    </p>
                    <div className="finding">
                        <div className="finding-heading">
                            <h4>Khóa &amp; Ràng buộc toàn vẹn (PK, FK, CHECK)</h4>
                            <span>58%</span>
                        </div>
                        <p>
                            Chưa xác định chặt chẽ miền giá trị, còn thiếu sót các ràng buộc tham chiếu ngoại (ON DELETE CASCADE/SET NULL) dẫn tới nguy cơ mất toàn vẹn thực thể.
                        </p>
                    </div>
                    <div className="finding">
                        <div className="finding-heading">
                            <h4>Thiết kế lược đồ &amp; Chuẩn hóa (1NF - BCNF)</h4>
                            <span>48%</span>
                        </div>
                        <p>
                            Dễ gặp dị thường thêm/xóa/sửa (Update/Delete Anomalies) và vi phạm phân rã nối không mất mát dữ liệu (Lossless Join) khi xử lý bài toán phụ thuộc hàm tổng quát.
                        </p>
                    </div>
                    <div className="finding">
                        <div className="finding-heading">
                            <h4>Lập luận thiết kế khái niệm (Entity &amp; Trade-offs)</h4>
                            <span>42%</span>
                        </div>
                        <p>
                            Lúng túng khi cân nhắc giữa hiệu năng truy vấn và mức độ dư thừa thông tin khi khử chuẩn hóa (Denormalization).
                        </p>
                    </div>
                </article>
            </div>
            <section className="roadmap">
                <div className="roadmap-heading">
                    <h3>KẾT LUẬN &amp; LỘ TRÌNH TÍCH HỢP CÁC BÀI KIỂM TRA ĐÃ LÀM</h3>
                    <p>Tổng hợp phân tích và kết quả chấm điểm từ các bài kiểm tra của sinh viên</p>
                </div>
                <div className="roadmap-grid">
                    <article className="roadmap-card">
                        <div className="roadmap-label">
                            <svg className="icon"><use href="#learner-i-chart"></use></svg> AI ĐÁNH GIÁ
                        </div>
                        <h4>Ưu thế duy trì qua 5 bài thi</h4>
                        <span className="badge badge-green">85% - 92% Ổn định</span>
                        <p>
                            Qua tổng hợp 5 bài kiểm tra gần nhất, sinh viên thể hiện kỹ năng truy vấn vượt trội với 92% ở
                            <code>SELECT</code> cơ bản và 82% ở
                            <code>JOIN/Aggregates</code>. Kỹ năng DML và CTE có độ chính xác cao, tốc độ xử lý nhanh.
                        </p>
                        <div className="roadmap-tags">
                            <span>Ưu thế: Logic quan hệ &amp; Tốc độ</span>
                            <strong>5/5 bài đạt trên chuẩn</strong>
                        </div>
                    </article>
                    <article className="roadmap-card diagnosis">
                        <div className="roadmap-label">
                            <svg className="icon"><use href="#learner-i-warning"></use></svg> AI CHẨN ĐOÁN
                        </div>
                        <h4>Điểm nghẽn lặp lại qua các bài kiểm tra</h4>
                        <span className="badge badge-rose">42% - 54% Tái diễn</span>
                        <p>
                            Đối soát lịch sử làm bài cho thấy sinh viên liên tục mất điểm ở lý thuyết chuẩn hóa
                            <code>1NF - BCNF</code> và ràng buộc khóa ngoại
                            <code>ON DELETE CASCADE</code> qua 3/5 bài gần đây. Lỗi phân rã và dị thường dữ liệu xuất hiện ở cả trắc nghiệm lẫn thực hành.
                        </p>
                        <div className="roadmap-tags">
                            <span>Cảnh báo: 3/5 bài dưới chuẩn nhóm III</span>
                            <strong>Cần bổ khuyết</strong>
                        </div>
                    </article>
                    <article className="roadmap-card recommendation">
                        <div className="roadmap-label">
                            <svg className="icon"><use href="#learner-i-target"></use></svg> AI ĐỀ XUẤT
                        </div>
                        <h4>Lộ trình khắc phục từ lỗi sai thực tế</h4>
                        <span className="badge badge-cyan">Cá nhân hóa</span>
                        <p>
                            Tập trung ôn lại 12 câu hỏi và tình huống làm sai. Ưu tiên ba chuyên đề: tìm khóa ứng viên bằng bao đóng
                            <code>X+</code>, chứng minh bảo toàn phụ thuộc hàm và thực hành thiết lập Foreign Key Constraint an toàn.
                        </p>
                        <div className="roadmap-tags">
                            <span>Kế hoạch: Trọng tâm sửa lỗi 5 bài đã thi</span>
                            <strong>Dự kiến +18% điểm số</strong>
                        </div>
                    </article>
                </div>
            </section>
            <div className="analysis-footer">
                <p  >
                    <svg className="icon"><use href="#learner-i-sparkles"></use></svg> Dữ liệu được AI phân tích &amp; tích hợp từ bài kiểm tra đã nộp
                </p>
                <div className="analysis-actions">
                    <Link to="/Phan_tich_Learner"
                        className="button button-secondary"
                        >
                        Xem phân tích chi tiết
                    <svg className="icon" aria-hidden="true">
                        <use href="#learner-i-arrow" />
                    </svg>
                    </Link>
                    <Link className="button button-primary" to="/Bai_kiem_tra_Learner">
                        Bắt đầu làm bài kiểm tra
                        <svg className="icon"><use href="#learner-i-arrow"></use></svg>
                    </Link>
                </div>
            </div>
        </section>
    </main>
    <footer className="footer">
        <div className="container footer-inner">
            <p>
                <strong>DBCAS</strong>
                <span>•</span> Nền tảng tự động Đánh giá Năng lực CSDL
            </p>
            <nav aria-label="Liên kết hỗ trợ">
                <Link to="/Quy_che">Quy chế khảo thí</Link>
                <Link to="/Tai_lieu#chuan-hoa">Chuẩn hóa 3NF</Link>
                <Link to="/Tai_lieu#sql">Tài liệu SQL</Link>
                <Link to="/Ho_tro">Hỗ trợ</Link>
            </nav>
        </div>
    </footer>
    <div className={`toast${toastVisible ? " show" : ""}`} role="status">Bạn chưa có thông báo mới.</div>
    
    </div>
  );
}
