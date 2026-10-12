import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useParams, useNavigate } from "react-router-dom";
import "./Ho_so_thanh_vien_Admin.css";
import logo from "./logo1.png";
import background from "./SQL.jpg";
const CLO_NAMES = ["Truy vấn SQL", "DML & DDL", "Thiết kế & Ràng buộc"];
function display(value) {
  return value === null || value === undefined || value === "" ? "Chưa cập nhật" : String(value);
}
function validScore(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const score = Number(value);
  return Number.isFinite(score) && score >= 0 && score <= 10 ? score : null;
}
function validCount(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const count = Number(value);
  return Number.isInteger(count) && count >= 0 ? count : null;
}
function makeDemoOverview(student) {
  const suffix = Number(String(student.studentId ?? student.id ?? "").slice(-3));
  const index = Number.isFinite(suffix) ? Math.max(0, suffix - 1) : 0;
  return {
    completedTests: validCount(student.completedTests) ?? 50 + index % 31,
    threshold: 6,
    updatedAt: "12/10/2026",
    clos: CLO_NAMES.map((name, position) => ({
      id: position + 1,
      name,
      score: validScore(student.skills?.[position])
    }))
  };
}
function SummaryList({
  items,
  emptyText
}) {
  const values = Array.isArray(items) ? items.filter(item => typeof item === "string" && item.trim()) : [];
  return values.length ? <ul className="sv-list">
      {values.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
    </ul> : <p className="sv-muted">{emptyText}</p>;
}
export default function HoSoThanhVienAdmin({
  students = []
}) {
  const location = useLocation();
  const {
    studentId
  } = useParams();
  const matchesId = item => item && String(item.studentId ?? item.id ?? "") === studentId;
  const student = (matchesId(location.state?.student) ? location.state.student : null) ?? (Array.isArray(students) ? students.find(matchesId) : null);
  if (!student) {
    return <div className="sv-page">
        <main className="sv-main sv-empty">
          <h1>Chưa có dữ liệu sinh viên</h1>
          <p>Quay lại danh sách và chọn “Xem chi tiết”.</p>

          <Link className="sv-back" to="/Danh_gia_nang_luc_Admin">
            ← Quay lại danh sách
          </Link>
        </main>
      </div>;
  }

  // Ưu tiên kết quả tổng hợp từ backend.
  // Khi chưa có backend, dùng dữ liệu tạm từ trang danh sách.
  const isDemo = !student.aiAnalysis && !student.cloOverview;
  const analysis = student.aiAnalysis ?? student.cloOverview ?? makeDemoOverview(student);
  const threshold = validScore(analysis.threshold) ?? 6;
  const sourceClos = Array.isArray(analysis.clos) ? analysis.clos : [];
  const clos = CLO_NAMES.map((name, index) => {
    const result = sourceClos.find(item => String(item.id) === String(index + 1));
    return {
      id: index + 1,
      name,
      score: validScore(result?.score)
    };
  });
  const evaluated = clos.filter(clo => clo.score !== null);
  const passed = evaluated.filter(clo => clo.score >= threshold);
  const weak = evaluated.filter(clo => clo.score < threshold);
  const complete = evaluated.length === 3;
  const highestScore = evaluated.length ? Math.max(...evaluated.map(clo => clo.score)) : null;
  const strongest = evaluated.filter(clo => clo.score === highestScore);
  const completedTests = validCount(analysis.completedTests);
  const achievementPercent = complete ? Math.round(passed.length / 3 * 100) : null;
  const initials = String(student.name ?? "").trim().split(/\s+/).slice(-2).map(word => word[0] || "").join("");
  const statusText = !complete ? "Chưa đủ kết quả đánh giá" : passed.length === 3 ? "Đạt chuẩn đầu ra" : `Cần cải thiện ${weak.length} CLO`;
  const demoSummary = !complete ? "Cần bổ sung kết quả của cả 3 CLO để đánh giá đầy đủ năng lực sinh viên." : passed.length === 3 ? "Sinh viên đạt yêu cầu ở cả 3 chuẩn đầu ra. Có thể tiếp tục luyện tập các nội dung nâng cao để phát triển năng lực." : `Sinh viên đạt ${passed.length}/3 chuẩn đầu ra. Cần ưu tiên củng cố ${weak.map(clo => clo.name).join(", ")} để hoàn thiện năng lực cơ sở dữ liệu.`;
  const overallSummary = typeof analysis.summary === "string" && analysis.summary.trim() ? analysis.summary : isDemo ? demoSummary : "Chưa có nhận xét tổng quan từ AI.";
  const strengths = isDemo ? strongest.map(clo => `${clo.name} là năng lực nổi bật hiện tại.`) : analysis.strengths;
  const weaknesses = isDemo ? weak.map(clo => `Cần củng cố ${clo.name}.`) : analysis.weaknesses;
  const recommendations = isDemo ? weak.length ? weak.map(clo => `Ưu tiên thực hành thêm nội dung ${clo.name}.`) : complete ? ["Tiếp tục luyện tập các bài vận dụng nâng cao."] : [] : analysis.recommendations;
  return <div className="sv-page" style={{
    backgroundImage: `
          linear-gradient(
            rgba(7, 11, 20, .85),
            rgba(7, 11, 20, .85)
          ),
          url(${background})
        `
  }}>
      <header className="sp-topbar admin-unified-topbar">
        <div className="sp-brand">
          <img src={logo} alt="DBCAS" draggable="false" />
        </div>

        <div className="sp-breadcrumb">
          <Link to="/Danh_gia_nang_luc_Admin">
            Đánh giá năng lực
          </Link>
          <span>/</span>
          <strong>Hồ sơ sinh viên</strong>
        </div>
      <AdminAccountMenu /></header>

      <main className="sv-main">
        <div className="sv-heading admin-unified-banner">
          <div>
            <span className="sv-eyebrow">HỒ SƠ CÁ NHÂN</span>
            <h1>Tổng quan năng lực sinh viên</h1>
          </div>

          <Link className="sv-back" to="/Danh_gia_nang_luc_Admin">
            ← Quay lại danh sách
          </Link>
        </div>

        <section className="sv-profile">
          <div className="sv-identity">
            <span className="sv-avatar">{initials || "SV"}</span>

            <div>
              <h2>{display(student.name)}</h2>
              <p>MSSV · {studentId}</p>
              <span className="sv-status">{statusText}</span>
            </div>
          </div>

          <dl className="sv-info">
            <div>
              <dt>Email</dt>
              <dd>{display(student.email)}</dd>
            </div>

            <div>
              <dt>Ngành đào tạo</dt>
              <dd>{display(student.major)}</dd>
            </div>

            <div>
              <dt>Năm học</dt>
              <dd>{display(student.year)}</dd>
            </div>

            <div>
              <dt>Số điện thoại</dt>
              <dd>{display(student.phone)}</dd>
            </div>
          </dl>
        </section>

        <div className="sv-overview-grid">
          <section className="sv-card sv-achievement">
            <div className="sv-ring" style={{
            "--achievement": `${achievementPercent ?? 0}%`
          }} role="img" aria-label={complete ? `${passed.length} trong 3 CLO đạt chuẩn` : "Chưa đủ kết quả đánh giá CLO"}>
              <div>
                <strong>
                  {achievementPercent === null ? "—" : `${achievementPercent}%`}
                </strong>
                <span>CLO đạt chuẩn</span>
              </div>
            </div>

            <h2>
              {complete ? `${passed.length}/3 chuẩn đầu ra` : "Chưa đủ kết quả"}
            </h2>

            <p>
              Tỷ lệ CLO đạt yêu cầu trong hồ sơ năng lực.
            </p>
          </section>

          <section className="sv-card sv-overview">
            <div className="sv-stat-row">
              <div>
                <span>Bài kiểm tra đã làm</span>
                <strong>
                  {completedTests === null ? "—" : completedTests.toLocaleString("vi-VN")}
                </strong>
              </div>

              <div>
                <span>CLO cần cải thiện</span>
                <strong>{complete ? weak.length : "—"}</strong>
              </div>

              <div>
                <span>Cập nhật gần nhất</span>
                <strong className="sv-date">
                  {display(analysis.updatedAt)}
                </strong>
              </div>
            </div>

            <div className="sv-overall-review">
              <div className="sv-review-heading">
                <h2>Nhận định tổng quan</h2>
                <span>{isDemo ? "Dữ liệu tạm" : "Phân tích AI"}</span>
              </div>

              <p>{overallSummary}</p>
            </div>
          </section>
        </div>

        <section className="sv-card sv-clo-overview">
          <div className="sv-section-heading">
            <h2>Bức tranh năng lực</h2>
            <span>Chuẩn đạt {threshold}/10</span>
          </div>

          <div className="sv-clo-grid">
            {clos.map(clo => {
            const hasScore = clo.score !== null;
            const isPass = hasScore && clo.score >= threshold;
            return <article className="sv-clo" key={clo.id}>
                  <div className="sv-clo-heading">
                    <span>CLO {clo.id}</span>
                    <i className={!hasScore ? "pending" : isPass ? "pass" : "weak"} />
                  </div>

                  <h3>{clo.name}</h3>

                  <div className="sv-clo-bottom">
                    <strong>
                      {hasScore ? clo.score.toFixed(2) : "—"}
                      <small>/10</small>
                    </strong>

                    <span>
                      {!hasScore ? "Chưa có kết quả" : isPass ? "Đạt chuẩn" : "Cần cải thiện"}
                    </span>
                  </div>
                </article>;
          })}
          </div>
        </section>

        <div className="sv-insight-grid">
          <section className="sv-card sv-insight">
            <span className="sv-insight-label">ĐIỂM MẠNH</span>
            <h2>
              {isDemo && strongest.length ? strongest.map(clo => clo.name).join(", ") : "Năng lực nổi bật"}
            </h2>

            <SummaryList items={strengths} emptyText="Chưa có nhận xét điểm mạnh." />
          </section>

          <section className="sv-card sv-insight sv-insight-weak">
            <span className="sv-insight-label">ƯU TIÊN CẢI THIỆN</span>
            <h2>
              {isDemo && weak.length ? weak.map(clo => clo.name).join(", ") : isDemo && complete ? "Duy trì và nâng cao" : "Nội dung cần củng cố"}
            </h2>

            <SummaryList items={weaknesses} emptyText={isDemo && complete ? "Cả 3 CLO đều đạt chuẩn hiện tại." : "Chưa có nhận xét điểm yếu."} />
          </section>
        </div>

        <section className="sv-card sv-guidance">
          <div>
            <span className="sv-eyebrow">ĐỊNH HƯỚNG HỌC TẬP</span>
            <h2>Bước tiếp theo</h2>
          </div>

          <SummaryList items={recommendations} emptyText="Chưa có đề xuất học tập." />
        </section>

        <footer className="sv-footer">
          DBCAS · Hồ sơ năng lực sinh viên
        </footer>
      </main>
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