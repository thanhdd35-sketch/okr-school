from fastapi import APIRouter, Depends
from typing import Optional
from database import supabase
from auth import chi_quan_tri

router = APIRouter()

@router.get("/thong-ke-tong-quan")
def thong_ke_tong_quan(ky_id: Optional[str] = None, nguoi_dung=Depends(chi_quan_tri)):
    gv_res = supabase.table("nguoi_dung").select("id, ho_ten, ten_lop, si_so").eq("vai_tro", "giao_vien").eq("dang_hoat_dong", True).execute()
    ket_qua = []

    for gv in gv_res.data:
        ten_lop = gv.get("ten_lop")
        if not ten_lop:
            continue

        hs_res = supabase.table("nguoi_dung").select("id").eq("ten_lop", ten_lop).eq("vai_tro", "hoc_sinh").eq("dang_hoat_dong", True).execute()
        hs_ids = [h["id"] for h in hs_res.data]
        so_hs = len(hs_ids)

        if not hs_ids:
            ket_qua.append({
                "ten_giao_vien": gv["ho_ten"],
                "ten_lop": ten_lop,
                "si_so": gv.get("si_so", 0),
                "so_hs_nop": 0,
                "so_hs_duoc_duyet": 0,
                "ti_le_hoan_thanh": 0
            })
            continue

        query = supabase.table("muc_tieu").select("hoc_sinh_id, trang_thai, tien_do_phan_tram").in_("hoc_sinh_id", hs_ids)
        if ky_id:
            query = query.eq("ky_danh_gia_id", ky_id)
        mt_res = query.execute()

        hs_nop = set(m["hoc_sinh_id"] for m in mt_res.data)
        hs_duoc_duyet = set(m["hoc_sinh_id"] for m in mt_res.data if m["trang_thai"] == "da_duyet")
        tien_do_all = [m["tien_do_phan_tram"] for m in mt_res.data if m["tien_do_phan_tram"] is not None]
        ti_le = round(sum(tien_do_all) / len(tien_do_all), 1) if tien_do_all else 0

        ket_qua.append({
            "ten_giao_vien": gv["ho_ten"],
            "ten_lop": ten_lop,
            "si_so": gv.get("si_so", so_hs),
            "so_hs_nop": len(hs_nop),
            "so_hs_duoc_duyet": len(hs_duoc_duyet),
            "ti_le_hoan_thanh": ti_le
        })

    return ket_qua

@router.get("/nhat-ky")
def xem_nhat_ky(
    nguoi_dung_id: Optional[str] = None,
    hanh_dong: Optional[str] = None,
    tu_ngay: Optional[str] = None,
    den_ngay: Optional[str] = None,
    nguoi_dung=Depends(chi_quan_tri)
):
    query = supabase.table("nhat_ky_hoat_dong").select("*, nguoi_dung:nguoi_dung_id(ho_ten, email)")

    if nguoi_dung_id:
        query = query.eq("nguoi_dung_id", nguoi_dung_id)
    if hanh_dong:
        query = query.eq("hanh_dong", hanh_dong)
    if tu_ngay:
        query = query.gte("thoi_diem", tu_ngay)
    if den_ngay:
        query = query.lte("thoi_diem", den_ngay)

    res = query.order("thoi_diem", desc=True).limit(200).execute()
    return res.data
