-- ============================================================
--  v2.6 — DIEU KHOAN BAO MAT + DAT LAI MAT KHAU
--  Chay trong: Supabase Dashboard -> SQL Editor -> New query -> Run
-- ============================================================

-- 1) Ghi nhan viec dong y dieu khoan bao ve du lieu ca nhan
--    (bang chung tuan thu Luat 91/2025/QH15: AI dong y - LUC NAO - BAN NAO)
ALTER TABLE public.nguoi_dung
    ADD COLUMN IF NOT EXISTS dong_y_dieu_khoan_luc   TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS phien_ban_dieu_khoan    TEXT;

-- 2) Bang yeu cau dat lai mat khau
--    LUU Y BAO MAT: KHONG luu ma goc, chi luu ban bam (SHA-256).
--    Ke ca nguoi doc duoc CSDL cung khong dung lai duoc link dat lai.
CREATE TABLE IF NOT EXISTS public.yeu_cau_dat_lai_mat_khau (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nguoi_dung_id  UUID NOT NULL,
    ma_bam         TEXT NOT NULL,           -- SHA-256 cua ma dat lai
    het_han        TIMESTAMPTZ NOT NULL,
    da_su_dung     BOOLEAN NOT NULL DEFAULT FALSE,
    dia_chi_ip     TEXT,
    thoi_diem_tao  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dat_lai_ma_bam   ON public.yeu_cau_dat_lai_mat_khau (ma_bam);
CREATE INDEX IF NOT EXISTS idx_dat_lai_nguoi    ON public.yeu_cau_dat_lai_mat_khau (nguoi_dung_id, thoi_diem_tao DESC);

-- 3) Bat RLS (backend dung service key nen khong bi anh huong)
ALTER TABLE public.yeu_cau_dat_lai_mat_khau ENABLE ROW LEVEL SECURITY;

-- ============================================================
--  KIEM TRA SAU KHI CHAY
-- ============================================================
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name='nguoi_dung' AND column_name LIKE '%dieu_khoan%';
-- SELECT COUNT(*) FROM public.yeu_cau_dat_lai_mat_khau;
