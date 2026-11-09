# Kịch bản demo 5 phút — DBCAS (midterm)

> Trạng thái đã chuẩn bị sẵn trên máy: stack healthy, 3 bài đã công bố của
> `learner@dbcas.local` (đủ cho Đánh giá tổng thể) và **1 bài #6 đang chờ
> Admin duyệt**. Luồng công bố đang ở mặc định **Tự động**.

## Địa chỉ và tài khoản

| Mục | Giá trị |
| --- | --- |
| Ứng dụng | http://localhost:18080 |
| API / Swagger | http://localhost:18000/docs |
| Hộp thư local (Mailpit) | http://localhost:18025 |
| Học viên | `learner@dbcas.local` · `linh@dbcas.local` · `minh@dbcas.local` |
| Quản trị | `admin@dbcas.local` |
| Mật khẩu chung | `Demo12345!` |

## Click path 5 phút

### 0:00–2:30 — Học viên

1. Đăng nhập `learner@dbcas.local` → **Tổng quan**: 3 lượt đã hoàn thành,
   điểm và nội dung cần ưu tiên.
2. **Luyện tập** → chọn khái niệm (hoặc *Chọn tất cả*) → giữ độ khó
   Dễ/Vừa/Khó → nguồn **Từ ngân hàng câu hỏi** → **5 câu** → **Bắt đầu**.
3. Làm nhanh 1–2 câu (trắc nghiệm/SQL), bấm **Nộp bài** → xác nhận.
4. Trang **Đánh giá bài làm**: điểm, nhận xét, điểm theo CLO/chủ đề/độ khó.
   Nếu chưa có API key, dòng "Đánh giá dự phòng theo quy tắc" là bình thường.
5. **Đánh giá tổng thể** (`/competency`) để thấy xu hướng ≥2 lượt và gap.

### 2:30–4:30 — Quản trị

1. Đăng xuất → đăng nhập `admin@dbcas.local`.
2. **Tổng quan nhóm**: số học viên, lượt đã kết thúc, bảng gap theo khái niệm.
3. **Duyệt bài**: mở bài **Nguyễn An · #6 · Chờ người chấm xác nhận**.
   Kiểm tra SQL/essay, nhập điểm xác nhận nếu cần → **Duyệt**.
4. Học viên **Kiểm tra cập nhật** ở trang kết quả để thấy bài đã công bố.
5. **Hệ thống**: chỉ ra 2 luồng **Tự động** / **Admin duyệt**; hiện để
   **Tự động** cho buổi demo.

### 4:30–5:00 — Chốt

- Nhấn mạnh: bài được tạo theo khái niệm/độ khó, plan đóng băng trước câu 1;
  SQL luôn lấy từ ngân hàng đã kiểm định; AI chỉ hỗ trợ sinh câu và chấm tự
  luận, có fallback; Admin duyệt là quyết định cuối.

## 3 mẹo dự phòng

1. **Stack lỗi/healthy chậm**: `npm run stop` → `npm start`; nếu vẫn lỗi
   `npm run reset` rồi `npm start` (2–4 phút). Kiểm tra
   `docker compose --project-name dbcas-local -f docker-compose.local.yml ps`
   và http://localhost:18080/readiness (phải trả 200).
2. **Mailpit**: mở http://localhost:18025 để chứng minh email đặt lại mật
   khẩu; đây là hộp thư local, không phải email thật.
3. **AI chậm/không key**: nói rõ hệ thống dùng prompt template + chấm dự
   phòng theo quy tắc; chờ dòng "Đánh giá dự phòng theo quy tắc" hoặc bấm
   **Kiểm tra cập nhật**. Không refresh trong lúc đang nộp bài.

## Dừng / reset

```bash
npm run stop     # dừng, giữ dữ liệu
npm start        # chạy lại
npm run reset    # xóa volume, seed lại dữ liệu demo (mất bài đã làm)
```
