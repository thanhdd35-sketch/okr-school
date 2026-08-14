-- ============================================================
--  BẬT ROW-LEVEL SECURITY (RLS) CHO TOÀN BỘ BẢNG
--  Mục đích: khóa mọi truy cập bằng khóa công khai (anon key).
--  Backend dùng SERVICE KEY -> tự động BỎ QUA RLS -> app chạy bình thường.
--  Chạy trong: Supabase Dashboard -> SQL Editor -> New query -> Run
-- ============================================================

-- 1) Bật RLS trên 12 bảng.
--    RLS bật + KHÔNG có policy nào = anon/authenticated bị chặn hoàn toàn.
--    service_role (backend) có quyền BYPASSRLS -> không bị ảnh hưởng.
ALTER TABLE public.nguoi_dung          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.muc_tieu            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ket_qua_then_chot   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ky_danh_gia         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lich_su_cap_nhat    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.danh_gia_giua_ky    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.danh_gia_cuoi_ky    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.thong_bao           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mau_muc_tieu        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.okr_to_chuc         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ket_qua_phe_duyet   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nhat_ky_hoat_dong   ENABLE ROW LEVEL SECURITY;

-- 2) Thu hồi quyền trực tiếp của anon & authenticated (phòng thủ nhiều lớp).
--    Ngay cả khi RLS có sơ hở, 2 role công khai này cũng không có quyền bảng.
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon, authenticated;

-- ============================================================
--  KIỂM TRA SAU KHI CHẠY: mọi bảng phải rowsecurity = true
-- ============================================================
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- ORDER BY tablename;
