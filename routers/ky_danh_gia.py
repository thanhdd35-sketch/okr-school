from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from database import supabase
from auth import lay_nguoi_dung_hien_tai, chi_quan_tri

router = APIRouter()

class TaoKy(BaseModel):
    ten_ky: str
    mo_ta: Optional[str] = None
    ngay_bat_dau: date
    ngay_ket_thuc: date
    han_nop_muc_tieu: Optional[date] = None

class SuaKy(BaseModel):
    ten_ky: Optional[str] = None
    mo_ta: Optional[str] = None
    ngay_bat_dau: Optional[date] = None
    ngay_ket_thuc: Optional[date] = None
    han_nop_muc_tieu: Optional[date] = None

class DoiTrangThai(BaseModel):
    trang_thai: str  # chuan_bi | mo | dong

@router.get("/")
def danh_sach_ky(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("ky_danh_gia").select("*").order("ngay_tao", desc=True).execute()
    return res.data

@router.post("/")
def tao_ky(body: TaoKy, nguoi_dung=Depends(chi_quan_tri)):
    # DB chi chap nhan trang_thai: 'mo' | 'khoa'
    data = {
        "ten_ky": body.ten_ky,
        "trang_thai": "khoa",   # mac dinh: chua mo
        "ngay_bat_dau": body.ngay_bat_dau.isoformat(),
        "ngay_ket_thuc": body.ngay_ket_thuc.isoformat(),
        "nguoi_tao": nguoi_dung["id"]
    }
    if body.mo_ta:
        data["mo_ta"] = body.mo_ta
    if body.han_nop_muc_tieu:
        data["han_nop_muc_tieu"] = body.han_nop_muc_tieu.isoformat()
    res = supabase.table("ky_danh_gia").insert(data).execute()
    return res.data[0]

@router.put("/{id}")
def sua_ky(id: str, body: SuaKy, nguoi_dung=Depends(chi_quan_tri)):
    data = {}
    if body.ten_ky: data["ten_ky"] = body.ten_ky
    if body.mo_ta is not None: data["mo_ta"] = body.mo_ta
    if body.ngay_bat_dau: data["ngay_bat_dau"] = body.ngay_bat_dau.isoformat()
    if body.ngay_ket_thuc: data["ngay_ket_thuc"] = body.ngay_ket_thuc.isoformat()
    if body.han_nop_muc_tieu: data["han_nop_muc_tieu"] = body.han_nop_muc_tieu.isoformat()
    if not data:
        raise HTTPException(status_code=400, detail="Khong co du lieu de cap nhat")
    res = supabase.table("ky_danh_gia").update(data).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay ky danh gia")
    return res.data[0]

@router.patch("/{id}/trang-thai")
def doi_trang_thai(id: str, body: DoiTrangThai, nguoi_dung=Depends(chi_quan_tri)):
    cho_phep = ["mo", "khoa"]
    if body.trang_thai not in cho_phep:
        raise HTTPException(status_code=400, detail=f"Trang thai phai la: {cho_phep}")
    res = supabase.table("ky_danh_gia").update({"trang_thai": body.trang_thai}).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay ky danh gia")
    return {"message": f"Da cap nhat trang thai thanh {body.trang_thai}"}

@router.put("/{id}/khoa")
def khoa_ky(id: str, nguoi_dung=Depends(chi_quan_tri)):
    res = supabase.table("ky_danh_gia").update({"trang_thai": "dong"}).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay ky danh gia")
    return {"message": "Da khoa ky danh gia"}

@router.put("/{id}/mo")
def mo_ky(id: str, nguoi_dung=Depends(chi_quan_tri)):
    res = supabase.table("ky_danh_gia").update({"trang_thai": "mo"}).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay ky danh gia")
    return {"message": "Da mo ky danh gia"}
