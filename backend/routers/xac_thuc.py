from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from database import supabase
from auth import (hash_mat_khau, kiem_tra_mat_khau, tao_token, tao_token_lam_moi,
                  kiem_tra_gioi_han_dang_nhap, ghi_dang_nhap_sai,
                  xoa_dang_nhap_sai, lay_nguoi_dung_hien_tai,
                  giai_ma_token, thu_hoi_phien, LOAI_LAM_MOI)
import audit

router = APIRouter()

# Vai tro duoc tu dat lai mat khau qua email. Hoc sinh (chua thanh nien)
# phai qua GVCN de co buoc xac minh danh tinh truc tiep.
VAI_TRO_DUOC_DAT_LAI_QUA_EMAIL = ("giao_vien", "quan_tri", "pho_hieu_truong")

HAN_MA_DAT_LAI_PHUT = 30
SO_YEU_CAU_TOI_DA_MOI_GIO = 3


def kiem_tra_do_manh_mat_khau(mat_khau: str):
    """Quy tac do manh dung chung cho doi mat khau va dat lai mat khau."""
    if len(mat_khau) < 8:
        raise HTTPException(status_code=400, detail="Mat khau phai co it nhat 8 ky tu")
    if not any(c.isupper() for c in mat_khau):
        raise HTTPException(status_code=400, detail="Mat khau phai co it nhat 1 chu hoa")
    if not any(c.isdigit() for c in mat_khau):
        raise HTTPException(status_code=400, detail="Mat khau phai co it nhat 1 chu so")


def _bam_ma(ma: str) -> str:
    """Bam ma dat lai truoc khi luu — CSDL khong bao gio giu ma goc."""
    return hashlib.sha256(ma.encode()).hexdigest()

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

    kiem_tra_do_manh_mat_khau(body.mat_khau_moi)

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

# ============================================================
#  DIEU KHOAN BAO VE DU LIEU CA NHAN (Luat 91/2025/QH15)
# ============================================================
@router.get("/dieu-khoan")
def xem_dieu_khoan():
    """Tra ve noi dung dieu khoan hien hanh (khong can dang nhap)."""
    from dieu_khoan import NOI_DUNG
    return NOI_DUNG


@router.get("/trang-thai-dieu-khoan")
def trang_thai_dieu_khoan(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    """Cho biet nguoi dung da dong y ban dieu khoan hien hanh chua."""
    from dieu_khoan import PHIEN_BAN
    try:
        res = supabase.table("nguoi_dung").select("phien_ban_dieu_khoan, dong_y_dieu_khoan_luc") \
            .eq("id", nguoi_dung["id"]).execute()
    except Exception:
        return {"can_dong_y": False, "phien_ban_hien_hanh": PHIEN_BAN}   # chua chay migration
    if not res.data:
        return {"can_dong_y": False, "phien_ban_hien_hanh": PHIEN_BAN}
    da_dong_y = res.data[0].get("phien_ban_dieu_khoan")
    return {
        "can_dong_y": str(da_dong_y or "") != PHIEN_BAN,
        "phien_ban_hien_hanh": PHIEN_BAN,
        "phien_ban_da_dong_y": da_dong_y,
        "dong_y_luc": res.data[0].get("dong_y_dieu_khoan_luc"),
    }


@router.post("/dong-y-dieu-khoan")
def dong_y_dieu_khoan(request: Request, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    """Ghi nhan viec dong y — bang chung tuan thu: AI, LUC NAO, BAN NAO."""
    from dieu_khoan import PHIEN_BAN
    try:
        supabase.table("nguoi_dung").update({
            "phien_ban_dieu_khoan": PHIEN_BAN,
            "dong_y_dieu_khoan_luc": datetime.now(timezone.utc).isoformat(),
        }).eq("id", nguoi_dung["id"]).execute()
    except Exception:
        raise HTTPException(status_code=503,
            detail="Chua the ghi nhan. Can chay migration v2.6_dieu_khoan_va_dat_lai_mat_khau.sql")

    audit.ghi_nhat_ky("dong_y_dieu_khoan", f"Dong y dieu khoan ban {PHIEN_BAN}",
                      nguoi_dung=nguoi_dung, request=request)
    return {"message": "Da ghi nhan dong y", "phien_ban": PHIEN_BAN}


# ============================================================
#  QUEN MAT KHAU
#  - Hoc sinh  : bao GVCN dat lai (co buoc xac minh danh tinh truc tiep)
#  - GV/QTV/PHT: tu dat lai qua link gui email, han 30 phut, dung 1 lan
# ============================================================
class QuenMatKhauBody(BaseModel):
    email: str


class DatLaiMatKhauBody(BaseModel):
    ma: str
    mat_khau_moi: str


# Thong bao dung chung cho MOI truong hop -> khong lo email nao ton tai
THONG_BAO_CHUNG = ("Neu email nay ton tai trong he thong va thuoc nhom duoc phep tu dat lai, "
                   "mot huong dan dat lai mat khau da duoc gui den hop thu. "
                   "Hoc sinh vui long lien he giao vien chu nhiem de duoc dat lai mat khau.")


@router.post("/quen-mat-khau")
def quen_mat_khau(body: QuenMatKhauBody, request: Request):
    ip = request.client.host if request.client else ""

    res = supabase.table("nguoi_dung").select("id, email, ho_ten, vai_tro, dang_hoat_dong") \
        .eq("email", body.email).eq("dang_hoat_dong", True).execute()

    # Luon tra ve cung mot thong bao (chong do tim tai khoan ton tai)
    if not res.data:
        audit.ghi_nhat_ky("yeu_cau_dat_lai_mat_khau", f"Email khong ton tai: {body.email}",
                          request=request, ket_qua="that_bai")
        return {"message": THONG_BAO_CHUNG}

    user = res.data[0]

    # Hoc sinh / phu huynh khong dung luong email — phai qua GVCN
    if user["vai_tro"] not in VAI_TRO_DUOC_DAT_LAI_QUA_EMAIL:
        audit.ghi_nhat_ky("yeu_cau_dat_lai_mat_khau",
                          "Tai khoan hoc sinh — huong dan lien he GVCN",
                          nguoi_dung_id=user["id"], vai_tro=user["vai_tro"],
                          request=request, ket_qua="tu_choi")
        return {"message": THONG_BAO_CHUNG}

    # Gioi han so lan yeu cau trong 1 gio
    try:
        moc = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        gan_day = supabase.table("yeu_cau_dat_lai_mat_khau").select("id") \
            .eq("nguoi_dung_id", user["id"]).gte("thoi_diem_tao", moc).execute()
        if len(gan_day.data or []) >= SO_YEU_CAU_TOI_DA_MOI_GIO:
            audit.ghi_nhat_ky("yeu_cau_dat_lai_mat_khau", "Vuot gioi han yeu cau/gio",
                              nguoi_dung_id=user["id"], request=request, ket_qua="tu_choi")
            return {"message": THONG_BAO_CHUNG}
    except Exception:
        raise HTTPException(status_code=503,
            detail="Chua the xu ly. Can chay migration v2.6_dieu_khoan_va_dat_lai_mat_khau.sql")

    ma = secrets.token_urlsafe(32)
    supabase.table("yeu_cau_dat_lai_mat_khau").insert({
        "nguoi_dung_id": user["id"],
        "ma_bam": _bam_ma(ma),
        "het_han": (datetime.now(timezone.utc) + timedelta(minutes=HAN_MA_DAT_LAI_PHUT)).isoformat(),
        "dia_chi_ip": ip,
    }).execute()

    from email_service import gui_email_dat_lai_mat_khau
    gui_email_dat_lai_mat_khau(user["email"], user["ho_ten"], ma, HAN_MA_DAT_LAI_PHUT)

    audit.ghi_nhat_ky("yeu_cau_dat_lai_mat_khau", "Da gui link dat lai qua email",
                      nguoi_dung_id=user["id"], vai_tro=user["vai_tro"], request=request)
    return {"message": THONG_BAO_CHUNG}


@router.post("/dat-lai-mat-khau")
def dat_lai_mat_khau(body: DatLaiMatKhauBody, request: Request):
    kiem_tra_do_manh_mat_khau(body.mat_khau_moi)

    try:
        res = supabase.table("yeu_cau_dat_lai_mat_khau").select("*") \
            .eq("ma_bam", _bam_ma(body.ma)).eq("da_su_dung", False).execute()
    except Exception:
        raise HTTPException(status_code=503,
            detail="Chua the xu ly. Can chay migration v2.6_dieu_khoan_va_dat_lai_mat_khau.sql")

    if not res.data:
        raise HTTPException(status_code=400, detail="Ma dat lai khong hop le hoac da duoc su dung")

    yeu_cau = res.data[0]
    het_han = datetime.fromisoformat(str(yeu_cau["het_han"]).replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > het_han:
        raise HTTPException(status_code=400, detail="Ma dat lai da het han. Vui long yeu cau lai.")

    uid = yeu_cau["nguoi_dung_id"]
    supabase.table("nguoi_dung").update({
        "mat_khau_hash": hash_mat_khau(body.mat_khau_moi),
        "bat_buoc_doi_mat_khau": False,
    }).eq("id", uid).execute()

    # Danh dau ma da dung (dung 1 lan) va thu hoi moi phien dang mo
    supabase.table("yeu_cau_dat_lai_mat_khau").update({"da_su_dung": True}) \
        .eq("id", yeu_cau["id"]).execute()
    thu_hoi_phien(uid)

    audit.ghi_nhat_ky(audit.DAT_LAI_MAT_KHAU, "Tu dat lai mat khau qua email",
                      nguoi_dung_id=uid, request=request)
    return {"message": "Dat lai mat khau thanh cong. Vui long dang nhap lai."}


@router.get("/thong-tin-ca-nhan")
def thong_tin_ca_nhan(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("nguoi_dung").select("id, email, vai_tro, ho_ten, ten_lop, email_phu_huynh, si_so, bat_buoc_doi_mat_khau").eq("id", nguoi_dung["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay nguoi dung")
    return res.data[0]
