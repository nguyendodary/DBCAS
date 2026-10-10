import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import "./Xem_lai_bai_Learner.css";
import video from "./video1.mp4";
import poster from "./nen1.jpg";

// TODO BE:
// Dùng testId để lấy bài làm, điểm, đáp án và lời giải từ API.
// Hiện tất cả bài thi sử dụng cùng bộ câu hỏi mẫu bên dưới.

const mcqMaxScore = 0.4;
const essayScore = 1.8;

const mcqQuestions = [
  {
    number: 1,
    title:
      "Lược đồ quan hệ R được coi là đạt dạng chuẩn 1NF khi thỏa mãn điều kiện nào?",
    options: [
      "Không chứa phụ thuộc hàm bắc cầu qua khóa.",
      "Mọi miền giá trị thuộc tính chỉ chứa giá trị nguyên tử, không chứa tập hợp hoặc danh sách lặp.",
      "Mọi thuộc tính không khóa phụ thuộc hàm đầy đủ vào khóa chính.",
      "Với mọi phụ thuộc hàm X → Y, X phải là siêu khóa.",
    ],
    selected: 1,
    correct: 1,
  },
  {
    number: 2,
    title:
      "Cho R(MASV, MAMH, TenSV, Diem), khóa là (MASV, MAMH). Phụ thuộc hàm nào sau đây vi phạm 2NF?",
    options: [
      "MASV → TenSV: thuộc tính không khóa phụ thuộc vào một phần của khóa.",
      "(MASV, MAMH) → Diem.",
      "(MASV, MAMH) → TenSV, Diem.",
      "Không có phụ thuộc hàm nào vi phạm.",
    ],
    selected: 0,
    correct: 0,
  },
  {
    number: 3,
    title:
      "Điều kiện nào đúng với mọi phụ thuộc hàm không tầm thường X → Y để lược đồ đạt 3NF?",
    options: [
      "X phải là khóa chính duy nhất của lược đồ.",
      "Y phải chứa toàn bộ thuộc tính của lược đồ.",
      "X là siêu khóa hoặc mỗi thuộc tính trong Y − X thuộc ít nhất một khóa ứng viên.",
      "Không tồn tại bất kỳ phụ thuộc hàm nào.",
    ],
    selected: 2,
    correct: 2,
  },
  {
    number: 4,
    title:
      "Cho R(A, B, C, D, E) và tập phụ thuộc hàm bên dưới. Tập khóa ứng viên nào là đúng?",
    formula: "R(A, B, C, D, E)\nF = { AB → C, C → D, D → E, E → A }",
    options: [
      "AB và BC.",
      "AB và C.",
      "AB, CD và DE.",
      "AB, BC, BD và BE.",
    ],
    selected: 1,
    correct: 3,
    explanation:
      "B không xuất hiện ở vế phải của bất kỳ phụ thuộc hàm nào, " +
      "nên mọi khóa phải chứa B. Bao đóng của C là {C, D, E, A}, " +
      "thiếu B, vì vậy C không phải khóa. AB, BC, BD và BE đều " +
      "có bao đóng bằng toàn bộ R. B đơn lẻ không xác định được " +
      "các thuộc tính còn lại, nên bốn tập trên đều là khóa ứng viên tối thiểu.",
  },
  {
    number: 5,
    title:
      "Cho R(A, B, C, D, E, G), F = {A → B, BC → D, D → E, E → G}. Bao đóng của AC là gì?",
    options: [
      "{A, B, C}.",
      "{A, B, C, D, E, G}.",
      "{A, C, D, E}.",
      "{A, B, C, G}.",
    ],
    selected: 1,
    correct: 1,
  },
  {
    number: 6,
    title: "Thuộc tính khóa (prime attribute) được định nghĩa như thế nào?",
    options: [
      "Thuộc tính chỉ xuất hiện trong khóa chính đã chọn.",
      "Thuộc tính thuộc ít nhất một khóa ứng viên.",
      "Thuộc tính không bao giờ nhận giá trị NULL.",
      "Thuộc tính xuất hiện ở vế trái của mọi phụ thuộc hàm.",
    ],
    selected: 1,
    correct: 1,
  },
  {
    number: 7,
    title:
      "Thuật toán bảng kiểm tra Tableau có thể được sử dụng để kiểm tra tính chất nào của một phép phân rã?",
    options: [
      "Tính không mất mát thông tin.",
      "Tốc độ thực thi của câu lệnh SELECT.",
      "Số lượng chỉ mục cần tạo.",
      "Kích thước vật lý của cơ sở dữ liệu.",
    ],
    selected: 0,
    correct: 0,
  },
  {
    number: 8,
    title:
      "Thao tác nào KHÔNG thuộc các bước tìm phủ tối thiểu của tập phụ thuộc hàm?",
    options: [
      "Tách vế phải thành từng thuộc tính đơn.",
      "Loại bỏ thuộc tính dư thừa ở vế trái.",
      "Loại bỏ phụ thuộc hàm dư thừa.",
      "Bắt buộc thêm phụ thuộc hàm giữa khóa chính và khóa ngoại.",
    ],
    selected: 3,
    correct: 3,
  },
  {
    number: 9,
    title: "Điểm khác biệt chính giữa 3NF và BCNF là gì?",
    options: [
      "BCNF yêu cầu vế trái của mọi phụ thuộc hàm không tầm thường là siêu khóa, không có ngoại lệ cho thuộc tính khóa ở vế phải.",
      "BCNF cho phép nhiều thuộc tính đa trị hơn 3NF.",
      "3NF không sử dụng khái niệm phụ thuộc hàm.",
      "Mọi lược đồ đạt 3NF đều tự động đạt BCNF.",
    ],
    selected: 0,
    correct: 0,
  },
  {
    number: 10,
    title: "Ý nghĩa của phụ thuộc đa trị X ↠ Y trong lược đồ R là gì?",
    options: [
      "Với một giá trị X cố định, tập giá trị Y độc lập với tập giá trị của các thuộc tính còn lại R − X − Y.",
      "X chỉ xác định đúng một giá trị Y.",
      "Y luôn là khóa chính của R.",
      "X và Y phải có cùng số thuộc tính.",
    ],
    selected: 0,
    correct: 0,
  },
];

const sqlQuestions = [
  {
    number: 11,
    score: 1,
    maxScore: 1,
    title:
      "Viết truy vấn liệt kê khách hàng có tổng giá trị đơn hàng trong năm 2024 lớn hơn 100 triệu đồng.",
    description:
      "Kết quả gồm CustomerID, CustomerName, TotalOrders và TotalSpent; sắp xếp TotalSpent giảm dần.",
    code: `SELECT
    c.CustomerID,
    c.CustomerName,
    COUNT(DISTINCT o.OrderID) AS TotalOrders,
    SUM(od.Quantity * od.UnitPrice) AS TotalSpent
FROM Customers AS c
INNER JOIN Orders AS o
    ON o.CustomerID = c.CustomerID
INNER JOIN OrderDetails AS od
    ON od.OrderID = o.OrderID
WHERE o.OrderDate >= DATE '2024-01-01'
  AND o.OrderDate < DATE '2025-01-01'
GROUP BY
    c.CustomerID,
    c.CustomerName
HAVING SUM(od.Quantity * od.UnitPrice) > 100000000
ORDER BY TotalSpent DESC;`,
  },
  {
    number: 12,
    score: 1,
    maxScore: 1,
    title:
      "Cập nhật hạng khách hàng theo điểm tích lũy bằng một câu lệnh UPDATE sử dụng CASE.",
    description:
      "Từ 5000 điểm: VIP; từ 2000 điểm: Platinum; từ 500 điểm: Gold; còn lại: Standard.",
    code: `UPDATE Customers
SET CustomerTier = CASE
    WHEN LoyaltyPoints >= 5000 THEN 'VIP'
    WHEN LoyaltyPoints >= 2000 THEN 'Platinum'
    WHEN LoyaltyPoints >= 500 THEN 'Gold'
    ELSE 'Standard'
END;`,
  },
  {
    number: 13,
    score: 1,
    maxScore: 1,
    title:
      "Tạo bảng OrderDetails với khóa chính ghép, khóa ngoại và các ràng buộc kiểm tra dữ liệu.",
    description:
      "Khóa chính gồm OrderID, ProductID. Quantity phải lớn hơn 0; UnitPrice không âm. Xóa đơn hàng sẽ xóa các chi tiết liên quan.",
    code: `CREATE TABLE OrderDetails (
    OrderID INTEGER NOT NULL,
    ProductID INTEGER NOT NULL,
    Quantity INTEGER NOT NULL,
    UnitPrice NUMERIC(12, 2) NOT NULL,

    CONSTRAINT PK_OrderDetails
        PRIMARY KEY (OrderID, ProductID),

    CONSTRAINT FK_OrderDetails_Orders
        FOREIGN KEY (OrderID)
        REFERENCES Orders(OrderID)
        ON DELETE CASCADE,

    CONSTRAINT FK_OrderDetails_Products
        FOREIGN KEY (ProductID)
        REFERENCES Products(ProductID),

    CONSTRAINT CK_OrderDetails_Quantity
        CHECK (Quantity > 0),

    CONSTRAINT CK_OrderDetails_UnitPrice
        CHECK (UnitPrice >= 0)
);`,
  },
];

function Icon({ name }) {
  return (
    <svg className="icon" aria-hidden="true">
      <use href={`#review-i-${name}`} />
    </svg>
  );
}

function IconDefinitions() {
  return (
    <svg
      className="svg-definitions"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <symbol id="review-i-database" viewBox="0 0 24 24">
          <ellipse cx="12" cy="5" rx="8" ry="3" />
          <path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
          <path d="M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" />
        </symbol>

        <symbol id="review-i-home" viewBox="0 0 24 24">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </symbol>

        <symbol id="review-i-file" viewBox="0 0 24 24">
          <path d="M14 3H5v18h14V8z" />
          <path d="M14 3v5h5M8 12h8M8 16h8" />
        </symbol>

        <symbol id="review-i-chart" viewBox="0 0 24 24">
          <path d="M4 3v18h17M8 17v-5M13 17V7M18 17v-8" />
        </symbol>

        <symbol id="review-i-settings" viewBox="0 0 24 24">
          <path d="M3 6h18M3 12h18M3 18h18" />
          <circle cx="8" cy="6" r="2" />
          <circle cx="16" cy="12" r="2" />
          <circle cx="10" cy="18" r="2" />
        </symbol>

        <symbol id="review-i-bell" viewBox="0 0 24 24">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
        </symbol>

        <symbol id="review-i-check" viewBox="0 0 24 24">
          <path d="m5 12 4 4L19 6" />
        </symbol>

        <symbol id="review-i-close" viewBox="0 0 24 24">
          <path d="m6 6 12 12M18 6 6 18" />
        </symbol>

        <symbol id="review-i-clock" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </symbol>

        <symbol id="review-i-calendar" viewBox="0 0 24 24">
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M16 3v4M8 3v4M3 11h18" />
        </symbol>

        <symbol id="review-i-award" viewBox="0 0 24 24">
          <circle cx="12" cy="8" r="5" />
          <path d="m8 12-2 10 6-3 6 3-2-10" />
        </symbol>

        <symbol id="review-i-sparkles" viewBox="0 0 24 24">
          <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5ZM20 2v4M18 4h4" />
        </symbol>

        <symbol id="review-i-cap" viewBox="0 0 24 24">
          <path d="m2 9 10-5 10 5-10 5ZM6 11v6c4 3 8 3 12 0v-6M22 9v7" />
        </symbol>

        <symbol id="review-i-arrow" viewBox="0 0 24 24">
          <path d="m12 5-7 7 7 7M5 12h14" />
        </symbol>
      </defs>
    </svg>
  );
}

function MCQ({ question }) {
  const isCorrect = question.selected === question.correct;

  return (
    <article
      className={`question-card ${
        isCorrect ? "correct-card" : "incorrect-card"
      }`}
    >
      <header className="question-header">
        <span
          className={`question-badge ${
            isCorrect ? "green-badge" : "red-badge"
          }`}
        >
          CÂU {question.number} • TRẮC NGHIỆM
        </span>

        <span
          className={`score-badge ${
            isCorrect ? "green-score" : "red-score"
          }`}
        >
          <Icon name={isCorrect ? "check" : "close"} />
          {isCorrect ? mcqMaxScore : 0} / {mcqMaxScore} điểm
          {!isCorrect && " • Trả lời sai"}
        </span>
      </header>

      <div className="question-body">
        <h3 className="question-title">{question.title}</h3>

        {question.formula && (
          <pre className="formula-box">
            <code>{question.formula}</code>
          </pre>
        )}

        <div className="answers-grid">
          {question.options.map((answer, index) => {
            const selected = index === question.selected;
            const correct = index === question.correct;

            const stateClass = correct
              ? "answer-correct"
              : selected
                ? "answer-incorrect"
                : "";

            const stateText = correct
              ? selected
                ? "Bạn đã chọn • Đúng"
                : "Đáp án đúng"
              : selected
                ? "Bạn đã chọn • Sai"
                : "";

            return (
              <div
                key={index}
                className={`answer-option ${stateClass}`}
              >
                <span className="answer-letter">{"ABCD"[index]}</span>

                <div className="answer-content">
                  <span>{answer}</span>

                  {stateText && (
                    <span className="answer-state">{stateText}</span>
                  )}
                </div>

                {(correct || selected) && (
                  <Icon name={correct ? "check" : "close"} />
                )}
              </div>
            );
          })}
        </div>

        {question.explanation && (
          <section className="ai-panel wrong-ai">
            <h4 className="ai-heading">
              <Icon name="sparkles" />
              PHÂN TÍCH AI &amp; LỜI GIẢI CHI TIẾT
            </h4>

            <p>{question.explanation}</p>
          </section>
        )}
      </div>
    </article>
  );
}

function SQLCode({ code }) {
  const tokens =
    /(--[^\n]*|'(?:''|[^'])*'|\b(?:SELECT|FROM|WHERE|JOIN|INNER|ON|AS|COUNT|DISTINCT|SUM|GROUP|BY|HAVING|ORDER|DESC|DATE|UPDATE|SET|CASE|WHEN|THEN|ELSE|END|CREATE|TABLE|INTEGER|NOT|NULL|NUMERIC|CONSTRAINT|PRIMARY|KEY|FOREIGN|REFERENCES|DELETE|CASCADE|CHECK)\b|\b\d+(?:\.\d+)?\b)/gi;

  return code.split(tokens).map((part, index) => {
    // Phần tại vị trí lẻ là token được regex bắt.
    if (index % 2 === 0) {
      return <span key={index}>{part}</span>;
    }

    let className = "sql-keyword";

    if (part.startsWith("--")) {
      className = "sql-comment";
    } else if (part.startsWith("'")) {
      className = "sql-string";
    } else if (/^\d/.test(part)) {
      className = "sql-number";
    }

    return (
      <span key={index} className={className}>
        {part}
      </span>
    );
  });
}

function SQL({ question }) {
  const isCorrect = question.score > 0;

  return (
    <article
      className={`question-card ${
        isCorrect ? "correct-card" : "incorrect-card"
      }`}
    >
      <header className="question-header">
        <span
          className={`question-badge ${
            isCorrect ? "green-badge" : "red-badge"
          }`}
        >
          CÂU {question.number} • SQL
        </span>

        <span
          className={`score-badge ${
            isCorrect ? "green-score" : "red-score"
          }`}
        >
          <Icon name={isCorrect ? "check" : "close"} />
          {question.score} / {question.maxScore} điểm
        </span>
      </header>

      <div className="question-body">
        <h3 className="question-title">{question.title}</h3>

        <p className="question-description">{question.description}</p>

        <div className="code-editor">
          <div className="code-toolbar">
            <div className="code-file">
              <span className="window-dots" aria-hidden="true">
                <i />
                <i />
                <i />
              </span>

              <span>SQL</span>
            </div>

            <span className="code-status">Bài làm đã nộp</span>
          </div>

          <pre>
            <code>
              <SQLCode code={question.code} />
            </code>
          </pre>
        </div>
      </div>
    </article>
  );
}

function Essay() {
  return (
    <article className="question-card partial-card">
      <header className="question-header">
        <span className="question-badge amber-badge">
          CÂU 14 • TỰ LUẬN
        </span>

        <span className="score-badge amber-score">
          {essayScore} / 3 điểm
        </span>
      </header>

      <div className="question-body">
        <h3 className="question-title">
          Cho lược đồ R(A, B, C, D, E) với tập phụ thuộc hàm
          F = {"{A → B, B → C, C → D, D → E}"}. Phân rã R thành
          các lược đồ đạt BCNF và chứng minh tính bảo toàn phụ thuộc hàm.
        </h3>

        <div className="student-answer">
          <div className="answer-label-row">
            <strong>BÀI LÀM CỦA THÍ SINH NỘP</strong>

            <span className="deduction-label">
              Trừ 1.2 điểm: thiếu lập luận chứng minh
            </span>
          </div>

          <p>
            Phân rã thành R1(A, B), R2(B, C), R3(C, D) và R4(D, E).
            Tất cả các lược đồ đều đạt BCNF vì thuộc tính ở vế trái
            là khóa của từng lược đồ.
          </p>

          <p>
            Lược đồ bảo toàn phụ thuộc hàm vì các vế trái đều là khóa.
          </p>
        </div>

        <section className="ai-panel">
          <h4 className="ai-heading">
            <Icon name="sparkles" />
            LỜI GIẢI TỪ AI ASSESSMENT ENGINE
          </h4>

          <div className="ai-warning">
            <strong>Nhận xét về bài làm:</strong> Phương án phân rã đúng.
            Tuy nhiên, việc vế trái là khóa giải thích điều kiện BCNF,
            chưa chứng minh tính bảo toàn phụ thuộc hàm. Cần xét
            các phụ thuộc hàm được chiếu lên từng lược đồ.
          </div>

          <p>Các phụ thuộc hàm cơ sở và khóa tương ứng:</p>

          <div className="table-scroll">
            <table className="proof-table">
              <thead>
                <tr>
                  <th>Lược đồ</th>
                  <th>Phụ thuộc hàm cơ sở</th>
                  <th>Khóa</th>
                  <th>Chuẩn hóa</th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td>R1(A, B)</td>
                  <td>A → B</td>
                  <td>A</td>
                  <td className="bcnf-status">✓ BCNF</td>
                </tr>

                <tr>
                  <td>R2(B, C)</td>
                  <td>B → C</td>
                  <td>B</td>
                  <td className="bcnf-status">✓ BCNF</td>
                </tr>

                <tr>
                  <td>R3(C, D)</td>
                  <td>C → D</td>
                  <td>C</td>
                  <td className="bcnf-status">✓ BCNF</td>
                </tr>

                <tr>
                  <td>R4(D, E)</td>
                  <td>D → E</td>
                  <td>D</td>
                  <td className="bcnf-status">✓ BCNF</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="proof-conclusion">
            <strong>Chứng minh bảo toàn phụ thuộc hàm:</strong>

            <p>
              Đặt G = {"{A → B, B → C, C → D, D → E}"}.
              Đây là hợp các phụ thuộc hàm cơ sở trên bốn lược đồ.
              Vì G = F nên G⁺ = F⁺. Do đó phân rã bảo toàn
              phụ thuộc hàm.
            </p>

            <p>
              Phân rã cũng không mất mát thông tin: lần lượt tách
              theo D → E, C → D và B → C. Trong mỗi bước,
              phần giao xác định được một trong hai lược đồ
              được tạo ra.
            </p>
          </div>
        </section>
      </div>
    </article>
  );
}

function Recommendations() {
  return (
    <section className="recommendations">
      <div className="recommendation-heading">
        <span className="recommendation-icon">
          <Icon name="cap" />
        </span>

        <div>
          <h2>Khung Khuyến nghị Ôn tập Cốt lõi</h2>

          <p>
            Dựa trên hai nội dung cần cải thiện: xác định khóa ứng viên
            và chứng minh bảo toàn phụ thuộc hàm.
          </p>
        </div>
      </div>

      <div className="recommendation-grid">
        <article className="recommendation-item">
          <span className="recommendation-label cyan-text">
            TÀI LIỆU LÝ THUYẾT TRỌNG TÂM
          </span>

          <h3>Thuật toán Bao đóng &amp; Phủ tối thiểu</h3>

          <p>
            Ôn cách tính bao đóng thuộc tính, xác định khóa ứng viên
            và loại bỏ thuộc tính dư thừa trong tập phụ thuộc hàm.
          </p>

          <span className="resource-label">
            Tài liệu ôn tập • Chuẩn hóa lược đồ quan hệ
          </span>
        </article>

        <article className="recommendation-item">
          <span className="recommendation-label purple-text">
            LƯU Ý SAI LẦM CỐT LÕI
          </span>

          <h3>Đối chiếu 3NF vs BCNF</h3>

          <p>
            Phân biệt điều kiện của 3NF và BCNF. Kiểm tra tính
            không mất mát thông tin và tính bảo toàn phụ thuộc hàm
            sau phân rã.
          </p>

          <span className="resource-label">
            Gợi ý AI • Nội dung để tham khảo
          </span>
        </article>

        <article className="recommendation-item">
          <span className="recommendation-label green-text">
            KẾ HOẠCH TIẾP THEO
          </span>

          <h3>Phụ thuộc đa trị &amp; Chuẩn 4NF</h3>

          <p>
            Luyện tập phụ thuộc đa trị, cách phân rã đạt 4NF và
            kiểm tra kết quả bằng các ví dụ dữ liệu cụ thể.
          </p>

          <span className="resource-label">
            Lộ trình đề xuất • Bài luyện tập tiếp theo
          </span>
        </article>
      </div>
    </section>
  );
}

export default function XemLaiBaiLearner() {
  const [params] = useSearchParams();

  // TODO BE: lấy bài thi theo mã này.
  const testId = params.get("testId");

  const examTitle =
    params.get("title")?.trim() ||
    "Chuẩn hóa lược đồ Quan hệ & Phụ thuộc hàm (1NF - BCNF)";

  const examDate = params.get("date")?.trim() || "14/11/2024";

  const correctMCQ = mcqQuestions.filter(
    (question) => question.selected === question.correct,
  ).length;

  // Giữ cách đếm của giao diện gốc:
  // Câu SQL/tự luận có điểm > 0 được tính vào nhóm câu làm đúng.
  const correctSQL = sqlQuestions.filter(
    (question) => question.score > 0,
  ).length;

  const correctCount =
    correctMCQ + correctSQL + (essayScore > 0 ? 1 : 0);

  const questionCount = mcqQuestions.length + sqlQuestions.length + 1;

  const computedScore =
    correctMCQ * mcqMaxScore +
    sqlQuestions.reduce((sum, question) => sum + question.score, 0) +
    essayScore;

  const scoreValue = params.get("score");
  const receivedScore = scoreValue?.trim() ? Number(scoreValue) : NaN;

  const totalScore =
    Number.isFinite(receivedScore) &&
    receivedScore >= 0 &&
    receivedScore <= 10
      ? receivedScore
      : computedScore;

  const videoRef = useRef(null);
  const toastTimer = useRef(null);

  const [videoNotice, setVideoNotice] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    return () => {
      clearTimeout(toastTimer.current);
    };
  }, []);

  async function playVideo() {
    try {
      await videoRef.current?.play();
    } catch {
      setVideoNotice("Bấm Phát lại video để phát nền.");
    }
  }

  function retryVideo() {
    videoRef.current?.load();
    playVideo();
  }

  function showVideoError() {
    setVideoNotice(
      "Không tải được video nền. Kiểm tra file video1.mp4.",
    );
  }

  function showNotification() {
    clearTimeout(toastTimer.current);

    setNotice("Bạn chưa có thông báo mới.");

    toastTimer.current = setTimeout(() => {
      setNotice("");
    }, 3000);
  }

  return (
    <div
      className="dbcas-learner-review"
      data-test-id={testId ?? undefined}
    >
      <IconDefinitions />

      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <span className="brand-icon">
              <Icon name="database" />
            </span>

            <div>
              <strong>Datamaster</strong>
              <span>ASSESSMENT ENGINE</span>
            </div>
          </div>

          <nav className="main-nav" aria-label="Menu người học">
            <Link className="nav-link" to="/Home_Learner">
              <Icon name="home" />
              <span>Trang chủ</span>
            </Link>

            <Link className="nav-link" to="/Bai_kiem_tra_Learner">
              <Icon name="file" />
              <span>Bài kiểm tra</span>
            </Link>

            <Link className="nav-link active" to="/Phan_tich_Learner">
              <Icon name="chart" />
              <span>Xem đánh giá</span>
            </Link>

            <Link className="nav-link" to="/Cai_dat_Learner">
              <Icon name="settings" />
              <span>Cài đặt</span>
            </Link>
          </nav>

          <div className="toolbar-actions">
            <button
              type="button"
              className="notification-button"
              aria-label="Thông báo"
              onClick={showNotification}
            >
              <Icon name="bell" />
              <span className="notification-dot" />
            </button>

            <Link className="profile" to="/Cai_dat_Learner">
              <span className="avatar">HL</span>

              <span className="profile-info">
                <strong>Nguyễn Hoàng Long</strong>
                <span>long.nh20216049@sis.hust.edu.vn</span>
              </span>
            </Link>
          </div>
        </div>
      </header>

      <section className="detail-banner">
        <video
          ref={videoRef}
          className="detail-video"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          poster={poster}
          aria-hidden="true"
          onCanPlay={playVideo}
          onPlaying={() => setVideoNotice("")}
          onError={showVideoError}
        >
          <source
            src={video}
            type="video/mp4"
            onError={showVideoError}
          />
        </video>

        <div className="banner-overlay" />

        <div className="container detail-banner-content">
          <nav className="detail-breadcrumb" aria-label="Đường dẫn">
            <Link to="/Home_Learner">
              <Icon name="home" />
              Trang chủ
            </Link>

            <span>/</span>

            <Link to="/Phan_tich_Learner">
              Phân tích chi tiết
            </Link>

            <span>/</span>

            <span aria-current="page">Xem lại bài thi</span>
          </nav>

          <h1>{examTitle}</h1>

          <div className="exam-meta">
            <span>
              <Icon name="calendar" />
              Thời gian nộp:
              <strong>{examDate}</strong>
            </span>

            <span>
              <Icon name="clock" />
              Thời gian làm bài:
              <strong>42 phút / 45 phút</strong>
            </span>

            <span>
              <Icon name="award" />
              Điểm số:
              <strong>{totalScore.toFixed(1)} / 10</strong>
            </span>
          </div>

          <div
            className="video-notice"
            role="status"
            hidden={!videoNotice}
          >
            <span>{videoNotice}</span>

            <button type="button" onClick={retryVideo}>
              Phát lại video
            </button>
          </div>
        </div>
      </section>

      <main className="container main-content">
        <section
          className="summary-card"
          aria-label="Tổng quan kết quả"
        >
          <div className="summary-pills">
            <span className="summary-pill correct">
              <Icon name="check" />
              Câu làm đúng
              <strong>{correctCount}</strong>
            </span>

            <span className="summary-pill incorrect">
              <Icon name="close" />
              Câu làm sai
              <strong>{questionCount - correctCount}</strong>
            </span>
          </div>
        </section>

        <section className="exam-section">
          <h2 className="section-heading cyan">
            Phần I: Trắc nghiệm Lý thuyết &amp; Giải thuật CSDL
          </h2>

          <div className="question-list">
            {mcqQuestions.map((question) => (
              <MCQ key={question.number} question={question} />
            ))}
          </div>
        </section>

        <section className="exam-section">
          <h2 className="section-heading green">
            Phần II: Thực hành SQL Nâng cao
          </h2>

          <div className="question-list">
            {sqlQuestions.map((question) => (
              <SQL key={question.number} question={question} />
            ))}
          </div>
        </section>

        <section className="exam-section">
          <h2 className="section-heading amber">
            Phần III: Tự luận Giải thuật &amp; Chứng minh CSDL
          </h2>

          <Essay />
        </section>

        <Recommendations />

        <div className="back-row">
          <Link className="back-button" to="/Phan_tich_Learner">
            <Icon name="arrow" />
            Quay lại trang phân tích
          </Link>
        </div>
      </main>

      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <strong>DBCAS</strong>

            <span className="footer-dot">•</span>

            <span>Nền tảng tự động Đánh giá Năng lực CSDL</span>
          </div>

          <div className="footer-links">
            <span>Quy chế khảo thí</span>
            <span>Chuẩn hóa 3NF</span>
            <span>Tài liệu SQL</span>
            <span>Hỗ trợ</span>
          </div>
        </div>
      </footer>

      <div className="review-notification" role="status">
        {notice}
      </div>
    </div>
  );
}