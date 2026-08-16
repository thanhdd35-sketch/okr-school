# TÀI LIỆU KỸ THUẬT & BÀN GIAO HỆ THỐNG
## Phần mềm Quản lý OKR Trường học

| | |
|---|---|
| **Tên hệ thống** | Hệ thống Quản lý Mục tiêu (OKR) Trường học |
| **Phiên bản tài liệu** | 1.0 |
| **Đối tượng đọc** | Ban Giám hiệu, Bộ phận Công nghệ thông tin (IT) |
| **Mục đích** | Mô tả kiến trúc, công nghệ, dữ liệu, bảo mật và quy trình vận hành để phục vụ bàn giao và tiếp quản quản trị hệ thống |
| **Trạng thái hệ thống** | Đang vận hành thử nghiệm (pilot) |

---

## 1. Tổng quan hệ thống

Phần mềm là một **ứng dụng web nhiều người dùng (multi-user web application)** phục vụ việc thiết lập, phê duyệt và theo dõi mục tiêu (OKR — Objectives and Key Results) trong nhà trường. Hệ thống hỗ trợ **5 nhóm vai trò**: Quản trị viên, Phó Hiệu trưởng, Giáo viên chủ nhiệm (kiêm Trưởng khối), Học sinh và Phụ huynh.

Hệ thống được xây dựng theo **kiến trúc client–server ba tầng tách rời**, triển khai trên hạ tầng điện toán đám mây, truy cập qua trình duyệt trên máy tính và điện thoại.

---

## 2. Kiến trúc hệ thống

```
   Người dùng (trình duyệt máy tính / điện thoại)
                    │  HTTPS
                    ▼
   ┌──────────────────────────────────┐
   │  TẦNG GIAO DIỆN (Frontend)        │   Next.js — triển khai trên Vercel
   └──────────────────────────────────┘
                    │  REST API (HTTPS, kèm JWT)
                    ▼
   ┌──────────────────────────────────┐
   │  TẦNG ỨNG DỤNG (Backend)          │   FastAPI — triển khai trên Railway (Docker)
   │  Xác thực, phân quyền, nghiệp vụ  │
   └──────────────────────────────────┘
          │                      │
          │ REST + Service Key   │ HTTPS
          ▼                      ▼
   ┌───────────────┐     ┌──────────────────────┐
   │ CƠ SỞ DỮ LIỆU │     │ DỊCH VỤ NGOÀI          │
   │ PostgreSQL    │     │ • Claude API (AI)      │
   │ (Supabase)    │     │ • Resend (email)       │
   └───────────────┘     └──────────────────────┘
```

**Nguyên tắc thiết kế cốt lõi:** trình duyệt của người dùng **không truy cập trực tiếp** cơ sở dữ liệu. Mọi thao tác đọc/ghi đều đi qua Backend, nơi thực hiện xác thực và kiểm soát phân quyền tập trung.

---

## 3. Công nghệ sử dụng (Technology Stack)

### 3.1. Tầng giao diện (Frontend)
| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| Framework | Next.js 16 (App Router) | Kết xuất giao diện, định tuyến |
| Ngôn ngữ | TypeScript | Ngôn ngữ lập trình |
| Giao diện | Tailwind CSS v4, shadcn/ui, lucide-react | Thành phần và kiểu dáng UI |
| Quản lý trạng thái | Zustand | Lưu phiên đăng nhập phía client |
| Giao tiếp API | Axios | Gọi REST API, tự đăng xuất khi token hết hạn |

### 3.2. Tầng ứng dụng (Backend)
| Thư viện | Phiên bản | Vai trò |
|---|---|---|
| FastAPI | 0.115.0 | Web framework (REST API) |
| Uvicorn | 0.30.6 | Máy chủ ứng dụng (ASGI) |
| PyJWT | 2.9.0 | Sinh và xác thực token đăng nhập (JWT, HS256) |
| bcrypt | 4.0.1 | Băm mật khẩu (cost factor 12) |
| httpx | 0.27.2 | Gọi Supabase REST và Claude API |
| APScheduler | 3.10.4 | Tác vụ định kỳ (nhắc nhở, dọn dữ liệu) |
| resend | 2.4.0 | Gửi email thông báo |
| python-docx / openpyxl | — | Xuất báo cáo Word, đọc/ghi Excel |

### 3.3. Cơ sở dữ liệu và dịch vụ ngoài
| Dịch vụ | Vai trò | Vị trí/Ghi chú |
|---|---|---|
| **Supabase (PostgreSQL)** | Lưu trữ toàn bộ dữ liệu | AWS `ap-southeast-1` (Singapore); gói Free (compute NANO) |
| **Resend** | Gửi email tự động | Tùy chọn; tự tắt nếu không cấu hình khóa |

> **Lưu ý kiến trúc:** Backend **không dùng SDK Supabase tiêu chuẩn** mà sử dụng một lớp truy vấn REST tự viết (`backend/database.py`), gọi trực tiếp endpoint `/rest/v1` của Supabase bằng httpx.

---

## 4. Cấu trúc mã nguồn

Hệ thống gồm **hai kho mã (repository) độc lập**:

### 4.1. Backend — `okr-backend`
```
/
├── Dockerfile              # Ảnh triển khai (python:3.11-slim)
├── railway.toml            # Cấu hình triển khai Railway
├── backend/
│   ├── main.py             # Điểm vào ứng dụng, đăng ký router, cấu hình CORS
│   ├── auth.py             # Băm mật khẩu, JWT, phân quyền theo vai trò
│   ├── database.py         # Lớp truy vấn REST tới Supabase
│   ├── scheduler.py        # Tác vụ định kỳ (APScheduler)
│   ├── email_service.py    # Gửi email (Resend)
│   ├── ky_helper.py        # Kiểm tra kỳ đánh giá mở/khóa
│   ├── requirements.txt    # Danh mục thư viện
│   ├── routers/            # 13 nhóm API nghiệp vụ
│   │   ├── xac_thuc.py        (đăng nhập, đổi mật khẩu)
│   │   ├── nguoi_dung.py      (quản lý người dùng)
│   │   ├── muc_tieu.py        (OKR cá nhân)
│   │   ├── ket_qua_then_chot.py (kết quả then chốt - KR)
│   │   ├── ky_danh_gia.py     (kỳ đánh giá, khóa kỳ)
│   │   ├── danh_gia_giua_ky.py / danh_gia_cuoi_ky.py
│   │   ├── okr_to_chuc.py     (OKR trường/khối/lớp)
│   │   ├── giam_sat.py        (giám sát 3 cấp)
│   │   ├── bao_cao.py         (xuất báo cáo Word)
│   │   │   ├── quan_tri.py       (chức năng quản trị, nhật ký)
│   │   ├── mau_muc_tieu.py   (mẫu OKR)
│   │   └── thong_bao.py      (thông báo)
│   └── sql/
│       └── bat_rls.sql       # Script bật Row-Level Security
```

### 4.2. Frontend — `okr-frontend`
```
frontend/
├── app/                    # Các trang theo vai trò (App Router)
│   ├── dang-nhap/          # Đăng nhập
│   ├── quan-tri/           # Quản trị viên
│   ├── pho-hieu-truong/    # Phó Hiệu trưởng
│   ├── giao-vien/          # Giáo viên chủ nhiệm / Trưởng khối
│   ├── hoc-sinh/           # Học sinh
│   ├── phu-huynh/          # Phụ huynh
│   └── globals.css         # Kiểu dáng toàn cục
├── components/             # Thành phần dùng chung (Layout, biểu mẫu, thẻ trạng thái…)
└── lib/                    # api.ts (Axios), store.ts (Zustand)
```

---

## 5. Mô hình dữ liệu

Cơ sở dữ liệu gồm **12 bảng** trong schema `public`:

| Bảng | Nội dung |
|---|---|
| `nguoi_dung` | Tài khoản người dùng: email, mật khẩu (đã băm), vai trò, lớp/khối, trạng thái |
| `muc_tieu` | OKR cá nhân của học sinh (mục tiêu lớn, trạng thái duyệt, tiến độ) |
| `ket_qua_then_chot` | Kết quả then chốt (KR) thuộc từng OKR |
| `ky_danh_gia` | Kỳ đánh giá và trạng thái mở/khóa |
| `lich_su_cap_nhat` | Lịch sử cập nhật tiến độ OKR |
| `danh_gia_giua_ky` | Đánh giá giữa kỳ |
| `danh_gia_cuoi_ky` | Đánh giá cuối kỳ (nhận xét giáo viên, xếp loại) |
| `okr_to_chuc` | OKR cấp tổ chức (trường / khối / lớp) |
| `ket_qua_phe_duyet` | Lịch sử phê duyệt OKR |
| `thong_bao` | Thông báo trong hệ thống |
| `mau_muc_tieu` | Mẫu OKR dùng lại |
| `nhat_ky_hoat_dong` | Nhật ký hoạt động (audit log) |

---

## 6. Xác thực và phân quyền

- **Không sử dụng Supabase Auth.** Việc xác thực do Backend tự quản lý.
- **Mật khẩu:** băm bằng bcrypt (cost 12); hệ thống không lưu và không thể khôi phục mật khẩu gốc.
- **Phiên đăng nhập:** cấp JWT ký bằng thuật toán HS256, thời hạn mặc định **480 phút (8 giờ)**, cấu hình qua biến môi trường.
- **Chống dò mật khẩu:** giới hạn **5 lần đăng nhập sai / 10 phút** theo địa chỉ IP.
- **Kiểm soát phân quyền:** thực hiện tại tầng Backend (`auth.py`) theo 5 vai trò, gồm cả kiểm tra theo phạm vi (Trưởng khối chỉ thao tác đúng khối, GVCN chỉ thao tác đúng lớp).

---

## 7. Hạ tầng triển khai và biến môi trường

### 7.1. Nền tảng triển khai
| Thành phần | Nền tảng | Cơ chế |
|---|---|---|
| Frontend | Vercel | Tự động build & deploy khi đẩy mã lên nhánh `main` |
| Backend | Railway (gói Hobby) | Build từ `Dockerfile`, chạy Uvicorn |
| Cơ sở dữ liệu | Supabase (gói Free) | PostgreSQL được quản lý |

### 7.2. Biến môi trường (bí mật — bàn giao riêng, không lưu trong mã nguồn)

**Backend:**
| Biến | Ý nghĩa |
|---|---|
| `SUPABASE_URL` | Địa chỉ dự án Supabase |
| `SUPABASE_SECRET_KEY` | **Khóa dịch vụ toàn quyền** — nhạy cảm cao, chỉ đặt tại Backend |
| `SUPABASE_PUBLISHABLE_KEY` | Khóa công khai (anon) |
| `JWT_SECRET` | Khóa bí mật ký JWT — nhạy cảm cao |
| `JWT_ALGORITHM` | Mặc định `HS256` |
| `JWT_EXPIRE_MINUTES` | Thời hạn phiên (mặc định 480) |
| `ANTHROPIC_API_KEY` | Khóa Claude API |
| `RESEND_API_KEY` | Khóa gửi email (tùy chọn) |
| `TEN_TRUONG` | Tên trường hiển thị trong email |

**Frontend:**
| Biến | Ý nghĩa |
|---|---|
| `NEXT_PUBLIC_API_URL` | Địa chỉ công khai của Backend |

---

## 8. Bảo mật — hiện trạng và khuyến nghị

### 8.1. Biện pháp đã triển khai
- Mã hóa đường truyền (HTTPS/TLS) toàn tuyến.
- Mã hóa dữ liệu khi lưu (at-rest) — mặc định của Supabase.
- Băm mật khẩu bcrypt; không lưu mật khẩu gốc.
- JWT có thời hạn; tự đăng xuất khi hết hạn.
- Giới hạn tần suất đăng nhập sai.
- Nhật ký hoạt động (audit log).
- Nguyên tắc thu thập dữ liệu tối thiểu; không lưu dữ liệu sức khỏe/nhạy cảm.

### 8.2. Hạng mục cần khắc phục trước khi vận hành chính thức
| # | Hạng mục | Rủi ro nếu bỏ qua | Mức độ |
|---|---|---|---|
| 1 | **Bật Row-Level Security (RLS)** cho 12 bảng | Khóa công khai (anon) có thể đọc trực tiếp dữ liệu | 🔴 Cao — *đã có script `backend/sql/bat_rls.sql`* |
| 2 | ~~Giới hạn CORS~~ | **Đã siết (v2.6): chỉ chấp nhận tên miền cấu hình qua biến CORS_ORIGINS; mặc định chỉ localhost và *.vercel.app** | ✅ Xong |
| 3 | **Cô lập & định kỳ đổi** `SUPABASE_SECRET_KEY`, `JWT_SECRET` | Lộ khóa toàn quyền → lộ toàn bộ dữ liệu | 🔴 Cao |
| 4 | ~~Ẩn danh hóa dữ liệu trước khi gửi Claude API~~ | **Đã xử lý triệt để: gỡ bỏ hoàn toàn tính năng AI khỏi hệ thống (v2.6). Không còn dữ liệu học sinh rời khỏi hệ thống.** | ✅ Xong |
| 5 | **Mã hóa cấp ứng dụng** cho các trường nhạy cảm | Nhà cung cấp/kẻ tấn công đọc được dữ liệu gốc | 🟠 Trung bình |
| 6 | **Ký thỏa thuận xử lý dữ liệu (DPA)** với nhà cung cấp; thông báo & xin đồng ý phụ huynh | Yêu cầu của Luật Bảo vệ dữ liệu cá nhân 2025 | 🔴 Bắt buộc về pháp lý |

> **Ghi chú:** RLS không bảo vệ trước trường hợp lộ khóa dịch vụ (service key), vì khóa này được thiết kế để bỏ qua RLS. Do đó hạng mục 1–3 cần thực hiện đồng bộ.

---

## 9. Vận hành

### 9.1. Chi phí (thời điểm lập tài liệu)
| Dịch vụ | Gói | Chi phí |
|---|---|---|
| Supabase | Free | 0 |
| Railway | Hobby | ~5 USD/tháng |
| ~~Claude API~~ | **Đã gỡ bỏ (v2.6)** | 0 |
| Vercel | Free | 0 |

### 9.2. Năng lực chịu tải và lộ trình mở rộng
- **Gói hiện tại (Supabase Free/NANO):** phục vụ tốt khi số người **thao tác đồng thời** dưới ~40–60. Phù hợp chạy thử theo hình thức cuốn chiếu từng lớp.
- **Quy mô ~1.500 người dùng, cao điểm truy cập dồn:** cần nâng **Supabase Pro (~25 USD/tháng)** và bật **Connection Pooler (chế độ transaction)** ở Backend. Chi phí vận hành ước tính ~750.000–1.200.000 đồng/tháng.
- Gói Supabase Pro có thể **bật/tắt theo tháng** để tối ưu chi phí trong các đợt cao điểm.

### 9.3. Dung lượng dữ liệu
- Hiện dùng ~27 MB / 500 MB (giới hạn gói Free).
- Ước tính ~250–350 MB cho một năm học ở quy mô đầy đủ.
- Kiểm soát tăng trưởng: bảng `thong_bao` có thể dọn định kỳ.
- **Đính chính (v2.6):** khuyến nghị trước đây về việc "dọn bảng `nhat_ky_hoat_dong`" là **không phù hợp** — đây là **nhật ký kiểm toán**, theo Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 phải được **lưu tối thiểu 12–24 tháng** và **không được xoá tuỳ tiện**. Cơ chế đúng đã triển khai: xuất định kỳ ra **object store (Supabase Storage)** tách khỏi cơ sở dữ liệu nghiệp vụ, giữ trong CSDL 24 tháng, và **mặc định không xoá bất kỳ bản ghi nào**.

### 9.4. Sao lưu
- Gói Free: sao lưu hạn chế. Khuyến nghị dùng **Supabase Pro** để có **Point-in-Time Recovery (PITR)** khi vận hành chính thức.

---

## 10. Danh mục tài sản bàn giao

Để tiếp quản quản trị, cần bàn giao các tài sản sau:

**A. Mã nguồn (GitHub)**
- Kho Backend: `okr-backend`
- Kho Frontend: `okr-frontend`

**B. Tài khoản dịch vụ (chuyển quyền sở hữu hoặc cấp quyền quản trị)**
- Supabase (dự án PostgreSQL)
- Railway (dịch vụ Backend)
- Vercel (dịch vụ Frontend)
- Anthropic Console (Claude API)
- Resend (nếu sử dụng email)

**C. Bí mật (bàn giao qua kênh an toàn, không qua email/chat thường)**
- Toàn bộ biến môi trường ở mục 7.2, đặc biệt `SUPABASE_SECRET_KEY` và `JWT_SECRET`.

**D. Tài liệu**
- Tài liệu này.
- Script `backend/sql/bat_rls.sql`.

---

## 11. Danh mục kiểm tra bàn giao (Handover checklist)

- [ ] Chuyển quyền sở hữu/quản trị 2 kho GitHub cho bộ phận IT.
- [ ] Chuyển quyền quản trị các tài khoản dịch vụ (Supabase, Railway, Vercel, Anthropic, Resend).
- [ ] Bàn giao toàn bộ biến môi trường qua kênh an toàn.
- [ ] **Đổi mới** `JWT_SECRET` và `SUPABASE_SECRET_KEY` sau bàn giao (rotate).
- [ ] Thực thi script bật RLS (`bat_rls.sql`) và xác minh.
- [ ] Giới hạn CORS về đúng tên miền Frontend.
- [ ] Thiết lập DPA và quy trình đồng ý của phụ huynh theo Luật BVDLCN 2025.
- [ ] Thống nhất quy trình sao lưu và phương án nâng cấp cho quy mô chính thức.

---

*Tài liệu được lập phục vụ mục đích bàn giao kỹ thuật. Các thông tin bí mật (khóa, mật khẩu) không được đưa vào tài liệu này và phải bàn giao qua kênh an toàn riêng.*
