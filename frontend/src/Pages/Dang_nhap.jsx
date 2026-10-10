import { useRef, useState } from "react";
import "./Dang_nhap.css";
import background from "./hinhnen.png";

export default function DangNhap({
  onLogin, onNavigate,
  demoMode = true,
  homeHref = "/", registerHref = "/Dang_ky.html",
  forgotHref = "/Forgot_password", googleHref = "/Google",
  githubHref = "/GitHub",
  learnerHref = "/Home_Learner", adminHref = "/Home_Admin",
}) {
  const [role, setRole] = useState("learner");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [invalid, setInvalid] = useState({ username: false, password: false });
  const [submitting, setSubmitting] = useState(false);
  const pending = useRef(false);
  const usernameRef = useRef(null);
  const passwordRef = useRef(null);

  function clearError() {
    setError("");
    setInvalid({ username: false, password: false });
  }
  function changeRole(value) { setRole(value); clearError(); }

  async function handleLogin(event) {
    event.preventDefault();
    if (pending.current) return;
    const account = username.trim();
    // Giữ quy tắc định dạng của giao diện gốc. BE xác minh tài khoản thật.
    const validUsername = account.includes("@")
    ? /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(account)
    : /^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])\S{6,}$/.test(account);
    const validPassword = /[\p{L}\p{N}]/u.test(password);
    setInvalid({ username: !validUsername, password: !validPassword });
    if (!validUsername || !validPassword) {
      setError("Email/tên đăng nhập hoặc mật khẩu chưa đúng định dạng.");
      (!validUsername ? usernameRef : passwordRef).current?.focus();
      return;
    }
    clearError();
    pending.current = true;
    setSubmitting(true);
    try {
      let authenticatedRole;
      if (onLogin) {
        // TODO BE: gọi API, kiểm tra tài khoản/mật khẩu và trả { role } sau khi xác thực.
        // Không lưu mật khẩu. Việc quản lý phiên/token do lớp xác thực của nhóm xử lý.
        const result = await onLogin({ username: account, password, selectedRole: role, rememberMe });
        if (!result || !["learner", "admin"].includes(result.role)) {
          throw new Error("Không xác định được quyền tài khoản. Vui lòng kiểm tra kết quả đăng nhập.");
        }
        authenticatedRole = result.role;
      } else if (demoMode) {
        // CHỈ DEMO: chuyển trang theo tab đã chọn; không xác thực, không tạo phiên đăng nhập.
        authenticatedRole = role;
      } else {
        setError("Chức năng đăng nhập chưa được kết nối backend.");
        return;
      }
      const target = authenticatedRole === "admin" ? adminHref : learnerHref;
      if (onNavigate) onNavigate(target);
      else window.location.assign(target);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại. Vui lòng thử lại.");
    } finally {
      pending.current = false;
      setSubmitting(false);
    }
  }
  return (
<div className="ng-nhp" style={{ backgroundImage: `linear-gradient(rgba(11,16,29,0.85), rgba(11,16,29,0.85)), url(${background})` }}>
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
            {/* Cột bên phải */}
            <div className="overlay-border-wrapper">
                <div className="overlay-border-4">
                    <div className="horizontal-divider"></div>
                    <div className="container-7">
                        <div className="container-8">
                            <div className="div-wrapper-2">
                                <div className="text-wrapper-2">
                                    Đăng nhập hệ thống
                                </div>
                            </div>
                        </div>
                        <div className="container-9">
                            <p className="text-wrapper-3">
                                Vui lòng chọn phân hệ và nhập thông tin truy cập
                            </p>
                        </div>
                    </div>
                    {/* Chọn vai trò */}
                    <div className="background-border" id="roleSelector">
                        <button type="button" className={`button${role === "learner" ? " active" : ""}`} id="btnLearner" onClick={() => changeRole("learner")} aria-pressed={role === "learner"}>
                            <div className="container-10">
                                <div className="text-3">
                                    Học viên (Learner)
                                </div>
                            </div>
                        </button>
                        <button type="button" className={`button-2${role === "admin" ? " active" : ""}`} id="btnAdmin" onClick={() => changeRole("admin")} aria-pressed={role === "admin"}>
                            <div className="container-10">
                                <div className="text-4">
                                    Quản trị (Admin)
                                </div>
                            </div>
                        </button>
                    </div>
                    {/* Form đăng nhập */}
                    <form className="form" id="login-form" onSubmit={handleLogin} noValidate>
                        {/* Email hoặc tên đăng nhập */}
                        <div className="container-11">
                            <div className="container-12">
                                <div className="div-2">
                                    <label className="label" htmlFor="input-1">
                                        Email hoặc Tên đăng nhập
                                    </label>
                                </div>
                            </div>
                            <div className="container-14 input-wrapper-container">
                                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                    <path
                                        d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"
                                    ></path>
                                    <polyline
                                        points="22,6 12,13 2,6"
                                    ></polyline>
                                </svg>
                                <input className="container-15 has-icon" type="text" id="input-1" name="username" placeholder="Nhập tên đăng nhập hoặc email..." autoComplete="username" autoCapitalize="none" spellCheck="false" aria-describedby="login-error" aria-invalid={invalid.username} ref={usernameRef} value={username} onChange={event => { setUsername(event.target.value); clearError(); }} required />
                            </div>
                        </div>
                        {/* Mật khẩu */}
                        <div className="container-11">
                            <div className="container-8">
                                <div className="div-wrapper-2">
                                    <label className="text-wrapper-4" htmlFor="input-password">
                                        Mật khẩu
                                    </label>
                                </div>
                            </div>
                            <div className="container-14 input-wrapper-container">
                                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                    <rect
                                        x="3"
                                        y="11"
                                        width="18"
                                        height="11"
                                        rx="2"
                                        ry="2"
                                    ></rect>
                                    <path
                                        d="M7 11V7a5 5 0 0 1 10 0v4"
                                    ></path>
                                </svg>
                                <input className="container-15 has-icon has-right-icon" type={showPassword ? "text" : "password"} id="input-password" name="password" placeholder="Nhập mật khẩu..." autoComplete="current-password" aria-describedby="login-error" aria-invalid={invalid.password} ref={passwordRef} value={password} onChange={event => { setPassword(event.target.value); clearError(); }} required />
                                <button type="button" className="button-toggle-password" onClick={() => setShowPassword(value => !value)} title={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"} aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"} aria-controls="input-password" aria-pressed={showPassword}>
                                    <svg
                                        id="eyeIcon"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        width="16"
                                        height="16"
                                        aria-hidden="true"
                                    >
                                        <path
                                            d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
                                        ></path>
                                        <circle
                                            cx="12"
                                            cy="12"
                                            r="3"
                                        ></circle>
                                    {showPassword && <line x1="1" y1="1" x2="23" y2="23" />}
</svg>
                                </button>
                            </div>
                        </div>
                        {/* Ghi nhớ đăng nhập */}
                        <div className="container-16">
                            <div className="label-2">
                                <input type="checkbox" id="rememberMe" name="rememberMe" className="input-3" checked={rememberMe} onChange={event => setRememberMe(event.target.checked)} />
                                <div className="div-2">
                                    <label htmlFor="rememberMe" className="text-5" style={{ cursor: "pointer" }}>
                                        Ghi nhớ đăng nhập
                                    </label>
                                </div>
                            </div>
                            <div className="div-2">
                                <a href={forgotHref} className="forgot-password">
                                    Quên mật khẩu?
                                </a>
                            </div>
                        </div>
                        {/* Thông báo lỗi */}
                        <p id="login-error" role="alert" hidden={!error}>{error}</p>
                        {/* Nút đăng nhập */}
                        <button type="submit" className="button-3" disabled={submitting}>
                            <div className="container-17">
                                <span className="text-wrapper-6">
                                    {submitting ? "ĐANG ĐĂNG NHẬP..." : "ĐĂNG NHẬP"}
                                </span>
                            </div>
                            <div className="container-18"></div>
                        </button>
                    </form>
                    {/* Đường phân cách */}
                    <div className="container-19">
                        <div className="horizontal-divider-wrapper">
                            <div className="horizontal-divider-2"></div>
                        </div>
                        <div className="background">
                            <div className="or">OR</div>
                        </div>
                    </div>
                    {/* Google và GitHub */}
                    <div className="container-20">
                        <a href={googleHref} className="button-4">
                            <svg className="social-logo" viewBox="0 0 24 24" aria-hidden="true">
                                <path
                                    fill="#EA4335"
                                    d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.8 14.8 1 12 1 7.4 1 3.5 3.6 1.6 7.4l3.7 2.9C6.2 7.1 8.9 5 12 5z"
                                ></path>
                                <path
                                    fill="#4285F4"
                                    d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
                                ></path>
                                <path
                                    fill="#FBBC05"
                                    d="M5.3 14.7c-.2-.7-.4-1.5-.4-2.7s.2-2 .4-2.7L1.6 6.4C.6 8.4 0 10.6 0 13s.6 4.6 1.6 6.6l3.7-2.9z"
                                ></path>
                                <path
                                    fill="#34A853"
                                    d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3.1 0-5.8-2.1-6.7-5.3L1.6 15C3.5 18.8 7.4 23 12 23z"
                                ></path>
                            </svg>
                            <div className="container-10">
                                <div className="text-7">Google</div>
                            </div>
                        </a>
                        <a href={githubHref} className="button-5">
                            <svg className="social-logo" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                                <path
                                    fillRule="evenodd"
                                    clipRule="evenodd"
                                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                                ></path>
                            </svg>
                            <div className="container-10">
                                <div className="text-7">GitHub</div>
                            </div>
                        </a>
                    </div>
                    {/* Đăng ký */}
                    <div className="horizontal-border">
                        <div className="paragraph">
                            <div className="text-8">
                                Chưa có tài khoản?
                            </div>
                            <a href={registerHref} className="link-ng-k-ngay">
                                Đăng ký ngay
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {/* Thanh phía trên */}
        <div className="top-navigation">
            <div className="container-21">
                <a href={homeHref} className="button-6">
                    <svg className="back-arrow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16" aria-hidden="true">
                        <line
                            x1="19"
                            y1="12"
                            x2="5"
                            y2="12"
                        ></line>
                        <polyline
                            points="12 19 5 12 12 5"
                        ></polyline>
                    </svg>
                    <div className="container-10">
                        <div className="text-4">Quay lại</div>
                    </div>
                </a>
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
