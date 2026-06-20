from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, timezone
from database import supabase
from auth import (lay_nguoi_dung_hien_tai, chi_pho_ht_tro_len,
                  require_truong_khoi, require_gvcn_cua_lop)

router = APIRouter()


class OKRToChucBody(BaseModel):
    muc_tieu_lon: str
    ket_qua_then_chot: Optional[List[Any]] = None
    mo_ta: Optional[str] = None
    ky_danh_gia_id: Optional[str] = None
    khoi: Optional[str] = None
    lop: Optional[str] = None
    han_hoan_thanh: Optional[str] = None
    tien_do: Optional[float] = None
    minh_chung_url: Optional[str] = None
    nhan_xet_cuoi_ky: Optional[str] = None

def _them_field_mo_rong(data: dict, body: "OKRToChucBody"):
    if body.han_hoan_thanh: data["han_hoan_thanh"] = body.han_hoan_thanh
    if body.tien_do is not None: data["tien_do"] = body.tien_do
    if body.minh_chung_url is not None: data["minh_chung_url"] = body.minh_chung_url
    if body.nhan_xet_cuoi_ky is not None: data["nhan_xet_cuoi_ky"] = body.nhan_xet_cuoi_ky


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
    _them_field_mo_rong(data, body)
    try:
        res = supabase.table("okr_to_chuc").insert(data).execute()
    except Exception:
        for k in ["han_hoan_thanh", "tien_do", "minh_chung_url", "nhan_xet_cuoi_ky"]:
            data.pop(k, None)
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
    _them_field_mo_rong(data, body)
    try:
        res = supabase.table("okr_to_chuc").update(data).eq("id", id).eq("cap_okr", "truong").execute()
    except Exception:
        for k in ["han_hoan_thanh", "tien_do", "minh_chung_url", "nhan_xet_cuoi_ky"]:
            data.pop(k, None)
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


# ---------- OKR cấp LỚP (GVCN đặt) ----------
@router.post("/lop/{lop}")
def tao_okr_lop(lop: str, body: OKRToChucBody, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    require_gvcn_cua_lop(lop)(nguoi_dung)
    data = {
        "cap_okr": "lop", "lop": lop,
        "muc_tieu_lon": body.muc_tieu_lon,
        "ket_qua_then_chot": body.ket_qua_then_chot,
        "mo_ta": body.mo_ta,
        "ky_danh_gia_id": body.ky_danh_gia_id,
        "nguoi_tao_id": nguoi_dung["id"],
    }
    _them_field_mo_rong(data, body)
    try:
        res = supabase.table("okr_to_chuc").insert(data).execute()
    except Exception:
        for k in ["han_hoan_thanh", "tien_do", "minh_chung_url", "nhan_xet_cuoi_ky"]:
            data.pop(k, None)
        res = supabase.table("okr_to_chuc").insert(data).execute()
    return res.data[0]


@router.get("/lop/{lop}")
def danh_sach_okr_lop(lop: str, ky_id: Optional[str] = None, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    q = supabase.table("okr_to_chuc").select("*").eq("cap_okr", "lop").eq("lop", lop).eq("trang_thai", "hoat_dong")
    if ky_id:
        q = q.eq("ky_danh_gia_id", ky_id)
    return q.order("ngay_tao", desc=True).execute().data


class BaoCaoBody(BaseModel):
    ket_qua_then_chot: List[Any]   # KR da cap nhat gia_tri_hien_tai + ngay_du_lieu
    tien_do: float
    nhan_xet: Optional[str] = None
    loai_bao_cao: Optional[str] = None  # trong_ky | hoan_thanh

@router.put("/{id}/bao-cao")
def bao_cao_okr(id: str, body: BaoCaoBody, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    cur = supabase.table("okr_to_chuc").select("nguoi_tao_id").eq("id", id).execute()
    if not cur.data:
        raise HTTPException(404, "Khong tim thay OKR")
    if nguoi_dung.get("vai_tro") not in ("pho_hieu_truong", "quan_tri") \
       and cur.data[0].get("nguoi_tao_id") != nguoi_dung["id"]:
        raise HTTPException(403, "Khong co quyen bao cao OKR nay")
    data = {
        "ket_qua_then_chot": body.ket_qua_then_chot,
        "tien_do": body.tien_do,
        "nhan_xet_cuoi_ky": body.nhan_xet,
        "ngay_cap_nhat": datetime.now(timezone.utc).isoformat(),
    }
    res = supabase.table("okr_to_chuc").update(data).eq("id", id).execute()
    return res.data[0] if res.data else {"message": "ok"}

@router.delete("/{id}")
def xoa_okr(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    # PHT/QTV xoa bat ky; nguoi tao xoa OKR cua minh
    cur = supabase.table("okr_to_chuc").select("nguoi_tao_id").eq("id", id).execute()
    if not cur.data:
        raise HTTPException(404, "Khong tim thay OKR")
    if nguoi_dung.get("vai_tro") not in ("pho_hieu_truong", "quan_tri") \
       and cur.data[0].get("nguoi_tao_id") != nguoi_dung["id"]:
        raise HTTPException(403, "Khong co quyen xoa OKR nay")
    supabase.table("okr_to_chuc").delete().eq("id", id).execute()
    return {"message": "Da xoa OKR"}
