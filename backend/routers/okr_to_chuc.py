from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, timezone
from database import supabase
from auth import (lay_nguoi_dung_hien_tai, chi_pho_ht_tro_len,
                  require_truong_khoi)

router = APIRouter()


class OKRToChucBody(BaseModel):
    muc_tieu_lon: str
    ket_qua_then_chot: Optional[List[Any]] = None
    mo_ta: Optional[str] = None
    ky_danh_gia_id: Optional[str] = None
    khoi: Optional[str] = None
    lop: Optional[str] = None


# ---------- OKR cấp TRƯỜNG ----------
@router.post("/truong")
def tao_okr_truong(body: OKRToChucBody, nguoi_dung=Depends(chi_pho_ht_tro_len)):
    data = {
        "cap_okr": "truong",
        "muc_tieu_lon": body.muc_tieu_lon,
        "ket_qua_then_chot": body.ket_qua_then_chot,
        "mo_ta": body.mo_ta,
        "ky_danh_gia_id": body.ky_danh_gia_id,
        "nguoi_tao_id": nguoi_dung["id"],
    }
    res = supabase.table("okr_to_chuc").insert(data).execute()
    return res.data[0]


@router.get("/truong")
def danh_sach_okr_truong(ky_id: Optional[str] = None, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    q = supabase.table("okr_to_chuc").select("*").eq("cap_okr", "truong").eq("trang_thai", "hoat_dong")
    if ky_id:
        q = q.eq("ky_danh_gia_id", ky_id)
    return q.order("ngay_tao", desc=True).execute().data


@router.put("/truong/{id}")
def sua_okr_truong(id: str, body: OKRToChucBody, nguoi_dung=Depends(chi_pho_ht_tro_len)):
    data = {"muc_tieu_lon": body.muc_tieu_lon, "ket_qua_then_chot": body.ket_qua_then_chot,
            "mo_ta": body.mo_ta, "ngay_cap_nhat": datetime.now(timezone.utc).isoformat()}
    res = supabase.table("okr_to_chuc").update(data).eq("id", id).eq("cap_okr", "truong").execute()
    if not res.data:
        raise HTTPException(404, "Khong tim thay OKR truong")
    return res.data[0]


# ---------- OKR cấp KHỐI ----------
@router.post("/khoi/{khoi}")
def tao_okr_khoi(khoi: str, body: OKRToChucBody, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    require_truong_khoi(khoi)(nguoi_dung)  # kiem tra quyen
    data = {
        "cap_okr": "khoi", "khoi": khoi,
        "muc_tieu_lon": body.muc_tieu_lon,
        "ket_qua_then_chot": body.ket_qua_then_chot,
        "mo_ta": body.mo_ta,
        "ky_danh_gia_id": body.ky_danh_gia_id,
        "nguoi_tao_id": nguoi_dung["id"],
    }
    res = supabase.table("okr_to_chuc").insert(data).execute()
    return res.data[0]


@router.get("/khoi/{khoi}")
def danh_sach_okr_khoi(khoi: str, ky_id: Optional[str] = None, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    q = supabase.table("okr_to_chuc").select("*").eq("cap_okr", "khoi").eq("khoi", khoi).eq("trang_thai", "hoat_dong")
    if ky_id:
        q = q.eq("ky_danh_gia_id", ky_id)
    return q.order("ngay_tao", desc=True).execute().data


@router.put("/khoi/{khoi}/{id}")
def sua_okr_khoi(khoi: str, id: str, body: OKRToChucBody, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    require_truong_khoi(khoi)(nguoi_dung)
    data = {"muc_tieu_lon": body.muc_tieu_lon, "ket_qua_then_chot": body.ket_qua_then_chot,
            "mo_ta": body.mo_ta, "ngay_cap_nhat": datetime.now(timezone.utc).isoformat()}
    res = supabase.table("okr_to_chuc").update(data).eq("id", id).eq("khoi", khoi).execute()
    if not res.data:
        raise HTTPException(404, "Khong tim thay OKR khoi")
    return res.data[0]


@router.delete("/{id}")
def an_okr(id: str, nguoi_dung=Depends(chi_pho_ht_tro_len)):
    supabase.table("okr_to_chuc").update({"trang_thai": "an"}).eq("id", id).execute()
    return {"message": "Da an OKR"}
