import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import "./TN_Learner.css";

// TODO BE: thay SAMPLE_QUESTIONS bằng đề trắc nghiệm từ API.
const SAMPLE_QUESTIONS = Array.from({

                length: 10

            }, (_, index) => ({

                id: index + 1,

                title: "Nội dung câu hỏi " + (index + 1) +

                    " sẽ được bổ sung tại đây.",

                options: [{

                    text: "Phương án A",

                    description: ""

                }, {

                    text: "Phương án B",

                    description: ""

                }, {

                    text: "Phương án C",

                    description: ""

                }, {

                    text: "Phương án D",

                    description: ""

                }]

            }));



            SAMPLE_QUESTIONS[3] = {

                id: 4,

                title: "Xác định các khóa dự tuyển của lược đồ quan hệ R.",

                introduction: "Cho lược đồ quan hệ",

                schema: "R(A, B, C, D, E)",

                dependencies: "F = {\n" +

                    "    AB → C,\n" +

                    "    C → D,\n" +

                    "    D → E,\n" +

                    "    E → A\n" +

                    "}",

                options: [{

                    text: "B, C, D",

                    description: "Các thuộc tính đơn lẻ xác định từng phần bao đóng."

                }, {

                    text: "AB, BC, BD, BE",

                    description: "Các cặp thuộc tính kết hợp với B."

                }, {

                    text: "A, B, C",

                    description: "Tập hợp các thuộc tính bên vế trái của phụ thuộc hàm."

                }, {

                    text: "Không có khóa nào thỏa mãn",

                    description: "Lược đồ có các phụ thuộc hàm tạo thành vòng."

                }]

            };



            
function readJSON(key) {
 try { return JSON.parse(localStorage.getItem(key) || "null"); } catch { return null; }
}
function formatTime(seconds) {
 const safe = Math.max(0,Math.floor(seconds));
 return `${String(Math.floor(safe / 60)).padStart(2,"0")}:${String(safe % 60).padStart(2,"0")}`;
}
function validDuration(value) { return Number.isFinite(value) && value >= 10 && value <= 120; }
function initializeAttempt(key,testId,params,questions) {
 const old = readJSON(key);
 const requestedDeadline = Number(params.get("deadline"));
 const requestedDuration = Number(params.get("duration"));
 const reuse = old && Number.isFinite(old.deadline) && (!requestedDeadline || old.deadline === requestedDeadline);
 const durationMinutes = reuse && validDuration(old.durationMinutes) ? old.durationMinutes : validDuration(requestedDuration) ? requestedDuration : 50;
 const deadline = reuse ? old.deadline : requestedDeadline > 0 && Number.isFinite(requestedDeadline) ? requestedDeadline : Date.now() + durationMinutes * 60000;
 const answers = {};
 if (reuse) questions.forEach(q => { const value = old.answers?.[q.id]; if (Number.isInteger(value) && value >= 0 && value < q.options.length) answers[q.id] = value; });
 return {testId,durationMinutes,deadline,answers,currentIndex:reuse && Number.isInteger(old.currentIndex) ? Math.max(0,Math.min(questions.length - 1,old.currentIndex)) : 0,submitted:reuse && old.submitted === true,submittedPayload:reuse ? old.submittedPayload : null,remainingSeconds:reuse ? old.remainingSeconds : durationMinutes * 60};
}
export default function TNLearner(props) {
 const [params] = useSearchParams();
 const testId = params.get("testId") || "de-mau-01";
 // Remount khi chuyển sang một bài thi/lượt thi khác.
 return <Attempt key={`${testId}:${params.get("deadline") || ""}`} {...props} testId={testId} params={params} />;
}
function Attempt({testId,params,questions=SAMPLE_QUESTIONS,listHref="/Bai_kiem_tra_Learner",sqlHref="/SQL_Learner",essayHref="/TL_Learner"}) {
 const navigate = useNavigate();
 const storageKey = `dbcas-tn-attempt-v3:${testId}`;
 const [attempt,setAttempt] = useState(() => initializeAttempt(storageKey,testId,params,questions));
 const stateRef = useRef(attempt);
 const [draftAnswers,setDraftAnswers] = useState(() => ({...attempt.answers}));
 const [remaining,setRemaining] = useState(() => attempt.submitted ? Math.max(0,attempt.remainingSeconds || 0) : Math.max(0,Math.ceil((attempt.deadline - Date.now()) / 1000)));
 const [toast,setToast] = useState("");
 const [sectionCounts,setSectionCounts] = useState({sql:0,essay:0});
 const [saveFailed,setSaveFailed] = useState(false);
 const toastTimer = useRef(null);
 const redirectTimer = useRef(null);
 const dialogRef = useRef(null);
 const warned = useRef(false);
 const submitted = attempt.submitted;
 const currentIndex = attempt.currentIndex;
 const question = questions[currentIndex];
 const sqlCount = sectionCounts.sql;
 const essayCount = sectionCounts.essay;
 const saveStatus = submitted ? (saveFailed ? "Bài đã kết thúc nhưng chưa lưu được bản nộp." : "Đã lưu bản nộp trên trình duyệt. Chưa kết nối BE.") : Number.isInteger(draftAnswers[question.id]) && draftAnswers[question.id] !== attempt.answers[question.id] ? "Đáp án chưa lưu. Bấm Lưu câu trả lời để được tính." : Number.isInteger(attempt.answers[question.id]) ? "Câu này đã lưu câu trả lời." : "Câu này chưa lưu câu trả lời.";
 function showToast(message) { clearTimeout(toastTimer.current); setToast(message); toastTimer.current = setTimeout(() => setToast(""),4000); }
 function writeJSON(key,value) {
  try { localStorage.setItem(key,JSON.stringify(value)); return true; }
  catch { showToast("Không lưu được dữ liệu trên trình duyệt."); return false; }
 }
 function adopt(value) { stateRef.current=value; setAttempt(value); if(value.submitted) {setDraftAnswers({...value.answers});dialogRef.current?.close();} }
 function commit(value) {
  const latest=readJSON(storageKey);
  if(latest?.deadline===value.deadline && latest.submitted && !value.submitted) {adopt(latest);return false;}
  if(!writeJSON(storageKey,value)) return false;
  adopt(value);return true;
 }
 function sectionAnswers(suffix) { const saved=readJSON(storageKey+suffix);return saved?.deadline===stateRef.current.deadline ? saved.answers || {} : {}; }
 function refreshCounts() {
  const sql=sectionAnswers(":sql"),essay=sectionAnswers(":tl");
  setSectionCounts({sql:[11,12,13].filter(id=>typeof sql[id]==="string" && sql[id].trim()).length,essay:Object.values(essay).some(value=>typeof value==="string" && value.trim()) ? 1 : 0});
 }
 function canEdit() {
  const latest=readJSON(storageKey);
  if(latest?.deadline===stateRef.current.deadline && latest.submitted) adopt(latest);
  if(stateRef.current.submitted) return false;
  if(Date.now()>=stateRef.current.deadline) {finishExam("timeout");return false;}
  return true;
 }
 function saveAnswer() {
  if(!canEdit()) return;
  const value=draftAnswers[question.id];
  if(!Number.isInteger(value)) {showToast("Bạn hãy chọn một đáp án trước khi lưu.");return;}
  if(commit({...stateRef.current,answers:{...stateRef.current.answers,[question.id]:value}})) showToast(`Đã lưu câu ${question.id}.`);
 }
 function resetAnswer() {
  if(!canEdit()) return;
  const answers={...stateRef.current.answers};delete answers[question.id];
  if(commit({...stateRef.current,answers})) {setDraftAnswers(previous=>{const next={...previous};delete next[question.id];return next;});showToast(`Đã xóa câu trả lời của câu ${question.id}.`);}
 }
 function changeQuestion(index) {
  if(index<0 || index>=questions.length) return;
  // Có thể xem lại các câu sau khi kết thúc nhưng không sửa đáp án.
  if(!stateRef.current.submitted && !canEdit()) return;
  const next={...stateRef.current,currentIndex:index};
  if(commit(next)) setDraftAnswers({...next.answers});
 }
 function sectionURL(path) {
  const query=new URLSearchParams({testId,duration:String(attempt.durationMinutes),deadline:String(attempt.deadline)});
  return `${path}?${query.toString()}`;
 }
 function handleSection(event) {
  if(!canEdit()) {event.preventDefault();showToast("Bài thi đã kết thúc.");return;}
  commit(stateRef.current);
 }
 function nextQuestion() {
  if(currentIndex<questions.length - 1) changeQuestion(currentIndex+1);
  else if(canEdit()) {commit(stateRef.current);navigate(sectionURL(sqlHref));}
 }
 function openSubmit() {
  if(!canEdit()) return;
  dialogRef.current?.showModal();
 }
 function finishExam(reason) {
  const current=stateRef.current;
  if(current.submitted) return;
  const latest=readJSON(storageKey);
  if(latest?.deadline===current.deadline && latest.submitted) {adopt(latest);return;}
  const payload={testId,submittedAt:new Date().toISOString(),submissionReason:reason,durationMinutes:current.durationMinutes,deadline:current.deadline,answers:{mcq:{...current.answers},sql:[11,12,13].filter(id=>typeof sectionAnswers(":sql")[id]==="string" && sectionAnswers(":sql")[id].trim()).map(id=>({questionId:id,answer:sectionAnswers(":sql")[id]})),essay:sectionAnswers(":tl")}};
  const seconds=reason==="timeout" ? 0 : Math.max(0,Math.ceil((current.deadline-Date.now())/1000));
  const finished={...current,submitted:true,remainingSeconds:seconds,submittedPayload:payload};
  adopt(finished);setRemaining(seconds);
  const saved=writeJSON(storageKey,finished);
  const archived=writeJSON(storageKey+":last-submission",payload);
  setSaveFailed(!saved || !archived);
  // TODO BE: gọi API nộp bài tại đây. Đây chỉ là bản nộp cục bộ.
  if(saved && archived) {
   showToast(reason==="timeout" ? "Đã hết giờ. Đã lưu bản nộp trên trình duyệt; chưa gửi BE." : "Đã lưu bản nộp trên trình duyệt; chưa gửi BE.");
   redirectTimer.current=setTimeout(()=>navigate(listHref),1800);
  } else showToast("Không lưu được bản nộp. Trang giữ nguyên để tránh mất bài.");
 }
 function blockCopy(event) {event.preventDefault();}
 useEffect(() => {
  commit(stateRef.current);refreshCounts();
  function tick() {
   const latest=readJSON(storageKey);
   if(latest?.deadline===stateRef.current.deadline && latest.submitted && !stateRef.current.submitted) adopt(latest);
   if(stateRef.current.submitted) return;
   const seconds=Math.max(0,Math.ceil((stateRef.current.deadline-Date.now())/1000));setRemaining(seconds);
   if(seconds===0) finishExam("timeout");
   else if(seconds<=300 && !warned.current) {warned.current=true;showToast("Chỉ còn 5 phút.");}
  }
  function refresh() {tick();refreshCounts();}
  tick();const interval=setInterval(tick,1000);
  window.addEventListener("storage",refresh);window.addEventListener("focus",refresh);document.addEventListener("visibilitychange",refresh);
  return () => {clearInterval(interval);clearTimeout(toastTimer.current);clearTimeout(redirectTimer.current);window.removeEventListener("storage",refresh);window.removeEventListener("focus",refresh);document.removeEventListener("visibilitychange",refresh);};
 }, []);
 return <div className="dbcas-learner-tn">


    <svg className="svg-library" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">



        <symbol id="tn-i-left" viewBox="0 0 24 24">

            <path d="m12 5-7 7 7 7M5 12h14"></path>

        </symbol>



        <symbol id="tn-i-right" viewBox="0 0 24 24">

            <path d="M5 12h14m-7-7 7 7-7 7"></path>

        </symbol>



        <symbol id="tn-i-clock" viewBox="0 0 24 24">

            <circle cx="12" cy="14" r="8"></circle>

            <path d="M12 10v4l3 2M9 2h6M12 2v4M18 6l2-2"></path>

        </symbol>



        <symbol id="tn-i-upload" viewBox="0 0 24 24">

            <path d="M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6"></path>

        </symbol>



        <symbol id="tn-i-save" viewBox="0 0 24 24">

            <path d="M4 3h13l4 4v14H3V3h1Z"></path>

            <path d="M7 3v6h10V3M7 21v-8h10v8"></path>

        </symbol>



        <symbol id="tn-i-reset" viewBox="0 0 24 24">

            <path d="M3 10a9 9 0 1 1 2 9M3 4v6h6"></path>

        </symbol>



        <symbol id="tn-i-list" viewBox="0 0 24 24">

            <rect x="4" y="3" width="16" height="18" rx="2"></rect>

            <path d="M8 8h1m3 0h4M8 12h1m3 0h4M8 16h1m3 0h4"></path>

        </symbol>



        <symbol id="tn-i-code" viewBox="0 0 24 24">

            <path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18"></path>

        </symbol>



        <symbol id="tn-i-edit" viewBox="0 0 24 24">

            <path d="m14 4 6 6M4 20l5-1L21 7l-5-5L4 14v6Z"></path>

        </symbol>

    </svg>



    

    <header className="exam-header">

        <div className="header-inner">

            <div className="exam-identity">

                <button className="back-button" onClick={() => submitted ? navigate(listHref) : openSubmit()} type="button">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tn-i-left"></use>

                    </svg>

                    <span>Quay lại</span>

                </button>



                <span className="header-divider" aria-hidden="true"></span>



                <div className="exam-heading">

                    <h1>Datamaster Assessment</h1>

                    <p>

                        Chuẩn hóa Lược đồ, Phụ thuộc hàm &amp; SQL Nâng cao

                    </p>

                </div>

            </div>



            <div className="exam-controls">

                <div className={`timer-box${submitted ? " ended" : remaining <= 300 ? " time-warning" : ""}`}>

                    <svg className="icon timer-icon" aria-hidden="true">

                        <use href="#tn-i-clock"></use>

                    </svg>



                    <div>

                        <span className="timer-label">{submitted ? "ĐÃ KẾT THÚC" : "THỜI GIAN CÒN LẠI"}</span>



                        <div className="timer-value">

                            <strong>{formatTime(remaining)}</strong>

                            <span>/ {formatTime(attempt.durationMinutes * 60)}</span>

                        </div>

                    </div>

                </div>



                <button className="submit-button" onClick={openSubmit} disabled={submitted} type="button">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tn-i-upload"></use>

                    </svg>

                    <span>{submitted ? "ĐÃ KẾT THÚC" : "NỘP BÀI THI"}</span>

                </button>

            </div>

        </div>

    </header>



    <main className="exam-layout">

        

        <aside className="sidebar">

            

            <section className="question-navigation">

                <div className="section-heading">

                    <h2 className="section-title">

                        <svg className="icon" aria-hidden="true">

                            <use href="#tn-i-list"></use>

                        </svg> TRẮC NGHIỆM

                    </h2>



                    <span className="doing-badge">{submitted ? "ĐÃ KẾT THÚC" : "ĐANG LÀM"}</span>

                </div>



                <div className="navigation-heading">

                    <span>DANH SÁCH CÂU HỎI TRẮC NGHIỆM</span>

                    <strong>4.0 ĐIỂM</strong>

                </div>



                <div className="question-grid">{questions.map((item,index) => <button key={item.id} type="button" className={`question-button${Number.isInteger(attempt.answers[item.id]) ? " answered" : ""}${index === currentIndex ? " active" : ""}`} aria-current={index === currentIndex ? "true" : undefined} aria-label={`Câu ${item.id}, ${Number.isInteger(attempt.answers[item.id]) ? "đã lưu" : "chưa lưu"}`} onClick={() => changeQuestion(index)}><span>{String(item.id).padStart(2,"0")}</span><small>{index === currentIndex ? (submitted ? "ĐÃ XONG" : "ĐANG LÀM") : Number.isInteger(attempt.answers[item.id]) ? "✓" : "–"}</small></button>)}</div>



                <p className="navigation-note">

                    Dấu ✓ thể hiện câu đã lưu đáp án.

                </p>

            </section>



            

            <Link className="section-link" to={sectionURL(sqlHref)} onClick={handleSection}>

                <span className="section-name">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tn-i-code"></use>

                    </svg>

                    THỰC HÀNH SQL

                </span>



                <span className="saved-count">{sqlCount}/3 ĐÃ LƯU</span>



                <strong className="section-points">3.0 ĐIỂM</strong>

            </Link>



            <Link className="section-link" to={sectionURL(essayHref)} onClick={handleSection}>

                <span className="section-name">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tn-i-edit"></use>

                    </svg>

                    TỰ LUẬN

                </span>



                <span className="saved-count">{essayCount}/1 ĐÃ LƯU</span>



                <strong className="section-points">3.0 ĐIỂM</strong>

            </Link>



            <p className="sidebar-note">

                Chỉ câu trả lời đã lưu mới được đưa vào bài nộp.

            </p>

        </aside>



        

        <section className="question-panel" aria-labelledby="question-number">

            <div className="question-top">

                <h2 id="question-number">CÂU HỎI {String(question.id).padStart(2,"0")} / {questions.length}</h2>

                <span className="question-score">Điểm: 0.4 điểm</span>

            </div>



            <div className="question-content protected-content" onCopy={blockCopy} onCut={blockCopy} onContextMenu={blockCopy} onDragStart={blockCopy}>
{question.dependencies ? <><p>{question.introduction} <code>{question.schema}</code> với tập phụ thuộc hàm:</p><pre>{question.dependencies}</pre><p>Dựa trên thuật toán tìm bao đóng thuộc tính X⁺, hãy xác định tất cả các khóa dự tuyển (Candidate Keys) của lược đồ quan hệ R?</p></> : <p>{question.title}</p>}
</div>



            <fieldset className="answers-fieldset protected-content">

                <legend>CHỌN MỘT PHƯƠNG ÁN ĐÚNG NHẤT:</legend>

                <div className="answer-list">{question.options.map((option,index) => <label key={index} className="answer-option"><input type="radio" name={`answer-${question.id}`} checked={draftAnswers[question.id] === index} disabled={submitted} onChange={() => { if (canEdit()) setDraftAnswers(previous => ({...previous,[question.id]:index})); }} /><span className="answer-body"><span className="answer-heading"><span className="answer-letter">{"ABCD"[index]}</span><span className="answer-text">{option.text}</span><span className="selected-tag">ĐÃ CHỌN</span></span>{option.description && <span className="answer-description">{option.description}</span>}</span></label>)}</div>

            </fieldset>



            <p className="save-status" role="status" aria-live="polite">{saveStatus}</p>



            <div className="question-actions">

                <button className="action-button" disabled={currentIndex === 0} onClick={() => changeQuestion(currentIndex - 1)} type="button">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tn-i-left"></use>

                    </svg>

                    <span>Câu trước</span>

                </button>



                <div className="right-actions">

                    <button className="action-button reset-button" disabled={submitted} onClick={resetAnswer} type="button">

                        <svg className="icon" aria-hidden="true">

                            <use href="#tn-i-reset"></use>

                        </svg>

                        Đặt lại

                    </button>



                    <button className="action-button" disabled={submitted} onClick={saveAnswer} type="button">

                        <svg className="icon" aria-hidden="true">

                            <use href="#tn-i-save"></use>

                        </svg>

                        Lưu câu trả lời

                    </button>



                    <button className="action-button next-button" onClick={nextQuestion} type="button">

                        <span>{currentIndex === questions.length - 1 ? "Chuyển sang phần SQL" : "Sang câu tiếp"}</span>

                        <svg className="icon" aria-hidden="true">

                            <use href="#tn-i-right"></use>

                        </svg>

                    </button>

                </div>

            </div>

        </section>

    </main>



    

    <footer className="footer">

        <div className="footer-inner">

            <p>

                <strong>DBCAS</strong>

                <span>•</span>

                <span>Nền tảng tự động Đánh giá Năng lực CSDL</span>

            </p>



            <nav aria-label="Thông tin cuối trang">

                <span>Quy chế khảo thí</span>

                <span>Chuẩn hóa 3NF</span>

                <span>Tài liệu SQL</span>

                <span>Hỗ trợ</span>

            </nav>

        </div>

    </footer>



    <div className="toast" role="status" aria-live="polite" hidden={!toast}>{toast}</div>



    

    <dialog className="submit-dialog" ref={dialogRef} onCancel={() => dialogRef.current?.close()} aria-labelledby="submit-dialog-title">

        <h2 id="submit-dialog-title">Xác nhận nộp bài</h2>



        <p>Bạn có chắc chắn muốn nộp bài thi không?</p>



        <p className="dialog-note">

            Chỉ câu trả lời đã bấm lưu được đưa vào bài nộp. Thời gian vẫn tiếp tục đếm ngược.

        </p>



        <p className="dialog-warning" role="status" aria-live="polite" hidden={remaining > 300}>

            Chỉ còn 5 phút

        </p>



        <div className="dialog-actions">

            <button className="action-button" onClick={() => dialogRef.current?.close()} type="button" autoFocus>

                Tiếp tục làm bài

            </button>



            <button className="action-button next-button" disabled={submitted} onClick={() => finishExam("manual")} type="button">

                Chắc chắn nộp bài

            </button>

        </div>

    </dialog>    
</div>;
}
