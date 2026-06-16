"""Tao tai khoan mau: giao vien, hoc sinh, phu huynh"""
import asyncio, sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

import bcrypt, httpx, json

SUPABASE_URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SECRET_KEY")
HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

def hash_pw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

async def main():
    async with httpx.AsyncClient() as c:
        # 1. Tao giao vien
        gv = {
            "ho_ten": "Nguyen Thi Lan",
            "email": "giaovien1@truong.edu.vn",
            "mat_khau_hash": hash_pw("Gv@123456"),
            "vai_tro": "giao_vien",
            "ten_lop": "10A1",
            "trang_thai": "hoat_dong",
        }
        r = await c.post(f"{SUPABASE_URL}/rest/v1/nguoi_dung", headers=HEADERS, json=gv)
        if r.status_code in (200, 201):
            gv_data = r.json()
            gv_id = gv_data[0]["id"] if isinstance(gv_data, list) else gv_data["id"]
            print(f"[OK] Giao vien: giaovien1@truong.edu.vn / Gv@123456  (id={gv_id[:8]}...)")
        else:
            # Co the da ton tai
            r2 = await c.get(f"{SUPABASE_URL}/rest/v1/nguoi_dung?email=eq.giaovien1@truong.edu.vn&select=id", headers=HEADERS)
            gv_id = r2.json()[0]["id"]
            print(f"[DA TON TAI] Giao vien: giaovien1@truong.edu.vn (id={gv_id[:8]}...)")

        # 2. Tao hoc sinh
        hs = {
            "ho_ten": "Tran Van Minh",
            "email": "hocsinh1@truong.edu.vn",
            "mat_khau_hash": hash_pw("Hs@123456"),
            "vai_tro": "hoc_sinh",
            "ten_lop": "10A1",
            "giao_vien_id": gv_id,
            "email_phu_huynh": "phuhuynh1@gmail.com",
            "trang_thai": "hoat_dong",
        }
        r = await c.post(f"{SUPABASE_URL}/rest/v1/nguoi_dung", headers=HEADERS, json=hs)
        if r.status_code in (200, 201):
            hs_data = r.json()
            hs_id = hs_data[0]["id"] if isinstance(hs_data, list) else hs_data["id"]
            print(f"[OK] Hoc sinh: hocsinh1@truong.edu.vn / Hs@123456  (id={hs_id[:8]}...)")
        else:
            r2 = await c.get(f"{SUPABASE_URL}/rest/v1/nguoi_dung?email=eq.hocsinh1@truong.edu.vn&select=id", headers=HEADERS)
            hs_id = r2.json()[0]["id"]
            print(f"[DA TON TAI] Hoc sinh: hocsinh1@truong.edu.vn (id={hs_id[:8]}...)")

        print(f"[OK] Phu huynh: phuhuynh1@gmail.com / Hs@123456 (mat khau cua con)")
        print()
        print("=== HOAN THANH ===")
        print("TAI KHOAN MAU:")
        print("  Quan tri : admin@truong.edu.vn     / Admin@2025")
        print("  Giao vien: giaovien1@truong.edu.vn / Gv@123456")
        print("  Hoc sinh : hocsinh1@truong.edu.vn  / Hs@123456")
        print("  Phu huynh: phuhuynh1@gmail.com + mat khau con: Hs@123456")

asyncio.run(main())
