from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

from routers import xac_thuc, muc_tieu, nguoi_dung, ky_danh_gia, mau_muc_tieu, danh_gia_cuoi_ky, thong_bao, bao_cao, quan_tri
from routers import ket_qua_then_chot
from routers import okr_to_chuc, danh_gia_giua_ky, giam_sat
from scheduler import khoi_dong_scheduler

app = FastAPI(title="OKR Truong Hoc API", version="2.6.0")

# ============================================================
#  CORS — chi cho phep dung ten mien cua nha truong (v2.6)
#  Truoc day de allow_origins=["*"]: BAT KY trang web nao tren Internet
#  cung goi duoc API nay bang token cua nguoi dung.
#
#  Cau hinh: dat bien moi truong CORS_ORIGINS, cac ten mien cach nhau bang dau phay
#    VD: CORS_ORIGINS=https://okr-truong.vercel.app,https://okr.truong.edu.vn
#  Neu chua dat -> chi chap nhan localhost (phat trien) va *.vercel.app.
# ============================================================
_cors_env = os.getenv("CORS_ORIGINS", "").strip()
if _cors_env:
    CORS_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]
    CORS_REGEX = None
    print(f"[CORS] Chi cho phep: {CORS_ORIGINS}")
else:
    CORS_ORIGINS = []
    CORS_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://[a-zA-Z0-9-]+\.vercel\.app$"
    print("[CORS] CANH BAO: chua dat CORS_ORIGINS -> tam chap nhan localhost va *.vercel.app. "
          "Nen dat CORS_ORIGINS ve dung ten mien chinh thuc cua truong.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_REGEX,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ============================================================
#  Canh bao cau hinh bao mat khi khoi dong
# ============================================================
_jwt_secret = os.getenv("JWT_SECRET", "")
if len(_jwt_secret.encode()) < 32:
    print("[BAO MAT] CANH BAO: JWT_SECRET ngan hon 32 byte — de bi do khoa. "
          "Hay doi sang chuoi ngau nhien it nhat 32 ky tu tren Railway.")

# Global exception handler - đảm bảo luôn trả về JSON thay vì drop connection
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {request.method} {request.url}: {exc}")
    traceback.print_exc()
    # Khong tu dat Access-Control-Allow-Origin: * o day nua — de CORSMiddleware
    # quyet dinh theo danh sach ten mien duoc phep.
    return JSONResponse(
        status_code=500,
        content={"detail": f"Loi server: {str(exc)[:200]}"},
    )

app.include_router(xac_thuc.router, prefix="/api/v1/xac-thuc", tags=["Xac thuc"])
app.include_router(muc_tieu.router, prefix="/api/v1/muc-tieu", tags=["Muc tieu"])
app.include_router(nguoi_dung.router, prefix="/api/v1/nguoi-dung", tags=["Nguoi dung"])
app.include_router(ky_danh_gia.router, prefix="/api/v1/ky-danh-gia", tags=["Ky danh gia"])
app.include_router(mau_muc_tieu.router, prefix="/api/v1/mau-muc-tieu", tags=["Mau muc tieu"])
app.include_router(danh_gia_cuoi_ky.router, prefix="/api/v1/danh-gia-cuoi-ky", tags=["Danh gia cuoi ky"])
app.include_router(thong_bao.router, prefix="/api/v1/thong-bao", tags=["Thong bao"])
app.include_router(bao_cao.router, prefix="/api/v1/bao-cao", tags=["Bao cao"])
app.include_router(quan_tri.router, prefix="/api/v1/quan-tri", tags=["Quan tri"])
app.include_router(ket_qua_then_chot.router, prefix="/api/v1/kr", tags=["Ket qua then chot"])
app.include_router(okr_to_chuc.router, prefix="/api/v1/okr-to-chuc", tags=["OKR to chuc"])
app.include_router(danh_gia_giua_ky.router, prefix="/api/v1/danh-gia-giua-ky", tags=["Danh gia giua ky"])
app.include_router(giam_sat.router, prefix="/api/v1/giam-sat", tags=["Giam sat"])

@app.on_event("startup")
async def startup_event():
    khoi_dong_scheduler()

@app.get("/")
def root():
    return {"message": "OKR Truong Hoc API dang chay"}
