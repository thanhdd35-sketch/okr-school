-- ============================================================
--  v2.6 — NHAT KY KIEM TOAN (AUDIT LOG)
--  Chay trong: Supabase Dashboard -> SQL Editor -> New query -> Run
--
--  BOI CANH: bang nhat_ky_hoat_dong da ton tai va co man hinh xem,
--  nhung TRUOC DAY KHONG CO DONG CODE NAO GHI VAO -> bang luon rong.
--  Script nay chuan hoa cau truc bang de phuc vu ghi log day du theo
--  Luat Bao ve du lieu ca nhan 91/2025/QH15 (luu toi thieu 12-24 thang).
-- ============================================================

-- 1) Tao bang neu chua co
CREATE TABLE IF NOT EXISTS public.nhat_ky_hoat_dong (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nguoi_dung_id UUID,
    hanh_dong     TEXT NOT NULL,
    mo_ta         TEXT,
    thoi_diem     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2) Bo sung cac cot phuc vu tuan thu (an toan neu bang da ton tai)
ALTER TABLE public.nhat_ky_hoat_dong
    ADD COLUMN IF NOT EXISTS doi_tuong_id  UUID,          -- HS/OKR bi tac dong
    ADD COLUMN IF NOT EXISTS dia_chi_ip    TEXT,          -- nguon truy cap
    ADD COLUMN IF NOT EXISTS ket_qua       TEXT DEFAULT 'thanh_cong',
    ADD COLUMN IF NOT EXISTS vai_tro       TEXT,          -- vai tro tai thoi diem thao tac
    ADD COLUMN IF NOT EXISTS da_luu_tru    BOOLEAN DEFAULT FALSE;  -- da xuat ra object store chua

-- 3) Chi muc phuc vu tra cuu & xuat dinh ky
CREATE INDEX IF NOT EXISTS idx_nhat_ky_thoi_diem  ON public.nhat_ky_hoat_dong (thoi_diem DESC);
CREATE INDEX IF NOT EXISTS idx_nhat_ky_nguoi_dung ON public.nhat_ky_hoat_dong (nguoi_dung_id);
CREATE INDEX IF NOT EXISTS idx_nhat_ky_hanh_dong  ON public.nhat_ky_hoat_dong (hanh_dong);
CREATE INDEX IF NOT EXISTS idx_nhat_ky_luu_tru    ON public.nhat_ky_hoat_dong (da_luu_tru, thoi_diem);

-- 4) Bat RLS (backend dung service key nen khong bi anh huong)
ALTER TABLE public.nhat_ky_hoat_dong ENABLE ROW LEVEL SECURITY;

-- ============================================================
--  LUU Y QUAN TRONG VE TINH TOAN VEN CUA NHAT KY
--  Nhat ky kiem toan phai la "chi ghi them" (append-only): khong duoc
--  sua hay xoa. O muc CSDL, khoa dich vu cua ung dung van co quyen xoa,
--  nen bien phap bu dap la XUAT DINH KY ra Supabase Storage (object store)
--  va khoa file lai. Xem: backend/luu_tru_nhat_ky.py
--
--  KHONG dat lich tu dong xoa bang nay. Thoi han luu toi thieu 12-24 thang.
-- ============================================================
