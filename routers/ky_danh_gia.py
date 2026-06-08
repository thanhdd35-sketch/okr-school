from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from database import supabase
from auth import lay_nguoi_dung_hien_tai, chi_quan_tri

router = APIRouter()

class TaoKy(BaseModel):
    ten_ky: str
    ngay_bat_dau: date
    ngay_ket_thuc: date

@router.get("/")
def danh_sach_ky(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("ky_danh_gia").select("*").order("ngay_tao", desc=True).execute()
    return res.data

@router.post("/")
def tao_ky(body: TaoKy, nguoi_dung=Depends(chi_quan_tri)):
    data = {
        "ten_ky": body.ten_ky,
        "trang_thai": "mo",
        "ngay_bat_dau": body.ngay_bat_dau.isoformat(),
        "ngay_ket_thuc": body.ngay_ket_thuc.isoformat(),
        "nguoi_tao": nguoi_dung["id"]
    }
    res = supabase.table("ky_danh_gia").insert(data).execute()
    return res.data[0]

@router.put("/{id}/khoa")
def khoa_ky(id: str, nguoi_dung=Depends(chi_quan_tri)):
    res = supabase.table("ky_danh_gia").update({"trang_thai": "khoa"}).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay ky danh gia")
    return {"message": "Da khoa ky danh gia"}

@router.put("/{id}/mo")
def mo_ky(id: str, nguoi_dung=Depends(chi_quan_tri)):
    res = supabase.table("ky_danh_gia").update({"trang_thai": "mo"}).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay ky danh gia")
    return {"message": "Da mo ky danh gia"}
