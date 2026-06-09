-- =====================================================
-- MIGRATION v2.2 — Tách bảng KR + Tính năng mới
-- Chạy trong Supabase SQL Editor
-- =====================================================

-- 1. Xóa constraint cũ của muc_tieu.trang_thai và thêm trạng thái 'nhap'
ALTER TABLE muc_tieu DROP CONSTRAINT IF EXISTS muc_tieu_trang_thai_check;
ALTER TABLE muc_tieu ADD CONSTRAINT muc_tieu_trang_thai_check
  CHECK (trang_thai IN ('nhap','cho_duyet','da_duyet','yeu_cau_sua','xin_xoa'));

-- 2. Thêm cột mới vào muc_tieu
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS tan_suat TEXT DEFAULT 'hang_thang'
  CHECK (tan_suat IN ('hang_tuan','hai_tuan','hang_thang'));
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS nhan TEXT;
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS cau_chuyen TEXT;
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS tien_do_tong DECIMAL DEFAULT 0;
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS trang_thai_tien_do TEXT
  CHECK (trang_thai_tien_do IN ('xuat_sac','tot','dung_huong','can_chu_y','chech_huong'));
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS da_hoan_thanh BOOLEAN DEFAULT false;
ALTER TABLE muc_tieu ADD COLUMN IF NOT EXISTS ket_qua_checklist_hs JSONB;

-- 3. Tạo bảng ket_qua_then_chot (KR riêng biệt)
CREATE TABLE IF NOT EXISTS ket_qua_then_chot (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  muc_tieu_id         UUID REFERENCES muc_tieu(id) ON DELETE CASCADE,
  thu_tu              INTEGER DEFAULT 1,
  noi_dung            TEXT NOT NULL,
  loai_kr             TEXT DEFAULT 'so'
                      CHECK (loai_kr IN ('so','phan_tram','moc_viec')),
  gia_tri_khoi_diem   DECIMAL DEFAULT 0,
  gia_tri_muc_tieu    DECIMAL NOT NULL DEFAULT 100,
  gia_tri_hien_tai    DECIMAL DEFAULT 0,
  don_vi              TEXT NOT NULL DEFAULT 'diem',
  xu_huong            TEXT DEFAULT 'tang'
                      CHECK (xu_huong IN ('tang','giam')),
  han_hoan_thanh      DATE,
  tien_do_phan_tram   DECIMAL DEFAULT 0,
  nhan_xet_gv         TEXT,
  nguoi_phu_trach_id  UUID REFERENCES nguoi_dung(id),
  ngay_tao            TIMESTAMPTZ DEFAULT now(),
  ngay_cap_nhat       TIMESTAMPTZ DEFAULT now()
);

-- 4. Cập nhật lich_su_cap_nhat
ALTER TABLE lich_su_cap_nhat ADD COLUMN IF NOT EXISTS kr_id UUID REFERENCES ket_qua_then_chot(id) ON DELETE SET NULL;
ALTER TABLE lich_su_cap_nhat ADD COLUMN IF NOT EXISTS trang_thai_tu_danh_gia TEXT
  CHECK (trang_thai_tu_danh_gia IN ('xuat_sac','tot','dung_huong','can_chu_y','chech_huong'));
ALTER TABLE lich_su_cap_nhat ADD COLUMN IF NOT EXISTS tu_nhan_xet TEXT;

-- 5. Cập nhật danh_gia_cuoi_ky
ALTER TABLE danh_gia_cuoi_ky ADD COLUMN IF NOT EXISTS diem_so DECIMAL(3,1)
  CHECK (diem_so BETWEEN 0 AND 5);
ALTER TABLE danh_gia_cuoi_ky ADD COLUMN IF NOT EXISTS ky_vong_ky_tiep TEXT;
ALTER TABLE danh_gia_cuoi_ky ADD COLUMN IF NOT EXISTS trien_khai_xuat_sac BOOLEAN DEFAULT false;

-- 6. Tạo bảng ket_qua_phe_duyet (checklist duyệt của GV)
CREATE TABLE IF NOT EXISTS ket_qua_phe_duyet (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  muc_tieu_id         UUID REFERENCES muc_tieu(id) ON DELETE CASCADE,
  giao_vien_id        UUID REFERENCES nguoi_dung(id),
  tieu_chi_1          INTEGER CHECK (tieu_chi_1 BETWEEN 1 AND 4),
  tieu_chi_2          INTEGER CHECK (tieu_chi_2 BETWEEN 1 AND 4),
  tieu_chi_3          INTEGER CHECK (tieu_chi_3 BETWEEN 1 AND 4),
  tieu_chi_4          INTEGER CHECK (tieu_chi_4 BETWEEN 1 AND 4),
  nhan_xet_phe_duyet  TEXT,
  ket_qua             TEXT CHECK (ket_qua IN ('chap_thuan','tu_choi')),
  ngay_tao            TIMESTAMPTZ DEFAULT now()
);

-- 7. Di chuyển dữ liệu KR cũ từ muc_tieu sang ket_qua_then_chot (nếu có)
INSERT INTO ket_qua_then_chot (muc_tieu_id, noi_dung, gia_tri_muc_tieu, gia_tri_hien_tai, don_vi, tien_do_phan_tram)
SELECT id,
  COALESCE(ket_qua_then_chot, 'Kết quả then chốt'),
  COALESCE(chi_tieu, 100),
  COALESCE(thuc_dat, 0),
  COALESCE(don_vi, 'điểm'),
  COALESCE(tien_do_phan_tram, 0)
FROM muc_tieu
WHERE ket_qua_then_chot IS NOT NULL AND ket_qua_then_chot != ''
ON CONFLICT DO NOTHING;

-- Cập nhật tien_do_tong từ tien_do_phan_tram cũ
UPDATE muc_tieu SET tien_do_tong = COALESCE(tien_do_phan_tram, 0)
WHERE tien_do_phan_tram IS NOT NULL;

-- 8. Đặt mặc định trang_thai = 'nhap' cho muc_tieu mới
ALTER TABLE muc_tieu ALTER COLUMN trang_thai SET DEFAULT 'nhap';

SELECT 'Migration v2.2 hoàn tất!' AS result;
