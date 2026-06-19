from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase
from auth import lay_nguoi_dung_hien_tai, chi_giao_vien

router = APIRouter()


class DanhGiaNhanhBody(BaseModel):
    ky_danh_gia_id: str
    trang_thai_nhanh: str  # dang_tot | can_theo_doi | can_gap_ngay
    nhan_xet_ngan: Optional[str] = None


class TuKiemTraBody(BaseModel):
    ky_danh_gia_id: str
    hs_tu_kiem_tra: str


def _lay_dong(hoc_sinh_id: str, ky_id: str):
    res = supabase.table("danh_gia_giua_ky").select("*")\
        .eq("hoc_sinh_id", hoc_sinh_id).eq("ky_danh_gia_id", ky_id).execute()
    return res.data[0] if res.data else None


# ---------- GVCN: danh sách HS lớp + bản tự kiểm tra ----------
@router.get("/lop/{lop}")
def danh_sach_giua_ky(lop: str, ky_id: str, nguoi_dung=Depends(chi_giao_vien)):
    hs = supabase.table("nguoi_dung").select("id, ho_ten, so_thu_tu")\
        .eq("ten_lop", lop).eq("vai_tro", "hoc_sinh").eq("dang_hoat_dong", True)\
        .order("so_thu_tu").execute().data
    dg = supabase.table("danh_gia_giua_ky").select("*").eq("ky_danh_gia_id", ky_id).execute().data
    dg_map = {d["hoc_sinh_id"]: d for d in dg}
    mt = supabase.table("muc_tieu").select("hoc_sinh_id, tien_do_tong, trang_thai")\
        .eq("ky_danh_gia_id", ky_id).neq("trang_thai", "nhap").execute().data
    td_map: dict = {}
    for m in mt:
        td_map.setdefault(m["hoc_sinh_id"], []).append(m.get("tien_do_tong") or 0)
    out = []
    for h in hs:
        tds = td_map.get(h["id"], [])
        out.append({
            **h,
            "tien_do_tb": round(sum(tds) / len(tds), 1) if tds else 0,
            "danh_gia": dg_map.get(h["id"]),
        })
    return out


# ---------- GVCN: lưu đánh giá nhanh 1 HS ----------
@router.post("/{hoc_sinh_id}")
def luu_danh_gia_nhanh(hoc_sinh_id: str, body: DanhGiaNhanhBody, nguoi_dung=Depends(chi_giao_vien)):
    if body.trang_thai_nhanh not in ("dang_tot", "can_theo_doi", "can_gap_ngay"):
        raise HTTPException(400, "Trang thai khong hop le")
    dong = _lay_dong(hoc_sinh_id, body.ky_danh_gia_id)
    payload = {
        "trang_thai_nhanh": body.trang_thai_nhanh,
        "nhan_xet_ngan": body.nhan_xet_ngan,
        "giao_vien_id": nguoi_dung["id"],
    }
    if dong:
        res = supabase.table("danh_gia_giua_ky").update(payload).eq("id", dong["id"]).execute()
    else:
        payload.update({"hoc_sinh_id": hoc_sinh_id, "ky_danh_gia_id": body.ky_danh_gia_id})
        res = supabase.table("danh_gia_giua_ky").insert(payload).execute()
    return res.data[0]


# ---------- HS: tự kiểm tra giữa kỳ ----------
@router.post("/hs/tu-kiem-tra")
def hs_tu_kiem_tra(body: TuKiemTraBody, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung.get("vai_tro") != "hoc_sinh":
        raise HTTPException(403, "Chi hoc sinh")
    hsid = nguoi_dung["id"]
    dong = _lay_dong(hsid, body.ky_danh_gia_id)
    if dong:
        res = supabase.table("danh_gia_giua_ky").update({"hs_tu_kiem_tra": body.hs_tu_kiem_tra})\
            .eq("id", dong["id"]).execute()
    else:
        res = supabase.table("danh_gia_giua_ky").insert({
            "hoc_sinh_id": hsid, "ky_danh_gia_id": body.ky_danh_gia_id,
            "hs_tu_kiem_tra": body.hs_tu_kiem_tra}).execute()
    return res.data[0]


@router.get("/hs/cua-toi")
def hs_xem_danh_gia(ky_id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung.get("vai_tro") != "hoc_sinh":
        raise HTTPException(403, "Chi hoc sinh")
    return _lay_dong(nguoi_dung["id"], ky_id) or {}
