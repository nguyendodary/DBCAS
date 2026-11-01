# Xác thực và refresh token

Đăng ký/login/RBAC, bcrypt và password recovery dùng service hiện có. Đăng ký
không cấp Admin; tên role trong API là `Learner`/`Administrator`. Password giới
hạn 72 byte theo bcrypt, không ghi mật khẩu/token vào log. `.env` cấu hình
`JWT_SECRET`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` (1–30,
mặc định 7). Production từ chối secret mặc định.

`POST /api/v1/auth/login` trả access JWT, account và thêm `refresh_token`,
`refresh_expires_in`. Client cũ bỏ qua hai trường mới vẫn dùng được. Client mới
gửi JSON `{"refresh_token":"<JWT>"}` tới `POST /api/v1/auth/refresh` để nhận cặp
mới, kể cả access đã hết hạn. Refresh token có purpose riêng, không thể dùng làm
access. Chỉ hash SHA-256 được lưu; mỗi refresh dùng một lần, family có hạn tuyệt
đối không kéo dài khi quay vòng. Khóa account rồi token trong transaction đảm bảo
hai request đồng thời không cùng thành công.

Replay thu hồi toàn family và các access có claim `sid`; transaction thu hồi được
commit trước khi trả 401. Client phải chỉ có một refresh request đang chạy, gộp
các request đợi cùng kết quả. Mất response refresh có thể yêu cầu đăng nhập lại,
không phát lại bearer đã dùng. Đổi mật khẩu/disable tài khoản vô hiệu hóa refresh.
Quyền đọc từ DB hiện tại, không tin role cũ trong JWT. Những dòng hết hạn hơn một
ngày được dọn cho account khi đăng nhập lại; hệ thống lớn cần job retention riêng.

`POST /api/v1/auth/logout` nhận cùng body, trả 204 lặp an toàn, thu hồi family và
access liên quan. Token OAuth/legacy không có family tiếp tục chính sách expiry/
password version hiện có. `/auth/renew` vẫn đòi access còn hiệu lực và giới hạn
phiên tuyệt đối 8 giờ; giữ `sid` khi renew, không bỏ qua thu hồi.

Frontend mới cần lưu refresh an toàn, tránh URL/log; hợp đồng hiện tại dùng JSON
bearer để giữ tương thích REST, chưa triển khai cookie refresh/CSRF cho UI của team.
Tham khảo [RFC 9700, refresh replay](https://www.rfc-editor.org/rfc/rfc9700.html#name-refresh-token-protection).

Kiểm tra: `python manage.py test tests/test_auth.py tests/test_rbac.py tests/test_shared_auth.py tests/test_password_reset.py tests/dn/test_refresh_tokens.py`.
