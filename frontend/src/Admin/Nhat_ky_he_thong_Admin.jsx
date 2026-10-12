import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  useSettings,
  NotificationMenu,
} from "../Context/SettingsContext";

import "./Home_Admin.css";
import "./Nhat_ky_he_thong_Admin.css";
import background from "./SQL.jpg";
import logo from "./logo1.png";

const TEXT = {
  vi: {
    home: "Trang chủ",
    competency: "Đánh giá năng lực",
    clo: "CLO & Kỹ năng",
    exams: "Quản lý bài kiểm tra",
    ai: "Đánh giá bằng AI",
    reports: "Báo cáo",
    settings: "Cài đặt",
    create: "Tạo bài kiểm tra",
    logout: "Đăng xuất",
    loggingOut: "Đang đăng xuất...",
    title: "Nhật ký hệ thống",
    subtitle:
      "Theo dõi tài khoản, kết quả bài kiểm tra, chấm điểm AI và thay đổi năng lực CLO.",
    search: "Tìm tên sinh viên, MSSV, bài kiểm tra hoặc nội dung...",
    allTypes: "Tất cả hoạt động",
    accountType: "Tài khoản",
    examType: "Bài kiểm tra",
    aiType: "Chấm điểm AI",
    reviewType: "Duyệt điểm",
    cloType: "Thay đổi CLO",
    errorType: "Lỗi hệ thống",
    from: "Từ ngày",
    to: "Đến ngày",
    reset: "Đặt lại",
    time: "Thời gian",
    type: "Loại hoạt động",
    content: "Nội dung",
    action: "Thao tác",
    detail: "Xem chi tiết",
    empty: "Không có nhật ký phù hợp với bộ lọc.",
    invalidDate: "Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.",
    showing: "Hiển thị",
    of: "trên",
    entries: "hoạt động",
    previous: "Trước",
    next: "Sau",
    close: "Đóng",
    eventId: "Mã sự kiện",
    actor: "Tài khoản thực hiện",
    student: "Sinh viên",
    studentId: "MSSV",
    exam: "Bài kiểm tra",
    score: "Điểm bài kiểm tra",
    description: "Nội dung chi tiết",
    account: "Thông tin tài khoản",
    phone: "Số điện thoại",
    noPhone: "Chưa cập nhật",
    accountSettings: "Cài đặt tài khoản",
    logoutError: "Không thể đăng xuất.",
    footer: "DBCAS • Nền tảng đánh giá năng lực CSDL",
    completed: "Hoàn thành",
    pending: "Chờ Admin duyệt",
    failed: "Cần xử lý",
    status: "Trạng thái",
    count: "Số bài tự luận",
    before: "Điểm CLO trước",
    after: "Điểm CLO sau",
    comparison: "Mốc so sánh",
    previousAssessment: "Lần đánh giá trước",
    accountCreated: "Tài khoản sinh viên mới",
    examCompleted: "Sinh viên hoàn thành bài kiểm tra",
    aiCompleted: "AI chấm xong bài tự luận",
    scoreApproved: "Admin duyệt điểm tự luận",
    cloIncreased: "Năng lực CLO tăng",
    cloDecreased: "Năng lực CLO giảm",
    examCreated: "Tạo bài kiểm tra mới",
    aiFailed: "AI chấm bài thất bại",
  },
  en: {
    home: "Home",
    competency: "Competency assessment",
    clo: "CLO & Skills",
    exams: "Exam management",
    ai: "AI assessment",
    reports: "Reports",
    settings: "Settings",
    create: "Create an exam",
    logout: "Log out",
    loggingOut: "Logging out...",
    title: "System logs",
    subtitle:
      "Monitor accounts, exam results, AI grading and changes in CLO competency.",
    search: "Search student name, student ID, exam or content...",
    allTypes: "All activities",
    accountType: "Accounts",
    examType: "Exams",
    aiType: "AI grading",
    reviewType: "Grade approval",
    cloType: "CLO changes",
    errorType: "System errors",
    from: "From",
    to: "To",
    reset: "Reset",
    time: "Time",
    type: "Activity type",
    content: "Content",
    action: "Action",
    detail: "View details",
    empty: "No logs match your filters.",
    invalidDate: "The start date must not be after the end date.",
    showing: "Showing",
    of: "of",
    entries: "activities",
    previous: "Previous",
    next: "Next",
    close: "Close",
    eventId: "Event ID",
    actor: "Performed by",
    student: "Student",
    studentId: "Student ID",
    exam: "Exam",
    score: "Exam score",
    description: "Details",
    account: "Account information",
    phone: "Phone number",
    noPhone: "Not provided",
    accountSettings: "Account settings",
    logoutError: "Unable to log out.",
    footer: "DBCAS • Database competency assessment platform",
    completed: "Completed",
    pending: "Awaiting Admin approval",
    failed: "Action required",
    status: "Status",
    count: "Essay submissions",
    before: "Previous CLO score",
    after: "Current CLO score",
    comparison: "Comparison baseline",
    previousAssessment: "Previous assessment",
    accountCreated: "Student account created",
    examCompleted: "Student completed an exam",
    aiCompleted: "AI essay grading completed",
    scoreApproved: "Admin approved an essay grade",
    cloIncreased: "CLO competency increased",
    cloDecreased: "CLO competency decreased",
    examCreated: "New exam created",
    aiFailed: "AI grading failed",
  },
  ko: {
    home: "홈",
    competency: "역량 평가",
    clo: "CLO 및 역량",
    exams: "시험 관리",
    ai: "AI 평가",
    reports: "보고서",
    settings: "설정",
    create: "시험 만들기",
    logout: "로그아웃",
    loggingOut: "로그아웃 중...",
    title: "시스템 로그",
    subtitle: "계정, 시험 결과, AI 채점 및 CLO 역량 변화를 확인합니다.",
    search: "학생 이름, 학번, 시험 또는 내용 검색...",
    allTypes: "모든 활동",
    accountType: "계정",
    examType: "시험",
    aiType: "AI 채점",
    reviewType: "점수 승인",
    cloType: "CLO 변화",
    errorType: "시스템 오류",
    from: "시작 날짜",
    to: "종료 날짜",
    reset: "초기화",
    time: "시간",
    type: "활동 유형",
    content: "내용",
    action: "작업",
    detail: "상세 보기",
    empty: "필터에 해당하는 로그가 없습니다.",
    invalidDate: "시작 날짜는 종료 날짜보다 늦을 수 없습니다.",
    showing: "표시",
    of: "/",
    entries: "활동",
    previous: "이전",
    next: "다음",
    close: "닫기",
    eventId: "이벤트 ID",
    actor: "작업 계정",
    student: "학생",
    studentId: "학번",
    exam: "시험",
    score: "시험 점수",
    description: "상세 내용",
    account: "계정 정보",
    phone: "전화번호",
    noPhone: "등록되지 않음",
    accountSettings: "계정 설정",
    logoutError: "로그아웃할 수 없습니다.",
    footer: "DBCAS • 데이터베이스 역량 평가 플랫폼",
    completed: "완료",
    pending: "관리자 승인 대기",
    failed: "조치 필요",
    status: "상태",
    count: "서술형 답안 수",
    before: "이전 CLO 점수",
    after: "현재 CLO 점수",
    comparison: "비교 기준",
    previousAssessment: "이전 평가",
    accountCreated: "학생 계정 생성",
    examCompleted: "학생 시험 완료",
    aiCompleted: "AI 서술형 채점 완료",
    scoreApproved: "관리자 서술형 점수 승인",
    cloIncreased: "CLO 역량 상승",
    cloDecreased: "CLO 역량 하락",
    examCreated: "새 시험 생성",
    aiFailed: "AI 채점 실패",
  },
};

const TYPES = {
  account: "accountType",
  exam: "examType",
  ai: "aiType",
  review: "reviewType",
  clo: "cloType",
  error: "errorType",
};

const EVENT_TITLES = {
  account_created: "accountCreated",
  exam_completed: "examCompleted",
  ai_completed: "aiCompleted",
  score_approved: "scoreApproved",
  clo_increased: "cloIncreased",
  clo_decreased: "cloDecreased",
  exam_created: "examCreated",
  ai_failed: "aiFailed",
};

const EXAM_NAMES = {
  basic: {
    vi: "Kiểm tra CSDL cơ bản",
    en: "Basic Database Assessment",
    ko: "데이터베이스 기초 평가",
  },
  advanced: {
    vi: "Kiểm tra CSDL nâng cao",
    en: "Advanced Database Assessment",
    ko: "데이터베이스 심화 평가",
  },
  normalization: {
    vi: "Kiểm tra Chuẩn hóa CSDL",
    en: "Database Normalization Assessment",
    ko: "데이터베이스 정규화 평가",
  },
};

const CLO_NAMES = {
  1: {
    vi: "Truy vấn SQL",
    en: "SQL Queries",
    ko: "SQL 쿼리",
  },
  2: {
    vi: "DML & DDL",
    en: "DML & DDL",
    ko: "DML 및 DDL",
  },
  3: {
    vi: "Thiết kế & Ràng buộc",
    en: "Design & Constraints",
    ko: "설계 및 제약 조건",
  },
};

/* Dữ liệu mẫu. Khi có BE, truyền logs={dataFromAPI}. */
const DEMO_LOGS = [
  {
    id: "LOG-00001",
    createdAt: "2026-10-13T02:30:00+07:00",
    type: "account",
    event: "account_created",
    actor: "admin.dbcas@gmail.com",
    studentName: "Nguyễn Hoàng Long",
    studentId: "20216000100",
    email: "long.nh@dtu.edu.vn",
    status: "completed",
  },
  {
    id: "LOG-00002",
    createdAt: "2026-10-13T02:25:00+07:00",
    type: "exam",
    event: "exam_completed",
    actor: "long.nh@dtu.edu.vn",
    studentName: "Nguyễn Hoàng Long",
    studentId: "20216000100",
    examKey: "basic",
    examId: "EXAM-001",
    score: 7.4,
    status: "completed",
  },
  {
    id: "LOG-00003",
    createdAt: "2026-10-13T02:20:00+07:00",
    type: "ai",
    event: "ai_completed",
    actor: "AI Grading Service",
    examKey: "advanced",
    examId: "EXAM-002",
    essayCount: 5,
    status: "pending",
  },
  {
    id: "LOG-00004",
    createdAt: "2026-10-13T02:15:00+07:00",
    type: "review",
    event: "score_approved",
    actor: "admin.dbcas@gmail.com",
    studentName: "Trần Minh Anh",
    studentId: "20216000101",
    examKey: "advanced",
    examId: "EXAM-002",
    essayScore: 2.4,
    essayMaxScore: 3,
    status: "completed",
  },
  {
    id: "LOG-00005",
    createdAt: "2026-10-13T02:10:00+07:00",
    type: "clo",
    event: "clo_increased",
    actor: "Competency Engine",
    studentName: "Nguyễn Hoàng Long",
    studentId: "20216000100",
    cloId: 1,
    before: 6.5,
    after: 8,
    baselineAt: "2026-10-05T10:00:00+07:00",
    status: "completed",
  },
  {
    id: "LOG-00006",
    createdAt: "2026-10-13T02:05:00+07:00",
    type: "clo",
    event: "clo_decreased",
    actor: "Competency Engine",
    studentName: "Lê Ngọc Thư",
    studentId: "20216000102",
    cloId: 3,
    before: 7,
    after: 5.5,
    baselineAt: "2026-10-06T09:00:00+07:00",
    status: "completed",
  },
  {
    id: "LOG-00007",
    createdAt: "2026-10-13T02:00:00+07:00",
    type: "exam",
    event: "exam_created",
    actor: "admin.dbcas@gmail.com",
    examKey: "normalization",
    examId: "EXAM-003",
    duration: 60,
    status: "completed",
  },
  {
    id: "LOG-00008",
    createdAt: "2026-10-13T01:55:00+07:00",
    type: "error",
    event: "ai_failed",
    actor: "AI Grading Service",
    studentName: "Phạm Gia Huy",
    studentId: "20216000103",
    examKey: "advanced",
    examId: "EXAM-002",
    status: "failed",
  },
  {
    id: "LOG-00009",
    createdAt: "2026-10-12T21:40:00+07:00",
    type: "exam",
    event: "exam_completed",
    actor: "anh.tm@dtu.edu.vn",
    studentName: "Trần Minh Anh",
    studentId: "20216000101",
    examKey: "basic",
    examId: "EXAM-001",
    score: 8.2,
    status: "completed",
  },
  {
    id: "LOG-00010",
    createdAt: "2026-10-12T21:30:00+07:00",
    type: "ai",
    event: "ai_completed",
    actor: "AI Grading Service",
    examKey: "normalization",
    examId: "EXAM-003",
    essayCount: 12,
    status: "pending",
  },
  {
    id: "LOG-00011",
    createdAt: "2026-10-12T21:20:00+07:00",
    type: "clo",
    event: "clo_increased",
    actor: "Competency Engine",
    studentName: "Trần Minh Anh",
    studentId: "20216000101",
    cloId: 2,
    before: 6.8,
    after: 8.4,
    baselineAt: "2026-10-04T08:00:00+07:00",
    status: "completed",
  },
  {
    id: "LOG-00012",
    createdAt: "2026-10-12T21:10:00+07:00",
    type: "account",
    event: "account_created",
    actor: "admin.dbcas@gmail.com",
    studentName: "Võ Thanh Nam",
    studentId: "20216000104",
    email: "nam.vt@dtu.edu.vn",
    status: "completed",
  },
];

const ICONS = {
  home: "m3 10 9-7 9 7v11h-6v-8H9v8H3Z",
  users:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M15 3a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-3.87",
  clo: "m2 9 10-5 10 5-10 5ZM6 11v6c4 3 8 3 12 0v-6M22 9v7",
  file: "M14 2H6v20h14V8ZM14 2v6h6M9 12h8M9 16h8",
  ai: "M7 7h10v12H7ZM12 3v4M3 10h4M17 10h4M10 11h.01M14 11h.01M10 15h4",
  chart: "M4 3v18h17M8 16V9M13 16V5M18 16v-5",
  settings:
    "m12 3 2 2 3-.1 1 3 2 2-2 2-1 3-3-.1-2 2-2-2-3 .1-1-3-2-2 2-2 1-3 3 .1Z",
  plus: "M12 5v14M5 12h14",
  logout: "M10 4H4v16h6M9 12h12M17 8l4 4-4 4",
  search: "m21 21-5-5",
  reset: "M3 10a9 9 0 1 1 2 8M3 4v6h6",
};

function Icon({ name }) {
  return (
    <svg
      className="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {name === "search" && <circle cx="10" cy="10" r="6" />}
      {name === "users" && <circle cx="9" cy="7" r="4" />}
      {name === "settings" && <circle cx="12" cy="11" r="3" />}
      <path d={ICONS[name] || ICONS.file} />
    </svg>
  );
}

function localized(value, language) {
  if (value && typeof value === "object") {
    return value[language] || value.vi || value.en || "";
  }

  return String(value ?? "");
}

function examName(item, language) {
  return localized(
    item.examName || EXAM_NAMES[item.examKey],
    language
  );
}

function cloName(item, language) {
  return localized(
    item.cloName || CLO_NAMES[item.cloId],
    language
  );
}

function eventTitle(item, language) {
  return localized(item.title, language) ||
    TEXT[language][EVENT_TITLES[item.event]] ||
    item.event ||
    "";
}

function eventMessage(item, language) {
  if (item.message) return localized(item.message, language);

  const name = item.studentName || "—";
  const id = item.studentId || "—";
  const exam = examName(item, language) || "—";
  const clo = cloName(item, language) || "—";
  const actor = item.actor || "—";

  if (language === "en") {
    switch (item.event) {
      case "account_created":
        return `A student account was created for ${name} — Student ID ${id}.`;

      case "exam_completed":
        return `${name} — Student ID ${id} completed “${exam}” with a score of ${item.score}/10.`;

      case "ai_completed":
        return `AI finished grading ${item.essayCount} essay submissions for “${exam}”. They are awaiting Admin approval.`;

      case "score_approved":
        return `${actor} approved the essay grade for ${name} — Student ID ${id} in “${exam}”: ${item.essayScore}/${item.essayMaxScore}.`;

      case "clo_increased":
        return `CLO ${item.cloId} — ${clo} for ${name} — Student ID ${id} increased from ${item.before} to ${item.after}/10 compared with the previous assessment.`;

      case "clo_decreased":
        return `CLO ${item.cloId} — ${clo} for ${name} — Student ID ${id} decreased from ${item.before} to ${item.after}/10 compared with the previous assessment.`;

      case "exam_created":
        return `${actor} created “${exam}” with a duration of ${item.duration} minutes.`;

      case "ai_failed":
        return `AI could not grade the essay submitted by ${name} — Student ID ${id} for “${exam}”. Another grading attempt is required.`;

      default:
        return eventTitle(item, language);
    }
  }

  if (language === "ko") {
    switch (item.event) {
      case "account_created":
        return `${name} — 학번 ${id}의 학생 계정이 생성되었습니다.`;

      case "exam_completed":
        return `${name} — 학번 ${id}가 “${exam}” 시험을 완료했습니다. 점수: ${item.score}/10.`;

      case "ai_completed":
        return `AI가 “${exam}” 시험의 서술형 답안 ${item.essayCount}개를 채점했습니다. 관리자 승인을 기다리고 있습니다.`;

      case "score_approved":
        return `${actor}가 “${exam}” 시험에서 ${name} — 학번 ${id}의 서술형 점수를 승인했습니다. 점수: ${item.essayScore}/${item.essayMaxScore}.`;

      case "clo_increased":
        return `${name} — 학번 ${id}의 CLO ${item.cloId} — ${clo} 점수가 이전 평가 대비 ${item.before}에서 ${item.after}/10으로 상승했습니다.`;

      case "clo_decreased":
        return `${name} — 학번 ${id}의 CLO ${item.cloId} — ${clo} 점수가 이전 평가 대비 ${item.before}에서 ${item.after}/10으로 하락했습니다.`;

      case "exam_created":
        return `${actor}가 “${exam}” 시험을 생성했습니다. 시험 시간: ${item.duration}분.`;

      case "ai_failed":
        return `AI가 “${exam}” 시험의 ${name} — 학번 ${id}의 서술형 답안을 채점하지 못했습니다. 다시 처리해야 합니다.`;

      default:
        return eventTitle(item, language);
    }
  }

  switch (item.event) {
    case "account_created":
      return `Tài khoản sinh viên ${name} — MSSV ${id} vừa được tạo.`;

    case "exam_completed":
      return `${name} — MSSV ${id} đã hoàn thành “${exam}”, đạt ${item.score}/10.`;

    case "ai_completed":
      return `AI đã chấm xong ${item.essayCount} bài tự luận của “${exam}”, đang chờ Admin duyệt.`;

    case "score_approved":
      return `${actor} đã duyệt điểm tự luận của ${name} — MSSV ${id} trong “${exam}”: ${item.essayScore}/${item.essayMaxScore} điểm.`;

    case "clo_increased":
      return `CLO ${item.cloId} — ${clo} của ${name} — MSSV ${id} tăng từ ${item.before} lên ${item.after}/10 so với lần đánh giá trước.`;

    case "clo_decreased":
      return `CLO ${item.cloId} — ${clo} của ${name} — MSSV ${id} giảm từ ${item.before} xuống ${item.after}/10 so với lần đánh giá trước.`;

    case "exam_created":
      return `${actor} vừa tạo “${exam}”, thời lượng ${item.duration} phút.`;

    case "ai_failed":
      return `AI chưa chấm được bài tự luận của ${name} — MSSV ${id} trong “${exam}”, cần xử lý lại.`;

    default:
      return eventTitle(item, language);
  }
}

function dateKey(value) {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "";

  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function normalizeSearch(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();
}

function AccountMenu({ t, onLogout, busy }) {
  const rootRef = useRef(null);
  const triggerRef = useRef(null);

  const [open, setOpen] = useState(false);
  const [account, setAccount] = useState({
    name: "Admin System",
    email: "admin.dbcas@gmail.com",
    phone: "",
  });

  useEffect(() => {
    function refresh() {
      try {
        const saved = JSON.parse(
          localStorage.getItem(
            "dbcas.admin.account.v1:admin.dbcas@gmail.com"
          ) || "{}"
        );

        setAccount({
          name: saved.name || "Admin System",
          email: "admin.dbcas@gmail.com",
          phone: saved.phone || "",
        });
      } catch {
        // Giữ thông tin mặc định.
      }
    }

    refresh();
    window.addEventListener("storage", refresh);
    window.addEventListener("dbcas:account-changed", refresh);

    return () => {
      window.removeEventListener("storage", refresh);
      window.removeEventListener("dbcas:account-changed", refresh);
    };
  }, []);

  useEffect(() => {
    if (!open) return;

    function outside(event) {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    }

    function escape(event) {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    }

    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);

    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);

  const initials = account.name
    .split(" ")
    .filter(Boolean)
    .slice(-2)
    .map((word) => word[0])
    .join("");

  return (
    <div className="jl-account" ref={rootRef}>
      <button
        className="jl-account-trigger"
        ref={triggerRef}
        type="button"
        aria-label={t.account}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="jl-avatar">{initials}</span>

        <span className="jl-account-caption">
          <strong>{account.name}</strong>
          <small>{account.email}</small>
        </span>

        <span aria-hidden="true">⌄</span>
      </button>

      {open && (
        <div className="jl-account-panel">
          <strong>{t.account}</strong>
          <p>{account.name}</p>
          <p>{account.email}</p>
          <p>{t.phone}: {account.phone || t.noPhone}</p>

          <Link to="/Cai_dat_Admin">{t.accountSettings}</Link>

          <button
            type="button"
            disabled={busy}
            onClick={onLogout}
          >
            {busy ? t.loggingOut : t.logout}
          </button>
        </div>
      )}
    </div>
  );
}

export default function NhatKyHeThongAdmin({
  logs = DEMO_LOGS,
  onLogout,
}) {
  const navigate = useNavigate();
  const { language } = useSettings();
  const lang = TEXT[language] ? language : "vi";
  const t = TEXT[lang];

  const [query, setQuery] = useState("");
  const [type, setType] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  const dialogRef = useRef(null);
  const pageSize = 10;

  const invalidDate = Boolean(
    fromDate && toDate && fromDate > toDate
  );

  const source = useMemo(
    () => (Array.isArray(logs) ? logs : []),
    [logs]
  );

  const filtered = useMemo(() => {
    if (invalidDate) return [];

    const keyword = normalizeSearch(query.trim());

    return source
      .filter((item) => {
        const day = dateKey(item.createdAt);

        const content = normalizeSearch([
          item.id,
          item.actor,
          item.studentName,
          item.studentId,
          item.email,
          item.examId,
          examName(item, lang),
          eventTitle(item, lang),
          eventMessage(item, lang),
        ].join(" "));

        return (
          (!keyword || content.includes(keyword)) &&
          (!type || item.type === type) &&
          (!fromDate || day >= fromDate) &&
          (!toDate || day <= toDate)
        );
      })
      .sort(
        (a, b) => new Date(b.createdAt) - new Date(a.createdAt)
      );
  }, [source, query, type, fromDate, toDate, invalidDate, lang]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const start = (currentPage - 1) * pageSize;
  const visible = filtered.slice(start, start + pageSize);

  const navItems = [
    ["home", t.home, "/Home_Admin"],
    ["users", t.competency, "/Danh_gia_nang_luc_Admin"],
    ["clo", t.clo, "/CLO_Ky_nang_Admin"],
    ["file", t.exams, "/Quan_ly_bai_kiem_tra_Admin"],
    ["ai", t.ai, "/Danh_gia_AI_Admin"],
    ["chart", t.reports, "/Bao_cao_Admin"],
    ["settings", t.settings, "/Cai_dat_Admin"],
  ];

  useEffect(() => {
    if (selected) dialogRef.current?.showModal();
  }, [selected]);

  function changeFilter(setter, value) {
    setter(value);
    setPage(1);
  }

  function resetFilters() {
    setQuery("");
    setType("");
    setFromDate("");
    setToDate("");
    setPage(1);
  }

  function displayTime(value) {
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return "—";

    return new Intl.DateTimeFormat(
      lang === "en" ? "en-US" : lang === "ko" ? "ko-KR" : "vi-VN",
      {
        dateStyle: "short",
        timeStyle: "medium",
      }
    ).format(date);
  }

  function closeDetail() {
    dialogRef.current?.close();
    setSelected(null);
  }

  async function logout() {
    if (busy) return;

    setBusy(true);
    setNotice("");

    try {
      if (onLogout) await onLogout();

      window.dispatchEvent(
        new CustomEvent("dbcas:logout", {
          detail: { role: "admin" },
        })
      );

      navigate("/Dang_nhap");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : t.logoutError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="dbcas-admin-home dbcas-system-logs"
      style={{
        backgroundImage:
          `linear-gradient(rgba(7,11,20,.88), rgba(7,11,20,.88)), url(${background})`,
      }}
    >
      <aside className="sidebar">
        <div className="sidebar-content">
          <Link className="sidebar-brand" to="/Home_Admin">
            <img src={logo} alt="DBCAS" />
          </Link>

          <Link className="btn-new" to="/TN_Admin">
            <Icon name="plus" />
            <span>{t.create}</span>
          </Link>

          <nav className="sidebar-nav" aria-label="Admin">
            {navItems.map(([icon, label, path]) => (
              <Link
                key={path}
                to={path}
                className={`nav-link${
                  path === "/Home_Admin" ? " active" : ""
                }`}
              >
                <Icon name={icon} />
                <span>{label}</span>

                {path === "/Home_Admin" && (
                  <span className="nav-dot" />
                )}
              </Link>
            ))}
          </nav>
        </div>

        <div className="sidebar-bottom">
          <button
            className="btn-logout"
            type="button"
            disabled={busy}
            onClick={logout}
          >
            <Icon name="logout" />
            <span>{busy ? t.loggingOut : t.logout}</span>
          </button>
        </div>
      </aside>

      <header className="topbar admin-unified-topbar">
        <div className="breadcrumb">
          <span>DBCAS Admin</span>
          <span aria-hidden="true">›</span>
          <Link to="/Home_Admin">{t.home}</Link>
          <span aria-hidden="true">›</span>
          <strong>{t.title}</strong>
        </div>

        <div className="topbar-actions">
          <NotificationMenu role="admin" className="icon-button" />

          <AccountMenu
            t={t}
            onLogout={logout}
            busy={busy}
          />
        </div>
      </header>

      <main className="main">
        <section className="jl-heading">
          <div>
            <h1>{t.title}</h1>
            <p>{t.subtitle}</p>
          </div>
        </section>

        <section className="jl-card">
          <div className="jl-filters">
            <label className="jl-search">
              <Icon name="search" />

              <input
                type="search"
                value={query}
                placeholder={t.search}
                aria-label={t.search}
                onChange={(event) =>
                  changeFilter(setQuery, event.target.value)
                }
              />
            </label>

            <select
              aria-label={t.type}
              value={type}
              onChange={(event) =>
                changeFilter(setType, event.target.value)
              }
            >
              <option value="">{t.allTypes}</option>

              {Object.entries(TYPES).map(([value, key]) => (
                <option key={value} value={value}>
                  {t[key]}
                </option>
              ))}
            </select>

            <label className="jl-date">
              <span>{t.from}</span>
              <input
                type="date"
                value={fromDate}
                aria-label={t.from}
                onChange={(event) =>
                  changeFilter(setFromDate, event.target.value)
                }
              />
            </label>

            <label className="jl-date">
              <span>{t.to}</span>
              <input
                type="date"
                value={toDate}
                aria-label={t.to}
                onChange={(event) =>
                  changeFilter(setToDate, event.target.value)
                }
              />
            </label>

            <button
              className="jl-button"
              type="button"
              onClick={resetFilters}
            >
              <Icon name="reset" />
              {t.reset}
            </button>
          </div>

          {invalidDate && (
            <p className="jl-error" role="alert">
              {t.invalidDate}
            </p>
          )}

          <div className="jl-table-wrap">
            <table className="jl-table">
              <thead>
                <tr>
                  <th>{t.time}</th>
                  <th>{t.type}</th>
                  <th>{t.content}</th>
                  <th>{t.action}</th>
                </tr>
              </thead>

              <tbody>
                {visible.map((item) => (
                  <tr key={item.id}>
                    <td className="jl-time">
                      {displayTime(item.createdAt)}
                    </td>

                    <td>
                      <span className={`jl-badge jl-type-${item.type}`}>
                        {t[TYPES[item.type]] || item.type}
                      </span>
                    </td>

                    <td className="jl-content-cell">
                      <strong>{eventTitle(item, lang)}</strong>
                      <p>{eventMessage(item, lang)}</p>
                      <small>{item.id}</small>
                    </td>

                    <td>
                      <button
                        className="jl-detail"
                        type="button"
                        onClick={() => setSelected(item)}
                      >
                        {t.detail}
                      </button>
                    </td>
                  </tr>
                ))}

                {!visible.length && (
                  <tr>
                    <td colSpan={4} className="jl-empty">
                      {t.empty}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="jl-pagination">
            <p>
              {t.showing}{" "}
              <strong>
                {filtered.length ? start + 1 : 0}–
                {Math.min(start + pageSize, filtered.length)}
              </strong>{" "}
              {t.of} {filtered.length} {t.entries}
            </p>

            <div>
              <button
                className="jl-button"
                type="button"
                disabled={currentPage === 1}
                onClick={() => setPage(currentPage - 1)}
              >
                {t.previous}
              </button>

              <span>{currentPage} / {totalPages}</span>

              <button
                className="jl-button"
                type="button"
                disabled={currentPage === totalPages}
                onClick={() => setPage(currentPage + 1)}
              >
                {t.next}
              </button>
            </div>
          </div>
        </section>

        {notice && (
          <p className="jl-error" role="alert">{notice}</p>
        )}
      </main>

      <footer className="footer">
        <span>{t.footer}</span>
        <span>© 2026 Duy Tan University</span>
      </footer>

      <dialog
        className="jl-dialog"
        ref={dialogRef}
        aria-labelledby="jl-dialog-title"
        onCancel={closeDetail}
        onClose={() => setSelected(null)}
      >
        <h2 id="jl-dialog-title">{t.detail}</h2>

        {selected && (
          <dl>
            <dt>{t.eventId}</dt>
            <dd>{selected.id}</dd>

            <dt>{t.time}</dt>
            <dd>{displayTime(selected.createdAt)}</dd>

            <dt>{t.type}</dt>
            <dd>{t[TYPES[selected.type]] || selected.type}</dd>

            <dt>{t.actor}</dt>
            <dd>{selected.actor || "—"}</dd>

            {selected.studentName && (
              <>
                <dt>{t.student}</dt>
                <dd>{selected.studentName}</dd>

                <dt>{t.studentId}</dt>
                <dd>{selected.studentId}</dd>
              </>
            )}

            {(selected.examKey || selected.examName) && (
              <>
                <dt>{t.exam}</dt>
                <dd>
                  {examName(selected, lang)}
                  {selected.examId && ` · ${selected.examId}`}
                </dd>
              </>
            )}

            {selected.score != null && (
              <>
                <dt>{t.score}</dt>
                <dd>{selected.score}/10</dd>
              </>
            )}

            {selected.essayCount != null && (
              <>
                <dt>{t.count}</dt>
                <dd>{selected.essayCount}</dd>
              </>
            )}

            {selected.cloId != null && (
              <>
                <dt>CLO</dt>
                <dd>
                  CLO {selected.cloId} — {cloName(selected, lang)}
                </dd>

                <dt>{t.before}</dt>
                <dd>{selected.before}/10</dd>

                <dt>{t.after}</dt>
                <dd>{selected.after}/10</dd>

                <dt>{t.comparison}</dt>
                <dd>
                  {t.previousAssessment}
                  {selected.baselineAt &&
                    ` · ${displayTime(selected.baselineAt)}`}
                </dd>
              </>
            )}

            <dt>{t.status}</dt>
            <dd>{t[selected.status] || selected.status || "—"}</dd>

            <dt>{t.description}</dt>
            <dd>{eventMessage(selected, lang)}</dd>
          </dl>
        )}

        <button
          className="jl-button"
          type="button"
          autoFocus
          onClick={closeDetail}
        >
          {t.close}
        </button>
      </dialog>
    </div>
  );
}