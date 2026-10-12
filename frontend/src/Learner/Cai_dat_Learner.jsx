import { useRef, useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  readLearnerPreferences,
  saveLearnerPreferences,
} from "../Context/LearnerPreferences";

import {
  NotificationMenu,
  LearnerAccountMenu,
} from "../Context/SettingsContext";

import { Icon, MAJORS } from "./Xem_danh_gia_Learner";

import "./Home_Learner.css";
import "./Cai_dat_Learner.css";

import video from "./video1.mp4";
import poster from "./nen1.jpg";

function readSaved(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}

function PasswordField({
  label,
  value,
  onChange,
  autoComplete,
}) {
  const [visible, setVisible] = useState(false);

  return (
    <label className="cl-field">
      {label}

      <span className="cl-password">
        <input
          type={visible ? "text" : "password"}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          placeholder={`${label}...`}
          required
        />

        <button
          type="button"
          aria-label={visible ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
          aria-pressed={visible}
          onClick={() => setVisible((old) => !old)}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            aria-hidden="true"
          >
            <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
            <circle cx="12" cy="12" r="3" />
            {visible && <path d="m3 3 18 18" />}
          </svg>
        </button>
      </span>
    </label>
  );
}

export default function CaiDatLearner({
  user,
  onSaveProfile,
  onChangePassword,
  onSavePreferences,
  onLogout,
}) {
  const location = useLocation();
  const navigate = useNavigate();

  const account = user ?? location.state?.user;

  const accountId = String(
    account?.studentId ?? account?.mssv ?? "20216000100"
  );

  const profileKey = `dbcas-learner-profile:${accountId}`;
  const optionsKey = `dbcas-learner-options:${accountId}`;

  const [profile, setProfile] = useState(() =>
    readSaved(profileKey, {
      name: account?.name ?? "Nguyễn Hoàng Long",
      studentId: accountId,
      major: account?.major ?? MAJORS[0],
      email: account?.email ?? "long.nh20216049@sis.hust.edu.vn",
      phone: account?.phone ?? "",
      avatar: account?.avatar ?? "",
    })
  );

  const [form, setForm] = useState(profile);

  // Đọc cùng nguồn cài đặt mà TN, SQL và TL sử dụng.
  const [options, setOptions] = useState(readLearnerPreferences);

  const [passwords, setPasswords] = useState({
    current: "",
    next: "",
    confirm: "",
  });

  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const fileRef = useRef(null);
  const profileRef = useRef(null);

  const initials = String(profile.name ?? "")
    .trim()
    .split(/\s+/)
    .slice(-2)
    .map((word) => word[0] ?? "")
    .join("")
    .toUpperCase();

  const learner = {
    ...profile,
    initials,
  };

  function begin() {
    setError("");
    setNotice("");
  }

  function update(event) {
    const { name, value } = event.target;

    let nextValue = value;

    if (name === "studentId") {
      nextValue = value.replace(/[^0-9]/g, "").slice(0, 11);
    }

    if (name === "phone") {
      nextValue = value.replace(/[^0-9]/g, "").slice(0, 10);
    }

    setForm((old) => ({
      ...old,
      [name]: nextValue,
    }));
  }

  function updatePassword(name, value) {
    setPasswords((old) => ({
      ...old,
      [name]: value,
    }));
  }

  function selectAvatar(event) {
    begin();

    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    if (
      !["image/jpeg", "image/png", "image/webp"].includes(file.type)
    ) {
      setError("Chọn ảnh JPG, PNG hoặc WebP.");
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      setError("Ảnh không được lớn hơn 2 MB.");
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      setForm((old) => ({
        ...old,
        avatar: String(reader.result),
      }));
    };

    reader.onerror = () => {
      setError("Không đọc được ảnh. Vui lòng chọn lại.");
    };

    reader.readAsDataURL(file);
  }

  async function saveProfile(event) {
    event.preventDefault();
    begin();

    const cleaned = {
      ...form,
      name: String(form.name ?? "").trim(),
      email: String(form.email ?? "").trim(),
      studentId: String(form.studentId ?? ""),
      phone: String(form.phone ?? ""),
    };

    if (cleaned.name.length < 2) {
      setError("Vui lòng nhập họ tên từ 2 ký tự.");
      return;
    }

    if (!/^[0-9]{11}$/.test(cleaned.studentId)) {
      setError("MSSV phải gồm đúng 11 chữ số.");
      return;
    }

    if (!/^\S+@\S+\.\S+$/.test(cleaned.email)) {
      setError("Email không hợp lệ.");
      return;
    }

    if (!/^[0-9]{10}$/.test(cleaned.phone)) {
      setError("Số điện thoại phải gồm đúng 10 chữ số.");
      return;
    }

    setBusy("profile");

    try {
      if (onSaveProfile) {
        await onSaveProfile(cleaned);
      }

      localStorage.setItem(profileKey, JSON.stringify(cleaned));

      localStorage.setItem(
        "dbcas.learner.active-account.v1",
        accountId
      );

      setProfile(cleaned);
      setForm(cleaned);

      window.dispatchEvent(
        new CustomEvent("dbcas:learner-profile-changed")
      );

      setNotice(
        onSaveProfile
          ? "Đã cập nhật thông tin cá nhân."
          : "Đã lưu thông tin trên trình duyệt này."
      );
    } catch {
      setError("Chưa lưu được thông tin. Vui lòng thử lại.");
    } finally {
      setBusy("");
    }
  }

  async function changePassword(event) {
    event.preventDefault();
    begin();

    if (!passwords.current) {
      setError("Vui lòng nhập mật khẩu hiện tại.");
      return;
    }

    if (
      !/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(
        passwords.next
      )
    ) {
      setError(
        "Mật khẩu mới cần ít nhất 8 ký tự, gồm chữ hoa, chữ thường và số."
      );
      return;
    }

    if (passwords.next !== passwords.confirm) {
      setError("Mật khẩu xác nhận chưa khớp.");
      return;
    }

    if (passwords.current === passwords.next) {
      setError("Mật khẩu mới phải khác mật khẩu hiện tại.");
      return;
    }

    if (!onChangePassword) {
      setError(
        "Chưa kết nối chức năng đổi mật khẩu với máy chủ."
      );
      return;
    }

    setBusy("password");

    try {
      await onChangePassword({
        currentPassword: passwords.current,
        newPassword: passwords.next,
      });

      setPasswords({
        current: "",
        next: "",
        confirm: "",
      });

      setNotice("Đã cập nhật mật khẩu.");
    } catch {
      setError(
        "Không đổi được mật khẩu. Kiểm tra mật khẩu hiện tại và thử lại."
      );
    } finally {
      setBusy("");
    }
  }

  function changeFontSize(fontSize) {
    begin();

    try {
      saveLearnerPreferences({ fontSize });

      setOptions((old) => ({
        ...old,
        fontSize,
      }));

      document.documentElement.style.setProperty(
        "--learner-font-scale",
        String(fontSize / 16)
      );

      document.documentElement.style.setProperty(
        "--dbcas-learner-content-size",
        `${fontSize}px`
      );
    } catch {
      setError("Không lưu được cỡ chữ. Vui lòng thử lại.");
    }
  }

  function toggleSound() {
    begin();

    const sound = !options.sound;

    try {
      // Lưu ngay để các trang thi nhận trạng thái bật/tắt.
      saveLearnerPreferences({ sound });

      setOptions((old) => ({
        ...old,
        sound,
      }));
    } catch {
      setError(
        "Không lưu được tùy chọn âm thanh. Vui lòng thử lại."
      );
    }
  }

  async function toggleNotifications() {
    begin();

    if (options.notifications) {
      try {
        saveLearnerPreferences({
          notifications: false,
        });

        setOptions((old) => ({
          ...old,
          notifications: false,
        }));
      } catch {
        setError("Không lưu được tùy chọn thông báo.");
      }

      return;
    }

    if (!("Notification" in window)) {
      setError("Trình duyệt này chưa hỗ trợ thông báo.");
      return;
    }

    try {
      const permission = await Notification.requestPermission();

      if (permission !== "granted") {
        setError(
          "Chưa được cấp quyền thông báo. Bạn có thể bật trong cài đặt trình duyệt."
        );
        return;
      }

      saveLearnerPreferences({
        notifications: true,
      });

      setOptions((old) => ({
        ...old,
        notifications: true,
      }));
    } catch {
      setError("Không bật được thông báo trình duyệt.");
    }
  }

  async function saveOptions(event) {
    event.preventDefault();
    begin();
    setBusy("options");

    try {
      if (onSavePreferences) {
        await onSavePreferences(options);
      }

      localStorage.setItem(optionsKey, JSON.stringify(options));

      // Đồng bộ toàn bộ tùy chọn với các trang Learner.
      saveLearnerPreferences(options);

      setNotice("Đã lưu tùy chọn hệ thống.");
    } catch {
      setError("Chưa lưu được tùy chọn. Vui lòng thử lại.");
    } finally {
      setBusy("");
    }
  }

  async function logout() {
    if (!window.confirm("Bạn muốn đăng xuất tài khoản?")) {
      return;
    }

    begin();
    setBusy("logout");

    try {
      if (onLogout) {
        await onLogout();
      }

      window.dispatchEvent(
        new CustomEvent("dbcas:logout", {
          detail: { role: "learner" },
        })
      );

      navigate("/Dang_nhap", {
        replace: true,
      });
    } catch {
      setError("Chưa đăng xuất được. Vui lòng thử lại.");
    } finally {
      setBusy("");
    }
  }

  function focusProfile() {
    profileRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });

    profileRef.current
      ?.querySelector('input[name="name"]')
      ?.focus({
        preventScroll: true,
      });
  }

  return (
    <div className="dbcas-learner-home learner-settings-page">
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

          <nav
            className="main-nav"
            aria-label="Menu người học"
          >
            <Link className="nav-link" to="/Home_Learner">
              <Icon name="home" />
              <span>Trang chủ</span>
            </Link>

            <Link
              className="nav-link"
              to="/Bai_kiem_tra_Learner"
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

            <Link
              className="nav-link active"
              to="/Cai_dat_Learner"
              aria-current="page"
            >
              <Icon name="settings" />
              <span>Cài đặt</span>
            </Link>
          </nav>

          <div className="toolbar-actions">
            <NotificationMenu
              role="learner"
              className="notification-button"
            />

            <LearnerAccountMenu
              profile={learner}
              onLogout={onLogout}
            />
          </div>
        </div>
      </header>

      <section className="cl-hero">
        <video
          autoPlay
          muted
          loop
          playsInline
          poster={poster}
          aria-hidden="true"
        >
          <source src={video} type="video/mp4" />
        </video>

        <div className="container cl-hero-inner">
          <span className="cl-eyebrow">
            HỆ THỐNG ĐÁNH GIÁ NĂNG LỰC CSDL
          </span>

          <h1>Cài đặt Tài khoản</h1>

          <p>
            Quản lý thông tin cá nhân, bảo mật và tùy chọn
            trải nghiệm học tập
          </p>

          <div className="cl-account">
            <div className="cl-photo">
              {profile.avatar ? (
                <img
                  src={profile.avatar}
                  alt="Ảnh đại diện"
                />
              ) : (
                <span>{initials}</span>
              )}
            </div>

            <div className="cl-account-info">
              <strong>{profile.name}</strong>

              <span>
                MSSV: {profile.studentId}
                {" · "}
                Ngành: {profile.major}
              </span>
            </div>

            <span className="cl-account-status">
              Trạng thái học vụ
              <strong>● Tài khoản Learner</strong>
            </span>

            <button
              type="button"
              onClick={focusProfile}
            >
              Chỉnh sửa hồ sơ
            </button>
          </div>
        </div>
      </section>

      <main className="cl-main">
        {(notice || error) && (
          <div
            className={`cl-message ${error ? "error" : ""}`}
            role={error ? "alert" : "status"}
          >
            {error || notice}

            <button
              type="button"
              aria-label="Đóng thông báo"
              onClick={begin}
            >
              ×
            </button>
          </div>
        )}

        <form
          className="cl-card"
          ref={profileRef}
          onSubmit={saveProfile}
        >
          <div className="cl-card-heading">
            <span className="cl-section-icon">
              <Icon name="users" />
            </span>

            <div>
              <h2>Thông tin cá nhân</h2>
              <p>
                Cập nhật họ tên, ảnh đại diện và các chi tiết
                liên hệ của bạn
              </p>
            </div>

            <span className="cl-chip">Hồ sơ</span>
          </div>

          <div className="cl-avatar-editor">
            <div className="cl-photo">
              {form.avatar ? (
                <img
                  src={form.avatar}
                  alt="Ảnh đại diện đang chọn"
                />
              ) : (
                <span>{initials}</span>
              )}
            </div>

            <div>
              <strong>Ảnh đại diện hồ sơ sinh viên</strong>
              <p>Ảnh JPG, PNG hoặc WebP, tối đa 2 MB.</p>

              <div className="cl-avatar-actions">
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                >
                  Đổi ảnh đại diện
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setForm((old) => ({
                      ...old,
                      avatar: "",
                    }))
                  }
                >
                  Gỡ ảnh
                </button>
              </div>
            </div>

            <input
              hidden
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={selectAvatar}
            />
          </div>

          <div className="cl-fields">
            <label className="cl-field">
              Họ và tên sinh viên <em>*</em>
              <input
                name="name"
                value={form.name}
                onChange={update}
                maxLength={100}
                autoComplete="name"
                required
              />
            </label>

            <label className="cl-field">
              Mã số sinh viên (MSSV) <em>*</em>
              <input
                type="text"
                name="studentId"
                value={form.studentId ?? ""}
                onChange={update}
                inputMode="numeric"
                pattern="[0-9]{11}"
                minLength={11}
                maxLength={11}
                placeholder="Nhập 11 chữ số"
                required
              />
            </label>

            <label className="cl-field">
              Ngành học
              <select
                name="major"
                value={form.major}
                onChange={update}
              >
                {[...new Set([...MAJORS, form.major])]
                  .filter(Boolean)
                  .map((major) => (
                    <option key={major} value={major}>
                      {major}
                    </option>
                  ))}
              </select>
            </label>

            <label className="cl-field">
              Email <em>*</em>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={update}
                autoComplete="email"
                required
              />
            </label>

            <label className="cl-field cl-full">
              Số điện thoại <em>*</em>
              <input
                type="text"
                name="phone"
                value={form.phone ?? ""}
                onChange={update}
                inputMode="numeric"
                pattern="[0-9]{10}"
                minLength={10}
                maxLength={10}
                placeholder="Nhập 10 chữ số"
                autoComplete="tel"
                required
              />
              <small>
                Số điện thoại phải gồm đúng 10 chữ số.
              </small>
            </label>
          </div>

          <div className="cl-card-actions">
            <button
              type="submit"
              className="cl-primary"
              disabled={Boolean(busy)}
            >
              {busy === "profile"
                ? "Đang lưu..."
                : "✓ Lưu thông tin cá nhân"}
            </button>
          </div>
        </form>

        <form
          className="cl-card"
          onSubmit={changePassword}
        >
          <div className="cl-card-heading">
            <span className="cl-section-icon purple">
              <Icon name="file" />
            </span>

            <div>
              <h2>Đổi mật khẩu</h2>
              <p>
                Đổi mật khẩu định kỳ để nâng cao tính bảo mật
                khi truy cập
              </p>
            </div>

            <span className="cl-chip purple">Bảo mật</span>
          </div>

          <div className="cl-fields">
            <div className="cl-full">
              <PasswordField
                label="Mật khẩu hiện tại"
                value={passwords.current}
                autoComplete="current-password"
                onChange={(event) =>
                  updatePassword(
                    "current",
                    event.target.value
                  )
                }
              />
            </div>

            <PasswordField
              label="Mật khẩu mới"
              value={passwords.next}
              autoComplete="new-password"
              onChange={(event) =>
                updatePassword("next", event.target.value)
              }
            />

            <PasswordField
              label="Xác nhận mật khẩu mới"
              value={passwords.confirm}
              autoComplete="new-password"
              onChange={(event) =>
                updatePassword(
                  "confirm",
                  event.target.value
                )
              }
            />
          </div>

          <p className="cl-security-tip">
            <Icon name="check" />

            <span>
              <strong>Quy chuẩn bảo mật:</strong>{" "}
              Mật khẩu mới cần có{" "}
              <strong>tối thiểu 8 ký tự</strong>, bao gồm
              chữ hoa, chữ thường và chữ số.
            </span>
          </p>

          <div className="cl-card-actions">
            <button
              type="submit"
              className="cl-primary blue"
              disabled={Boolean(busy)}
            >
              {busy === "password"
                ? "Đang cập nhật..."
                : "Cập nhật mật khẩu"}
            </button>
          </div>
        </form>

        <form
          className="cl-card"
          onSubmit={saveOptions}
        >
          <div className="cl-card-heading">
            <span className="cl-section-icon teal">
              <Icon name="settings" />
            </span>

            <div>
              <h2>Tùy chọn hệ thống</h2>
              <p>
                Cài đặt hiển thị giao diện, thông báo và
                trải nghiệm cá nhân
              </p>
            </div>

            <span className="cl-chip teal">
              Trải nghiệm
            </span>
          </div>

          <fieldset className="cl-font-options">
            <legend>Cỡ chữ toàn bộ giao diện Learner</legend>

            <div>
              {[
                { size: 14, name: "Nhỏ" },
                { size: 16, name: "Tiêu chuẩn" },
                { size: 18, name: "Lớn" },
              ].map((item) => (
                <label
                  key={item.size}
                  className={
                    options.fontSize === item.size
                      ? "selected"
                      : ""
                  }
                >
                  <input
                    type="radio"
                    name="fontSize"
                    checked={
                      options.fontSize === item.size
                    }
                    onChange={() =>
                      changeFontSize(item.size)
                    }
                  />

                  <span style={{ fontSize: item.size }}>
                    Tᵀ
                  </span>

                  <strong>{item.name}</strong>

                  <small>
                    {item.size}px
                    {item.size === 16
                      ? " (Mặc định)"
                      : ""}
                  </small>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="cl-toggle-row">
            <Icon name="bell" />

            <div>
              <strong>Thông báo trên trình duyệt</strong>
              <p>
                Nhận thông báo trực tiếp khi có bài kiểm tra
                mới hoặc phản hồi từ hệ thống
              </p>
            </div>

            <button
              type="button"
              role="switch"
              aria-label="Thông báo trên trình duyệt"
              aria-checked={options.notifications}
              className={`cl-switch ${
                options.notifications ? "on" : ""
              }`}
              onClick={toggleNotifications}
            >
              <span />
            </button>
          </div>

          <div className="cl-toggle-row">
            <Icon name="warning" />

            <div>
              <strong>Âm thanh chuông báo</strong>
              <p>
                Bật để nghe chuông khi bài thi còn 5 phút.
                Tắt để không phát âm thanh.
              </p>
            </div>

            <button
              type="button"
              role="switch"
              aria-label="Âm thanh chuông báo"
              aria-checked={options.sound}
              className={`cl-switch ${
                options.sound ? "on" : ""
              }`}
              onClick={toggleSound}
            >
              <span />
            </button>
          </div>

          <label className="cl-field cl-language">
            Ngôn ngữ hiển thị
            <select
              value={options.language}
              onChange={(event) => {
                const language = event.target.value;

                setOptions((old) => ({
                  ...old,
                  language,
                }));
              }}
            >
              <option value="vi">
                Tiếng Việt (Mặc định)
              </option>
            </select>
          </label>

          <div className="cl-card-actions split">
            <button
              type="button"
              className="cl-logout"
              disabled={Boolean(busy)}
              onClick={logout}
            >
              ↪ Đăng xuất tài khoản
            </button>

            <button
              type="submit"
              className="cl-primary"
              disabled={Boolean(busy)}
            >
              {busy === "options"
                ? "Đang lưu..."
                : "Lưu tùy chọn"}
            </button>
          </div>
        </form>
      </main>

      <footer className="footer">
        <div className="container footer-inner">
          <p>
            <strong>DBCAS</strong>
            <span>•</span>
            Nền tảng tự động Đánh giá Năng lực CSDL
          </p>

          <nav aria-label="Liên kết hỗ trợ">
            <Link to="/Quy_che">
              Quy chế khảo thí
            </Link>

            <Link to="/Tai_lieu#chuan-hoa">
              Chuẩn hóa 3NF
            </Link>

            <Link to="/Tai_lieu#sql">
              Tài liệu SQL
            </Link>

            <Link to="/Ho_tro">
              Hỗ trợ
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}