from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, timezone
from database import supabase
from auth import lay_nguoi_dung_hien_tai, chi_giao_vien
from ky_helper import kiem_tra_ky_mo_theo_muc_tieu

router = APIRouter()

class TaoKR(BaseModel):
    noi_dung: str
    loai_kr: Optional[str] = "so"
    gia_tri_khoi_diem: Optional[float] = 0
    gia_tri_muc_tieu: float
    don_vi: str
    xu_huong: Optional[str] = "tang"
    han_hoan_thanh: Optional[date] = None
    thu_tu: Optional[int] = 1

class SuaKR(BaseModel):
    noi_dung: Optional[str] = None
    loai_kr: Optional[str] = None
    gia_tri_khoi_diem: Optional[float] = None
    gia_tri_muc_tieu: Optional[float] = None
    don_vi: Optional[str] = None
    xu_huong: Optional[str] = None
    han_hoan_thanh: Optional[date] = None

class CapNhatTienDoKR(BaseModel):
    gia_tri_hien_tai: float
    trang_thai_tu_danh_gia: Optional[str] = None
    tu_nhan_xet: Optional[str] = None

class NhanXetGVKR(BaseModel):
    nhan_xet_gv: str

def _tinh_tien_do(kr: dict, gia_tri_moi: float) -> float:
    kd = kr.get("gia_tri_khoi_diem", 0) or 0
    mt = kr.get("gia_tri_muc_tieu", 100) or 100
    xu = kr.get("xu_huong", "tang")
    if xu == "giam":
        if kd == mt:
            return 100.0
        if kd > mt:
            # Đúng hướng: khởi điểm cao hơn mục tiêu (VD: 100 → 20)
            td = (kd - gia_tri_moi) / (kd - mt) * 100
        else:
            # Setup không hợp lệ: khởi điểm thấp hơn mục tiêu
            return 100.0 if gia_tri_moi <= mt else 0.0
    else:
        if mt == kd:
            return 100.0
        td = (gia_tri_moi - kd) / (mt - kd) * 100
    return max(0.0, min(100.0, round(td, 1)))

def _cap_nhat_tien_do_tong(muc_tieu_id: str):
    """Tính lại tien_do_tong của Objective từ trung bình các KR"""
    krs = supabase.table("ket_qua_then_chot").select("tien_do_phan_tram").eq("muc_tieu_id", muc_tieu_id).execute()
    if krs.data:
        avg = sum(k["tien_do_phan_tram"] or 0 for k in krs.data) / len(krs.data)
        supabase.table("muc_tieu").update({"tien_do_tong": round(avg, 1)}).eq("id", muc_tieu_id).execute()

@router.get("/muc-tieu/{mt_id}")
def danh_sach_kr(mt_id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("ket_qua_then_chot").select("*").eq("muc_tieu_id", mt_id).order("thu_tu").execute()
    return res.data

@router.post("/muc-tieu/{mt_id}")
def them_kr(mt_id: str, body: TaoKR, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    kiem_tra_ky_mo_theo_muc_tieu(mt_id)
    # Kiểm tra quyền: chỉ HS sở hữu OKR mới được thêm KR
    mt = supabase.table("muc_tieu").select("*").eq("id", mt_id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")
    if nguoi_dung["vai_tro"] == "hoc_sinh" and mt.data[0]["hoc_sinh_id"] != nguoi_dung["id"]:
        raise HTTPException(status_code=403, detail="Khong co quyen")
    if mt.data[0]["trang_thai"] not in ["nhap", "yeu_cau_sua"]:
        raise HTTPException(status_code=400, detail="Chi duoc them KR khi OKR o trang thai nhap hoac can sua")

    # Đếm KR hiện tại (tối đa 5)
    count = supabase.table("ket_qua_then_chot").select("id").eq("muc_tieu_id", mt_id).execute()
    if len(count.data) >= 5:
        raise HTTPException(status_code=400, detail="Moi Objective chi duoc toi da 5 KR")

    data = {
        "muc_tieu_id": mt_id,
        "noi_dung": body.noi_dung,
        "loai_kr": body.loai_kr,
        "gia_tri_khoi_diem": body.gia_tri_khoi_diem or 0,
        "gia_tri_muc_tieu": body.gia_tri_muc_tieu,
        "gia_tri_hien_tai": body.gia_tri_khoi_diem or 0,
        "don_vi": body.don_vi,
        "xu_huong": body.xu_huong,
        "thu_tu": body.thu_tu,
        "nguoi_phu_trach_id": nguoi_dung["id"],
    }
    if body.han_hoan_thanh:
        data["han_hoan_thanh"] = body.han_hoan_thanh.isoformat()

    try:
        res = supabase.table("ket_qua_then_chot").insert(data).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loi tao KR: {str(e)[:150]}. Bang ket_qua_then_chot co the chua ton tai - vui long chay migration SQL.")

@router.put("/{kr_id}")
def sua_kr(kr_id: str, body: SuaKR, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    kr = supabase.table("ket_qua_then_chot").select("*, muc_tieu(hoc_sinh_id, trang_thai)").eq("id", kr_id).execute()
    if not kr.data:
        raise HTTPException(status_code=404, detail="Khong tim thay KR")
    mt = kr.data[0].get("muc_tieu", {})
    if nguoi_dung["vai_tro"] == "hoc_sinh":
        if mt.get("hoc_sinh_id") != nguoi_dung["id"]:
            raise HTTPException(status_code=403, detail="Khong co quyen")
        if mt.get("trang_thai") not in ["nhap", "yeu_cau_sua"]:
            raise HTTPException(status_code=400, detail="Chi sua KR khi OKR o trang thai nhap/can sua")

    update = {k: v for k, v in body.dict().items() if v is not None}
    if "han_hoan_thanh" in update and update["han_hoan_thanh"]:
        update["han_hoan_thanh"] = update["han_hoan_thanh"].isoformat()
    update["ngay_cap_nhat"] = datetime.now(timezone.utc).isoformat()
    res = supabase.table("ket_qua_then_chot").update(update).eq("id", kr_id).execute()
    return res.data[0]

@router.delete("/{kr_id}")
def xoa_kr(kr_id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    kr = supabase.table("ket_qua_then_chot").select("*, muc_tieu(hoc_sinh_id, trang_thai)").eq("id", kr_id).execute()
    if not kr.data:
        raise HTTPException(status_code=404, detail="Khong tim thay KR")
    mt = kr.data[0].get("muc_tieu", {})
    if nguoi_dung["vai_tro"] == "hoc_sinh":
        if mt.get("hoc_sinh_id") != nguoi_dung["id"]:
            raise HTTPException(status_code=403, detail="Khong co quyen")
        if mt.get("trang_thai") not in ["nhap", "yeu_cau_sua"]:
            raise HTTPException(status_code=400, detail="Chi xoa KR khi OKR o trang thai nhap/can sua")

    supabase.table("ket_qua_then_chot").delete().eq("id", kr_id).execute()
    return {"message": "Da xoa KR"}

@router.post("/{kr_id}/cap-nhat")
def cap_nhat_tien_do_kr(kr_id: str, body: CapNhatTienDoKR, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] != "hoc_sinh":
        raise HTTPException(status_code=403, detail="Chi hoc sinh moi duoc cap nhat")

    kr = supabase.table("ket_qua_then_chot").select("*, muc_tieu(hoc_sinh_id, trang_thai, ky_danh_gia_id)").eq("id", kr_id).execute()
    if not kr.data:
        raise HTTPException(status_code=404, detail="Khong tim thay KR")

    kr_data = kr.data[0]
    mt = kr_data.get("muc_tieu", {})
    from ky_helper import kiem_tra_ky_mo
    kiem_tra_ky_mo(mt.get("ky_danh_gia_id"))

    if mt.get("hoc_sinh_id") != nguoi_dung["id"]:
        raise HTTPException(status_code=403, detail="Khong co quyen")
    if mt.get("trang_thai") != "da_duyet":
        raise HTTPException(status_code=400, detail="OKR chua duoc duyet")

    tien_do = _tinh_tien_do(kr_data, body.gia_tri_hien_tai)

    # Cập nhật KR
    supabase.table("ket_qua_then_chot").update({
        "gia_tri_hien_tai": body.gia_tri_hien_tai,
        "tien_do_phan_tram": tien_do,
        "ngay_cap_nhat": datetime.now(timezone.utc).isoformat()
    }).eq("id", kr_id).execute()

    # Ghi lịch sử
    supabase.table("lich_su_cap_nhat").insert({
        "muc_tieu_id": kr_data["muc_tieu_id"],
        "kr_id": kr_id,
        "gia_tri_dat_duoc": body.gia_tri_hien_tai,
        "tien_do": tien_do,
        "trang_thai_tu_danh_gia": body.trang_thai_tu_danh_gia,
        "tu_nhan_xet": body.tu_nhan_xet,
        "ghi_chu": body.tu_nhan_xet
    }).execute()

    # Cập nhật tiến độ tổng
    _cap_nhat_tien_do_tong(kr_data["muc_tieu_id"])

    # Cập nhật trang_thai_tien_do trên muc_tieu nếu có
    if body.trang_thai_tu_danh_gia:
        supabase.table("muc_tieu").update({
            "trang_thai_tien_do": body.trang_thai_tu_danh_gia
        }).eq("id", kr_data["muc_tieu_id"]).execute()

    return {"message": "Cap nhat thanh cong", "tien_do": tien_do}

@router.put("/{kr_id}/nhan-xet")
def nhan_xet_gv_kr(kr_id: str, body: NhanXetGVKR, nguoi_dung=Depends(chi_giao_vien)):
    supabase.table("ket_qua_then_chot").update({"nhan_xet_gv": body.nhan_xet_gv}).eq("id", kr_id).execute()
    return {"message": "Da luu nhan xet"}
