from fastapi import APIRouter, Depends
from database import supabase
from auth import lay_nguoi_dung_hien_tai, chi_quan_tri

router = APIRouter()

@router.get("/")
def danh_sach_thong_bao(nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    res = supabase.table("thong_bao").select("*").eq("nguoi_nhan", nguoi_dung["id"]).order("ngay_tao", desc=True).limit(50).execute()
    return res.data

@router.put("/{id}/da-doc")
def danh_dau_da_doc(id: str, nguoi_dung=Depends(lay_nguoi_dung_hien_tai)):
    supabase.table("thong_bao").update({"da_doc": True}).eq("id", id).eq("nguoi_nhan", nguoi_dung["id"]).execute()
    return {"message": "Da danh dau da doc"}

@router.post("/test")
def test_email(nguoi_dung=Depends(chi_quan_tri)):
    from email_service import gui_email_test
    gui_email_test(nguoi_dung["email"])
    return {"message": "Da gui email thu nghiem"}
