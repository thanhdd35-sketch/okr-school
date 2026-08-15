-- ============================================================
--  v2.6 — SUA BANG NHAT KY KIEM TOAN
--
--  VAN DE PHAT HIEN KHI CHAY THUC TE:
--  Bang nhat_ky_hoat_dong DA TON TAI TU TRUOC voi muc dich khac
--  (ghi thay doi ban ghi: ten_bang / id_ban_ghi / gia_tri_cu / gia_tri_moi),
--  nen lenh CREATE TABLE IF NOT EXISTS o migration truoc KHONG chay.
--  Hau qua: bang thieu cot 'mo_ta' -> moi lenh ghi nhat ky deu loi 400
--  (PGRST204) va bi nuot loi, nen man hinh Nhat ky luon rong.
-- ============================================================

-- 1) Bo sung cot con thieu
ALTER TABLE public.nhat_ky_hoat_dong
    ADD COLUMN IF NOT EXISTS mo_ta TEXT;

-- 2) Them rang buoc khoa ngoai toi bang nguoi dung.
--    ON DELETE SET NULL: xoa nguoi dung KHONG duoc lam mat dau vet kiem toan.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_nhat_ky_nguoi_dung'
    ) THEN
        ALTER TABLE public.nhat_ky_hoat_dong
            ADD CONSTRAINT fk_nhat_ky_nguoi_dung
            FOREIGN KEY (nguoi_dung_id)
            REFERENCES public.nguoi_dung (id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================
--  KIEM TRA SAU KHI CHAY — phai tra ve 1 dong 'mo_ta'
-- ============================================================
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name = 'nhat_ky_hoat_dong' AND column_name = 'mo_ta';
