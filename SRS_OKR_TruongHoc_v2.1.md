# TÀI LIỆU ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)
# HỆ THỐNG QUẢN LÝ MỤC TIÊU (OKR) TRƯỜNG HỌC — PHIÊN BẢN 2.1

---

## I. TỔNG QUAN HỆ THỐNG

### Mục đích
Xây dựng ứng dụng web quản lý mục tiêu theo phương pháp OKR cho học sinh,
kết nối giữa Nhà trường (Quản trị viên, Giáo viên chủ nhiệm) và Gia đình
(Học sinh, Phụ huynh). Hệ thống theo dõi tiến độ theo thời gian thực,
thông báo tự động, và tích hợp trí tuệ nhân tạo hỗ trợ nhận xét.

### Nguyên tắc giao diện
- Toàn bộ giao diện, thông báo, nhãn, nút bấm, thông điệp lỗi: thuần tiếng Việt
- Không dùng từ tiếng Anh lẫn vào giao diện người dùng
- Phong cách chuyên nghiệp, hiện đại — tham khảo thiết kế ứng dụng FOKR
- Cỡ chữ vừa phải (14–15px nội dung, 13px nhãn phụ)
- Bố cục: Thanh điều hướng trái — Danh sách giữa — Chi tiết phải

### Công nghệ

| Lớp           | Công nghệ                                          |
|---------------|----------------------------------------------------|
| Giao diện     | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Máy chủ       | FastAPI (Python 3.11), Uvicorn                     |
| Cơ sở dữ liệu | Supabase (PostgreSQL)                              |
| Xác thực      | JWT tự quản lý + bcrypt                            |
| Thời gian thực| Supabase Realtime (WebSocket)                      |
| Gửi email     | Resend API                                         |
| Trí tuệ nhân tạo | Anthropic Claude API (claude-sonnet-4-20250514) |
| Xuất báo cáo  | python-docx (Word .docx, không lỗi font)           |
| Biểu đồ       | Recharts                                           |
| Kéo thả       | @dnd-kit/core                                      |
| Trạng thái    | Zustand + React Query                              |

### Quy mô triển khai
1 trường, khoảng 500 học sinh.

---

## II. BẢNG THUẬT NGỮ CHUẨN (tiếng Việt)

| Thuật ngữ cũ (không dùng) | Thuật ngữ chuẩn trong hệ thống       |
|---------------------------|---------------------------------------|
| Check-in                  | Cập nhật tiến độ                      |
| Dashboard                 | Trang tổng quan                       |
| Kanban                    | Bảng theo dõi lớp                     |
| Template / Mẫu            | Mẫu mục tiêu                          |
| Import                    | Nhập danh sách                        |
| Export                    | Xuất báo cáo                          |
| Chốt sổ                   | Hoàn tất đánh giá                     |
| Streak                    | Chuỗi ngày cập nhật                   |
| Approved / Pending        | Đã duyệt / Chờ duyệt                  |
| Finalized                 | Đã hoàn tất                           |
| Role                      | Vai trò                               |
| Period / Đợt              | Kỳ đánh giá                           |
| Key Result (KR)           | Kết quả then chốt                     |
| Objective                 | Mục tiêu                              |
| Feedback                  | Nhận xét / Phản hồi                   |
| Rating / Stars            | Đánh giá (thang điểm sao)            |
| PDF / Word Export         | Xuất báo cáo Word (.docx)             |
| Admin                     | Quản trị viên                         |
| Teacher                   | Giáo viên chủ nhiệm                   |
| Student                   | Học sinh                              |
| Parent                    | Phụ huynh                             |

---

## III. CƠ SỞ DỮ LIỆU — 8 BẢNG (Supabase PostgreSQL)

### 1. nguoi_dung (users)
| Cột                    | Kiểu                  | Ghi chú                                        |
|------------------------|-----------------------|------------------------------------------------|
| id                     | UUID PK               | gen_random_uuid()                              |
| email                  | TEXT UNIQUE NOT NULL  | Email đăng nhập                                |
| mat_khau_hash          | TEXT NOT NULL         | bcrypt hash                                    |
| vai_tro                | TEXT                  | 'quan_tri' / 'giao_vien' / 'hoc_sinh' / 'phu_huynh' |
| ho_ten                 | TEXT NOT NULL         | Họ tên đầy đủ                                 |
| ten_lop                | TEXT                  | Lớp chủ nhiệm (GV) hoặc lớp học (HS)          |
| email_phu_huynh        | TEXT                  | Email phụ huynh của học sinh                   |
| si_so                  | INTEGER               | Sĩ số lớp (GV)                                |
| bat_buoc_doi_mat_khau  | BOOLEAN DEFAULT true  | Bắt đổi mật khẩu lần đầu                      |
| dang_hoat_dong         | BOOLEAN DEFAULT true  | Tài khoản còn hoạt động                        |
| ngay_tao               | TIMESTAMPTZ           | Tự động                                        |
| ngay_cap_nhat          | TIMESTAMPTZ           | Tự cập nhật qua trigger                        |

### 2. ky_danh_gia (periods)
| Cột          | Kiểu                 | Ghi chú                               |
|--------------|----------------------|---------------------------------------|
| id           | UUID PK              |                                       |
| ten_ky       | TEXT NOT NULL        | VD: "Học kỳ 1 — 2025"                |
| trang_thai   | TEXT                 | 'mo' / 'khoa'                         |
| ngay_bat_dau | DATE                 | Ngày bắt đầu                          |
| ngay_ket_thuc| DATE                 | Ngày kết thúc                         |
| nguoi_tao    | UUID FK → nguoi_dung | Quản trị viên tạo                     |
| ngay_tao     | TIMESTAMPTZ          |                                       |

### 3. muc_tieu (okrs)
| Cột                 | Kiểu                    | Ghi chú                                                              |
|---------------------|-------------------------|----------------------------------------------------------------------|
| id                  | UUID PK                 |                                                                      |
| hoc_sinh_id         | UUID FK → nguoi_dung    | Học sinh sở hữu                                                      |
| ky_danh_gia_id      | UUID FK → ky_danh_gia   | Thuộc kỳ nào — bắt buộc chọn khi tạo                               |
| loai_okr            | TEXT                    | 'ca_nhan' / 'nhom' / 'lop' (tương tự FOKR)                         |
| muc_tieu_lon        | TEXT NOT NULL           | Objective — mục tiêu lớn                                            |
| ket_qua_then_chot   | TEXT NOT NULL           | Key Result — kết quả đo được                                        |
| chi_tieu            | DECIMAL NOT NULL        | Con số đích cần đạt                                                  |
| thuc_dat            | DECIMAL DEFAULT 0       | Thực đạt hiện tại                                                    |
| don_vi              | TEXT NOT NULL           | Đơn vị: điểm, cuốn, giờ, %...                                      |
| tien_do_phan_tram   | DECIMAL DEFAULT 0       | Tự tính qua trigger                                                  |
| trang_thai          | TEXT DEFAULT 'cho_duyet'| 'cho_duyet' / 'da_duyet' / 'yeu_cau_sua' / 'xin_xoa'               |
| han_hoan_thanh      | DATE                    | Deadline (hiển thị "còn N ngày" như FOKR)                           |
| nhan_xet_giao_vien  | TEXT                    | Nhận xét của giáo viên                                               |
| diem_phu_huynh      | INTEGER                 | Đánh giá phụ huynh (1–5 sao)                                        |
| ngay_tao            | TIMESTAMPTZ             |                                                                      |
| ngay_cap_nhat       | TIMESTAMPTZ             |                                                                      |

### 4. lich_su_cap_nhat (checkin_history)
| Cột              | Kiểu                  | Ghi chú                          |
|------------------|-----------------------|----------------------------------|
| id               | UUID PK               |                                  |
| muc_tieu_id      | UUID FK → muc_tieu    |                                  |
| gia_tri_dat_duoc | DECIMAL NOT NULL      | Số thực đạt tại thời điểm        |
| tien_do          | DECIMAL NOT NULL      | % tại thời điểm                  |
| ghi_chu          | TEXT                  | Ghi chú của học sinh             |
| thoi_diem        | TIMESTAMPTZ DEFAULT now() |                              |

### 5. danh_gia_cuoi_ky (final_reviews)
| Cột             | Kiểu                    | Ghi chú                             |
|-----------------|-------------------------|-------------------------------------|
| id              | UUID PK                 |                                     |
| hoc_sinh_id     | UUID FK → nguoi_dung    |                                     |
| ky_danh_gia_id  | UUID FK → ky_danh_gia   |                                     |
| nhan_xet_gv     | TEXT                    | Nhận xét tổng kết của giáo viên     |
| phan_hoi_ph     | TEXT                    | Ý kiến của phụ huynh                |
| trang_thai      | TEXT DEFAULT 'mo'       | 'mo' / 'hoan_tat'                   |
| thoi_diem_hoan_tat | TIMESTAMPTZ          | Khi giáo viên hoàn tất đánh giá     |
| UNIQUE          | (hoc_sinh_id, ky_danh_gia_id) | Mỗi HS chỉ có 1 đánh giá/kỳ  |

### 6. mau_muc_tieu (okr_templates)
| Cột                   | Kiểu                    | Ghi chú                         |
|-----------------------|-------------------------|---------------------------------|
| id                    | UUID PK                 |                                 |
| ten_mau               | TEXT NOT NULL           | Tên mẫu mục tiêu                |
| muc_tieu_lon_mau      | TEXT NOT NULL           | Mẫu câu mục tiêu lớn            |
| ket_qua_then_chot_mau | TEXT NOT NULL           | Mẫu câu kết quả then chốt       |
| don_vi_mac_dinh       | TEXT NOT NULL           | Đơn vị mặc định                 |
| loai_okr              | TEXT                    | 'ca_nhan' / 'nhom' / 'lop'     |
| ten_lop               | TEXT                    | Áp dụng lớp nào (rỗng = tất cả)|
| nguoi_tao             | UUID FK → nguoi_dung    |                                 |
| dang_hien_thi         | BOOLEAN DEFAULT true    |                                 |
| ngay_tao              | TIMESTAMPTZ             |                                 |

### 7. thong_bao (notifications)
| Cột        | Kiểu                    | Ghi chú          |
|------------|-------------------------|------------------|
| id         | UUID PK                 |                  |
| nguoi_nhan | UUID FK → nguoi_dung    | Người nhận       |
| loai       | TEXT                    | Loại thông báo   |
| tieu_de    | TEXT NOT NULL           | Tiêu đề          |
| noi_dung   | TEXT NOT NULL           | Nội dung         |
| da_doc     | BOOLEAN DEFAULT false   |                  |
| ngay_tao   | TIMESTAMPTZ             |                  |

### 8. nhat_ky_hoat_dong (audit_logs)
| Cột         | Kiểu        | Ghi chú                         |
|-------------|-------------|---------------------------------|
| id          | UUID PK     |                                 |
| nguoi_dung_id | UUID      | Người thực hiện                 |
| hanh_dong   | TEXT NOT NULL | Tên hành động                 |
| ten_bang    | TEXT        | Bảng bị tác động                |
| id_ban_ghi  | UUID        | ID bản ghi bị tác động          |
| gia_tri_cu  | JSONB       | Giá trị trước thay đổi          |
| gia_tri_moi | JSONB       | Giá trị sau thay đổi            |
| dia_chi_ip  | TEXT        | Địa chỉ IP                      |
| thoi_diem   | TIMESTAMPTZ |                                 |

### Database Triggers
- **tu_dong_cap_nhat_thoi_gian**: BEFORE UPDATE → gán ngay_cap_nhat = now() cho các bảng có cột này
- **tu_dong_tinh_tien_do**: AFTER INSERT trên lich_su_cap_nhat → UPDATE muc_tieu SET thuc_dat, tien_do_phan_tram = ROUND((thuc_dat/chi_tieu)*100, 1)
- **kiem_tra_ky_bi_khoa**: BEFORE INSERT/UPDATE trên muc_tieu → nếu ky_danh_gia.trang_thai = 'khoa' thì RAISE EXCEPTION 'Kỳ đánh giá đã bị khóa, không thể thay đổi mục tiêu'

---

## IV. CHI TIẾT CHỨC NĂNG THEO 4 VAI TRÒ

---

### VAI TRÒ 1: QUẢN TRỊ VIÊN

**Đăng nhập:**
- Tài khoản mặc định: `admin@truong.edu.vn` / `Admin@2025`
- Bắt buộc đổi mật khẩu ngay lần đầu đăng nhập
- Có thể vào trang tổng quan ngay cả khi chưa có kỳ đánh giá nào

**Bố cục giao diện:**
- Thanh điều hướng trái: Tổng quan | Kỳ đánh giá | Giáo viên | Nhật ký hoạt động
- Khu vực chính: nội dung từng mục

**Quản lý kỳ đánh giá:**
- Tạo kỳ mới: tên kỳ (VD: "Học kỳ 1 — 2025"), ngày bắt đầu, ngày kết thúc
- Mở kỳ: cho phép học sinh và giáo viên nhập liệu
- Khóa kỳ: đóng băng toàn bộ — trigger database chặn mọi thao tác ghi

**Quản lý tài khoản giáo viên:**
- Thêm thủ công: họ tên, email, lớp chủ nhiệm, sĩ số
- Nhập danh sách: tải lên file `.xlsx`, hệ thống tự tạo tài khoản hàng loạt, báo cáo số thành công/lỗi
- Vô hiệu hóa tài khoản (dữ liệu lịch sử giữ nguyên)
- Reset mật khẩu về mặc định

**Trang tổng quan toàn trường:**
- Bảng theo lớp: Tên giáo viên — Sĩ số — Số HS đã nộp mục tiêu — Số HS đã được duyệt — Tỉ lệ hoàn thành (%)
- Bộ lọc theo kỳ đánh giá

**Nhật ký hoạt động:**
- Xem lịch sử: ai thao tác gì, lúc nào, từ địa chỉ IP nào
- Lọc theo người dùng, loại hành động, khoảng thời gian
- Chỉ Quản trị viên mới truy cập được

**Tóm tắt lớp bằng trí tuệ nhân tạo:**
- Chọn lớp và kỳ → Claude AI đọc dữ liệu tiến độ, tự viết tóm tắt ngắn gọn
- Output: lớp nào đang tốt, lớp nào cần chú ý, xu hướng chung

---

### VAI TRÒ 2: GIÁO VIÊN CHỦ NHIỆM

**Đăng nhập:**
- Email và mật khẩu do Quản trị viên cấp, bắt buộc đổi lần đầu
- Chỉ thấy dữ liệu của lớp chủ nhiệm mình

**Bố cục giao diện (tham khảo FOKR):**
- Thanh điều hướng trái: Tổng quan lớp | Danh sách học sinh | Mẫu mục tiêu | Báo cáo
- Danh sách giữa: học sinh với trạng thái màu
- Chi tiết phải: nội dung mục tiêu, nhận xét, thao tác

**Quản lý danh sách học sinh:**
- Thêm thủ công: họ tên, email, email phụ huynh
- Nhập danh sách: tải lên file `.xlsx` để tạo tài khoản hàng loạt đầu kỳ
- Sửa thông tin: email học sinh, email phụ huynh
- Reset mật khẩu học sinh về mặc định
- Vô hiệu hóa tài khoản

**Bảng theo dõi lớp (thay thế Kanban):**
- Bảng danh sách học sinh với các cột: Họ tên — Số mục tiêu — Trạng thái — Tiến độ TB (%) — Cập nhật gần nhất — Thao tác
- Lọc theo trạng thái: Tất cả | Chờ duyệt | Đã duyệt | Đã hoàn tất
- Màu trạng thái trực quan: Chờ duyệt (vàng) | Đã duyệt (xanh lá) | Đã hoàn tất (xanh đậm) | Cần sửa (đỏ)

**Xem chi tiết mục tiêu học sinh:**
- Click vào tên học sinh → panel phải hiện chi tiết toàn bộ mục tiêu
- Mỗi mục tiêu hiện: tên mục tiêu lớn, kết quả then chốt, chỉ tiêu, thực đạt, % tiến độ, hạn hoàn thành, lịch sử cập nhật
- Tương tự cách FOKR hiển thị chi tiết OKR

**Phê duyệt mục tiêu:**
- Nút **Duyệt**: chấp nhận, chuyển trạng thái → Đã duyệt, hệ thống tự gửi email thông báo học sinh
- Nút **Yêu cầu chỉnh sửa**: từ chối, bắt buộc nhập nhận xét lý do, gửi email học sinh
- Nút **Đồng ý xóa**: khi học sinh gửi yêu cầu xóa, giáo viên xác nhận

**Nhận xét bằng trí tuệ nhân tạo:**
- Nút "Tạo nhận xét tự động" → hệ thống gửi dữ liệu lên Claude API
  (tên học sinh, mục tiêu, % hoàn thành, ghi chú cập nhật)
- Claude tự viết nhận xét 3–4 câu phong cách học bạ THPT, điền sẵn vào ô nhận xét
- Giáo viên chỉnh sửa rồi lưu

**Nhận xét tổng kết cuối kỳ:**
- Nhập nhận xét tổng hợp cho từng học sinh
- Xem ý kiến phụ huynh trước khi hoàn tất
- Nút **Hoàn tất đánh giá** (thay "chốt sổ"):
  → danh_gia_cuoi_ky.trang_thai = 'hoan_tat'
  → học sinh không thể cập nhật tiến độ thêm
  → hệ thống tự gửi email phụ huynh

**Quản lý mẫu mục tiêu:**
- Tạo mẫu: tên mẫu, câu mục tiêu lớn, câu kết quả then chốt, đơn vị, loại OKR, áp dụng cho lớp nào
- Xem danh sách mẫu đã tạo
- Kích hoạt / Ẩn mẫu

**Xuất báo cáo Word (.docx):**
- Xuất báo cáo 1 học sinh: phiếu đánh giá đầy đủ
- Xuất báo cáo cả lớp: gộp toàn bộ vào 1 file Word, mỗi học sinh trên một trang mới
- Font tiếng Việt chuẩn (Times New Roman hoặc Arial, hỗ trợ Unicode đầy đủ, không lỗi font)
- Nội dung phiếu: thông tin học sinh, bảng mục tiêu với tiến độ, nhận xét giáo viên, đánh giá phụ huynh, nhận xét tổng kết, ý kiến gia đình, ngày xuất

---

### VAI TRÒ 3: HỌC SINH

**Đăng nhập:**
- Email và mật khẩu do giáo viên tạo, bắt buộc đổi lần đầu
- Chỉ xem và chỉnh sửa dữ liệu của chính mình

**Bố cục giao diện (tham khảo FOKR):**
- Thanh điều hướng trái: Tổng quan | Mục tiêu của tôi | Mẫu mục tiêu
- Danh sách giữa: danh sách mục tiêu theo kỳ
- Chi tiết phải: nội dung chi tiết mục tiêu đang chọn (có tab: Thông tin chung | Lịch sử cập nhật | Nhận xét & Phản hồi)

**Tạo mục tiêu mới (luồng bắt buộc theo thứ tự — giống FOKR):**

Bước 1 — Chọn kỳ đánh giá:
- Bắt buộc chọn trước khi điền nội dung
- Danh sách dropdown chỉ hiện các kỳ đang ở trạng thái "Mở"
- Hiển thị tên kỳ + thời gian còn lại

Bước 2 — Chọn loại mục tiêu:
- Cá nhân: mục tiêu của riêng học sinh
- Nhóm: mục tiêu học sinh tham gia cùng nhóm
- Lớp: mục tiêu chung cả lớp (do giáo viên tạo)

Bước 3 — Điền nội dung:
- Mục tiêu lớn (Objective)
- Kết quả then chốt (Key Result): câu mô tả + con số chỉ tiêu + đơn vị
- Hạn hoàn thành (Deadline)
- Nút "Gợi ý kết quả then chốt bằng AI" → 3 gợi ý dạng chips

Hoặc thay thế Bước 3 bằng: chọn từ Mẫu mục tiêu (điền sẵn Objective, KR, đơn vị)

**Trang tổng quan học sinh:**
- Chuỗi ngày cập nhật liên tiếp (thay "streak"): hiển thị số ngày + biểu tượng
- Kỳ đánh giá hiện tại
- Số mục tiêu: Tổng | Chờ duyệt | Đã duyệt | Cần sửa

**Danh sách mục tiêu:**
- Hiển thị dạng danh sách (không dùng card dạng grid)
- Mỗi dòng: tên mục tiêu — trạng thái badge màu — % tiến độ — hạn hoàn thành — ngày cập nhật gần nhất
- Click vào dòng → mở chi tiết bên phải

**Chi tiết mục tiêu (panel phải):**
- Tab **Thông tin chung**: mục tiêu lớn, kết quả then chốt, chỉ tiêu, thực đạt, đơn vị, % tiến độ, hạn hoàn thành, vòng tròn tiến độ SVG
- Tab **Lịch sử cập nhật**: danh sách các lần cập nhật theo thời gian + biểu đồ đường (trục X: ngày, trục Y: %)
- Tab **Nhận xét & Phản hồi**: nhận xét giáo viên, đánh giá phụ huynh (sao), nhận xét tổng kết cuối kỳ

**Cập nhật tiến độ:**
- Nút "Cập nhật tiến độ" chỉ hiển thị khi: mục tiêu đã duyệt + kỳ đang mở + chưa cập nhật hôm nay
- Hộp thoại nhập: con số thực đạt mới + ghi chú (tuỳ chọn) + xem trước % sẽ đạt
- Trigger database tự tính lại % và lưu vào lịch sử

**Các thao tác khác:**
- Xin xóa mục tiêu: mục tiêu chuyển sang "Chờ giáo viên xác nhận xóa", không tự xóa được
- Sửa mục tiêu: chỉ khi trạng thái là "Chờ duyệt" hoặc "Cần sửa"

**Mẫu mục tiêu:**
- Danh sách mẫu do giáo viên tạo, lọc theo kỳ và loại
- Click chọn mẫu → điền sẵn thông tin vào form, học sinh chỉ nhập con số chỉ tiêu và hạn hoàn thành

---

### VAI TRÒ 4: PHỤ HUYNH

**Đăng nhập đặc biệt:**
- Nhập email phụ huynh (đã đăng ký trong hệ thống bởi giáo viên)
- Nhập mật khẩu của học sinh (con)
- Hệ thống tự nhận diện và hiển thị: "Theo dõi tiến độ của [Họ tên con]"

**Bố cục giao diện (tối ưu cho điện thoại):**
- Thiết kế ưu tiên màn hình điện thoại (mobile-first)
- Điều hướng: Tổng quan | Mục tiêu của con | Phản hồi gia đình

**Trang tổng quan:**
- Thông tin con: họ tên, lớp, giáo viên chủ nhiệm, kỳ đánh giá hiện tại
- Số mục tiêu theo trạng thái
- Tiến độ trung bình tổng thể của con

**Danh sách mục tiêu con:**
- Danh sách mục tiêu theo từng kỳ
- Mỗi dòng: tên mục tiêu — % tiến độ — hạn hoàn thành — đánh giá của phụ huynh (sao)
- Click vào dòng → xem chi tiết: mục tiêu lớn, kết quả then chốt, thực đạt / chỉ tiêu, nhận xét giáo viên
- Cập nhật thời gian thực qua WebSocket: khi con cập nhật, số liệu thay đổi ngay

**Đánh giá mục tiêu (chấm sao):**
- 5 biểu tượng sao bên dưới mỗi mục tiêu
- Phụ huynh chạm để chấm (1–5 sao)
- Có thể thay đổi nhiều lần cho đến khi giáo viên hoàn tất đánh giá

**Gửi ý kiến gia đình cuối kỳ:**
- Ô nhập văn bản "Ý kiến của gia đình"
- Nút Gửi → lưu vào danh_gia_cuoi_ky.phan_hoi_ph
- Giáo viên nhận thông báo ngay khi phụ huynh gửi

**Thông báo nhận được (email tự động):**
- Con không cập nhật tiến độ quá **7 ngày liên tiếp** → gửi email nhắc nhở phụ huynh
- Giáo viên đã **hoàn tất đánh giá** → gửi email mời phụ huynh xem nhận xét cuối kỳ

---

## V. HỆ THỐNG THÔNG BÁO

### Email tự động (Resend API)

| Sự kiện                               | Người nhận   | Tiêu đề email                                       |
|---------------------------------------|--------------|-----------------------------------------------------|
| Giáo viên duyệt mục tiêu             | Học sinh     | [OKR] Mục tiêu của bạn đã được duyệt               |
| Giáo viên yêu cầu chỉnh sửa         | Học sinh     | [OKR] Mục tiêu cần được chỉnh sửa                  |
| Học sinh không cập nhật quá 7 ngày  | Phụ huynh    | [OKR] Con bạn chưa cập nhật tiến độ {N} ngày       |
| Còn 3 ngày hết kỳ đánh giá          | GV + HS      | [OKR] Còn 3 ngày kết thúc kỳ "{tên kỳ}"           |
| Giáo viên hoàn tất đánh giá         | Phụ huynh    | [OKR] Nhận xét cuối kỳ của con đã sẵn sàng         |

### Tác vụ tự động (chạy lúc 8:00 sáng mỗi ngày)
- Quét lịch sử cập nhật, tìm mục tiêu không có bản ghi trong 7 ngày → gửi email phụ huynh
- Quét kỳ đánh giá, nếu ngày kết thúc còn đúng 3 ngày → gửi email giáo viên và học sinh

### Thông báo trong ứng dụng (Thời gian thực)
- Supabase Realtime subscription trên bảng thong_bao
- Biểu tượng chuông + số thông báo chưa đọc trên thanh tiêu đề
- Danh sách thông báo thả xuống khi click, click vào thông báo → đánh dấu đã đọc

---

## VI. TÍCH HỢP TRÍ TUỆ NHÂN TẠO (Claude API)

### Tính năng 1: Tạo nhận xét tự động cho giáo viên
- Gọi: `POST /api/v1/ai/tao-nhan-xet`
- Giáo viên click nút trên màn hình học sinh
- Backend lấy: tên HS, mục tiêu, % hoàn thành, danh sách ghi chú cập nhật
- Gọi claude-sonnet-4-20250514, nhận về đoạn nhận xét 3–4 câu
- Điền sẵn vào ô nhận xét → giáo viên chỉnh sửa rồi lưu

**Mẫu gợi ý cho Claude:**
```
Bạn là giáo viên chủ nhiệm THPT đang viết nhận xét cuối học kỳ.
Học sinh: {ho_ten}. Mục tiêu: {muc_tieu_lon}.
Kết quả then chốt: {ket_qua} — đạt {phan_tram}%.
Các ghi chú cập nhật: {danh_sach_ghi_chu}.
Yêu cầu: viết nhận xét 3–4 câu, khuyến khích, thực tế,
đề cập con số cụ thể, phù hợp văn phong học bạ THPT Việt Nam.
Chỉ trả về đoạn nhận xét, không thêm nội dung khác.
```

### Tính năng 2: Gợi ý kết quả then chốt cho học sinh
- Gọi: `POST /api/v1/ai/goi-y-kr`
- Học sinh nhập mục tiêu lớn → click nút gợi ý
- Claude trả về 3 gợi ý kết quả then chốt dạng chips để click chọn

### Tính năng 3: Tóm tắt lớp cho Quản trị viên
- Gọi: `POST /api/v1/ai/tom-tat-lop`
- Chọn lớp + kỳ → Claude đọc dữ liệu tiến độ toàn lớp
- Trả về đoạn tóm tắt ngắn: xu hướng chung, điểm nổi bật, lưu ý

---

## VII. BẢO MẬT & QUY TẮC NGHIỆP VỤ

### Bảo mật

- **Mật khẩu**: hash bằng bcrypt (cost 12), không bao giờ lưu văn bản thuần
- **Mật khẩu mặc định**: phải được hash ngay khi tạo seed data
- **Đổi mật khẩu lần đầu**: must_change_password = true → bắt buộc đổi trước khi vào app
- **Yêu cầu mật khẩu**: tối thiểu 8 ký tự, có chữ hoa, có số
- **JWT**: hết hạn sau 480 phút, payload gồm id, email, vai_tro
- **Giới hạn đăng nhập**: tối đa 5 lần sai trong 10 phút / địa chỉ IP → trả về lỗi 429
- **Nhật ký**: tất cả thao tác quan trọng đều ghi vào nhat_ky_hoat_dong

### Quy tắc nghiệp vụ quan trọng

1. **Kỳ bị khóa**: trigger database chặn hoàn toàn — không phụ thuộc kiểm tra phía giao diện
2. **Hoàn tất đánh giá**: khi danh_gia_cuoi_ky.trang_thai = 'hoan_tat', học sinh không thể cập nhật tiến độ thêm
3. **Cập nhật tiến độ 1 lần/ngày**: backend kiểm tra lich_su_cap_nhat trong ngày hiện tại trước khi cho phép
4. **Xóa mục tiêu**: học sinh chỉ được gửi yêu cầu (trang_thai = 'xin_xoa'), giáo viên mới được xóa thật
5. **Sửa mục tiêu**: chỉ được sửa khi trạng thái là 'cho_duyet' hoặc 'yeu_cau_sua'
6. **Phụ huynh**: chỉ xem và tương tác với dữ liệu của con mình (kiểm tra qua email_phu_huynh)
7. **Học sinh tạo mục tiêu**: bắt buộc chọn kỳ đánh giá trước (phải ở trạng thái 'mo')

---

## VIII. DANH SÁCH API ENDPOINTS

### Xác thực
```
POST   /api/v1/xac-thuc/dang-nhap            Đăng nhập, trả JWT
POST   /api/v1/xac-thuc/doi-mat-khau         Đổi mật khẩu
GET    /api/v1/xac-thuc/thong-tin-ca-nhan    Thông tin người dùng hiện tại
```

### Mục tiêu
```
GET    /api/v1/muc-tieu/                             Danh sách mục tiêu của người dùng hiện tại
POST   /api/v1/muc-tieu/                             Tạo mục tiêu mới (học sinh)
PUT    /api/v1/muc-tieu/{id}                         Sửa mục tiêu (chỉ khi cho_duyet/yeu_cau_sua)
POST   /api/v1/muc-tieu/{id}/cap-nhat-tien-do        Cập nhật tiến độ (học sinh)
POST   /api/v1/muc-tieu/{id}/duyet                   Duyệt mục tiêu (giáo viên)
POST   /api/v1/muc-tieu/{id}/yeu-cau-sua             Yêu cầu chỉnh sửa (giáo viên)
POST   /api/v1/muc-tieu/{id}/xin-xoa                 Gửi yêu cầu xóa (học sinh)
POST   /api/v1/muc-tieu/{id}/dong-y-xoa              Đồng ý xóa (giáo viên)
PUT    /api/v1/muc-tieu/{id}/danh-gia                Chấm sao (phụ huynh)
GET    /api/v1/muc-tieu/{id}/lich-su                 Lịch sử cập nhật (vẽ biểu đồ)
GET    /api/v1/muc-tieu/theo-lop/{ten_lop}           Toàn bộ mục tiêu của lớp (giáo viên)
```

### Người dùng
```
GET    /api/v1/nguoi-dung/hoc-sinh/{ten_lop}         Danh sách học sinh (giáo viên)
POST   /api/v1/nguoi-dung/hoc-sinh                   Thêm học sinh
POST   /api/v1/nguoi-dung/giao-vien                  Thêm giáo viên (quản trị viên)
POST   /api/v1/nguoi-dung/nhap-danh-sach             Nhập danh sách từ file xlsx
PUT    /api/v1/nguoi-dung/{id}/reset-mat-khau        Reset mật khẩu
DELETE /api/v1/nguoi-dung/{id}                       Vô hiệu hóa tài khoản
```

### Kỳ đánh giá
```
GET    /api/v1/ky-danh-gia/                  Danh sách kỳ
POST   /api/v1/ky-danh-gia/                  Tạo kỳ mới (quản trị viên)
PUT    /api/v1/ky-danh-gia/{id}/khoa         Khóa kỳ (quản trị viên)
PUT    /api/v1/ky-danh-gia/{id}/mo           Mở kỳ (quản trị viên)
```

### Mẫu mục tiêu
```
GET    /api/v1/mau-muc-tieu/                 Danh sách mẫu (lọc theo lớp, kỳ)
POST   /api/v1/mau-muc-tieu/                 Tạo mẫu (giáo viên/quản trị viên)
PUT    /api/v1/mau-muc-tieu/{id}             Sửa mẫu
POST   /api/v1/mau-muc-tieu/{id}/ap-dung     Học sinh áp dụng mẫu → tạo mục tiêu nháp
DELETE /api/v1/mau-muc-tieu/{id}             Xóa mẫu
```

### Đánh giá cuối kỳ
```
GET    /api/v1/danh-gia-cuoi-ky/{hs_id}?ky_id=    Xem đánh giá
PUT    /api/v1/danh-gia-cuoi-ky/{hs_id}            Cập nhật nhận xét giáo viên
POST   /api/v1/danh-gia-cuoi-ky/{hs_id}/hoan-tat  Hoàn tất đánh giá (giáo viên)
PUT    /api/v1/danh-gia-cuoi-ky/{hs_id}/y-kien     Phụ huynh gửi ý kiến gia đình
```

### Thông báo
```
GET    /api/v1/thong-bao/                   Danh sách thông báo của người dùng
PUT    /api/v1/thong-bao/{id}/da-doc        Đánh dấu đã đọc
POST   /api/v1/thong-bao/test               Gửi email thử nghiệm (quản trị viên)
```

### Xuất báo cáo
```
GET    /api/v1/bao-cao/hoc-sinh/{id}?ky_id=          Xuất Word 1 học sinh
GET    /api/v1/bao-cao/ca-lop/{ten_lop}?ky_id=        Xuất Word cả lớp
```

### Trí tuệ nhân tạo
```
POST   /api/v1/ai/tao-nhan-xet      Tạo nhận xét tự động (giáo viên)
POST   /api/v1/ai/goi-y-kr          Gợi ý kết quả then chốt (học sinh)
POST   /api/v1/ai/tom-tat-lop       Tóm tắt tiến độ lớp (quản trị viên)
```

### Quản trị viên
```
GET    /api/v1/quan-tri/thong-ke-tong-quan   Bảng thống kê toàn trường
GET    /api/v1/quan-tri/nhat-ky              Xem nhật ký hoạt động
```

---

## IX. XUẤT BÁO CÁO WORD (.docx)

### Yêu cầu kỹ thuật
- Dùng thư viện `python-docx`
- Font: Times New Roman 13pt (nội dung), 14pt bold (tiêu đề) — hỗ trợ Unicode đầy đủ
- Không dùng WeasyPrint hoặc xuất PDF
- File xuất ra có đuôi `.docx`, tên file: `BaoCao_{HoTen}_{TenKy}.docx`
- File cả lớp: `BaoCao_CaLop_{TenLop}_{TenKy}.docx`

### Nội dung phiếu đánh giá từng học sinh
```
[Header]
Trường: [Tên trường]           Năm học: [Năm]
Giáo viên chủ nhiệm: [Tên]    Kỳ đánh giá: [Tên kỳ]

[Thông tin học sinh]
Họ và tên: ___    Lớp: ___    Ngày xuất: ___

[Bảng mục tiêu]
STT | Mục tiêu lớn | Kết quả then chốt | Chỉ tiêu | Thực đạt | Đơn vị | Tiến độ (%) | Nhận xét giáo viên

[Đánh giá của phụ huynh]
Sao: [★★★★☆]

[Nhận xét tổng kết của giáo viên]
[Nội dung]

[Ý kiến gia đình]
[Nội dung]

[Footer]
Giáo viên chủ nhiệm          Phụ huynh học sinh
(Ký và ghi rõ họ tên)        (Ký và ghi rõ họ tên)
```

---

## X. BIẾN MÔI TRƯỜNG (.env)

```env
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...

# Xác thực JWT
JWT_SECRET=khoa-bi-mat-ngau-nhien-toi-thieu-32-ky-tu
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# Gửi email
RESEND_API_KEY=re_xxxx

# Trí tuệ nhân tạo
ANTHROPIC_API_KEY=sk-ant-xxxx

# Ứng dụng
FRONTEND_URL=http://localhost:3000
TEN_TRUONG=Trường THPT [Tên Trường]
```

---

## XI. DỮ LIỆU KHỞI TẠO (seed data)

```
Quản trị viên mặc định:
  Email: admin@truong.edu.vn
  Mật khẩu: Admin@2025 (được hash bằng bcrypt)
  Phải đổi mật khẩu khi đăng nhập lần đầu

Kỳ đánh giá mẫu:
  Tên: "Học kỳ 1 — 2025"
  Trạng thái: Mở
  Ngày bắt đầu: 01/09/2025
  Ngày kết thúc: 31/12/2025

Mẫu mục tiêu:
  1. Tên: "Nâng cao kết quả học tập"
     Mục tiêu lớn: "Cải thiện kết quả học tập học kỳ này"
     Kết quả then chốt: "Đạt điểm trung bình môn"
     Đơn vị: điểm — Loại: Cá nhân

  2. Tên: "Phát triển thói quen đọc sách"
     Mục tiêu lớn: "Xây dựng thói quen đọc sách thường xuyên"
     Kết quả then chốt: "Đọc xong số cuốn sách"
     Đơn vị: cuốn — Loại: Cá nhân

  3. Tên: "Rèn luyện thể chất"
     Mục tiêu lớn: "Duy trì lịch tập luyện thể thao đều đặn"
     Kết quả then chốt: "Tập thể dục số buổi"
     Đơn vị: buổi — Loại: Cá nhân
```

---

*Phiên bản 2.1 — Cập nhật: toàn bộ giao diện thuần tiếng Việt,*
*xuất báo cáo Word (.docx) thay PDF, thuật ngữ chuyên nghiệp,*
*học sinh bắt buộc chọn kỳ khi tạo mục tiêu, mẫu mục tiêu theo phong cách FOKR.*
