import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useEffect, useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home_Admin.css";
import "./Cai_dat_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";
const NAV_ITEMS = [["home", "Trang chủ", "/Home_Admin"], ["users", "Đánh giá năng lực", "/Danh_gia_nang_luc_Admin"], ["cap", "CLO & Kỹ năng", "/CLO_Ky_nang_Admin"], ["document", "Quản lý bài kiểm tra", "/Quan_ly_bai_kiem_tra_Admin"], ["robot", "Đánh giá bằng AI", "/Danh_gia_AI_Admin"], ["chart", "Báo cáo", "/Bao_cao_Admin"], ["settings", "Cài đặt", "/Cai_dat_Admin"]];
const STORAGE_KEY = "dbcas.admin.preferences.v1";
const PROFILE_KEY = "dbcas.admin.displayName.v1";
const DEFAULT_PROFILE = {
  name: "Admin DBCAS",
  email: "admin.dbcas@gmail.com",
  phone: ""
};
const DEFAULTS = {
  timezone: "Asia/Ho_Chi_Minh",
  dateFormat: "dmy",
  hourFormat: "24",
  language: "vi"
};
const TIMEZONES = [["Asia/Ho_Chi_Minh", "UTC+07:00 (Hà Nội, Bangkok)"], ["Asia/Seoul", "UTC+09:00 (Seoul)"], ["Asia/Singapore", "UTC+08:00 (Singapore)"], ["Europe/London", "Europe/London"], ["America/New_York", "America/New_York"], ["UTC", "UTC+00:00"]];
const TEXT = {
  vi: {
    settings: "Cài đặt",
    title: "Trung tâm Cài đặt DBCAS",
    intro: "Quản lý tài khoản quản trị viên, số điện thoại và tùy chọn hiển thị.",
    account: "Quản lý tài khoản Admin",
    accountHint: "Thông tin quản trị viên và bảo mật tài khoản.",
    name: "Họ và tên Admin",
    email: "Email quản trị",
    phone: "Số điện thoại",
    phonePlaceholder: "Nhập số điện thoại",
    phoneHint: "10 chữ số, bắt đầu bằng 0.",
    password: "Đổi mật khẩu tài khoản",
    current: "Mật khẩu hiện tại",
    next: "Mật khẩu mới (ít nhất 6 ký tự)",
    confirm: "Xác nhận mật khẩu",
    cancel: "Hủy bỏ",
    save: "Lưu thay đổi",
    saving: "Đang lưu...",
    time: "Cấu hình Múi giờ & Ngày tháng",
    timeHint: "Chọn cách hiển thị ngày giờ trên giao diện.",
    clock: "Thời gian hiện tại",
    timezone: "Múi giờ hệ thống",
    date: "Định dạng ngày",
    hour: "Định dạng giờ",
    h24: "24 giờ (HH:mm:ss)",
    h12: "12 giờ (hh:mm:ss AM/PM)",
    language: "Ngôn ngữ hệ thống",
    languageHint: "Chọn ngôn ngữ hiển thị cho trang cài đặt.",
    selected: "Đang chọn",
    local: "Tùy chọn lưu trên trình duyệt",
    show: "Hiện mật khẩu",
    hide: "Ẩn mật khẩu",
    nameRequired: "Vui lòng nhập họ và tên Admin.",
    invalidPhone: "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.",
    passwordRequired: "Vui lòng nhập đầy đủ ba ô mật khẩu.",
    passwordShort: "Mật khẩu mới cần ít nhất 6 ký tự.",
    passwordMismatch: "Xác nhận mật khẩu chưa khớp.",
    passwordSame: "Mật khẩu mới phải khác mật khẩu hiện tại.",
    passwordUnavailable: "Chưa kết nối chức năng đổi mật khẩu với backend.",
    noChanges: "Chưa có thay đổi để lưu.",
    saved: "Đã lưu thay đổi tài khoản.",
    savedLocal: "Đã lưu tên và số điện thoại trên trình duyệt.",
    savedMixed: "Đã đổi mật khẩu. Tên và số điện thoại đã lưu trên trình duyệt.",
    profileSaved: "Thông tin tài khoản đã được lưu.",
    saveFailed: "Không thể lưu thay đổi tài khoản.",
    preferencesFailed: "Không thể lưu tùy chọn trên trình duyệt này.",
    logout: "Đăng xuất",
    loggingOut: "Đang đăng xuất...",
    logoutFailed: "Không thể đăng xuất.",
    help: "Trợ giúp",
    helpText: "Cập nhật thông tin tài khoản và chọn tùy chọn hiển thị.",
    notifications: "Thông báo",
    noNotifications: "Chưa có thông báo mới.",
    close: "Đóng thông báo"
  },
  en: {
    settings: "Settings",
    title: "DBCAS Settings Center",
    intro: "Manage your administrator account, phone number and display preferences.",
    account: "Admin account",
    accountHint: "Administrator information and account security.",
    name: "Admin full name",
    email: "Admin email",
    phone: "Phone number",
    phonePlaceholder: "Enter phone number",
    phoneHint: "10 digits, starting with 0.",
    password: "Change password",
    current: "Current password",
    next: "New password (at least 6 characters)",
    confirm: "Confirm password",
    cancel: "Cancel",
    save: "Save changes",
    saving: "Saving...",
    time: "Time zone & Date settings",
    timeHint: "Choose how dates and times appear in the interface.",
    clock: "Current time",
    timezone: "System time zone",
    date: "Date format",
    hour: "Time format",
    h24: "24 hours (HH:mm:ss)",
    h12: "12 hours (hh:mm:ss AM/PM)",
    language: "System language",
    languageHint: "Choose the display language for this settings page.",
    selected: "Selected",
    local: "Preferences saved in this browser",
    show: "Show password",
    hide: "Hide password",
    nameRequired: "Please enter the administrator's full name.",
    invalidPhone: "The phone number must contain 10 digits and start with 0.",
    passwordRequired: "Please complete all three password fields.",
    passwordShort: "The new password must contain at least 6 characters.",
    passwordMismatch: "The password confirmation does not match.",
    passwordSame: "The new password must differ from the current password.",
    passwordUnavailable: "Password changes are not connected to the backend.",
    noChanges: "There are no changes to save.",
    saved: "Account changes saved.",
    savedLocal: "Name and phone number saved in this browser.",
    savedMixed: "Password changed. Name and phone number saved in this browser.",
    profileSaved: "Account information has been saved.",
    saveFailed: "Unable to save account changes.",
    preferencesFailed: "Unable to save preferences in this browser.",
    logout: "Log out",
    loggingOut: "Logging out...",
    logoutFailed: "Unable to log out.",
    help: "Help",
    helpText: "Update your account information and display preferences.",
    notifications: "Notifications",
    noNotifications: "No new notifications.",
    close: "Close notification"
  },
  ko: {
    settings: "설정",
    title: "DBCAS 설정 센터",
    intro: "관리자 계정, 전화번호 및 표시 설정을 관리합니다.",
    account: "관리자 계정 관리",
    accountHint: "관리자 정보 및 계정 보안.",
    name: "관리자 이름",
    email: "관리자 이메일",
    phone: "전화번호",
    phonePlaceholder: "전화번호 입력",
    phoneHint: "0으로 시작하는 10자리 숫자.",
    password: "비밀번호 변경",
    current: "현재 비밀번호",
    next: "새 비밀번호 (최소 6자)",
    confirm: "비밀번호 확인",
    cancel: "취소",
    save: "변경 사항 저장",
    saving: "저장 중...",
    time: "시간대 및 날짜 설정",
    timeHint: "날짜와 시간의 표시 형식을 선택하세요.",
    clock: "현재 시간",
    timezone: "시스템 시간대",
    date: "날짜 형식",
    hour: "시간 형식",
    h24: "24시간 (HH:mm:ss)",
    h12: "12시간 (hh:mm:ss AM/PM)",
    language: "시스템 언어",
    languageHint: "설정 페이지의 표시 언어를 선택하세요.",
    selected: "선택됨",
    local: "설정은 이 브라우저에 저장됩니다",
    show: "비밀번호 표시",
    hide: "비밀번호 숨기기",
    nameRequired: "관리자 이름을 입력하세요.",
    invalidPhone: "전화번호는 0으로 시작하는 10자리 숫자여야 합니다.",
    passwordRequired: "비밀번호 입력란 세 개를 모두 입력하세요.",
    passwordShort: "새 비밀번호는 최소 6자여야 합니다.",
    passwordMismatch: "비밀번호 확인이 일치하지 않습니다.",
    passwordSame: "새 비밀번호는 현재 비밀번호와 달라야 합니다.",
    passwordUnavailable: "비밀번호 변경 기능이 백엔드에 연결되지 않았습니다.",
    noChanges: "저장할 변경 사항이 없습니다.",
    saved: "계정 변경 사항이 저장되었습니다.",
    savedLocal: "이름과 전화번호가 이 브라우저에 저장되었습니다.",
    savedMixed: "비밀번호가 변경되었습니다. 이름과 전화번호는 브라우저에 저장되었습니다.",
    profileSaved: "계정 정보가 저장되었습니다.",
    saveFailed: "계정 변경 사항을 저장할 수 없습니다.",
    preferencesFailed: "이 브라우저에 설정을 저장할 수 없습니다.",
    logout: "로그아웃",
    loggingOut: "로그아웃 중...",
    logoutFailed: "로그아웃할 수 없습니다.",
    help: "도움말",
    helpText: "계정 정보 및 표시 설정을 업데이트하세요.",
    notifications: "알림",
    noNotifications: "새 알림이 없습니다.",
    close: "알림 닫기"
  }
};
function Icon({
  name
}) {
  const paths = {
    clock: "M12 7v5l3 2M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18",
    language: "M3 5h12M9 3v2M5 5c0 6 4 9 9 11M13 5c0 6-4 9-10 11M14 21l4-10 4 10M16 17h4",
    lock: "M6 10h12v11H6zM8 10V7a4 4 0 0 1 8 0v3",
    mail: "M3 5h18v14H3zM3 5l9 7 9-7",
    phone: "M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2Z",
    eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
    check: "m5 12 4 4L19 6",
    plus: "M12 5v14M5 12h14",
    home: "m3 10 9-7 9 7v10H3zM9 20v-7h6v7",
    users: "M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5.65",
    cap: "m2 9 10-5 10 5-10 5zM6 11v6c4 3 8 3 12 0v-6M22 9v7",
    document: "M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6",
    robot: "M4 7h16v13H4zM12 3v4M2 11v5M22 11v5M8 12h1M15 12h1M9 16h6",
    chart: "M4 3v17h17M8 16v-5M13 16V7M18 16V4",
    settings: "m9 3-1 3-3 1v4l-2 1 2 1v4l3 1 1 3h6l1-3 3-1v-4l2-1-2-1V7l-3-1-1-3z",
    logout: "M10 4H4v16h6M9 12h12M17 8l4 4-4 4",
    chevron: "m8 5 7 7-7 7",
    help: "M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 2-2.5 3.5M12 16h.01",
    bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"
  };
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name] || paths.chart} />
      {adminRender(name === "users" && <circle cx="9" cy="7" r="3" />)}
      {adminRender(name === "help" && <circle cx="12" cy="12" r="9" />)}
      {adminRender(name === "settings" && <circle cx="12" cy="12" r="3" />)}
    </svg>;
}
function loadPreferences() {
  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null");
    return {
      timezone: TIMEZONES.some(([value]) => value === stored?.timezone) ? stored.timezone : DEFAULTS.timezone,
      dateFormat: ["dmy", "mdy", "ymd"].includes(stored?.dateFormat) ? stored.dateFormat : DEFAULTS.dateFormat,
      hourFormat: ["24", "12"].includes(stored?.hourFormat) ? stored.hourFormat : DEFAULTS.hourFormat,
      language: ["vi", "en", "ko"].includes(stored?.language) ? stored.language : DEFAULTS.language
    };
  } catch {
    return {
      ...DEFAULTS
    };
  }
}
function loadAccount(profile, useBackend) {
  const fallback = {
    name: profile.name || "Admin DBCAS",
    phone: String(profile.phone ?? "")
  };
  if (useBackend) return fallback;
  try {
    const key = `dbcas.admin.account.v1:${profile.email || "admin"}`;
    const stored = JSON.parse(window.localStorage.getItem(key) || "null");
    return {
      name: typeof stored?.name === "string" ? stored.name : window.localStorage.getItem(PROFILE_KEY) || fallback.name,
      phone: typeof stored?.phone === "string" ? stored.phone : fallback.phone
    };
  } catch {
    return fallback;
  }
}
function formatDate(now, preferences) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: preferences.timezone,
    day: "2-digit",
    month: "2-digit",
    year: "numeric"
  }).formatToParts(now);
  const get = type => parts.find(part => part.type === type)?.value;
  const day = get("day");
  const month = get("month");
  const year = get("year");
  if (preferences.dateFormat === "ymd") {
    return `${year}-${month}-${day}`;
  }
  if (preferences.dateFormat === "mdy") {
    return `${month}/${day}/${year}`;
  }
  return `${day}/${month}/${year}`;
}
function PasswordInput({
  label,
  value,
  onChange,
  autoComplete,
  t
}) {
  const [shown, setShown] = useState(false);
  return <label className="settings-password">
      <span className="settings-sr-only">{adminRender(label)}</span>

      <input type={shown ? "text" : "password"} value={value} onChange={onChange} placeholder={label} autoComplete={autoComplete} />

      <button type="button" onClick={() => setShown(previous => !previous)} aria-label={shown ? t.hide : t.show} aria-pressed={shown}>
        <Icon name="eye" />
        {adminRender(!shown && <span className="settings-eye-slash" />)}
      </button>
    </label>;
}
export default function CaiDatAdmin({
  profile = DEFAULT_PROFILE,
  onSaveProfile,
  onChangePassword,
  onLogout
}) {
  useAdminLanguage();

  const navigate = useNavigate();
  const [preferences, setPreferences] = useState(loadPreferences);
  const [savedAccount, setSavedAccount] = useState(() => loadAccount(profile, Boolean(onSaveProfile)));
  const [name, setName] = useState(savedAccount.name);
  const [phone, setPhone] = useState(savedAccount.phone);
  const [passwords, setPasswords] = useState({
    current: "",
    next: "",
    confirm: ""
  });
  const [now, setNow] = useState(() => new Date());
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const t = TEXT[preferences.language];
  const accountKey = `dbcas.admin.account.v1:${profile.email || "admin"}`;
  useEffect(() => {
    const interval = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(interval);
  }, []);
  useEffect(() => {
    const account = loadAccount(profile, Boolean(onSaveProfile));
    setSavedAccount(account);
    setName(account.name);
    setPhone(account.phone);
    setPasswords({
      current: "",
      next: "",
      confirm: ""
    });
  }, [profile.name, profile.phone, profile.email, onSaveProfile]);
  const locale = preferences.language === "vi" ? "vi-VN" : preferences.language === "ko" ? "ko-KR" : "en-US";
  const clock = new Intl.DateTimeFormat(locale, {
    timeZone: preferences.timezone,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: preferences.hourFormat === "12"
  }).format(now);
  function updatePreference(key, value) {
    const updated = {
      ...preferences,
      [key]: value
    };
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      setPreferences(updated);
      window.dispatchEvent(new CustomEvent("dbcas:preferences-changed", {
        detail: updated
      }));
    } catch {
      setNotice(t.preferencesFailed);
    }
  }
  function changePassword(key, value) {
    setPasswords(previous => ({
      ...previous,
      [key]: value
    }));
  }
  function cancelChanges() {
    setName(savedAccount.name);
    setPhone(savedAccount.phone);
    setPasswords({
      current: "",
      next: "",
      confirm: ""
    });
    setNotice(adminText(""));
  }
  async function saveAccount(event) {
    event.preventDefault();
    if (saving) return;
    const nextName = name.trim();
    const nextPhone = phone.trim();
    if (!nextName) {
      setNotice(t.nameRequired);
      return;
    }

    // Cho phép để trống nếu chưa cập nhật số điện thoại.
    if (nextPhone && !/^0\d{9}$/.test(nextPhone)) {
      setNotice(t.invalidPhone);
      return;
    }
    const profileChanged = nextName !== savedAccount.name || nextPhone !== savedAccount.phone;
    const passwordChanged = Object.values(passwords).some(Boolean);
    if (passwordChanged) {
      if (!passwords.current || !passwords.next || !passwords.confirm) {
        setNotice(t.passwordRequired);
        return;
      }
      if (passwords.next.length < 6) {
        setNotice(t.passwordShort);
        return;
      }
      if (passwords.next !== passwords.confirm) {
        setNotice(t.passwordMismatch);
        return;
      }
      if (passwords.next === passwords.current) {
        setNotice(t.passwordSame);
        return;
      }
      if (!onChangePassword) {
        setNotice(t.passwordUnavailable);
        return;
      }
    }
    if (!profileChanged && !passwordChanged) {
      setNotice(t.noChanges);
      return;
    }
    setSaving(true);
    setNotice(adminText(""));
    let profileSaved = false;
    try {
      if (profileChanged) {
        const updated = {
          name: nextName,
          phone: nextPhone
        };
        if (onSaveProfile) {
          await onSaveProfile(updated);
        } else {
          // Lưu cùng một đối tượng để tên và số điện thoại
          // được cập nhật trong một lần ghi.
          window.localStorage.setItem(accountKey, JSON.stringify(updated));
        }
        setSavedAccount(updated);
        window.dispatchEvent(new CustomEvent("dbcas:account-changed"));
        setName(updated.name);
        setPhone(updated.phone);
        profileSaved = true;
      }
      if (passwordChanged) {
        await onChangePassword({
          currentPassword: passwords.current,
          newPassword: passwords.next
        });
        setPasswords({
          current: "",
          next: "",
          confirm: ""
        });
      }
      setNotice(profileChanged && !onSaveProfile ? passwordChanged ? t.savedMixed : t.savedLocal : t.saved);
    } catch (error) {
      setNotice(adminText(`${profileSaved ? `${t.profileSaved} ` : ""}${error instanceof Error ? error.message : t.saveFailed}`));
    } finally {
      setSaving(false);
    }
  }
  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      if (onLogout) await onLogout();
      navigate("/Dang_nhap");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : t.logoutFailed);
    } finally {
      setLoggingOut(false);
    }
  }
  return <div className="dbcas-admin-home dbcas-settings-page" lang={preferences.language} style={{
    backgroundImage: `
          linear-gradient(
            rgba(7,11,20,.8),
            rgba(7,11,20,.8)
          ),
          url(${background})
        `
  }}>
      <aside className="sidebar">
        <div className="sidebar-content">
          <div className="sidebar-brand">
            <img src={logo} alt="Logo DBCAS" draggable="false" />
          </div>

          <Link className="btn-new" to="/TN_Admin">
            <Icon name="plus" />
            <span>{adminText("Tạo bài kiểm tra")}</span>
          </Link>

          <nav className="sidebar-nav" aria-label={adminText("Menu quản trị")}>
            {adminRender(NAV_ITEMS.map(([icon, label, path]) => {
            const active = path === "/Cai_dat_Admin";
            return <Link key={path} className={`nav-link${active ? " active" : ""}`} to={path} aria-current={active ? "page" : undefined}>
                  <Icon name={icon} />
                  <span>{adminRender(label)}</span>
                  {adminRender(active && <span className="nav-dot" />)}
                </Link>;
          }))}
          </nav>
        </div>

        <div className="sidebar-bottom">
          <button className="btn-logout" type="button" disabled={loggingOut || saving} onClick={handleLogout}>
            <Icon name="logout" />
            <span>
              {adminRender(loggingOut ? t.loggingOut : t.logout)}
            </span>
          </button>
        </div>
      </aside>

      <header className="topbar admin-unified-topbar">
        <div className="breadcrumb">
          <span>DBCAS Admin</span>
          <Icon name="chevron" />
          <strong>{adminRender(t.settings)}</strong>
        </div>

        <div className="topbar-actions">
          <button className="icon-button" type="button" aria-label={t.help} onClick={() => setNotice(t.helpText)}>
            <Icon name="help" />
          </button>

          <NotificationMenu role="admin" className="icon-button" />

          <AdminAccountMenu profile={{
          ...profile,
          ...savedAccount
        }} onLogout={handleLogout} />
        </div>
      </header>

      <main className="main settings-main">
        <section className="settings-title admin-unified-banner">
          <div>
            <h1>
              <Icon name="settings" />
              {adminRender(t.title)}
            </h1>
            <p>{adminRender(t.intro)}</p>
          </div>

          <span className="settings-status">
            <i />
            {adminRender(t.local)}
          </span>
        </section>

        <div className="settings-stack">
          <section className="card settings-card" aria-labelledby="settings-account-title">
            <div className="settings-card-heading">
              <span className="settings-section-icon">
                <Icon name="lock" />
              </span>

              <div>
                <h2 id="settings-account-title">{adminRender(t.account)}</h2>
                <p>{adminRender(t.accountHint)}</p>
              </div>
            </div>

            <form onSubmit={saveAccount}>
              <fieldset disabled={saving} className="settings-fieldset">
                <div className="settings-profile-grid">
                  <label className="settings-field">
                    <span>{adminRender(t.name)}</span>

                    <div className="settings-input-wrap">
                      <Icon name="users" />
                      <input value={name} onChange={event => setName(event.target.value)} autoComplete="name" maxLength={100} required />
                    </div>
                  </label>

                  <label className="settings-field">
                    <span>{adminRender(t.email)}</span>

                    <div className="settings-input-wrap settings-readonly">
                      <Icon name="mail" />
                      <input type="email" value={profile.email || ""} readOnly autoComplete="username" />
                    </div>
                  </label>

                  <label className="settings-field">
                    <span>{adminRender(t.phone)}</span>

                    <div className="settings-input-wrap">
                      <Icon name="phone" />
                      <input type="tel" inputMode="numeric" autoComplete="tel" value={phone} onChange={event => setPhone(event.target.value.replace(/\D/g, "").slice(0, 10))} maxLength={10} placeholder={t.phonePlaceholder} aria-describedby="settings-phone-hint" />
                    </div>

                    <small className="settings-field-hint" id="settings-phone-hint">
                      {adminRender(t.phoneHint)}
                    </small>
                  </label>
                </div>

                <p className="settings-password-label">
                  {adminRender(t.password)}
                </p>

                <div className="settings-password-grid">
                  <PasswordInput t={t} label={t.current} autoComplete="current-password" value={passwords.current} onChange={event => changePassword("current", event.target.value)} />

                  <PasswordInput t={t} label={t.next} autoComplete="new-password" value={passwords.next} onChange={event => changePassword("next", event.target.value)} />

                  <PasswordInput t={t} label={t.confirm} autoComplete="new-password" value={passwords.confirm} onChange={event => changePassword("confirm", event.target.value)} />
                </div>

                <div className="settings-account-actions">
                  <button type="button" className="settings-cancel" onClick={cancelChanges}>
                    {adminRender(t.cancel)}
                  </button>

                  <button type="submit" className="settings-save">
                    <Icon name="check" />
                    {adminRender(saving ? t.saving : t.save)}
                  </button>
                </div>
              </fieldset>
            </form>
          </section>

          <section className="card settings-card" aria-labelledby="settings-time-title">
            <div className="settings-card-heading">
              <span className="settings-section-icon blue">
                <Icon name="clock" />
              </span>

              <div>
                <h2 id="settings-time-title">{adminRender(t.time)}</h2>
                <p>{adminRender(t.timeHint)}</p>
              </div>

              <span className="settings-clock">
                <i />
                {adminRender(t.clock)}: {adminRender(formatDate(now, preferences))} • {adminRender(clock)}
              </span>
            </div>

            <div className="settings-time-grid">
              <label className="settings-field">
                <span>{adminRender(t.timezone)}</span>

                <select value={preferences.timezone} onChange={event => updatePreference("timezone", event.target.value)}>
                  {adminRender(TIMEZONES.map(([value, label]) => <option key={value} value={value}>
                      {adminRender(label)}
                    </option>))}
                </select>
              </label>

              <label className="settings-field">
                <span>{adminRender(t.date)}</span>

                <select value={preferences.dateFormat} onChange={event => updatePreference("dateFormat", event.target.value)}>
                  <option value="dmy">DD/MM/YYYY</option>
                  <option value="mdy">MM/DD/YYYY</option>
                  <option value="ymd">YYYY-MM-DD</option>
                </select>
              </label>

              <label className="settings-field">
                <span>{adminRender(t.hour)}</span>

                <select value={preferences.hourFormat} onChange={event => updatePreference("hourFormat", event.target.value)}>
                  <option value="24">{adminRender(t.h24)}</option>
                  <option value="12">{adminRender(t.h12)}</option>
                </select>
              </label>
            </div>
          </section>

          <section className="card settings-card" aria-labelledby="settings-language-title">
            <div className="settings-card-heading">
              <span className="settings-section-icon">
                <Icon name="language" />
              </span>

              <div>
                <h2 id="settings-language-title">{adminRender(t.language)}</h2>
                <p>{adminRender(t.languageHint)}</p>
              </div>

              <span className="settings-language-badge">
                {adminRender(t.selected)}:{adminRender(" ")}
                {adminRender({
                vi: "Tiếng Việt",
                en: "English",
                ko: "한국어"
              }[preferences.language])}
              </span>
            </div>

            <div className="settings-language-grid" role="radiogroup" aria-label={t.language}>
              {adminRender([["vi", "Tiếng Việt", "Việt Nam"], ["en", "English (US)", "United States"], ["ko", "한국어", "대한민국"]].map(([value, label, hint]) => <label key={value} className={`settings-language-option${preferences.language === value ? " selected" : ""}`}>
                  <input type="radio" name="settings-language" value={value} checked={preferences.language === value} onChange={() => updatePreference("language", value)} />

                  <span>
                    <strong>{adminRender(label)}</strong>
                    <small>{adminRender(hint)}</small>
                  </span>

                  {adminRender(preferences.language === value && <span className="settings-selected-label">
                      {adminRender(t.selected)}
                    </span>)}
                </label>))}
            </div>
          </section>
        </div>
      </main>

      <footer className="footer">
        <span>{adminText("DBCAS • Nền tảng đánh giá năng lực CSDL")}</span>
        <span>© 2026 Duy Tan University</span>
      </footer>

      {adminRender(notice && <div className="admin-notice settings-notice" role="status">
          <span>{adminRender(notice)}</span>
          <button type="button" aria-label={t.close} onClick={() => setNotice(adminText(""))}>{adminText(" × ")}</button>
        </div>)}
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