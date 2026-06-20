from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import supabase
from auth import chi_quan_tri
import bcrypt

router = APIRouter()

# ── Models ──────────────────────────────────────────────
class TaoGiaoVien(BaseModel):
    ho_ten: str
    email: str
    mat_khau: str
    ten_lop: Optional[str] = None
    si_so: Optional[int] = None
    la_truong_khoi: Optional[bool] = False
    khoi_phu_trach: Optional[str] = None
    vai_tro: Optional[str] = "giao_vien"  # giao_vien | pho_hieu_truong
    gioi_tinh: Optional[str] = None  # nam | nu

class TaoHocSinh(BaseModel):
    ho_ten: str
    email: str
    mat_khau: str
    ten_lop: str
    email_phu_huynh: Optional[str] = None

class CapNhatNguoiDung(BaseModel):
    ho_ten: Optional[str] = None
    ten_lop: Optional[str] = None
    si_so: Optional[int] = None
    mat_khau: Optional[str] = None
    dang_hoat_dong: Optional[bool] = None
    la_truong_khoi: Optional[bool] = None
    khoi_phu_trach: Optional[str] = None
    gioi_tinh: Optional[str] = None

# ── Thống kê ────────────────────────────────────────────
@router.get("/thong-ke-tong-quan")
def thong_ke_tong_quan(ky_id: Optional[str] = None, nguoi_dung=Depends(chi_quan_tri)):
    gv_res = supabase.table("nguoi_dung").select("id, ho_ten, ten_lop, si_so").eq("vai_tro", "giao_vien").eq("dang_hoat_dong", True).execute()
    ket_qua = []

    for gv in gv_res.data:
        ten_lop = gv.get("ten_lop")
        if not ten_lop:
            continue

        hs_res = supabase.table("nguoi_dung").select("id").eq("ten_lop", ten_lop).eq("vai_tro", "hoc_sinh").eq("dang_hoat_dong", True).execute()
        hs_ids = [h["id"] for h in hs_res.data]
        so_hs = len(hs_ids)

        if not hs_ids:
            ket_qua.append({
                "ten_giao_vien": gv["ho_ten"],
                "ten_lop": ten_lop,
                "si_so": gv.get("si_so", 0),
                "so_hs_nop": 0,
                "so_hs_duoc_duyet": 0,
                "ti_le_hoan_thanh": 0
            })
            continue

        query = supabase.table("muc_tieu").select("hoc_sinh_id, trang_thai, tien_do_phan_tram").in_("hoc_sinh_id", hs_ids)
        if ky_id:
            query = query.eq("ky_danh_gia_id", ky_id)
        mt_res = query.execute()

        hs_nop = set(m["hoc_sinh_id"] for m in mt_res.data)
        hs_duoc_duyet = set(m["hoc_sinh_id"] for m in mt_res.data if m["trang_thai"] == "da_duyet")
        tien_do_all = [m["tien_do_phan_tram"] for m in mt_res.data if m["tien_do_phan_tram"] is not None]
        ti_le = round(sum(tien_do_all) / len(tien_do_all), 1) if tien_do_all else 0

        ket_qua.append({
            "ten_giao_vien": gv["ho_ten"],
            "ten_lop": ten_lop,
            "si_so": gv.get("si_so", so_hs),
            "so_hs_nop": len(hs_nop),
            "so_hs_duoc_duyet": len(hs_duoc_duyet),
            "ti_le_hoan_thanh": ti_le
        })

    return ket_qua

# ── Danh sách người dùng ────────────────────────────────
@router.get("/danh-sach-nguoi-dung")
def danh_sach_nguoi_dung(vai_tro: Optional[str] = None, nguoi_dung=Depends(chi_quan_tri)):
    query = supabase.table("nguoi_dung").select("id, ho_ten, email, vai_tro, ten_lop, si_so, email_phu_huynh, dang_hoat_dong, ngay_tao, la_truong_khoi, khoi_phu_trach, khoi")
    if vai_tro:
        query = query.eq("vai_tro", vai_tro)
    query = query.neq("vai_tro", "quan_tri").eq("dang_hoat_dong", True).order("ho_ten")
    res = query.execute()
    return res.data

# ── Tạo giáo viên ───────────────────────────────────────
@router.post("/tao-giao-vien")
def tao_giao_vien(body: TaoGiaoVien, nguoi_dung=Depends(chi_quan_tri)):
    # Kiểm tra email trùng
    kiem_tra = supabase.table("nguoi_dung").select("id").eq("email", body.email).execute()
    if kiem_tra.data:
        raise HTTPException(status_code=400, detail="Email nay da duoc su dung")

    vai_tro = body.vai_tro if body.vai_tro in ("giao_vien", "pho_hieu_truong") else "giao_vien"
    hash_pw = bcrypt.hashpw(body.mat_khau.encode(), bcrypt.gensalt()).decode()
    data = {
        "ho_ten": body.ho_ten,
        "email": body.email,
        "mat_khau_hash": hash_pw,
        "vai_tro": vai_tro,
        "dang_hoat_dong": True,
        "bat_buoc_doi_mat_khau": True,
    }
    if body.gioi_tinh in ("nam", "nu"):
        data["gioi_tinh"] = body.gioi_tinh
    if vai_tro == "giao_vien":
        if body.ten_lop: data["ten_lop"] = body.ten_lop
        if body.si_so: data["si_so"] = body.si_so
        data["la_truong_khoi"] = bool(body.la_truong_khoi)
        data["khoi_phu_trach"] = body.khoi_phu_trach if body.la_truong_khoi else None

    res = supabase.table("nguoi_dung").insert(data).execute()
    return res.data[0]

# ── Tạo học sinh ─────────────────────────────────────────
@router.post("/tao-hoc-sinh")
def tao_hoc_sinh(body: TaoHocSinh, nguoi_dung=Depends(chi_quan_tri)):
    kiem_tra = supabase.table("nguoi_dung").select("id").eq("email", body.email).execute()
    if kiem_tra.data:
        raise HTTPException(status_code=400, detail="Email nay da duoc su dung")

    hash_pw = bcrypt.hashpw(body.mat_khau.encode(), bcrypt.gensalt()).decode()
    data = {
        "ho_ten": body.ho_ten,
        "email": body.email,
        "mat_khau_hash": hash_pw,
        "vai_tro": "hoc_sinh",
        "ten_lop": body.ten_lop,
        "dang_hoat_dong": True,
        "bat_buoc_doi_mat_khau": True,
    }
    if body.email_phu_huynh: data["email_phu_huynh"] = body.email_phu_huynh

    res = supabase.table("nguoi_dung").insert(data).execute()
    return res.data[0]

# ── Cập nhật người dùng ──────────────────────────────────
@router.put("/cap-nhat-nguoi-dung/{id}")
def cap_nhat_nguoi_dung(id: str, body: CapNhatNguoiDung, nguoi_dung=Depends(chi_quan_tri)):
    data = {}
    if body.ho_ten: data["ho_ten"] = body.ho_ten
    if body.ten_lop is not None: data["ten_lop"] = body.ten_lop
    if body.si_so is not None: data["si_so"] = body.si_so
    if body.dang_hoat_dong is not None: data["dang_hoat_dong"] = body.dang_hoat_dong
    if body.la_truong_khoi is not None:
        data["la_truong_khoi"] = body.la_truong_khoi
        data["khoi_phu_trach"] = body.khoi_phu_trach if body.la_truong_khoi else None
    if body.gioi_tinh in ("nam", "nu"):
        data["gioi_tinh"] = body.gioi_tinh
    if body.mat_khau:
        data["mat_khau_hash"] = bcrypt.hashpw(body.mat_khau.encode(), bcrypt.gensalt()).decode()
        data["bat_buoc_doi_mat_khau"] = True
    if not data:
        raise HTTPException(status_code=400, detail="Khong co du lieu de cap nhat")
    res = supabase.table("nguoi_dung").update(data).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay nguoi dung")
    return res.data[0]

@router.patch("/cap-nhat-nguoi-dung/{id}")
def cap_nhat_nguoi_dung_patch(id: str, body: CapNhatNguoiDung, nguoi_dung=Depends(chi_quan_tri)):
    return cap_nhat_nguoi_dung(id, body, nguoi_dung)

# ── Nhật ký hoạt động ────────────────────────────────────
@router.get("/nhat-ky-hoat-dong")
def nhat_ky_hoat_dong(limit: int = 100, nguoi_dung=Depends(chi_quan_tri)):
    try:
        res = supabase.table("nhat_ky_hoat_dong").select("*, nguoi_dung:nguoi_dung_id(ho_ten, vai_tro, email)").order("thoi_diem", desc=True).limit(limit).execute()
        # Flatten dữ liệu
        data = []
        for item in res.data:
            nd = item.pop("nguoi_dung", None) or {}
            data.append({**item, "ho_ten": nd.get("ho_ten"), "vai_tro": nd.get("vai_tro"), "email": nd.get("email")})
        return data
    except Exception:
        return []

# Giữ endpoint cũ để tương thích
@router.get("/nhat-ky")
def xem_nhat_ky(nguoi_dung=Depends(chi_quan_tri)):
    return nhat_ky_hoat_dong(100, nguoi_dung)
