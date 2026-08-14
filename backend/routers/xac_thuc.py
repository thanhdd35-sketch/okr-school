from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from database import supabase
from auth import (hash_mat_khau, kiem_tra_mat_khau, tao_token, tao_token_lam_moi,
                  kiem_tra_gioi_han_dang_nhap, ghi_dang_nhap_sai,
                  xoa_dang_nhap_sai, lay_nguoi_dung_hien_tai,
                  giai_ma_token, thu_hoi_phien, LOAI_LAM_MOI)
import audit

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
    kiem_tra_gioi_han_dang_nhap(body.email, ip)

    res = supabase.table("nguoi_dung").select("*").eq("email", body.email).eq("dang_hoat_dong", True).execute()
    if not res.data:
        ghi_dang_nhap_sai(body.email, ip)
        audit.ghi_nhat_ky(audit.DANG_NHAP_THAT_BAI, f"Email khong ton tai: {body.email}",
                          request=request, ket_qua="that_bai")
        raise HTTPException(status_code=401, detail="Email hoac mat khau khong dung")

    user = res.data[0]
    if not kiem_tra_mat_khau(body.mat_khau, user["mat_khau_hash"]):
        ghi_dang_nhap_sai(body.email, ip)
        audit.ghi_nhat_ky(audit.DANG_NHAP_THAT_BAI, "Sai mat khau",
                          nguoi_dung_id=user["id"], vai_tro=user.get("vai_tro"),
                          request=request, ket_qua="that_bai")
        raise HTTPException(status_code=401, detail="Email hoac mat khau khong dung")

    xoa_dang_nhap_sai(body.email, ip)
    audit.ghi_nhat_ky(audit.DANG_NHAP, "Dang nhap thanh cong",
                      nguoi_dung_id=user["id"], vai_tro=user.get("vai_tro"), request=request)

    phien_ban = int(user.get("phien_ban_token") or 1)
    token = tao_token({
        "id": user["id"],
        "email": user["email"],
        "vai_tro": user["vai_tro"],
        "ho_ten": user["ho_ten"],
        "ten_lop": user.get("ten_lop"),
        "la_truong_khoi": user.get("la_truong_khoi", False),
        "khoi_phu_trach": user.get("khoi_phu_trach"),
        "khoi": user.get("khoi"),
    }, phien_ban=phien_ban)
    refresh_token = tao_token_lam_moi(user["id"], phien_ban)

    return {
        "token": token,
        "refresh_token": refresh_token,
        "bat_buoc_doi_mat_khau": user.get("bat_buoc_doi_mat_khau", False),
        "vai_tro": user["vai_tro"],
        "ho_ten": user["ho_ten"],
        "ten_lop": user.get("ten_lop"),
        "la_truong_khoi": user.get("la_truong_khoi", False),
        "khoi_phu_trach": user.get("khoi_phu_trach"),
        "khoi": user.get("khoi"),
        "id": user["id"]
    }

@router.post("/dang-nhap-phu-huynh")
def dang_nhap_phu_huynh(body: DangNhapPhuHuynh, request: Request):
    ip = request.client.host
    kiem_tra_gioi_han_dang_nhap(body.email_phu_huynh, ip)

    res = supabase.table("nguoi_dung").select("*").eq("email_phu_huynh", body.email_phu_huynh).eq("vai_tro", "hoc_sinh").eq("dang_hoat_dong", True).execute()
    if not res.data:
        ghi_dang_nhap_sai(body.email_phu_huynh, ip)
        raise HTTPException(status_code=401, detail="Email hoac mat khau khong dung")

    hoc_sinh = res.data[0]
    if not kiem_tra_mat_khau(body.mat_khau_hoc_sinh, hoc_sinh["mat_khau_hash"]):
        ghi_dang_nhap_sai(body.email_phu_huynh, ip)
        raise HTTPException(status_code=401, detail="Email hoac mat khau khong dung")

    xoa_dang_nhap_sai(body.email_phu_huynh, ip)
    audit.ghi_nhat_ky(audit.DANG_NHAP, "Phu huynh dang nhap",
                      nguoi_dung_id=hoc_sinh["id"], vai_tro="phu_huynh",
                      doi_tuong_id=hoc_sinh["id"], request=request)

    phien_ban = int(hoc_sinh.get("phien_ban_token") or 1)
    token = tao_token({
        "id": hoc_sinh["id"],
        "email": body.email_phu_huynh,
        "vai_tro": "phu_huynh",
        "ho_ten_con": hoc_sinh["ho_ten"],
        "hoc_sinh_id": hoc_sinh["id"],
        "ten_lop": hoc_sinh.get("ten_lop")
    }, phien_ban=phien_ban)
    refresh_token = tao_token_lam_moi(hoc_sinh["id"], phien_ban)

    return {
        "token": token,
        "refresh_token": refresh_token,
        "vai_tro": "phu_huynh",
        "ho_ten_con": hoc_sinh["ho_ten"],
        "lop": hoc_sinh.get("ten_lop"),
        "hoc_sinh_id": hoc_sinh["id"],
        "id": hoc_sinh["id"],
    }

@router.post("/doi-mat-khau")
def doi_mat_khau(body: DoiMatKhauBody, request: Request, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
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

    # [v2.6] Doi mat khau -> thu hoi TAT CA phien cu (moi thiet bi khac bi dang xuat)
    thu_hoi_phien(nguoi_dung["id"])
    audit.ghi_nhat_ky(audit.DOI_MAT_KHAU, "Nguoi dung tu doi mat khau",
                      nguoi_dung=nguoi_dung, request=request)

    # Cap lai token cho chinh thiet bi dang thao tac de khong bi dang xuat oan
    moi = supabase.table("nguoi_dung").select("*").eq("id", nguoi_dung["id"]).execute()
    phien_ban = int(moi.data[0].get("phien_ban_token") or 1) if moi.data else 1
    payload = {k: v for k, v in nguoi_dung.items() if k not in ("exp", "loai", "ptv")}
    return {
        "message": "Doi mat khau thanh cong. Cac thiet bi khac da bi dang xuat.",
        "token": tao_token(payload, phien_ban=phien_ban),
        "refresh_token": tao_token_lam_moi(nguoi_dung["id"], phien_ban),
    }


class LamMoiBody(BaseModel):
    refresh_token: str


@router.post("/lam-moi-token")
def lam_moi_token(body: LamMoiBody):
    """Doi token LAM MOI lay token TRUY CAP moi (phien truot).

    Tra 401 neu phien da bi thu hoi hoac tai khoan da bi vo hieu hoa
    -> frontend se dieu huong ve man hinh dang nhap.
    """
    payload = giai_ma_token(body.refresh_token)
    if payload.get("loai") != LOAI_LAM_MOI:
        raise HTTPException(status_code=401, detail="Token lam moi khong hop le")

    uid = payload.get("id")
    res = supabase.table("nguoi_dung").select("*").eq("id", uid).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Tai khoan khong ton tai")

    user = res.data[0]
    if not user.get("dang_hoat_dong", True):
        raise HTTPException(status_code=401, detail="Tai khoan da bi vo hieu hoa")

    phien_ban = int(user.get("phien_ban_token") or 1)
    if int(payload.get("ptv") or 1) != phien_ban:
        raise HTTPException(status_code=401, detail="Phien dang nhap da bi thu hoi. Vui long dang nhap lai.")

    # Phu huynh dung chinh ban ghi hoc sinh -> giu nguyen dinh danh trong token
    if payload.get("vai_tro") == "phu_huynh":
        du_lieu = {
            "id": user["id"], "vai_tro": "phu_huynh",
            "ho_ten_con": user["ho_ten"], "hoc_sinh_id": user["id"],
            "ten_lop": user.get("ten_lop"),
        }
    else:
        du_lieu = {
            "id": user["id"], "email": user["email"], "vai_tro": user["vai_tro"],
            "ho_ten": user["ho_ten"], "ten_lop": user.get("ten_lop"),
            "la_truong_khoi": user.get("la_truong_khoi", False),
            "khoi_phu_trach": user.get("khoi_phu_trach"), "khoi": user.get("khoi"),
        }

    return {
        "token": tao_token(du_lieu, phien_ban=phien_ban),
        "refresh_token": tao_token_lam_moi(user["id"], phien_ban),
    }


@router.post("/dang-xuat-tat-ca")
def dang_xuat_tat_ca(request: Request, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    """Nguoi dung chu dong thu hoi phien tren MOI thiet bi (khi nghi lo mat may/tai khoan)."""
    thanh_cong = thu_hoi_phien(nguoi_dung["id"])
    audit.ghi_nhat_ky(audit.THU_HOI_PHIEN, "Dang xuat khoi tat ca thiet bi",
                      nguoi_dung=nguoi_dung, request=request)
    if not thanh_cong:
        raise HTTPException(
            status_code=503,
            detail="Chua the thu hoi phien. Can chay migration v2.6_phien_dang_nhap.sql."
        )
    return {"message": "Da dang xuat khoi tat ca thiet bi. Vui long dang nhap lai."}

# ============================================================
#  [DA GO BO — v2.6] Endpoint POST /khoi-phuc-admin
#  Ly do: endpoint nay KHONG yeu cau xac thuc, bat ky ai tren Internet
#  goi duoc cung reset duoc mat khau quan tri ve gia tri co dinh
#  -> chiem toan quyen he thong. Day la lo hong nghiem trong (RCE-level
#  privilege escalation) nen da duoc go bo hoan toan.
#
#  Quy trinh khoi phuc quan tri AN TOAN thay the (thuc hien thu cong):
#  Supabase Dashboard -> SQL Editor -> cap nhat mat_khau_hash bang gia tri
#  bcrypt sinh rieng, sau do bat buoc doi mat khau o lan dang nhap ke tiep.
#  Xem: docs/QUY_TRINH_KHOI_PHUC_QUAN_TRI.md
# ============================================================

@router.get("/thong-tin-ca-nhan")
def thong_tin_ca_nhan(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("nguoi_dung").select("id, email, vai_tro, ho_ten, ten_lop, email_phu_huynh, si_so, bat_buoc_doi_mat_khau").eq("id", nguoi_dung["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay nguoi dung")
    return res.data[0]
