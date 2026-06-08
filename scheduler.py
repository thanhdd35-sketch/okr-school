from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
from database import supabase
from email_service import gui_email_nhac_cap_nhat, gui_email_sap_het_ky

def kiem_tra_khong_cap_nhat():
    print(f"[SCHEDULER] Dang kiem tra hoc sinh khong cap nhat...")
    bay_ngay_truoc = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    mt_res = supabase.table("muc_tieu").select("id, hoc_sinh_id, muc_tieu_lon").eq("trang_thai", "da_duyet").execute()

    da_gui = set()
    for mt in mt_res.data:
        if mt["hoc_sinh_id"] in da_gui:
            continue

        lich_su = supabase.table("lich_su_cap_nhat").select("thoi_diem").eq("muc_tieu_id", mt["id"]).gte("thoi_diem", bay_ngay_truoc).execute()
        if not lich_su.data:
            hs = supabase.table("nguoi_dung").select("ho_ten, email_phu_huynh").eq("id", mt["hoc_sinh_id"]).execute()
            if hs.data and hs.data[0].get("email_phu_huynh"):
                gui_email_nhac_cap_nhat(hs.data[0]["email_phu_huynh"], hs.data[0]["ho_ten"], 7)
                da_gui.add(mt["hoc_sinh_id"])

def kiem_tra_sap_het_ky():
    print(f"[SCHEDULER] Dang kiem tra ky sap ket thuc...")
    ngay_con_3 = (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat()

    ky_res = supabase.table("ky_danh_gia").select("*").eq("trang_thai", "mo").eq("ngay_ket_thuc", ngay_con_3).execute()

    for ky in ky_res.data:
        gv_res = supabase.table("nguoi_dung").select("ho_ten, email").eq("vai_tro", "giao_vien").eq("dang_hoat_dong", True).execute()
        for gv in gv_res.data:
            gui_email_sap_het_ky(gv["email"], gv["ho_ten"], ky["ten_ky"])

        hs_res = supabase.table("nguoi_dung").select("ho_ten, email").eq("vai_tro", "hoc_sinh").eq("dang_hoat_dong", True).execute()
        for hs in hs_res.data:
            gui_email_sap_het_ky(hs["email"], hs["ho_ten"], ky["ten_ky"])

def khoi_dong_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(kiem_tra_khong_cap_nhat, "cron", hour=8, minute=0)
    scheduler.add_job(kiem_tra_sap_het_ky, "cron", hour=8, minute=5)
    scheduler.start()
    print("[SCHEDULER] Da khoi dong thanh cong")
