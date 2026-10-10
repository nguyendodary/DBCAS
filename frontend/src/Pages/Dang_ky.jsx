import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Dang_ky.css";
import background from "./hinhnen.png";

const initialValues = {
  fullname: "", username: "", studentId: "", major: "",
  password: "", confirmPassword: "", terms: false,
};

function getErrors(values) {
  const errors = {};
  const name = values.fullname.trim();
  const account = values.username.trim();
  if (!name) errors.fullname = "Vui lòng nhập họ và tên.";
  else if (name.split(/\s+/).length < 2) errors.fullname = "Họ và tên phải có ít nhất 2 từ.";
  if (!account) errors.username = "Vui lòng nhập email hoặc tên đăng nhập.";
  else if (account.includes("@")) {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(account)) errors.username = "Email không đúng định dạng.";
  } else if (!/^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])\S{6,}$/.test(account)) {
    errors.username = "Tên đăng nhập cần ít nhất 6 ký tự, có chữ hoa, chữ thường và số, không có khoảng trắng.";
  }
  if (!/^[0-9]{11}$/.test(values.studentId)) errors.studentId = "Mã số sinh viên phải có đúng 11 chữ số.";
  if (!values.major) errors.major = "Vui lòng chọn ngành học.";
  if (!values.password) errors.password = "Vui lòng nhập mật khẩu.";
  else if (!/[\p{L}\p{N}]/u.test(values.password)) errors.password = "Mật khẩu phải có ít nhất 1 chữ hoặc 1 số.";
  if (!values.confirmPassword) errors.confirmPassword = "Vui lòng nhập lại mật khẩu.";
  else if (values.confirmPassword !== values.password) errors.confirmPassword = "Mật khẩu nhập lại không khớp.";
  if (!values.terms) errors.terms = "Bạn cần đồng ý với điều khoản để đăng ký.";
  return errors;
}

export default function DangKy({
  onRegister,
  loginHref = "/Dang_nhap", homeHref = "/",
  termsHref = "#", privacyHref = "#",
}) {
  const navigate = useNavigate();
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [visible, setVisible] = useState({ password: false, confirmPassword: false });
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [registered, setRegistered] = useState(false);
  const fieldRefs = useRef({});
  const pending = useRef(false);

  useEffect(() => {
    if (!registered) return;
    const timer = setTimeout(() => navigate(loginHref), 1500);
    return () => clearTimeout(timer);
  }, [registered, loginHref, navigate]);

  function validateField(key) {
    setErrors(current => ({ ...current, [key]: getErrors(values)[key] || "" }));
  }

  function changeField(key, value) {
    if (key === "studentId") value = value.replace(/[^0-9]/g, "").slice(0, 11);
    const next = { ...values, [key]: value };
    setValues(next);
    setMessage("");
    const nextErrors = getErrors(next);
    setErrors(current => {
      const updated = { ...current };
      if (current[key] || key === "major" || key === "terms") updated[key] = nextErrors[key] || "";
      if (key === "password" && next.confirmPassword) updated.confirmPassword = nextErrors.confirmPassword || "";
      return updated;
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (pending.current || registered) return;
    const nextErrors = getErrors(values);
    setErrors(nextErrors);
    setMessage("");
    const firstInvalid = Object.keys(nextErrors)[0];
    if (firstInvalid) {
      fieldRefs.current[firstInvalid]?.focus();
      return;
    }
    if (!onRegister) {
      // TODO BE: truyền onRegister để gọi API tạo tài khoản.
      // Chưa có BE: chỉ kiểm tra giao diện, không lưu hay tạo tài khoản.
      setMessage("Thông tin hợp lệ. Chưa kết nối backend nên tài khoản chưa được tạo.");
      return;
    }
    pending.current = true;
    setSubmitting(true);
    try {
      // TODO BE: API kiểm tra trùng email/MSSV và tạo tài khoản Learner.
      // Trả { success: true } khi API xác nhận thành công; throw Error khi thất bại.
      const result = await onRegister({
        fullname: values.fullname.trim(), username: values.username.trim(),
        studentId: values.studentId, major: values.major,
        password: values.password, acceptedTerms: values.terms,
      });
      if (result?.success !== true) throw new Error("Đăng ký chưa thành công. Vui lòng thử lại.");
      setValues(initialValues);
      setMessage("Đăng ký thành công! Đang chuyển về trang đăng nhập...");
      setRegistered(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Đăng ký thất bại. Vui lòng thử lại.");
    } finally {
      pending.current = false;
      setSubmitting(false);
    }
  }

  return (
<div className="dbcas-register" style={{ backgroundImage: `linear-gradient(rgba(11,16,29,.85), rgba(11,16,29,.85)), url(${background})` }}>
        <div className="main-central">
            {/* Cột bên trái */}
            <div className="container">
                <div className="heading-margin">
                    <div className="heading">
                        <p className="nh-gi-n-ng-l-c-CSDL">
                            <span className="text-wrapper">
                                Đánh giá năng lực CSDL<br />
                            </span>
                            <span className="span">
                                hỗ trợ chuyên sâu bởi AI
                            </span>
                        </p>
                    </div>
                </div>
                <div className="margin">
                    <div className="n-n-t-ng-kh-o-s-t-th-wrapper">
                        <p className="n-n-t-ng-kh-o-s-t-th">
                            Nền tảng khảo sát, thực thi và phân tích đồ án cơ sở dữ liệu tự động theo khung chuẩn học thuật và doanh nghiệp.
                        </p>
                    </div>
                </div>
                <div className="container-wrapper">
                    <div className="div">
                        <div className="overlay-border">
                            <div className="div-wrapper">
                                <div className="div-2">
                                    <span className="feature-badge-text">⚡</span>
                                </div>
                            </div>
                            <div className="container-2">
                                <div className="container-3">
                                    <p className="text">
                                        Chấm tự động Docker Sandbox
                                    </p>
                                </div>
                                <div className="container-4">
                                    <p className="p">
                                        Thực thi truy vấn SQL an toàn, cô lập và tức thời
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="overlay-border">
                            <div className="overlay-border-2">
                                <div className="div-2">
                                    <span className="feature-badge-text">✨</span>
                                </div>
                            </div>
                            <div className="container-5">
                                <div className="container-3">
                                    <p className="text">
                                        Đánh giá Rubric AI qua LLM API
                                    </p>
                                </div>
                                <div className="container-4">
                                    <p className="text-2">
                                        Chấm điểm tối ưu hóa chỉ mục, chuẩn hóa dữ liệu &amp; thiết kế ERD
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="overlay-border">
                            <div className="overlay-border-3">
                                <div className="div-2">
                                    <span className="feature-badge-text">📊</span>
                                </div>
                            </div>
                            <div className="container-6">
                                <div className="container-3">
                                    <p className="text">
                                        Phân tích Skill Gap &amp; Lộ trình học
                                    </p>
                                </div>
                                <div className="container-4">
                                    <p className="text-2">
                                        Báo cáo năng lực đa chiều cá nhân hóa cho từng sinh viên
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {/* Cột bên phải: Form đăng ký */}
            <div className="overlay-border-wrapper">
                <div className="overlay-border-4 register-card register-form-box">
                    <div className="horizontal-divider"></div>
                    <div className="container-7">
                        <div className="container-8">
                            <div className="div-wrapper-2">
                                <div className="text-wrapper-2 register-title">
                                    Đăng ký tài khoản
                                </div>
                            </div>
                        </div>
                        <div className="container-9">
                            <p className="text-wrapper-3 register-subtitle">
                                Vui lòng điền thông tin để tạo tài khoản sinh viên
                            </p>
                        </div>
                    </div>
                    <form className="form" id="registerForm" onSubmit={handleSubmit} noValidate>
                        {/* Họ và tên */}
                        <div className={`container-11${errors.fullname ? " has-error" : ""}`}>
                            <div className="container-12">
                                <div className="div-2">
                                    <label className="label" htmlFor="input-fullname">
                                        Họ và tên
                                    </label>
                                </div>
                            </div>
                            <div className="container-14 register-input">
                                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                    <circle cx="12" cy="8" r="4"></circle>
                                    <path
                                        d="M4 20c0-4.2 3.6-7 8-7s8 2.8 8 7"
                                    ></path>
                                </svg>
                                <input className="container-15 has-icon" type="text" id="input-fullname" name="fullname" placeholder="Nguyễn Văn A" autoComplete="name" aria-describedby="error-fullname" required  value={values.fullname} onChange={event => changeField("fullname", event.target.value)} onBlur={() => validateField("fullname")} aria-invalid={Boolean(errors.fullname)} ref={node => { fieldRefs.current.fullname = node; }} />
                            </div>
                            <p className="field-error" id="error-fullname" role="alert">{errors.fullname}</p>
                        </div>
                        {/* Email hoặc tên đăng nhập */}
                        <div className={`container-11${errors.username ? " has-error" : ""}`}>
                            <div className="container-12">
                                <div className="div-2">
                                    <label className="label" htmlFor="input-email">
                                        Email / Tên đăng nhập
                                    </label>
                                </div>
                            </div>
                            <div className="container-14 register-input">
                                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                    <path
                                        d="M3 6.5A2.5 2.5 0 0 1 5.5 4H10l2 2h6.5A2.5 2.5 0 0 1 21 8.5v8A2.5 2.5 0 0 1 18.5 19h-13A2.5 2.5 0 0 1 3 16.5v-10z"
                                    ></path>
                                    <path d="M3 9h18"></path>
                                </svg>
                                <input className="container-15 has-icon" type="text" id="input-email" name="username" placeholder="Nhập email hoặc tên đăng nhập..." autoComplete="username" aria-describedby="error-email" required  value={values.username} onChange={event => changeField("username", event.target.value)} onBlur={() => validateField("username")} aria-invalid={Boolean(errors.username)} ref={node => { fieldRefs.current.username = node; }} />
                            </div>
                            <p className="field-error" id="error-email" role="alert">{errors.username}</p>
                        </div>
                        {/* MSSV và ngành học */}
                        <div className="register-row">
                            <div className={`container-11 register-col${errors.studentId ? " has-error" : ""}`}>
                                <div className="container-12">
                                    <div className="div-2">
                                        <label className="label" htmlFor="input-mssv">
                                            Mã số sinh viên
                                        </label>
                                    </div>
                                </div>
                                <div className="container-14 register-input">
                                    <input className="container-15 no-icon" type="text" id="input-mssv" name="studentId" placeholder="Ví dụ: 29247801280" inputMode="numeric" maxLength="11" pattern="[0-9]{11}" aria-describedby="error-mssv" required  value={values.studentId} onChange={event => changeField("studentId", event.target.value)} onBlur={() => validateField("studentId")} aria-invalid={Boolean(errors.studentId)} ref={node => { fieldRefs.current.studentId = node; }} />
                                </div>
                                <p className="field-error" id="error-mssv" role="alert">{errors.studentId}</p>
                            </div>
                            <div className={`container-11 register-col${errors.major ? " has-error" : ""}`}>
                                <div className="container-12">
                                    <div className="div-2">
                                        <label className="label" htmlFor="input-major">
                                            Ngành học
                                        </label>
                                    </div>
                                </div>
                                <div className="container-14 register-input">
                                    <select className="container-15 no-icon" id="input-major" name="major" aria-describedby="error-major" required value={values.major} onChange={event => changeField("major", event.target.value)} onBlur={() => validateField("major")} aria-invalid={Boolean(errors.major)} ref={node => { fieldRefs.current.major = node; }}>
                                        <option value="" disabled hidden>
                                            Chọn ngành học
                                        </option>
                                        <option value="Kỹ thuật Phần mềm">
                                            Kỹ thuật Phần mềm
                                        </option>
                                        <option value="Khoa học Máy tính">
                                            Khoa học Máy tính
                                        </option>
                                        <option value="Hệ thống Thông tin Quản lý">
                                            Hệ thống Thông tin Quản lý
                                        </option>
                                        <option value="An ninh mạng">
                                            An ninh mạng
                                        </option>
                                        <option value="Công nghệ phần mềm">
                                            Công nghệ phần mềm
                                        </option>
                                    </select>
                                    <svg className="select-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </div>
                                <p className="field-error" id="error-major" role="alert">{errors.major}</p>
                            </div>
                        </div>
                        {/* Mật khẩu */}
                        <div className={`container-11${errors.password ? " has-error" : ""}`}>
                            <div className="container-12">
                                <div className="div-2">
                                    <label className="label" htmlFor="input-password">
                                        Mật khẩu
                                    </label>
                                </div>
                            </div>
                            <div className="container-14 register-input">
                                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                    <rect
                                        x="3"
                                        y="11"
                                        width="18"
                                        height="11"
                                        rx="2"
                                    ></rect>
                                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                                </svg>
                                <input className="container-15 has-eye" type={visible.password ? "text" : "password"} id="input-password" name="password" placeholder="Nhập mật khẩu..." autoComplete="new-password" aria-describedby="error-password" required  value={values.password} onChange={event => changeField("password", event.target.value)} onBlur={() => validateField("password")} aria-invalid={Boolean(errors.password)} ref={node => { fieldRefs.current.password = node; }} />
                                <button type="button" className="password-toggle" onClick={() => setVisible(current => ({ ...current, password: !current.password }))} title={visible.password ? "Ẩn mật khẩu" : "Hiện mật khẩu"} aria-label={visible.password ? "Ẩn mật khẩu" : "Hiện mật khẩu"} aria-pressed={visible.password} aria-controls="input-password">
<svg
                                        id="eyeIcon1"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        width="17"
                                        height="17"
                                        aria-hidden="true"
                                    >
                                        <path
                                            d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
                                        ></path>
                                        <circle cx="12" cy="12" r="3"></circle>
                                    {visible.password && <line x1="1" y1="1" x2="23" y2="23" />}
</svg>
                                </button>
                            </div>
                            <p className="field-error" id="error-password" role="alert">{errors.password}</p>
                        </div>
                        {/* Nhập lại mật khẩu */}
                        <div className={`container-11${errors.confirmPassword ? " has-error" : ""}`}>
                            <div className="container-12">
                                <div className="div-2">
                                    <label className="label" htmlFor="input-confirm-password">
                                        Nhập lại mật khẩu
                                    </label>
                                </div>
                            </div>
                            <div className="container-14 register-input">
                                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                    <rect
                                        x="3"
                                        y="11"
                                        width="18"
                                        height="11"
                                        rx="2"
                                    ></rect>
                                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                                </svg>
                                <input className="container-15 has-eye" type={visible.confirmPassword ? "text" : "password"} id="input-confirm-password" name="confirmPassword" placeholder="Nhập lại mật khẩu..." autoComplete="new-password" aria-describedby="error-confirm" required  value={values.confirmPassword} onChange={event => changeField("confirmPassword", event.target.value)} onBlur={() => validateField("confirmPassword")} aria-invalid={Boolean(errors.confirmPassword)} ref={node => { fieldRefs.current.confirmPassword = node; }} />
                                <button type="button" className="password-toggle" onClick={() => setVisible(current => ({ ...current, confirmPassword: !current.confirmPassword }))} title={visible.confirmPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"} aria-label={visible.confirmPassword ? "Ẩn mật khẩu xác nhận" : "Hiện mật khẩu xác nhận"} aria-pressed={visible.confirmPassword} aria-controls="input-confirm-password">
<svg
                                        id="eyeIcon2"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        width="17"
                                        height="17"
                                        aria-hidden="true"
                                    >
                                        <path
                                            d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
                                        ></path>
                                        <circle cx="12" cy="12" r="3"></circle>
                                    {visible.confirmPassword && <line x1="1" y1="1" x2="23" y2="23" />}
</svg>
                                </button>
                            </div>
                            <p className="field-error" id="error-confirm" role="alert">{errors.confirmPassword}</p>
                        </div>
                        {/* Điều khoản */}
                        <div className={`container-11${errors.terms ? " has-error" : ""}`}>
                            <label className="terms-register">
                                <input
                                    type="checkbox"
                                    id="terms"
                                    aria-describedby="error-terms"
                                    required
                                  checked={values.terms} onChange={event => changeField("terms", event.target.checked)} aria-invalid={Boolean(errors.terms)} ref={node => { fieldRefs.current.terms = node; }} />
                                <span>
                                    Tôi đồng ý với
                                    <a href={termsHref}>Điều khoản dịch vụ</a>
                                    và
                                    <a href={privacyHref}>Chính sách bảo mật</a>
                                </span>
                            </label>
                            <p className="field-error" id="error-terms" role="alert">{errors.terms}</p>
                        </div>
                        <button type="submit" className="register-submit" disabled={submitting || registered}>
                            {submitting ? "ĐANG XỬ LÝ..." : "ĐĂNG KÝ"}
                        </button>
                    </form>
                    {/* Chuyển sang đăng nhập */}
                    <div className="horizontal-border">
                        <div className="paragraph">
                            <div className="text-8">
                                Đã có tài khoản?
                            </div>
                            <Link to={loginHref} className="register-login-link">
                                Đăng nhập ngay
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {/* Thông báo */}
        <div className={`toast-success${message ? " show" : ""}`} id="toast" role="status">
            {message}
        </div>
        {/* Thanh phía trên */}
        <div className="top-navigation">
            <div className="container-21">
                <Link to={homeHref} className="button-6">
                    <svg className="back-arrow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16" aria-hidden="true">
                        <line x1="19" y1="12" x2="5" y2="12"></line>
                        <polyline points="12 19 5 12 12 5"></polyline>
                    </svg>
                    <div className="container-10">
                        <div className="text-4">Quay lại</div>
                    </div>
                </Link>
                <div className="container-22">
                    <div className="container-23">
                        <div className="text-9">DBCAS</div>
                    </div>
                    <div className="container-24">
                        <div className="text-10">SKILL ANALYTICS</div>
                    </div>
                </div>
            </div>
        </div>
        {/* Thanh phía dưới */}
        <div className="system-bottom-bar">
            <div className="container-25">
                <div className="div-wrapper-2">
                    <p className="text-wrapper-7">
                        © 2026 DBCAS Skill Analytics. All rights reserved. Hỗ trợ đào tạo công nghệ CSDL.
                    </p>
                </div>
            </div>
        </div>
    </div>
  );
}
