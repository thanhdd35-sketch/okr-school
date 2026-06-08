from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from database import supabase
from auth import (hash_mat_khau, kiem_tra_mat_khau, tao_token,
                  kiem_tra_gioi_han_dang_nhap, ghi_dang_nhap_sai,
                  xoa_dang_nhap_sai, lay_nguoi_dung_hien_tai)

router = APIRouter()

class DangNhapBody(BaseModel):
    email: str
    mat_khau: str

class DoiMatKhauBody(BaseModel):
    mat_khau_cu: str
    mat_khau_moi: str

class DangNhapPhuHuynh(BaseModel):
    email_phu_huynh: str
    mat_khau_hoc_sinh: str

@router.post("/dang-nhap")
def dang_nhap(body: DangNhapBody, request: Request):
    ip = request.client.host
    kiem_tra_gioi_han_dang_nhap(ip)

    res = supabase.table("nguoi_dung").select("*").eq("email", body.email).eq("dang_hoat_dong", True).execute()
    if not res.data:
        ghi_dang_nhap_sai(ip)
        raise HTTPException(status_code=401, detail="Email hoac mat khau khong dung")

    user = res.data[0]
    if not kiem_tra_mat_khau(body.mat_khau, user["mat_khau_hash"]):
        ghi_dang_nhap_sai(ip)
        raise HTTPException(status_code=401, detail="Email hoac mat khau khong dung")

    xoa_dang_nhap_sai(ip)

    token = tao_token({
        "id": user["id"],
        "email": user["email"],
        "vai_tro": user["vai_tro"],
        "ho_ten": user["ho_ten"],
        "ten_lop": user.get("ten_lop")
    })

    return {
        "token": token,
        "bat_buoc_doi_mat_khau": user.get("bat_buoc_doi_mat_khau", False),
        "vai_tro": user["vai_tro"],
        "ho_ten": user["ho_ten"]
    }

@router.post("/dang-nhap-phu-huynh")
def dang_nhap_phu_huynh(body: DangNhapPhuHuynh, request: Request):
    ip = request.client.host
    kiem_tra_gioi_han_dang_nhap(ip)

    res = supabase.table("nguoi_dung").select("*").eq("email_phu_huynh", body.email_phu_huynh).eq("vai_tro", "hoc_sinh").eq("dang_hoat_dong", True).execute()
    if not res.data:
        ghi_dang_nhap_sai(ip)
        raise HTTPException(status_code=401, detail="Khong tim thay hoc sinh voi email phu huynh nay")

    hoc_sinh = res.data[0]
    if not kiem_tra_mat_khau(body.mat_khau_hoc_sinh, hoc_sinh["mat_khau_hash"]):
        ghi_dang_nhap_sai(ip)
        raise HTTPException(status_code=401, detail="Mat khau khong dung")

    xoa_dang_nhap_sai(ip)

    token = tao_token({
        "id": hoc_sinh["id"],
        "email": body.email_phu_huynh,
        "vai_tro": "phu_huynh",
        "ho_ten_con": hoc_sinh["ho_ten"],
        "hoc_sinh_id": hoc_sinh["id"],
        "ten_lop": hoc_sinh.get("ten_lop")
    })

    return {
        "token": token,
        "vai_tro": "phu_huynh",
        "ho_ten_con": hoc_sinh["ho_ten"],
        "lop": hoc_sinh.get("ten_lop")
    }

@router.post("/doi-mat-khau")
def doi_mat_khau(body: DoiMatKhauBody, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("nguoi_dung").select("*").eq("id", nguoi_dung["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay nguoi dung")

    user = res.data[0]
    if not kiem_tra_mat_khau(body.mat_khau_cu, user["mat_khau_hash"]):
        raise HTTPException(status_code=400, detail="Mat khau cu khong dung")

    if len(body.mat_khau_moi) < 8:
        raise HTTPException(status_code=400, detail="Mat khau moi phai co it nhat 8 ky tu")
    if not any(c.isupper() for c in body.mat_khau_moi):
        raise HTTPException(status_code=400, detail="Mat khau moi phai co it nhat 1 chu hoa")
    if not any(c.isdigit() for c in body.mat_khau_moi):
        raise HTTPException(status_code=400, detail="Mat khau moi phai co it nhat 1 chu so")

    new_hash = hash_mat_khau(body.mat_khau_moi)
    supabase.table("nguoi_dung").update({
        "mat_khau_hash": new_hash,
        "bat_buoc_doi_mat_khau": False
    }).eq("id", nguoi_dung["id"]).execute()

    return {"message": "Doi mat khau thanh cong"}

@router.get("/thong-tin-ca-nhan")
def thong_tin_ca_nhan(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("nguoi_dung").select("id, email, vai_tro, ho_ten, ten_lop, email_phu_huynh, si_so, bat_buoc_doi_mat_khau").eq("id", nguoi_dung["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay nguoi dung")
    return res.data[0]
