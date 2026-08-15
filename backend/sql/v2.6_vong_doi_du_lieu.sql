-- ============================================================
--  v2.6 — VONG DOI DU LIEU HOC SINH
--  Chay trong: Supabase Dashboard -> SQL Editor -> New query -> Run
--
--  CHINH SACH DA DUOC NHA TRUONG CHOT:
--    - THCS hoc 4 nam (khoi 6-9), THPT hoc 3 nam (khoi 10-12)
--    - Khi hoc sinh ra truong / chuyen truong / nghi hoc -> KHOA tai khoan ngay
--    - Sau do giu them 1 NAM -> AN DANH HOA va XOA du lieu dinh danh
--    - Chi giu lai so lieu thong ke KHONG dinh danh de bao cao nhieu nam
-- ============================================================

ALTER TABLE public.nguoi_dung
    ADD COLUMN IF NOT EXISTS trang_thai_hoc     TEXT DEFAULT 'dang_hoc',
    ADD COLUMN IF NOT EXISTS ngay_ket_thuc_hoc  DATE,
    ADD COLUMN IF NOT EXISTS ly_do_ket_thuc     TEXT,
    ADD COLUMN IF NOT EXISTS da_an_danh         BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS thoi_diem_an_danh  TIMESTAMPTZ;

COMMENT ON COLUMN public.nguoi_dung.trang_thai_hoc IS
    'dang_hoc | da_ra_truong | chuyen_truong | nghi_hoc';

CREATE INDEX IF NOT EXISTS idx_nguoi_dung_vong_doi
    ON public.nguoi_dung (trang_thai_hoc, da_an_danh, ngay_ket_thuc_hoc);

-- Bang ghi nhan yeu cau xoa du lieu theo quyen chu the du lieu (Luat 91/2025)
CREATE TABLE IF NOT EXISTS public.yeu_cau_xoa_du_lieu (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hoc_sinh_id    UUID NOT NULL,
    nguoi_yeu_cau  UUID,
    ly_do          TEXT,
    trang_thai     TEXT NOT NULL DEFAULT 'cho_duyet',   -- cho_duyet | da_duyet | tu_choi
    nguoi_duyet    UUID,
    ghi_chu_duyet  TEXT,
    thoi_diem_tao  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    thoi_diem_duyet TIMESTAMPTZ
);

ALTER TABLE public.yeu_cau_xoa_du_lieu ENABLE ROW LEVEL SECURITY;

-- ============================================================
--  KIEM TRA SAU KHI CHAY
-- ============================================================
-- SELECT trang_thai_hoc, COUNT(*) FROM public.nguoi_dung
-- WHERE vai_tro='hoc_sinh' GROUP BY trang_thai_hoc;
