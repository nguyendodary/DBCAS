import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Forgot_password.css";

function Icon({ type }) {
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
      {type === "email" ? (
        <>
          <rect x="3" y="5" width="18" height="14" rx="2" />
          <path d="m3 6 9 7 9-7" />
        </>
      ) : type === "clock" ? (
        <>
          <circle cx="12" cy="12" r="10" />
          <path d="M12 6v6l4 2" />
        </>
      ) : type === "back" ? (
        <>
          <path d="M19 12H5" />
          <path d="m12 19-7-7 7-7" />
        </>
      ) : (
        <>
          <path d="M5 12h14" />
          <path d="m12 5 7 7-7 7" />
        </>
      )}
    </svg>
  );
}

export default function ForgotPassword({
  loginHref = "/Dang_nhap",
  resetHref = "/Reset_password",

  // Chỉ dùng để thử giao diện khi chưa có BE.
  demoMode = true,

  // TODO BE:
  // onSendOtp({ email }) trả { success: true }.
  // Có thể trả thêm expiresIn, resendAfter (đơn vị giây).
  onSendOtp,

  // onVerifyOtp({ email, otp }) trả:
  // { success: true, resetToken: "token-do-backend-cap" }.
  onVerifyOtp,
}) {
  const navigate = useNavigate();
  const inputsRef = useRef([]);
  const pending = useRef(false);

  const [email, setEmail] = useState("");
  const [digits, setDigits] = useState(Array(6).fill(""));
  const [sent, setSent] = useState(false);
  const [expiresAt, setExpiresAt] = useState(0);
  const [resendAt, setResendAt] = useState(0);
  const [now, setNow] = useState(Date.now());
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info");

  useEffect(() => {
    if (!sent) return;

    const timer = setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => clearInterval(timer);
  }, [sent]);

  const validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
    email.trim()
  );

  const otp = digits.join("");
  const timeLeft = Math.max(
    0,
    Math.ceil((expiresAt - now) / 1000)
  );
  const resendLeft = Math.max(
    0,
    Math.ceil((resendAt - now) / 1000)
  );

  const canVerify =
    sent && validEmail && otp.length === 6 && timeLeft > 0;

  const timerText = !sent
    ? "Chưa gửi mã"
    : timeLeft === 0
      ? "Đã hết hạn"
      : `${String(Math.floor(timeLeft / 60)).padStart(2, "0")}:${String(
          timeLeft % 60
        ).padStart(2, "0")}`;

  function showMessage(text, type = "info") {
    setMessage(text);
    setMessageType(type);
  }

  function handleEmailChange(event) {
    setEmail(event.target.value);
    setDigits(Array(6).fill(""));
    setSent(false);
    setExpiresAt(0);
    setResendAt(0);
    setMessage("");
  }

  async function sendCode() {
    if (pending.current || (sent && resendLeft > 0)) return;

    if (!validEmail) {
      showMessage("Vui lòng nhập email đúng định dạng.", "error");
      return;
    }

    if (!onSendOtp && !demoMode) {
      showMessage(
        "Chưa kết nối backend nên chưa thể gửi OTP.",
        "info"
      );
      return;
    }

    pending.current = true;
    setBusy("send");
    setMessage("");

    try {
      let expiry = 600;
      let cooldown = 60;

      if (onSendOtp) {
        const result = await onSendOtp({ email: email.trim() });

        if (result?.success !== true) {
          throw new Error(
            result?.message || "Không thể gửi mã. Vui lòng thử lại."
          );
        }

        if (
          Number.isFinite(result.expiresIn) &&
          result.expiresIn > 0
        ) {
          expiry = result.expiresIn;
        }

        if (
          Number.isFinite(result.resendAfter) &&
          result.resendAfter >= 0
        ) {
          cooldown = result.resendAfter;
        }

        showMessage(
          "Yêu cầu gửi mã đã được tiếp nhận. Vui lòng kiểm tra email."
        );
      } else {
        showMessage(
          "Đang thử giao diện: không gửi email thật. Nhập 6 số bất kỳ để thử bước tiếp theo."
        );
      }

      const timestamp = Date.now();

      setNow(timestamp);
      setExpiresAt(timestamp + expiry * 1000);
      setResendAt(timestamp + cooldown * 1000);
      setSent(true);
      setDigits(Array(6).fill(""));
      inputsRef.current[0]?.focus();
    } catch (error) {
      showMessage(
        error instanceof Error
          ? error.message
          : "Có lỗi xảy ra khi gửi mã.",
        "error"
      );
    } finally {
      pending.current = false;
      setBusy("");
    }
  }

  function handleDigitChange(index, value) {
    const digit = value.replace(/\D/g, "").slice(-1);

    setDigits((current) =>
      current.map((item, position) =>
        position === index ? digit : item
      )
    );
    setMessage("");

    if (digit && index < 5) {
      inputsRef.current[index + 1]?.focus();
    }
  }

  function handleKeyDown(event, index) {
    if (event.key === "Backspace" && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }

    if (event.key === "ArrowLeft" && index > 0) {
      event.preventDefault();
      inputsRef.current[index - 1]?.focus();
    }

    if (event.key === "ArrowRight" && index < 5) {
      event.preventDefault();
      inputsRef.current[index + 1]?.focus();
    }
  }

  function handlePaste(event, index) {
    event.preventDefault();

    const pasted = event.clipboardData
      .getData("text")
      .replace(/\D/g, "")
      .slice(0, 6 - index);

    if (!pasted) return;

    setDigits((current) => {
      const next = [...current];

      [...pasted].forEach((digit, offset) => {
        next[index + offset] = digit;
      });

      return next;
    });

    setMessage("");
    inputsRef.current[
      Math.min(index + pasted.length, 5)
    ]?.focus();
  }

  async function verifyCode(event) {
    event.preventDefault();

    if (!canVerify || pending.current) return;

    if (Date.now() >= expiresAt) {
      setNow(Date.now());
      showMessage("Mã đã hết hạn. Vui lòng gửi lại mã.", "error");
      return;
    }

    if (!onVerifyOtp && (!demoMode || onSendOtp)) {
      showMessage(
        "Chưa kết nối chức năng xác minh OTP của backend.",
        "info"
      );
      return;
    }

    pending.current = true;
    setBusy("verify");
    setMessage("");

    try {
      if (onVerifyOtp) {
        const result = await onVerifyOtp({
          email: email.trim(),
          otp,
        });

        if (
          result?.success !== true ||
          typeof result.resetToken !== "string" ||
          !result.resetToken
        ) {
          throw new Error(
            result?.message ||
              "Không thể xác minh OTP hoặc thiếu token đặt lại mật khẩu."
          );
        }

        navigate(resetHref, {
          state: { resetToken: result.resetToken },
        });
      } else {
        // CHỈ DEMO: không xác minh OTP, không tạo token thật.
        navigate(resetHref, { state: { demoMode: true } });
      }
    } catch (error) {
      showMessage(
        error instanceof Error
          ? error.message
          : "Không thể xác minh mã.",
        "error"
      );
    } finally {
      pending.current = false;
      setBusy("");
    }
  }

  return (
    <div className="qun-mt-khu">
      <header className="top-navigation">
        <div className="logo-thng-hiu-bn-phi">
          <span className="text-13">DBCAS</span>
          <span className="text-14">SKILL ANALYTICS</span>
        </div>
      </header>

      <main className="khung-chun-x">
        <div className="gradient" aria-hidden="true" />

        <div className="main-content-area-gi">
          <div className="CT-PHI-khung-nhp">
            <div className="background-border">
              <div className="header-form">
                <div className="div-wrapper">
                  <h1 className="text">Quên mật khẩu?</h1>

                  <button
                    type="button"
                    className="button-nt-gi-li"
                    onClick={sendCode}
                    disabled={
                      Boolean(busy) || (sent && resendLeft > 0)
                    }
                  >
                    <span className="text-2">
                      {busy === "send"
                        ? "Đang gửi..."
                        : sent
                          ? "Gửi lại"
                          : "Gửi mã"}
                    </span>
                  </button>
                </div>

                <p className="nh-p-email-t-i-kho-n">
                  Nhập email tài khoản học đường hoặc email quản trị.
                  Mã xác nhận 6 số được dùng để thiết lập mật khẩu mới.
                </p>
              </div>

              <form
                className="form-bc-trc-quan"
                onSubmit={verifyCode}
              >
                <div className="trng-email">
                  <label
                    htmlFor="forgot-email"
                    className="text-wrapper"
                  >
                    Email tài khoản
                  </label>

                  <div className="input-group-wrapper">
                    <div className="input">
                      <input
                        id="forgot-email"
                        className="container-2"
                        type="email"
                        placeholder="nguyen_vana@dtu.edu.vn"
                        autoComplete="email"
                        value={email}
                        onChange={handleEmailChange}
                        disabled={Boolean(busy)}
                        required
                      />

                      <span className="SVG-wrapper">
                        <Icon type="email" />
                      </span>
                    </div>
                  </div>
                </div>

                <div className="khi-nhp-m-xc-nhn-OTP">
                  <div className="div-2">
                    <p className="text-3">
                      Mã xác nhận 6 số (OTP qua Email)
                    </p>

                    <div className="div-3">
                      <Icon type="clock" />
                      <span className="text-4">
                        {sent ? `Hiệu lực: ${timerText}` : timerText}
                      </span>
                    </div>
                  </div>

                  <div
                    className="otp-inputs"
                    role="group"
                    aria-label="Mã OTP gồm 6 số"
                  >
                    {digits.map((digit, index) => (
                      <input
                        key={index}
                        ref={(element) => {
                          inputsRef.current[index] = element;
                        }}
                        className="otp-input-box"
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        placeholder="•"
                        aria-label={`Số OTP thứ ${index + 1}`}
                        autoComplete={
                          index === 0 ? "one-time-code" : "off"
                        }
                        value={digit}
                        onChange={(event) =>
                          handleDigitChange(index, event.target.value)
                        }
                        onKeyDown={(event) =>
                          handleKeyDown(event, index)
                        }
                        onPaste={(event) =>
                          handlePaste(event, index)
                        }
                        disabled={Boolean(busy)}
                      />
                    ))}
                  </div>

                  <button
                    type="button"
                    className="button-resend-text"
                    onClick={sendCode}
                    disabled={
                      Boolean(busy) || (sent && resendLeft > 0)
                    }
                  >
                    Chưa nhận được mã?{" "}
                    <span>
                      {!sent
                        ? "Gửi mã"
                        : resendLeft > 0
                          ? `Gửi lại mã (${resendLeft}s)`
                          : "Gửi lại mã"}
                    </span>
                  </button>
                </div>

                <button
                  type="submit"
                  className="nt-hnh-ng-xc-nhn-tip"
                  disabled={!canVerify || Boolean(busy)}
                >
                  <span className="text-9">
                    {busy === "verify"
                      ? "ĐANG XÁC NHẬN..."
                      : "XÁC NHẬN MÃ & ĐẶT LẠI MẬT KHẨU"}
                  </span>
                  <Icon type="arrow" />
                </button>

                {message && (
                  <p
                    className={`form-message ${messageType}`}
                    role="status"
                  >
                    {message}
                  </p>
                )}

                <div className="iu-hng-ph-v-ng-nhp">
                  <Link
                    to={loginHref}
                    className="back-login-link"
                  >
                    <Icon type="back" />
                    Quay lại đăng nhập
                  </Link>
                </div>
              </form>
            </div>
          </div>
        </div>
      </main>

      <footer className="footer-bn-quyn-chun">
        <p className="text-15">
          © 2026 DBCAS Skill Analytics. All rights reserved. Nền tảng
          kiểm định &amp; đánh giá năng lực Cơ sở dữ liệu.
        </p>
      </footer>
    </div>
  );
}