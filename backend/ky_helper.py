from fastapi import HTTPException
from database import supabase


def kiem_tra_ky_mo(ky_id):
    """Raise 403 neu ky da bi khoa. Cho phep neu ky_id rong hoac ky dang mo."""
    if not ky_id:
        return
    try:
        r = supabase.table("ky_danh_gia").select("trang_thai").eq("id", ky_id).execute()
    except Exception:
        return
    if r.data and r.data[0].get("trang_thai") == "khoa":
        raise HTTPException(status_code=403,
            detail="Kỳ đánh giá đã bị khóa — chỉ xem, không thể thao tác.")


def kiem_tra_ky_mo_theo_muc_tieu(muc_tieu_id):
    """Lay ky tu muc_tieu roi kiem tra."""
    try:
        mt = supabase.table("muc_tieu").select("ky_danh_gia_id").eq("id", muc_tieu_id).execute()
        if mt.data:
            kiem_tra_ky_mo(mt.data[0].get("ky_danh_gia_id"))
    except HTTPException:
        raise
    except Exception:
        pass
