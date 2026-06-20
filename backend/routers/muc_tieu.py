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
    tan_suat: Optional[str] = "hang_thang"
    nhan: Optional[str] = None
    cau_chuyen: Optional[str] = None
    han_hoan_thanh: Optional[date] = None
    la_nhap: Optional[bool] = True
    tro_ngai_du_doan: Optional[str] = None
    ke_hoach_vuot_qua: Optional[str] = None

class SuaMucTieu(BaseModel):
    muc_tieu_lon: Optional[str] = None
    tan_suat: Optional[str] = None
    nhan: Optional[str] = None
    cau_chuyen: Optional[str] = None
    han_hoan_thanh: Optional[date] = None
    loai_okr: Optional[str] = None
    tro_ngai_du_doan: Optional[str] = None
    ke_hoach_vuot_qua: Optional[str] = None

class NopOKR(BaseModel):
    ket_qua_checklist_hs: Optional[dict] = None

class DuyetOKR(BaseModel):
    tieu_chi_1: Optional[int] = None
    tieu_chi_2: Optional[int] = None
    tieu_chi_3: Optional[int] = None
    tieu_chi_4: Optional[int] = None
    nhan_xet: Optional[str] = None

class TuChoiOKR(BaseModel):
    tieu_chi_1: Optional[int] = None
    tieu_chi_2: Optional[int] = None
    tieu_chi_3: Optional[int] = None
    tieu_chi_4: Optional[int] = None
    ly_do: str

class NhanXetGiaoVien(BaseModel):
    nhan_xet: str

class HoanThanhOKR(BaseModel):
    trang_thai_tu_danh_gia: Optional[str] = None
    tu_nhan_xet: Optional[str] = None

@router.get("/")
def danh_sach_muc_tieu(ky_id: Optional[str] = None, hoc_sinh_id: Optional[str] = None,
                        bao_gom_nhap: Optional[bool] = False,
                        nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    vai_tro = nguoi_dung.get("vai_tro")
    query = supabase.table("muc_tieu").select("*, ky_danh_gia(ten_ky), nguoi_dung:hoc_sinh_id(ho_ten, ten_lop)")

    if vai_tro == "hoc_sinh":
        query = query.eq("hoc_sinh_id", nguoi_dung["id"])
    elif vai_tro == "phu_huynh":
        query = query.eq("hoc_sinh_id", nguoi_dung.get("hoc_sinh_id"))
        query = query.neq("trang_thai", "nhap")
    elif hoc_sinh_id:
        query = query.eq("hoc_sinh_id", hoc_sinh_id)
        if not bao_gom_nhap:
            query = query.neq("trang_thai", "nhap")

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

    trang_thai = "nhap" if body.la_nhap else "cho_duyet"
    # Chỉ gửi các cột cơ bản - cột mới dùng DEFAULT nếu migration đã chạy
    data = {
        "hoc_sinh_id": nguoi_dung["id"],
        "ky_danh_gia_id": body.ky_danh_gia_id,
        "loai_okr": body.loai_okr,
        "muc_tieu_lon": body.muc_tieu_lon,
        "trang_thai": trang_thai,
    }
    # Thêm cột mới (chỉ có sau migration v2.2)
    optional_fields = {}
    if body.tan_suat:
        optional_fields["tan_suat"] = body.tan_suat
    if body.nhan:
        optional_fields["nhan"] = body.nhan
    if body.cau_chuyen:
        optional_fields["cau_chuyen"] = body.cau_chuyen
    if body.han_hoan_thanh:
        optional_fields["han_hoan_thanh"] = body.han_hoan_thanh.isoformat()
    if body.tro_ngai_du_doan:
        optional_fields["tro_ngai_du_doan"] = body.tro_ngai_du_doan
    if body.ke_hoach_vuot_qua:
        optional_fields["ke_hoach_vuot_qua"] = body.ke_hoach_vuot_qua

    try:
        res = supabase.table("muc_tieu").insert({**data, **optional_fields}).execute()
        return res.data[0]
    except Exception as e:
        err_str = str(e)
        # Nếu lỗi do cột mới chưa tồn tại, thử lại với dữ liệu tối thiểu
        if "400" in err_str or "column" in err_str.lower() or "constraint" in err_str.lower():
            try:
                res2 = supabase.table("muc_tieu").insert(data).execute()
                return res2.data[0]
            except Exception as e2:
                raise HTTPException(status_code=500, detail=f"Loi tao OKR: {str(e2)[:200]}. Vui long chay migration SQL trong Supabase.")
        raise HTTPException(status_code=500, detail=f"Loi tao OKR: {err_str[:200]}")

@router.put("/{id}")
def sua_muc_tieu(id: str, body: SuaMucTieu, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    mt = supabase.table("muc_tieu").select("*").eq("id", id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")
    muc_tieu = mt.data[0]
    if nguoi_dung["vai_tro"] == "hoc_sinh":
        if muc_tieu["hoc_sinh_id"] != nguoi_dung["id"]:
            raise HTTPException(status_code=403, detail="Khong co quyen")
        if muc_tieu["trang_thai"] not in ["nhap", "yeu_cau_sua"]:
            raise HTTPException(status_code=400, detail="Chi sua khi trang thai la nhap hoac can sua")
    update = {k: v for k, v in body.dict().items() if v is not None}
    if "han_hoan_thanh" in update and update["han_hoan_thanh"]:
        update["han_hoan_thanh"] = update["han_hoan_thanh"].isoformat()
    update["ngay_cap_nhat"] = datetime.now(timezone.utc).isoformat()
    res = supabase.table("muc_tieu").update(update).eq("id", id).execute()
    return res.data[0]

@router.post("/{id}/nop")
def nop_okr(id: str, body: NopOKR, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] != "hoc_sinh":
        raise HTTPException(status_code=403, detail="Chi hoc sinh")
    mt = supabase.table("muc_tieu").select("*").eq("id", id).eq("hoc_sinh_id", nguoi_dung["id"]).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay")
    if mt.data[0]["trang_thai"] not in ["nhap", "yeu_cau_sua"]:
        raise HTTPException(status_code=400, detail="Chi nop khi o trang thai nhap hoac can sua")
    try:
        krs = supabase.table("ket_qua_then_chot").select("id").eq("muc_tieu_id", id).execute()
        if not krs.data:
            raise HTTPException(status_code=400, detail="OKR chua co Ket qua then chot (KR). Vui long them it nhat 1 KR truoc khi nop.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loi kiem tra KR: {str(e)[:100]}. Vui long chay lai migration SQL trong Supabase.")
    update = {"trang_thai": "cho_duyet", "ngay_cap_nhat": datetime.now(timezone.utc).isoformat()}
    if body.ket_qua_checklist_hs:
        update["ket_qua_checklist_hs"] = body.ket_qua_checklist_hs
    supabase.table("muc_tieu").update(update).eq("id", id).execute()
    return {"message": "Da nop OKR thanh cong"}

@router.delete("/{id}")
def xoa_muc_tieu(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    mt = supabase.table("muc_tieu").select("*").eq("id", id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay")
    muc_tieu = mt.data[0]
    vt = nguoi_dung["vai_tro"]
    # Pho HT / Quan tri: xoa truc tiep khong can thong qua ai
    if vt in ("pho_hieu_truong", "quan_tri"):
        supabase.table("muc_tieu").delete().eq("id", id).execute()
        return {"message": "Da xoa"}
    if vt == "hoc_sinh":
        if muc_tieu["hoc_sinh_id"] != nguoi_dung["id"]:
            raise HTTPException(status_code=403, detail="Khong co quyen")
        if muc_tieu["trang_thai"] not in ["nhap", "yeu_cau_sua"]:
            raise HTTPException(status_code=400, detail="Chi xoa ban nhap. OKR da nop can xin xoa.")
    supabase.table("muc_tieu").delete().eq("id", id).execute()
    return {"message": "Da xoa"}

class DanhGiaPH(BaseModel):
    diem: Optional[int] = None
    binh_luan: Optional[str] = None

@router.put("/{id}/danh-gia")
def phu_huynh_danh_gia(id: str, body: DanhGiaPH, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung.get("vai_tro") != "phu_huynh":
        raise HTTPException(status_code=403, detail="Chi phu huynh moi danh gia")
    data = {}
    if body.diem is not None:
        data["diem_phu_huynh"] = body.diem
    if body.binh_luan is not None:
        data["binh_luan_phu_huynh"] = body.binh_luan
    if not data:
        raise HTTPException(status_code=400, detail="Khong co du lieu")
    try:
        res = supabase.table("muc_tieu").update(data).eq("id", id).execute()
    except Exception:
        # Neu cot binh_luan_phu_huynh chua ton tai (chua chay migration v2.4)
        if "diem_phu_huynh" in data:
            res = supabase.table("muc_tieu").update({"diem_phu_huynh": data["diem_phu_huynh"]}).eq("id", id).execute()
        else:
            raise HTTPException(status_code=500, detail="Chua chay migration v2.4")
    if not res.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")
    return res.data[0]

@router.post("/{id}/xin-xoa")
def xin_xoa(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] != "hoc_sinh":
        raise HTTPException(status_code=403, detail="Chi hoc sinh")
    mt = supabase.table("muc_tieu").select("*").eq("id", id).eq("hoc_sinh_id", nguoi_dung["id"]).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay")
    supabase.table("muc_tieu").update({"trang_thai": "xin_xoa"}).eq("id", id).execute()
    return {"message": "Da gui yeu cau xoa"}

@router.post("/{id}/dong-y-xoa")
def dong_y_xoa(id: str, nguoi_dung=Depends(chi_giao_vien)):
    supabase.table("muc_tieu").delete().eq("id", id).execute()
    return {"message": "Da xoa"}

@router.post("/{id}/duyet")
def duyet_muc_tieu(id: str, body: Optional[DuyetOKR] = None, nguoi_dung=Depends(chi_giao_vien)):
    if body is None:
        body = DuyetOKR()
    mt = supabase.table("muc_tieu").select("*").eq("id", id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay")
    if mt.data[0]["trang_thai"] != "cho_duyet":
        raise HTTPException(status_code=400, detail="OKR khong o trang thai cho duyet")
    supabase.table("muc_tieu").update({
        "trang_thai": "da_duyet", "nhan_xet_giao_vien": body.nhan_xet,
        "ngay_cap_nhat": datetime.now(timezone.utc).isoformat()
    }).eq("id", id).execute()
    checklist = {k: v for k, v in {
        "tieu_chi_1": body.tieu_chi_1, "tieu_chi_2": body.tieu_chi_2,
        "tieu_chi_3": body.tieu_chi_3, "tieu_chi_4": body.tieu_chi_4,
    }.items() if v is not None}
    if checklist:
        try:
            supabase.table("ket_qua_phe_duyet").insert({
                "muc_tieu_id": id, "giao_vien_id": nguoi_dung["id"],
                "ket_qua": "chap_thuan", "nhan_xet_phe_duyet": body.nhan_xet, **checklist
            }).execute()
        except Exception:
            pass
    hoc_sinh = supabase.table("nguoi_dung").select("email, ho_ten").eq("id", mt.data[0]["hoc_sinh_id"]).execute()
    if hoc_sinh.data:
        try:
            from email_service import gui_email_duyet_muc_tieu
            gui_email_duyet_muc_tieu(hoc_sinh.data[0]["email"], hoc_sinh.data[0]["ho_ten"], mt.data[0]["muc_tieu_lon"])
        except: pass
    supabase.table("thong_bao").insert({
        "nguoi_nhan": mt.data[0]["hoc_sinh_id"], "loai": "duyet_muc_tieu",
        "tieu_de": "Muc tieu da duoc duyet", "noi_dung": "Muc tieu da duoc giao vien duyet"
    }).execute()
    return {"message": "Duyet thanh cong"}

@router.post("/{id}/yeu-cau-sua")
def yeu_cau_sua(id: str, body: TuChoiOKR, nguoi_dung=Depends(chi_giao_vien)):
    mt = supabase.table("muc_tieu").select("*").eq("id", id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay")
    supabase.table("muc_tieu").update({
        "trang_thai": "yeu_cau_sua", "nhan_xet_giao_vien": body.ly_do,
        "ngay_cap_nhat": datetime.now(timezone.utc).isoformat()
    }).eq("id", id).execute()
    checklist = {k: v for k, v in {
        "tieu_chi_1": body.tieu_chi_1, "tieu_chi_2": body.tieu_chi_2,
        "tieu_chi_3": body.tieu_chi_3, "tieu_chi_4": body.tieu_chi_4,
    }.items() if v is not None}
    if checklist:
        supabase.table("ket_qua_phe_duyet").insert({
            "muc_tieu_id": id, "giao_vien_id": nguoi_dung["id"],
            "ket_qua": "tu_choi", "nhan_xet_phe_duyet": body.ly_do, **checklist
        }).execute()
    hoc_sinh = supabase.table("nguoi_dung").select("email, ho_ten").eq("id", mt.data[0]["hoc_sinh_id"]).execute()
    if hoc_sinh.data:
        try:
            from email_service import gui_email_yeu_cau_sua
            gui_email_yeu_cau_sua(hoc_sinh.data[0]["email"], hoc_sinh.data[0]["ho_ten"], mt.data[0]["muc_tieu_lon"], body.ly_do)
        except: pass
    supabase.table("thong_bao").insert({
        "nguoi_nhan": mt.data[0]["hoc_sinh_id"], "loai": "yeu_cau_sua",
        "tieu_de": "Muc tieu can chinh sua", "noi_dung": f"Can chinh sua: {body.ly_do}"
    }).execute()
    return {"message": "Da yeu cau chinh sua"}

@router.post("/{id}/huy-duyet")
def huy_duyet(id: str, nguoi_dung=Depends(chi_giao_vien)):
    mt = supabase.table("muc_tieu").select("*").eq("id", id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay")
    if mt.data[0]["trang_thai"] != "da_duyet":
        raise HTTPException(status_code=400, detail="OKR chua duoc duyet")
    lich_su = supabase.table("lich_su_cap_nhat").select("id").eq("muc_tieu_id", id).execute()
    if lich_su.data:
        raise HTTPException(status_code=400, detail="Khong the huy duyet khi hoc sinh da cap nhat tien do")
    supabase.table("muc_tieu").update({
        "trang_thai": "cho_duyet",
        "ngay_cap_nhat": datetime.now(timezone.utc).isoformat()
    }).eq("id", id).execute()
    supabase.table("thong_bao").insert({
        "nguoi_nhan": mt.data[0]["hoc_sinh_id"], "loai": "huy_duyet",
        "tieu_de": "OKR bi thu hoi phe duyet",
        "noi_dung": "Giao vien da thu hoi phe duyet. Vui long chinh sua va nop lai."
    }).execute()
    return {"message": "Da thu hoi phe duyet"}

@router.post("/{id}/nhan-ban")
def nhan_ban(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] != "hoc_sinh":
        raise HTTPException(status_code=403, detail="Chi hoc sinh")
    mt = supabase.table("muc_tieu").select("*").eq("id", id).eq("hoc_sinh_id", nguoi_dung["id"]).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay")
    if mt.data[0]["trang_thai"] != "yeu_cau_sua":
        raise HTTPException(status_code=400, detail="Chi nhan ban OKR can sua")
    old = mt.data[0]
    new_data = {k: v for k, v in {
        "hoc_sinh_id": nguoi_dung["id"],
        "ky_danh_gia_id": old["ky_danh_gia_id"],
        "loai_okr": old["loai_okr"],
        "muc_tieu_lon": old["muc_tieu_lon"],
        "tan_suat": old.get("tan_suat", "hang_thang"),
        "nhan": old.get("nhan"),
        "cau_chuyen": old.get("cau_chuyen"),
        "han_hoan_thanh": old.get("han_hoan_thanh"),
        "trang_thai": "nhap",
        "tien_do_tong": 0,
        "nhan_xet_giao_vien": old.get("nhan_xet_giao_vien"),
    }.items() if v is not None}
    new_mt = supabase.table("muc_tieu").insert(new_data).execute()
    new_id = new_mt.data[0]["id"]
    krs = supabase.table("ket_qua_then_chot").select("*").eq("muc_tieu_id", id).execute()
    for kr in krs.data:
        kr_new = {k: v for k, v in {
            "muc_tieu_id": new_id, "thu_tu": kr["thu_tu"],
            "noi_dung": kr["noi_dung"], "loai_kr": kr.get("loai_kr"),
            "gia_tri_khoi_diem": kr.get("gia_tri_khoi_diem", 0),
            "gia_tri_muc_tieu": kr["gia_tri_muc_tieu"],
            "gia_tri_hien_tai": kr.get("gia_tri_khoi_diem", 0),
            "don_vi": kr["don_vi"], "xu_huong": kr.get("xu_huong"),
            "han_hoan_thanh": kr.get("han_hoan_thanh"),
            "nguoi_phu_trach_id": nguoi_dung["id"],
        }.items() if v is not None}
        supabase.table("ket_qua_then_chot").insert(kr_new).execute()
    return {"id": new_id, "nhan_xet_cu": old.get("nhan_xet_giao_vien"), "message": "Da nhan ban OKR"}

@router.post("/{id}/hoan-thanh")
def hoan_thanh_okr(id: str, body: HoanThanhOKR, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    if nguoi_dung["vai_tro"] != "hoc_sinh":
        raise HTTPException(status_code=403, detail="Chi hoc sinh")
    mt = supabase.table("muc_tieu").select("*").eq("id", id).eq("hoc_sinh_id", nguoi_dung["id"]).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay")
    if mt.data[0]["trang_thai"] != "da_duyet":
        raise HTTPException(status_code=400, detail="Chi hoan thanh OKR da duyet")
    update = {"da_hoan_thanh": True, "ngay_cap_nhat": datetime.now(timezone.utc).isoformat()}
    if body.trang_thai_tu_danh_gia:
        update["trang_thai_tien_do"] = body.trang_thai_tu_danh_gia
    supabase.table("muc_tieu").update(update).eq("id", id).execute()
    return {"message": "Da danh dau hoan thanh OKR"}

@router.put("/{id}/nhan-xet")
def cap_nhat_nhan_xet(id: str, body: NhanXetGiaoVien, nguoi_dung=Depends(chi_giao_vien)):
    supabase.table("muc_tieu").update({"nhan_xet_giao_vien": body.nhan_xet}).eq("id", id).execute()
    return {"message": "Da luu nhan xet"}

@router.get("/{id}/lich-su")
def lich_su(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("lich_su_cap_nhat").select("*").eq("muc_tieu_id", id).order("thoi_diem", desc=True).execute()
    return res.data

@router.get("/theo-lop/{ten_lop}")
def muc_tieu_theo_lop(ten_lop: str, ky_id: Optional[str] = None, nguoi_dung=Depends(chi_giao_vien)):
    hs_res = supabase.table("nguoi_dung").select("id").eq("ten_lop", ten_lop).eq("vai_tro", "hoc_sinh").execute()
    hs_ids = [h["id"] for h in hs_res.data]
    if not hs_ids:
        return []
    query = supabase.table("muc_tieu").select("*, nguoi_dung:hoc_sinh_id(ho_ten, ten_lop)").in_("hoc_sinh_id", hs_ids).neq("trang_thai", "nhap")
    if ky_id:
        query = query.eq("ky_danh_gia_id", ky_id)
    res = query.order("ngay_tao", desc=True).execute()
    return res.data
