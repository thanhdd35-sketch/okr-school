from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import openpyxl
import io
from database import supabase
from auth import hash_mat_khau, lay_nguoi_dung_hien_tai, chi_giao_vien, chi_quan_tri

router = APIRouter()

MAT_KHAU_MAC_DINH = "Okr@12345"

class ThemHocSinh(BaseModel):
    ho_ten: str
    email: str
    email_phu_huynh: Optional[str] = None
    ten_lop: str

class ThemGiaoVien(BaseModel):
    ho_ten: str
    email: str
    ten_lop: str
    si_so: Optional[int] = None

@router.get("/hoc-sinh/{ten_lop}")
def danh_sach_hoc_sinh(ten_lop: str, nguoi_dung=Depends(chi_giao_vien)):
    res = supabase.table("nguoi_dung").select("id, ho_ten, email, email_phu_huynh, dang_hoat_dong, ngay_tao").eq("ten_lop", ten_lop).eq("vai_tro", "hoc_sinh").eq("dang_hoat_dong", True).order("ho_ten").execute()
    return res.data

@router.post("/hoc-sinh")
def them_hoc_sinh(body: ThemHocSinh, nguoi_dung=Depends(chi_giao_vien)):
    kiem_tra = supabase.table("nguoi_dung").select("id").eq("email", body.email).execute()
    if kiem_tra.data:
        raise HTTPException(status_code=400, detail="Email nay da ton tai trong he thong")

    data = {
        "ho_ten": body.ho_ten,
        "email": body.email,
        "email_phu_huynh": body.email_phu_huynh,
        "ten_lop": body.ten_lop,
        "vai_tro": "hoc_sinh",
        "mat_khau_hash": hash_mat_khau(MAT_KHAU_MAC_DINH),
        "bat_buoc_doi_mat_khau": True
    }
    res = supabase.table("nguoi_dung").insert(data).execute()
    return {"message": "Tao hoc sinh thanh cong", "id": res.data[0]["id"]}

@router.post("/giao-vien")
def them_giao_vien(body: ThemGiaoVien, nguoi_dung=Depends(chi_quan_tri)):
    kiem_tra = supabase.table("nguoi_dung").select("id").eq("email", body.email).execute()
    if kiem_tra.data:
        raise HTTPException(status_code=400, detail="Email nay da ton tai trong he thong")

    data = {
        "ho_ten": body.ho_ten,
        "email": body.email,
        "ten_lop": body.ten_lop,
        "si_so": body.si_so,
        "vai_tro": "giao_vien",
        "mat_khau_hash": hash_mat_khau(MAT_KHAU_MAC_DINH),
        "bat_buoc_doi_mat_khau": True
    }
    res = supabase.table("nguoi_dung").insert(data).execute()
    return {"message": "Tao giao vien thanh cong", "id": res.data[0]["id"]}

@router.post("/nhap-danh-sach")
async def nhap_danh_sach(vai_tro: str, ten_lop: Optional[str] = None, file: UploadFile = File(...), nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] not in ["quan_tri", "giao_vien"]:
        raise HTTPException(status_code=403, detail="Khong co quyen")

    # Neu frontend khong gui ten_lop, lay tu JWT cua giao vien
    ten_lop_mac_dinh = ten_lop or nguoi_dung.get("ten_lop") or ""

    noi_dung = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(noi_dung))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File Excel khong hop le: {str(e)}")
    ws = wb.active

    thanh_cong = 0
    loi = []

    # Phat hien co cot STT o dau khong (header row 1)
    headers = [str(c.value).strip().lower() if c.value else "" for c in ws[1]]
    has_stt = bool(headers) and (headers[0] in ("stt", "số thứ tự", "so thu tu", "tt") or
                                  (ws.cell(2, 1).value is not None and
                                   str(ws.cell(2, 1).value).strip().lstrip("0123456789.") == ""))

    # Format GV: STT | Ho ten | Email | Lop CN | Si so
    # Format HS: STT | Ho ten | Email HS | Email PH | Lop
    # (khi khong co STT, dich trai 1 cot)

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or all(v is None or str(v).strip() == "" for v in row):
            continue
        try:
            offset = 1 if has_stt else 0
            stt_val = row[0] if has_stt else None
            stt = int(float(str(stt_val))) if stt_val is not None else i - 1

            def _s(idx: int) -> str:
                return str(row[offset + idx]).strip() if len(row) > offset + idx and row[offset + idx] else ""

            ho_ten = _s(0)
            email = _s(1)

            if vai_tro == "giao_vien":
                lop = _s(2) or ten_lop_mac_dinh
                si_so_str = _s(3)
                si_so = int(float(si_so_str)) if si_so_str else None
                email_ph = None
            else:
                email_ph = _s(2) or None
                if email_ph == "None": email_ph = None
                lop = _s(3) or ten_lop_mac_dinh
                si_so = None

            if not ho_ten:
                loi.append(f"Dong {i}: Thieu ho ten")
                continue
            if not email or "@" not in email:
                loi.append(f"Dong {i}: Email khong hop le: '{email}'")
                continue
            if vai_tro != "giao_vien" and not lop:
                loi.append(f"Dong {i}: Khong xac dinh duoc lop (GV chua duoc phan lop)")
                continue

            kiem_tra = supabase.table("nguoi_dung").select("id").eq("email", email).execute()
            if kiem_tra.data:
                loi.append(f"Dong {i}: Email '{email}' da ton tai")
                continue

            record: dict = {
                "ho_ten": ho_ten,
                "email": email,
                "email_phu_huynh": email_ph,
                "ten_lop": lop or None,
                "vai_tro": vai_tro,
                "so_thu_tu": stt,
                "mat_khau_hash": hash_mat_khau(MAT_KHAU_MAC_DINH),
                "bat_buoc_doi_mat_khau": True,
                "dang_hoat_dong": True,
            }
            if si_so is not None:
                record["si_so"] = si_so
            supabase.table("nguoi_dung").insert(record).execute()
            thanh_cong += 1
        except Exception as e:
            loi.append(f"Dong {i}: {str(e)[:120]}")

    return {"thanh_cong": thanh_cong, "loi": loi, "tong": thanh_cong + len(loi)}

class CapNhatHocSinh(BaseModel):
    ho_ten: Optional[str] = None
    email: Optional[str] = None

@router.put("/hoc-sinh/{id}")
def cap_nhat_hoc_sinh(id: str, body: CapNhatHocSinh, nguoi_dung=Depends(chi_giao_vien)):
    data = {}
    if body.ho_ten: data["ho_ten"] = body.ho_ten
    if body.email: data["email"] = body.email
    if not data:
        raise HTTPException(status_code=400, detail="Khong co du lieu de cap nhat")
    res = supabase.table("nguoi_dung").update(data).eq("id", id).eq("vai_tro", "hoc_sinh").execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay hoc sinh")
    return res.data[0]

@router.put("/{id}/reset-mat-khau")
def reset_mat_khau(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] not in ["quan_tri", "giao_vien"]:
        raise HTTPException(status_code=403, detail="Khong co quyen")

    supabase.table("nguoi_dung").update({
        "mat_khau_hash": hash_mat_khau(MAT_KHAU_MAC_DINH),
        "bat_buoc_doi_mat_khau": True
    }).eq("id", id).execute()

    return {"message": f"Da reset mat khau ve mac dinh: {MAT_KHAU_MAC_DINH}"}

@router.delete("/{id}")
def vo_hieu_hoa(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] not in ["quan_tri", "giao_vien"]:
        raise HTTPException(status_code=403, detail="Khong co quyen")

    supabase.table("nguoi_dung").update({"dang_hoat_dong": False}).eq("id", id).execute()
    return {"message": "Da vo hieu hoa tai khoan"}
