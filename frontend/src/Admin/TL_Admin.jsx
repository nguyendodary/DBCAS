import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./TL_Admin.css";
// Điểm được cộng theo đơn vị 0.01 để tránh sai số số thực.
const DRAFT_KEYS = {tn:"dbcas_tn_admin_full_draft_v1",sql:"dbcas_sql_admin_draft_v1",tl:"dbcas_tl_admin_draft_v1"};
function readStoredDraft(key){try{return JSON.parse(sessionStorage.getItem(key));}catch{return null;}}
function pointValue(value,fallback=0){const number=Number(value??fallback);return Number.isFinite(number)&&number>=0 ? Math.round(number*100)/100 : 0;}
function validPoints(value,fallback=0){return String(value??fallback).trim()!==""&&Number.isFinite(Number(value??fallback))&&Number(value??fallback)>0;}
function questionScore(q,section){
 if(section==="tl")return (Array.isArray(q?.criteria)?q.criteria:[]).reduce((sum,item)=>sum+Math.round(pointValue(item?.points)*100),0)/100;
 return pointValue(q?.points,section==="tn" ? .4 : 1);
}
function sectionSummary(draft,section){const questions=Array.isArray(draft?.questions)?draft.questions:[];return {count:questions.length,points:questions.reduce((sum,q)=>sum+Math.round(questionScore(q,section)*100),0)/100};}
function examSummary(section,current){
 const result={};for(const type of ["tn","sql","tl"])result[type]=sectionSummary(type===section?current:readStoredDraft(DRAFT_KEYS[type]),type);
 result.total=(Math.round(result.tn.points*100)+Math.round(result.sql.points*100)+Math.round(result.tl.points*100))/100;
 result.count=result.tn.count+result.sql.count+result.tl.count;return result;
}
function fmtPoints(value){return pointValue(value).toFixed(2);}


const TN_KEY = "dbcas_tn_admin_full_draft_v1";
const SQL_KEY = "dbcas_sql_admin_draft_v1";
const TL_KEY = "dbcas_tl_admin_draft_v1";
const EXAM_KEY = "dbcas_admin_completed_exam_v1";
const DEFAULT_QUESTIONS = [{
  title: "Kiến trúc Sharding & Phân tán CSDL",
  description: "Phân tích giải pháp mở rộng quy mô (Horizontal Partitioning vs Sharding) cho hệ thống thương mại điện tử 50 triệu người dùng. Đề xuất chiến lược chọn Shard Key phù hợp, giải quyết bài toán Data Skew và cơ chế đảm bảo tính toàn vẹn giao dịch phân tán (2-Phase Commit / Sagas pattern).",
  answer: "1. So sánh Partitioning & Sharding: Partitioning chia bảng logic cùng server; Sharding phân tán vật lý độc lập (scale-out).\n\n2. Chọn Shard Key: Dựa vào tần suất truy vấn chính (User_ID), giải quyết Data Skew bằng Salting/Virtual Shards.\n\n3. Giao dịch phân tán: Phân tích đánh đổi giữa 2-Phase Commit (ACID) và Sagas Pattern.",
  criteria: [
    { title: "Kiến trúc B-Tree & Indexing", points: 1 },
    { title: "Tối ưu I/O & Sharding", points: 1 },
    { title: "Giải pháp ACID & Lock", points: 1 },
  ],
}];
function readDraft(key) {
  try { return JSON.parse(sessionStorage.getItem(key)); } catch { return null; }
}
function safePoints(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.round(number * 100) / 100) : 0;
}
function normalizeQuestion(source) {
  const q = source && typeof source === "object" ? source : {};
  return {
    title: String(q.title || ""), description: String(q.description || ""),
    answer: String(q.answer || ""),
    criteria: Array.isArray(q.criteria) ? q.criteria.map(item => ({
      title: String(item?.title || ""), points: safePoints(item?.points),
    })) : [],
  };
}
function initialDraft() {
  const tn = readDraft(TN_KEY), sql = readDraft(SQL_KEY), saved = readDraft(TL_KEY);
  const course = { testName: "Kiểm tra Cơ sở Dữ liệu Nâng cao", major: "Ngành Công nghệ phần mềm", schoolYear: "2024 - 2025", duration: 60 };
  // TN/SQL đã lưu học phần ở cấp gốc. Hỗ trợ cả cấu trúc course của HTML cũ.
  // SQL là bước trước TL nên ưu tiên học phần mới nhất từ SQL khi quay lại.
  for (const draft of [saved, tn, sql]) {
    const source = draft?.course || draft;
    if (!source) continue;
    for (const key of ["testName", "major", "schoolYear"]) {
      if (typeof source[key] === "string") course[key] = source[key];
    }
    if (Number.isFinite(source.duration)) course.duration = Math.max(10, Math.min(120, Math.round(source.duration)));
  }
  const questions = (Array.isArray(saved?.questions) && saved.questions.length ? saved.questions : DEFAULT_QUESTIONS).map(normalizeQuestion);
  return { course, questions, selectedIndex: Math.max(0, Math.min(questions.length - 1, Number.isInteger(saved?.selectedIndex) ? saved.selectedIndex : 0)) };
}
function questionPoints(q) { return questionScore(q,"tl"); }
function complete(q) {
  return Boolean(q.title.trim() && q.description.trim() && q.answer.trim() && q.criteria.length && q.criteria.every(item => item.title.trim() && safePoints(item.points) > 0));
}
function mcqComplete(q) {
  return Boolean(q && typeof q.title === "string" && q.title.trim() && typeof q.content === "string" && q.content.trim() && Array.isArray(q.answers) && q.answers.length >= 2 && q.answers.every(a => typeof a === "string" && a.trim()) && Number.isInteger(q.correct) && q.correct >= 0 && q.correct < q.answers.length && validPoints(q.points,.4));
}
function sqlComplete(q) {
  return Boolean(q && ["title", "description", "sql"].every(key => typeof q[key] === "string" && q[key].trim()) && validPoints(q.points,1));
}
function validateExam(tn, sql, essay) {
  if (!Array.isArray(tn?.questions) || !tn.questions.length || !tn.questions.every(mcqComplete)) return "Phần trắc nghiệm chưa soạn đủ hoặc điểm câu không hợp lệ. Quay lại TN để kiểm tra.";
  if (!Array.isArray(sql?.questions) || !sql.questions.length || !sql.questions.every(sqlComplete)) return "Phần SQL chưa soạn đủ hoặc điểm câu không hợp lệ. Quay lại SQL để kiểm tra.";
  if (!essay.questions.every(complete)) return "Nhập đủ tên, đề bài, đáp án mẫu và tiêu chí có điểm lớn hơn 0 cho từng câu tự luận.";
  return "";
}
const ICON_PATHS = {
  back: "M12 5 5 12l7 7M5 12h14", left: "m15 6-6 6 6 6", right: "m9 6 6 6-6 6",
  plus: "M12 5v14M5 12h14", clock: "M12 7v5l3 2", user: "M4 21v-2a8 8 0 0 1 16 0v2",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
  help: "M9.5 9a2.5 2.5 0 1 1 4 2c-1 .6-1.5 1-1.5 2M12 17h.01",
  book: "M12 5v15M12 5C8 2 4 3 2 4v15c3-1 6-1 10 1 4-2 7-2 10-1V4c-2-1-6-2-10 1Z",
  file: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8ZM14 2v6h6M8 12h8M8 16h6",
  chart: "M4 3v18h17M8 16v-5M13 16V7M18 16v-8", check: "m5 12 4 4L19 6",
  edit: "m16 3 5 5-12 12-6 1 1-6ZM14 5l5 5",
  trash: "M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7",
  list: "M9 6h12M9 12h12M9 18h12M3 6h.01M3 12h.01M3 18h.01",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z",
  save: "M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h12l4 4v12a2 2 0 0 1-2 2ZM7 3v6h10V3M7 21v-8h10v8",
};
function Icon({ name }) {
  return <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
    {["clock", "help"].includes(name) && <circle cx="12" cy="12" r="9" />}
    {name === "user" && <circle cx="12" cy="8" r="4" />}
    {name === "eye" && <circle cx="12" cy="12" r="3" />}
    <path d={ICON_PATHS[name] || ICON_PATHS.file} />
  </svg>;
}
const MAJORS = ["Ngành Công nghệ phần mềm", "Ngành Hệ thống Thông tin Quản lý", "Ngành Khoa học Máy tính", "Ngành Kỹ thuật Phần mềm", "An ninh Mạng"];
const YEARS = ["2024 - 2025", "2025 - 2026", "2026 - 2027"];
// TODO BE: lấy/lưu đề, rubric và phát hành bài kiểm tra qua API.
// Bản hoàn tất dưới đây chỉ được lưu trên trình duyệt; chưa tạo đề cho Learner.
export default function TLAdmin({ tnHref = "/TN_Admin", sqlHref = "/SQL_Admin", managementHref = "/Quan_ly_de_thi", onFinish }) {
  const navigate = useNavigate();
  const [draft, setDraft] = useState(initialDraft);
  const [toast, setToast] = useState(""), [isError, setIsError] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);
  const [renameIndex, setRenameIndex] = useState(null), [renameTitle, setRenameTitle] = useState("");
  const [studentAnswer, setStudentAnswer] = useState(""), [finishing, setFinishing] = useState(false);
  const renameDialog = useRef(null), previewDialog = useRef(null), toastTimer = useRef(null), finishLock = useRef(false);
  const question = draft.questions[draft.selectedIndex];
  const scores=examSummary("tl",draft);
  useEffect(() => () => clearTimeout(toastTimer.current), []);
  function notify(message, error = false) {
    clearTimeout(toastTimer.current); setToast(message); setIsError(error);
    toastTimer.current = setTimeout(() => setToast(""), 4500);
  }
  function updateCourse(key, value) { setDraft(old => ({ ...old, course: { ...old.course, [key]: value } })); }
  function updateDuration(value) { if (String(value).trim() && Number.isFinite(Number(value))) updateCourse("duration", Math.max(10, Math.min(120, Math.round(Number(value))))); }
  function updateQuestion(patch) { setDraft(old => ({ ...old, questions: old.questions.map((q, i) => i === old.selectedIndex ? { ...q, ...patch } : q) })); }
  function selectQuestion(index) { setEditingIndex(null); setDraft(old => ({ ...old, selectedIndex: Math.max(0, Math.min(old.questions.length - 1, index)) })); }
  function addQuestion() {
    setDraft(old => ({ ...old, questions: [...old.questions, normalizeQuestion({})], selectedIndex: old.questions.length })); setEditingIndex(null);
  }
  function deleteQuestion(index) {
    if (draft.questions.length === 1) { notify("Cần giữ ít nhất một câu tự luận.", true); return; }
    setDraft(old => ({ ...old, questions: old.questions.filter((_, i) => i !== index), selectedIndex: Math.max(0, Math.min(old.questions.length - 2, old.selectedIndex - (index < old.selectedIndex ? 1 : 0))) })); setEditingIndex(null);
  }
  function openRename(index) { setRenameIndex(index); setRenameTitle(draft.questions[index].title); renameDialog.current?.showModal(); }
  function submitRename(event) {
    event.preventDefault(); if (!renameTitle.trim()) return;
    setDraft(old => ({ ...old, questions: old.questions.map((q, i) => i === renameIndex ? { ...q, title: renameTitle.trim() } : q) })); renameDialog.current?.close();
  }
  function updateCriterion(index, patch) { updateQuestion({ criteria: question.criteria.map((item, i) => i === index ? { ...item, ...patch } : item) }); }
  function addCriterion() { updateQuestion({ criteria: [...question.criteria, { title: "", points: 0 }] }); setEditingIndex(question.criteria.length); }
  function deleteCriterion(index) { updateQuestion({ criteria: question.criteria.filter((_, i) => i !== index) }); setEditingIndex(null); }
  function saveDraft(status = "draft") {
    try {
      sessionStorage.setItem(TL_KEY, JSON.stringify({ ...draft, questions: draft.questions.map(normalizeQuestion), status, savedAt: new Date().toISOString() }));
      for (const key of [TN_KEY, SQL_KEY]) {
        const old = readDraft(key);
        if (old && typeof old === "object" && !Array.isArray(old)) sessionStorage.setItem(key, JSON.stringify({ ...old, ...draft.course, ...(old.course ? { course: draft.course } : {}) }));
      }
      return true;
    } catch { notify("Không lưu đầy đủ được bản nháp. Hãy thử lại trước khi chuyển trang.", true); return false; }
  }
  function beforeNavigate(event) { if (!saveDraft()) event.preventDefault(); }
  async function finishExam() {
    if (finishLock.current) return;
    if (!draft.course.testName.trim()) { notify("Vui lòng nhập tên bài kiểm tra.", true); return; }
    const tn = readDraft(TN_KEY), sql = readDraft(SQL_KEY);
    const error = validateExam(tn, sql, draft);
    if (error) { const index = draft.questions.findIndex(q => !complete(q)); if (index >= 0) selectQuestion(index); notify(error, true); return; }
    const payload = {
      course: { ...draft.course, testName: draft.course.testName.trim() },
      mcq: tn.questions.map(q => ({ ...q, points: questionScore(q,"tn") })),
      sql: sql.questions.map(q => ({ ...q, points: questionScore(q,"sql") })),
      essay: draft.questions.map(q => ({ ...normalizeQuestion(q), points: questionPoints(q) })),
      totalPoints: examSummary("tl",draft).total, totalQuestions: examSummary("tl",draft).count, savedAt: new Date().toISOString(), status: "local-completed",
    };
    finishLock.current = true; setFinishing(true);
    try {
      if (!saveDraft("completed")) return;
      sessionStorage.setItem(EXAM_KEY, JSON.stringify(payload));
      if (onFinish) {
        // TODO BE: onFinish phải gửi API và trả { success: true } khi máy chủ đã lưu.
        const result = await onFinish(payload);
        if (result?.success !== true) throw new Error("Máy chủ chưa xác nhận lưu đề.");
        navigate(managementHref);
      } else {
        notify("Đã lưu đủ bộ đề trong trình duyệt. Chưa gửi BE hoặc phát hành cho Learner.");
      }
    } catch (error) { notify(error instanceof Error ? error.message : "Chưa lưu được bộ đề.", true); }
    finally { finishLock.current = false; setFinishing(false); }
  }
  return (
    <div className="dbcas-admin-essay">
      <header className="topbar">
        <div className="topbar-left">
          <Link className="back-button" to={sqlHref} onClick={beforeNavigate}><Icon name="back" />Quay lại</Link>
          <span className="divider" /><nav className="breadcrumb" aria-label="Đường dẫn"><span>Quản lý bài kiểm tra</span><span>/</span><strong>Tạo bài kiểm tra mới</strong></nav>
        </div>
        <div className="topbar-right">
          <button className="icon-button" type="button" aria-label="Trợ giúp" onClick={() => notify("Soạn đề, đáp án mẫu và tiêu chí. Điểm câu hỏi bằng tổng điểm các tiêu chí.")}><Icon name="help" /></button>
          <button className="icon-button notification-button" type="button" aria-label="Thông báo" onClick={() => notify("Bạn chưa có thông báo mới.")}><Icon name="bell" /><span className="notification-dot" /></button>
          <Link className="admin-profile" to="/Cai_dat_Admin"><span className="avatar"><Icon name="user" /><span className="online-dot" /></span><span className="admin-info"><strong>Admin DBCAS</strong><span>admin.dbcas@gmail.com</span></span></Link>
        </div>
      </header>
      <main className="page-layout">
        <aside className="sidebar">
          <section className="card course-card">
            <h2 className="section-title"><span className="title-icon"><Icon name="book" /></span>THÔNG TIN HỌC PHẦN</h2>
            <div className="form-field"><label htmlFor="tl-test-name">TÊN BÀI KIỂM TRA</label><input id="tl-test-name" value={draft.course.testName} onChange={e => updateCourse("testName", e.target.value)} /></div>
            <div className="form-field"><label htmlFor="tl-major">NGÀNH HỌC</label><select id="tl-major" value={draft.course.major} onChange={e => updateCourse("major", e.target.value)}>{[...new Set([...MAJORS, draft.course.major])].map(value => <option key={value}>{value}</option>)}</select></div>
            <div className="form-field"><label htmlFor="tl-year">NĂM HỌC</label><select id="tl-year" value={draft.course.schoolYear} onChange={e => updateCourse("schoolYear", e.target.value)}>{[...new Set([...YEARS, draft.course.schoolYear])].map(value => <option key={value}>{value}</option>)}</select></div>
            <div className="form-field">
              <div className="field-heading"><label htmlFor="tl-duration">THỜI GIAN LÀM BÀI</label><span className="time-value">{draft.course.duration} phút</span></div>
              <div className="duration-control"><button className="duration-button" type="button" disabled={draft.course.duration <= 10} aria-label="Giảm thời gian" onClick={() => updateDuration(draft.course.duration - 1)}>−</button><div className="duration-input"><Icon name="clock" /><input id="tl-duration" type="number" min="10" max="120" step="1" value={draft.course.duration} onChange={e => updateDuration(e.target.value)} /><span>phút</span></div><button className="duration-button" type="button" disabled={draft.course.duration >= 120} aria-label="Tăng thời gian" onClick={() => updateDuration(draft.course.duration + 1)}>+</button></div>
              <div className="duration-presets">{[45, 60, 90, 120].map(value => <button key={value} type="button" className={draft.course.duration === value ? "active" : ""} aria-pressed={draft.course.duration === value} onClick={() => updateDuration(value)}>{value}m</button>)}</div>
            </div>
          </section>
          <section className="card questions-card">
            <h2 className="section-title questions-heading"><Icon name="file" />CÂU TỰ LUẬN</h2>
            <ol className="question-list">{draft.questions.map((q, index) => <li key={index} className={`question-item${draft.selectedIndex === index ? " selected" : ""}`}>
              <button className="question-select" type="button" aria-pressed={draft.selectedIndex === index} onClick={() => selectQuestion(index)}><span className="question-number">{String(index + 1).padStart(2, "0")}</span><span className="question-info"><span className={`question-title${q.title ? "" : " placeholder"}`}>{q.title || "Nhập tên câu hỏi..."}</span><span className="question-points">{questionPoints(q).toFixed(2)} điểm</span></span></button>
              <div className="question-actions"><button className="small-button" type="button" aria-label={`Sửa tên câu ${index + 1}`} onClick={() => openRename(index)}><Icon name="edit" /></button><button className="small-button delete-button" type="button" aria-label={`Xóa câu ${index + 1}`} onClick={() => deleteQuestion(index)}><Icon name="trash" /></button><span className={`question-status${complete(q) ? " completed" : ""}`}>{draft.selectedIndex === index ? "ĐANG CHỌN" : complete(q) ? "ĐÃ XONG" : "BẢN NHÁP"}</span></div>
            </li>)}</ol>
            <button className="add-button" type="button" onClick={addQuestion}><Icon name="plus" />Thêm câu hỏi tự luận</button>
          </section>
        </aside>
        <div className="main-content">
          <section className="card score-card">
            <div className="score-card-heading"><h2 className="section-title"><Icon name="chart" />CẤU TRÚC ĐIỂM THI &amp; PHÂN BỔ CÂU HỎI</h2><div className="total-score">Tổng điểm:<strong>{fmtPoints(scores.total)} Điểm • {scores.count} câu</strong></div></div>
            <div className="score-grid">
<div className="score-item"><div className="score-heading"><strong>1. TRẮC NGHIỆM</strong><span className="score-points">{fmtPoints(scores.tn.points)} đ</span></div><p>{scores.tn.count} câu • Tổng {fmtPoints(scores.tn.points)} điểm</p><span className="score-status">{scores.tn.count ? "Đã lưu nháp" : "Chưa có nháp"}</span></div>
<div className="score-item"><div className="score-heading"><strong>2. TRUY VẤN SQL</strong><span className="score-points">{fmtPoints(scores.sql.points)} đ</span></div><p>{scores.sql.count} câu • Tổng {fmtPoints(scores.sql.points)} điểm</p><span className="score-status">{scores.sql.count ? "Đã lưu nháp" : "Chưa có nháp"}</span></div>
<div className="score-item active"><div className="score-heading"><strong>3. TỰ LUẬN CSDL</strong><span className="score-points">{fmtPoints(scores.tl.points)} đ</span></div><p>{scores.tl.count} câu • Tổng {fmtPoints(scores.tl.points)} điểm</p><span className="score-status">ĐANG SOẠN</span></div>
</div>
          </section>
          <section className="card editor-card">
            <header className="editor-heading"><div><span className="question-badge">CÂU {String(draft.selectedIndex + 1).padStart(2, "0")} / {String(draft.questions.length).padStart(2, "0")}</span><h1>{question.title || "Chưa đặt tên câu hỏi"}</h1></div><span className="point-badge">Điểm số: {questionPoints(question).toFixed(2)} điểm</span></header>
            <div className="editor-body">
              <section><label className="section-title" htmlFor="tl-description"><Icon name="file" />ĐỀ BÀI TỰ LUẬN</label><textarea id="tl-description" className="content-textarea" placeholder="Nhập đề bài tự luận..." value={question.description} onChange={e => updateQuestion({ description: e.target.value })} /></section>
              <section><label className="section-title accent-title" htmlFor="tl-answer"><Icon name="check" />ĐÁP ÁN MẪU &amp; HƯỚNG DẪN CHẤM</label><textarea id="tl-answer" className="content-textarea answer-textarea" placeholder="Nhập đáp án mẫu và hướng dẫn chấm..." value={question.answer} onChange={e => updateQuestion({ answer: e.target.value })} /></section>
              <section className="criteria-section">
                <div className="section-heading"><h2 className="section-title accent-title"><Icon name="list" />TIÊU CHÍ CHẤM ĐIỂM</h2><button className="small-add-button" type="button" onClick={addCriterion}><Icon name="plus" />Thêm tiêu chí</button></div>
                <div className="criteria-list">{question.criteria.length === 0 && <p className="empty-message">Chưa có tiêu chí. Bấm “Thêm tiêu chí” để bổ sung.</p>}{question.criteria.map((item, index) => <div key={`${draft.selectedIndex}:${index}`} className={`criterion-row${editingIndex === index ? " editing" : ""}`}>
                  <span className="criterion-number">{index + 1}</span>
                  {editingIndex === index ? <><input className="criterion-title-input" autoFocus value={item.title} placeholder="Nhập tên tiêu chí..." aria-label="Tên tiêu chí" onChange={e => updateCriterion(index, { title: e.target.value })} onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); setEditingIndex(null); } }} /><input className="criterion-points-input" type="number" min="0" step="0.01" value={item.points} aria-label="Điểm tiêu chí" onChange={e => updateCriterion(index, { points: e.target.value })} /></> : <><span className={`criterion-title${item.title ? "" : " placeholder"}`}>{item.title || "Nhập tên tiêu chí..."}</span><span className="criterion-points">{safePoints(item.points).toFixed(2)} đ</span></>}
                  <div className="criterion-actions"><button className="small-button" type="button" aria-label={editingIndex === index ? "Hoàn tất sửa tiêu chí" : "Sửa tiêu chí"} onClick={() => setEditingIndex(editingIndex === index ? null : index)}><Icon name={editingIndex === index ? "check" : "edit"} /></button><button className="small-button delete-button" type="button" aria-label="Xóa tiêu chí" onClick={() => deleteCriterion(index)}><Icon name="trash" /></button></div>
                </div>)}</div>
                <p className="criteria-note">Điểm câu hỏi bằng tổng điểm các tiêu chí. Tổng điểm đề được tự cộng từ TN, SQL và tự luận.</p>
              </section>
            </div>
          </section>
        </div>
      </main>
      <footer className="page-footer">
        <div className="footer-tools"><button className="button" type="button" onClick={() => { setStudentAnswer(""); previewDialog.current?.showModal(); }}><Icon name="eye" />Xem trước giao diện sinh viên</button><button className="button" type="button" onClick={() => saveDraft() && notify("Đã lưu bản nháp tự luận trong trình duyệt.")}><Icon name="save" />Lưu bản nháp</button></div>
        <div className="footer-navigation"><Link className="button" to={sqlHref} onClick={beforeNavigate}><Icon name="back" />Bài trước (SQL)</Link><button className="button" type="button" disabled={draft.selectedIndex === 0} onClick={() => selectQuestion(draft.selectedIndex - 1)}><Icon name="left" />Câu trước</button><span className="page-indicator">{draft.selectedIndex + 1} / {draft.questions.length}</span><button className="button" type="button" disabled={draft.selectedIndex === draft.questions.length - 1} onClick={() => selectQuestion(draft.selectedIndex + 1)}>Câu tiếp theo<Icon name="right" /></button><button className="button primary" type="button" disabled={finishing} onClick={finishExam}><Icon name="check" />{finishing ? "Đang lưu..." : "Lưu & Hoàn tất đề thi"}</button></div>
      </footer>
      <dialog className="dialog" ref={renameDialog}><form onSubmit={submitRename}><h2>Chỉnh sửa tên câu hỏi</h2><label htmlFor="tl-rename">Tên câu hỏi</label><input id="tl-rename" required maxLength={200} value={renameTitle} onChange={e => setRenameTitle(e.target.value)} /><div className="dialog-actions"><button className="button" type="button" onClick={() => renameDialog.current?.close()}>Hủy</button><button className="button primary" type="submit">Cập nhật</button></div></form></dialog>
      <dialog className="dialog preview-dialog" ref={previewDialog}><h2>Câu {draft.selectedIndex + 1}: {question.title || "Chưa đặt tên câu hỏi"}</h2><p className="preview-description">{question.description || "Chưa nhập đề bài."}</p><label htmlFor="tl-student-answer">Bài làm của sinh viên</label><textarea className="content-textarea" id="tl-student-answer" value={studentAnswer} onChange={e => setStudentAnswer(e.target.value)} placeholder="Nhập câu trả lời..." /><div className="dialog-actions"><button className="button" type="button" onClick={() => previewDialog.current?.close()}>Đóng</button></div></dialog>
      <div className={`toast${toast ? " show" : ""}${isError ? " error" : ""}`} role="status" aria-live="polite">{toast}</div>
    </div>
  );
}
