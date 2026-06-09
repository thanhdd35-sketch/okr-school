from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from routers import xac_thuc, muc_tieu, nguoi_dung, ky_danh_gia, mau_muc_tieu, danh_gia_cuoi_ky, thong_bao, bao_cao, ai, quan_tri
from routers import ket_qua_then_chot
from scheduler import khoi_dong_scheduler

app = FastAPI(title="OKR Truong Hoc API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(xac_thuc.router, prefix="/api/v1/xac-thuc", tags=["Xac thuc"])
app.include_router(muc_tieu.router, prefix="/api/v1/muc-tieu", tags=["Muc tieu"])
app.include_router(nguoi_dung.router, prefix="/api/v1/nguoi-dung", tags=["Nguoi dung"])
app.include_router(ky_danh_gia.router, prefix="/api/v1/ky-danh-gia", tags=["Ky danh gia"])
app.include_router(mau_muc_tieu.router, prefix="/api/v1/mau-muc-tieu", tags=["Mau muc tieu"])
app.include_router(danh_gia_cuoi_ky.router, prefix="/api/v1/danh-gia-cuoi-ky", tags=["Danh gia cuoi ky"])
app.include_router(thong_bao.router, prefix="/api/v1/thong-bao", tags=["Thong bao"])
app.include_router(bao_cao.router, prefix="/api/v1/bao-cao", tags=["Bao cao"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(quan_tri.router, prefix="/api/v1/quan-tri", tags=["Quan tri"])
app.include_router(ket_qua_then_chot.router, prefix="/api/v1/kr", tags=["Ket qua then chot"])

@app.on_event("startup")
async def startup_event():
    khoi_dong_scheduler()

@app.get("/")
def root():
    return {"message": "OKR Truong Hoc API dang chay"}
