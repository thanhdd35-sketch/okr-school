from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, timezone
from database import supabase
from auth import lay_nguoi_dung_hien_tai, chi_giao_vien

router = APIRouter()

class TaoMucTieu(BaseModel):
    ky_danh_gia_id: str
    loai_okr: str
    muc_tieu_lon: str
    ket_qua_then_chot: str
    chi_tieu: float
    don_vi: str
    han_hoan_thanh: Optional[date] = None

class SuaMucTieu(BaseModel):
    muc_tieu_lon: Optional[str] = None
    ket_qua_then_chot: Optional[str] = None
    chi_tieu: Optional[float] = None
    don_vi: Optional[str] = None
    han_hoan_thanh: Optional[date] = None

class CapNhatTienDo(BaseModel):
    gia_tri_dat_duoc: float
    ghi_chu: Optional[str] = None

class NhanXetGiaoVien(BaseModel):
    nhan_xet: str

class ChamSao(BaseModel):
    diem: int

class YeuCauSua(BaseModel):
    ly_do: str

@router.get("/")
def danh_sach_muc_tieu(ky_id: Optional[str] = None, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    vai_tro = nguoi_dung.get("vai_tro")
    query = supabase.table("muc_tieu").select("*, ky_danh_gia(ten_ky), nguoi_dung:hoc_sinh_id(ho_ten, ten_lop)")

    if vai_tro == "hoc_sinh":
        query = query.eq("hoc_sinh_id", nguoi_dung["id"])
    elif vai_tro == "phu_huynh":
        query = query.eq("hoc_sinh_id", nguoi_dung.get("hoc_sinh_id"))

    if ky_id:
        query = query.eq("ky_danh_gia_id", ky_id)

    res = query.order("ngay_tao", desc=True).execute()
    return res.data

@router.post("/")
def tao_muc_tieu(body: TaoMucTieu, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung.get("vai_tro") != "hoc_sinh":
        raise HTTPException(status_code=403, detail="Chi hoc sinh moi duoc tao muc tieu")

    ky = supabase.table("ky_danh_gia").select("*").eq("id", body.ky_danh_gia_id).execute()
    if not ky.data or ky.data[0]["trang_thai"] != "mo":
        raise HTTPException(status_code=400, detail="Ky danh gia khong ton tai hoac da bi khoa")

    data = {
        "hoc_sinh_id": nguoi_dung["id"],
        "ky_danh_gia_id": body.ky_danh_gia_id,
        "loai_okr": body.loai_okr,
        "muc_tieu_lon": body.muc_tieu_lon,
        "ket_qua_then_chot": body.ket_qua_then_chot,
        "chi_tieu": body.chi_tieu,
        "don_vi": body.don_vi,
        "trang_thai": "cho_duyet"
    }
    if body.han_hoan_thanh:
        data["han_hoan_thanh"] = body.han_hoan_thanh.isoformat()

    res = supabase.table("muc_tieu").insert(data).execute()
    return res.data[0]

@router.put("/{id}")
def sua_muc_tieu(id: str, body: SuaMucTieu, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    mt = supabase.table("muc_tieu").select("*").eq("id", id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")

    muc_tieu = mt.data[0]
    if nguoi_dung["vai_tro"] == "hoc_sinh":
        if muc_tieu["hoc_sinh_id"] != nguoi_dung["id"]:
            raise HTTPException(status_code=403, detail="Khong co quyen sua muc tieu nay")
        if muc_tieu["trang_thai"] not in ["cho_duyet", "yeu_cau_sua"]:
            raise HTTPException(status_code=400, detail="Chi duoc sua khi trang thai la cho duyet hoac can sua")

    update = {k: v for k, v in body.dict().items() if v is not None}
    if "han_hoan_thanh" in update and update["han_hoan_thanh"]:
        update["han_hoan_thanh"] = update["han_hoan_thanh"].isoformat()

    res = supabase.table("muc_tieu").update(update).eq("id", id).execute()
    return res.data[0]

@router.post("/{id}/cap-nhat-tien-do")
def cap_nhat_tien_do(id: str, body: CapNhatTienDo, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] != "hoc_sinh":
        raise HTTPException(status_code=403, detail="Chi hoc sinh moi duoc cap nhat tien do")

    mt = supabase.table("muc_tieu").select("*").eq("id", id).eq("hoc_sinh_id", nguoi_dung["id"]).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")

    muc_tieu = mt.data[0]
    if muc_tieu["trang_thai"] != "da_duyet":
        raise HTTPException(status_code=400, detail="Muc tieu chua duoc duyet")

    ky = supabase.table("ky_danh_gia").select("*").eq("id", muc_tieu["ky_danh_gia_id"]).execute()
    if not ky.data or ky.data[0]["trang_thai"] == "khoa":
        raise HTTPException(status_code=400, detail="Ky danh gia da bi khoa")

    danh_gia = supabase.table("danh_gia_cuoi_ky").select("*").eq("hoc_sinh_id", nguoi_dung["id"]).eq("ky_danh_gia_id", muc_tieu["ky_danh_gia_id"]).execute()
    if danh_gia.data and danh_gia.data[0]["trang_thai"] == "hoan_tat":
        raise HTTPException(status_code=400, detail="Danh gia cuoi ky da hoan tat, khong the cap nhat them")

    hom_nay = datetime.now(timezone.utc).date().isoformat()
    lich_su_hom_nay = supabase.table("lich_su_cap_nhat").select("id").eq("muc_tieu_id", id).gte("thoi_diem", f"{hom_nay}T00:00:00").execute()
    if lich_su_hom_nay.data:
        raise HTTPException(status_code=400, detail="Ban da cap nhat tien do hom nay roi")

    tien_do = round((body.gia_tri_dat_duoc / muc_tieu["chi_tieu"]) * 100, 1)

    data = {
        "muc_tieu_id": id,
        "gia_tri_dat_duoc": body.gia_tri_dat_duoc,
        "tien_do": tien_do,
        "ghi_chu": body.ghi_chu
    }
    supabase.table("lich_su_cap_nhat").insert(data).execute()
    return {"message": "Cap nhat thanh cong", "tien_do": tien_do}

@router.post("/{id}/duyet")
def duyet_muc_tieu(id: str, nguoi_dung=Depends(chi_giao_vien)):
    mt = supabase.table("muc_tieu").select("*").eq("id", id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")

    supabase.table("muc_tieu").update({"trang_thai": "da_duyet"}).eq("id", id).execute()

    hoc_sinh = supabase.table("nguoi_dung").select("email, ho_ten").eq("id", mt.data[0]["hoc_sinh_id"]).execute()
    if hoc_sinh.data:
        from email_service import gui_email_duyet_muc_tieu
        gui_email_duyet_muc_tieu(hoc_sinh.data[0]["email"], hoc_sinh.data[0]["ho_ten"], mt.data[0]["muc_tieu_lon"])

    supabase.table("thong_bao").insert({
        "nguoi_nhan": mt.data[0]["hoc_sinh_id"],
        "loai": "duyet_muc_tieu",
        "tieu_de": "Muc tieu da duoc duyet",
        "noi_dung": f"Muc tieu '{mt.data[0]['muc_tieu_lon']}' cua ban da duoc giao vien duyet"
    }).execute()

    return {"message": "Duyet muc tieu thanh cong"}

@router.post("/{id}/yeu-cau-sua")
def yeu_cau_sua(id: str, body: YeuCauSua, nguoi_dung=Depends(chi_giao_vien)):
    mt = supabase.table("muc_tieu").select("*").eq("id", id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")

    supabase.table("muc_tieu").update({
        "trang_thai": "yeu_cau_sua",
        "nhan_xet_giao_vien": body.ly_do
    }).eq("id", id).execute()

    hoc_sinh = supabase.table("nguoi_dung").select("email, ho_ten").eq("id", mt.data[0]["hoc_sinh_id"]).execute()
    if hoc_sinh.data:
        from email_service import gui_email_yeu_cau_sua
        gui_email_yeu_cau_sua(hoc_sinh.data[0]["email"], hoc_sinh.data[0]["ho_ten"], mt.data[0]["muc_tieu_lon"], body.ly_do)

    supabase.table("thong_bao").insert({
        "nguoi_nhan": mt.data[0]["hoc_sinh_id"],
        "loai": "yeu_cau_sua",
        "tieu_de": "Muc tieu can chinh sua",
        "noi_dung": f"Muc tieu '{mt.data[0]['muc_tieu_lon']}' can chinh sua: {body.ly_do}"
    }).execute()

    return {"message": "Da yeu cau chinh sua"}

@router.post("/{id}/xin-xoa")
def xin_xoa(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] != "hoc_sinh":
        raise HTTPException(status_code=403, detail="Chi hoc sinh moi duoc gui yeu cau xoa")

    mt = supabase.table("muc_tieu").select("*").eq("id", id).eq("hoc_sinh_id", nguoi_dung["id"]).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")

    supabase.table("muc_tieu").update({"trang_thai": "xin_xoa"}).eq("id", id).execute()
    return {"message": "Da gui yeu cau xoa, cho giao vien xac nhan"}

@router.post("/{id}/dong-y-xoa")
def dong_y_xoa(id: str, nguoi_dung=Depends(chi_giao_vien)):
    mt = supabase.table("muc_tieu").select("*").eq("id", id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")

    supabase.table("muc_tieu").delete().eq("id", id).execute()
    return {"message": "Da xoa muc tieu thanh cong"}

@router.put("/{id}/danh-gia")
def cham_sao(id: str, body: ChamSao, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] != "phu_huynh":
        raise HTTPException(status_code=403, detail="Chi phu huynh moi duoc cham sao")
    if body.diem < 1 or body.diem > 5:
        raise HTTPException(status_code=400, detail="Diem phai tu 1 den 5 sao")

    supabase.table("muc_tieu").update({"diem_phu_huynh": body.diem}).eq("id", id).execute()
    return {"message": "Da cham sao thanh cong"}

@router.get("/{id}/lich-su")
def lich_su(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("lich_su_cap_nhat").select("*").eq("muc_tieu_id", id).order("thoi_diem").execute()
    return res.data

@router.get("/theo-lop/{ten_lop}")
def muc_tieu_theo_lop(ten_lop: str, ky_id: Optional[str] = None, nguoi_dung=Depends(chi_giao_vien)):
    hs_res = supabase.table("nguoi_dung").select("id").eq("ten_lop", ten_lop).eq("vai_tro", "hoc_sinh").execute()
    hs_ids = [h["id"] for h in hs_res.data]

    if not hs_ids:
        return []

    query = supabase.table("muc_tieu").select("*, nguoi_dung:hoc_sinh_id(ho_ten, ten_lop)").in_("hoc_sinh_id", hs_ids)
    if ky_id:
        query = query.eq("ky_danh_gia_id", ky_id)

    res = query.order("ngay_tao", desc=True).execute()
    return res.data

@router.put("/{id}/nhan-xet")
def cap_nhat_nhan_xet(id: str, body: NhanXetGiaoVien, nguoi_dung=Depends(chi_giao_vien)):
    supabase.table("muc_tieu").update({"nhan_xet_giao_vien": body.nhan_xet}).eq("id", id).execute()
    return {"message": "Da luu nhan xet"}
