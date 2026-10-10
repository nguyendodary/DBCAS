import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./SQL_Admin.css";
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


const DRAFT_KEY="dbcas_sql_admin_draft_v1";
const MCQ_DRAFT_KEY="dbcas_tn_admin_full_draft_v1";
function emptyQuestion(title = "") {
            return {
                title,
                description: "",
                sql: "",
                keywords: [],
                points: "1.0"
            };
        }
        const questions = [
            emptyQuestion("Truy vấn JOIN & Phân nhóm Aggregation"), {
                title: "Tối ưu Window Functions & CTE",
                description: "Viết truy vấn phân tích doanh số đơn hàng theo quý " +
                    "sử dụng Recursive CTE và DENSE_RANK() để xếp hạng " +
                    "top khách hàng VIP có tổng chi tiêu cao nhất qua " +
                    "từng quý của năm tài chính 2023.",
                sql: `WITH RECURSIVE quarterly_spending AS (
    SELECT
        c.customer_id,
        c.full_name,
        DATE_PART('quarter', o.order_date) AS qtr,
        SUM(oi.quantity * oi.unit_price) AS total_spent
    FROM customers c
    INNER JOIN orders o
        ON c.customer_id = o.customer_id
    INNER JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE DATE_PART('year', o.order_date) = 2023
    GROUP BY c.customer_id, c.full_name, qtr
)
SELECT
    qtr,
    customer_id,
    full_name,
    total_spent,
    DENSE_RANK() OVER (
        PARTITION BY qtr
        ORDER BY total_spent DESC
    ) AS rank_vip
FROM quarterly_spending
ORDER BY qtr ASC, rank_vip ASC;`,
                keywords: [
                    "DENSE_RANK()",
                    "PARTITION BY",
                    "WITH RECURSIVE",
                    "INNER JOIN"
                ],
                points: "1.0"
            },
            emptyQuestion("Transaction & Isolation Level Testing")
        ];
function readDraft(key){try{return JSON.parse(sessionStorage.getItem(key));}catch{return null;}}
function validQuestion(q){return q && ["title","description","sql"].every(key=>typeof q[key]==="string")&&Array.isArray(q.keywords)&&q.keywords.every(word=>typeof word==="string");}
function initialDraft(){
 const fallback={testName:"Kiểm tra Cơ sở Dữ liệu Nâng cao",major:"Ngành Công nghệ phần mềm",schoolYear:"2024 - 2025",duration:60,selectedIndex:1,questions};
 const sql=readDraft(DRAFT_KEY),mcq=readDraft(MCQ_DRAFT_KEY),result={...fallback};
 if(sql&&Array.isArray(sql.questions)&&sql.questions.length>0&&sql.questions.every(validQuestion)){result.questions=sql.questions;result.selectedIndex=Math.max(0,Math.min(sql.questions.length-1,Number.isInteger(sql.selectedIndex)?sql.selectedIndex:0));}
 // Học phần thống nhất với bản nháp TN được lưu khi chuyển sang SQL.
 for(const source of [sql,mcq]){if(!source)continue;for(const key of ["testName","major","schoolYear"]){if(typeof source[key]==="string")result[key]=source[key];}if(Number.isFinite(source.duration))result.duration=Math.max(10,Math.min(120,Math.round(source.duration)));}
 return result;
}
function complete(q){return Boolean(q.title.trim()&&q.description.trim()&&q.sql.trim()&&validPoints(q.points,1));}
function Icon({name}){return <svg className="icon" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><use href={`#sqla-icon-${name}`} /></svg>;}
// TODO BE: lấy/lưu đề qua API; chạy đáp án trong Docker với dữ liệu kiểm thử.
// Từ khóa chỉ là thông tin soạn đề, chưa dùng để chấm đúng/sai SQL.
export default function SQLAdmin({tnHref="/TN_Admin",essayHref="/TL_Admin",settingsHref="/Cai_dat_Admin"}){
 const navigate=useNavigate();
 const [draft,setDraft]=useState(initialDraft),[toast,setToast]=useState("");
 const [addingKeyword,setAddingKeyword]=useState(false),[keyword,setKeyword]=useState("");
 const [renameIndex,setRenameIndex]=useState(null),[renameTitle,setRenameTitle]=useState(""),[studentSQL,setStudentSQL]=useState("");
 const renameDialog=useRef(null),previewDialog=useRef(null),sqlInput=useRef(null),toastTimer=useRef(null),selectionFrame=useRef(null);
 const question=draft.questions[draft.selectedIndex];
 const scores=examSummary("sql",draft);
 useEffect(()=>()=>{clearTimeout(toastTimer.current);if(selectionFrame.current!==null)cancelAnimationFrame(selectionFrame.current);},[]);
 function notify(message){clearTimeout(toastTimer.current);setToast(message);toastTimer.current=setTimeout(()=>setToast(""),3500);}
 function updateMeta(key,value){setDraft(old=>({...old,[key]:value}));}
 function updateDuration(value){const number=Number(value);if(Number.isFinite(number)&&String(value).trim())updateMeta("duration",Math.max(10,Math.min(120,Math.round(number))));}
 function updateQuestion(patch){setDraft(old=>({...old,questions:old.questions.map((q,i)=>i===old.selectedIndex ? {...q,...patch} : q)}));}
 function selectQuestion(index){setAddingKeyword(false);setKeyword("");updateMeta("selectedIndex",index);}
 function addQuestion(){setDraft(old=>({...old,questions:[...old.questions,emptyQuestion("Câu SQL mới")],selectedIndex:old.questions.length}));setAddingKeyword(false);}
 function deleteQuestion(index){if(draft.questions.length===1){notify("Phải giữ ít nhất một câu SQL.");return;}setDraft(old=>({...old,questions:old.questions.filter((_,i)=>i!==index),selectedIndex:Math.max(0,Math.min(old.questions.length-2,old.selectedIndex-(index<old.selectedIndex?1:0)))}));setAddingKeyword(false);}
 function openRename(index){setRenameIndex(index);setRenameTitle(draft.questions[index].title);renameDialog.current?.showModal();}
 function submitRename(event){event.preventDefault();if(!renameTitle.trim())return;setDraft(old=>({...old,questions:old.questions.map((q,i)=>i===renameIndex ? {...q,title:renameTitle.trim()} : q)}));renameDialog.current?.close();}
 function submitKeyword(event){event.preventDefault();const word=keyword.trim().replace(/\s+/g," ").toUpperCase();if(!word)return;if(question.keywords.some(old=>old.toUpperCase()===word)){notify("Từ khóa này đã có.");return;}updateQuestion({keywords:[...question.keywords,word]});setKeyword("");setAddingKeyword(false);}
 function handleSQLTab(event){if(event.key!=="Tab"||event.shiftKey)return;event.preventDefault();const {selectionStart:start,selectionEnd:end}=event.currentTarget;updateQuestion({sql:question.sql.slice(0,start)+"    "+question.sql.slice(end)});selectionFrame.current=requestAnimationFrame(()=>sqlInput.current?.setSelectionRange(start+4,start+4));}
 async function copySQL(){if(!question.sql.trim()){notify("Chưa nhập nội dung SQL.");return;}try{await navigator.clipboard.writeText(question.sql);notify("Đã sao chép SQL.");}catch{sqlInput.current?.focus();sqlInput.current?.select();notify("SQL đã được chọn. Nhấn Ctrl+C để sao chép.");}}
 function saveDraft(){try{
  sessionStorage.setItem(DRAFT_KEY,JSON.stringify({...draft,questions:draft.questions.map(q=>({...q,points:questionScore(q,"sql")}))}));
  const mcq=readDraft(MCQ_DRAFT_KEY);
  if(mcq&&typeof mcq==="object"&&!Array.isArray(mcq))sessionStorage.setItem(MCQ_DRAFT_KEY,JSON.stringify({...mcq,testName:draft.testName,major:draft.major,schoolYear:draft.schoolYear,duration:draft.duration}));
  return true;
 }catch{notify("Không lưu đầy đủ được bản nháp. Hãy thử lại trước khi chuyển trang.");return false;}}
 function beforeNavigate(event){if(!saveDraft())event.preventDefault();}
 function previousQuestion(){if(draft.selectedIndex>0)selectQuestion(draft.selectedIndex-1);else if(saveDraft())navigate(tnHref);}
 function nextQuestion(){if(draft.selectedIndex<draft.questions.length-1)selectQuestion(draft.selectedIndex+1);else if(saveDraft())navigate(essayHref);}
 return <div className="dbcas-admin-sql"><svg className="svg-definitions" aria-hidden="true"><defs><symbol id="sqla-icon-back" viewBox="0 0 24 24"><path d="m12 19-7-7 7-7M5 12h14"/></symbol><symbol id="sqla-icon-next" viewBox="0 0 24 24"><path d="m12 5 7 7-7 7M5 12h14"/></symbol><symbol id="sqla-icon-help" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .7-1.5 1-1.5 2M12 16h.01"/></symbol><symbol id="sqla-icon-bell" viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></symbol><symbol id="sqla-icon-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/></symbol><symbol id="sqla-icon-book" viewBox="0 0 24 24"><path d="M12 5v15M12 5C8 2 4 3 2 4v15c3-1 7-1 10 1M12 5c4-3 8-2 10-1v15c-3-1-7-1-10 1"/></symbol><symbol id="sqla-icon-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></symbol><symbol id="sqla-icon-list" viewBox="0 0 24 24"><path d="M9 6h12M9 12h12M9 18h12M3 6h1M3 12h1M3 18h1"/></symbol><symbol id="sqla-icon-chart" viewBox="0 0 24 24"><path d="M4 3v17h17M8 16v-5m5 5V7m5 9V4"/></symbol><symbol id="sqla-icon-edit" viewBox="0 0 24 24"><path d="m16 3 5 5-12 12-6 1 1-6Zm-2 2 5 5"/></symbol><symbol id="sqla-icon-trash" viewBox="0 0 24 24"><path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/></symbol><symbol id="sqla-icon-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol><symbol id="sqla-icon-code" viewBox="0 0 24 24"><path d="m8 5-7 7 7 7m8-14 7 7-7 7m-3-16-2 18"/></symbol><symbol id="sqla-icon-play" viewBox="0 0 24 24"><path d="m8 4 12 8-12 8Z"/></symbol><symbol id="sqla-icon-copy" viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/></symbol><symbol id="sqla-icon-tag" viewBox="0 0 24 24"><path d="M3 3h8l10 10-8 8L3 11Z"/><circle cx="7" cy="7" r="1"/></symbol><symbol id="sqla-icon-eye" viewBox="0 0 24 24"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></symbol><symbol id="sqla-icon-save" viewBox="0 0 24 24"><path d="M4 3h13l3 3v15H4ZM8 3v6h8V3M8 21v-8h8v8"/></symbol></defs></svg>
    <header className="topbar">
        <div className="topbar-left">
            <Link className="back-button" to={tnHref} onClick={beforeNavigate}>
                <Icon name="back" /> Quay lại
            </Link>
            <span className="divider"></span>
            <nav className="breadcrumb" aria-label="Đường dẫn">
                <span>Quản lý bài kiểm tra</span>
                <span>/</span>
                <strong>Tạo bài kiểm tra mới</strong>
            </nav>
        </div>
        <div className="topbar-right">
            <button className="icon-button" onClick={()=>notify("Soạn đề, nhập đáp án chuẩn, thêm từ khóa rồi lưu nháp.")} type="button" aria-label="Trợ giúp">
                <Icon name="help" />
            </button>
            <button className="icon-button notification-button" onClick={()=>notify("Bạn chưa có thông báo mới.")} type="button" aria-label="Thông báo">
                <Icon name="bell" />
                <span className="notification-dot"></span>
            </button>
            <span className="divider"></span>
            <Link className="admin-profile" to={settingsHref}>
                <span className="avatar">
                    <Icon name="user" />
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
                    <Icon name="book" /> THÔNG TIN HỌC PHẦN
                </h2>
                <div className="form-field">
                    <label htmlFor="test-name">TÊN BÀI KIỂM TRA</label>
                    <input id="test-name" type="text" value={draft.testName} onChange={event=>updateMeta("testName",event.target.value)} />
                </div>
                <div className="form-field">
                    <label htmlFor="major">NGÀNH HỌC</label>
                    <select id="major" value={draft.major} onChange={event=>updateMeta("major",event.target.value)}>
                            <option>Ngành Công nghệ phần mềm</option>
                            <option>Ngành Hệ thống Thông tin Quản lý</option>
                            <option>Ngành Khoa học Máy tính</option>
                            <option>Ngành Kỹ thuật Phần mềm</option>  &#x20;
                            <option>An ninh Mạng</option>
                        </select>
                </div>
                <div className="form-field">
                    <label htmlFor="school-year">NĂM HỌC</label>
                    <select id="school-year" value={draft.schoolYear} onChange={event=>updateMeta("schoolYear",event.target.value)}>
                        <option>2024 - 2025</option>
                        <option>2025 - 2026</option>
                        <option>2026 - 2027</option>
                    </select>
                </div>
                <div className="form-field">
                    <div className="field-heading">
                        <label htmlFor="duration">THỜI GIAN LÀM BÀI</label>
                        <span>{draft.duration} phút</span>
                    </div>
                    <div className="duration-control">
                        <button disabled={draft.duration<=10} onClick={()=>updateDuration(draft.duration-1)} type="button" aria-label="Giảm 1 phút">−</button>
                        <div className="duration-input">
                            <Icon name="clock" />
                            <input id="duration" type="number" min="10" max="120" step="1" value={draft.duration} onChange={event=>updateDuration(event.target.value)} aria-label="Số phút làm bài" />
                            <span>phút</span>
                        </div>
                        <button disabled={draft.duration>=120} onClick={()=>updateDuration(draft.duration+1)} type="button" aria-label="Tăng 1 phút">+</button>
                    </div>
                    <div className="duration-presets">
                        <button type="button" className={draft.duration===45 ? "active" : ""} aria-pressed={draft.duration===45} onClick={()=>updateDuration(45)}>45m</button>
                        <button type="button" className={draft.duration===60 ? "active" : ""} aria-pressed={draft.duration===60} onClick={()=>updateDuration(60)}>60m</button>
                        <button type="button" className={draft.duration===90 ? "active" : ""} aria-pressed={draft.duration===90} onClick={()=>updateDuration(90)}>90m</button>
                        <button type="button" className={draft.duration===120 ? "active" : ""} aria-pressed={draft.duration===120} onClick={()=>updateDuration(120)}>120m</button>
                    </div>
                </div>
            </section>
            <section className="card questions-card">
                <h2 className="section-title">
                    <Icon name="list" /> CÂU HỎI SQL
                </h2>
                <ol className="question-list">{draft.questions.map((item,index)=>(
<li key={index} className={`question-item${draft.selectedIndex===index ? " selected" : ""}`}>
<button type="button" className="question-select" aria-pressed={draft.selectedIndex===index} onClick={()=>selectQuestion(index)}><span className="question-number">{String(index+1).padStart(2,"0")}</span><span className="question-info"><span className="question-title">{item.title || "Chưa nhập tên câu hỏi"}</span><span className="question-points">{fmtPoints(questionScore(item,"sql"))} điểm</span></span></button>
<div className="question-actions"><span className="question-status">{draft.selectedIndex===index ? "ĐANG CHỌN" : complete(item) ? "Đã xong" : "Chưa soạn"}</span><button type="button" className="small-button" aria-label={`Sửa tên câu ${index+1}`} onClick={()=>openRename(index)}><Icon name="edit" /></button><button type="button" className="small-button delete-button" aria-label={`Xóa câu ${index+1}`} onClick={()=>deleteQuestion(index)}><Icon name="trash" /></button></div></li>))}</ol>
                <button onClick={addQuestion} className="add-button" type="button">
                    <Icon name="plus" />
                    Thêm câu hỏi SQL
                </button>
            </section>
        </aside>
        <div className="main-content">
            <section className="card scoring-card">
                <div className="scoring-heading">
                    <h2 className="section-title">
                        <Icon name="chart" /> CẤU TRÚC ĐIỂM THI &amp; PHÂN BỔ CÂU HỎI
                    </h2>
                    <div className="total-score">
                        Tổng điểm: <strong>{fmtPoints(scores.total)} Điểm • {scores.count} câu</strong>
                    </div>
                </div>
                <div className="score-grid">
<div className="score-item"><div className="score-item-heading"><strong>1. TRẮC NGHIỆM</strong><span className="score-points">{fmtPoints(scores.tn.points)} đ</span></div><p>{scores.tn.count} câu • Tổng {fmtPoints(scores.tn.points)} điểm</p><span className="score-status">{scores.tn.count ? "Đã lưu nháp" : "Chưa có nháp"}</span></div>
<div className="score-item active"><div className="score-item-heading"><strong>2. TRUY VẤN SQL</strong><span className="score-points">{fmtPoints(scores.sql.points)} đ</span></div><p>{scores.sql.count} câu • Tổng {fmtPoints(scores.sql.points)} điểm</p><span className="score-status">ĐANG SOẠN</span></div>
<div className="score-item"><div className="score-item-heading"><strong>3. TỰ LUẬN CSDL</strong><span className="score-points">{fmtPoints(scores.tl.points)} đ</span></div><p>{scores.tl.count} câu • Tổng {fmtPoints(scores.tl.points)} điểm</p><span className="score-status">{scores.tl.count ? "Đã lưu nháp" : "Chưa có nháp"}</span></div>
</div>
            </section>
            <section className="card editor-card">
                <header className="editor-heading">
                    <div>
                        <span className="question-badge">CÂU SQL {String(draft.selectedIndex+1).padStart(2,"0")} / {draft.questions.length}</span>
                        <h1>{question.title || "Câu hỏi chưa đặt tên"}</h1>
                    </div>
                    <label className="point-badge editable-point" style={{ display: "flex", alignItems: "center", gap: 8 }}>Điểm câu này<input type="number" min="0.01" step="0.01" aria-label="Điểm câu hỏi" style={{ width: 85, minWidth: 0, padding: "6px 8px", border: "1px solid #334155", borderRadius: 6, background: "#070c17", color: "#22d3ee", font: "inherit" }} value={question.points ?? 1} onChange={event=>updateQuestion({points:event.target.value})} />đ</label>
                </header>
                <div className="editor-body">
                    <section className="editor-section">
                        <h2 className="section-title">
                            <Icon name="edit" />
                            <label htmlFor="question-description">
                                MÔ TẢ YÊU CẦU ĐỀ BÀI
                            </label>
                        </h2>
                        <textarea id="question-description" value={question.description} onChange={event=>updateQuestion({description:event.target.value})} className="description-input" rows="4" placeholder="Nhập mô tả yêu cầu đề bài..."></textarea>
                    </section>
                    <section className="editor-section">
                        <div className="section-heading">
                            <h2 className="section-title">
                                <Icon name="code" />
                                <label htmlFor="sql-code">
                                    ĐÁP ÁN TRUY VẤN CHUẨN
                                </label>
                            </h2>
                            <button onClick={()=>notify("Chưa kết nối BE và Docker Sandbox để chạy SQL.")} className="button sandbox-button" type="button">
                                <Icon name="play" />
                                Chạy thử Sandbox
                            </button>
                        </div>
                        <div className="code-editor">
                            <div className="code-toolbar">
                                <div className="code-dots">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                                <span className="code-language">SQL</span>
                                <button onClick={copySQL} className="copy-button" type="button">
                                    <Icon name="copy" />
                                    Copy
                                </button>
                            </div>
                            <textarea id="sql-code" ref={sqlInput} value={question.sql} onChange={event=>updateQuestion({sql:event.target.value})} onKeyDown={handleSQLTab} className="sql-input" rows="13" spellCheck={false} autoCapitalize="off" autoComplete="off" placeholder="Nhập đáp án truy vấn SQL..."></textarea>
                        </div>
                    </section>
                    <section className="keywords-section">
                        <div className="section-heading">
                            <h2 className="section-title">
                                <Icon name="tag" /> TỪ KHÓA BẮT BUỘC ĐỐI CHIẾU TRỌNG TÂM
                            </h2>
                            <span className="keyword-count">{question.keywords.length} từ khóa</span>
                        </div>
                        <div className="keyword-controls">
                            <div className="keyword-list">{question.keywords.map((word,index)=><span className="keyword-tag" key={index}><span>{word}</span><button type="button" aria-label={`Xóa từ khóa ${word}`} onClick={()=>updateQuestion({keywords:question.keywords.filter((_,i)=>i!==index)})}>×</button></span>)}</div>
                            <button onClick={()=>{setAddingKeyword(true);setKeyword("");}} className="add-keyword" type="button">
                                <Icon name="plus" />
                                Thêm từ khóa
                            </button>
                        </div>
                        <form onSubmit={submitKeyword} className="keyword-form" hidden={!addingKeyword}>
                            <input id="keyword-input" value={keyword} onChange={event=>setKeyword(event.target.value)} type="text" maxLength="100" placeholder="Ví dụ: INNER JOIN" aria-label="Từ khóa SQL" required />
                            <button className="button button-primary" type="submit">
                                Thêm
                            </button>
                            <button onClick={()=>setAddingKeyword(false)} className="button" type="button">Hủy</button>
                        </form>
                    </section>
                </div>
            </section>
        </div>
    </main>
    <footer className="bottom-toolbar">
        <div className="toolbar-actions">
            <button onClick={()=>{setStudentSQL("");previewDialog.current?.showModal();}} className="button" type="button">
                <Icon name="eye" />
                Xem trước giao diện sinh viên
            </button>
            <button onClick={()=>saveDraft() && notify("Đã lưu nháp SQL trong trình duyệt. Chưa gửi BE.")} className="button" type="button">
                <Icon name="save" />
                Lưu bản nháp
            </button>
        </div>
        <div className="question-navigation">
            <button onClick={previousQuestion} className="button" type="button">
                <Icon name="back" />
                <span>{draft.selectedIndex===0 ? "Về Trắc nghiệm" : "Câu trước"}</span>
            </button>
            <span>{draft.selectedIndex+1} / {draft.questions.length}</span>
            <button onClick={nextQuestion} className="button" type="button">
                <span>{draft.selectedIndex===draft.questions.length-1 ? "Sang Tự luận" : "Câu tiếp theo"}</span>
                <Icon name="next" />
            </button>
        </div>
        <Link className="button button-primary" to={essayHref} onClick={beforeNavigate}>
            Chuyển sang phần thi Tự luận (1 câu)
            <Icon name="next" />
        </Link>
    </footer>
    <dialog ref={renameDialog}>
        <form onSubmit={submitRename}>
            <h2>Sửa tên câu hỏi SQL</h2>
            <label htmlFor="rename-input">Tên câu hỏi</label>
            <input id="rename-input" value={renameTitle} onChange={event=>setRenameTitle(event.target.value)} type="text" maxLength="200" placeholder="Nhập tên câu hỏi..." required />
            <p id="rename-error" className="field-error"></p>
            <div className="dialog-actions">
                <button onClick={()=>renameDialog.current?.close()} className="button" type="button">
                    Hủy
                </button>
                <button className="button button-primary" type="submit">
                    Cập nhật
                </button>
            </div>
        </form>
    </dialog>
    <dialog ref={previewDialog} className="preview-dialog">
        <h2>Xem trước giao diện sinh viên</h2>
        <h3>Câu SQL {draft.selectedIndex+1}: {question.title}</h3>
        <p className="preview-description">{question.description || "Chưa nhập mô tả đề bài."}</p>
        <label htmlFor="student-sql">Bài làm SQL</label>
        <textarea id="student-sql" value={studentSQL} onChange={event=>setStudentSQL(event.target.value)} className="sql-input" rows="8" placeholder="Sinh viên nhập truy vấn tại đây..." spellCheck={false}></textarea>
        <div className="dialog-actions">
            <button onClick={()=>previewDialog.current?.close()} className="button" type="button">
                Đóng
            </button>
        </div>
    </dialog>
    <div className={`toast${toast ? " show" : ""}`} role="status" aria-live="polite">{toast}</div>
</div>;
}
