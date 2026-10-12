import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

const SettingsContext = createContext(null);
const STORAGE_KEY = "dbcas.admin.preferences.v1";
export const DEFAULT_SETTINGS = { language: "vi", timezone: "Asia/Ho_Chi_Minh", dateFormat: "dmy", hourFormat: "24" };
export const LANGUAGES = ["vi", "en", "ko"];
export const TIMEZONES = [
  ["Asia/Ho_Chi_Minh", "UTC+07:00 (Hà Nội, Bangkok)"],
  ["Asia/Seoul", "UTC+09:00 (Seoul)"],
  ["Asia/Singapore", "UTC+08:00 (Singapore)"],
  ["Europe/London", "Europe/London"],
  ["America/New_York", "America/New_York"],
  ["UTC", "UTC+00:00"],
];
const LOCALES = { vi: "vi-VN", en: "en-US", ko: "ko-KR" };
// [Tiếng Việt, English, 한국어]. Add page-specific keys here as pages are integrated.
const MESSAGES = {
  home: ["Trang chủ", "Home", "홈"],
  competency: ["Đánh giá năng lực", "Competency assessment", "역량 평가"],
  skills: ["CLO & Kỹ năng", "CLO & Skills", "CLO 및 역량"],
  tests: ["Quản lý bài kiểm tra", "Test management", "시험 관리"],
  aiReview: ["Đánh giá bằng AI", "AI assessment", "AI 평가"],
  reports: ["Báo cáo", "Reports", "보고서"],
  settings: ["Cài đặt", "Settings", "설정"],
  newTest: ["Tạo bài kiểm tra", "Create test", "시험 만들기"],
  logout: ["Đăng xuất", "Log out", "로그아웃"],
  loggingOut: ["Đang đăng xuất...", "Logging out...", "로그아웃 중..."],
  login: ["Đăng nhập", "Log in", "로그인"],
  register: ["Đăng ký", "Sign up", "회원가입"],
  forgotPassword: ["Quên mật khẩu", "Forgot password", "비밀번호 찾기"],
  resetPassword: ["Đặt lại mật khẩu", "Reset password", "비밀번호 재설정"],
  analysis: ["Phân tích năng lực", "Competency analysis", "역량 분석"],
  review: ["Xem lại bài", "Review submission", "제출 답안 확인"],
  mcq: ["Trắc nghiệm", "Multiple choice", "객관식"],
  sql: ["Truy vấn SQL", "SQL queries", "SQL 쿼리"],
  essay: ["Tự luận", "Essay", "서술형"],
  help: ["Trợ giúp", "Help", "도움말"],
  notifications: ["Thông báo", "Notifications", "알림"],
  noNotifications: ["Chưa có thông báo mới.", "No new notifications.", "새 알림이 없습니다."],
  close: ["Đóng thông báo", "Close notification", "알림 닫기"],
  adminMenu: ["Menu quản trị", "Admin navigation", "관리자 메뉴"],
  save: ["Lưu thay đổi", "Save changes", "변경 사항 저장"],
  cancel: ["Hủy bỏ", "Cancel", "취소"],
  search: ["Tìm kiếm", "Search", "검색"],
  searchStudent: ["Tìm sinh viên hoặc MSSV...", "Search student name or ID...", "학생 이름 또는 학번 검색..."],
  allMajors: ["Tất cả ngành", "All majors", "모든 전공"],
  allYears: ["Tất cả năm học", "All academic years", "모든 학년도"],
  reset: ["Đặt lại", "Reset", "초기화"],
  student: ["Sinh viên", "Student", "학생"],
  studentId: ["MSSV", "Student ID", "학번"],
  score: ["Điểm", "Score", "점수"],
  status: ["Trạng thái", "Status", "상태"],
  actions: ["Thao tác", "Actions", "작업"],
  noData: ["Chưa có dữ liệu.", "No data available.", "데이터가 없습니다."],
  previous: ["Trước", "Previous", "이전"],
  next: ["Sau", "Next", "다음"],
  submit: ["Nộp bài", "Submit", "제출"],
  footer: ["DBCAS • Nền tảng đánh giá năng lực CSDL", "DBCAS • Database competency assessment platform", "DBCAS • 데이터베이스 역량 평가 플랫폼"],
  university: ["© 2026 Đại học Duy Tân", "© 2026 Duy Tan University", "© 2026 두이탄 대학교"],
  nameRequired: ["Vui lòng nhập họ và tên Admin.", "Please enter the admin name.", "관리자 이름을 입력하세요."],
  passwordsRequired: ["Vui lòng nhập đầy đủ ba ô mật khẩu.", "Please fill in all three password fields.", "비밀번호 입력란 세 개를 모두 입력하세요."],
  passwordMin: ["Mật khẩu mới cần ít nhất 6 ký tự.", "The new password must contain at least 6 characters.", "새 비밀번호는 최소 6자여야 합니다."],
  passwordMismatch: ["Xác nhận mật khẩu chưa khớp.", "The password confirmation does not match.", "비밀번호 확인이 일치하지 않습니다."],
  passwordSame: ["Mật khẩu mới phải khác mật khẩu hiện tại.", "The new password must differ from the current password.", "새 비밀번호는 현재 비밀번호와 달라야 합니다."],
  passwordBackend: ["Chưa kết nối chức năng đổi mật khẩu với backend.", "Password changes are not connected to the backend yet.", "비밀번호 변경 기능이 아직 서버에 연결되지 않았습니다."],
  unchanged: ["Chưa có thay đổi để lưu.", "There are no changes to save.", "저장할 변경 사항이 없습니다."],
  accountSaved: ["Đã lưu thay đổi tài khoản.", "Account changes saved.", "계정 변경 사항을 저장했습니다."],
  nameSaved: ["Đã cập nhật tên Admin.", "Admin name updated.", "관리자 이름을 변경했습니다."],
  nameSavedLocal: ["Đã lưu tên Admin trên trình duyệt.", "Admin name saved in this browser.", "관리자 이름을 이 브라우저에 저장했습니다."],
  nameSavedPartial: ["Tên đã được lưu. ", "The name was saved. ", "이름을 저장했습니다. "],
  accountSaveFailed: ["Không thể lưu thay đổi tài khoản.", "Could not save account changes.", "계정 변경 사항을 저장할 수 없습니다."],
  preferenceSaveFailed: ["Không thể lưu tùy chọn trên trình duyệt này.", "Could not save preferences in this browser.", "이 브라우저에 설정을 저장할 수 없습니다."],
  logoutFailed: ["Không thể đăng xuất.", "Could not log out.", "로그아웃할 수 없습니다."],
  settingsHelp: ["Chỉnh tài khoản, múi giờ, định dạng ngày giờ và ngôn ngữ.", "Configure your account, time zone, date and time formats, and language.", "계정, 시간대, 날짜 및 시간 형식과 언어를 설정하세요."],
};
export function translate(language, key, values = {}) {
  const message = MESSAGES[key];
  const text = message ? message[LANGUAGES.indexOf(language)] || message[0] : key;
  return text.replace(/\{(\w+)\}/g, (match, name) => values[name] == null ? match : String(values[name]));
}
export function sanitizeSettings(value) {
  return {
    language: LANGUAGES.includes(value?.language) ? value.language : DEFAULT_SETTINGS.language,
    timezone: TIMEZONES.some(([zone]) => zone === value?.timezone) ? value.timezone : DEFAULT_SETTINGS.timezone,
    dateFormat: ["dmy", "mdy", "ymd"].includes(value?.dateFormat) ? value.dateFormat : DEFAULT_SETTINGS.dateFormat,
    hourFormat: ["24", "12"].includes(value?.hourFormat) ? value.hourFormat : DEFAULT_SETTINGS.hourFormat,
  };
}
function readSettings() {
  try { return sanitizeSettings(JSON.parse(window.localStorage.getItem(STORAGE_KEY))); }
  catch { return { ...DEFAULT_SETTINGS }; }
}
// Timestamps must be Date objects, epoch milliseconds, or ISO strings with Z/UTC offset.
// Preformatted display strings are deliberately not parsed.
function parseTimestamp(value) {
  if (value instanceof Date) return Number.isFinite(value.getTime()) ? value : null;
  if (typeof value === "number") { const date = new Date(value); return Number.isFinite(date.getTime()) ? date : null; }
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/i.test(value)) return null;
  const date = new Date(value);
  return Number.isFinite(date.getTime()) ? date : null;
}
export function formatTimestamp(value, settings, options = {}) {
  const date = parseTimestamp(value);
  if (!date) return "—";
  const showDate = options.date !== false, showTime = options.time !== false;
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: settings.timezone, day: "2-digit", month: "2-digit", year: "numeric",
  }).formatToParts(date);
  const get = key => parts.find(part => part.type === key)?.value;
  const d = get("day"), m = get("month"), y = get("year");
  const formattedDate = settings.dateFormat === "ymd" ? `${y}-${m}-${d}` : settings.dateFormat === "mdy" ? `${m}/${d}/${y}` : `${d}/${m}/${y}`;
  const formattedTime = new Intl.DateTimeFormat(LOCALES[settings.language], {
    timeZone: settings.timezone, hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: settings.hourFormat === "12",
  }).format(date);
  return [showDate && formattedDate, showTime && formattedTime].filter(Boolean).join(" • ");
}
export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(readSettings);
  const current = useRef(settings);
  const updateSettings = useCallback(patch => {
    const next = sanitizeSettings({ ...current.current, ...patch });
    // Persistence must succeed before showing a saved preference.
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    current.current = next;
    setSettings(next);
  }, []);
  useEffect(() => {
    document.documentElement.lang = settings.language;
  }, [settings.language]);
  useEffect(() => {
    function sync(event) {
      if (event.key === STORAGE_KEY || event.key === null) {
        const next = readSettings(); current.current = next; setSettings(next);
      }
    }
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  const value = useMemo(() => ({
    settings, ...settings, locale: LOCALES[settings.language], updateSettings,
    setLanguage: language => updateSettings({ language }),
    setTimezone: timezone => updateSettings({ timezone }),
    t: (key, values) => translate(settings.language, key, values),
    formatDateTime: (date, options) => formatTimestamp(date, settings, options),
    formatDate: date => formatTimestamp(date, settings, { time: false }),
    formatTime: date => formatTimestamp(date, settings, { date: false }),
    formatNumber: (number, options) => new Intl.NumberFormat(LOCALES[settings.language], options).format(number),
  }), [settings, updateSettings]);
  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}
export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) throw new Error("useSettings must be used inside SettingsProvider.");
  return context;
}
