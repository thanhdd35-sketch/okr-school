from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase
from auth import lay_nguoi_dung_hien_tai, chi_giao_vien

router = APIRouter()

class TaoMau(BaseModel):
    ten_mau: str
    muc_tieu_lon_mau: str
    ket_qua_then_chot_mau: str
    don_vi_mac_dinh: str
    loai_okr: str
    ten_lop: Optional[str] = None

@router.get("/")
def danh_sach_mau(ten_lop: Optional[str] = None, loai_okr: Optional[str] = None, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    query = supabase.table("mau_muc_tieu").select("*").eq("dang_hien_thi", True)
    if ten_lop:
        query = query.or_(f"ten_lop.eq.{ten_lop},ten_lop.is.null")
    if loai_okr:
        query = query.eq("loai_okr", loai_okr)
    res = query.order("ngay_tao", desc=True).execute()
    return res.data

@router.post("/")
def tao_mau(body: TaoMau, nguoi_dung=Depends(chi_giao_vien)):
    data = {
        "ten_mau": body.ten_mau,
        "muc_tieu_lon_mau": body.muc_tieu_lon_mau,
        "ket_qua_then_chot_mau": body.ket_qua_then_chot_mau,
        "don_vi_mac_dinh": body.don_vi_mac_dinh,
        "loai_okr": body.loai_okr,
        "ten_lop": body.ten_lop,
        "nguoi_tao": nguoi_dung["id"],
        "dang_hien_thi": True
    }
    res = supabase.table("mau_muc_tieu").insert(data).execute()
    return res.data[0]

@router.put("/{id}")
def sua_mau(id: str, body: TaoMau, nguoi_dung=Depends(chi_giao_vien)):
    res = supabase.table("mau_muc_tieu").update(body.dict()).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay mau")
    return res.data[0]

@router.post("/{id}/ap-dung")
def ap_dung_mau(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    mau = supabase.table("mau_muc_tieu").select("*").eq("id", id).execute()
    if not mau.data:
        raise HTTPException(status_code=404, detail="Khong tim thay mau")
    m = mau.data[0]
    return {
        "muc_tieu_lon": m["muc_tieu_lon_mau"],
        "ket_qua_then_chot": m["ket_qua_then_chot_mau"],
        "don_vi": m["don_vi_mac_dinh"],
        "loai_okr": m["loai_okr"]
    }

@router.delete("/{id}")
def xoa_mau(id: str, nguoi_dung=Depends(chi_giao_vien)):
    supabase.table("mau_muc_tieu").update({"dang_hien_thi": False}).eq("id", id).execute()
    return {"message": "Da an mau muc tieu"}
