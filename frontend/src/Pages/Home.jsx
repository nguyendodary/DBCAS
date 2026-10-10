import "./Home.css";
import video from "./hinhnen_Home.mp4";
import poster from "./hinhnen_Home.jpg";

export default function Home({
  loginHref = "/Dang_nhap",
  registerHref = "/Dang_ky",

  // TODO BE: truyền trạng thái đăng nhập từ hệ thống xác thực.
  isLoggedIn = false,

  assessmentHref = "/Bai_kiem_tra_Learner",
  analysisHref = "/Phan_tich_Learner",
}) {
  const assessmentTarget = isLoggedIn ? assessmentHref : loginHref;
  const analysisTarget = isLoggedIn ? analysisHref : loginHref;

  return (
    <div className="dbcas-landing">
      {/* Video và ảnh phải nằm cùng thư mục với Home.jsx */}
      <video
        className="bg-video"
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        poster={poster}
        aria-hidden="true"
      >
        <source src={video} type="video/mp4" />
      </video>

      <div className="main-container">
        {/* Header */}
        <header className="header">
          <div className="logo-area">
            <div className="logo-text-group">
              <span className="logo-title">DBCAS</span>
              <span className="logo-subtitle">AI SKILL ANALYTICS</span>
            </div>

            <div className="logo-desc">
              DATABASE COMPETENCY ASSESSMENT SYSTEM
            </div>
          </div>

          <div className="auth-buttons">
            <a href={loginHref} className="btn-login">
              Đăng nhập
            </a>

            <a href={registerHref} className="btn-register">
              Đăng ký
            </a>
          </div>
        </header>

        {/* Giới thiệu */}
        <section className="hero-section">
          <div className="badge-wrapper">
            <div className="badge-dot-group">
              <span className="dot light" />
              <span className="dot dark" />
            </div>

            <span className="badge-text">
              HỆ THỐNG ĐÁNH GIÁ NĂNG LỰC CSDL THẾ HỆ MỚI
            </span>
          </div>

          <h1 className="hero-title">
            Đánh Giá Năng Lực &amp; Phân Tích AI
            <br />
            Cho Cơ Sở Dữ Liệu
          </h1>

          <p className="hero-desc">
            Nền tảng khảo sát, thực thi và phân tích đồ án cơ sở dữ liệu tự
            động theo khung chuẩn học thuật và doanh nghiệp với Docker
            Sandbox và AI Rubric.
          </p>

          <div className="hero-actions">
            <a href={assessmentTarget} className="btn btn-primary">
              🚀 Bắt đầu khảo thí AI
            </a>

            <a href={analysisTarget} className="btn btn-secondary">
              📊 Xem sơ đồ năng lực
            </a>
          </div>
        </section>

        {/* Thống kê */}
        <section className="stats-section">
          <div className="stat-card">
            <div className="stat-number">1,250+</div>

            <div className="stat-label">
              Sinh viên đã hoàn thành khảo sát
            </div>

            <div className="stat-sub">
              Tích hợp toàn diện 8 học phần CSDL
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-number green">94.8%</div>

            <div className="stat-label">
              Đạt chuẩn kết quả học tập CLO
            </div>

            <div className="stat-sub">
              Chuẩn đầu ra ABET &amp; ACM/IEEE Curricula
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-number blue">100%</div>

            <div className="stat-label">
              Tự động hóa qua Docker &amp; AI Rubric
            </div>

            <div className="stat-sub">
              Chống gian lận &amp; đánh giá tức thời
            </div>
          </div>
        </section>

        {/* Ba trụ cột khảo thí */}
        <section className="pillars-section">
          <div className="section-header">
            <div className="section-badge">
              <span>🛡️ QUY TRÌNH KHẢO THÍ CHUẨN HÓA</span>
            </div>

            <h2 className="section-title">
              3 Trụ Cột Khảo Thí Năng Lực Toàn Diện
            </h2>

            <p className="section-desc">
              Cơ chế khảo thí đa tầng phối hợp kiểm tra nhận thức, năng lực
              lập trình cơ sở dữ liệu thực tiễn và tư duy thiết kế kiến
              trúc hệ thống dữ liệu lớn.
            </p>
          </div>

          <div className="pillars-grid">
            <div className="pillar-card">
              <div className="pillar-top">
                <span className="pillar-tag">PHẦN 1 • NỀN TẢNG</span>
                <div className="pillar-icon">📖</div>
              </div>

              <h3 className="pillar-name">TRẮC NGHIỆM CSDL</h3>

              <p className="pillar-text">
                Đánh giá kiến thức nền tảng, mô hình quan hệ ERD, toàn
                vẹn dữ liệu, khóa chính - ngoại và kỹ thuật chuẩn hóa
                dữ liệu từ 1NF đến BCNF.
              </p>

              <div className="pillar-footer">
                <span className="pillar-info">
                  Bank 500+ câu hỏi xáo trộn
                </span>
              </div>
            </div>

            <div className="pillar-card">
              <div className="pillar-top">
                <span className="pillar-tag">PHẦN 2 • THỰC NGHIỆM</span>
                <div className="pillar-icon">💻</div>
              </div>

              <h3 className="pillar-name">THỰC NGHIỆM SQL LAB</h3>

              <p className="pillar-text">
                Chấm tự động cô lập qua Docker Sandbox. Kiểm tra các câu
                truy vấn phức tạp (CTE, Window Functions, Subquery,
                Grouping) và đánh giá tối ưu hóa Indexing.
              </p>

              <div className="pillar-footer">
                <span className="pillar-info">
                  Docker Sandbox cô lập (Postgres/MySQL)
                </span>
              </div>
            </div>

            <div className="pillar-card">
              <div className="pillar-top">
                <span className="pillar-tag">PHẦN 3 • CHUYÊN SÂU</span>
                <div className="pillar-icon">🤖</div>
              </div>

              <h3 className="pillar-name">TỰ LUẬN KIẾN TRÚC</h3>

              <p className="pillar-text">
                Đối chiếu Rubric và chấm thông minh qua LLM API. Phân
                tích bài toán kiến trúc phân tán thực tế: Sharding,
                Partitioning, ACID, Concurrency Control và High
                Availability.
              </p>

              <div className="pillar-footer">
                <span className="pillar-info">
                  Rubric đa tầng + LLM Verification
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="footer">
          <p>
            © 2026 DBCAS Skill Analytics. All rights reserved. Hỗ trợ
            đào tạo công nghệ CSDL.
          </p>
        </footer>
      </div>
    </div>
  );
}