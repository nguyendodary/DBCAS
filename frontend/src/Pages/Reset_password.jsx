import { useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./Reset_password.css";

function Icon({ type, visible = false }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {type === "lock" ? (
        <>
          <rect x="3" y="11" width="18" height="11" rx="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </>
      ) : type === "back" ? (
        <>
          <path d="M19 12H5" />
          <path d="m12 19-7-7 7-7" />
        </>
      ) : type === "arrow" ? (
        <>
          <path d="M5 12h14" />
          <path d="m12 5 7 7-7 7" />
        </>
      ) : (
        <>
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12Z" />
          <circle cx="12" cy="12" r="3" />
          {visible && <path d="m2 2 20 20" />}
        </>
      )}
    </svg>
  );
}

export default function ReserPassword({
  loginHref = "/Dang_nhap",
  forgotHref = "/Forgot_password",

  // TODO BE:
  // Nhận { password, token }.
  // Trả về { success: true } khi cập nhật thành công.
  onResetPassword,
  resetToken = "",
}) {
  const location = useLocation();
  const pending = useRef(false);

  // Token được truyền từ trang xác minh OTP.
  const token = resetToken || location.state?.resetToken || "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info");

  const rules = [
    {
      label: "Tối thiểu 6 ký tự",
      valid: password.length >= 6,
    },
    {
      label: "Chữ hoa và chữ thường",
      valid: /[A-Z]/.test(password) && /[a-z]/.test(password),
    },
    {
      label: "Ít nhất 1 chữ số (0-9)",
      valid: /[0-9]/.test(password),
    },
    {
      label: "Ít nhất 1 ký tự đặc biệt (@, #, ...)",
      valid: /[^\p{L}\p{N}\s]/u.test(password),
    },
  ];

  const score = rules.filter((rule) => rule.valid).length;

  const isMatch =
    confirmPassword.length > 0 && password === confirmPassword;

  const canSubmit = score === 4 && isMatch && !success;

  const strengthColor = !password
    ? "#64748b"
    : score === 4
      ? "#10b981"
      : score === 3
        ? "#f59e0b"
        : "#ef4444";

  const strengthText = !password
    ? "● Chưa nhập"
    : score === 4
      ? "● Đủ 4 tiêu chí"
      : score === 3
        ? "● Mật khẩu trung bình"
        : "● Mật khẩu yếu";

  const matchColor = !confirmPassword
    ? "#64748b"
    : isMatch
      ? "#10b981"
      : "#ef4444";

  const matchText = !confirmPassword
    ? "○ Chưa khớp"
    : isMatch
      ? "✓ Mật khẩu trùng khớp"
      : "✕ Mật khẩu không khớp";

  function clearMessage() {
    setMessage("");
    setMessageType("info");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!canSubmit || pending.current) return;

    if (!onResetPassword) {
      setMessageType("info");
      setMessage(
        "Thông tin hợp lệ. Chưa kết nối backend nên mật khẩu chưa được cập nhật. Bạn có thể quay lại đăng nhập để tiếp tục thử giao diện."
      );
      return;
    }

    if (!token) {
      setMessageType("error");
      setMessage(
        "Thiếu thông tin xác minh. Vui lòng quay lại bước Quên mật khẩu."
      );
      return;
    }

    pending.current = true;
    setSubmitting(true);
    clearMessage();

    try {
      // TODO BE: backend kiểm tra token, thời hạn và cập nhật mật khẩu.
      const result = await onResetPassword({
        password,
        token,
      });

      if (result?.success !== true) {
        throw new Error(
          result?.message ||
            "Không thể cập nhật mật khẩu. Vui lòng thử lại."
        );
      }

      setPassword("");
      setConfirmPassword("");
      setShowPassword(false);
      setShowConfirm(false);
      setSuccess(true);
      setMessageType("success");
      setMessage(
        "Cập nhật mật khẩu thành công. Vui lòng quay lại đăng nhập."
      );
    } catch (error) {
      setMessageType("error");
      setMessage(
        error instanceof Error
          ? error.message
          : "Có lỗi xảy ra. Vui lòng thử lại."
      );
    } finally {
      pending.current = false;
      setSubmitting(false);
    }
  }

  return (
    <div className="dbcas-reset-password">
      <header className="reset-top-navigation">
        <div className="reset-brand">
          <span className="reset-brand-name">DBCAS</span>
          <span className="reset-brand-subtitle">
            SKILL ANALYTICS
          </span>
        </div>
      </header>

      <main className="reset-main">
        <div className="reset-gradient" aria-hidden="true" />

        <section
          className="reset-card"
          aria-labelledby="reset-title"
        >
          <div className="reset-heading">
            <h1 id="reset-title">Thiết lập mật khẩu mới</h1>

            <p>
              Vui lòng nhập mật khẩu mới bảo mật cho tài khoản học
              đường hoặc quản trị DBCAS của bạn.
            </p>
          </div>

          <form className="reset-form" onSubmit={handleSubmit}>
            <div className="reset-field">
              <label htmlFor="new-password">
                Mật khẩu mới
              </label>

              <div
                className="reset-input-wrapper"
                style={{
                  borderColor: password
                    ? strengthColor
                    : "#cbd5e1",
                }}
              >
                <span className="reset-input-icon">
                  <Icon type="lock" />
                </span>

                <input
                  id="new-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Nhập mật khẩu mới..."
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value);
                    clearMessage();
                  }}
                  aria-describedby="reset-rules"
                  disabled={submitting || success}
                  required
                />

                <button
                  type="button"
                  className="reset-eye-button"
                  onClick={() =>
                    setShowPassword((current) => !current)
                  }
                  aria-label={
                    showPassword
                      ? "Ẩn mật khẩu mới"
                      : "Hiện mật khẩu mới"
                  }
                  aria-pressed={showPassword}
                  disabled={submitting || success}
                >
                  <Icon type="eye" visible={showPassword} />
                </button>
              </div>
            </div>

            <div className="reset-strength-box">
              <div className="reset-strength-heading">
                <span>Độ mạnh mật khẩu:</span>

                <strong style={{ color: strengthColor }}>
                  {strengthText}
                </strong>
              </div>

              <div
                className="reset-strength-bars"
                aria-hidden="true"
              >
                {[0, 1, 2, 3].map((index) => (
                  <span
                    key={index}
                    style={{
                      backgroundColor:
                        index < score
                          ? strengthColor
                          : "#e2e8f0",
                    }}
                  />
                ))}
              </div>

              <div className="reset-rules" id="reset-rules">
                {rules.map((rule) => (
                  <div
                    key={rule.label}
                    style={{
                      color: rule.valid ? "#10b981" : "#64748b",
                    }}
                  >
                    <span aria-hidden="true">
                      {rule.valid ? "✓" : "○"}
                    </span>
                    <span>{rule.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="reset-field">
              <div className="reset-confirm-heading">
                <label htmlFor="confirm-new-password">
                  Xác nhận mật khẩu mới
                </label>

                <span
                  id="reset-match-status"
                  className="reset-match-status"
                  style={{ color: matchColor }}
                >
                  {matchText}
                </span>
              </div>

              <div
                className="reset-input-wrapper"
                style={{
                  borderColor: confirmPassword
                    ? matchColor
                    : "#cbd5e1",
                }}
              >
                <span className="reset-input-icon">
                  <Icon type="lock" />
                </span>

                <input
                  id="confirm-new-password"
                  type={showConfirm ? "text" : "password"}
                  placeholder="Nhập lại mật khẩu..."
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => {
                    setConfirmPassword(event.target.value);
                    clearMessage();
                  }}
                  aria-describedby="reset-match-status"
                  aria-invalid={
                    confirmPassword.length > 0 && !isMatch
                  }
                  disabled={submitting || success}
                  required
                />

                <button
                  type="button"
                  className="reset-eye-button"
                  onClick={() =>
                    setShowConfirm((current) => !current)
                  }
                  aria-label={
                    showConfirm
                      ? "Ẩn mật khẩu xác nhận"
                      : "Hiện mật khẩu xác nhận"
                  }
                  aria-pressed={showConfirm}
                  disabled={submitting || success}
                >
                  <Icon type="eye" visible={showConfirm} />
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="reset-submit-button"
              disabled={!canSubmit || submitting}
              aria-busy={submitting}
            >
              <span>
                {submitting
                  ? "ĐANG CẬP NHẬT..."
                  : "CẬP NHẬT MẬT KHẨU"}
              </span>
              <Icon type="arrow" />
            </button>

            {message && (
              <p
                className={`reset-message ${messageType}`}
                role="status"
              >
                {message}
              </p>
            )}

            <div className="reset-links">
              {!success && (
                <Link to={forgotHref} className="reset-back-link">
                  <Icon type="back" />
                  Quay lại
                </Link>
              )}

              <Link to={loginHref} className="reset-login-link">
                {success
                  ? "Đăng nhập ngay"
                  : "Quay lại đăng nhập"}
              </Link>
            </div>
          </form>
        </section>
      </main>

      <footer className="reset-footer">
        <p>
          © 2026 DBCAS Skill Analytics. All rights reserved. Nền tảng
          kiểm định &amp; đánh giá năng lực Cơ sở dữ liệu.
        </p>
      </footer>
    </div>
  );
}