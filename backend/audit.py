"""
NHAT KY KIEM TOAN (AUDIT LOG) — v2.6

Ghi lai "ai — lam gi — tren doi tuong nao — luc nao — tu dau" phuc vu
Luat Bao ve du lieu ca nhan 91/2025/QH15.

NGUYEN TAC THIET KE
 1. KHONG BAO GIO lam gay luong nghiep vu: moi loi ghi log deu bi nuot.
 2. KHONG ghi noi dung nhay cam (nhan xet, mat khau) vao log — chi ghi
    dinh danh doi tuong va loai hanh dong.
 3. Han che phinh dung luong: su kien DOC du lieu nhay cam duoc gom nhom
    (cung nguoi dung + cung doi tuong trong 15 phut chi ghi 1 lan).
 4. KHONG tu dong xoa. Thoi han luu toi thieu 12-24 thang; viec dua ra
    kho luu tru dai han do luu_tru_nhat_ky.py dam nhiem.
"""

from datetime import datetime, timedelta, timezone

# ---- Danh muc hanh dong chuan hoa ----
DANG_NHAP = "dang_nhap"
DANG_NHAP_THAT_BAI = "dang_nhap_that_bai"
DOI_MAT_KHAU = "doi_mat_khau"
DAT_LAI_MAT_KHAU = "dat_lai_mat_khau"
THU_HOI_PHIEN = "thu_hoi_phien"
VO_HIEU_HOA_TK = "vo_hieu_hoa_tai_khoan"
CAP_NHAT_TAI_KHOAN = "cap_nhat_tai_khoan"
XEM_DU_LIEU_NHAY_CAM = "xem_du_lieu_nhay_cam"
GHI_NHAN_XET = "ghi_nhan_xet"
HOAN_TAT_DANH_GIA = "hoan_tat_danh_gia"
DUYET_OKR = "duyet_okr"
XUAT_BAO_CAO = "xuat_bao_cao"
GOI_AI = "goi_ai"

# Cac hanh dong mang tinh "doc" -> gom nhom de tranh phinh du lieu
_HANH_DONG_GOM_NHOM = {XEM_DU_LIEU_NHAY_CAM}
_CUA_SO_GOM_NHOM_PHUT = 15
_da_ghi_gan_day: dict = {}     # {(nguoi_dung_id, hanh_dong, doi_tuong_id): thoi_diem}


def lay_ip(request) -> str:
    """Lay IP that cua client, uu tien header do reverse proxy (Railway/Vercel) dat."""
    if request is None:
        return ""
    try:
        chuyen_tiep = request.headers.get("x-forwarded-for")
        if chuyen_tiep:
            return chuyen_tiep.split(",")[0].strip()
        return request.client.host if request.client else ""
    except Exception:
        return ""


def _nen_bo_qua(nguoi_dung_id, hanh_dong, doi_tuong_id) -> bool:
    """True neu su kien doc nay vua duoc ghi trong cua so gom nhom."""
    if hanh_dong not in _HANH_DONG_GOM_NHOM:
        return False
    khoa = (nguoi_dung_id, hanh_dong, doi_tuong_id)
    now = datetime.now()
    lan_truoc = _da_ghi_gan_day.get(khoa)
    if lan_truoc and (now - lan_truoc) < timedelta(minutes=_CUA_SO_GOM_NHOM_PHUT):
        return True
    _da_ghi_gan_day[khoa] = now
    # Don bo nho dinh ky de khong phinh vo han
    if len(_da_ghi_gan_day) > 5000:
        nguong = now - timedelta(minutes=_CUA_SO_GOM_NHOM_PHUT)
        for k in [k for k, v in _da_ghi_gan_day.items() if v < nguong]:
            _da_ghi_gan_day.pop(k, None)
    return False


def ghi_nhat_ky(hanh_dong: str, mo_ta: str = "", nguoi_dung=None,
                nguoi_dung_id: str = None, doi_tuong_id: str = None,
                request=None, ket_qua: str = "thanh_cong", vai_tro: str = None):
    """Ghi mot su kien vao nhat ky kiem toan.

    Tuyet doi khong nem loi ra ngoai — nghiep vu luon duoc uu tien.
    """
    try:
        if nguoi_dung and not nguoi_dung_id:
            nguoi_dung_id = nguoi_dung.get("id")
        if nguoi_dung and not vai_tro:
            vai_tro = nguoi_dung.get("vai_tro")

        if _nen_bo_qua(nguoi_dung_id, hanh_dong, doi_tuong_id):
            return

        from database import supabase
        ban_ghi = {
            "hanh_dong": hanh_dong,
            "mo_ta": (mo_ta or "")[:500],
            "thoi_diem": datetime.now(timezone.utc).isoformat(),
            "ket_qua": ket_qua,
        }
        if nguoi_dung_id:
            ban_ghi["nguoi_dung_id"] = nguoi_dung_id
        if doi_tuong_id:
            ban_ghi["doi_tuong_id"] = doi_tuong_id
        if vai_tro:
            ban_ghi["vai_tro"] = vai_tro
        ip = lay_ip(request)
        if ip:
            ban_ghi["dia_chi_ip"] = ip

        try:
            supabase.table("nhat_ky_hoat_dong").insert(ban_ghi).execute()
        except Exception as loi_day_du:
            # Bang co the thieu cot (vi du chua chay migration bo sung 'mo_ta').
            # Thu lai voi bo cot toi thieu chac chan ton tai -> khong mat dau vet.
            print(f"[AUDIT] Ghi day du that bai, thu bo cot toi thieu: {str(loi_day_du)[:160]}")
            toi_thieu = {"hanh_dong": hanh_dong, "thoi_diem": ban_ghi["thoi_diem"]}
            if nguoi_dung_id:
                toi_thieu["nguoi_dung_id"] = nguoi_dung_id
            supabase.table("nhat_ky_hoat_dong").insert(toi_thieu).execute()
    except Exception as e:
        print(f"[AUDIT] Khong ghi duoc nhat ky ({hanh_dong}): {str(e)[:120]}")
