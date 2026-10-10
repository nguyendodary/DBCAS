import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./TN_Admin.css";
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


const DRAFT_KEY = "dbcas_tn_admin_full_draft_v1";
const sampleTitles = [
            "Khái niệm ACID & Giao dịch CSDL",
            "Khóa ngoại & Ràng buộc toàn vẹn cơ sở dữ liệu",
            "Index B-Tree và tối ưu truy vấn",
            "Mức độ cô lập Isolation Levels",
            "Tối ưu hóa cây thực thi Query Plan",
            "Khóa bi quan vs Lạc quan",
            "Kỹ thuật Sharding & Replication",
            "Nguyên lý Chuẩn hóa BCNF & 3NF",
            "View và Materialized View",
            "Deadlock & Giải thuật phát hiện"
        ];
        function emptyQuestion(title = "") {
            return {
                title,
                content: "",
                answers: ["", "", "", ""],
                correct: null,
                explanation: "",
                points: "0.4"
            };
        }
        const questions = sampleTitles.map((title) => emptyQuestion(title));
        questions[1] = {
            title: sampleTitles[1],
            content: "Viết truy vấn phân tích doanh số đơn hàng theo quý " +
                "sử dụng Recursive CTE và DENSE_RANK() để xếp hạng " +
                "top khách hàng VIP có tổng chi tiêu cao nhất qua " +
                "từng quý của năm tài chính 2023.",
            answers: [
                "Foreign Key Constraint kết hợp thuộc tính Referential Integrity",
                "Unique Index kết hợp Check Constraint độc lập",
                "Composite Primary Key kết hợp Clustered Index",
                "Trigger AFTER INSERT/UPDATE độc lập không qua định nghĩa Schema"
            ],
            correct: 0,
            explanation: "Ghi chú đối chiếu: Khóa ngoại (Foreign Key) thiết lập " +
                "ràng buộc toàn vẹn tham chiếu giữa hai bảng. Khi định " +
                "nghĩa thêm quy tắc hành động ON DELETE CASCADE, hệ " +
                "quản trị cơ sở dữ liệu sẽ tự động xóa tất cả các hàng " +
                "tương ứng ở bảng con khi bản ghi cha bị xóa, ngăn ngừa " +
                "tình trạng bản ghi mồ côi (orphaned records).",
            points: "1.0"
        };
function validQuestion(q) {
 return q && ["title","content","explanation"].every(key=>typeof q[key]==="string") && Array.isArray(q.answers) && q.answers.length>=2 && q.answers.length<=26 && q.answers.every(a=>typeof a==="string") && (q.correct===null || (Number.isInteger(q.correct)&&q.correct>=0&&q.correct<q.answers.length));
}
function initialDraft() {
 const fallback={testName:"Kiểm tra Cơ sở Dữ liệu Nâng cao",major:"Ngành Công nghệ phần mềm",schoolYear:"2024 - 2025",duration:60,selectedIndex:1,questions};
 try { const old=JSON.parse(sessionStorage.getItem(DRAFT_KEY));
 if(old && Array.isArray(old.questions)&&old.questions.length>0&&old.questions.every(validQuestion)) return {...fallback,...old,testName:typeof old.testName==="string" ? old.testName : fallback.testName,major:typeof old.major==="string" ? old.major : fallback.major,schoolYear:typeof old.schoolYear==="string" ? old.schoolYear : fallback.schoolYear,duration:Number.isFinite(old.duration)?Math.max(10,Math.min(120,Math.round(old.duration))):60,selectedIndex:Math.max(0,Math.min(old.questions.length-1,Number.isInteger(old.selectedIndex)?old.selectedIndex:0))};
 } catch { /* Bản nháp hỏng: hiển thị dữ liệu mẫu. */ }
 return fallback;
}
function Icon({name}) { return <svg className="icon" aria-hidden="true"><use href={`#tna-icon-${name}`} /></svg>; }
function complete(q) {return Boolean(q.title.trim()&&q.content.trim()&&q.answers.every(a=>a.trim())&&Number.isInteger(q.correct)&&validPoints(q.points,.4));}
// TODO BE: lấy/lưu đề qua API, kiểm tra quyền Admin và phát hành đề sau khi đủ ba phần.
// Hiện chỉ lưu nháp sessionStorage; chưa tạo bài kiểm tra trên máy chủ.
export default function TNAdmin({managementHref="/Quan_ly_de_thi",sqlHref="/SQL_Admin"}) {
 const navigate=useNavigate();
 const [draft,setDraft]=useState(initialDraft);
 const [toast,setToast]=useState(""),[editingAnswer,setEditingAnswer]=useState(null);
 const [renameIndex,setRenameIndex]=useState(null),[renameTitle,setRenameTitle]=useState("");
 const renameDialog=useRef(null),previewDialog=useRef(null),toastTimer=useRef(null);
 const question=draft.questions[draft.selectedIndex];
 const scores=examSummary("tn",draft);
 useEffect(()=>()=>clearTimeout(toastTimer.current),[]);
 function notify(message){clearTimeout(toastTimer.current);setToast(message);toastTimer.current=setTimeout(()=>setToast(""),3500);}
 function updateMeta(key,value){setDraft(old=>({...old,[key]:value}));}
 function updateDuration(value){const number=Number(value);if(Number.isFinite(number))updateMeta("duration",Math.max(10,Math.min(120,Math.round(number))));}
 function updateQuestion(patch){setDraft(old=>({...old,questions:old.questions.map((q,index)=>index===old.selectedIndex ? {...q,...patch} : q)}));}
 function selectQuestion(index){setEditingAnswer(null);updateMeta("selectedIndex",Math.max(0,Math.min(draft.questions.length-1,index)));}
 function addQuestion(){setDraft(old=>({...old,questions:[...old.questions,emptyQuestion("Câu hỏi mới")],selectedIndex:old.questions.length}));setEditingAnswer(null);}
 function deleteQuestion(index){if(draft.questions.length===1){notify("Phải giữ ít nhất một câu hỏi.");return;}setDraft(old=>({...old,questions:old.questions.filter((_,i)=>i!==index),selectedIndex:Math.max(0,Math.min(old.questions.length-2,old.selectedIndex-(index<old.selectedIndex?1:0)))}));setEditingAnswer(null);}
 function updateAnswer(index,value){updateQuestion({answers:question.answers.map((a,i)=>i===index?value:a)});}
 function addAnswer(){if(question.answers.length>=26){notify("Tối đa 26 phương án.");return;}updateQuestion({answers:[...question.answers,""]});setEditingAnswer(question.answers.length);}
 function deleteAnswer(index){if(question.answers.length<=2){notify("Phải giữ ít nhất hai phương án.");return;}updateQuestion({answers:question.answers.filter((_,i)=>i!==index),correct:question.correct===index ? null : Number.isInteger(question.correct)&&question.correct>index ? question.correct-1 : question.correct});setEditingAnswer(null);}
 function openRename(index){setRenameIndex(index);setRenameTitle(draft.questions[index].title);renameDialog.current?.showModal();}
 function submitRename(event){event.preventDefault();if(!renameTitle.trim())return;setDraft(old=>({...old,questions:old.questions.map((q,i)=>i===renameIndex ? {...q,title:renameTitle.trim()} : q)}));renameDialog.current?.close();}
 function saveDraft(){try{sessionStorage.setItem(DRAFT_KEY,JSON.stringify({...draft,questions:draft.questions.map(q=>({...q,points:questionScore(q,"tn")}))}));return true;}catch{notify("Không lưu được bản nháp trong trình duyệt.");return false;}}
 return <div className="dbcas-admin-mcq">
    <svg className="svg-library" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <defs>
            <symbol id="tna-icon-back" viewBox="0 0 24 24">
                <path d="m12 19-7-7 7-7M5 12h14"/>
            </symbol>
            <symbol id="tna-icon-next" viewBox="0 0 24 24">
                <path d="m12 5 7 7-7 7M5 12h14"/>
            </symbol>
            <symbol id="tna-icon-bell" viewBox="0 0 24 24">
                <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/>
                <path d="M10 21h4"/>
            </symbol>
            <symbol id="tna-icon-help" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9"/>
                <path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .7-1.5 1-1.5 2"/>
                <path d="M12 16h.01"/>
            </symbol>
            <symbol id="tna-icon-user" viewBox="0 0 24 24">
                <circle cx="12" cy="8" r="4"/>
                <path d="M4 21v-2a8 8 0 0 1 16 0v2"/>
            </symbol>
            <symbol id="tna-icon-book" viewBox="0 0 24 24">
                <path d="M12 5v15M12 5C8 2 4 3 2 4v15c3-1 7-1 10 1"/>
                <path d="M12 5c4-3 8-2 10-1v15c-3-1-7-1-10 1"/>
            </symbol>
            <symbol id="tna-icon-clock" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9"/>
                <path d="M12 7v5l3 2"/>
            </symbol>
            <symbol id="tna-icon-list" viewBox="0 0 24 24">
                <path d="M9 6h12M9 12h12M9 18h12"/>
                <path d="m3 6 1 1 2-2m-3 7 1 1 2-2m-3 7 1 1 2-2"/>
            </symbol>
            <symbol id="tna-icon-chart" viewBox="0 0 24 24">
                <path d="M4 3v17h17M8 16v-5m5 5V7m5 9V4"/>
            </symbol>
            <symbol id="tna-icon-edit" viewBox="0 0 24 24">
                <path d="m16 3 5 5-12 12-6 1 1-6Z"/>
                <path d="m14 5 5 5"/>
            </symbol>
            <symbol id="tna-icon-check" viewBox="0 0 24 24">
                <path d="m5 12 4 4L19 6"/>
            </symbol>
            <symbol id="tna-icon-plus" viewBox="0 0 24 24">
                <path d="M12 5v14M5 12h14"/>
            </symbol>
            <symbol id="tna-icon-trash" viewBox="0 0 24 24">
                <path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15"/>
                <path d="M10 10v7M14 10v7"/>
            </symbol>
            <symbol id="tna-icon-eye" viewBox="0 0 24 24">
                <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/>
                <circle cx="12" cy="12" r="3"/>
            </symbol>
            <symbol id="tna-icon-save" viewBox="0 0 24 24">
                <path d="M4 3h13l3 3v15H4Z"/>
                <path d="M8 3v6h8V3M8 21v-8h8v8"/>
            </symbol>
            <symbol id="tna-icon-light" viewBox="0 0 24 24">
                <path d="M9 18h6M10 21h4"/>
                <path d="M8 14a6 6 0 1 1 8 0c-1 1-1 2-1 4H9c0-2 0-3-1-4Z"/>
            </symbol>
            <symbol id="tna-icon-down" viewBox="0 0 24 24">
                <path d="m6 9 6 6 6-6"/>
            </symbol>
        </defs>
    </svg>
    <header className="topbar">
        <div className="topbar-left">
            <Link className="back-button" to={managementHref} onClick={event=>{if(!saveDraft())event.preventDefault();}}>
                <svg className="icon"><use href="#tna-icon-back"/></svg>
                <span>Quay lại</span>
            </Link>
            <span className="divider"></span>
            <nav className="breadcrumb" aria-label="Đường dẫn">
                <span>Quản lý đề thi</span>
                <span className="breadcrumb-slash">/</span>
                <span className="breadcrumb-current">
                    Tạo bài kiểm tra mới
                </span>
            </nav>
        </div>
        <div className="topbar-right">
            <button className="icon-button" type="button" aria-label="Trợ giúp" onClick={()=>notify("Soạn câu hỏi, chọn đáp án đúng rồi lưu bản nháp.")}>
                <svg className="icon"><use href="#tna-icon-help"/></svg>
            </button>
            <button className="icon-button notification-button" type="button" aria-label="Thông báo" onClick={()=>notify("Bạn chưa có thông báo mới.")}>
                <svg className="icon"><use href="#tna-icon-bell"/></svg>
                <span className="notification-dot"></span>
            </button>
            <span className="divider"></span>
            <Link className="admin-profile" to="/Cai_dat_Admin">
                <span className="avatar">
                    <svg className="icon"><use href="#tna-icon-user"/></svg>
                    <span className="online-dot"></span>
                </span>
                <span className="admin-info">
                    <strong>Admin DBCAS</strong>
                    <span>admin.dbcas@gmail.com</span>
                </span>
            </Link>
        </div>
    </header>
    <main className="page-layout">
        <aside className="sidebar">
            <section className="card course-card">
                <h2 className="section-title">
                    <span className="title-icon">
                        <svg className="icon"><use href="#tna-icon-book"/></svg>
                    </span> THÔNG TIN HỌC PHẦN
                </h2>
                <div className="form-field">
                    <label htmlFor="test-name">TÊN BÀI KIỂM TRA</label>
                    <input id="test-name" type="text" value={draft.testName} onChange={event=>updateMeta("testName",event.target.value)} />
                </div>
                <div className="form-field">
                    <label htmlFor="major">NGÀNH HỌC</label>
                    <div className="select-wrapper">
                        <select id="major" value={draft.major} onChange={event=>updateMeta("major",event.target.value)}>
                            <option>Ngành Công nghệ phần mềm</option>
                            <option>Ngành Hệ thống Thông tin Quản lý</option>
                            <option>Ngành Khoa học Máy tính</option>
                            <option>Ngành Kỹ thuật Phần mềm</option>  &#x20;
                            <option>An ninh Mạng</option>
                        </select>
                        <svg className="icon select-icon">
                            <use href="#tna-icon-down"/>
                        </svg>
                    </div>
                </div>
                <div className="form-field">
                    <label htmlFor="school-year">NĂM HỌC</label>
                    <div className="select-wrapper">
                        <select id="school-year" value={draft.schoolYear} onChange={event=>updateMeta("schoolYear",event.target.value)}>
                            <option>2024 - 2025</option>
                            <option>2025 - 2026</option>
                            <option>2026 - 2027</option>
                        </select>
                        <svg className="icon select-icon">
                            <use href="#tna-icon-down"/>
                        </svg>
                    </div>
                </div>
                <div className="form-field time-field">
                    <div className="field-heading">
                        <label htmlFor="duration">THỜI GIAN LÀM BÀI</label>
                        <span id="time-value" className="time-value">{draft.duration} phút</span>
                    </div>
                    <div className="duration-control">
                        <button onClick={()=>updateDuration(draft.duration-1)} type="button" aria-label="Giảm 1 phút">
                            −
                        </button>
                        <div className="duration-input">
                            <svg className="icon"><use href="#tna-icon-clock"/></svg>
                            <input id="duration" type="number" min="10" max="120" step="1" value={draft.duration} onChange={event=>updateDuration(event.target.value)} required aria-label="Số phút làm bài" />
                            <span>phút</span>
                        </div>
                        <button onClick={()=>updateDuration(draft.duration+1)} type="button" aria-label="Tăng 1 phút">
                            +
                        </button>
                    </div>
                    <div className="duration-presets">
                        <button type="button" className={draft.duration===45 ? "active" : ""} onClick={()=>updateDuration(45)}>45m</button>
                        <button type="button" className={draft.duration===60 ? "active" : ""} onClick={()=>updateDuration(60)}>60m</button>
                        <button type="button" className={draft.duration===90 ? "active" : ""} onClick={()=>updateDuration(90)}>90m</button>
                        <button type="button" className={draft.duration===120 ? "active" : ""} onClick={()=>updateDuration(120)}>120m</button>
                    </div>
                </div>
            </section>
            <section className="card questions-card">
                <div className="card-heading">
                    <h2 className="section-title">
                        <svg className="icon cyan"><use href="#tna-icon-list"/></svg> CÂU HỎI TRẮC NGHIỆM
                    </h2>
                </div>
                <ol className="question-list">{draft.questions.map((item,index)=>(
<li key={index} className={`question-item${index===draft.selectedIndex ? " selected" : ""}`}>
<span className="question-number">{String(index+1).padStart(2,"0")}</span>
<button type="button" className="question-info question-select" onClick={()=>selectQuestion(index)} aria-current={index===draft.selectedIndex ? "true" : undefined}><span className="question-title">{item.title}</span><span className="question-points">{fmtPoints(questionScore(item,"tn"))} điểm</span></button>
<div className="question-actions"><span className={`question-status${complete(item) ? " completed" : ""}`}>{complete(item) ? "Đã soạn" : "Chưa hoàn tất"}</span><button type="button" className="edit-question" aria-label={`Sửa tên câu ${index+1}`} onClick={()=>openRename(index)}><Icon name="edit" /></button><button type="button" className="delete-question" aria-label={`Xóa câu ${index+1}`} onClick={()=>deleteQuestion(index)}><Icon name="trash" /></button></div>
</li>))}</ol>
                <button onClick={addQuestion} className="add-question" type="button">
                    <svg className="icon"><use href="#tna-icon-plus"/></svg>
                    Thêm câu hỏi trắc nghiệm
                </button>
            </section>
        </aside>
        <div className="main-content">
            <section className="card scoring-card">
                <div className="scoring-heading">
                    <h2 className="section-title">
                        <svg className="icon cyan"><use href="#tna-icon-chart"/></svg> CẤU TRÚC ĐIỂM THI &amp; PHÂN BỔ CÂU HỎI
                    </h2>
                    <div className="total-score">
                        <span>Tổng điểm:</span>
                        <strong>{fmtPoints(scores.total)} Điểm • {scores.count} câu</strong>
                    </div>
                </div>
                <div className="score-grid">
<div className="score-item active"><div className="score-item-heading"><strong>1. TRẮC NGHIỆM</strong><span className="score-points">{fmtPoints(scores.tn.points)} đ</span></div><p>{scores.tn.count} câu • Tổng {fmtPoints(scores.tn.points)} điểm</p><span className="score-status">ĐANG SOẠN</span></div>
<div className="score-item"><div className="score-item-heading"><strong>2. TRUY VẤN SQL</strong><span className="score-points">{fmtPoints(scores.sql.points)} đ</span></div><p>{scores.sql.count} câu • Tổng {fmtPoints(scores.sql.points)} điểm</p><span className="score-status">{scores.sql.count ? "Đã lưu nháp" : "Chưa có nháp"}</span></div>
<div className="score-item"><div className="score-item-heading"><strong>3. TỰ LUẬN CSDL</strong><span className="score-points">{fmtPoints(scores.tl.points)} đ</span></div><p>{scores.tl.count} câu • Tổng {fmtPoints(scores.tl.points)} điểm</p><span className="score-status">{scores.tl.count ? "Đã lưu nháp" : "Chưa có nháp"}</span></div>
</div>
            </section>
            <section className="card editor-card">
                <header className="editor-heading">
                    <div>
                        <span id="question-badge" className="question-badge">CÂU {String(draft.selectedIndex+1).padStart(2,"0")} / {draft.questions.length}</span>
                        <h1>{question.title || "Câu hỏi chưa đặt tên"}</h1>
                    </div>
                    <label className="point-badge editable-point" style={{ display: "flex", alignItems: "center", gap: 8 }}>Điểm câu này<input type="number" min="0.01" step="0.01" aria-label="Điểm câu hỏi" style={{ width: 85, minWidth: 0, padding: "6px 8px", border: "1px solid #334155", borderRadius: 6, background: "#070c17", color: "#22d3ee", font: "inherit" }} value={question.points ?? .4} onChange={event=>updateQuestion({points:event.target.value})} />đ</label>
                </header>
                <div className="editor-body">
                    <section className="question-section">
                        <h2 className="section-title">
                            <svg className="icon cyan"><use href="#tna-icon-edit"/></svg>
                            <label htmlFor="question-content">CÂU HỎI</label>
                        </h2>
                        <textarea id="question-content" value={question.content} onChange={event=>updateQuestion({content:event.target.value})} className="question-textarea" rows="4" placeholder="Nhập nội dung câu hỏi..."></textarea>
                    </section>
                    <section className="answers-section">
                        <div className="answers-heading">
                            <h2 className="section-title">
                                <svg className="icon cyan"><use href="#tna-icon-list"/></svg> PHƯƠNG ÁN LỰA CHỌN (CHỌN 1 ĐÁP ÁN ĐÚNG)
                            </h2>
                            <span className="answer-count">{question.answers.length} phương án</span>
                        </div>
                        <div className="answer-list">{question.answers.map((answer,index)=>(
<div key={`${draft.selectedIndex}:${index}`} className={`answer-row${question.correct===index ? " correct" : ""}`}><span className="answer-letter">{String.fromCharCode(65+index)}</span><div className="answer-choice">
{editingAnswer===index ? <input className="answer-edit-input" autoFocus value={answer} aria-label={`Nội dung phương án ${String.fromCharCode(65+index)}`} onChange={event=>updateAnswer(index,event.target.value)} onKeyDown={event=>{if(event.key==="Enter"){event.preventDefault();setEditingAnswer(null);}}} /> : <span className="answer-text">{answer}</span>}
<label className="answer-action"><span>{question.correct===index ? "Đáp án đúng" : "Chọn đúng"}</span><input type="radio" name="correct-answer" checked={question.correct===index} onChange={()=>updateQuestion({correct:index})} aria-label={`Chọn ${String.fromCharCode(65+index)} là đáp án đúng`} /></label></div>
<button type="button" className={`edit-answer${editingAnswer===index ? " editing" : ""}`} aria-label={editingAnswer===index ? "Hoàn tất sửa" : "Sửa phương án"} onClick={()=>setEditingAnswer(editingAnswer===index ? null : index)}><Icon name="edit" /></button><button type="button" className="delete-answer" aria-label="Xóa phương án" onClick={()=>deleteAnswer(index)}><Icon name="trash" /></button></div>))}</div>
                        <button onClick={addAnswer} className="add-answer" type="button">
                            <svg className="icon"><use href="#tna-icon-plus"/></svg>
                            Thêm phương án lựa chọn
                        </button>
                    </section>
                    <section className="explanation-section">
                        <h2 className="section-title">
                            <svg className="icon"><use href="#tna-icon-light"/></svg>
                            <label htmlFor="explanation-text">
                                GIẢI THÍCH ĐÁP ÁN &amp; ĐỐI CHIẾU KIẾN THỨC
                            </label>
                        </h2>
                        <textarea id="explanation-text" value={question.explanation} onChange={event=>updateQuestion({explanation:event.target.value})} className="explanation-textarea" rows="4" placeholder="Nhập giải thích đáp án và nội dung đối chiếu kiến thức..."></textarea>
                    </section>
                </div>
            </section>
        </div>
    </main>
    <footer className="bottom-toolbar">
        <div className="toolbar-actions">
            <button onClick={()=>previewDialog.current?.showModal()} className="button button-secondary" type="button">
                <svg className="icon"><use href="#tna-icon-eye"/></svg>
                Xem trước giao diện sinh viên
            </button>
            <button onClick={()=>saveDraft() && notify("Đã lưu bản nháp trong trình duyệt. Chưa gửi BE.")} className="button button-secondary" type="button">
                <svg className="icon"><use href="#tna-icon-save"/></svg>
                Lưu bản nháp
            </button>
        </div>
        <div className="question-navigation">
            <button disabled={draft.selectedIndex===0} onClick={()=>selectQuestion(draft.selectedIndex-1)} className="button button-secondary" type="button">
                <svg className="icon"><use href="#tna-icon-back"/></svg>
                <span>Câu trước</span>
            </button>
            <span className="page-indicator">{draft.selectedIndex+1} / {draft.questions.length}</span>
            <button disabled={draft.selectedIndex===draft.questions.length-1} onClick={()=>selectQuestion(draft.selectedIndex+1)} className="button button-secondary" type="button">
                <span>Câu tiếp theo</span>
                <svg className="icon"><use href="#tna-icon-next"/></svg>
            </button>
        </div>
        <button onClick={()=>{if(saveDraft())navigate(sqlHref);}} className="button button-primary" type="button">
            Chuyển sang phần thi SQL (3 câu)
            <svg className="icon"><use href="#tna-icon-next"/></svg>
        </button>
    </footer>
    <dialog ref={renameDialog} className="rename-dialog">
        <form onSubmit={submitRename}>
            <h2>Sửa tên câu hỏi</h2>
            <label htmlFor="rename-input">Tên câu hỏi</label>
            <input id="rename-input" value={renameTitle} onChange={event=>setRenameTitle(event.target.value)} type="text" maxLength="200" placeholder="Nhập tên câu hỏi..." required />
            <p id="rename-error" className="field-error"></p>
            <div className="dialog-actions">
                <button onClick={()=>renameDialog.current?.close()} className="button button-secondary" type="button">
                    Hủy
                </button>
                <button className="button button-primary" type="submit">
                    Cập nhật
                </button>
            </div>
        </form>
    </dialog>
    <dialog ref={previewDialog} className="rename-dialog preview-dialog">
        <h2>Xem trước giao diện sinh viên</h2>
        <h3>Câu {draft.selectedIndex+1}: {question.title}</h3>
        <p className="preview-content">{question.content || "Chưa nhập nội dung câu hỏi."}</p>
        <ol>{question.answers.map((answer,index)=><li key={index}>{String.fromCharCode(65+index)}. {answer || "Chưa nhập phương án"}</li>)}</ol>
        <div className="dialog-actions">
            <button onClick={()=>previewDialog.current?.close()} className="button button-secondary" type="button">
                Đóng
            </button>
        </div>
    </dialog>
    <div className={`toast${toast ? " show" : ""}`} role="status" aria-live="polite">{toast}</div>
</div>;
}
