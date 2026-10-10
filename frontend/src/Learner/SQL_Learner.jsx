import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import "./SQL_Learner.css";

// TODO BE: tải câu hỏi SQL từ API. Chưa chạy Docker hoặc chấm SQL.
const SAMPLE_QUESTIONS = [{

                id: 11,

                shortTitle: "JOIN & CTE: Tổng hợp doanh thu",

                title: "Truy vấn JOIN đa bảng kèm CTE: Thống kê Doanh thu " +

                    "& Xếp hạng Khách hàng VIP 2024",

                description: "Viết truy vấn SQL trên cơ sở dữ liệu PostgreSQL, " +

                    "kết nối các bảng Customers, Orders và OrderDetails. " +

                    "Sử dụng CTE RevenuePerCustomer để tính tổng doanh thu " +

                    "trong năm 2024 theo công thức " +

                    "SUM(UnitPrice * Quantity * (1 - Discount)). " +

                    "Dùng DENSE_RANK() để xếp hạng khách hàng theo doanh thu " +

                    "giảm dần. Hiển thị CustomerID, CompanyName, " +

                    "TotalRevenue và VipRank.",

                schema: "Customers(CustomerID, CompanyName)\n" +

                    "Orders(OrderID, CustomerID, OrderDate)\n" +

                    "OrderDetails(OrderID, UnitPrice, Quantity, Discount)",

                starter: "-- Viết câu trả lời SQL của bạn bên dưới\n\n" +

                    "WITH RevenuePerCustomer AS (\n" +

                    "    -- Tổng hợp doanh thu khách hàng năm 2024\n" +

                    ")\n" +

                    "SELECT\n" +

                    "    -- Các cột cần hiển thị\n" +

                    "FROM RevenuePerCustomer;"

            }, {

                id: 12,

                shortTitle: "Window Function: DENSE_RANK",

                title: "Window Function: Xếp hạng doanh thu nhân viên",

                description: "Viết truy vấn lấy EmployeeID, DepartmentID và Revenue " +

                    "từ bảng Sales. Sử dụng DENSE_RANK() để xếp hạng " +

                    "doanh thu giảm dần trong từng phòng ban. " +

                    "Nhân viên có cùng doanh thu phải có cùng thứ hạng. " +

                    "Đặt tên cột xếp hạng là RevenueRank.",

                schema: "Sales(EmployeeID, DepartmentID, Revenue)",

                starter: "-- Xếp hạng doanh thu theo từng phòng ban\n\n" +

                    "SELECT\n" +

                    "    EmployeeID,\n" +

                    "    DepartmentID,\n" +

                    "    Revenue\n" +

                    "    -- Thêm biểu thức DENSE_RANK tại đây\n" +

                    "FROM Sales;"

            }, {

                id: 13,

                shortTitle: "DDL & Foreign Key CASCADE",

                title: "Thiết kế bảng và ràng buộc khóa ngoại",

                description: "Viết câu lệnh tạo bảng Departments và Employees. " +

                    "DepartmentID là khóa chính của Departments, " +

                    "DepartmentName không được NULL. EmployeeID là khóa " +

                    "chính của Employees, FullName không được NULL. " +

                    "DepartmentID trong Employees tham chiếu Departments. " +

                    "Khi xóa phòng ban, các nhân viên thuộc phòng ban đó " +

                    "được xóa theo bằng ON DELETE CASCADE.",

                schema: "Departments(DepartmentID, DepartmentName)\n" +

                    "Employees(EmployeeID, FullName, DepartmentID)",

                starter: "-- Tạo bảng và khai báo các ràng buộc\n\n" +

                    "CREATE TABLE Departments (\n" +

                    "    -- Khai báo các cột tại đây\n" +

                    ");\n\n" +

                    "CREATE TABLE Employees (\n" +

                    "    -- Khai báo các cột và khóa ngoại tại đây\n" +

                    ");"

            }];



            
function readJSON(key) {try{return JSON.parse(localStorage.getItem(key)||"null");}catch{return null;}}
function formatTime(seconds) {const n=Math.max(0,Math.floor(seconds));return `${String(Math.floor(n/60)).padStart(2,"0")}:${String(n%60).padStart(2,"0")}`;}
function initialShared(key,testId,params) {
 const old=readJSON(key),requestedDeadline=Number(params.get("deadline")),duration=Number(params.get("duration"));
 if(old && Number.isFinite(old.deadline) && (!requestedDeadline || requestedDeadline===old.deadline)) return old;
 const durationMinutes=Number.isFinite(duration) && duration>=10 && duration<=120 ? duration : 50;
 return {testId,durationMinutes,deadline:Number.isFinite(requestedDeadline) && requestedDeadline>0 ? requestedDeadline : Date.now()+durationMinutes*60000,answers:{},currentIndex:0,submitted:false,remainingSeconds:durationMinutes*60};
}
export default function SQLLearner(props) {
 const [params]=useSearchParams();const testId=params.get("testId")||"de-mau-01";
 return <SQLAttempt key={`${testId}:${params.get("deadline")||""}`} {...props} testId={testId} params={params} />;
}
function SQLAttempt({testId,params,questions=SAMPLE_QUESTIONS,listHref="/Bai_kiem_tra_Learner",tnHref="/TN_Learner",essayHref="/TL_Learner"}) {
 const navigate=useNavigate();const sharedKey=`dbcas-tn-attempt-v3:${testId}`,sqlKey=sharedKey+":sql";
 const [shared,setShared]=useState(()=>initialShared(sharedKey,testId,params));
 const sharedRef=useRef(shared);
 const [sqlState,setSQLState]=useState(()=>{const old=readJSON(sqlKey);return old?.deadline===shared.deadline ? {...old,currentIndex:Math.max(0,Math.min(questions.length-1,old.currentIndex||0))} : {deadline:shared.deadline,answers:{},currentIndex:0};});
 const sqlRef=useRef(sqlState);
 const [draft,setDraft]=useState(()=>sqlState.answers?.[questions[sqlState.currentIndex].id] ?? questions[sqlState.currentIndex].starter);
 const [remaining,setRemaining]=useState(()=>shared.submitted ? Math.max(0,shared.remainingSeconds||0) : Math.max(0,Math.ceil((shared.deadline-Date.now())/1000)));
 const [counts,setCounts]=useState({mcq:0,essay:0});const [toast,setToast]=useState("");const [saveFailed,setSaveFailed]=useState(false);
 const dialogRef=useRef(null),editorRef=useRef(null),gutterRef=useRef(null),toastTimer=useRef(null),redirectTimer=useRef(null),warned=useRef(false);
 const submitted=shared.submitted===true,currentIndex=sqlState.currentIndex,question=questions[currentIndex],savedAnswers=sqlState.answers||{};
 const isSaved=Boolean(savedAnswers[question.id]?.trim()) && savedAnswers[question.id]===draft;
 const answerStatus=submitted ? (saveFailed ? "Bài đã kết thúc nhưng chưa lưu được bản nộp." : "Đã lưu bản nộp trên trình duyệt. Chưa kết nối BE.") : isSaved ? "Câu này đã lưu câu trả lời." : "Câu trả lời chưa lưu. Bấm Lưu câu trả lời để đưa vào bài nộp.";
 function showToast(message){clearTimeout(toastTimer.current);setToast(message);toastTimer.current=setTimeout(()=>setToast(""),4000);}
 function writeJSON(key,value){try{localStorage.setItem(key,JSON.stringify(value));return true;}catch{showToast("Không lưu được dữ liệu trên trình duyệt.");return false;}}
 function latestShared(){const latest=readJSON(sharedKey);return latest?.deadline===sharedRef.current.deadline ? latest : sharedRef.current;}
 function adoptShared(value){sharedRef.current=value;setShared(value);if(value.submitted){dialogRef.current?.close();setDraft(sqlRef.current.answers?.[questions[sqlRef.current.currentIndex].id]??questions[sqlRef.current.currentIndex].starter);setRemaining(Math.max(0,value.remainingSeconds||0));}}
 function commitSQL(value){if(!writeJSON(sqlKey,value))return false;sqlRef.current=value;setSQLState(value);return true;}
 function essayAnswers(){const value=readJSON(sharedKey+":tl");return value?.deadline===sharedRef.current.deadline ? value.answers||{} : {};}
 function refreshCounts(){const latest=latestShared();setCounts({mcq:Array.from({length:10},(_,index)=>index+1).filter(id=>Number.isInteger(latest.answers?.[id])).length,essay:Object.values(essayAnswers()).some(value=>typeof value==="string" && value.trim()) ? 1 : 0});}
 function canEdit(){const latest=latestShared();if(latest.submitted){adoptShared(latest);return false;}if(Date.now()>=latest.deadline){finishExam("timeout");return false;}return true;}
 function saveAnswer(){if(!canEdit())return;if(!draft.trim()){showToast("Bạn hãy nhập câu trả lời SQL trước khi lưu.");return;}if(commitSQL({...sqlRef.current,answers:{...sqlRef.current.answers,[question.id]:draft}}))showToast(`Đã lưu câu ${question.id}.`);}
 function resetAnswer(){if(!canEdit())return;const answers={...sqlRef.current.answers};delete answers[question.id];if(commitSQL({...sqlRef.current,answers})){setDraft(question.starter);showToast(`Đã đặt lại câu ${question.id}.`);}}
 function changeQuestion(index){if(index<0||index>=questions.length)return;if(!sharedRef.current.submitted&&!canEdit())return;const next={...sqlRef.current,currentIndex:index};if(commitSQL(next)){setDraft(next.answers?.[questions[index].id]??questions[index].starter);if(editorRef.current)editorRef.current.scrollTop=0;if(gutterRef.current)gutterRef.current.style.transform="";}}
 function sectionURL(path){const query=new URLSearchParams({testId,duration:String(shared.durationMinutes),deadline:String(shared.deadline)});return `${path}?${query.toString()}`;}
 function handleSection(event){if(!canEdit()){event.preventDefault();showToast("Bài thi đã kết thúc.");}}
 function nextQuestion(){if(currentIndex<questions.length-1)changeQuestion(currentIndex+1);else if(canEdit())navigate(sectionURL(essayHref));}
 function openSubmit(){if(canEdit())dialogRef.current?.showModal();}
 function finishExam(reason){const current=latestShared();if(current.submitted){adoptShared(current);return;}const seconds=reason==="timeout" ? 0 : Math.max(0,Math.ceil((current.deadline-Date.now())/1000));const payload={testId,submittedAt:new Date().toISOString(),submissionReason:reason,durationMinutes:current.durationMinutes,deadline:current.deadline,answers:{mcq:{...current.answers},sql:questions.filter(q=>sqlRef.current.answers?.[q.id]?.trim()).map(q=>({questionId:q.id,answer:sqlRef.current.answers[q.id]})),essay:essayAnswers()}};const finished={...current,submitted:true,remainingSeconds:seconds,submittedPayload:payload};adoptShared(finished);const saved=writeJSON(sharedKey,finished),archived=writeJSON(sharedKey+":last-submission",payload);setSaveFailed(!saved||!archived);
 // TODO BE: gửi payload bằng API nộp bài. Không chạy/chấm SQL tại frontend.
 if(saved&&archived){showToast(reason==="timeout" ? "Đã hết giờ. Đã lưu bản nộp trên trình duyệt; chưa gửi BE." : "Đã lưu bản nộp trên trình duyệt; chưa gửi BE.");redirectTimer.current=setTimeout(()=>navigate(listHref),1800);}else showToast("Không lưu được bản nộp. Trang giữ nguyên để tránh mất bài.");}
 function handleEditorKey(event){if(event.key!=="Tab"||submitted)return;event.preventDefault();if(!canEdit())return;const start=event.currentTarget.selectionStart,end=event.currentTarget.selectionEnd;setDraft(value=>value.slice(0,start)+"    "+value.slice(end));requestAnimationFrame(()=>editorRef.current?.setSelectionRange(start+4,start+4));}
 useEffect(()=>{writeJSON(sharedKey,sharedRef.current);refreshCounts();function tick(){const latest=latestShared();if(latest.submitted){if(!sharedRef.current.submitted)adoptShared(latest);return;}const seconds=Math.max(0,Math.ceil((latest.deadline-Date.now())/1000));setRemaining(seconds);if(seconds===0)finishExam("timeout");else if(seconds<=300&&!warned.current){warned.current=true;showToast("Chỉ còn 5 phút.");}}
 function refresh(){const oldSQL=readJSON(sqlKey);if(oldSQL?.deadline===sharedRef.current.deadline){sqlRef.current=oldSQL;setSQLState(oldSQL);}tick();refreshCounts();}
 tick();const timer=setInterval(tick,1000);window.addEventListener("storage",refresh);window.addEventListener("focus",refresh);document.addEventListener("visibilitychange",refresh);
 return()=>{clearInterval(timer);clearTimeout(toastTimer.current);clearTimeout(redirectTimer.current);window.removeEventListener("storage",refresh);window.removeEventListener("focus",refresh);document.removeEventListener("visibilitychange",refresh);};},[]);
 return <div className="dbcas-learner-sql">


    <svg className="svg-library" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">



        <symbol id="sql-i-back" viewBox="0 0 24 24">

            <path d="m12 5-7 7 7 7M5 12h14"></path>

        </symbol>



        <symbol id="sql-i-clock" viewBox="0 0 24 24">

            <circle cx="12" cy="14" r="8"></circle>

            <path d="M12 10v4l3 2M9 2h6M12 2v4M18 6l2-2"></path>

        </symbol>



        <symbol id="sql-i-submit" viewBox="0 0 24 24">

            <path d="M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6"></path>

        </symbol>



        <symbol id="sql-i-code" viewBox="0 0 24 24">

            <path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18"></path>

        </symbol>



        <symbol id="sql-i-list" viewBox="0 0 24 24">

            <rect x="4" y="3" width="16" height="18" rx="2"></rect>

            <path d="M8 8h1m3 0h4M8 12h1m3 0h4M8 16h1m3 0h4"></path>

        </symbol>



        <symbol id="sql-i-edit" viewBox="0 0 24 24">

            <path d="m14 4 6 6M4 20l5-1L21 7l-5-5L4 14v6Z"></path>

        </symbol>



        <symbol id="sql-i-save" viewBox="0 0 24 24">

            <path d="M4 3h13l4 4v14H3V3h1Z"></path>

            <path d="M7 3v6h10V3M7 21v-8h10v8"></path>

        </symbol>



        <symbol id="sql-i-reset" viewBox="0 0 24 24">

            <path d="M3 10a9 9 0 1 1 2 9M3 4v6h6"></path>

        </symbol>



        <symbol id="sql-i-next" viewBox="0 0 24 24">

            <path d="M5 12h14m-7-7 7 7-7 7"></path>

        </symbol>

    </svg>



    <header className="exam-header">

        <div className="header-inner">

            <div className="exam-identity">

                <button className="back-button" onClick={() => submitted ? navigate(listHref) : openSubmit()} type="button">

                    <svg className="icon" aria-hidden="true">

                        <use href="#sql-i-back"></use>

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

                        <use href="#sql-i-clock"></use>

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

                        <use href="#sql-i-submit"></use>

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

                        <use href="#sql-i-list"></use>

                    </svg>

                    TRẮC NGHIỆM

                </span>



                <span className="saved-count">{counts.mcq}/10 ĐÃ LƯU</span>



                <strong className="section-points">4.0 ĐIỂM</strong>

            </Link>



            

            <section className="sql-section">

                <div className="sql-section-heading">

                    <h2>

                        <svg className="icon" aria-hidden="true">

                            <use href="#sql-i-code"></use>

                        </svg> THỰC HÀNH SQL

                    </h2>



                    <span className="doing-badge">{submitted ? "ĐÃ KẾT THÚC" : "ĐANG LÀM"}</span>

                </div>



                <div className="question-list-heading">

                    <span>DANH SÁCH CÂU HỎI SQL</span>

                    <strong>3.0 ĐIỂM</strong>

                </div>



                <div className="question-list">{questions.map((item,index) => <button key={item.id} type="button" className={`question-card${index===currentIndex ? " active" : ""}`} aria-current={index===currentIndex ? "true" : undefined} onClick={()=>changeQuestion(index)}><span className="card-number">{item.id}</span><span className="card-content"><strong>{item.shortTitle}</strong><span className="card-status">{savedAnswers[item.id]?.trim() ? "✓ ĐÃ LƯU" : index===currentIndex && !submitted ? "ĐANG LÀM" : "CHƯA LƯU"}</span></span></button>)}</div>

            </section>



            

            <Link className="section-link" to={sectionURL(essayHref)} onClick={handleSection}>

                <span className="section-name">

                    <svg className="icon" aria-hidden="true">

                        <use href="#sql-i-edit"></use>

                    </svg>

                    TỰ LUẬN

                </span>



                <span className="saved-count">{counts.essay}/1 ĐÃ LƯU</span>



                <strong className="section-points">3.0 ĐIỂM</strong>

            </Link>



            <p className="sidebar-note">

                Chỉ câu trả lời đã lưu mới được đưa vào bài nộp. Chuyển câu sẽ bỏ phần thay đổi chưa lưu.

            </p>

        </aside>



        <section className="question-panel">

            <div className="question-meta">

                <span className="question-number">CÂU HỎI {question.id} / 14</span>

                <span className="question-score">Điểm: 1.0 điểm</span>

            </div>



            <div className="question-content" id="question-content">

                <h2 className="question-title">

                    <svg className="icon" aria-hidden="true">

                        <use href="#sql-i-code"></use>

                    </svg>

                    <span>{question.title}</span>

                </h2>



                <p className="question-description">{question.description}</p>

                <pre className="schema-box">{question.schema}</pre>

            </div>



            <div className="editor-heading">

                <div className="editor-caption">

                    <span className="window-dots" aria-hidden="true">

                        <i></i><i></i><i></i>

                    </span>



                    <svg className="icon" aria-hidden="true">

                        <use href="#sql-i-code"></use>

                    </svg>



                    <span>SQL EDITOR</span>

                </div>

            </div>



            <div className="sql-editor">

                <div className="line-gutter" aria-hidden="true">

                    <pre ref={gutterRef}>{Array.from({length:draft.split("\n").length},(_,index)=>index+1).join("\n")}</pre>

                </div>



                <textarea id="sql-input" ref={editorRef} aria-label="Câu trả lời SQL" placeholder="Nhập câu lệnh SQL của bạn tại đây..." spellCheck={false} autoComplete="off" autoCapitalize="off" wrap="off" value={draft} readOnly={submitted} onChange={event=>{if(canEdit()) setDraft(event.target.value);}} onScroll={event=>{if(gutterRef.current) gutterRef.current.style.transform=`translateY(-${event.currentTarget.scrollTop}px)`;}} onKeyDown={handleEditorKey} />

            </div>



            <div className={`answer-status${isSaved ? " saved" : ""}`} role="status" aria-live="polite">{answerStatus}</div>



            <div className="question-actions">

                <button className="secondary-button" type="button" disabled={currentIndex===0} onClick={()=>changeQuestion(currentIndex-1)}>

                    <svg className="icon" aria-hidden="true">

                        <use href="#sql-i-back"></use>

                    </svg>

                    <span>Câu trước</span>

                </button>



                <div className="right-actions">

                    <button className="reset-button" disabled={submitted} onClick={resetAnswer} type="button">

                        <svg className="icon" aria-hidden="true">

                            <use href="#sql-i-reset"></use>

                        </svg>

                        Đặt lại

                    </button>



                    <button className="secondary-button" disabled={submitted} onClick={saveAnswer} type="button">

                        <svg className="icon" aria-hidden="true">

                            <use href="#sql-i-save"></use>

                        </svg>

                        Lưu câu trả lời

                    </button>



                    <button className="next-button" onClick={nextQuestion} type="button">

                        <span>{currentIndex===questions.length-1 ? "Chuyển sang tự luận" : "Sang câu tiếp"}</span>

                        <svg className="icon" aria-hidden="true">

                            <use href="#sql-i-next"></use>

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
