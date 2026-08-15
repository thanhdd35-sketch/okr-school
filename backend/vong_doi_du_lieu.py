"""
VONG DOI DU LIEU HOC SINH — v2.6
Tuan thu nguyen tac GIOI HAN THOI GIAN LUU TRU cua Luat 91/2025/QH15.

CHINH SACH DA DUOC NHA TRUONG CHOT
  - THCS: khoi 6-9  (4 nam)   |   THPT: khoi 10-12 (3 nam)
  - Hoc sinh ra truong / chuyen truong / nghi hoc -> KHOA tai khoan NGAY
  - Giu them 1 NAM  -> AN DANH HOA: xoa toan bo du lieu dinh danh va moi
    noi dung van ban tu do (co the chua ten nguoi khac)
  - CHI GIU LAI so lieu dinh luong khong dinh danh (tien do %, trang thai,
    so luong OKR) de nha truong con bao cao, so sanh qua cac nam

LUU Y: an danh hoa la THAO TAC KHONG THE HOAN TAC. Vi vay:
  - Chi chay voi hoc sinh da qua han giu
  - Luon ghi nhat ky kiem toan truoc va sau khi thuc hien
"""

import os
from datetime import datetime, date, timedelta, timezone

from database import supabase
import audit

# So nam dao tao theo cap hoc
SO_NAM_THCS = 4
SO_NAM_THPT = 3

# Giu them bao lau sau khi ket thuc hoc roi moi an danh hoa
GIU_THEM_THANG = int(os.getenv("GIU_DU_LIEU_HS_THANG", 12))   # 1 nam

TRANG_THAI_KET_THUC = ("da_ra_truong", "chuyen_truong", "nghi_hoc")

# Cac truong van ban tu do can xoa khi an danh hoa
_TRUONG_CAN_XOA = {
    "muc_tieu": ["muc_tieu_lon", "cau_chuyen", "nhan", "nhan_xet_giao_vien",
                 "binh_luan_phu_huynh", "tro_ngai_du_doan", "ke_hoach_vuot_qua",
                 "tu_nhan_xet"],
    "ket_qua_then_chot": ["noi_dung", "ghi_chu"],
    "lich_su_cap_nhat": ["ghi_chu", "tu_nhan_xet"],
    "danh_gia_cuoi_ky": ["nhan_xet_gv", "phan_hoi_ph", "ky_vong_ky_tiep",
                         "hs_nhin_lai_hanh_trinh", "hs_cam_nhan_ca_nhan",
                         "hs_bai_hoc_rut_ra", "hs_cam_ket_cai_tien"],
    "danh_gia_giua_ky": ["nhan_xet_ngan", "hs_tu_kiem_tra"],
}


def cap_hoc_tu_khoi(khoi) -> str:
    """Suy ra cap hoc tu khoi. Khoi 6-9 = THCS, 10-12 = THPT."""
    try:
        so = int(str(khoi).strip())
        return "THCS" if 6 <= so <= 9 else "THPT"
    except (TypeError, ValueError):
        return "THPT"


def so_nam_dao_tao(khoi) -> int:
    return SO_NAM_THCS if cap_hoc_tu_khoi(khoi) == "THCS" else SO_NAM_THPT


def _cong_thang(goc: date, so_thang: int) -> date:
    """Cong dung so thang theo lich (khong dung uoc luong 30 ngay/thang)."""
    thang_tong = goc.month - 1 + so_thang
    nam = goc.year + thang_tong // 12
    thang = thang_tong % 12 + 1
    # Lui ngay neu thang dich khong co ngay do (vi du 31/01 + 1 thang)
    ngay = goc.day
    while ngay > 28:
        try:
            return date(nam, thang, ngay)
        except ValueError:
            ngay -= 1
    return date(nam, thang, ngay)


def han_an_danh(ngay_ket_thuc) -> date:
    """Thoi diem duoc phep an danh hoa = ngay ket thuc hoc + thoi gian giu them."""
    if isinstance(ngay_ket_thuc, str):
        ngay_ket_thuc = datetime.fromisoformat(ngay_ket_thuc[:10]).date()
    return _cong_thang(ngay_ket_thuc, GIU_THEM_THANG)


# ------------------------------------------------------------------
#  DANH DAU KET THUC HOC
# ------------------------------------------------------------------
def ket_thuc_hoc(hoc_sinh_id: str, trang_thai: str, ly_do: str = "",
                 nguoi_thuc_hien=None, ngay=None) -> dict:
    """Danh dau hoc sinh ket thuc hoc va KHOA tai khoan ngay lap tuc."""
    if trang_thai not in TRANG_THAI_KET_THUC:
        raise ValueError(f"Trang thai khong hop le: {trang_thai}")

    ngay_kt = (ngay or date.today()).isoformat() if not isinstance(ngay, str) else ngay

    supabase.table("nguoi_dung").update({
        "trang_thai_hoc": trang_thai,
        "ngay_ket_thuc_hoc": ngay_kt,
        "ly_do_ket_thuc": (ly_do or "")[:300],
        "dang_hoat_dong": False,        # khoa dang nhap ngay
    }).eq("id", hoc_sinh_id).execute()

    # Thu hoi moi phien dang mo cua hoc sinh do
    try:
        from auth import thu_hoi_phien
        thu_hoi_phien(hoc_sinh_id)
    except Exception:
        pass

    audit.ghi_nhat_ky("ket_thuc_hoc", f"Danh dau {trang_thai}; khoa tai khoan",
                      nguoi_dung=nguoi_thuc_hien, doi_tuong_id=hoc_sinh_id)

    return {"hoc_sinh_id": hoc_sinh_id, "trang_thai_hoc": trang_thai,
            "ngay_ket_thuc_hoc": ngay_kt,
            "du_kien_an_danh": han_an_danh(ngay_kt).isoformat()}


# ------------------------------------------------------------------
#  AN DANH HOA
# ------------------------------------------------------------------
def _xoa_van_ban_tu_do(hoc_sinh_id: str, muc_tieu_ids: list):
    """Xoa moi noi dung van ban tu do lien quan den hoc sinh."""
    for bang, cot in _TRUONG_CAN_XOA.items():
        du_lieu = {c: None for c in cot}
        try:
            if bang in ("muc_tieu", "danh_gia_cuoi_ky", "danh_gia_giua_ky"):
                supabase.table(bang).update(du_lieu).eq("hoc_sinh_id", hoc_sinh_id).execute()
            elif muc_tieu_ids:
                # Cac bang con lien ket qua muc_tieu_id
                for i in range(0, len(muc_tieu_ids), 50):
                    supabase.table(bang).update(du_lieu) \
                        .in_("muc_tieu_id", muc_tieu_ids[i:i + 50]).execute()
        except Exception as e:
            print(f"[VONG DOI] Bo qua {bang}: {str(e)[:120]}")


def an_danh_hoc_sinh(hoc_sinh_id: str, nguoi_thuc_hien=None, ly_do: str = "qua_han_luu_tru") -> dict:
    """Xoa du lieu dinh danh, chi giu so lieu thong ke. KHONG THE HOAN TAC."""
    res = supabase.table("nguoi_dung").select("id, ho_ten, khoi, ten_lop, da_an_danh") \
        .eq("id", hoc_sinh_id).execute()
    if not res.data:
        raise ValueError("Khong tim thay hoc sinh")
    if res.data[0].get("da_an_danh"):
        return {"hoc_sinh_id": hoc_sinh_id, "ket_qua": "da_an_danh_truoc_do"}

    # Ghi nhat ky TRUOC khi xoa (sau khi xoa se khong con doi chieu duoc)
    audit.ghi_nhat_ky("an_danh_hoc_sinh",
                      f"Bat dau an danh hoa (ly do: {ly_do}); lop {res.data[0].get('ten_lop')}",
                      nguoi_dung=nguoi_thuc_hien, doi_tuong_id=hoc_sinh_id)

    mt = supabase.table("muc_tieu").select("id").eq("hoc_sinh_id", hoc_sinh_id).execute()
    muc_tieu_ids = [m["id"] for m in (mt.data or [])]

    _xoa_van_ban_tu_do(hoc_sinh_id, muc_tieu_ids)

    # Thong bao thuong chua ten -> xoa han
    try:
        supabase.table("thong_bao").delete().eq("nguoi_nhan", hoc_sinh_id).execute()
    except Exception:
        pass

    # Xoa dinh danh trong ho so nguoi dung
    ma_an_danh = f"HS-{str(hoc_sinh_id)[:8]}"
    import secrets
    supabase.table("nguoi_dung").update({
        "ho_ten": "Hoc sinh da an danh",
        "email": f"an-danh-{str(hoc_sinh_id)[:8]}@da-xoa.local",
        "email_phu_huynh": None,
        "mat_khau_hash": f"!khong-the-dang-nhap!{secrets.token_hex(16)}",
        "dang_hoat_dong": False,
        "da_an_danh": True,
        "thoi_diem_an_danh": datetime.now(timezone.utc).isoformat(),
    }).eq("id", hoc_sinh_id).execute()

    audit.ghi_nhat_ky("an_danh_hoc_sinh",
                      f"Hoan tat an danh hoa -> {ma_an_danh}; da xoa du lieu dinh danh "
                      f"va {len(muc_tieu_ids)} OKR van ban; giu lai so lieu thong ke",
                      nguoi_dung=nguoi_thuc_hien, doi_tuong_id=hoc_sinh_id)

    return {"hoc_sinh_id": hoc_sinh_id, "ma_an_danh": ma_an_danh,
            "so_okr_da_xu_ly": len(muc_tieu_ids), "ket_qua": "thanh_cong"}


# ------------------------------------------------------------------
#  DANH SACH DEN HAN & TAC VU DINH KY
# ------------------------------------------------------------------
def danh_sach_den_han() -> list:
    """Hoc sinh da ket thuc hoc va qua thoi han giu -> den han an danh hoa."""
    # Hoc sinh ket thuc hoc TRUOC moc nay la da qua thoi han giu
    moc = _cong_thang(date.today(), -GIU_THEM_THANG).isoformat()
    try:
        res = (supabase.table("nguoi_dung")
               .select("id, ho_ten, ten_lop, khoi, trang_thai_hoc, ngay_ket_thuc_hoc")
               .eq("vai_tro", "hoc_sinh").eq("da_an_danh", False)
               .neq("trang_thai_hoc", "dang_hoc")
               .lte("ngay_ket_thuc_hoc", moc).execute())
        return res.data or []
    except Exception as e:
        print(f"[VONG DOI] Chua doc duoc danh sach (co the chua chay migration): {str(e)[:130]}")
        return []


def chay_an_danh_dinh_ky():
    """Tac vu dinh ky: an danh hoa hoc sinh da qua han luu tru."""
    ds = danh_sach_den_han()
    if not ds:
        print("[VONG DOI] Khong co hoc sinh den han an danh hoa.")
        return
    print(f"[VONG DOI] Co {len(ds)} hoc sinh den han an danh hoa.")
    for hs in ds:
        try:
            kq = an_danh_hoc_sinh(hs["id"], ly_do="qua_han_luu_tru_tu_dong")
            print(f"[VONG DOI] {kq}")
        except Exception as e:
            print(f"[VONG DOI] Loi voi {hs.get('id')}: {str(e)[:150]}")
