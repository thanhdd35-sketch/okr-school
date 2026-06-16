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

# Luu tru de gioi han dang nhap sai
login_attempts: dict = {}

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

def kiem_tra_gioi_han_dang_nhap(ip: str):
    now = datetime.now()
    if ip in login_attempts:
        attempts, first_time = login_attempts[ip]
        if (now - first_time).seconds < 600:
            if attempts >= 5:
                raise HTTPException(status_code=429, detail="Qua nhieu lan dang nhap sai. Vui long thu lai sau 10 phut")
        else:
            login_attempts[ip] = (0, now)

def ghi_dang_nhap_sai(ip: str):
    now = datetime.now()
    if ip in login_attempts:
        attempts, first_time = login_attempts[ip]
        if (now - first_time).seconds < 600:
            login_attempts[ip] = (attempts + 1, first_time)
        else:
            login_attempts[ip] = (1, now)
    else:
        login_attempts[ip] = (1, now)

def xoa_dang_nhap_sai(ip: str):
    if ip in login_attempts:
        del login_attempts[ip]
