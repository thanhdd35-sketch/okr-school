from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import anthropic
import os
from database import supabase
from auth import lay_nguoi_dung_hien_tai, chi_giao_vien, chi_quan_tri

router = APIRouter()

def lay_client_ai():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class TaoNhanXetBody(BaseModel):
    hoc_sinh_id: str
    muc_tieu_id: str

class GoiYKRBody(BaseModel):
    muc_tieu_lon: Optional[str] = None
    muc_tieu: Optional[str] = None   # alias từ frontend cũ
    loai_okr: Optional[str] = None

class TomTatLopBody(BaseModel):
    ten_lop: str
    ky_danh_gia_id: str

@router.post("/tao-nhan-xet")
def tao_nhan_xet(body: TaoNhanXetBody, nguoi_dung=Depends(chi_giao_vien)):
    hs = supabase.table("nguoi_dung").select("ho_ten").eq("id", body.hoc_sinh_id).execute()
    if not hs.data:
        raise HTTPException(status_code=404, detail="Khong tim thay hoc sinh")

    mt = supabase.table("muc_tieu").select("*").eq("id", body.muc_tieu_id).execute()
    if not mt.data:
        raise HTTPException(status_code=404, detail="Khong tim thay muc tieu")

    lich_su = supabase.table("lich_su_cap_nhat").select("ghi_chu, tien_do, thoi_diem").eq("muc_tieu_id", body.muc_tieu_id).order("thoi_diem", desc=True).limit(10).execute()

    ho_ten = hs.data[0]["ho_ten"]
    muc_tieu = mt.data[0]
    ghi_chu_list = [l["ghi_chu"] for l in lich_su.data if l.get("ghi_chu")]

    prompt = f"""Ban la giao vien chu nhiem THPT dang viet nhan xet cuoi hoc ky.
Hoc sinh: {ho_ten}. Muc tieu: {muc_tieu['muc_tieu_lon']}.
Ket qua then chot: {muc_tieu['ket_qua_then_chot']} — dat {muc_tieu['tien_do_phan_tram']}%.
Chi tieu: {muc_tieu['chi_tieu']} {muc_tieu['don_vi']}, Thuc dat: {muc_tieu['thuc_dat']} {muc_tieu['don_vi']}.
Cac ghi chu cap nhat: {'; '.join(ghi_chu_list) if ghi_chu_list else 'Khong co ghi chu'}.
Yeu cau: viet nhan xet 3-4 cau, khuyen khich, thuc te, de cap con so cu the, phu hop van phong hoc ba THPT Viet Nam.
Chi tra ve doan nhan xet, khong them noi dung khac."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="AI chua duoc cau hinh")
    try:
        client = lay_client_ai()
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"nhan_xet": message.content[0].text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Loi goi AI: {str(e)[:150]}")

@router.post("/goi-y-kr")
def goi_y_kr(body: GoiYKRBody, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    ten_mt = body.muc_tieu_lon or body.muc_tieu or ""
    if not ten_mt:
        raise HTTPException(status_code=400, detail="Chua co noi dung muc tieu")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="AI chua duoc cau hinh")
    prompt = f"""Ban la tro ly giao duc giup hoc sinh THPT Viet Nam dat muc tieu.
Hoc sinh dat muc tieu lon: "{ten_mt}"
Hay de xuat 3 ket qua then chot (Key Result) cu the, do luong duoc cho muc tieu nay.
Moi ket qua then chot phai co: mo ta ngan gon + con so cu the + don vi.
Tra ve DUNG 3 goi y, moi goi y tren 1 dong, dinh dang: "Mo ta — X don_vi"
Vi du: "Doc sach thuong xuyen — 12 cuon"
Chi tra ve 3 dong goi y, khong them gi khac."""

    client = lay_client_ai()
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    lines = [l.strip() for l in message.content[0].text.strip().split("\n") if l.strip()]
    return {"goi_y": lines[:3]}

@router.post("/tom-tat-lop")
def tom_tat_lop(body: TomTatLopBody, nguoi_dung=Depends(chi_quan_tri)):
    hs_res = supabase.table("nguoi_dung").select("id, ho_ten").eq("ten_lop", body.ten_lop).eq("vai_tro", "hoc_sinh").execute()
    if not hs_res.data:
        raise HTTPException(status_code=404, detail="Khong co hoc sinh trong lop nay")

    hs_ids = [h["id"] for h in hs_res.data]
    mt_res = supabase.table("muc_tieu").select("hoc_sinh_id, trang_thai, tien_do_phan_tram, muc_tieu_lon").in_("hoc_sinh_id", hs_ids).eq("ky_danh_gia_id", body.ky_danh_gia_id).execute()

    tong_hs = len(hs_res.data)
    co_muc_tieu = len(set(m["hoc_sinh_id"] for m in mt_res.data))
    da_duyet = len([m for m in mt_res.data if m["trang_thai"] == "da_duyet"])
    tien_do_tb = round(sum(m["tien_do_phan_tram"] or 0 for m in mt_res.data) / len(mt_res.data), 1) if mt_res.data else 0

    prompt = f"""Ban la quan tri vien truong THPT dang tom tat tinh hinh lop {body.ten_lop}.
Du lieu:
- Tong so hoc sinh: {tong_hs}
- So hoc sinh da nop muc tieu: {co_muc_tieu}
- So muc tieu da duoc duyet: {da_duyet}
- Tien do trung binh: {tien_do_tb}%
- Tong so muc tieu: {len(mt_res.data)}

Hay viet doan tom tat 3-4 cau ve tinh hinh chung, diem noi bat va luu y cho lop nay.
Chi tra ve doan tom tat, khong them gi khac."""

    client = lay_client_ai()
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    return {"tom_tat": message.content[0].text}
