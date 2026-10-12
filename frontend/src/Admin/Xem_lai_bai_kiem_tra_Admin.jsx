import { useAdminLanguage, adminText, adminRender, NotificationMenu } from "../Context/SettingsContext";
import { useEffect, useMemo, useState, useRef } from "react";
import { useLocation, useNavigate, useParams, Link } from "react-router-dom";
import "./Home_Admin.css";
import "./Xem_lai_bai_kiem_tra_Admin.css";
import background from "./SQL.jpg";
const STORAGE_KEY = "dbcas-exam-content-v1";
const TYPES = {
  mcq: "Trắc nghiệm",
  sql: "Truy vấn SQL",
  essay: "Tự luận"
};
const clone = value => JSON.parse(JSON.stringify(value));
const MCQ_SEEDS = [["Lý thuyết chuẩn hóa (1NF)", "Một quan hệ đạt chuẩn 1NF khi thỏa mãn điều kiện nào?", ["Mọi thuộc tính không khóa phụ thuộc đầy đủ vào khóa chính.", "Mỗi ô chứa một giá trị nguyên tố, không chứa nhóm lặp.", "Không có phụ thuộc bắc cầu giữa các thuộc tính không khóa.", "Mọi định thức đều là khóa ứng viên."], 1], ["Xác định dạng chuẩn", "Quan hệ đã đạt 1NF và mọi thuộc tính không khóa phụ thuộc đầy đủ vào toàn bộ khóa chính đạt tối thiểu dạng chuẩn nào?", ["1NF", "2NF", "3NF", "4NF"], 1], ["Thuật toán Tableau", "Thuật toán Tableau thường được sử dụng để kiểm tra tính chất nào của phép phân rã quan hệ?", ["Số lượng chỉ mục", "Kết nối không mất mát", "Thời gian thực thi", "Dung lượng lưu trữ"], 1], ["Tính toàn vẹn", "Ràng buộc nào đảm bảo mỗi bản ghi có một định danh duy nhất và không NULL?", ["DEFAULT", "CHECK", "PRIMARY KEY", "FOREIGN KEY"], 2], ["Chuẩn BCNF", "Quan hệ đạt BCNF khi với mọi phụ thuộc hàm không tầm thường X → Y, X là gì?", ["Thuộc tính không khóa", "Siêu khóa", "Khóa ngoại", "Tập rỗng"], 1], ["Phụ thuộc hàm", "Phụ thuộc hàm X → Y có ý nghĩa gì?", ["Một giá trị X xác định duy nhất giá trị Y.", "Y luôn là khóa chính.", "X và Y phải có cùng kiểu dữ liệu.", "X phải là khóa ngoại."], 0], ["JOIN", "INNER JOIN trả về những dòng nào?", ["Tất cả dòng bên trái", "Các dòng khớp điều kiện nối", "Tất cả dòng bên phải", "Chỉ dòng không khớp"], 1], ["GROUP BY", "Mệnh đề nào lọc các nhóm sau khi GROUP BY?", ["ORDER BY", "WHERE", "HAVING", "LIMIT"], 2], ["Transaction & ACID", "Chữ A trong ACID biểu thị tính chất nào?", ["Availability", "Atomicity", "Authorization", "Aggregation"], 1], ["Chỉ mục", "Mục đích chính của chỉ mục trong cơ sở dữ liệu là gì?", ["Tăng tốc tra cứu dữ liệu", "Xóa các dòng trùng lặp", "Thay thế khóa ngoại", "Ngăn mọi lỗi giao dịch"], 0]];
function buildQuestions(exam) {
  const count = (value, fallback) => Number.isInteger(Number(value)) && Number(value) >= 0 && Number(value) <= 100 ? Number(value) : fallback;
  const result = [];
  const mcqCount = count(exam.mcqCount, 10),
    sqlCount = count(exam.sqlCount, 3),
    essayCount = count(exam.essayCount, 1);
  for (let i = 0; i < mcqCount; i++) {
    const [topic, prompt, options, correct] = MCQ_SEEDS[i % MCQ_SEEDS.length];
    result.push({
      id: `mcq-${i + 1}`,
      type: "mcq",
      topic,
      prompt,
      points: Number((4 / Math.max(1, mcqCount)).toFixed(4)),
      options: options.map((text, index) => ({
        id: `option-${index}`,
        text
      })),
      correctId: `option-${correct}`
    });
  }
  for (let i = 0; i < sqlCount; i++) {
    const seeds = [["SELECT & WHERE", "Liệt kê MSSV và họ tên các sinh viên có điểm từ 8 trở lên.", "SELECT MSSV, HoTen FROM SinhVien WHERE Diem >= 8;"], ["GROUP BY", "Thống kê số sinh viên theo từng ngành, trả về MaNganh và SoSinhVien.", "SELECT MaNganh, COUNT(*) AS SoSinhVien FROM SinhVien GROUP BY MaNganh;"], ["JOIN", "Liệt kê MSSV, họ tên và tên ngành của từng sinh viên.", "SELECT s.MSSV, s.HoTen, n.TenNganh FROM SinhVien s JOIN Nganh n ON s.MaNganh = n.MaNganh;"]];
    const [topic, prompt, answer] = seeds[i % seeds.length];
    result.push({
      id: `sql-${i + 1}`,
      type: "sql",
      topic,
      prompt,
      points: Number((3 / Math.max(1, sqlCount)).toFixed(4)),
      schema: "SinhVien(MSSV, HoTen, MaNganh, Diem)\nNganh(MaNganh, TenNganh)",
      answer
    });
  }
  for (let i = 0; i < essayCount; i++) result.push({
    id: `essay-${i + 1}`,
    type: "essay",
    topic: "Thiết kế & Chuẩn hóa",
    prompt: "Giải thích các dạng chuẩn 1NF, 2NF, 3NF và nêu ví dụ về một phép phân rã quan hệ.",
    points: Number((3 / Math.max(1, essayCount)).toFixed(4)),
    answer: "1NF: các giá trị nguyên tố, không có nhóm lặp. 2NF: đạt 1NF và không có phụ thuộc bộ phận vào khóa. 3NF: đạt 2NF và không có phụ thuộc bắc cầu giữa các thuộc tính không khóa.",
    rubric: "Giải thích đúng các dạng chuẩn: 1.5 điểm. Ví dụ và phân rã hợp lý: 1.0 điểm. Trình bày rõ ràng: 0.5 điểm."
  });
  return result;
}
function readSaved(id) {
  try {
    const record = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}")[id];
    return record && Array.isArray(record.questions) && record.questions.length && record.questions.every(q => q && q.id && TYPES[q.type] && Array.isArray(q.type === "mcq" ? q.options : [])) ? record : null;
  } catch {
    return null;
  }
}
function loadExam(examId, state) {
  const saved = readSaved(examId);
  let sessionExam = null;
  try {
    sessionExam = JSON.parse(window.sessionStorage.getItem(`dbcas-exam-preview:${examId}`) || "null");
  } catch {/* Storage may be unavailable. */}
  const exam = state?.exam?.id === examId ? state.exam : sessionExam?.id === examId ? sessionExam : saved || {
    id: examId,
    title: "Kiểm tra Cơ sở Dữ liệu Nâng cao",
    duration: 60,
    date: "",
    startTime: "",
    mcqCount: 10,
    sqlCount: 3,
    essayCount: 1
  };
  const questions = saved?.questions || buildQuestions(exam);
  return {
    ...exam,
    questions: questions.length ? questions : buildQuestions({
      mcqCount: 10,
      sqlCount: 3,
      essayCount: 1
    })
  };
}
function validateQuestion(question) {
  if (!question.topic.trim()) return "Vui lòng nhập chủ đề câu hỏi.";
  if (!question.prompt.trim()) return "Vui lòng nhập đề bài.";
  if (!Number.isFinite(Number(question.points)) || Number(question.points) <= 0 || Number(question.points) > 10) return "Điểm câu hỏi phải lớn hơn 0 và không vượt quá 10.";
  if (question.type === "mcq") {
    if (question.options.length < 2 || question.options.some(option => !option.text.trim())) return "Cần ít nhất hai phương án và không để trống nội dung.";
    if (!question.options.some(option => option.id === question.correctId)) return "Vui lòng chọn đáp án đúng.";
  } else if (!question.answer.trim()) return "Vui lòng nhập đáp án tham khảo.";
  return "";
}
function getRubricItems(question) {
  if (Array.isArray(question.rubricItems)) return question.rubricItems;
  const matches = [...String(question.rubric || "").matchAll(/([^:]+):\s*(\d+(?:[.,]\d+)?)\s*điểm/g)];
  if (matches.length) return matches.map((match, index) => ({
    id: `rubric-${index}`,
    title: match[1].replace(/^[.\s]+/, "").trim(),
    points: Number(match[2].replace(",", ".")),
    description: ""
  }));
  return [{
    id: "rubric-0",
    title: question.rubric || "Tiêu chí chấm điểm",
    points: Number(question.points) || 3,
    description: ""
  }];
}
function getKeywords(question) {
  if (Array.isArray(question.keywords)) return question.keywords;
  if (question.type === "sql") {
    const words = String(question.answer || "").toUpperCase().match(/\b(?:SELECT|FROM|WHERE|JOIN|GROUP BY|HAVING|ORDER BY|WITH|SUM|COUNT|DENSE_RANK|EXTRACT)\b/g) || [];
    return [...new Set(words)];
  }
  return [];
}
function KeywordsEditor({
  question,
  onChange
}) {
  const [newWord, setNewWord] = useState("");
  const [adding, setAdding] = useState(false);
  const words = getKeywords(question);
  function add() {
    const value = newWord.trim();
    if (!value) return;
    if (!words.some(word => word.toLowerCase() === value.toLowerCase())) onChange([...words, value]);
    setNewWord("");
    setAdding(false);
  }
  return <section className="review-keywords-card">
    <div className="review-section-line"><span>◇ {adminRender(question.type === "sql" ? "Từ khóa bắt buộc (Keywords bắt buộc trong câu lệnh SQL để chấm điểm):" : "Từ khóa bắt buộc (Keywords để đối chiếu nội dung bài làm):")}</span>
      <button type="button" onClick={() => setAdding(!adding)}>{adminText("⊕ Thêm từ khóa bắt buộc")}</button>
    </div>
    <div className="review-keywords-list">{adminRender(words.map(word => <span className="review-keyword" key={word}>{adminRender(word)}<button type="button" aria-label={`Xóa từ khóa ${word}`} onClick={() => onChange(words.filter(item => item !== word))}>{adminText("×")}</button></span>))}
      {adminRender(!words.length && <small>{adminText("Chưa có từ khóa.")}</small>)}
    </div>
    {adminRender(adding && <div className="review-keyword-add"><input autoFocus aria-label={adminText("Từ khóa mới")} value={newWord} placeholder={adminText("Nhập từ khóa...")} onChange={event => setNewWord(event.target.value)} onKeyDown={event => {
        if (event.key === "Enter") {
          event.preventDefault();
          add();
        }
      }} /><button type="button" onClick={add}>{adminText("Thêm")}</button></div>)}
    <p>{adminRender(question.type === "sql" ? "Các từ khóa dùng để đối chiếu cú pháp và nội dung truy vấn khi chấm bài." : "Các từ khóa dùng để đối chiếu các ý cần có trong bài tự luận.")}</p>
  </section>;
}
function Icon({
  name
}) {
  const paths = {
    back: "m14 6-6 6 6 6M8 12h12",
    save: "M4 3h13l4 4v14H3V3zM7 3v7h10V3M7 21v-7h10v7",
    list: "M8 6h13M8 12h13M8 18h13M3 6h1M3 12h1M3 18h1",
    plus: "M12 5v14M5 12h14",
    reset: "M3 10a9 9 0 1 1 2 8M3 4v6h6",
    trash: "M3 6h18M8 6V3h8v3M6 6l1 15h10l1-15M10 10v7M14 10v7",
    next: "M4 12h16m-6-6 6 6-6 6",
    clock: "M12 7v5l3 2M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18"
  };
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name] || paths.list} /></svg>;
}
export default function XemLaiBaiKiemTraAdmin() {
  useAdminLanguage();

  const {
    examId
  } = useParams();
  const location = useLocation();
  // Remount when opening a different exam ID so no edits leak between exams.
  return <ExamEditor key={examId} examId={examId} routeState={location.state} />;
}
function ExamEditor({
  examId,
  routeState
}) {
  const navigate = useNavigate();
  const [exam] = useState(() => loadExam(examId, routeState));
  const [questions, setQuestions] = useState(() => clone(exam.questions));
  const [savedQuestions, setSavedQuestions] = useState(() => clone(exam.questions));
  const [activeId, setActiveId] = useState(exam.questions[0]?.id);
  const [tab, setTab] = useState("all");
  const [notice, setNotice] = useState("");
  const [deleteId, setDeleteId] = useState(null);
  useEffect(() => {
    try {
      const {
        questions: ignoredQuestions,
        ...metadata
      } = exam;
      window.sessionStorage.setItem(`dbcas-exam-preview:${examId}`, JSON.stringify(metadata));
    } catch {/* Editing still works when session storage is unavailable. */}
  }, [exam, examId]);
  useEffect(() => {
    if (!deleteId) return;
    const handleEscape = event => {
      if (event.key === "Escape") setDeleteId(null);
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [deleteId]);
  const visible = questions.filter(q => tab === "all" || q.type === tab);
  const current = visible.find(q => q.id === activeId) || visible[0];
  const index = current ? questions.findIndex(q => q.id === current.id) : -1;
  const dirty = JSON.stringify(questions) !== JSON.stringify(savedQuestions);
  const totalPoints = useMemo(() => questions.reduce((sum, q) => sum + (Number(q.points) || 0), 0), [questions]);
  useEffect(() => {
    function warn(event) {
      if (dirty) {
        event.preventDefault();
        event.returnValue = "";
      }
    }
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  function update(patch) {
    setQuestions(previous => previous.map(q => q.id === current.id ? {
      ...q,
      ...patch
    } : q));
  }
  function persist(nextQuestions) {
    const existing = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
    if (!existing || typeof existing !== "object" || Array.isArray(existing)) throw new Error("Dữ liệu lưu trên trình duyệt không hợp lệ.");
    const counts = Object.fromEntries(Object.keys(TYPES).map(type => [`${type}Count`, nextQuestions.filter(q => q.type === type).length]));
    existing[examId] = {
      id: examId,
      title: exam.title,
      date: exam.date,
      startTime: exam.startTime,
      duration: exam.duration,
      ...counts,
      questions: nextQuestions,
      updatedAt: new Date().toISOString()
    };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(existing));
    setSavedQuestions(clone(nextQuestions));
  }
  function saveAll() {
    const confirmed = window.confirm(adminText("Bạn đã chỉnh sửa xong bài kiểm tra và muốn lưu rồi thoát chưa?\n\nChọn OK để lưu và quay lại. Chọn Hủy để tiếp tục chỉnh sửa."));
    if (!confirmed) return;
    const invalidIndex = questions.findIndex(q => validateQuestion(q));
    if (invalidIndex !== -1) {
      setTab("all");
      setActiveId(questions[invalidIndex].id);
      setNotice(adminText(`Câu ${invalidIndex + 1}: ${validateQuestion(questions[invalidIndex])}`));
      return;
    }
    try {
      persist(questions);
      navigate("/Quan_ly_bai_kiem_tra_Admin");
    } catch (error) {
      setNotice(error.message || "Không thể lưu thay đổi.");
    }
  }
  function saveCurrent(goNext = false) {
    if (!current) return;
    const error = validateQuestion(current);
    if (error) {
      setNotice(error);
      return;
    }
    const structural = questions.map(q => q.id).join("|") !== savedQuestions.map(q => q.id).join("|");
    if (structural && questions.some(q => validateQuestion(q))) {
      setNotice(adminText("Có câu hỏi chưa hoàn thiện. Vui lòng hoàn thiện các câu trước khi lưu."));
      return;
    }
    const next = structural ? questions : savedQuestions.map(q => q.id === current.id ? clone(current) : q);
    try {
      persist(next);
      setNotice(adminText("Đã lưu thay đổi trên trình duyệt."));
      if (goNext) {
        const position = visible.findIndex(q => q.id === current.id);
        if (visible[position + 1]) setActiveId(visible[position + 1].id);
      }
    } catch (error) {
      setNotice(error.message || "Không thể lưu câu hỏi.");
    }
  }
  function saveAllStay() {
    const invalidIndex = questions.findIndex(q => validateQuestion(q));
    if (invalidIndex !== -1) {
      setTab("all");
      setActiveId(questions[invalidIndex].id);
      setNotice(adminText(`Câu ${invalidIndex + 1}: ${validateQuestion(questions[invalidIndex])}`));
      return;
    }
    try {
      persist(questions);
      setNotice(adminText("Đã lưu tất cả thay đổi trên trình duyệt."));
    } catch (error) {
      setNotice(error.message || "Không thể lưu thay đổi.");
    }
  }
  function restore() {
    const saved = savedQuestions.find(q => q.id === current.id);
    if (!saved) {
      setNotice(adminText("Câu hỏi mới chưa có bản lưu để khôi phục."));
      return;
    }
    setQuestions(previous => previous.map(q => q.id === current.id ? clone(saved) : q));
    setNotice(adminText("Đã khôi phục câu hỏi về bản lưu gần nhất."));
  }
  function addQuestion() {
    const type = tab === "all" ? current?.type || "mcq" : tab;
    const id = `new-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const question = {
      id,
      type,
      topic: "",
      prompt: "",
      points: type === "mcq" ? 0.4 : type === "sql" ? 1 : 3
    };
    if (type === "mcq") {
      question.options = ["A", "B", "C", "D"].map(letter => ({
        id: `${id}-${letter}`,
        text: ""
      }));
      question.correctId = "";
    } else {
      question.answer = "";
      if (type === "sql") question.schema = "";else question.rubric = "";
    }
    setQuestions(previous => [...previous, question]);
    setActiveId(id);
  }
  function removeQuestion() {
    const next = questions.filter(q => q.id !== deleteId);
    setQuestions(next);
    setActiveId(next[Math.min(index, next.length - 1)]?.id);
    setDeleteId(null);
  }
  function back() {
    if (dirty && !window.confirm(adminText("Có thay đổi chưa lưu. Bạn muốn quay lại và bỏ các thay đổi này?"))) return;
    navigate("/Quan_ly_bai_kiem_tra_Admin");
  }
  const displayDate = exam.date && /^\d{4}-\d{2}-\d{2}$/.test(exam.date) ? exam.date.split("-").reverse().join("/") : "Chưa xếp lịch";
  const duration = Number(exam.duration) || 60;
  const startMinutes = /^\d{2}:\d{2}$/.test(exam.startTime || "") ? Number(exam.startTime.slice(0, 2)) * 60 + Number(exam.startTime.slice(3)) : null;
  const endMinutes = startMinutes === null ? null : startMinutes + duration;
  const endTime = endMinutes === null ? "" : `${String(Math.floor(endMinutes / 60) % 24).padStart(2, "0")}:${String(endMinutes % 60).padStart(2, "0")}${endMinutes >= 1440 ? " (+1 ngày)" : ""}`;
  return <div className="dbcas-admin-home dbcas-exam-review" style={{
    backgroundImage: `linear-gradient(rgba(7,11,20,.8),rgba(7,11,20,.8)),url(${background})`
  }}>
    <header className="review-topbar admin-unified-topbar"><NotificationMenu role="admin" className="icon-button" /><div className="review-breadcrumb"><Icon name="list" /><span>DBCAS Admin</span><span>/</span><button type="button" onClick={back}>{adminText("Quản lý bài kiểm tra")}</button><span>/</span><strong>{adminText("Xem lại bài kiểm tra")}</strong></div>
      <div className="review-top-actions"><button type="button" className="review-primary" onClick={saveAllStay}><Icon name="save" />{adminText("Lưu tất cả thay đổi")}</button><button type="button" onClick={back}><Icon name="back" />{adminText("Quay lại")}</button></div>
    <AdminAccountMenu /></header>
    <main className="review-main">
      <section className="review-banner admin-unified-banner"><h1>{adminRender(exam.title)}</h1><div className="review-exam-meta"><span><Icon name="list" />{adminText("Tổng: ")}<strong>{adminRender(questions.length)}{adminText(" câu hỏi (")}{adminRender(totalPoints.toFixed(1))}{adminText(" điểm)")}</strong></span><span><Icon name="clock" />{adminText("Thời gian: ")}{adminRender(duration)}{adminText(" phút")}</span><span>{adminText("Lịch thi: ")}{adminRender(startMinutes !== null ? `${exam.startTime} – ${endTime}, ` : "")}{adminRender(displayDate)}</span></div></section>
      <div className="review-layout">
        <aside className="review-question-list"><div className="review-list-heading"><h2><Icon name="list" />{adminText("Mục lục câu hỏi")}</h2><small>{adminRender(questions.length)}{adminText(" câu · ")}{adminRender(totalPoints.toFixed(1))}{adminText("đ")}</small></div>
          <div className="review-tabs" role="tablist" aria-label={adminText("Loại câu hỏi")}>{adminRender([["all", "Tất cả"], ["mcq", "TN"], ["sql", "SQL"], ["essay", "Tự luận"]].map(([type, label]) => <button type="button" role="tab" aria-selected={tab === type} key={type} className={tab === type ? "active" : ""} onClick={() => setTab(type)}>{adminRender(label)} ({adminRender(type === "all" ? questions.length : questions.filter(q => q.type === type).length)})</button>))}</div>
          <button className="review-add-question" type="button" onClick={addQuestion}><Icon name="plus" />{adminText("Thêm câu hỏi mới")}</button>
          <div className="review-list-scroll">{adminRender(Object.entries(TYPES).map(([type, label]) => {
              const items = visible.filter(q => q.type === type);
              if (!items.length) return null;
              return <section key={type}><div className="review-group-heading"><span>{adminText("PHẦN: ")}{adminRender(label.toUpperCase())} ({adminRender(items.length)}{adminText(" CÂU)")}</span><span>{adminRender(items.reduce((sum, q) => sum + (Number(q.points) || 0), 0).toFixed(1))}{adminText("đ")}</span></div>
              {adminRender(items.map(q => {
                  const number = questions.findIndex(item => item.id === q.id) + 1;
                  const changed = JSON.stringify(q) !== JSON.stringify(savedQuestions.find(item => item.id === q.id));
                  return <button type="button" key={q.id} className={`review-question-item${current?.id === q.id ? " selected" : ""}`} onClick={() => setActiveId(q.id)} aria-current={current?.id === q.id ? "true" : undefined}>
                  <span className="review-question-item-heading"><b>{adminRender(String(number).padStart(2, "0"))}</b><strong>{adminRender(q.topic || "Chưa nhập chủ đề")}</strong><small>{adminRender(Number(q.points || 0).toFixed(1))}{adminText("đ")}</small></span><span className="review-question-preview">{adminRender(q.prompt || "Chưa nhập đề bài")}</span><span className="review-item-status">{adminRender(changed ? "Chưa lưu" : "Đã lưu")}</span>
                </button>;
                }))}</section>;
            }))}{adminRender(!visible.length && <p className="review-empty">{adminText("Chưa có câu hỏi thuộc loại này.")}</p>)}</div>
        </aside>
        <section className="review-editor" aria-label={adminText("Nội dung câu hỏi")}>{adminRender(current ? <>
          <div className="review-editor-heading"><span className="review-question-number">{adminRender(String(index + 1).padStart(2, "0"))}</span><div><small>{adminText("PHẦN · ")}{adminRender(TYPES[current.type].toUpperCase())}</small><h2>{adminText("CÂU ")}{adminRender(String(index + 1).padStart(2, "0"))}: {adminRender(current.topic || "CÂU HỎI MỚI")}</h2></div><div className="review-question-actions"><button type="button" onClick={restore}><Icon name="reset" />{adminText("Khôi phục")}</button><button type="button" className="review-danger" disabled={questions.length <= 1} onClick={() => setDeleteId(current.id)}><Icon name="trash" />{adminText("Xóa câu")}</button></div></div>
          <div className="review-editor-body"><div className="review-question-meta"><label>{adminText("CHỦ ĐỀ CÂU HỎI")}<input aria-label={adminText("Chủ đề câu hỏi")} value={current.topic} onChange={event => update({
                    topic: event.target.value
                  })} /></label><label>{adminText("ĐIỂM SỐ CÂU HỎI")}<div><input aria-label={adminText("Điểm số câu hỏi")} type="number" min="0.01" max="10" step="any" value={current.points} onChange={event => update({
                      points: event.target.value === "" ? "" : Number(event.target.value)
                    })} /><span>{adminText("điểm")}</span></div></label></div>
            <label className="review-field"><span>{adminRender(current.type === "sql" ? "Đề bài câu hỏi (Problem Statement):" : "Đề bài:")}</span><textarea rows={4} value={current.prompt} onChange={event => update({
                  prompt: event.target.value
                })} /></label>
            {adminRender(current.type === "mcq" ? <div className="review-options"><div className="review-options-heading"><span>{adminText("Phương án trả lời (Chọn radio để đánh dấu đáp án đúng):")}</span><button type="button" disabled={current.options.length >= 8} onClick={() => update({
                    options: [...current.options, {
                      id: `option-${Date.now()}-${Math.random().toString(36).slice(2)}`,
                      text: ""
                    }]
                  })}><Icon name="plus" />{adminText("Thêm phương án")}</button></div>
              {adminRender(current.options.map((option, optionIndex) => <div key={option.id} className={`review-option${current.correctId === option.id ? " correct" : ""}`}><input type="radio" name={`answer-${current.id}`} aria-label={`Chọn đáp án ${String.fromCharCode(65 + optionIndex)} là đúng`} checked={current.correctId === option.id} onChange={() => update({
                    correctId: option.id
                  })} /><b>{adminRender(String.fromCharCode(65 + optionIndex))}.</b><input type="text" aria-label={`Nội dung phương án ${String.fromCharCode(65 + optionIndex)}`} value={option.text} onChange={event => update({
                    options: current.options.map(item => item.id === option.id ? {
                      ...item,
                      text: event.target.value
                    } : item)
                  })} />{adminRender(current.correctId === option.id ? <span className="review-answer-badge">{adminText("ĐÁP ÁN ĐÚNG")}</span> : <span className="review-answer-wrong">Sai</span>)}<button type="button" className="review-delete-option" aria-label={`Xóa phương án ${String.fromCharCode(65 + optionIndex)}`} disabled={current.options.length <= 2} onClick={() => update({
                    options: current.options.filter(item => item.id !== option.id),
                    correctId: current.correctId === option.id ? "" : current.correctId
                  })}><Icon name="trash" /></button></div>))}
            </div> : current.type === "sql" ? <div className="review-sql-content">
              <div className="review-section-line"><span>{adminText("▣ Thử nghiệm trên Sandbox")}</span>
                <button className="review-sandbox-button" type="button" onClick={() => setNotice(adminText("Chức năng chạy truy vấn sẽ hoạt động khi kết nối SQL Sandbox."))}>{adminText("▷ Chạy thử nghiệm trên Sandbox")}</button>
              </div>
              <div className="review-code-window"><div className="review-code-window-title"><span className="review-code-dots"><i /><i /><i /></span><strong>PostgreSQL 16 Reference Solution</strong></div>
                <label className="review-field review-code-field"><span className="review-sr-only">{adminText("Truy vấn đáp án SQL")}</span><textarea spellCheck={false} className="review-code" rows={Math.max(10, String(current.answer).split("\n").length + 2)} value={current.answer} onChange={event => update({
                      answer: event.target.value
                    })} /></label>
              </div>
              <KeywordsEditor key={current.id} question={current} onChange={keywords => update({
                  keywords
                })} />
            </div> : <div className="review-essay-content">
              <div className="review-section-line"><span>{adminText("▤ Tiêu chuẩn chấm điểm")}</span><button type="button" onClick={() => {
                    const items = [...getRubricItems(current), {
                      id: `rubric-${Date.now()}`,
                      title: "Tiêu chí mới",
                      description: "",
                      points: 0
                    }];
                    update({
                      rubricItems: items,
                      rubric: items.map(item => `${item.title}: ${item.points} điểm`).join(". ")
                    });
                  }}>{adminText("⊕ Thêm tiêu chí chấm")}</button></div>
              <div className="review-rubric-list">{adminRender(getRubricItems(current).map((item, itemIndex, items) => <div className="review-rubric-row" key={item.id}>
                <span className="review-rubric-marker">▣</span><div className="review-rubric-text"><input aria-label={`Tên tiêu chí ${itemIndex + 1}`} value={item.title} onChange={event => {
                        const updated = items.map(row => row.id === item.id ? {
                          ...row,
                          title: event.target.value
                        } : row);
                        update({
                          rubricItems: updated,
                          rubric: updated.map(row => `${row.title}: ${row.points} điểm`).join(". ")
                        });
                      }} /><input className="review-rubric-description" aria-label={`Mô tả tiêu chí ${itemIndex + 1}`} value={item.description || ""} placeholder={adminText("Nội dung cần đạt ở tiêu chí này...")} onChange={event => update({
                        rubricItems: items.map(row => row.id === item.id ? {
                          ...row,
                          description: event.target.value
                        } : row)
                      })} /></div>
                <label className="review-rubric-points"><input aria-label={`Điểm tiêu chí ${itemIndex + 1}`} type="number" min="0" max="10" step="0.1" value={item.points} onChange={event => {
                        const updated = items.map(row => row.id === item.id ? {
                          ...row,
                          points: event.target.value === "" ? "" : Number(event.target.value)
                        } : row);
                        update({
                          rubricItems: updated,
                          rubric: updated.map(row => `${row.title}: ${row.points} điểm`).join(". ")
                        });
                      }} /><span>{adminText("điểm")}</span></label><button type="button" className="review-rubric-delete" aria-label={`Xóa tiêu chí ${itemIndex + 1}`} disabled={items.length <= 1} onClick={() => {
                      const updated = items.filter(row => row.id !== item.id);
                      update({
                        rubricItems: updated,
                        rubric: updated.map(row => `${row.title}: ${row.points} điểm`).join(". ")
                      });
                    }}><Icon name="trash" /></button>
              </div>))}</div>
              <div className="review-section-line review-answer-title"><span>{adminText("▣ Đáp án mẫu / Hướng dẫn chấm")}</span><span className="review-rubric-total">{adminText("Tổng tiêu chí: ")}{adminRender(getRubricItems(current).reduce((sum, item) => sum + (Number(item.points) || 0), 0).toFixed(1))}{adminText(" điểm")}</span></div>
              <label className="review-field review-essay-answer"><span className="review-sr-only">{adminText("Đáp án mẫu hoặc hướng dẫn chấm tự luận")}</span><textarea spellCheck={false} className="review-code" rows={16} value={current.answer} onChange={event => update({
                    answer: event.target.value
                  })} /></label>

            </div>)}
          </div>
          <div className="review-editor-footer"><button type="button" disabled={visible.findIndex(q => q.id === current.id) <= 0} onClick={() => setActiveId(visible[visible.findIndex(q => q.id === current.id) - 1].id)}><Icon name="back" />{adminText("Câu trước (")}{adminRender(index + 1)}/{adminRender(questions.length)})</button><div><button type="button" className="review-save-one" onClick={() => saveCurrent()}><Icon name="save" />{adminText("Lưu thay đổi câu này")}</button><button type="button" className="review-primary" onClick={() => current.type === "essay" ? saveAll() : saveCurrent(true)}>{adminRender(current.type === "essay" ? "Lưu bài" : "Lưu & sang câu tiếp theo")}<Icon name={current.type === "essay" ? "save" : "next"} /></button></div></div>
        </> : <p className="review-empty">{adminText("Chọn loại câu hỏi khác hoặc thêm câu hỏi mới.")}</p>)}</section>
      </div>
    </main>
    {adminRender(notice && <div className="review-notice" role="status"><span>{adminRender(notice)}</span><button type="button" aria-label={adminText("Đóng thông báo")} onClick={() => setNotice(adminText(""))}>{adminText("×")}</button></div>)}
    {adminRender(deleteId && <div className="review-modal-backdrop"><div className="review-delete-dialog" role="dialog" aria-modal="true" aria-labelledby="review-delete-title"><h2 id="review-delete-title">{adminText("Xóa câu hỏi?")}</h2><p>{adminText("Câu hỏi sẽ được bỏ khỏi đề sau khi bạn lưu thay đổi.")}</p><div><button type="button" autoFocus onClick={() => setDeleteId(null)}>{adminText("Hủy bỏ")}</button><button type="button" className="review-danger" onClick={removeQuestion}>{adminText("Xóa câu")}</button></div></div></div>)}
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