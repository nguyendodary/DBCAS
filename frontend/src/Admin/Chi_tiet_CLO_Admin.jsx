import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useParams, useNavigate } from "react-router-dom";
import "./Chi_tiet_CLO_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";
const CLO_DEFINITIONS = [{
  id: 1,
  title: "Kỹ năng truy vấn dữ liệu",
  description: "SELECT, WHERE, JOIN, GROUP BY và truy vấn nâng cao.",
  strength: "Có khả năng sử dụng các câu lệnh truy vấn để khai thác dữ liệu.",
  weakness: "Cần củng cố cách xây dựng truy vấn và kiểm tra kết quả trả về.",
  recommendation: "Luyện thêm truy vấn nhiều bảng, gom nhóm và truy vấn lồng."
}, {
  id: 2,
  title: "Thao tác và định nghĩa dữ liệu",
  description: "INSERT, UPDATE, DELETE, CREATE, ALTER và quản lý dữ liệu.",
  strength: "Nắm được các thao tác dữ liệu và cách định nghĩa cấu trúc bảng.",
  weakness: "Cần củng cố cú pháp thao tác dữ liệu và kiểm soát phạm vi cập nhật.",
  recommendation: "Thực hành tạo bảng, thay đổi cấu trúc và thao tác dữ liệu có điều kiện."
}, {
  id: 3,
  title: "Ràng buộc và thiết kế CSDL",
  description: "Khóa, ràng buộc toàn vẹn, quan hệ và chuẩn hóa dữ liệu.",
  strength: "Có khả năng xác định cấu trúc dữ liệu và các ràng buộc cơ bản.",
  weakness: "Cần củng cố cách xác định quan hệ, khóa và chuẩn hóa dữ liệu.",
  recommendation: "Luyện xác định khóa chính, khóa ngoại và chuẩn hóa đến 3NF."
}];
function validScore(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const score = Number(value);
  return Number.isFinite(score) && score >= 0 && score <= 10 ? score : null;
}
function display(value) {
  return value === null || value === undefined || value === "" ? "Chưa cập nhật" : String(value);
}
function TextList({
  items,
  emptyText
}) {
  const values = Array.isArray(items) ? items.filter(item => typeof item === "string" && item.trim()) : [];
  return values.length ? <ul>
            {adminRender(values.map((item, index) => <li key={`${index}-${item}`}>{adminRender(item)}</li>))}
        </ul> : <p className="clod-muted">{adminRender(emptyText)}</p>;
}
export default function ChiTietCloAdmin({
  students = []
}) {
  useAdminLanguage();

  const location = useLocation();
  const {
    studentId
  } = useParams();
  const matches = item => item && String(item.studentId ?? item.id ?? "") === studentId;
  const student = (matches(location.state?.student) ? location.state.student : null) ?? (Array.isArray(students) ? students.find(matches) : null);
  const backLink = <Link className="clod-back" to="/CLO_Ky_nang_Admin">
            <span aria-hidden="true">←</span>{adminText(" Quay lại CLO & Kỹ năng ")}</Link>;
  if (!student) {
    return <div className="clod-page">
                <main className="clod-main">
                    <section className="clod-empty">
                        <h1>{adminText("Chưa có dữ liệu sinh viên")}</h1>
                        <p>{adminText("Quay lại danh sách và chọn “Xem chi tiết”.")}</p>
                        {adminRender(backLink)}
                    </section>
                </main>
            </div>;
  }

  /*
    Backend có thể trả về:
    student.cloAiDetails = [
      {
        id: 1,
        score: 8.2,
        status: "pass",
        summary: "Nhận xét tổng quan...",
        strengths: ["Điểm mạnh..."],
        weaknesses: ["Điểm cần cải thiện..."],
        recommendations: ["Đề xuất..."]
      }
    ];
        Nếu chưa có trường này, dùng dữ liệu tạm cho giao diện.
  */

  const isDemo = !Array.isArray(student.cloAiDetails);
  const results = CLO_DEFINITIONS.map((definition, index) => {
    if (!isDemo) {
      const result = student.cloAiDetails.find(item => String(item.id) === String(definition.id));
      return {
        ...definition,
        score: validScore(result?.score),
        status: result?.status === "pass" || result?.status === "weak" ? result.status : "pending",
        summary: result?.summary || "Chưa có nhận xét AI.",
        strengths: result?.strengths,
        weaknesses: result?.weaknesses,
        recommendations: result?.recommendations
      };
    }
    const score = validScore(student.skills?.[index]);
    const state = student.clos?.[index];
    const status = state === "pass" || state === true ? "pass" : state === "weak" || state === false ? "weak" : score !== null ? score >= 6 ? "pass" : "weak" : "pending";
    return {
      ...definition,
      score,
      status,
      summary: status === "pass" ? "Sinh viên đạt yêu cầu của CLO này. Tiếp tục luyện tập để nâng cao khả năng vận dụng." : status === "weak" ? "Sinh viên cần củng cố kiến thức và thực hành thêm các nội dung thuộc CLO này." : "Chưa đủ dữ liệu để đánh giá CLO.",
      strengths: status === "pass" ? [definition.strength] : [],
      weaknesses: status === "weak" ? [definition.weakness] : [],
      recommendations: status === "pending" ? [] : [definition.recommendation]
    };
  });
  return <div className="clod-page" style={{
    backgroundImage: `
          linear-gradient(
            rgba(7, 11, 20, .85),
            rgba(7, 11, 20, .85)
          ),
          url(${background})
        `
  }}>
            <header className="clod-topbar admin-unified-topbar"><NotificationMenu role="admin" className="icon-button" />
                <div className="clod-brand">
                    <img src={logo} alt="DBCAS" draggable="false" />
                </div>

                <div className="clod-breadcrumb">
                    <Link to="/CLO_Ky_nang_Admin">{adminText(" CLO & Kỹ năng ")}</Link>
                    <span>/</span>
                    <strong>{adminText("Chi tiết CLO sinh viên")}</strong>
                </div>
            <AdminAccountMenu /></header>

            <main className="clod-main">
                <div className="clod-page-heading admin-unified-banner">
                    <div>
                        <span className="clod-eyebrow">{adminText("ĐÁNH GIÁ CHUẨN ĐẦU RA")}</span>
                        <h1>{adminText("Chi tiết năng lực CLO")}</h1>
                    </div>

                    {adminRender(backLink)}
                </div>

                <section className="clod-student">
                    <div>
                        <span>{adminText("Họ và tên")}</span>
                        <strong>{adminRender(display(student.name))}</strong>
                    </div>

                    <div>
                        <span>{adminText("Mã số sinh viên")}</span>
                        <strong>{adminRender(studentId)}</strong>
                    </div>

                    <div>
                        <span>{adminText("Ngành đào tạo")}</span>
                        <strong>{adminRender(display(student.major))}</strong>
                    </div>
                </section>

                <div className="clod-analysis-heading">
                    <h2>{adminText("Đánh giá từng CLO")}</h2>
                    <span>{adminRender(isDemo ? "Dữ liệu tạm" : "Kết quả phân tích AI")}</span>
                </div>

                <div className="clod-results">
                    {adminRender(results.map(clo => <section className="clod-card" key={clo.id}>
                            <div className="clod-card-head">
                                <div className="clod-title">
                                    <span className="clod-number">0{adminRender(clo.id)}</span>

                                    <div>
                                        <span className="clod-code">CLO {adminRender(clo.id)}</span>
                                        <h2>{adminRender(clo.title)}</h2>
                                        <p>{adminRender(clo.description)}</p>
                                    </div>
                                </div>

                                <div className="clod-result">
                                    <strong>
                                        {adminRender(clo.score === null ? "—" : clo.score.toFixed(2))}
                                        <small>/10</small>
                                    </strong>

                                    <span className={`clod-status ${clo.status}`}>
                                        {adminRender(clo.status === "pass" ? "Đạt chuẩn" : clo.status === "weak" ? "Cần cải thiện" : "Chưa có kết quả")}
                                    </span>
                                </div>
                            </div>

                            <div className="clod-summary">
                                <span>{adminText("Nhận xét tổng quan")}</span>
                                <p>{adminRender(clo.summary)}</p>
                            </div>

                            <div className="clod-detail-grid">
                                <article className="clod-detail strengths">
                                    <h3>{adminText("Điểm mạnh")}</h3>

                                    <TextList items={clo.strengths} emptyText="Chưa ghi nhận điểm mạnh cụ thể." />
                                </article>

                                <article className="clod-detail weaknesses">
                                    <h3>{adminText("Điểm cần cải thiện")}</h3>

                                    <TextList items={clo.weaknesses} emptyText="Chưa ghi nhận nội dung cần cải thiện." />
                                </article>
                            </div>

                            <div className="clod-recommendations">
                                <h3>{adminText("Đề xuất học tập")}</h3>

                                <TextList items={clo.recommendations} emptyText="Chưa có đề xuất học tập." />
                            </div>
                        </section>))}
                </div>

                <footer className="clod-footer">{adminText(" DBCAS · Đánh giá năng lực chuẩn đầu ra ")}</footer>
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