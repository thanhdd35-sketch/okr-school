from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from database import supabase
from auth import lay_nguoi_dung_hien_tai, chi_giao_vien

router = APIRouter()

class CapNhatNhanXet(BaseModel):
    nhan_xet_gv: str

class YKienPhuHuynh(BaseModel):
    phan_hoi_ph: str

@router.get("/{hs_id}")
def xem_danh_gia(hs_id: str, ky_id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("danh_gia_cuoi_ky").select("*").eq("hoc_sinh_id", hs_id).eq("ky_danh_gia_id", ky_id).execute()
    if not res.data:
        return {"hoc_sinh_id": hs_id, "ky_danh_gia_id": ky_id, "nhan_xet_gv": None, "phan_hoi_ph": None, "trang_thai": "mo"}
    return res.data[0]

@router.put("/{hs_id}")
def cap_nhat_nhan_xet(hs_id: str, ky_id: str, body: CapNhatNhanXet, nguoi_dung=Depends(chi_giao_vien)):
    res = supabase.table("danh_gia_cuoi_ky").select("*").eq("hoc_sinh_id", hs_id).eq("ky_danh_gia_id", ky_id).execute()
    if res.data:
        supabase.table("danh_gia_cuoi_ky").update({"nhan_xet_gv": body.nhan_xet_gv}).eq("hoc_sinh_id", hs_id).eq("ky_danh_gia_id", ky_id).execute()
    else:
        supabase.table("danh_gia_cuoi_ky").insert({
            "hoc_sinh_id": hs_id,
            "ky_danh_gia_id": ky_id,
            "nhan_xet_gv": body.nhan_xet_gv
        }).execute()
    return {"message": "Da luu nhan xet"}

@router.post("/{hs_id}/hoan-tat")
def hoan_tat_danh_gia(hs_id: str, ky_id: str, nguoi_dung=Depends(chi_giao_vien)):
    res = supabase.table("danh_gia_cuoi_ky").select("*").eq("hoc_sinh_id", hs_id).eq("ky_danh_gia_id", ky_id).execute()
    thoi_diem = datetime.now(timezone.utc).isoformat()

    if res.data:
        supabase.table("danh_gia_cuoi_ky").update({
            "trang_thai": "hoan_tat",
            "thoi_diem_hoan_tat": thoi_diem
        }).eq("hoc_sinh_id", hs_id).eq("ky_danh_gia_id", ky_id).execute()
    else:
        supabase.table("danh_gia_cuoi_ky").insert({
            "hoc_sinh_id": hs_id,
            "ky_danh_gia_id": ky_id,
            "trang_thai": "hoan_tat",
            "thoi_diem_hoan_tat": thoi_diem
        }).execute()

    hoc_sinh = supabase.table("nguoi_dung").select("email_phu_huynh, ho_ten").eq("id", hs_id).execute()
    if hoc_sinh.data and hoc_sinh.data[0].get("email_phu_huynh"):
        from email_service import gui_email_hoan_tat_danh_gia
        ky = supabase.table("ky_danh_gia").select("ten_ky").eq("id", ky_id).execute()
        ten_ky = ky.data[0]["ten_ky"] if ky.data else ""
        gui_email_hoan_tat_danh_gia(hoc_sinh.data[0]["email_phu_huynh"], hoc_sinh.data[0]["ho_ten"], ten_ky)

    return {"message": "Da hoan tat danh gia cuoi ky"}

@router.put("/{hs_id}/y-kien")
def y_kien_phu_huynh(hs_id: str, ky_id: str, body: YKienPhuHuynh, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung.get("vai_tro") != "phu_huynh":
        raise HTTPException(status_code=403, detail="Chi phu huynh moi duoc gui y kien")

    res = supabase.table("danh_gia_cuoi_ky").select("*").eq("hoc_sinh_id", hs_id).eq("ky_danh_gia_id", ky_id).execute()
    if res.data:
        supabase.table("danh_gia_cuoi_ky").update({"phan_hoi_ph": body.phan_hoi_ph}).eq("hoc_sinh_id", hs_id).eq("ky_danh_gia_id", ky_id).execute()
    else:
        supabase.table("danh_gia_cuoi_ky").insert({
            "hoc_sinh_id": hs_id,
            "ky_danh_gia_id": ky_id,
            "phan_hoi_ph": body.phan_hoi_ph
        }).execute()

    gv_res = supabase.table("nguoi_dung").select("id").eq("ten_lop", nguoi_dung.get("ten_lop")).eq("vai_tro", "giao_vien").execute()
    if gv_res.data:
        hs = supabase.table("nguoi_dung").select("ho_ten").eq("id", hs_id).execute()
        ten_hs = hs.data[0]["ho_ten"] if hs.data else ""
        supabase.table("thong_bao").insert({
            "nguoi_nhan": gv_res.data[0]["id"],
            "loai": "y_kien_phu_huynh",
            "tieu_de": "Phu huynh gui y kien",
            "noi_dung": f"Phu huynh cua {ten_hs} da gui y kien cuoi ky"
        }).execute()

    return {"message": "Da gui y kien gia dinh"}
