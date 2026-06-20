-- =====================================================
-- MIGRATION v2.4 — gioi tinh GV, binh luan PH, OKR to chuc mo rong
-- Chay trong Supabase SQL Editor. An toan chay lai nhieu lan.
-- =====================================================

-- Gioi tinh giao vien/PHT (nam -> thay, nu -> co) cho AI nhan xet
ALTER TABLE nguoi_dung ADD COLUMN IF NOT EXISTS gioi_tinh TEXT
  CHECK (gioi_tinh IN ('nam','nu'));

-- Binh luan cua phu huynh tren tung OKR (kem cham sao diem_phu_huynh da co)
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS binh_luan_phu_huynh TEXT;

-- OKR to chuc (truong/khoi): them han, tien do, minh chung, danh gia cuoi ky
ALTER TABLE okr_to_chuc ADD COLUMN IF NOT EXISTS han_hoan_thanh DATE;
ALTER TABLE okr_to_chuc ADD COLUMN IF NOT EXISTS tien_do NUMERIC DEFAULT 0;
ALTER TABLE okr_to_chuc ADD COLUMN IF NOT EXISTS minh_chung_url TEXT;
ALTER TABLE okr_to_chuc ADD COLUMN IF NOT EXISTS nhan_xet_cuoi_ky TEXT;
