-- =====================================================
-- MIGRATION v2.3 — Phan quyen 5 vai tro, OKR to chuc,
-- danh gia giua ky, tu danh gia HS, du doan tro ngai
-- Chay trong Supabase SQL Editor. An toan chay lai nhieu lan.
-- =====================================================

-- ---------- A.1 PHAN QUYEN ----------
-- Giu nguyen 'quan_tri' (KHONG doi thanh quan_tri_vien), chi THEM pho_hieu_truong
ALTER TABLE nguoi_dung DROP CONSTRAINT IF EXISTS nguoi_dung_vai_tro_check;
ALTER TABLE nguoi_dung ADD CONSTRAINT nguoi_dung_vai_tro_check
  CHECK (vai_tro IN (
    'quan_tri',        -- Quan tri vien (toan quyen, xem moi OKR read-only)
    'pho_hieu_truong', -- Pho Hieu truong (OKR truong + xem moi khoi)
    'giao_vien',       -- GVCN (co the kiem Truong khoi qua co la_truong_khoi)
    'hoc_sinh',
    'phu_huynh'
  ));

-- Co truong khoi (THEM quyen, van la giao_vien). Tai dung ten_lop cho lop chu nhiem.
ALTER TABLE nguoi_dung ADD COLUMN IF NOT EXISTS la_truong_khoi BOOLEAN DEFAULT false;
ALTER TABLE nguoi_dung ADD COLUMN IF NOT EXISTS khoi_phu_trach TEXT;  -- '6'..'12'
ALTER TABLE nguoi_dung ADD COLUMN IF NOT EXISTS khoi TEXT;            -- khoi cua HS (suy ra tu ten_lop)

-- ---------- A.2 OKR TO CHUC (bang rieng — KHONG dung chung muc_tieu) ----------
CREATE TABLE IF NOT EXISTS okr_to_chuc (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cap_okr         TEXT NOT NULL CHECK (cap_okr IN ('truong','khoi','lop')),
  khoi            TEXT,        -- bat buoc khi cap_okr='khoi'
  lop             TEXT,        -- bat buoc khi cap_okr='lop'
  ky_danh_gia_id  UUID REFERENCES ky_danh_gia(id),
  nguoi_tao_id    UUID REFERENCES nguoi_dung(id),
  muc_tieu_lon    TEXT NOT NULL,
  ket_qua_then_chot JSONB,     -- danh sach KR [{noi_dung, chi_tieu, don_vi, ...}]
  mo_ta           TEXT,
  trang_thai      TEXT DEFAULT 'hoat_dong' CHECK (trang_thai IN ('hoat_dong','an')),
  ngay_tao        TIMESTAMPTZ DEFAULT now(),
  ngay_cap_nhat   TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_okr_to_chuc_cap ON okr_to_chuc(cap_okr);
CREATE INDEX IF NOT EXISTS idx_okr_to_chuc_khoi ON okr_to_chuc(khoi);
CREATE INDEX IF NOT EXISTS idx_okr_to_chuc_lop ON okr_to_chuc(lop);

-- Lien ket tuy chon: OKR ca nhan HS -> OKR lop
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS lien_ket_okr_to_chuc_id UUID
  REFERENCES okr_to_chuc(id);

-- ---------- A.3 DANH GIA GIUA KY ----------
CREATE TABLE IF NOT EXISTS danh_gia_giua_ky (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hoc_sinh_id     UUID REFERENCES nguoi_dung(id) ON DELETE CASCADE,
  ky_danh_gia_id  UUID REFERENCES ky_danh_gia(id),
  giao_vien_id    UUID REFERENCES nguoi_dung(id),
  trang_thai_nhanh TEXT CHECK (trang_thai_nhanh IN ('dang_tot','can_theo_doi','can_gap_ngay')),
  nhan_xet_ngan   TEXT,
  hs_tu_kiem_tra  TEXT,
  ngay_tao        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dggk_hs ON danh_gia_giua_ky(hoc_sinh_id, ky_danh_gia_id);

ALTER TABLE ky_danh_gia ADD COLUMN IF NOT EXISTS mo_danh_gia_giua_ky BOOLEAN DEFAULT false;
ALTER TABLE ky_danh_gia ADD COLUMN IF NOT EXISTS mo_danh_gia_cuoi_ky BOOLEAN DEFAULT false;

-- ---------- A.4 TU DANH GIA CUOI KY (phan tu) ----------
ALTER TABLE danh_gia_cuoi_ky ADD COLUMN IF NOT EXISTS hs_nhin_lai_hanh_trinh TEXT;
ALTER TABLE danh_gia_cuoi_ky ADD COLUMN IF NOT EXISTS hs_cam_nhan_ca_nhan TEXT;
ALTER TABLE danh_gia_cuoi_ky ADD COLUMN IF NOT EXISTS hs_bai_hoc_rut_ra TEXT;
ALTER TABLE danh_gia_cuoi_ky ADD COLUMN IF NOT EXISTS hs_cam_ket_cai_tien TEXT;
ALTER TABLE danh_gia_cuoi_ky ADD COLUMN IF NOT EXISTS hs_da_tu_danh_gia BOOLEAN DEFAULT false;

-- ---------- A.5 DU DOAN TRO NGAI ----------
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS tro_ngai_du_doan TEXT;
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS ke_hoach_vuot_qua TEXT;

-- ---------- Backfill: suy ra khoi tu ten_lop cho HS ----------
UPDATE nguoi_dung
SET khoi = substring(ten_lop FROM '^[0-9]+')
WHERE vai_tro = 'hoc_sinh' AND (khoi IS NULL OR khoi = '') AND ten_lop ~ '^[0-9]';
