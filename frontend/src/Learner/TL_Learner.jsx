import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import "./TL_Learner.css";

// TODO BE: lấy đề tự luận, gửi bài và nhận điểm/nhận xét AI qua API.
// Hiện chỉ lưu bài làm trên trình duyệt, chưa chấm điểm.
function readJSON(key) {try{return JSON.parse(localStorage.getItem(key)||"null");}catch{return null;}}
function formatTime(seconds) {const n=Math.max(0,Math.floor(seconds));return `${String(Math.floor(n/60)).padStart(2,"0")}:${String(n%60).padStart(2,"0")}`;}
function initialShared(key,testId,params) {
 const old=readJSON(key),requestedDeadline=Number(params.get("deadline")),duration=Number(params.get("duration"));
 if(old && Number.isFinite(old.deadline) && (!requestedDeadline || requestedDeadline===old.deadline)) return old;
 const durationMinutes=Number.isFinite(duration) && duration>=10 && duration<=120 ? duration : 50;
 return {testId,durationMinutes,deadline:Number.isFinite(requestedDeadline) && requestedDeadline>0 ? requestedDeadline : Date.now()+durationMinutes*60000,answers:{},currentIndex:0,submitted:false,remainingSeconds:durationMinutes*60};
}

export default function TLLearner(props) {
 const [params]=useSearchParams();const testId=params.get("testId")||"de-mau-01";
 return <EssayAttempt key={`${testId}:${params.get("deadline")||""}`} {...props} testId={testId} params={params} />;
}
function EssayAttempt({testId,params,listHref="/Bai_kiem_tra_Learner",tnHref="/TN_Learner",sqlHref="/SQL_Learner"}) {
 const navigate=useNavigate();const sharedKey=`dbcas-tn-attempt-v3:${testId}`,essayKey=sharedKey+":tl";
 const [shared,setShared]=useState(()=>initialShared(sharedKey,testId,params));const sharedRef=useRef(shared);
 const [essay,setEssay]=useState(()=>{const old=readJSON(essayKey);return old?.deadline===shared.deadline ? old : {deadline:shared.deadline,answers:{}};});const essayRef=useRef(essay);
 const [draft,setDraft]=useState(()=>essay.answers?.[14]||"");
 const [remaining,setRemaining]=useState(()=>shared.submitted ? Math.max(0,shared.remainingSeconds||0) : Math.max(0,Math.ceil((shared.deadline-Date.now())/1000)));
 const [counts,setCounts]=useState({mcq:0,sql:0}),[toast,setToast]=useState(""),[saveFailed,setSaveFailed]=useState(false);
 const dialogRef=useRef(null),toastTimer=useRef(null),redirectTimer=useRef(null),warned=useRef(false);
 const submitted=shared.submitted===true,savedAnswer=essay.answers?.[14]||"",isSaved=Boolean(savedAnswer.trim())&&savedAnswer===draft;
 const answerStatus=submitted ? (saveFailed ? "Bài đã kết thúc nhưng chưa lưu được bản nộp." : "Đã lưu bản nộp trên trình duyệt. Chưa kết nối BE.") : isSaved ? "Câu này đã lưu câu trả lời." : "Bài tự luận chưa lưu. Bấm Lưu câu trả lời để đưa vào bài nộp.";
 function showToast(message){clearTimeout(toastTimer.current);setToast(message);toastTimer.current=setTimeout(()=>setToast(""),4500);}
 function writeJSON(key,value){try{localStorage.setItem(key,JSON.stringify(value));return true;}catch{showToast("Không lưu được dữ liệu trên trình duyệt.");return false;}}
 function latestShared(){const latest=readJSON(sharedKey);return latest?.deadline===sharedRef.current.deadline ? latest : sharedRef.current;}
 function adoptShared(value){sharedRef.current=value;setShared(value);if(value.submitted){dialogRef.current?.close();setDraft(essayRef.current.answers?.[14]||"");setRemaining(Math.max(0,value.remainingSeconds||0));}}
 function sqlAnswers(){const old=readJSON(sharedKey+":sql");return old?.deadline===sharedRef.current.deadline ? old.answers||{} : {};}
 function refreshCounts(){const latest=latestShared(),sql=sqlAnswers();setCounts({mcq:Array.from({length:10},(_,i)=>i+1).filter(id=>Number.isInteger(latest.answers?.[id])).length,sql:[11,12,13].filter(id=>typeof sql[id]==="string"&&sql[id].trim()).length});}
 function commitEssay(value){if(!writeJSON(essayKey,value))return false;essayRef.current=value;setEssay(value);return true;}
 function canEdit(){const latest=latestShared();if(latest.submitted){adoptShared(latest);return false;}if(Date.now()>=latest.deadline){finishExam("timeout");return false;}return true;}
 function saveAnswer(){if(!canEdit())return;if(!draft.trim()){showToast("Bạn hãy nhập bài tự luận trước khi lưu.");return;}if(commitEssay({...essayRef.current,answers:{...essayRef.current.answers,[14]:draft}}))showToast("Đã lưu bài tự luận câu 14.");}
 function resetAnswer(){if(!canEdit())return;const answers={...essayRef.current.answers};delete answers[14];if(commitEssay({...essayRef.current,answers})){setDraft("");showToast("Đã xóa bài tự luận câu 14.");}}
 function sectionURL(path){const query=new URLSearchParams({testId,duration:String(shared.durationMinutes),deadline:String(shared.deadline)});return `${path}?${query.toString()}`;}
 function handleSection(event){if(!canEdit()){event.preventDefault();showToast("Bài thi đã kết thúc.");}}
 function openSubmit(){if(canEdit())dialogRef.current?.showModal();}
 function finishExam(reason){const current=latestShared();if(current.submitted){adoptShared(current);return;}const sql=sqlAnswers();const seconds=reason==="timeout" ? 0 : Math.max(0,Math.ceil((current.deadline-Date.now())/1000));const payload={testId,submittedAt:new Date().toISOString(),submissionReason:reason,durationMinutes:current.durationMinutes,deadline:current.deadline,answers:{mcq:{...current.answers},sql:[11,12,13].filter(id=>typeof sql[id]==="string"&&sql[id].trim()).map(id=>({questionId:id,answer:sql[id]})),essay:{...essayRef.current.answers}}};const finished={...current,submitted:true,remainingSeconds:seconds,submittedPayload:payload};adoptShared(finished);const saved=writeJSON(sharedKey,finished),archived=writeJSON(sharedKey+":last-submission",payload);setSaveFailed(!saved||!archived);
 // TODO BE: gọi API nộp payload, sau đó mới hiển thị kết quả thật.
 if(saved&&archived){showToast(reason==="timeout" ? "Đã hết giờ. Đã lưu bản nộp trên trình duyệt; chưa gửi BE." : "Đã lưu bản nộp trên trình duyệt; chưa gửi BE.");redirectTimer.current=setTimeout(()=>navigate(listHref),1800);}else showToast("Không lưu được bản nộp. Trang giữ nguyên để tránh mất bài.");}
 useEffect(()=>{writeJSON(sharedKey,sharedRef.current);refreshCounts();function tick(){const latest=latestShared();if(latest.submitted){if(!sharedRef.current.submitted)adoptShared(latest);return;}const seconds=Math.max(0,Math.ceil((latest.deadline-Date.now())/1000));setRemaining(seconds);if(seconds===0)finishExam("timeout");else if(seconds<=300&&!warned.current){warned.current=true;showToast("Chỉ còn 5 phút.");}}
 function refresh(){const old=readJSON(essayKey);if(old?.deadline===sharedRef.current.deadline){essayRef.current=old;setEssay(old);}tick();refreshCounts();}
 tick();const timer=setInterval(tick,1000);window.addEventListener("storage",refresh);window.addEventListener("focus",refresh);document.addEventListener("visibilitychange",refresh);
 return()=>{clearInterval(timer);clearTimeout(toastTimer.current);clearTimeout(redirectTimer.current);window.removeEventListener("storage",refresh);window.removeEventListener("focus",refresh);document.removeEventListener("visibilitychange",refresh);};},[]);
 return <div className="dbcas-learner-essay">


    <svg className="svg-library" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">



        <symbol id="tl-i-back" viewBox="0 0 24 24">

            <path d="m12 5-7 7 7 7M5 12h14"></path>

        </symbol>



        <symbol id="tl-i-clock" viewBox="0 0 24 24">

            <circle cx="12" cy="14" r="8"></circle>

            <path d="M12 10v4l3 2M9 2h6M12 2v4M18 6l2-2"></path>

        </symbol>



        <symbol id="tl-i-submit" viewBox="0 0 24 24">

            <path d="M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6"></path>

        </symbol>



        <symbol id="tl-i-list" viewBox="0 0 24 24">

            <rect x="4" y="3" width="16" height="18" rx="2"></rect>

            <path d="M8 8h1m3 0h4M8 12h1m3 0h4M8 16h1m3 0h4"></path>

        </symbol>



        <symbol id="tl-i-code" viewBox="0 0 24 24">

            <path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18"></path>

        </symbol>



        <symbol id="tl-i-edit" viewBox="0 0 24 24">

            <path d="m14 4 6 6M4 20l5-1L21 7l-5-5L4 14v6Z"></path>

        </symbol>



        <symbol id="tl-i-save" viewBox="0 0 24 24">

            <path d="M4 3h13l4 4v14H3V3h1Z"></path>

            <path d="M7 3v6h10V3M7 21v-8h10v8"></path>

        </symbol>



        <symbol id="tl-i-reset" viewBox="0 0 24 24">

            <path d="M3 10a9 9 0 1 1 2 9M3 4v6h6"></path>

        </symbol>

    </svg>



    <header className="exam-header">

        <div className="header-inner">

            <div className="exam-identity">

                <button className="back-button" onClick={() => submitted ? navigate(listHref) : openSubmit()} type="button">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tl-i-back"></use>

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



            <div className="header-actions">

                <div className={`timer-box${submitted ? " ended" : remaining <= 300 ? " warning" : ""}`}>

                    <svg className="timer-icon" aria-hidden="true">

                        <use href="#tl-i-clock"></use>

                    </svg>



                    <div>

                        <span className="timer-label">{submitted ? "ĐÃ KẾT THÚC" : "THỜI GIAN CÒN LẠI"}</span>



                        <div className="timer-values">

                            <strong>{formatTime(remaining)}</strong>

                            <span>/ {formatTime(shared.durationMinutes * 60)}</span>

                        </div>

                    </div>

                </div>



                <button className="submit-button" onClick={openSubmit} disabled={submitted} type="button">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tl-i-submit"></use>

                    </svg>

                    <span>{submitted ? "ĐÃ KẾT THÚC" : "NỘP BÀI THI"}</span>

                </button>

            </div>

        </div>

    </header>



    <main className="exam-layout">

        

        <aside className="question-sidebar">

            <Link className="section-link" to={sectionURL(tnHref)} onClick={handleSection}>

                <span className="section-name">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tl-i-list"></use>

                    </svg>

                    TRẮC NGHIỆM

                </span>



                <span className="saved-count">{counts.mcq}/10 ĐÃ LƯU</span>



                <strong className="section-points">4.0 ĐIỂM</strong>

            </Link>



            <Link className="section-link" to={sectionURL(sqlHref)} onClick={handleSection}>

                <span className="section-name">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tl-i-code"></use>

                    </svg>

                    THỰC HÀNH SQL

                </span>



                <span className="saved-count">{counts.sql}/3 ĐÃ LƯU</span>



                <strong className="section-points">3.0 ĐIỂM</strong>

            </Link>



            <section className="essay-section">

                <div className="essay-section-heading">

                    <h2>

                        <svg className="icon" aria-hidden="true">

                            <use href="#tl-i-edit"></use>

                        </svg> TỰ LUẬN

                    </h2>



                    <span className="doing-badge">{submitted ? "ĐÃ KẾT THÚC" : "ĐANG LÀM"}</span>

                </div>



                <div className="question-list-heading">

                    <span>DANH SÁCH CÂU TỰ LUẬN</span>

                    <strong>3.0 ĐIỂM</strong>

                </div>



                <div className="question-card active" aria-current="true">

                    <span className="card-number">14</span>



                    <span className="card-content">

                        <strong>

                            Chuẩn BCNF &amp; Chứng minh bảo toàn phụ thuộc hàm

                        </strong>

                        <span className="card-status">{savedAnswer.trim() ? "✓ ĐÃ LƯU" : "CHƯA LƯU"}</span>

                    </span>

                </div>

            </section>



            <p className="sidebar-note">

                Chỉ nội dung đã bấm lưu mới được đưa vào bài nộp. Chuyển phần thi sẽ bỏ thay đổi chưa lưu.

            </p>

        </aside>



        

        <section className="question-panel">

            <div className="question-meta">

                <span className="question-number">CÂU HỎI 14 / 14</span>

                <span className="question-score">Điểm: 3.0 điểm</span>

            </div>



            <div className="question-content" id="question-content">

                <h2 className="question-title">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tl-i-edit"></use>

                    </svg>

                    <span>

                        Chuẩn BCNF &amp; Chứng minh bảo toàn phụ thuộc hàm

                    </span>

                </h2>



                <div className="statement-box">

                    <h3>ĐỀ BÀI</h3>



                    <p>

                        Cho lược đồ quan hệ

                        <code>R(A, B, C, D, E)</code> với tập phụ thuộc hàm:

                    </p>



                    <pre>{"F = {\n    A → B,\n    B → C,\n    C → D,\n    D → E\n}"}</pre>



                    <h4>Yêu cầu:</h4>



                    <ol>

                        <li>

                            Tìm tất cả các khóa dự tuyển (Candidate Keys) của R và giải thích cách tìm.

                        </li>

                        <li>

                            Xác định dạng chuẩn cao nhất của R. Chỉ ra các phụ thuộc hàm vi phạm BCNF.

                        </li>

                        <li>

                            Phân rã R thành các lược đồ con đạt BCNF.

                        </li>

                        <li>

                            Chứng minh phép phân rã không mất thông tin (Lossless Join) và bảo toàn phụ thuộc hàm.

                        </li>

                    </ol>

                </div>

            </div>



            <div className="answer-heading">

                <svg className="icon" aria-hidden="true">

                    <use href="#tl-i-edit"></use>

                </svg>

                <label htmlFor="essay-input">Phần trả lời</label>

            </div>



            <textarea id="essay-input" aria-label="Bài làm tự luận" placeholder="Nhập bài tự luận của bạn tại đây..." spellCheck={false} autoComplete="off" value={draft} readOnly={submitted} onChange={event=>{if(canEdit())setDraft(event.target.value);}} />



            <div className={`answer-status${isSaved ? " saved" : ""}`} role="status" aria-live="polite">{answerStatus}</div>



            <div className="question-actions">

                <button className="secondary-button" disabled={submitted} onClick={()=>{if(canEdit())navigate(sectionURL(sqlHref));}} type="button">

                    <svg className="icon" aria-hidden="true">

                        <use href="#tl-i-back"></use>

                    </svg>

                    Quay lại câu hỏi SQL

                </button>



                <div className="right-actions">

                    <button className="reset-button" disabled={submitted} onClick={resetAnswer} type="button">

                        <svg className="icon" aria-hidden="true">

                            <use href="#tl-i-reset"></use>

                        </svg>

                        Đặt lại

                    </button>



                    <button className="secondary-button" disabled={submitted} onClick={saveAnswer} type="button">

                        <svg className="icon" aria-hidden="true">

                            <use href="#tl-i-save"></use>

                        </svg>

                        Lưu câu trả lời

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



    <dialog className="submit-dialog" ref={dialogRef} aria-labelledby="dialog-title">

        <h2 id="dialog-title">Xác nhận nộp bài</h2>



        <p>Bạn có chắc chắn muốn nộp bài thi không?</p>



        <p className="dialog-note">

            Chỉ câu trả lời đã bấm lưu được đưa vào bài nộp. Thời gian vẫn tiếp tục đếm ngược.

        </p>



        <p className="dialog-warning" hidden={remaining>300}>

            Chỉ còn 5 phút

        </p>



        <div className="dialog-actions">

            <button className="secondary-button" onClick={()=>dialogRef.current?.close()} type="button" autoFocus>

                Tiếp tục làm bài

            </button>



            <button className="next-button" disabled={submitted} onClick={()=>finishExam("manual")} type="button">

                Chắc chắn nộp bài

            </button>

        </div>

    </dialog>



    <div className="toast" role="status" aria-live="polite" hidden={!toast}>{toast}</div>
</div>;
}
