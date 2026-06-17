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

    # Phat hien dinh dang: neu cot dau la so thi co cot STT
    # Format moi: STT | Ho ten | Email | Email PH | Lop
    # Format cu:  Ho ten | Email | Email PH | Lop
    headers = [str(c.value).strip().lower() if c.value else "" for c in ws[1]]
    has_stt = headers and (headers[0] in ("stt", "số thứ tự", "so thu tu", "tt") or
                           (ws.cell(2, 1).value is not None and str(ws.cell(2, 1).value).strip().lstrip("0123456789.") == ""))

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or all(v is None or str(v).strip() == "" for v in row):
            continue
        try:
            if has_stt:
                stt_val = row[0]
                stt = int(float(str(stt_val))) if stt_val is not None else i - 1
                ho_ten = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                email = str(row[2]).strip() if len(row) > 2 and row[2] else ""
                email_ph = str(row[3]).strip() if len(row) > 3 and row[3] and str(row[3]).strip() != "None" else None
                lop = str(row[4]).strip() if len(row) > 4 and row[4] else ten_lop_mac_dinh
            else:
                stt = i - 1
                ho_ten = str(row[0]).strip() if row[0] else ""
                email = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                email_ph = str(row[2]).strip() if len(row) > 2 and row[2] and str(row[2]).strip() != "None" else None
                lop = str(row[3]).strip() if len(row) > 3 and row[3] else ten_lop_mac_dinh

            if not ho_ten:
                loi.append(f"Dong {i}: Thieu ho ten")
                continue
            if not email or "@" not in email:
                loi.append(f"Dong {i}: Email khong hop le: '{email}'")
                continue
            if not lop:
                loi.append(f"Dong {i}: Khong xac dinh duoc lop (GV chua duoc phan lop)")
                continue

            kiem_tra = supabase.table("nguoi_dung").select("id").eq("email", email).execute()
            if kiem_tra.data:
                loi.append(f"Dong {i}: Email '{email}' da ton tai")
                continue

            supabase.table("nguoi_dung").insert({
                "ho_ten": ho_ten,
                "email": email,
                "email_phu_huynh": email_ph,
                "ten_lop": lop,
                "vai_tro": vai_tro,
                "so_thu_tu": stt,
                "mat_khau_hash": hash_mat_khau(MAT_KHAU_MAC_DINH),
                "bat_buoc_doi_mat_khau": True,
                "dang_hoat_dong": True
            }).execute()
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
