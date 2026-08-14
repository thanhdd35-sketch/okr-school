-- ============================================================
--  v2.6 — THU HOI & LAM MOI PHIEN DANG NHAP
--  Chay trong: Supabase Dashboard -> SQL Editor -> New query -> Run
--
--  Y nghia: moi tai khoan co mot "phien ban token". Token dang nhap
--  mang theo so phien ban tai thoi diem cap. Khi can thu hoi phien
--  (doi mat khau, admin dat lai mat khau, vo hieu hoa tai khoan,
--  dang xuat tat ca thiet bi) -> tang so nay len 1.
--  Moi token cu mang phien ban cu lap tuc het hieu luc.
-- ============================================================

ALTER TABLE public.nguoi_dung
  ADD COLUMN IF NOT EXISTS phien_ban_token INTEGER NOT NULL DEFAULT 1;

-- ============================================================
--  KIEM TRA SAU KHI CHAY
-- ============================================================
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'nguoi_dung' AND column_name = 'phien_ban_token';
