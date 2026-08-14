import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 480))

security = HTTPBearer()

# ============================================================
#  CHONG DO MAT KHAU (v2.6)
#  Khoa theo TAI KHOAN + backoff luy tien. IP chi la tin hieu phu
#  (truong dung chung 1 dai IP -> khoa theo IP se khoa ca truong).
# ============================================================
NGUONG_SAI_TK = 5          # so lan sai truoc khi bat dau khoa tai khoan
BAC_KHOA_PHUT = [1, 2, 5, 15, 30, 60]   # backoff luy tien (phut)
CUA_SO_RESET_PHUT = 30     # khong sai them trong 30' -> reset bo dem
NGUONG_SAI_IP = 50         # nguong IP cao (tin hieu phu, tranh khoa ca truong)

dang_nhap_sai_tk: dict = {}   # {tai_khoan: {"so_lan", "khoa_den", "lan_cuoi"}}
dang_nhap_sai_ip: dict = {}   # {ip: {"so_lan", "lan_dau"}}

def hash_mat_khau(mat_khau: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(mat_khau.encode(), salt).decode()

def kiem_tra_mat_khau(mat_khau: str, hash: str) -> bool:
    return bcrypt.checkpw(mat_khau.encode(), hash.encode())

def tao_token(data: dict) -> str:
    payload = data.copy()
    het_han = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload["exp"] = het_han
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def giai_ma_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token da het han, vui long dang nhap lai")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token khong hop le")

def lay_nguoi_dung_hien_tai(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = giai_ma_token(token)
    return payload

def chi_quan_tri(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung.get("vai_tro") != "quan_tri":
        raise HTTPException(status_code=403, detail="Chi quan tri vien moi co quyen nay")
    return nguoi_dung

def chi_giao_vien(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung.get("vai_tro") not in ["quan_tri", "giao_vien"]:
        raise HTTPException(status_code=403, detail="Chi giao vien moi co quyen nay")
    return nguoi_dung

def chi_pho_ht_tro_len(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    """Pho Hieu truong hoac Quan tri vien — dat OKR truong, xem moi khoi."""
    if nguoi_dung.get("vai_tro") not in ["quan_tri", "pho_hieu_truong"]:
        raise HTTPException(status_code=403, detail="Chi Pho Hieu truong hoac Quan tri vien")
    return nguoi_dung

def require_truong_khoi(khoi: str):
    """Truong khoi cua dung khoi do (hoac Pho HT / QTV)."""
    def checker(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
        vt = nguoi_dung.get("vai_tro")
        if vt in ("quan_tri", "pho_hieu_truong"):
            return nguoi_dung
        if vt == "giao_vien" and nguoi_dung.get("la_truong_khoi") \
           and str(nguoi_dung.get("khoi_phu_trach")) == str(khoi):
            return nguoi_dung
        raise HTTPException(status_code=403, detail=f"Chi Truong khoi {khoi} moi co quyen nay")
    return checker

def require_gvcn_cua_lop(lop: str):
    """GVCN cua dung lop do (dung ten_lop). Pho HT / QTV cung qua."""
    def checker(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
        vt = nguoi_dung.get("vai_tro")
        if vt in ("quan_tri", "pho_hieu_truong"):
            return nguoi_dung
        if vt == "giao_vien" and str(nguoi_dung.get("ten_lop")) == str(lop):
            return nguoi_dung
        raise HTTPException(status_code=403, detail=f"Chi GVCN lop {lop} moi co quyen nay")
    return checker

def kiem_tra_gioi_han_dang_nhap(tai_khoan: str, ip: str = ""):
    """Chan dang nhap khi tai khoan dang bi khoa tam theo backoff luy tien."""
    now = datetime.now()
    tk = (tai_khoan or "").strip().lower()

    ban_ghi = dang_nhap_sai_tk.get(tk)
    if ban_ghi:
        khoa_den = ban_ghi.get("khoa_den")
        if khoa_den and now < khoa_den:
            con_lai = max(1, int((khoa_den - now).total_seconds() // 60) + 1)
            raise HTTPException(
                status_code=429,
                detail=f"Tai khoan tam bi khoa do dang nhap sai nhieu lan. Vui long thu lai sau {con_lai} phut."
            )
        # Het cua so quan sat -> reset bo dem
        if (now - ban_ghi.get("lan_cuoi", now)) > timedelta(minutes=CUA_SO_RESET_PHUT):
            dang_nhap_sai_tk.pop(tk, None)

    # IP chi la tin hieu phu: nguong rat cao de khong khoa nham ca truong
    if ip:
        ip_rec = dang_nhap_sai_ip.get(ip)
        if ip_rec and (now - ip_rec["lan_dau"]) < timedelta(minutes=10) \
           and ip_rec["so_lan"] >= NGUONG_SAI_IP:
            raise HTTPException(
                status_code=429,
                detail="Phat hien qua nhieu yeu cau dang nhap that bai tu mang nay. Vui long thu lai sau."
            )


def ghi_dang_nhap_sai(tai_khoan: str, ip: str = ""):
    """Ghi nhan 1 lan dang nhap sai va tinh thoi gian khoa luy tien."""
    now = datetime.now()
    tk = (tai_khoan or "").strip().lower()

    ban_ghi = dang_nhap_sai_tk.get(tk)
    if not ban_ghi or (now - ban_ghi.get("lan_cuoi", now)) > timedelta(minutes=CUA_SO_RESET_PHUT):
        ban_ghi = {"so_lan": 0, "khoa_den": None, "lan_cuoi": now}

    ban_ghi["so_lan"] += 1
    ban_ghi["lan_cuoi"] = now

    if ban_ghi["so_lan"] >= NGUONG_SAI_TK:
        bac = min(ban_ghi["so_lan"] - NGUONG_SAI_TK, len(BAC_KHOA_PHUT) - 1)
        ban_ghi["khoa_den"] = now + timedelta(minutes=BAC_KHOA_PHUT[bac])

    dang_nhap_sai_tk[tk] = ban_ghi

    if ip:
        ip_rec = dang_nhap_sai_ip.get(ip)
        if not ip_rec or (now - ip_rec["lan_dau"]) > timedelta(minutes=10):
            dang_nhap_sai_ip[ip] = {"so_lan": 1, "lan_dau": now}
        else:
            ip_rec["so_lan"] += 1


def xoa_dang_nhap_sai(tai_khoan: str, ip: str = ""):
    """Dang nhap thanh cong -> xoa bo dem cua tai khoan do."""
    dang_nhap_sai_tk.pop((tai_khoan or "").strip().lower(), None)


# ============================================================
#  KIEM SOAT PHAM VI TRUY CAP DU LIEU HOC SINH (v2.6)
#  Chan IDOR: moi vai tro chi doc/ghi duoc du lieu trong pham vi minh.
# ============================================================
def kiem_tra_quyen_tren_hoc_sinh(nguoi_dung: dict, hs_id: str):
    """Raise 403 neu nguoi dung khong duoc phep truy cap du lieu cua hs_id.

    - hoc_sinh   : chi chinh minh
    - phu_huynh  : chi dung con da rang buoc trong token (hoc_sinh_id)
    - giao_vien  : chi HS cung lop chu nhiem; truong khoi -> them ca khoi phu trach
    - pho_hieu_truong / quan_tri : toan truong
    """
    from database import supabase   # import cuc bo de tranh vong lap import

    vai_tro = nguoi_dung.get("vai_tro")

    if vai_tro in ("quan_tri", "pho_hieu_truong"):
        return

    if vai_tro == "hoc_sinh":
        if str(nguoi_dung.get("id")) != str(hs_id):
            raise HTTPException(status_code=403, detail="Khong co quyen tren du lieu hoc sinh nay")
        return

    if vai_tro == "phu_huynh":
        con_id = nguoi_dung.get("hoc_sinh_id")
        if not con_id or str(con_id) != str(hs_id):
            raise HTTPException(status_code=403, detail="Phu huynh chi xem duoc du lieu cua con minh")
        return

    if vai_tro == "giao_vien":
        hs = supabase.table("nguoi_dung").select("ten_lop, khoi").eq("id", hs_id).execute()
        if not hs.data:
            raise HTTPException(status_code=404, detail="Khong tim thay hoc sinh")
        hs_lop = hs.data[0].get("ten_lop")
        hs_khoi = hs.data[0].get("khoi")
        if hs_lop and str(hs_lop) == str(nguoi_dung.get("ten_lop")):
            return
        if nguoi_dung.get("la_truong_khoi") and hs_khoi \
           and str(hs_khoi) == str(nguoi_dung.get("khoi_phu_trach")):
            return
        raise HTTPException(status_code=403, detail="Chi GVCN cua lop (hoac Truong khoi) moi truy cap duoc")

    raise HTTPException(status_code=403, detail="Khong co quyen truy cap")
