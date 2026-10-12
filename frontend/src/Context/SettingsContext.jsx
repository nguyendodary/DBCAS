import { useLearnerPreferences } from "./LearnerPreferences";
export { readLearnerPreferences, saveLearnerPreferences, useLearnerPreferences, useFiveMinuteAlarm } from "./LearnerPreferences";
import "./Interface.css";
import { Link, useLocation, useNavigate } from "react-router-dom";
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
    const syncPreferences = () => { const next = readSettings(); current.current = next; setSettings(next); };
    window.addEventListener("dbcas:preferences-changed", syncPreferences);
    window.addEventListener("storage", sync);
    return () => { window.removeEventListener("storage", sync); window.removeEventListener("dbcas:preferences-changed", syncPreferences); };
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

const ADMIN_TRANSLATIONS = {
  "Trang chủ": [
    "Home",
    "홈"
  ],
  "Đánh giá năng lực": [
    "Competency assessment",
    "역량 평가"
  ],
  "CLO & Kỹ năng": [
    "CLO & Skills",
    "CLO 및 역량"
  ],
  "Quản lý bài kiểm tra": [
    "Test management",
    "시험 관리"
  ],
  "Đánh giá bằng AI": [
    "AI assessment",
    "AI 평가"
  ],
  "Báo cáo": [
    "Reports",
    "보고서"
  ],
  "Cài đặt": [
    "Settings",
    "설정"
  ],
  "Kỹ thuật Phần mềm": [
    "Software Engineering",
    "소프트웨어 공학"
  ],
  "Khoa học Máy tính": [
    "Computer Science",
    "컴퓨터 과학"
  ],
  "Hệ thống Thông tin Quản lý": [
    "Management Information Systems",
    "경영 정보 시스템"
  ],
  "An ninh Mạng": [
    "Cybersecurity",
    "사이버 보안"
  ],
  "Công nghệ Phần mềm": [
    "Software Technology",
    "소프트웨어 기술"
  ],
  "Truy vấn SQL": [
    "SQL queries",
    "SQL 쿼리"
  ],
  "Thiết kế & Ràng buộc": [
    "Design & Constraints",
    "설계 및 제약 조건"
  ],
  "KT CSDL Cơ Bản": [
    "Basic Database Test",
    "기초 데이터베이스 시험"
  ],
  "KT CSDL Nâng Cao": [
    "Advanced Database Test",
    "고급 데이터베이스 시험"
  ],
  "Thiết kế và Chuẩn hóa CSDL": [
    "Database Design and Normalization",
    "데이터베이스 설계 및 정규화"
  ],
  "Xuất sắc": [
    "Excellent",
    "최우수"
  ],
  "Giỏi": [
    "Very good",
    "우수"
  ],
  "Khá": [
    "Good",
    "양호"
  ],
  "Trung bình": [
    "Average",
    "보통"
  ],
  "Cần bồi dưỡng": [
    "Needs improvement",
    "보충 학습 필요"
  ],
  "Không có dữ liệu để xuất.": [
    "No data to export.",
    "내보낼 데이터가 없습니다."
  ],
  "Sinh viên": [
    "Student",
    "학생"
  ],
  "Ngành": [
    "Major",
    "전공"
  ],
  "Năm học": [
    "Academic year",
    "학년도"
  ],
  "Điểm": [
    "Score",
    "점수"
  ],
  "Xếp loại": [
    "Classification",
    "등급"
  ],
  "Không thể đăng xuất.": [
    "Could not log out.",
    "로그아웃할 수 없습니다."
  ],
  "Tạo bài kiểm tra": [
    "Create test",
    "시험 만들기"
  ],
  "Menu quản trị": [
    "Admin navigation",
    "관리자 메뉴"
  ],
  "Đang đăng xuất...": [
    "Logging out...",
    "로그아웃 중..."
  ],
  "Đăng xuất": [
    "Log out",
    "로그아웃"
  ],
  "Trợ giúp": [
    "Help",
    "도움말"
  ],
  "Tìm tên hoặc MSSV, chọn ngành và năm học để lọc cả hai biểu đồ.": [
    "Search by name or student ID, major and academic year to filter both charts.",
    "이름 또는 학번, 전공과 학년도로 두 차트를 필터링하세요."
  ],
  "Thông báo": [
    "Notifications",
    "알림"
  ],
  "Chưa có thông báo mới.": [
    "No new notifications.",
    "새 알림이 없습니다."
  ],
  "Tìm kiếm và bộ lọc": [
    "Search and filters",
    "검색 및 필터"
  ],
  "Tìm tên sinh viên hoặc MSSV...": [
    "Search student name or ID...",
    "학생 이름 또는 학번 검색..."
  ],
  "Tìm sinh viên hoặc MSSV": [
    "Search student or ID",
    "학생 또는 학번 검색"
  ],
  "Bộ lọc phạm vi:": [
    "Scope filters:",
    "범위 필터:"
  ],
  "Lọc ngành": [
    "Filter by major",
    "전공 필터"
  ],
  "Tất cả ngành": [
    "All majors",
    "모든 전공"
  ],
  "Lọc năm học": [
    "Filter by academic year",
    "학년도 필터"
  ],
  "Tất cả năm học": [
    "All academic years",
    "모든 학년도"
  ],
  "Năm học:": [
    "Academic year:",
    "학년도:"
  ],
  "Đặt lại": [
    "Reset",
    "초기화"
  ],
  "Báo cáo thống kê tổng quan": [
    "Statistical overview",
    "통계 개요"
  ],
  "Phân bố điểm và mức xếp loại năng lực của sinh viên.": [
    "Student score and competency distributions.",
    "학생 점수 및 역량 등급 분포."
  ],
  "Xuất CSV": [
    "Export CSV",
    "CSV 내보내기"
  ],
  "Xuất PDF": [
    "Export PDF",
    "PDF 내보내기"
  ],
  "Biểu đồ phân bố điểm số trực quan (Score Distribution)": [
    "Score distribution chart",
    "점수 분포 차트"
  ],
  "Mật độ phân bố phổ điểm của": [
    "Score distribution for",
    "점수 분포 대상:"
  ],
  "sinh viên theo thang điểm 10": [
    "students on a 10-point scale",
    "학생, 10점 만점"
  ],
  "Chưa có dữ liệu.": [
    "No data available.",
    "데이터가 없습니다."
  ],
  "Phân bố mức xếp loại năng lực": [
    "Competency classification distribution",
    "역량 등급 분포"
  ],
  "sinh viên": [
    "students",
    "학생"
  ],
  "Tỷ lệ hoàn thành chuẩn năng lực": [
    "Competency attainment rate",
    "역량 기준 달성률"
  ],
  "% · Vượt ngưỡng chuẩn (≥ 5.0)": [
    "% · Above threshold (≥ 5.0)",
    "% · 기준 이상 (≥ 5.0)"
  ],
  "Bảng xếp hạng sinh viên theo năng lực": [
    "Student competency ranking",
    "학생 역량 순위"
  ],
  "Xếp theo điểm năng lực giảm dần · Trắc nghiệm 40%, truy vấn SQL 30%, tự luận 30%": [
    "Descending competency score · MCQ 40%, SQL 30%, essay 30%",
    "역량 점수 내림차순 · 객관식 40%, SQL 30%, 서술형 30%"
  ],
  "Lọc theo tên hoặc MSSV...": [
    "Filter by name or student ID...",
    "이름 또는 학번 필터..."
  ],
  "Tìm sinh viên trong bảng": [
    "Search students in table",
    "표에서 학생 검색"
  ],
  "Lọc mức xếp loại": [
    "Filter classification",
    "등급 필터"
  ],
  "Mọi mức xếp loại": [
    "All classifications",
    "모든 등급"
  ],
  "Làm mới": [
    "Refresh",
    "새로고침"
  ],
  "Hạng": [
    "Rank",
    "순위"
  ],
  "Sinh viên / MSSV": [
    "Student / ID",
    "학생 / 학번"
  ],
  "Số bài": [
    "Tests",
    "시험 수"
  ],
  "Năng lực từng kỹ năng": [
    "Competency by skill",
    "역량별 점수"
  ],
  "Không có sinh viên phù hợp.": [
    "No matching students.",
    "일치하는 학생이 없습니다."
  ],
  "Mạnh:": [
    "Strengths:",
    "강점:"
  ],
  "Cần cải thiện:": [
    "Needs improvement:",
    "개선 필요:"
  ],
  "Đạt chuẩn": [
    "Meets standard",
    "기준 충족"
  ],
  "Chưa đủ": [
    "Insufficient",
    "미충족"
  ],
  "Hiển thị": [
    "Showing",
    "표시"
  ],
  "Phân trang": [
    "Pagination",
    "페이지 탐색"
  ],
  "‹ Trước": [
    "‹ Previous",
    "‹ 이전"
  ],
  "DBCAS • Nền tảng đánh giá năng lực CSDL": [
    "DBCAS • Database competency assessment platform",
    "DBCAS • 데이터베이스 역량 평가 플랫폼"
  ],
  "Đóng thông báo": [
    "Close notification",
    "알림 닫기"
  ],
  "Thông tin tài khoản Admin": [
    "Admin account information",
    "관리자 계정 정보"
  ],
  "Quản trị viên": [
    "Administrator",
    "관리자"
  ],
  "Số điện thoại": [
    "Phone number",
    "전화번호"
  ],
  "Chưa cập nhật": [
    "Not updated",
    "미등록"
  ],
  "Cài đặt tài khoản": [
    "Account settings",
    "계정 설정"
  ],
  "Kỹ năng truy vấn dữ liệu": [
    "Data querying skills",
    "데이터 질의 역량"
  ],
  "Thành phần 1: Truy vấn cơ bản": [
    "Part 1: Basic queries",
    "영역 1: 기본 쿼리"
  ],
  "Truy vấn các cột dữ liệu": [
    "Query data columns",
    "데이터 열 조회"
  ],
  "Lọc dòng theo điều kiện": [
    "Filter rows by condition",
    "조건에 따른 행 필터링"
  ],
  "Sắp xếp ASC / DESC": [
    "Sort ASC / DESC",
    "ASC / DESC 정렬"
  ],
  "Loại bỏ kết quả trùng lặp": [
    "Remove duplicate results",
    "중복 결과 제거"
  ],
  "Thành phần 2: JOIN và gom nhóm": [
    "Part 2: JOIN and grouping",
    "영역 2: JOIN 및 그룹화"
  ],
  "Gom nhóm dữ liệu": [
    "Group data",
    "데이터 그룹화"
  ],
  "Lọc sau khi gom nhóm": [
    "Filter grouped data",
    "그룹화 후 필터링"
  ],
  "Thành phần 3: Truy vấn nâng cao": [
    "Part 3: Advanced queries",
    "영역 3: 고급 쿼리"
  ],
  "Truy vấn lồng": [
    "Subqueries",
    "하위 쿼리"
  ],
  "Thao tác và định nghĩa dữ liệu": [
    "Data manipulation and definition",
    "데이터 조작 및 정의"
  ],
  "Thành phần 1: Thao tác dữ liệu": [
    "Part 1: Data manipulation",
    "영역 1: 데이터 조작"
  ],
  "Thêm bản ghi": [
    "Insert records",
    "레코드 삽입"
  ],
  "Cập nhật dữ liệu": [
    "Update data",
    "데이터 갱신"
  ],
  "Xóa bản ghi theo điều kiện": [
    "Delete records by condition",
    "조건에 따른 레코드 삭제"
  ],
  "Trả về dữ liệu sau thao tác": [
    "Return data after operation",
    "작업 후 데이터 반환"
  ],
  "Thành phần 2: Định nghĩa dữ liệu": [
    "Part 2: Data definition",
    "영역 2: 데이터 정의"
  ],
  "Tạo bảng dữ liệu": [
    "Create tables",
    "테이블 생성"
  ],
  "Thay đổi cấu trúc bảng": [
    "Alter table structure",
    "테이블 구조 변경"
  ],
  "Xóa bảng dữ liệu": [
    "Drop tables",
    "테이블 삭제"
  ],
  "Thành phần 3: View và giao dịch": [
    "Part 3: Views and transactions",
    "영역 3: 뷰 및 트랜잭션"
  ],
  "Tạo và quản lý khung nhìn": [
    "Create and manage views",
    "뷰 생성 및 관리"
  ],
  "Khung nhìn lưu kết quả": [
    "Materialized views",
    "구체화된 뷰"
  ],
  "Xóa toàn bộ dữ liệu trong bảng": [
    "Delete all table data",
    "테이블의 모든 데이터 삭제"
  ],
  "Ràng buộc và thiết kế CSDL": [
    "Database constraints and design",
    "데이터베이스 제약 조건 및 설계"
  ],
  "Thành phần 1: Ràng buộc toàn vẹn": [
    "Part 1: Integrity constraints",
    "영역 1: 무결성 제약 조건"
  ],
  "Khóa chính của bảng": [
    "Table primary key",
    "테이블 기본 키"
  ],
  "Khóa ngoại liên kết các bảng": [
    "Foreign keys linking tables",
    "테이블을 연결하는 외래 키"
  ],
  "Đảm bảo giá trị không trùng lặp": [
    "Ensure unique values",
    "고유한 값 보장"
  ],
  "Kiểm tra điều kiện và giá trị bắt buộc": [
    "Validate conditions and required values",
    "조건 및 필수 값 검사"
  ],
  "Thành phần 2: Thiết kế dữ liệu": [
    "Part 2: Data design",
    "영역 2: 데이터 설계"
  ],
  "Xác định thực thể và thuộc tính": [
    "Identify entities and attributes",
    "개체 및 속성 식별"
  ],
  "Quan hệ 1–1 / 1–N / N–N": [
    "Relationships 1–1 / 1–N / N–N",
    "관계 1–1 / 1–N / N–N"
  ],
  "Mô hình thực thể và liên kết": [
    "Entity relationship model",
    "개체 관계 모델"
  ],
  "Chuyển mô hình ERD thành bảng": [
    "Convert ERD to tables",
    "ERD를 테이블로 변환"
  ],
  "Thành phần 3: Chuẩn hóa và chỉ mục": [
    "Part 3: Normalization and indexes",
    "영역 3: 정규화 및 인덱스"
  ],
  "Phụ thuộc hàm": [
    "Functional dependencies",
    "함수 종속성"
  ],
  "Các dạng chuẩn hóa dữ liệu": [
    "Normal forms",
    "정규형"
  ],
  "Dạng chuẩn Boyce–Codd": [
    "Boyce–Codd normal form",
    "보이스-코드 정규형"
  ],
  "Chỉ mục hỗ trợ truy xuất dữ liệu": [
    "Indexes for data retrieval",
    "데이터 검색 인덱스"
  ],
  "Chưa đủ kết quả": [
    "Insufficient results",
    "결과 부족"
  ],
  "Đạt chuẩn (3/3 CLO)": [
    "Meets standard (3/3 CLOs)",
    "기준 충족 (3/3 CLO)"
  ],
  "Cần bồi dưỡng (2/3 CLO)": [
    "Needs improvement (2/3 CLOs)",
    "보충 학습 필요 (2/3 CLO)"
  ],
  "Không thể lưu ánh xạ.": [
    "Could not save mapping.",
    "매핑을 저장할 수 없습니다."
  ],
  "Tìm kiếm sinh viên": [
    "Search students",
    "학생 검색"
  ],
  "Chọn CLO để chỉnh ánh xạ khái niệm. Bộ lọc trạng thái sinh viên xét tổng kết quả cả 3 CLO.": [
    "Select a CLO to edit concept mappings. Student status reflects all three CLOs.",
    "CLO를 선택하여 개념 매핑을 편집하세요. 학생 상태는 세 CLO 전체를 반영합니다."
  ],
  "Quản lý Chuẩn đầu ra (CLO)": [
    "Learning Outcome (CLO) Management",
    "학습 성과 (CLO) 관리"
  ],
  "Thiết lập ma trận ánh xạ giữa chuẩn đầu ra học phần và khái niệm PostgreSQL để hỗ trợ chấm điểm, đánh giá năng lực.": [
    "Map course learning outcomes to PostgreSQL concepts for scoring and competency assessment.",
    "채점과 역량 평가를 위해 학습 성과를 PostgreSQL 개념에 매핑합니다."
  ],
  "Danh sách CLO": [
    "CLO list",
    "CLO 목록"
  ],
  "Bấm vào một CLO để chỉnh ánh xạ bên phải.": [
    "Select a CLO to edit its mapping on the right.",
    "CLO를 선택하여 오른쪽 매핑을 편집하세요."
  ],
  "Đang chọn": [
    "Selected",
    "선택됨"
  ],
  "Chưa có ánh xạ": [
    "No mappings",
    "매핑 없음"
  ],
  "Trọng số:": [
    "Weight:",
    "가중치:"
  ],
  "khái niệm đã áp dụng": [
    "applied concepts",
    "적용된 개념"
  ],
  "Tổng trọng số:": [
    "Total weight:",
    "총 가중치:"
  ],
  "Danh mục PostgreSQL & Ánh xạ": [
    "PostgreSQL concepts & mappings",
    "PostgreSQL 개념 및 매핑"
  ],
  "Tích chọn khái niệm cần ánh xạ.": [
    "Select concepts to map.",
    "매핑할 개념을 선택하세요."
  ],
  "khái niệm": [
    "concepts",
    "개념"
  ],
  "đã chọn": [
    "selected",
    "선택됨"
  ],
  "Đã chọn:": [
    "Selected:",
    "선택됨:"
  ],
  "khái niệm · CLO": [
    "concepts · CLO",
    "개념 · CLO"
  ],
  "Có thay đổi chưa áp dụng": [
    "Unapplied changes",
    "미적용 변경 사항"
  ],
  "Không có thay đổi mới": [
    "No new changes",
    "새 변경 사항 없음"
  ],
  "Chọn tất cả": [
    "Select all",
    "모두 선택"
  ],
  "Hủy chọn": [
    "Deselect",
    "선택 해제"
  ],
  "Khôi phục": [
    "Restore",
    "복원"
  ],
  "Đang lưu...": [
    "Saving...",
    "저장 중..."
  ],
  "Tra cứu Năng lực CLO theo Sinh viên": [
    "Student CLO competency lookup",
    "학생별 CLO 역량 조회"
  ],
  "Theo dõi kết quả tổng hợp của cả 3 chuẩn đầu ra.": [
    "View aggregated results for all three learning outcomes.",
    "세 학습 성과의 종합 결과를 확인하세요."
  ],
  "Tìm sinh viên": [
    "Search students",
    "학생 검색"
  ],
  "Ngành đào tạo": [
    "Major",
    "전공"
  ],
  "Trạng thái tổng hợp CLO": [
    "Overall CLO status",
    "종합 CLO 상태"
  ],
  "Tất cả trạng thái": [
    "All statuses",
    "모든 상태"
  ],
  "Chưa đạt (0–1/3 CLO)": [
    "Below standard (0–1/3 CLOs)",
    "기준 미달 (0–1/3 CLO)"
  ],
  "Mã SV": [
    "Student ID",
    "학번"
  ],
  "Trạng thái năng lực CLO": [
    "CLO competency status",
    "CLO 역량 상태"
  ],
  "Thao tác": [
    "Actions",
    "작업"
  ],
  "Không có sinh viên phù hợp với bộ lọc.": [
    "No students match the filters.",
    "필터에 맞는 학생이 없습니다."
  ],
  "Đạt": [
    "Pass",
    "충족"
  ],
  "Yếu": [
    "Weak",
    "부족"
  ],
  "Chưa có": [
    "None",
    "없음"
  ],
  "Xem chi tiết": [
    "View details",
    "상세 보기"
  ],
  "trên": [
    "of",
    "중"
  ],
  "sinh viên · Trang": [
    "students · Page",
    "학생 · 페이지"
  ],
  "Phân trang sinh viên": [
    "Student pagination",
    "학생 페이지 탐색"
  ],
  "Trước": [
    "Previous",
    "이전"
  ],
  "UTC+07:00 (Hà Nội, Bangkok)": [
    "UTC+07:00 (Hanoi, Bangkok)",
    "UTC+07:00 (하노이, 방콕)"
  ],
  "Trung tâm Cài đặt DBCAS": [
    "DBCAS Settings Center",
    "DBCAS 설정 센터"
  ],
  "Quản lý tài khoản quản trị viên, số điện thoại và tùy chọn hiển thị.": [
    "Manage administrator accounts, phone numbers and display preferences.",
    "관리자 계정, 전화번호 및 표시 설정을 관리하세요."
  ],
  "Quản lý tài khoản Admin": [
    "Admin account management",
    "관리자 계정 관리"
  ],
  "Thông tin quản trị viên và bảo mật tài khoản.": [
    "Administrator information and account security.",
    "관리자 정보 및 계정 보안."
  ],
  "Họ và tên Admin": [
    "Admin full name",
    "관리자 이름"
  ],
  "Email quản trị": [
    "Admin email",
    "관리자 이메일"
  ],
  "Nhập số điện thoại": [
    "Enter phone number",
    "전화번호 입력"
  ],
  "10 chữ số, bắt đầu bằng 0.": [
    "10 digits, starting with 0.",
    "0으로 시작하는 10자리 숫자."
  ],
  "Đổi mật khẩu tài khoản": [
    "Change account password",
    "계정 비밀번호 변경"
  ],
  "Mật khẩu hiện tại": [
    "Current password",
    "현재 비밀번호"
  ],
  "Mật khẩu mới (ít nhất 6 ký tự)": [
    "New password (at least 6 characters)",
    "새 비밀번호 (최소 6자)"
  ],
  "Xác nhận mật khẩu": [
    "Confirm password",
    "비밀번호 확인"
  ],
  "Hủy bỏ": [
    "Cancel",
    "취소"
  ],
  "Lưu thay đổi": [
    "Save changes",
    "변경 사항 저장"
  ],
  "Cấu hình Múi giờ & Ngày tháng": [
    "Time zone & date settings",
    "시간대 및 날짜 설정"
  ],
  "Chọn cách hiển thị ngày giờ trên giao diện.": [
    "Choose how dates and times are displayed.",
    "날짜와 시간 표시 방법을 선택하세요."
  ],
  "Thời gian hiện tại": [
    "Current time",
    "현재 시간"
  ],
  "Múi giờ hệ thống": [
    "System time zone",
    "시스템 시간대"
  ],
  "Định dạng ngày": [
    "Date format",
    "날짜 형식"
  ],
  "Định dạng giờ": [
    "Time format",
    "시간 형식"
  ],
  "24 giờ (HH:mm:ss)": [
    "24-hour (HH:mm:ss)",
    "24시간 (HH:mm:ss)"
  ],
  "12 giờ (hh:mm:ss AM/PM)": [
    "12-hour (hh:mm:ss AM/PM)",
    "12시간 (hh:mm:ss AM/PM)"
  ],
  "Ngôn ngữ hệ thống": [
    "System language",
    "시스템 언어"
  ],
  "Chọn ngôn ngữ hiển thị cho trang cài đặt.": [
    "Choose the language for all Admin pages.",
    "모든 관리자 페이지의 언어를 선택하세요."
  ],
  "Tùy chọn lưu trên trình duyệt": [
    "Preferences saved in this browser",
    "이 브라우저에 저장된 설정"
  ],
  "Hiện mật khẩu": [
    "Show password",
    "비밀번호 표시"
  ],
  "Ẩn mật khẩu": [
    "Hide password",
    "비밀번호 숨기기"
  ],
  "Vui lòng nhập họ và tên Admin.": [
    "Please enter the admin name.",
    "관리자 이름을 입력하세요."
  ],
  "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.": [
    "Phone number must have 10 digits and start with 0.",
    "전화번호는 0으로 시작하는 10자리여야 합니다."
  ],
  "Vui lòng nhập đầy đủ ba ô mật khẩu.": [
    "Please fill in all three password fields.",
    "비밀번호 입력란 세 개를 모두 입력하세요."
  ],
  "Mật khẩu mới cần ít nhất 6 ký tự.": [
    "New password must have at least 6 characters.",
    "새 비밀번호는 최소 6자여야 합니다."
  ],
  "Xác nhận mật khẩu chưa khớp.": [
    "Password confirmation does not match.",
    "비밀번호 확인이 일치하지 않습니다."
  ],
  "Mật khẩu mới phải khác mật khẩu hiện tại.": [
    "New password must differ from the current password.",
    "새 비밀번호는 현재 비밀번호와 달라야 합니다."
  ],
  "Chưa kết nối chức năng đổi mật khẩu với backend.": [
    "Password changes are not connected to the server yet.",
    "비밀번호 변경 기능이 아직 서버에 연결되지 않았습니다."
  ],
  "Chưa có thay đổi để lưu.": [
    "No changes to save.",
    "저장할 변경 사항이 없습니다."
  ],
  "Đã lưu thay đổi tài khoản.": [
    "Account changes saved.",
    "계정 변경 사항을 저장했습니다."
  ],
  "Đã lưu tên và số điện thoại trên trình duyệt.": [
    "Name and phone number saved in this browser.",
    "이름과 전화번호를 이 브라우저에 저장했습니다."
  ],
  "Đã đổi mật khẩu. Tên và số điện thoại đã lưu trên trình duyệt.": [
    "Password changed. Name and phone number saved in this browser.",
    "비밀번호를 변경하고 이름과 전화번호를 이 브라우저에 저장했습니다."
  ],
  "Thông tin tài khoản đã được lưu.": [
    "Account information saved.",
    "계정 정보를 저장했습니다."
  ],
  "Không thể lưu thay đổi tài khoản.": [
    "Could not save account changes.",
    "계정 변경 사항을 저장할 수 없습니다."
  ],
  "Không thể lưu tùy chọn trên trình duyệt này.": [
    "Could not save preferences in this browser.",
    "이 브라우저에 설정을 저장할 수 없습니다."
  ],
  "Cập nhật thông tin tài khoản và chọn tùy chọn hiển thị.": [
    "Update account information and display preferences.",
    "계정 정보와 표시 설정을 변경하세요."
  ],
  "Tiếng Việt": [
    "Vietnamese",
    "베트남어"
  ],
  "Việt Nam": [
    "Vietnam",
    "베트남"
  ],
  "SELECT, WHERE, JOIN, GROUP BY và truy vấn nâng cao.": [
    "SELECT, WHERE, JOIN, GROUP BY and advanced queries.",
    "SELECT, WHERE, JOIN, GROUP BY 및 고급 쿼리."
  ],
  "Có khả năng sử dụng các câu lệnh truy vấn để khai thác dữ liệu.": [
    "Can use queries to retrieve data.",
    "쿼리를 사용하여 데이터를 조회할 수 있습니다."
  ],
  "Cần củng cố cách xây dựng truy vấn và kiểm tra kết quả trả về.": [
    "Improve query construction and result validation.",
    "쿼리 작성 및 결과 검증을 보완해야 합니다."
  ],
  "Luyện thêm truy vấn nhiều bảng, gom nhóm và truy vấn lồng.": [
    "Practice multi-table queries, grouping and subqueries.",
    "다중 테이블 쿼리, 그룹화 및 하위 쿼리를 연습하세요."
  ],
  "INSERT, UPDATE, DELETE, CREATE, ALTER và quản lý dữ liệu.": [
    "INSERT, UPDATE, DELETE, CREATE, ALTER and data management.",
    "INSERT, UPDATE, DELETE, CREATE, ALTER 및 데이터 관리."
  ],
  "Nắm được các thao tác dữ liệu và cách định nghĩa cấu trúc bảng.": [
    "Understands data operations and table definitions.",
    "데이터 작업과 테이블 정의를 이해합니다."
  ],
  "Cần củng cố cú pháp thao tác dữ liệu và kiểm soát phạm vi cập nhật.": [
    "Improve data manipulation syntax and update scope control.",
    "데이터 조작 구문 및 갱신 범위 관리를 보완해야 합니다."
  ],
  "Thực hành tạo bảng, thay đổi cấu trúc và thao tác dữ liệu có điều kiện.": [
    "Practice creating and altering tables and conditional data operations.",
    "테이블 생성, 구조 변경 및 조건부 데이터 작업을 연습하세요."
  ],
  "Khóa, ràng buộc toàn vẹn, quan hệ và chuẩn hóa dữ liệu.": [
    "Keys, integrity constraints, relationships and normalization.",
    "키, 무결성 제약 조건, 관계 및 정규화."
  ],
  "Có khả năng xác định cấu trúc dữ liệu và các ràng buộc cơ bản.": [
    "Can identify data structures and basic constraints.",
    "데이터 구조와 기본 제약 조건을 식별할 수 있습니다."
  ],
  "Cần củng cố cách xác định quan hệ, khóa và chuẩn hóa dữ liệu.": [
    "Improve relationship, key and normalization analysis.",
    "관계, 키 및 정규화 분석을 보완해야 합니다."
  ],
  "Luyện xác định khóa chính, khóa ngoại và chuẩn hóa đến 3NF.": [
    "Practice primary keys, foreign keys and normalization to 3NF.",
    "기본 키, 외래 키 및 3NF 정규화를 연습하세요."
  ],
  "Quay lại CLO & Kỹ năng": [
    "Back to CLO & Skills",
    "CLO 및 역량으로 돌아가기"
  ],
  "Chưa có dữ liệu sinh viên": [
    "No student data",
    "학생 데이터 없음"
  ],
  "Quay lại danh sách và chọn “Xem chi tiết”.": [
    "Return to the list and select “View details”.",
    "목록으로 돌아가서 “상세 보기”를 선택하세요."
  ],
  "Chưa có nhận xét AI.": [
    "No AI comments yet.",
    "AI 평가 의견이 없습니다."
  ],
  "Sinh viên đạt yêu cầu của CLO này. Tiếp tục luyện tập để nâng cao khả năng vận dụng.": [
    "This CLO is achieved. Continue practicing to improve application skills.",
    "이 CLO를 달성했습니다. 응용 역량을 높이기 위해 계속 연습하세요."
  ],
  "Sinh viên cần củng cố kiến thức và thực hành thêm các nội dung thuộc CLO này.": [
    "The student needs further study and practice for this CLO.",
    "이 CLO에 대한 보충 학습과 연습이 필요합니다."
  ],
  "Chưa đủ dữ liệu để đánh giá CLO.": [
    "Insufficient data to assess this CLO.",
    "이 CLO를 평가할 데이터가 부족합니다."
  ],
  "Chi tiết CLO sinh viên": [
    "Student CLO details",
    "학생 CLO 상세"
  ],
  "ĐÁNH GIÁ CHUẨN ĐẦU RA": [
    "LEARNING OUTCOME ASSESSMENT",
    "학습 성과 평가"
  ],
  "Chi tiết năng lực CLO": [
    "CLO competency details",
    "CLO 역량 상세"
  ],
  "Họ và tên": [
    "Full name",
    "이름"
  ],
  "Mã số sinh viên": [
    "Student ID",
    "학번"
  ],
  "Đánh giá từng CLO": [
    "Assessment by CLO",
    "CLO별 평가"
  ],
  "Dữ liệu tạm": [
    "Temporary data",
    "임시 데이터"
  ],
  "Kết quả phân tích AI": [
    "AI analysis results",
    "AI 분석 결과"
  ],
  "Cần cải thiện": [
    "Needs improvement",
    "개선 필요"
  ],
  "Chưa có kết quả": [
    "No results yet",
    "결과 없음"
  ],
  "Nhận xét tổng quan": [
    "Overall assessment",
    "종합 평가"
  ],
  "Điểm mạnh": [
    "Strengths",
    "강점"
  ],
  "Chưa ghi nhận điểm mạnh cụ thể.": [
    "No specific strengths recorded.",
    "구체적인 강점이 기록되지 않았습니다."
  ],
  "Điểm cần cải thiện": [
    "Areas for improvement",
    "개선 영역"
  ],
  "Chưa ghi nhận nội dung cần cải thiện.": [
    "No improvement areas recorded.",
    "개선 영역이 기록되지 않았습니다."
  ],
  "Đề xuất học tập": [
    "Study recommendations",
    "학습 추천"
  ],
  "Chưa có đề xuất học tập.": [
    "No study recommendations yet.",
    "학습 추천이 없습니다."
  ],
  "DBCAS · Đánh giá năng lực chuẩn đầu ra": [
    "DBCAS · Learning outcome assessment",
    "DBCAS · 학습 성과 평가"
  ],
  "ACID & Khóa phân tán": [
    "ACID & Distributed locks",
    "ACID 및 분산 잠금"
  ],
  "Chưa duyệt": [
    "Pending review",
    "검토 대기"
  ],
  "Đã duyệt thủ công": [
    "Manually approved",
    "수동 승인됨"
  ],
  "Đã duyệt AI": [
    "AI score approved",
    "AI 점수 승인됨"
  ],
  "Chưa kết nối chức năng duyệt điểm.": [
    "Score approval is not connected yet.",
    "점수 승인 기능이 연결되지 않았습니다."
  ],
  "Đã xác nhận điểm AI làm điểm cuối cùng.": [
    "AI score confirmed as the final score.",
    "AI 점수를 최종 점수로 확정했습니다."
  ],
  "Không thể duyệt điểm.": [
    "Could not approve score.",
    "점수를 승인할 수 없습니다."
  ],
  "Nhập đầy đủ điểm từ 0 đến 1 cho mỗi tiêu chí.": [
    "Enter a score from 0 to 1 for every criterion.",
    "각 기준에 0부터 1까지의 점수를 입력하세요."
  ],
  "Vui lòng nhập nhận xét.": [
    "Please enter comments.",
    "평가 의견을 입력하세요."
  ],
  "Chưa kết nối chức năng lưu điểm GV.": [
    "Teacher score saving is not connected yet.",
    "교사 점수 저장 기능이 연결되지 않았습니다."
  ],
  "Không thể xác nhận điểm GV.": [
    "Could not confirm teacher score.",
    "교사 점수를 확정할 수 없습니다."
  ],
  "Tìm tên sinh viên hoặc MSSV": [
    "Search student name or ID",
    "학생 이름 또는 학번 검색"
  ],
  "Duyệt điểm AI để giữ kết quả AI. Sửa điểm để chấm và xác nhận kết quả thủ công.": [
    "Approve the AI score or edit it to confirm a manual assessment.",
    "AI 점수를 승인하거나 수정하여 수동 평가를 확정하세요."
  ],
  "THẨM ĐỊNH BÀI THI": [
    "EXAM REVIEW",
    "시험 검토"
  ],
  "Đối chiếu kết quả AI, chấm lại thủ công theo rubric và xác nhận điểm cuối cùng cho sinh viên.": [
    "Compare AI results, regrade using the rubric and confirm final student scores.",
    "AI 결과를 비교하고 루브릭으로 재채점하여 최종 점수를 확정하세요."
  ],
  "Chỉ số chấm AI": [
    "AI grading metrics",
    "AI 채점 지표"
  ],
  "Bài thi tự luận đã chấm AI": [
    "AI-graded essays",
    "AI 채점 서술형 답안"
  ],
  "bài làm": [
    "submissions",
    "제출 답안"
  ],
  "Trong năm học đã chọn": [
    "In the selected academic year",
    "선택한 학년도"
  ],
  "Thời gian AI chấm trung bình": [
    "Average AI grading time",
    "평균 AI 채점 시간"
  ],
  "/ bài làm": [
    "/ submission",
    "/ 답안"
  ],
  "Trung bình thời gian chấm": [
    "Average grading time",
    "평균 채점 시간"
  ],
  "Độ tương đồng GV & AI": [
    "Teacher & AI agreement",
    "교사 및 AI 일치도"
  ],
  "bài có điểm đối chiếu": [
    "compared submissions",
    "점수 비교 답안"
  ],
  "Cảnh báo chênh lệch (>0.75đ)": [
    "Score discrepancy alerts (>0.75)",
    "점수 차이 경고 (>0.75)"
  ],
  "bài thi": [
    "exams",
    "시험"
  ],
  "bài chưa duyệt": [
    "pending submissions",
    "검토 대기 답안"
  ],
  "Xem bài thi đã duyệt": [
    "View approved exams",
    "승인된 시험 보기"
  ],
  "Thẩm định lại điểm AI": [
    "Review AI scores",
    "AI 점수 재검토"
  ],
  "Kết quả bài thi đã được xác nhận.": [
    "Exam results have been confirmed.",
    "시험 결과가 확정되었습니다."
  ],
  "Quay lại thẩm định": [
    "Back to review",
    "검토로 돌아가기"
  ],
  "Bài chưa duyệt trước": [
    "Previous pending submission",
    "이전 검토 대기 답안"
  ],
  "Bài chưa duyệt tiếp theo": [
    "Next pending submission",
    "다음 검토 대기 답안"
  ],
  "Điểm AI": [
    "AI score",
    "AI 점수"
  ],
  "Điểm GV": [
    "Teacher score",
    "교사 점수"
  ],
  "Điểm cuối cùng": [
    "Final score",
    "최종 점수"
  ],
  "Chờ xác nhận": [
    "Awaiting confirmation",
    "확정 대기"
  ],
  "Bài làm tự luận": [
    "Essay submission",
    "서술형 답안"
  ],
  "Chưa có nội dung bài làm.": [
    "No submission content.",
    "답안 내용이 없습니다."
  ],
  "Nhận xét AI": [
    "AI comments",
    "AI 평가 의견"
  ],
  "Điểm mạnh:": [
    "Strengths:",
    "강점:"
  ],
  "Chưa có nhận xét.": [
    "No comments yet.",
    "평가 의견이 없습니다."
  ],
  "Nhận xét duyệt của GV": [
    "Teacher approval comments",
    "교사 승인 의견"
  ],
  "Điểm GV:": [
    "Teacher score:",
    "교사 점수:"
  ],
  "· Chênh lệch AI:": [
    "· AI difference:",
    "· AI 점수 차이:"
  ],
  "đ": [
    "pts",
    "점"
  ],
  "← Bài trước": [
    "← Previous submission",
    "← 이전 답안"
  ],
  "Bài tiếp theo →": [
    "Next submission →",
    "다음 답안 →"
  ],
  "Sửa điểm": [
    "Edit score",
    "점수 수정"
  ],
  "Đang duyệt...": [
    "Approving...",
    "승인 중..."
  ],
  "Duyệt điểm AI": [
    "Approve AI score",
    "AI 점수 승인"
  ],
  "Không có bài thi chờ duyệt": [
    "No exams awaiting review",
    "검토 대기 시험 없음"
  ],
  "Bấm Xem trong danh sách để xem lại bài đã duyệt.": [
    "Select View in the list to review approved submissions.",
    "목록에서 보기를 선택하여 승인된 답안을 확인하세요."
  ],
  "Danh sách bài thi chấm bằng AI": [
    "AI-graded exam list",
    "AI 채점 시험 목록"
  ],
  "Điểm AI, điểm GV và kết quả cuối cùng theo thang 3.0": [
    "AI, teacher and final scores out of 3.0",
    "AI, 교사 및 최종 점수, 3.0점 만점"
  ],
  "Lọc trạng thái": [
    "Filter status",
    "상태 필터"
  ],
  "Đã duyệt": [
    "Approved",
    "승인됨"
  ],
  "Duyệt thủ công": [
    "Manual approval",
    "수동 승인"
  ],
  "Chưa kết nối chức năng xuất bảng điểm.": [
    "Score export is not connected yet.",
    "성적표 내보내기 기능이 연결되지 않았습니다."
  ],
  "Xuất bảng điểm": [
    "Export scores",
    "성적표 내보내기"
  ],
  "Đề bài": [
    "Problem statement",
    "문제"
  ],
  "Điểm cuối": [
    "Final score",
    "최종 점수"
  ],
  "Chênh lệch": [
    "Difference",
    "차이"
  ],
  "Trạng thái": [
    "Status",
    "상태"
  ],
  "Không tìm thấy bài thi phù hợp.": [
    "No matching exams.",
    "일치하는 시험이 없습니다."
  ],
  "Chưa đối chiếu": [
    "Not compared",
    "미비교"
  ],
  "Phân trang bài thi": [
    "Exam pagination",
    "시험 페이지 탐색"
  ],
  "Chấm lại thủ công": [
    "Manual regrading",
    "수동 재채점"
  ],
  "Đóng hộp chấm thủ công": [
    "Close manual grading dialog",
    "수동 채점 창 닫기"
  ],
  "Nhập điểm theo đánh giá của GV. Điểm AI được giữ nguyên để đối chiếu.": [
    "Enter teacher scores. AI scores remain available for comparison.",
    "교사 점수를 입력하세요. AI 점수는 비교를 위해 유지됩니다."
  ],
  "Tiêu chí": [
    "Criterion",
    "기준"
  ],
  "Tổng điểm AI": [
    "Total AI score",
    "AI 총점"
  ],
  "Tổng điểm GV": [
    "Total teacher score",
    "교사 총점"
  ],
  "Vui lòng nhận xét": [
    "Please enter comments",
    "평가 의견 입력"
  ],
  "Xác nhận sẽ lấy điểm GV làm điểm cuối cùng, chuyển bài sang Đã duyệt thủ công.": [
    "Confirmation uses the teacher score as final and marks the submission manually approved.",
    "확정 시 교사 점수가 최종 점수가 되며 수동 승인 상태로 변경됩니다."
  ],
  "Hủy": [
    "Cancel",
    "취소"
  ],
  "Đang xác nhận...": [
    "Confirming...",
    "확정 중..."
  ],
  "Xác nhận điểm GV": [
    "Confirm teacher score",
    "교사 점수 확정"
  ],
  "Kỹ năng truy vấn và khai thác dữ liệu.": [
    "Data querying and retrieval skills.",
    "데이터 질의 및 조회 역량."
  ],
  "Thao tác và định nghĩa cấu trúc dữ liệu.": [
    "Data manipulation and structure definition.",
    "데이터 조작 및 구조 정의."
  ],
  "Ràng buộc toàn vẹn và thiết kế cơ sở dữ liệu.": [
    "Integrity constraints and database design.",
    "무결성 제약 조건 및 데이터베이스 설계."
  ],
  "Dữ liệu danh sách sinh viên không hợp lệ.": [
    "Invalid student list data.",
    "학생 목록 데이터가 유효하지 않습니다."
  ],
  "Không thể tải danh sách sinh viên.": [
    "Could not load student list.",
    "학생 목록을 불러올 수 없습니다."
  ],
  "Sinh viên chưa có mã số để mở hồ sơ.": [
    "Student ID is required to open the profile.",
    "프로필을 열려면 학번이 필요합니다."
  ],
  "Tìm sinh viên và bấm Xem chi tiết để mở hồ sơ năng lực.": [
    "Find a student and select View details to open the competency profile.",
    "학생을 찾아 상세 보기를 선택하여 역량 프로필을 여세요."
  ],
  "Đánh giá năng lực sinh viên": [
    "Student competency assessment",
    "학생 역량 평가"
  ],
  "Theo dõi chuẩn đầu ra và xem hồ sơ năng lực của từng sinh viên.": [
    "Track learning outcomes and view individual competency profiles.",
    "학습 성과와 학생별 역량 프로필을 확인하세요."
  ],
  "Chỉ số năng lực": [
    "Competency metrics",
    "역량 지표"
  ],
  "Năng lực trung bình": [
    "Average competency",
    "평균 역량"
  ],
  "Chưa có dữ liệu tổng quan": [
    "No overview data",
    "개요 데이터 없음"
  ],
  "Sinh viên đạt chuẩn": [
    "Students meeting standards",
    "기준 충족 학생"
  ],
  "Sinh viên chưa đạt": [
    "Students below standards",
    "기준 미달 학생"
  ],
  "Biểu đồ radar 3 chuẩn đầu ra": [
    "Radar chart of 3 learning outcomes",
    "학습 성과 3개 레이더 차트"
  ],
  "Tỷ lệ sinh viên đạt từng CLO so với mục tiêu 80%.": [
    "CLO attainment rates compared with the 80% target.",
    "CLO 달성률과 80% 목표 비교."
  ],
  "Tỷ lệ đạt thực tế": [
    "Actual attainment rate",
    "실제 달성률"
  ],
  "Mục tiêu 80%": [
    "80% target",
    "목표 80%"
  ],
  "CLO có tỷ lệ đạt cao nhất": [
    "CLO with highest attainment",
    "달성률이 가장 높은 CLO"
  ],
  "CLO có tỷ lệ đạt thấp nhất": [
    "CLO with lowest attainment",
    "달성률이 가장 낮은 CLO"
  ],
  "Chưa có dữ liệu radar.": [
    "No radar data available.",
    "레이더 데이터가 없습니다."
  ],
  "Ma trận phân tích chuẩn đầu ra": [
    "Learning outcome analysis matrix",
    "학습 성과 분석 행렬"
  ],
  "Mục tiêu: ít nhất 80% sinh viên đạt từng CLO.": [
    "Target: at least 80% of students achieve each CLO.",
    "목표: 각 CLO에서 학생 80% 이상 달성."
  ],
  "Đạt mục tiêu": [
    "Target achieved",
    "목표 달성"
  ],
  "Chưa có dữ liệu CLO.": [
    "No CLO data available.",
    "CLO 데이터가 없습니다."
  ],
  "Xem ma trận ánh xạ CLO & Kỹ năng": [
    "View CLO & Skills mapping matrix",
    "CLO 및 역량 매핑 행렬 보기"
  ],
  "Danh sách sinh viên": [
    "Student list",
    "학생 목록"
  ],
  "Tra cứu sinh viên và xem hồ sơ phân tích năng lực cá nhân.": [
    "Look up students and view individual competency analysis.",
    "학생을 조회하고 개인 역량 분석을 확인하세요."
  ],
  "Trạng thái CLO": [
    "CLO status",
    "CLO 상태"
  ],
  "Tất cả trạng thái CLO": [
    "All CLO statuses",
    "모든 CLO 상태"
  ],
  "Chưa đạt (1/3 CLO)": [
    "Below standard (1/3 CLOs)",
    "기준 미달 (1/3 CLO)"
  ],
  "Chưa đạt (0/3 CLO)": [
    "Below standard (0/3 CLOs)",
    "기준 미달 (0/3 CLO)"
  ],
  "Điểm yếu": [
    "Weaknesses",
    "약점"
  ],
  "Chuẩn CLO": [
    "CLO standard",
    "CLO 기준"
  ],
  "Đang tải danh sách sinh viên...": [
    "Loading student list...",
    "학생 목록 로딩 중..."
  ],
  "Thử lại": [
    "Retry",
    "다시 시도"
  ],
  "Chưa có phân tích": [
    "No analysis yet",
    "분석 없음"
  ],
  "Đang tải...": [
    "Loading...",
    "로딩 중..."
  ],
  "Chưa tải được danh sách": [
    "Could not load list",
    "목록을 불러오지 못했습니다"
  ],
  "← Quay lại danh sách": [
    "← Back to list",
    "← 목록으로 돌아가기"
  ],
  "Chưa đủ kết quả đánh giá": [
    "Insufficient assessment results",
    "평가 결과 부족"
  ],
  "Đạt chuẩn đầu ra": [
    "Learning outcomes achieved",
    "학습 성과 달성"
  ],
  "Cần bổ sung kết quả của cả 3 CLO để đánh giá đầy đủ năng lực sinh viên.": [
    "Results for all three CLOs are required for a complete competency assessment.",
    "완전한 역량 평가를 위해 세 CLO의 결과가 필요합니다."
  ],
  "Sinh viên đạt yêu cầu ở cả 3 chuẩn đầu ra. Có thể tiếp tục luyện tập các nội dung nâng cao để phát triển năng lực.": [
    "All three learning outcomes are achieved. Continue advanced practice to develop competency.",
    "세 학습 성과를 모두 달성했습니다. 고급 연습으로 역량을 발전시키세요."
  ],
  "Chưa có nhận xét tổng quan từ AI.": [
    "No overall AI comments yet.",
    "AI 종합 평가 의견이 없습니다."
  ],
  "Tiếp tục luyện tập các bài vận dụng nâng cao.": [
    "Continue practicing advanced applications.",
    "고급 응용 문제를 계속 연습하세요."
  ],
  "Hồ sơ sinh viên": [
    "Student profile",
    "학생 프로필"
  ],
  "HỒ SƠ CÁ NHÂN": [
    "PERSONAL PROFILE",
    "개인 프로필"
  ],
  "Tổng quan năng lực sinh viên": [
    "Student competency overview",
    "학생 역량 개요"
  ],
  "Chưa đủ kết quả đánh giá CLO": [
    "Insufficient CLO assessment results",
    "CLO 평가 결과 부족"
  ],
  "CLO đạt chuẩn": [
    "Achieved CLOs",
    "달성한 CLO"
  ],
  "Tỷ lệ CLO đạt yêu cầu trong hồ sơ năng lực.": [
    "CLO attainment rate in the competency profile.",
    "역량 프로필의 CLO 달성률."
  ],
  "Bài kiểm tra đã làm": [
    "Completed tests",
    "완료한 시험"
  ],
  "CLO cần cải thiện": [
    "CLOs needing improvement",
    "개선이 필요한 CLO"
  ],
  "Cập nhật gần nhất": [
    "Last updated",
    "최근 업데이트"
  ],
  "Nhận định tổng quan": [
    "Overall assessment",
    "종합 평가"
  ],
  "Phân tích AI": [
    "AI analysis",
    "AI 분석"
  ],
  "Bức tranh năng lực": [
    "Competency overview",
    "역량 현황"
  ],
  "Chuẩn đạt": [
    "Passing standard",
    "달성 기준"
  ],
  "ĐIỂM MẠNH": [
    "STRENGTHS",
    "강점"
  ],
  "Năng lực nổi bật": [
    "Outstanding competencies",
    "우수 역량"
  ],
  "Chưa có nhận xét điểm mạnh.": [
    "No strength comments yet.",
    "강점 평가 의견이 없습니다."
  ],
  "ƯU TIÊN CẢI THIỆN": [
    "IMPROVEMENT PRIORITIES",
    "개선 우선순위"
  ],
  "Duy trì và nâng cao": [
    "Maintain and improve",
    "유지 및 향상"
  ],
  "Nội dung cần củng cố": [
    "Areas to reinforce",
    "보완 영역"
  ],
  "Cả 3 CLO đều đạt chuẩn hiện tại.": [
    "All three CLOs currently meet standards.",
    "현재 세 CLO 모두 기준을 충족합니다."
  ],
  "Chưa có nhận xét điểm yếu.": [
    "No weakness comments yet.",
    "약점 평가 의견이 없습니다."
  ],
  "ĐỊNH HƯỚNG HỌC TẬP": [
    "STUDY GUIDANCE",
    "학습 방향"
  ],
  "Bước tiếp theo": [
    "Next steps",
    "다음 단계"
  ],
  "DBCAS · Hồ sơ năng lực sinh viên": [
    "DBCAS · Student competency profile",
    "DBCAS · 학생 역량 프로필"
  ],
  "Không thể mở chi tiết sinh viên.": [
    "Could not open student details.",
    "학생 상세 정보를 열 수 없습니다."
  ],
  "Chưa có dữ liệu theo năm học. Các số liệu hiện tại chưa thay đổi.": [
    "No data for this academic year. Current figures are unchanged.",
    "이 학년도의 데이터가 없어 현재 수치를 유지합니다."
  ],
  "Không thể tải dữ liệu năm học.": [
    "Could not load academic year data.",
    "학년도 데이터를 불러올 수 없습니다."
  ],
  "Họ tên": [
    "Full name",
    "이름"
  ],
  "Trắc nghiệm (4đ)": [
    "MCQ (4 pts)",
    "객관식 (4점)"
  ],
  "SQL (3đ)": [
    "SQL (3 pts)",
    "SQL (3점)"
  ],
  "Tự luận (3đ)": [
    "Essay (3 pts)",
    "서술형 (3점)"
  ],
  "Tổng điểm (10đ)": [
    "Total (10 pts)",
    "총점 (10점)"
  ],
  "Không thể xuất báo cáo.": [
    "Could not export report.",
    "보고서를 내보낼 수 없습니다."
  ],
  "Liên hệ nhóm hỗ trợ DBCAS.": [
    "Contact DBCAS support.",
    "DBCAS 지원팀에 문의하세요."
  ],
  "Chưa có thông báo mới trong bản giao diện mẫu.": [
    "No new notifications.",
    "새 알림이 없습니다."
  ],
  "Tổng quan hệ thống": [
    "System overview",
    "시스템 개요"
  ],
  "Cập nhật 16:45:20": [
    "Updated 16:45:20",
    "업데이트 16:45:20"
  ],
  "Xin chào Admin!": [
    "Hello, Admin!",
    "안녕하세요, 관리자님!"
  ],
  "Hệ thống đang hoạt động tối ưu.": [
    "The system is operating normally.",
    "시스템이 정상 작동 중입니다."
  ],
  "Theo dõi năng lực của": [
    "Track competency for",
    "역량 추적 대상:"
  ],
  "thông qua 10 câu hỏi trắc nghiệm, 3 bài thực hành SQL Sandbox và 1 bài tự luận thiết kế CSDL được hỗ trợ đánh giá bằng AI.": [
    "through 10 MCQs, 3 SQL Sandbox tasks and 1 AI-assisted database design essay.",
    "객관식 10문항, SQL Sandbox 3문항, AI 지원 데이터베이스 설계 서술형 1문항으로 평가합니다."
  ],
  "Tổng sinh viên": [
    "Total students",
    "전체 학생"
  ],
  "So với học kỳ trước": [
    "Compared with last semester",
    "지난 학기 대비"
  ],
  "Bài kiểm tra": [
    "Tests",
    "시험"
  ],
  "đợt thi": [
    "exam sessions",
    "시험 회차"
  ],
  "13 đề đang soạn": [
    "13 drafts in progress",
    "작성 중 시험지 13개"
  ],
  "Điểm năng lực trung bình": [
    "Average competency score",
    "평균 역량 점수"
  ],
  "ĐẠT CLO": [
    "CLO ACHIEVEMENT",
    "CLO 달성"
  ],
  "Mục tiêu ≥ 85%": [
    "Target ≥ 85%",
    "목표 ≥ 85%"
  ],
  "Ma Trận & Đánh Giá Năng Lực CSDL": [
    "Database Competency Matrix & Assessment",
    "데이터베이스 역량 행렬 및 평가"
  ],
  "Phân tích Concept Breakdown, biểu đồ Radar và khoảng cách năng lực": [
    "Concept breakdown, radar charts and competency gaps",
    "개념 분석, 레이더 차트 및 역량 격차"
  ],
  "Học viên": [
    "Learners",
    "학습자"
  ],
  "Benchmark: ĐHQGHN": [
    "Benchmark: VNU Hanoi",
    "벤치마크: 하노이 국립대학교"
  ],
  "Tỷ lệ đạt": [
    "Attainment rate",
    "달성률"
  ],
  "Trọng tâm: JOIN, Gom nhóm & Truy vấn nâng cao": [
    "Focus: JOIN, Grouping & Advanced queries",
    "중점: JOIN, 그룹화 및 고급 쿼리"
  ],
  "Trọng tâm: Cú pháp DML/DDL, Schema & Views": [
    "Focus: DML/DDL syntax, Schema & Views",
    "중점: DML/DDL 구문, 스키마 및 뷰"
  ],
  "Trọng tâm: Ràng buộc toàn vẹn, Chuẩn hóa dữ liệu": [
    "Focus: Integrity constraints & Normalization",
    "중점: 무결성 제약 조건 및 정규화"
  ],
  "Thực tế": [
    "Actual",
    "실제"
  ],
  "Trụ cột đạt mục tiêu": [
    "Pillars meeting target",
    "목표 달성 영역"
  ],
  "/3 trụ cột": [
    "/3 pillars",
    "/3 영역"
  ],
  "Tỷ lệ đạt trung bình:": [
    "Average attainment:",
    "평균 달성률:"
  ],
  "Tỉ lệ đạt chuẩn": [
    "Standard attainment rate",
    "기준 달성률"
  ],
  "Điểm Trung Bình Khóa": [
    "Cohort Average Score",
    "전체 평균 점수"
  ],
  "Trung vị": [
    "Median",
    "중앙값"
  ],
  "Thủ Khoa Đợt Thi": [
    "Top Student in Exam Session",
    "시험 회차 수석"
  ],
  "Điểm cao nhất": [
    "Highest score",
    "최고 점수"
  ],
  "Tỉ Lệ Giỏi / Xuất sắc": [
    "Very Good / Excellent Rate",
    "우수 / 최우수 비율"
  ],
  "Chưa có dữ liệu": [
    "No data",
    "데이터 없음"
  ],
  "Xem bảng xếp hạng đầy đủ →": [
    "View full ranking →",
    "전체 순위 보기 →"
  ],
  "Nhật Ký & Cảnh Báo Trực Tiếp": [
    "Live Logs & Alerts",
    "실시간 로그 및 경고"
  ],
  "hoàn thành 3 bài thực hành SQL, đạt toàn bộ test case.": [
    "completed 3 SQL tasks, passing all test cases.",
    "SQL 3문항을 완료하고 모든 테스트를 통과했습니다."
  ],
  "1 phút trước": [
    "1 minute ago",
    "1분 전"
  ],
  "AI đã đánh giá": [
    "AI assessed",
    "AI 평가 완료:"
  ],
  "18 bài tự luận": [
    "18 essays",
    "서술형 답안 18개"
  ],
  "thiết kế Schema & ERD.": [
    "Schema & ERD design.",
    "스키마 및 ERD 설계."
  ],
  "5 phút trước": [
    "5 minutes ago",
    "5분 전"
  ],
  "Phát hiện": [
    "Detected",
    "감지:"
  ],
  "14 sinh viên": [
    "14 students",
    "학생 14명"
  ],
  "cần củng cố kiến thức Transaction & Concurrency.": [
    "need to reinforce Transaction & Concurrency knowledge.",
    "트랜잭션 및 동시성 보충 학습이 필요합니다."
  ],
  "18 phút trước": [
    "18 minutes ago",
    "18분 전"
  ],
  "đã giải phóng tài nguyên sau đợt thi.": [
    "released resources after the exam session.",
    "시험 후 리소스를 해제했습니다."
  ],
  "25 phút trước": [
    "25 minutes ago",
    "25분 전"
  ],
  "Bài tự luận của": [
    "Essay by",
    "서술형 답안 작성자:"
  ],
  "đã được chấm theo rubric AI.": [
    "was graded using the AI rubric.",
    "AI 루브릭으로 채점되었습니다."
  ],
  "31 phút trước": [
    "31 minutes ago",
    "31분 전"
  ],
  "Đã đồng bộ kết quả của": [
    "Synchronized results for",
    "결과 동기화 완료:"
  ],
  "42 phút trước": [
    "42 minutes ago",
    "42분 전"
  ],
  "Khởi tạo": [
    "Initialized",
    "초기화:"
  ],
  "phục vụ ca thi chiều.": [
    "for the afternoon exam session.",
    "오후 시험을 위한 준비."
  ],
  "50 phút trước": [
    "50 minutes ago",
    "50분 전"
  ],
  "Nhật ký hiện là dữ liệu mẫu. Chức năng tải nhật ký hệ thống chưa được kết nối.": [
    "Logs currently use sample data. System log loading is not connected yet.",
    "현재 로그는 예시 데이터이며 시스템 로그 불러오기는 아직 연결되지 않았습니다."
  ],
  "Xem toàn bộ nhật ký hệ thống": [
    "View all system logs",
    "전체 시스템 로그 보기"
  ],
  "Kết quả đánh giá sinh viên gần đây": [
    "Recent student assessment results",
    "최근 학생 평가 결과"
  ],
  "Trọng số: Trắc nghiệm 40% • SQL 30% • Tự luận 30%": [
    "Weights: MCQ 40% • SQL 30% • Essay 30%",
    "가중치: 객관식 40% • SQL 30% • 서술형 30%"
  ],
  "Đang xuất...": [
    "Exporting...",
    "내보내는 중..."
  ],
  "Xuất báo cáo": [
    "Export report",
    "보고서 내보내기"
  ],
  "SINH VIÊN": [
    "STUDENT",
    "학생"
  ],
  "BÀI KIỂM TRA": [
    "TEST",
    "시험"
  ],
  "TRẮC NGHIỆM": [
    "MCQ",
    "객관식"
  ],
  "TỰ LUẬN AI": [
    "AI ESSAY",
    "AI 서술형"
  ],
  "TỔNG ĐIỂM": [
    "TOTAL SCORE",
    "총점"
  ],
  "THAO TÁC": [
    "ACTIONS",
    "작업"
  ],
  "Cần ôn luyện": [
    "Needs practice",
    "복습 필요"
  ],
  "Bài kiểm tra CSDL": [
    "Database test",
    "데이터베이스 시험"
  ],
  "Trắc nghiệm": [
    "Multiple choice",
    "객관식"
  ],
  "điểm": [
    "points",
    "점"
  ],
  "Tự luận": [
    "Essay",
    "서술형"
  ],
  "Không tìm thấy sinh viên phù hợp.": [
    "No matching students found.",
    "일치하는 학생을 찾을 수 없습니다."
  ],
  "kết quả": [
    "results",
    "결과"
  ],
  "Phân trang kết quả sinh viên": [
    "Student results pagination",
    "학생 결과 페이지 탐색"
  ],
  "Tiếp": [
    "Next",
    "다음"
  ],
  "Đề chưa đặt tên": [
    "Untitled test",
    "제목 없는 시험"
  ],
  "Chưa chọn ngày": [
    "No date selected",
    "날짜 미선택"
  ],
  "Vui lòng chọn ngày thi và giờ bắt đầu.": [
    "Please select exam date and start time.",
    "시험 날짜와 시작 시간을 선택하세요."
  ],
  "Ngày thi không hợp lệ.": [
    "Invalid exam date.",
    "시험 날짜가 유효하지 않습니다."
  ],
  "Thời lượng phải là số nguyên từ 1 đến 600 phút.": [
    "Duration must be an integer from 1 to 600 minutes.",
    "시간은 1부터 600분까지의 정수여야 합니다."
  ],
  "Giờ bắt đầu không hợp lệ.": [
    "Invalid start time.",
    "시작 시간이 유효하지 않습니다."
  ],
  "Đã lưu thời gian thi.": [
    "Exam schedule saved.",
    "시험 일정을 저장했습니다."
  ],
  "Đã lưu thời gian thi trong trình duyệt.": [
    "Exam schedule saved in this browser.",
    "시험 일정을 이 브라우저에 저장했습니다."
  ],
  "Đã cập nhật lịch trong phiên hiện tại. Không lưu được khi tải lại trang.": [
    "Schedule updated for this session but could not be persisted.",
    "현재 세션의 일정은 변경되었지만 영구 저장하지 못했습니다."
  ],
  "Không thể lưu thời gian thi.": [
    "Could not save exam schedule.",
    "시험 일정을 저장할 수 없습니다."
  ],
  "Không thể mở bài kiểm tra.": [
    "Could not open test.",
    "시험을 열 수 없습니다."
  ],
  "Bài đã công bố và bản nháp nằm ở hai tab.": [
    "Published tests and drafts are in separate tabs.",
    "공개 시험과 초안은 별도 탭에 있습니다."
  ],
  "Bấm Soạn tiếp để mở phần đang soạn.": [
    "Select Continue editing to open the draft section.",
    "계속 작성을 선택하여 초안을 여세요."
  ],
  "QUẢN TRỊ ĐÁNH GIÁ": [
    "ASSESSMENT ADMINISTRATION",
    "평가 관리"
  ],
  "Quản lý bài kiểm tra đã công bố, điều chỉnh lịch thi và tiếp tục soạn các đề trong mục bản nháp.": [
    "Manage published tests, adjust schedules and continue editing drafts.",
    "공개 시험 관리, 일정 조정 및 초안 작성을 계속하세요."
  ],
  "Quản lý danh sách bài kiểm tra": [
    "Manage test list",
    "시험 목록 관리"
  ],
  "Loại danh sách bài kiểm tra": [
    "Test list type",
    "시험 목록 유형"
  ],
  "Đã công bố": [
    "Published",
    "공개됨"
  ],
  "Bản nháp": [
    "Drafts",
    "초안"
  ],
  "Bài kiểm tra đã công bố": [
    "Published tests",
    "공개된 시험"
  ],
  "Bản nháp bài kiểm tra": [
    "Test drafts",
    "시험 초안"
  ],
  "Các đề đã công bố cho sinh viên.": [
    "Tests published for students.",
    "학생에게 공개된 시험."
  ],
  "Các đề đang soạn, chưa công bố cho sinh viên.": [
    "Draft tests not yet published for students.",
    "학생에게 아직 공개되지 않은 시험 초안."
  ],
  "bài kiểm tra": [
    "tests",
    "시험"
  ],
  "Tìm tên bài kiểm tra...": [
    "Search test name...",
    "시험 이름 검색..."
  ],
  "Tìm tên bài kiểm tra": [
    "Search test name",
    "시험 이름 검색"
  ],
  "Đề đang soạn": [
    "Test in progress",
    "작성 중 시험"
  ],
  "Cấu trúc đề": [
    "Test structure",
    "시험 구성"
  ],
  "Thời gian & lịch thi": [
    "Duration & schedule",
    "시간 및 일정"
  ],
  "Lịch thi dự kiến": [
    "Planned exam schedule",
    "예정 시험 일정"
  ],
  "Không tìm thấy bài kiểm tra phù hợp.": [
    "No matching tests found.",
    "일치하는 시험을 찾을 수 없습니다."
  ],
  "Chưa có bài kiểm tra đã công bố.": [
    "No published tests yet.",
    "공개된 시험이 없습니다."
  ],
  "Chưa có bản nháp bài kiểm tra.": [
    "No test drafts yet.",
    "시험 초안이 없습니다."
  ],
  "Chưa công bố": [
    "Unpublished",
    "미공개"
  ],
  "câu trắc nghiệm": [
    "MCQs",
    "객관식 문항"
  ],
  "câu SQL": [
    "SQL questions",
    "SQL 문항"
  ],
  "câu tự luận": [
    "essay questions",
    "서술형 문항"
  ],
  "(ngày hôm sau)": [
    " (next day)",
    " (다음 날)"
  ],
  "Chưa xếp giờ": [
    "Time not scheduled",
    "시간 미정"
  ],
  "phút": [
    "minutes",
    "분"
  ],
  "Soạn tiếp": [
    "Continue editing",
    "계속 작성"
  ],
  "Xem lại": [
    "Review",
    "검토"
  ],
  "Chỉnh thời gian": [
    "Edit schedule",
    "일정 수정"
  ],
  "bài đã công bố": [
    "published tests",
    "공개된 시험"
  ],
  "bản nháp": [
    "drafts",
    "초안"
  ],
  "· Tổng trong tab:": [
    "· Total in tab:",
    "· 탭 합계:"
  ],
  "Phân trang bài kiểm tra": [
    "Test pagination",
    "시험 페이지 탐색"
  ],
  "Trang trước": [
    "Previous page",
    "이전 페이지"
  ],
  "LỊCH KIỂM TRA": [
    "TEST SCHEDULE",
    "시험 일정"
  ],
  "Chỉnh thời gian thi": [
    "Edit exam schedule",
    "시험 일정 수정"
  ],
  "Đóng hộp chỉnh thời gian": [
    "Close schedule dialog",
    "일정 창 닫기"
  ],
  "Ngày thi": [
    "Exam date",
    "시험 날짜"
  ],
  "Giờ bắt đầu": [
    "Start time",
    "시작 시간"
  ],
  "Thời lượng (phút)": [
    "Duration (minutes)",
    "시간 (분)"
  ],
  "Giờ kết thúc dự kiến": [
    "Expected end time",
    "예상 종료 시간"
  ],
  "· Ngày hôm sau": [
    " · Next day",
    " · 다음 날"
  ],
  "Chưa đủ thông tin": [
    "Insufficient information",
    "정보 부족"
  ],
  "Đây là lịch dự kiến. Lưu thời gian không công bố đề cho sinh viên.": [
    "This is a planned schedule. Saving it does not publish the test.",
    "예정 일정입니다. 저장해도 시험이 공개되지는 않습니다."
  ],
  "Bấm Lưu thời gian để cập nhật lịch thi.": [
    "Select Save schedule to update the exam schedule.",
    "일정 저장을 선택하여 시험 일정을 변경하세요."
  ],
  "Lưu thời gian": [
    "Save schedule",
    "일정 저장"
  ],
  "Bài kiểm tra mới": [
    "New test",
    "새 시험"
  ],
  "Ngành Công nghệ phần mềm": [
    "Software Technology major",
    "소프트웨어 기술 전공"
  ],
  "Mã đề hoặc phần thi không hợp lệ.": [
    "Invalid test ID or section.",
    "시험 ID 또는 영역이 유효하지 않습니다."
  ],
  "Truy vấn JOIN & Phân nhóm Aggregation": [
    "JOIN queries & Aggregation",
    "JOIN 쿼리 및 집계"
  ],
  "Tối ưu Window Functions & CTE": [
    "Optimizing Window Functions & CTE",
    "윈도우 함수 및 CTE 최적화"
  ],
  "Kiểm tra Cơ sở Dữ liệu Nâng cao": [
    "Advanced Database Test",
    "고급 데이터베이스 시험"
  ],
  "Ngành Hệ thống Thông tin Quản lý": [
    "Management Information Systems major",
    "경영 정보 시스템 전공"
  ],
  "Ngành Khoa học Máy tính": [
    "Computer Science major",
    "컴퓨터 과학 전공"
  ],
  "Ngành Kỹ thuật Phần mềm": [
    "Software Engineering major",
    "소프트웨어 공학 전공"
  ],
  "Câu SQL mới": [
    "New SQL question",
    "새 SQL 문항"
  ],
  "Phải giữ ít nhất một câu SQL.": [
    "Keep at least one SQL question.",
    "SQL 문항을 최소 하나 유지해야 합니다."
  ],
  "Từ khóa này đã có.": [
    "This keyword already exists.",
    "이미 있는 키워드입니다."
  ],
  "Chưa nhập nội dung SQL.": [
    "No SQL entered yet.",
    "SQL이 입력되지 않았습니다."
  ],
  "Đã sao chép SQL.": [
    "SQL copied.",
    "SQL을 복사했습니다."
  ],
  "SQL đã được chọn. Nhấn Ctrl+C để sao chép.": [
    "SQL selected. Press Ctrl+C to copy.",
    "SQL이 선택되었습니다. Ctrl+C로 복사하세요."
  ],
  "Không lưu được bản nháp SQL trong trình duyệt.": [
    "Could not save SQL draft in this browser.",
    "이 브라우저에 SQL 초안을 저장할 수 없습니다."
  ],
  "Quay lại": [
    "Back",
    "뒤로"
  ],
  "Đường dẫn": [
    "Breadcrumb",
    "탐색 경로"
  ],
  "Soạn bài kiểm tra": [
    "Edit test",
    "시험 작성"
  ],
  "Soạn đề, nhập đáp án chuẩn, thêm từ khóa rồi lưu nháp.": [
    "Write questions, reference answers and keywords, then save the draft.",
    "문제, 기준 답안 및 키워드를 작성하고 초안을 저장하세요."
  ],
  "Bạn chưa có thông báo mới.": [
    "No new notifications.",
    "새 알림이 없습니다."
  ],
  "THÔNG TIN HỌC PHẦN": [
    "COURSE INFORMATION",
    "교과목 정보"
  ],
  "TÊN BÀI KIỂM TRA": [
    "TEST NAME",
    "시험 이름"
  ],
  "NGÀNH HỌC": [
    "MAJOR",
    "전공"
  ],
  "NĂM HỌC": [
    "ACADEMIC YEAR",
    "학년도"
  ],
  "THỜI GIAN LÀM BÀI": [
    "TEST DURATION",
    "시험 시간"
  ],
  "Giảm 1 phút": [
    "Decrease by 1 minute",
    "1분 줄이기"
  ],
  "Số phút làm bài": [
    "Test duration in minutes",
    "시험 시간 (분)"
  ],
  "Tăng 1 phút": [
    "Increase by 1 minute",
    "1분 늘리기"
  ],
  "CÂU HỎI SQL": [
    "SQL QUESTIONS",
    "SQL 문항"
  ],
  "Chưa nhập tên câu hỏi": [
    "Question name not entered",
    "문항 이름 미입력"
  ],
  "ĐANG CHỌN": [
    "SELECTED",
    "선택됨"
  ],
  "Đã xong": [
    "Complete",
    "완료"
  ],
  "Chưa soạn": [
    "Not drafted",
    "미작성"
  ],
  "Thêm câu hỏi SQL": [
    "Add SQL question",
    "SQL 문항 추가"
  ],
  "CẤU TRÚC ĐIỂM THI & PHÂN BỔ CÂU HỎI": [
    "SCORING & QUESTION DISTRIBUTION",
    "배점 및 문항 구성"
  ],
  "Tổng điểm:": [
    "Total score:",
    "총점:"
  ],
  "Điểm •": [
    "Points •",
    "점수 •"
  ],
  "câu": [
    "questions",
    "문항"
  ],
  "1. TRẮC NGHIỆM": [
    "1. MULTIPLE CHOICE",
    "1. 객관식"
  ],
  "câu • Tổng": [
    "questions • Total",
    "문항 • 합계"
  ],
  "Đã lưu nháp": [
    "Draft saved",
    "초안 저장됨"
  ],
  "Chưa có nháp": [
    "No draft",
    "초안 없음"
  ],
  "2. TRUY VẤN SQL": [
    "2. SQL QUERIES",
    "2. SQL 쿼리"
  ],
  "ĐANG SOẠN": [
    "EDITING",
    "작성 중"
  ],
  "3. TỰ LUẬN CSDL": [
    "3. DATABASE ESSAY",
    "3. 데이터베이스 서술형"
  ],
  "CÂU SQL": [
    "SQL QUESTION",
    "SQL 문항"
  ],
  "Câu hỏi chưa đặt tên": [
    "Untitled question",
    "제목 없는 문항"
  ],
  "Điểm câu này": [
    "Question score",
    "문항 점수"
  ],
  "Điểm câu hỏi": [
    "Question score",
    "문항 점수"
  ],
  "MÔ TẢ YÊU CẦU ĐỀ BÀI": [
    "PROBLEM REQUIREMENTS",
    "문제 요구 사항"
  ],
  "Nhập mô tả yêu cầu đề bài...": [
    "Enter problem requirements...",
    "문제 요구 사항 입력..."
  ],
  "ĐÁP ÁN TRUY VẤN CHUẨN": [
    "REFERENCE SQL ANSWER",
    "기준 SQL 답안"
  ],
  "Chưa kết nối Docker Sandbox để chạy SQL.": [
    "Docker Sandbox is not connected to run SQL.",
    "SQL 실행용 Docker Sandbox가 연결되지 않았습니다."
  ],
  "Chạy thử Sandbox": [
    "Run Sandbox",
    "Sandbox 실행"
  ],
  "Nhập đáp án truy vấn SQL...": [
    "Enter SQL reference answer...",
    "SQL 기준 답안 입력..."
  ],
  "TỪ KHÓA BẮT BUỘC ĐỐI CHIẾU TRỌNG TÂM": [
    "REQUIRED REFERENCE KEYWORDS",
    "필수 대조 키워드"
  ],
  "từ khóa": [
    " keywords",
    " 키워드"
  ],
  "Thêm từ khóa": [
    "Add keyword",
    "키워드 추가"
  ],
  "Ví dụ: INNER JOIN": [
    "Example: INNER JOIN",
    "예: INNER JOIN"
  ],
  "Từ khóa SQL": [
    "SQL keyword",
    "SQL 키워드"
  ],
  "Thêm": [
    "Add",
    "추가"
  ],
  "Xem trước giao diện sinh viên": [
    "Preview student interface",
    "학생 화면 미리 보기"
  ],
  "Đã lưu nháp SQL trong trình duyệt.": [
    "SQL draft saved in this browser.",
    "SQL 초안을 이 브라우저에 저장했습니다."
  ],
  "Lưu bản nháp": [
    "Save draft",
    "초안 저장"
  ],
  "Về Trắc nghiệm": [
    "Back to MCQ",
    "객관식으로 돌아가기"
  ],
  "Câu trước": [
    "Previous question",
    "이전 문항"
  ],
  "Sang Tự luận": [
    "Go to Essay",
    "서술형으로 이동"
  ],
  "Câu tiếp theo": [
    "Next question",
    "다음 문항"
  ],
  "Chuyển sang phần thi Tự luận": [
    "Go to Essay section",
    "서술형 영역으로 이동"
  ],
  "Sửa tên câu hỏi SQL": [
    "Edit SQL question name",
    "SQL 문항 이름 수정"
  ],
  "Tên câu hỏi": [
    "Question name",
    "문항 이름"
  ],
  "Nhập tên câu hỏi...": [
    "Enter question name...",
    "문항 이름 입력..."
  ],
  "Cập nhật": [
    "Update",
    "업데이트"
  ],
  "Câu SQL": [
    "SQL question",
    "SQL 문항"
  ],
  "Chưa nhập mô tả đề bài.": [
    "Problem description not entered.",
    "문제 설명이 입력되지 않았습니다."
  ],
  "Bài làm SQL": [
    "SQL answer",
    "SQL 답안"
  ],
  "Sinh viên nhập truy vấn tại đây...": [
    "Students enter queries here...",
    "여기에 쿼리 입력..."
  ],
  "Đóng": [
    "Close",
    "닫기"
  ],
  "Không tìm thấy bản nháp của đề.": [
    "Test draft not found.",
    "시험 초안을 찾을 수 없습니다."
  ],
  "Kiến trúc Sharding & Phân tán CSDL": [
    "Sharding & Distributed Database Architecture",
    "샤딩 및 분산 데이터베이스 구조"
  ],
  "So sánh Partitioning và Sharding": [
    "Compare Partitioning and Sharding",
    "파티셔닝과 샤딩 비교"
  ],
  "Chọn Shard Key và xử lý Data Skew": [
    "Choose Shard Key and handle Data Skew",
    "샤드 키 선택 및 데이터 편중 처리"
  ],
  "Phân tích giao dịch phân tán": [
    "Analyze distributed transactions",
    "분산 트랜잭션 분석"
  ],
  "Cần giữ ít nhất một câu tự luận.": [
    "Keep at least one essay question.",
    "서술형 문항을 최소 하나 유지해야 합니다."
  ],
  "Không lưu được bản nháp tự luận trong trình duyệt.": [
    "Could not save essay draft in this browser.",
    "이 브라우저에 서술형 초안을 저장할 수 없습니다."
  ],
  "Vui lòng nhập tên bài kiểm tra.": [
    "Please enter the test name.",
    "시험 이름을 입력하세요."
  ],
  "Chưa lưu được bộ đề.": [
    "Could not save the test.",
    "시험을 저장할 수 없습니다."
  ],
  "Giảm thời gian": [
    "Decrease duration",
    "시간 줄이기"
  ],
  "Tăng thời gian": [
    "Increase duration",
    "시간 늘리기"
  ],
  "CÂU TỰ LUẬN": [
    "ESSAY QUESTION",
    "서술형 문항"
  ],
  "ĐÃ XONG": [
    "COMPLETE",
    "완료"
  ],
  "BẢN NHÁP": [
    "DRAFT",
    "초안"
  ],
  "Thêm câu hỏi tự luận": [
    "Add essay question",
    "서술형 문항 추가"
  ],
  "CÂU": [
    "QUESTION",
    "문항"
  ],
  "Chưa đặt tên câu hỏi": [
    "Untitled question",
    "제목 없는 문항"
  ],
  "Điểm số:": [
    "Score:",
    "점수:"
  ],
  "ĐỀ BÀI TỰ LUẬN": [
    "ESSAY PROMPT",
    "서술형 문제"
  ],
  "Nhập đề bài tự luận...": [
    "Enter essay prompt...",
    "서술형 문제 입력..."
  ],
  "ĐÁP ÁN MẪU & HƯỚNG DẪN CHẤM": [
    "SAMPLE ANSWER & GRADING GUIDE",
    "예시 답안 및 채점 지침"
  ],
  "Nhập đáp án mẫu và hướng dẫn chấm...": [
    "Enter sample answer and grading guide...",
    "예시 답안 및 채점 지침 입력..."
  ],
  "TIÊU CHÍ CHẤM ĐIỂM": [
    "GRADING CRITERIA",
    "채점 기준"
  ],
  "Thêm tiêu chí": [
    "Add criterion",
    "기준 추가"
  ],
  "Chưa có tiêu chí. Bấm “Thêm tiêu chí” để bổ sung.": [
    "No criteria yet. Select “Add criterion”.",
    "기준이 없습니다. “기준 추가”를 선택하세요."
  ],
  "Nhập tên tiêu chí...": [
    "Enter criterion name...",
    "기준 이름 입력..."
  ],
  "Tên tiêu chí": [
    "Criterion name",
    "기준 이름"
  ],
  "Điểm tiêu chí": [
    "Criterion score",
    "기준 점수"
  ],
  "Hoàn tất sửa tiêu chí": [
    "Finish editing criterion",
    "기준 수정 완료"
  ],
  "Sửa tiêu chí": [
    "Edit criterion",
    "기준 수정"
  ],
  "Xóa tiêu chí": [
    "Delete criterion",
    "기준 삭제"
  ],
  "Điểm câu hỏi bằng tổng điểm các tiêu chí. Tổng điểm đề được tự cộng từ trắc nghiệm, SQL và tự luận.": [
    "Question score equals the sum of criterion scores. Test total adds MCQ, SQL and essay scores.",
    "문항 점수는 기준 점수의 합이며 총점은 객관식, SQL 및 서술형 점수의 합입니다."
  ],
  "Đã lưu bản nháp tự luận trong trình duyệt.": [
    "Essay draft saved in this browser.",
    "서술형 초안을 이 브라우저에 저장했습니다."
  ],
  "Bài trước (SQL)": [
    "Previous section (SQL)",
    "이전 영역 (SQL)"
  ],
  "Lưu bài": [
    "Save test",
    "시험 저장"
  ],
  "Chỉnh sửa tên câu hỏi": [
    "Edit question name",
    "문항 이름 수정"
  ],
  "Câu": [
    "Question",
    "문항"
  ],
  "Chưa nhập đề bài.": [
    "Problem statement not entered.",
    "문제가 입력되지 않았습니다."
  ],
  "Bài làm của sinh viên": [
    "Student answer",
    "학생 답안"
  ],
  "Nhập câu trả lời...": [
    "Enter answer...",
    "답안 입력..."
  ],
  "Khái niệm ACID & Giao dịch CSDL": [
    "ACID & Database Transactions",
    "ACID 및 데이터베이스 트랜잭션"
  ],
  "Khóa ngoại & Ràng buộc toàn vẹn cơ sở dữ liệu": [
    "Foreign Keys & Database Integrity Constraints",
    "외래 키 및 데이터베이스 무결성 제약 조건"
  ],
  "Index B-Tree và tối ưu truy vấn": [
    "B-Tree Indexes and Query Optimization",
    "B-Tree 인덱스 및 쿼리 최적화"
  ],
  "Mức độ cô lập Isolation Levels": [
    "Transaction Isolation Levels",
    "트랜잭션 격리 수준"
  ],
  "Tối ưu hóa cây thực thi Query Plan": [
    "Query Plan Optimization",
    "쿼리 실행 계획 최적화"
  ],
  "Khóa bi quan vs Lạc quan": [
    "Pessimistic vs Optimistic Locking",
    "비관적 및 낙관적 잠금"
  ],
  "Kỹ thuật Sharding & Replication": [
    "Sharding & Replication Techniques",
    "샤딩 및 복제 기술"
  ],
  "Nguyên lý Chuẩn hóa BCNF & 3NF": [
    "BCNF & 3NF Normalization Principles",
    "BCNF 및 3NF 정규화 원리"
  ],
  "View và Materialized View": [
    "Views and Materialized Views",
    "뷰 및 구체화된 뷰"
  ],
  "Deadlock & Giải thuật phát hiện": [
    "Deadlocks & Detection Algorithms",
    "교착 상태 및 탐지 알고리즘"
  ],
  "Câu hỏi mới": [
    "New question",
    "새 문항"
  ],
  "Phải giữ ít nhất một câu hỏi.": [
    "Keep at least one question.",
    "문항을 최소 하나 유지해야 합니다."
  ],
  "Tối đa 26 phương án.": [
    "Maximum 26 options.",
    "선택지는 최대 26개입니다."
  ],
  "Phải giữ ít nhất hai phương án.": [
    "Keep at least two options.",
    "선택지를 최소 두 개 유지해야 합니다."
  ],
  "Không lưu được bản nháp trong trình duyệt.": [
    "Could not save draft in this browser.",
    "이 브라우저에 초안을 저장할 수 없습니다."
  ],
  "Quản lý đề thi": [
    "Test editor",
    "시험 편집"
  ],
  "Soạn câu hỏi, chọn đáp án đúng rồi lưu bản nháp.": [
    "Write questions, select correct answers and save the draft.",
    "문항 작성, 정답 선택 후 초안을 저장하세요."
  ],
  "CÂU HỎI TRẮC NGHIỆM": [
    "MULTIPLE CHOICE QUESTIONS",
    "객관식 문항"
  ],
  "Chưa đặt tên": [
    "Untitled",
    "제목 없음"
  ],
  "Đã soạn": [
    "Drafted",
    "작성됨"
  ],
  "Chưa hoàn tất": [
    "Incomplete",
    "미완료"
  ],
  "Thêm câu hỏi trắc nghiệm": [
    "Add multiple choice question",
    "객관식 문항 추가"
  ],
  "CÂU HỎI": [
    "QUESTION",
    "문항"
  ],
  "Nhập nội dung câu hỏi...": [
    "Enter question content...",
    "문항 내용 입력..."
  ],
  "PHƯƠNG ÁN LỰA CHỌN (CHỌN 1 ĐÁP ÁN ĐÚNG)": [
    "ANSWER OPTIONS (SELECT ONE CORRECT ANSWER)",
    "선택지 (정답 하나 선택)"
  ],
  "phương án": [
    "options",
    "선택지"
  ],
  "Chưa nhập phương án": [
    "Option not entered",
    "선택지 미입력"
  ],
  "Đáp án đúng": [
    "Correct answer",
    "정답"
  ],
  "Chọn đúng": [
    "Mark correct",
    "정답 표시"
  ],
  "Hoàn tất sửa": [
    "Finish editing",
    "수정 완료"
  ],
  "Sửa phương án": [
    "Edit option",
    "선택지 수정"
  ],
  "Thêm phương án lựa chọn": [
    "Add answer option",
    "선택지 추가"
  ],
  "GIẢI THÍCH ĐÁP ÁN & ĐỐI CHIẾU KIẾN THỨC": [
    "ANSWER EXPLANATION & KNOWLEDGE REFERENCE",
    "정답 해설 및 지식 대조"
  ],
  "Nhập giải thích đáp án và nội dung đối chiếu kiến thức...": [
    "Enter answer explanation and knowledge reference...",
    "정답 해설 및 지식 대조 내용 입력..."
  ],
  "Đã lưu bản nháp trong trình duyệt.": [
    "Draft saved in this browser.",
    "초안을 이 브라우저에 저장했습니다."
  ],
  "Chuyển sang phần thi SQL": [
    "Go to SQL section",
    "SQL 영역으로 이동"
  ],
  "Sửa tên câu hỏi": [
    "Edit question name",
    "문항 이름 수정"
  ],
  "Chưa nhập nội dung câu hỏi.": [
    "Question content not entered.",
    "문항 내용이 입력되지 않았습니다."
  ],
  "Vui lòng nhập chủ đề câu hỏi.": [
    "Please enter question topic.",
    "문항 주제를 입력하세요."
  ],
  "Vui lòng nhập đề bài.": [
    "Please enter problem statement.",
    "문제를 입력하세요."
  ],
  "Điểm câu hỏi phải lớn hơn 0 và không vượt quá 10.": [
    "Question score must be greater than 0 and at most 10.",
    "문항 점수는 0보다 크고 10 이하여야 합니다."
  ],
  "Cần ít nhất hai phương án và không để trống nội dung.": [
    "At least two nonempty options are required.",
    "내용이 있는 선택지가 최소 두 개 필요합니다."
  ],
  "Vui lòng chọn đáp án đúng.": [
    "Please select the correct answer.",
    "정답을 선택하세요."
  ],
  "Vui lòng nhập đáp án tham khảo.": [
    "Please enter reference answer.",
    "참고 답안을 입력하세요."
  ],
  "Tiêu chí chấm điểm": [
    "Grading criteria",
    "채점 기준"
  ],
  "Từ khóa bắt buộc (Keywords bắt buộc trong câu lệnh SQL để chấm điểm):": [
    "Required keywords (for SQL grading):",
    "필수 키워드 (SQL 채점용):"
  ],
  "Từ khóa bắt buộc (Keywords để đối chiếu nội dung bài làm):": [
    "Required keywords (for answer comparison):",
    "필수 키워드 (답안 대조용):"
  ],
  "⊕ Thêm từ khóa bắt buộc": [
    "⊕ Add required keyword",
    "⊕ 필수 키워드 추가"
  ],
  "Chưa có từ khóa.": [
    "No keywords yet.",
    "키워드가 없습니다."
  ],
  "Từ khóa mới": [
    "New keyword",
    "새 키워드"
  ],
  "Nhập từ khóa...": [
    "Enter keyword...",
    "키워드 입력..."
  ],
  "Các từ khóa dùng để đối chiếu cú pháp và nội dung truy vấn khi chấm bài.": [
    "Keywords are used to compare query syntax and content during grading.",
    "채점 시 키워드로 쿼리 구문과 내용을 대조합니다."
  ],
  "Các từ khóa dùng để đối chiếu các ý cần có trong bài tự luận.": [
    "Keywords are used to check required ideas in essays.",
    "키워드로 서술형 답안의 필수 내용을 확인합니다."
  ],
  "Dữ liệu lưu trên trình duyệt không hợp lệ.": [
    "Invalid browser storage data.",
    "브라우저 저장 데이터가 유효하지 않습니다."
  ],
  "Không thể lưu thay đổi.": [
    "Could not save changes.",
    "변경 사항을 저장할 수 없습니다."
  ],
  "Có câu hỏi chưa hoàn thiện. Vui lòng hoàn thiện các câu trước khi lưu.": [
    "Some questions are incomplete. Complete them before saving.",
    "일부 문항이 미완료입니다. 저장 전에 완성하세요."
  ],
  "Đã lưu thay đổi trên trình duyệt.": [
    "Changes saved in this browser.",
    "변경 사항을 이 브라우저에 저장했습니다."
  ],
  "Không thể lưu câu hỏi.": [
    "Could not save question.",
    "문항을 저장할 수 없습니다."
  ],
  "Đã lưu tất cả thay đổi trên trình duyệt.": [
    "All changes saved in this browser.",
    "모든 변경 사항을 이 브라우저에 저장했습니다."
  ],
  "Câu hỏi mới chưa có bản lưu để khôi phục.": [
    "No saved version of this new question to restore.",
    "새 문항에 복원할 저장본이 없습니다."
  ],
  "Đã khôi phục câu hỏi về bản lưu gần nhất.": [
    "Question restored to its latest saved version.",
    "문항을 최근 저장본으로 복원했습니다."
  ],
  "Có thay đổi chưa lưu. Bạn muốn quay lại và bỏ các thay đổi này?": [
    "There are unsaved changes. Go back and discard them?",
    "저장하지 않은 변경 사항이 있습니다. 취소하고 돌아갈까요?"
  ],
  "Chưa xếp lịch": [
    "Not scheduled",
    "일정 미정"
  ],
  "(+1 ngày)": [
    " (+1 day)",
    " (+1일)"
  ],
  "Xem lại bài kiểm tra": [
    "Review test",
    "시험 검토"
  ],
  "Lưu tất cả thay đổi": [
    "Save all changes",
    "모든 변경 사항 저장"
  ],
  "Tổng:": [
    "Total:",
    "합계:"
  ],
  "câu hỏi (": [
    "questions (",
    "문항 ("
  ],
  "điểm)": [
    "points)",
    "점)"
  ],
  "Thời gian:": [
    "Duration:",
    "시간:"
  ],
  "Lịch thi:": [
    "Schedule:",
    "시험 일정:"
  ],
  "Mục lục câu hỏi": [
    "Question index",
    "문항 목록"
  ],
  "câu ·": [
    "questions ·",
    "문항 ·"
  ],
  "Loại câu hỏi": [
    "Question type",
    "문항 유형"
  ],
  "Tất cả": [
    "All",
    "전체"
  ],
  "Thêm câu hỏi mới": [
    "Add new question",
    "새 문항 추가"
  ],
  "PHẦN:": [
    "SECTION:",
    "영역:"
  ],
  "CÂU)": [
    "QUESTIONS)",
    "문항)"
  ],
  "Chưa nhập chủ đề": [
    "Topic not entered",
    "주제 미입력"
  ],
  "Chưa nhập đề bài": [
    "Problem not entered",
    "문제 미입력"
  ],
  "Chưa lưu": [
    "Unsaved",
    "미저장"
  ],
  "Đã lưu": [
    "Saved",
    "저장됨"
  ],
  "Chưa có câu hỏi thuộc loại này.": [
    "No questions of this type yet.",
    "이 유형의 문항이 없습니다."
  ],
  "Nội dung câu hỏi": [
    "Question content",
    "문항 내용"
  ],
  "PHẦN ·": [
    "SECTION ·",
    "영역 ·"
  ],
  "CÂU HỎI MỚI": [
    "NEW QUESTION",
    "새 문항"
  ],
  "Xóa câu": [
    "Delete question",
    "문항 삭제"
  ],
  "CHỦ ĐỀ CÂU HỎI": [
    "QUESTION TOPIC",
    "문항 주제"
  ],
  "Chủ đề câu hỏi": [
    "Question topic",
    "문항 주제"
  ],
  "ĐIỂM SỐ CÂU HỎI": [
    "QUESTION SCORE",
    "문항 점수"
  ],
  "Điểm số câu hỏi": [
    "Question score",
    "문항 점수"
  ],
  "Đề bài câu hỏi (Problem Statement):": [
    "Problem statement:",
    "문제:"
  ],
  "Đề bài:": [
    "Problem:",
    "문제:"
  ],
  "Phương án trả lời (Chọn radio để đánh dấu đáp án đúng):": [
    "Answer options (select radio to mark the correct answer):",
    "선택지 (라디오 버튼으로 정답 표시):"
  ],
  "Thêm phương án": [
    "Add option",
    "선택지 추가"
  ],
  "ĐÁP ÁN ĐÚNG": [
    "CORRECT ANSWER",
    "정답"
  ],
  "▣ Thử nghiệm trên Sandbox": [
    "▣ Test in Sandbox",
    "▣ Sandbox 테스트"
  ],
  "Chức năng chạy truy vấn sẽ hoạt động khi kết nối SQL Sandbox.": [
    "Query execution requires a connected SQL Sandbox.",
    "쿼리 실행에는 SQL Sandbox 연결이 필요합니다."
  ],
  "▷ Chạy thử nghiệm trên Sandbox": [
    "▷ Run in Sandbox",
    "▷ Sandbox 실행"
  ],
  "Truy vấn đáp án SQL": [
    "SQL reference query",
    "SQL 기준 쿼리"
  ],
  "▤ Tiêu chuẩn chấm điểm": [
    "▤ Grading standard",
    "▤ 채점 기준"
  ],
  "Tiêu chí mới": [
    "New criterion",
    "새 기준"
  ],
  "⊕ Thêm tiêu chí chấm": [
    "⊕ Add grading criterion",
    "⊕ 채점 기준 추가"
  ],
  "Nội dung cần đạt ở tiêu chí này...": [
    "Required content for this criterion...",
    "이 기준의 필수 내용..."
  ],
  "▣ Đáp án mẫu / Hướng dẫn chấm": [
    "▣ Sample answer / Grading guide",
    "▣ 예시 답안 / 채점 지침"
  ],
  "Tổng tiêu chí:": [
    "Criteria total:",
    "기준 합계:"
  ],
  "Đáp án mẫu hoặc hướng dẫn chấm tự luận": [
    "Sample answer or essay grading guide",
    "예시 답안 또는 서술형 채점 지침"
  ],
  "Câu trước (": [
    "Previous question (",
    "이전 문항 ("
  ],
  "Lưu thay đổi câu này": [
    "Save this question",
    "이 문항 저장"
  ],
  "Lưu & sang câu tiếp theo": [
    "Save & next question",
    "저장 및 다음 문항"
  ],
  "Chọn loại câu hỏi khác hoặc thêm câu hỏi mới.": [
    "Select another question type or add a new question.",
    "다른 문항 유형을 선택하거나 새 문항을 추가하세요."
  ],
  "Xóa câu hỏi?": [
    "Delete question?",
    "문항을 삭제할까요?"
  ],
  "Câu hỏi sẽ được bỏ khỏi đề sau khi bạn lưu thay đổi.": [
    "The question will be removed from the test after saving changes.",
    "변경 사항 저장 후 시험에서 문항이 삭제됩니다."
  ],
  "Bảng xếp hạng": [
    "Ranking",
    "순위"
  ],
  "Bảng xếp hạng sinh viên có thể cuộn": [
    "Scrollable student ranking",
    "스크롤 가능한 학생 순위"
  ],
  "HẠNG": [
    "RANK",
    "순위"
  ],
  "Tối đa 4 điểm": [
    "Maximum 4 points",
    "최대 4점"
  ],
  "Tối đa 3 điểm": [
    "Maximum 3 points",
    "최대 3점"
  ],
  "TỰ LUẬN": [
    "ESSAY",
    "서술형"
  ],
  "Thang điểm 10": [
    "10-point scale",
    "10점 만점"
  ],
  "Chưa có tên": [
    "Unnamed",
    "이름 없음"
  ],
  "Chưa có dữ liệu sinh viên.": [
    "No student data available.",
    "학생 데이터가 없습니다."
  ],
  "Em đề xuất kết hợp tối ưu truy vấn tại từng node với phân phối dữ liệu giữa các node.": [
    "I propose optimizing queries on each node and distributing data across nodes.",
    "각 노드의 쿼리 최적화와 노드 간 데이터 분산을 제안합니다."
  ],
  "Với truy vấn lọc theo tenant và thời gian, cần xem xét chỉ mục ghép trên TenantID và CreatedAt. Thứ tự cột trong chỉ mục phải phù hợp điều kiện lọc và được kiểm tra bằng execution plan.": [
    "For tenant and time filters, consider a composite index on TenantID and CreatedAt. Match column order to filters and verify the execution plan.",
    "테넌트와 시간 필터에는 TenantID와 CreatedAt 복합 인덱스를 고려하고 열 순서를 조건에 맞춰 실행 계획으로 검증해야 합니다."
  ],
  "Dữ liệu có thể phân mảnh ngang theo TenantID. Khi một tenant có lượng dữ liệu lớn, cần theo dõi tải và điều chỉnh cách phân phối để hạn chế hotspot.": [
    "Data can be horizontally partitioned by TenantID. Monitor large tenants and adjust distribution to prevent hotspots.",
    "TenantID로 수평 분할할 수 있습니다. 대규모 테넌트의 부하를 추적하고 분산 방식을 조정하여 핫스폿을 줄여야 합니다."
  ],
  "Các giao dịch giữa nhiều dịch vụ được phối hợp bằng Saga. Bài làm chưa giải thích rõ thao tác bù khi một bước thất bại.": [
    "Saga coordinates transactions across services. The answer does not clearly explain compensation when a step fails.",
    "Saga가 서비스 간 트랜잭션을 조정합니다. 답안에 단계 실패 시 보상 작업 설명이 부족합니다."
  ],
  "Các giao dịch giữa nhiều dịch vụ có thể phối hợp bằng Saga. Mỗi bước cần có thao tác bù, xử lý retry và bảo đảm idempotency.": [
    "Saga can coordinate cross-service transactions. Each step needs compensation, retries and idempotency.",
    "Saga로 서비스 간 트랜잭션을 조정할 수 있습니다. 각 단계에 보상 작업, 재시도 및 멱등성이 필요합니다."
  ],
  "Trình bày được hướng lựa chọn chỉ mục và phân phối dữ liệu theo tenant.": [
    "Explains index selection and data distribution by tenant.",
    "인덱스 선택과 테넌트별 데이터 분산을 설명합니다."
  ],
  "Cần kiểm tra phần giao dịch bù và xử lý khi một bước thất bại.": [
    "Review compensating transactions and step failure handling.",
    "보상 트랜잭션 및 단계 실패 처리를 검토해야 합니다."
  ],
  "Cần làm rõ điều kiện áp dụng và kiểm chứng bằng execution plan.": [
    "Clarify applicability and verify with an execution plan.",
    "적용 조건을 명확히 하고 실행 계획으로 검증해야 합니다."
  ],
  "Viết truy vấn tính tổng chi tiêu của từng khách hàng": [
    "Write a query for each customer's total spending",
    "고객별 총 지출을 계산하는 쿼리를 작성하세요"
  ],
  "theo quý trong năm 2023. Sử dụng CTE và DENSE_RANK()": [
    " by quarter in 2023. Use CTE and DENSE_RANK()",
    " 2023년 분기별로 계산하고 CTE 및 DENSE_RANK()를 사용하세요"
  ],
  "để xếp hạng khách hàng theo tổng chi tiêu giảm dần": [
    "to rank customers by descending total spending",
    "고객을 총 지출 내림차순으로 순위화하세요"
  ],
  "trong từng quý.": [
    "in each quarter.",
    "각 분기 내에서."
  ],
  "Phân tích giải pháp mở rộng quy mô bằng": [
    "Analyze scaling solutions using",
    "다음을 이용한 확장 방안을 분석하세요:"
  ],
  "Horizontal Partitioning và Sharding cho hệ thống": [
    "Horizontal Partitioning and Sharding for an",
    "수평 파티셔닝과 샤딩, 대상 시스템:"
  ],
  "thương mại điện tử có 50 triệu người dùng.": [
    "e-commerce system with 50 million users.",
    "사용자 5천만 명의 전자상거래 시스템."
  ],
  "Đề xuất chiến lược chọn Shard Key, xử lý Data Skew": [
    "Propose Shard Key selection and Data Skew handling",
    "샤드 키 선택 및 데이터 편중 처리 전략을 제안하세요"
  ],
  "và đảm bảo giao dịch phân tán bằng": [
    "and ensure distributed transactions using",
    "다음을 이용해 분산 트랜잭션을 보장하세요:"
  ],
  "Two-Phase Commit hoặc Saga.": [
    "Two-Phase Commit or Saga.",
    "2단계 커밋 또는 Saga."
  ],
  "1. So sánh Partitioning và Sharding:": [
    "1. Compare Partitioning and Sharding:",
    "1. 파티셔닝과 샤딩 비교:"
  ],
  "Partitioning chia dữ liệu thành các phần; Sharding": [
    "Partitioning divides data into parts; Sharding",
    "파티셔닝은 데이터를 분할하고 샤딩은"
  ],
  "phân phối dữ liệu trên nhiều máy chủ để mở rộng.": [
    "distributes data across servers to scale.",
    "확장을 위해 여러 서버에 데이터를 분산합니다."
  ],
  "2. Chọn Shard Key:": [
    "2. Select Shard Key:",
    "2. 샤드 키 선택:"
  ],
  "Chọn theo mẫu truy vấn và phân bố dữ liệu.": [
    "Choose based on query patterns and data distribution.",
    "쿼리 패턴과 데이터 분포에 따라 선택합니다."
  ],
  "Có thể dùng User_ID, Virtual Shards hoặc Salting": [
    "Use User_ID, Virtual Shards or Salting",
    "User_ID, 가상 샤드 또는 솔팅을 사용할 수 있습니다"
  ],
  "để hạn chế dữ liệu phân bố không đều.": [
    "to reduce uneven data distribution.",
    "불균등한 데이터 분포를 줄이기 위해."
  ],
  "3. Giao dịch phân tán:": [
    "3. Distributed transactions:",
    "3. 분산 트랜잭션:"
  ],
  "Phân tích ưu nhược điểm của Two-Phase Commit": [
    "Analyze pros and cons of Two-Phase Commit",
    "2단계 커밋의 장단점을 분석하세요"
  ],
  "và Saga; lựa chọn theo yêu cầu nhất quán": [
    "and Saga; choose based on consistency requirements",
    "Saga와 비교하여 일관성 요구에 따라 선택하세요"
  ],
  "và khả năng chịu lỗi.": [
    "and fault tolerance.",
    "내결함성도 고려하세요."
  ],
  "Phần trắc nghiệm chưa soạn đủ hoặc điểm câu": [
    "MCQ section is incomplete or question scores are",
    "객관식 영역이 미완료이거나 문항 점수가"
  ],
  "không hợp lệ. Quay lại TN để kiểm tra.": [
    "invalid. Return to MCQ to check.",
    "유효하지 않습니다. 객관식으로 돌아가 확인하세요."
  ],
  "Phần SQL chưa soạn đủ hoặc điểm câu không hợp lệ.": [
    "SQL section is incomplete or question scores are invalid.",
    "SQL 영역이 미완료이거나 문항 점수가 유효하지 않습니다."
  ],
  "Quay lại SQL để kiểm tra.": [
    "Return to SQL to check.",
    "SQL로 돌아가 확인하세요."
  ],
  "Nhập đủ tên, đề bài, đáp án mẫu và tiêu chí": [
    "Enter the name, prompt, sample answer and criteria",
    "이름, 문제, 예시 답안 및 기준을 입력하세요"
  ],
  "có điểm lớn hơn 0 cho từng câu tự luận.": [
    "with scores greater than 0 for each essay question.",
    "각 서술형 문항 점수는 0보다 커야 합니다."
  ],
  "Bạn đã hoàn tất đề thi và muốn lưu rồi": [
    "Have you finished the test and want to save and",
    "시험 작성을 마치고 저장한 후"
  ],
  "quay lại danh sách chưa?": [
    "return to the list?",
    "목록으로 돌아갈까요?"
  ],
  "OK: Lưu bài và thoát.": [
    "OK: Save and exit.",
    "확인: 저장 후 종료."
  ],
  "Hủy: Tiếp tục chỉnh sửa.": [
    "Cancel: Continue editing.",
    "취소: 계속 수정."
  ],
  "Soạn đề, đáp án mẫu và tiêu chí.": [
    "Write questions, sample answers and criteria.",
    "문제, 예시 답안 및 기준을 작성하세요."
  ],
  "Điểm câu hỏi bằng tổng điểm các tiêu chí.": [
    "Question score equals the sum of criterion scores.",
    "문항 점수는 기준 점수의 합입니다."
  ],
  "Trong cơ sở dữ liệu quan hệ, cơ chế nào thiết lập": [
    "In a relational database, which mechanism establishes",
    "관계형 데이터베이스에서 어떤 기능이 다음을 설정합니까:"
  ],
  "ràng buộc toàn vẹn tham chiếu giữa bảng cha và bảng con?": [
    "referential integrity between parent and child tables?",
    "부모 테이블과 자식 테이블 간 참조 무결성?"
  ],
  "Unique Index độc lập": [
    "Standalone Unique Index",
    "독립 고유 인덱스"
  ],
  "Check Constraint độc lập": [
    "Standalone Check Constraint",
    "독립 CHECK 제약 조건"
  ],
  "Khóa ngoại thiết lập ràng buộc toàn vẹn tham chiếu": [
    "A foreign key establishes referential integrity",
    "외래 키는 참조 무결성을 설정합니다"
  ],
  "giữa hai bảng. Quy tắc ON DELETE CASCADE có thể": [
    " between two tables. ON DELETE CASCADE can",
    " 두 테이블 사이에. ON DELETE CASCADE는"
  ],
  "tự động xóa các bản ghi con khi bản ghi cha bị xóa.": [
    " automatically delete child records when the parent is deleted.",
    " 부모 레코드 삭제 시 자식 레코드를 자동 삭제할 수 있습니다."
  ],
  "Lý thuyết chuẩn hóa (1NF)": [
    "Normalization theory (1NF)",
    "정규화 이론 (1NF)"
  ],
  "Một quan hệ đạt chuẩn 1NF khi thỏa mãn điều kiện nào?": [
    "Which condition makes a relation satisfy 1NF?",
    "관계가 1NF를 만족하는 조건은 무엇입니까?"
  ],
  "Mọi thuộc tính không khóa phụ thuộc đầy đủ vào khóa chính.": [
    "All non-key attributes fully depend on the primary key.",
    "모든 비키 속성이 기본 키에 완전 종속됩니다."
  ],
  "Mỗi ô chứa một giá trị nguyên tố, không chứa nhóm lặp.": [
    "Each cell has an atomic value with no repeating groups.",
    "각 셀은 원자 값을 가지며 반복 그룹이 없습니다."
  ],
  "Không có phụ thuộc bắc cầu giữa các thuộc tính không khóa.": [
    "No transitive dependencies among non-key attributes.",
    "비키 속성 간 이행 종속성이 없습니다."
  ],
  "Mọi định thức đều là khóa ứng viên.": [
    "Every determinant is a candidate key.",
    "모든 결정자가 후보 키입니다."
  ],
  "Xác định dạng chuẩn": [
    "Identify normal form",
    "정규형 판별"
  ],
  "Quan hệ đã đạt 1NF và mọi thuộc tính không khóa phụ thuộc đầy đủ vào toàn bộ khóa chính đạt tối thiểu dạng chuẩn nào?": [
    "A relation in 1NF whose non-key attributes fully depend on the entire primary key achieves which minimum normal form?",
    "1NF이며 모든 비키 속성이 전체 기본 키에 완전 종속되는 관계의 최소 정규형은 무엇입니까?"
  ],
  "Thuật toán Tableau": [
    "Tableau algorithm",
    "Tableau 알고리즘"
  ],
  "Thuật toán Tableau thường được sử dụng để kiểm tra tính chất nào của phép phân rã quan hệ?": [
    "Which property of relational decomposition does the Tableau algorithm usually test?",
    "Tableau 알고리즘은 관계 분해의 어떤 속성을 검사합니까?"
  ],
  "Số lượng chỉ mục": [
    "Number of indexes",
    "인덱스 수"
  ],
  "Kết nối không mất mát": [
    "Lossless join",
    "무손실 조인"
  ],
  "Thời gian thực thi": [
    "Execution time",
    "실행 시간"
  ],
  "Dung lượng lưu trữ": [
    "Storage capacity",
    "저장 용량"
  ],
  "Tính toàn vẹn": [
    "Integrity",
    "무결성"
  ],
  "Ràng buộc nào đảm bảo mỗi bản ghi có một định danh duy nhất và không NULL?": [
    "Which constraint ensures each record has a unique, non-NULL identifier?",
    "각 레코드의 고유하고 NULL이 아닌 식별자를 보장하는 제약 조건은 무엇입니까?"
  ],
  "Chuẩn BCNF": [
    "BCNF normal form",
    "BCNF 정규형"
  ],
  "Quan hệ đạt BCNF khi với mọi phụ thuộc hàm không tầm thường X → Y, X là gì?": [
    "For every nontrivial functional dependency X → Y in BCNF, what must X be?",
    "BCNF의 모든 비자명 함수 종속 X → Y에서 X는 무엇이어야 합니까?"
  ],
  "Thuộc tính không khóa": [
    "Non-key attribute",
    "비키 속성"
  ],
  "Siêu khóa": [
    "Superkey",
    "슈퍼 키"
  ],
  "Khóa ngoại": [
    "Foreign key",
    "외래 키"
  ],
  "Tập rỗng": [
    "Empty set",
    "공집합"
  ],
  "Phụ thuộc hàm X → Y có ý nghĩa gì?": [
    "What does functional dependency X → Y mean?",
    "함수 종속 X → Y는 무엇을 의미합니까?"
  ],
  "Một giá trị X xác định duy nhất giá trị Y.": [
    "An X value uniquely determines Y.",
    "X 값이 Y 값을 유일하게 결정합니다."
  ],
  "Y luôn là khóa chính.": [
    "Y is always the primary key.",
    "Y는 항상 기본 키입니다."
  ],
  "X và Y phải có cùng kiểu dữ liệu.": [
    "X and Y must have the same data type.",
    "X와 Y는 같은 데이터 형식이어야 합니다."
  ],
  "X phải là khóa ngoại.": [
    "X must be a foreign key.",
    "X는 외래 키여야 합니다."
  ],
  "INNER JOIN trả về những dòng nào?": [
    "Which rows does INNER JOIN return?",
    "INNER JOIN은 어떤 행을 반환합니까?"
  ],
  "Tất cả dòng bên trái": [
    "All left-hand rows",
    "모든 왼쪽 행"
  ],
  "Các dòng khớp điều kiện nối": [
    "Rows matching the join condition",
    "조인 조건과 일치하는 행"
  ],
  "Tất cả dòng bên phải": [
    "All right-hand rows",
    "모든 오른쪽 행"
  ],
  "Chỉ dòng không khớp": [
    "Only nonmatching rows",
    "일치하지 않는 행만"
  ],
  "Mệnh đề nào lọc các nhóm sau khi GROUP BY?": [
    "Which clause filters groups after GROUP BY?",
    "GROUP BY 후 그룹을 필터링하는 절은 무엇입니까?"
  ],
  "Chữ A trong ACID biểu thị tính chất nào?": [
    "What property does A in ACID represent?",
    "ACID의 A는 어떤 속성을 의미합니까?"
  ],
  "Chỉ mục": [
    "Index",
    "인덱스"
  ],
  "Mục đích chính của chỉ mục trong cơ sở dữ liệu là gì?": [
    "What is the main purpose of a database index?",
    "데이터베이스 인덱스의 주요 목적은 무엇입니까?"
  ],
  "Tăng tốc tra cứu dữ liệu": [
    "Speed up data lookup",
    "데이터 조회 가속"
  ],
  "Xóa các dòng trùng lặp": [
    "Delete duplicate rows",
    "중복 행 삭제"
  ],
  "Thay thế khóa ngoại": [
    "Replace foreign keys",
    "외래 키 대체"
  ],
  "Ngăn mọi lỗi giao dịch": [
    "Prevent all transaction errors",
    "모든 트랜잭션 오류 방지"
  ],
  "Liệt kê MSSV và họ tên các sinh viên có điểm từ 8 trở lên.": [
    "List student IDs and names for scores of 8 or higher.",
    "8점 이상 학생의 학번과 이름을 나열하세요."
  ],
  "Thống kê số sinh viên theo từng ngành, trả về MaNganh và SoSinhVien.": [
    "Count students by major, returning MaNganh and SoSinhVien.",
    "전공별 학생 수를 계산하여 MaNganh와 SoSinhVien을 반환하세요."
  ],
  "Liệt kê MSSV, họ tên và tên ngành của từng sinh viên.": [
    "List each student's ID, full name and major.",
    "학생별 학번, 이름 및 전공을 나열하세요."
  ],
  "Thiết kế & Chuẩn hóa": [
    "Design & Normalization",
    "설계 및 정규화"
  ],
  "Giải thích các dạng chuẩn 1NF, 2NF, 3NF và nêu ví dụ về một phép phân rã quan hệ.": [
    "Explain 1NF, 2NF and 3NF and give a relational decomposition example.",
    "1NF, 2NF, 3NF를 설명하고 관계 분해 예를 제시하세요."
  ],
  "1NF: các giá trị nguyên tố, không có nhóm lặp. 2NF: đạt 1NF và không có phụ thuộc bộ phận vào khóa. 3NF: đạt 2NF và không có phụ thuộc bắc cầu giữa các thuộc tính không khóa.": [
    "1NF: atomic values, no repeating groups. 2NF: 1NF with no partial key dependencies. 3NF: 2NF with no transitive dependencies among non-key attributes.",
    "1NF: 원자 값, 반복 그룹 없음. 2NF: 1NF이며 키의 부분 종속 없음. 3NF: 2NF이며 비키 속성의 이행 종속 없음."
  ],
  "Giải thích đúng các dạng chuẩn: 1.5 điểm. Ví dụ và phân rã hợp lý: 1.0 điểm. Trình bày rõ ràng: 0.5 điểm.": [
    "Correct normal form explanation: 1.5 points. Valid example and decomposition: 1.0 point. Clear presentation: 0.5 points.",
    "정규형 설명: 1.5점. 타당한 예와 분해: 1.0점. 명확한 서술: 0.5점."
  ],
  "Bạn đã chỉnh sửa xong bài kiểm tra và muốn lưu rồi thoát chưa?\n\nChọn OK để lưu và quay lại. Chọn Hủy để tiếp tục chỉnh sửa.": [
    "Finished editing? Save and exit?\n\nSelect OK to save and return, or Cancel to continue editing.",
    "수정을 완료했습니까? 저장 후 종료할까요?\n\n확인을 누르면 저장 후 돌아가며 취소를 누르면 계속 수정합니다."
  ],
  "Không thể tải thông báo.": [
    "Could not load notifications.",
    "알림을 불러올 수 없습니다."
  ],
  "Không thể cập nhật thông báo.": [
    "Could not update notification.",
    "알림을 갱신할 수 없습니다."
  ]
};
const ADMIN_TRANSLATION_KEYS = Object.keys(ADMIN_TRANSLATIONS).sort((a,b)=>b.length-a.length);

const ACTIVE_LEARNER_KEY = "dbcas.learner.active-account.v1";
export function useAdminLanguage() { return useSettings().language; }
export function adminText(value, language) {
  if (typeof value !== "string") return value;
  const lang = language || (() => { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}").language || "vi"; } catch { return "vi"; } })();
  if (lang === "vi" || !["en","ko"].includes(lang)) return value;
  const index = lang === "en" ? 0 : 1;
  const normalized = value.replace(/\s+/g," ").trim();
  const pair = ADMIN_TRANSLATIONS[normalized];
  if (pair) return value.match(/^\s*/)[0] + pair[index] + value.match(/\s*$/)[0];
  let result = value;
  // Static sentence fragments can be concatenated in the original source.
  for (const key of ADMIN_TRANSLATION_KEYS) {
    if (key.length >= 5 && result.includes(key)) result = result.split(key).join(ADMIN_TRANSLATIONS[key][index]);
  }
  return result;
}
export function adminRender(value) {
  if (typeof value === "string") return adminText(value);
  if (Array.isArray(value)) return value.map(adminRender);
  return value;
}
function BellGlyph() { return <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg>; }
function usePopup(open,setOpen,root,trigger) {
  useEffect(() => {
    if (!open) return;
    root.current?.querySelector('[data-popup-focus]')?.focus();
    function dismiss(event) { if (!root.current?.contains(event.target)) setOpen(false); }
    function escape(event) { if (event.key === "Escape") { setOpen(false); trigger.current?.focus(); } }
    document.addEventListener("pointerdown",dismiss); document.addEventListener("keydown",escape);
    return () => { document.removeEventListener("pointerdown",dismiss); document.removeEventListener("keydown",escape); };
  },[open,setOpen,root,trigger]);
}
const NotificationContext = createContext({items:{admin:[],learner:[]},error:{},loading:{},refresh:async()=>{},markRead:async()=>{}});
export function NotificationProvider({ children, service }) {
  const [items,setItems]=useState({admin:[],learner:[]});
  const [error,setError]=useState({}); const [loading,setLoading]=useState({});
  const known = useRef(new Set());
  const prefs = useLearnerPreferences();
  const prefsRef=useRef(prefs); prefsRef.current=prefs;
  function accept(role, rows, announce=false) {
    if (!["admin","learner"].includes(role) || !Array.isArray(rows)) return;
    const normalized=rows.filter(row=>row && row.id!=null).map(row=>({...row,id:String(row.id),read:row.read===true}));
    for (const item of normalized) {
      const key=`${role}:${item.id}`;
      if (announce && !known.current.has(key) && !item.read && role === "learner" && prefsRef.current.notifications && "Notification" in window && Notification.permission === "granted") {
        try { new Notification(item.title || "DBCAS", {body:item.message || "",tag:key}); } catch { /* Browser may require service-worker notifications. */ }
      }
      known.current.add(key);
    }
    setItems(old=>({...old,[role]:normalized}));
  }
  useEffect(() => {
    function receive(event) { accept(event.detail?.role,event.detail?.items,true); }
    window.addEventListener("dbcas:notifications",receive); return ()=>window.removeEventListener("dbcas:notifications",receive);
  },[]);
  const refresh=async role=>{
    if (!service?.list) return;
    setLoading(old=>({...old,[role]:true})); setError(old=>({...old,[role]:""}));
    try { accept(role,await service.list(role)); } catch { setError(old=>({...old,[role]:"Không thể tải thông báo."})); }
    finally {setLoading(old=>({...old,[role]:false}));}
  };
  const markRead=async(role,id)=>{
    try { if(service?.markRead)await service.markRead(role,id); setItems(old=>({...old,[role]:old[role].map(item=>item.id===id?{...item,read:true}:item)})); }
    catch {setError(old=>({...old,[role]:"Không thể cập nhật thông báo."}));}
  };
  return <NotificationContext.Provider value={{items,error,loading,refresh,markRead}}>{children}</NotificationContext.Provider>;
}
export function NotificationMenu({role="learner",className="notification-button"}) {
  const feed=useContext(NotificationContext), {language}=useSettings();
  const location=useLocation(); const [open,setOpen]=useState(false);
  const root=useRef(null),trigger=useRef(null);
  const text=value=>role==="admin"?adminText(value,language):value;
  const rows=feed.items[role]||[], unread=rows.filter(item=>!item.read).length;
  usePopup(open,setOpen,root,trigger);
  useEffect(()=>setOpen(false),[location.pathname]);
  return <div className="dbcas-popup-root" ref={root}><button className={className} type="button" ref={trigger} aria-label={text("Thông báo")} aria-expanded={open} aria-haspopup="dialog" onClick={()=>{setOpen(!open);if(!open)feed.refresh(role);}}><BellGlyph />{unread>0&&<span className="dbcas-unread-count">{unread>99?"99+":unread}</span>}</button>
    {open&&<section className="dbcas-header-popup" role="dialog" aria-label={text("Thông báo")}><div className="dbcas-popup-heading"><strong>{text("Thông báo")}</strong><button type="button" data-popup-focus onClick={()=>setOpen(false)} aria-label={text("Đóng")}>×</button></div>
      {feed.loading[role]&&<p role="status">{text("Đang tải...")}</p>}{feed.error[role]&&<p role="alert">{text(feed.error[role])}</p>}
      {!rows.length&&!feed.loading[role]&&<p>{text("Chưa có thông báo mới.")}</p>}
      <ul>{rows.map(item=><li key={item.id} className={item.read?"":"unread"}><button type="button" onClick={async()=>{await feed.markRead(role,item.id);}}><strong>{item.title}</strong><span>{item.message}</span>{item.createdAt&&<small>{Number.isNaN(Date.parse(item.createdAt))?"":new Date(item.createdAt).toLocaleString(role==="admin"?({vi:"vi-VN",en:"en-US",ko:"ko-KR"}[language]):"vi-VN")}</small>}</button></li>)}</ul><button className="dbcas-popup-refresh" type="button" onClick={()=>feed.refresh(role)}>{text("Làm mới")}</button>
    </section>}
  </div>;
}
export function LearnerAccountMenu({profile: supplied,onLogout}) {
  const location=useLocation(),navigate=useNavigate();
  const [open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState("");
  const [version,setVersion]=useState(0); const root=useRef(null),trigger=useRef(null);
  usePopup(open,setOpen,root,trigger);
  useEffect(()=>{const sync=()=>setVersion(v=>v+1);window.addEventListener("storage",sync);window.addEventListener("dbcas:learner-profile-changed",sync);return()=>{window.removeEventListener("storage",sync);window.removeEventListener("dbcas:learner-profile-changed",sync);};},[]);
  useEffect(()=>setOpen(false),[location.pathname]);
  let saved={},id=supplied?.studentId||location.state?.user?.studentId||"20216000100";
  try {if (!supplied?.studentId && !location.state?.user?.studentId) id=localStorage.getItem(ACTIVE_LEARNER_KEY)||id;saved=JSON.parse(localStorage.getItem(`dbcas-learner-profile:${id}`)||"{}");}catch {/*Use current profile.*/}
  const profile={name:"Nguyễn Hoàng Long",email:"long.nh20216049@sis.hust.edu.vn",studentId:id,major:"Kỹ thuật Phần mềm",phone:"",...location.state?.user,...supplied,...saved};
  const initials=profile.name.trim().split(/\s+/).slice(-2).map(word=>word[0]).join("").toUpperCase();
  async function logout(){setBusy(true);setError("");try{if(onLogout)await onLogout();window.dispatchEvent(new CustomEvent("dbcas:logout",{detail:{role:"learner"}}));navigate("/Dang_nhap",{replace:true});}catch{setError("Không thể đăng xuất.");}finally{setBusy(false);}}
  return <div ref={root} className="dbcas-popup-root"><button ref={trigger} className="profile dbcas-profile-trigger" type="button" aria-expanded={open} aria-haspopup="dialog" onClick={()=>setOpen(!open)}><span className="avatar">{profile.avatar?<img src={profile.avatar} alt=""/>:initials}</span><span className="profile-info"><strong>{profile.name}</strong><span>{profile.email}</span></span></button>
  {open&&<section className="dbcas-header-popup dbcas-account-popup" role="dialog" aria-label="Thông tin tài khoản"><div className="dbcas-popup-heading"><strong>Thông tin tài khoản</strong><button type="button" data-popup-focus aria-label="Đóng" onClick={()=>setOpen(false)}>×</button></div><dl><dt>Họ và tên</dt><dd>{profile.name}</dd><dt>Email</dt><dd>{profile.email}</dd><dt>MSSV</dt><dd>{profile.studentId}</dd><dt>Ngành học</dt><dd>{profile.major}</dd><dt>Số điện thoại</dt><dd>{profile.phone||"Chưa cập nhật"}</dd></dl><Link to="/Cai_dat_Learner" state={{user:profile}}>Cài đặt tài khoản</Link><button className="dbcas-popup-logout" type="button" disabled={busy} onClick={logout}>{busy?"Đang đăng xuất...":"Đăng xuất"}</button>{error&&<p role="alert">{error}</p>}</section>}
  </div>;
}
export function InterfaceRuntime() {
  const {pathname}=useLocation(); const {language}=useSettings(); const preferences=useLearnerPreferences();
  useEffect(()=>{
    const learner=/Learner/i.test(pathname);
    document.documentElement.lang=learner?"vi":language;
    document.documentElement.style.setProperty("--learner-font-scale",learner?String(preferences.fontSize/16):"1");
    document.documentElement.style.setProperty("--dbcas-learner-content-size",`${preferences.fontSize}px`);
  },[pathname,language,preferences.fontSize]);
  return null;
}
