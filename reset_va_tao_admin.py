"""
Reset toan bo du lieu va chi tao lai 1 tai khoan quan tri vien.
Chay: python reset_va_tao_admin.py
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

import bcrypt, httpx

SUPABASE_URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SECRET_KEY")
HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def xoa_bang(c: httpx.Client, bang: str):
    """Xoa tat ca dong trong bang (khong dieu kien)."""
    # Dung neq voi truong id de match tat ca
    r = c.delete(
        f"{SUPABASE_URL}/rest/v1/{bang}",
        headers={**HEADERS, "Prefer": ""},
        params={"id": "neq.00000000-0000-0000-0000-000000000000"},
    )
    if r.status_code in (200, 204):
        print(f"  [OK] Xoa {bang}")
    else:
        print(f"  [!] {bang}: {r.status_code} {r.text[:120]}")

def main():
    print("=" * 50)
    print("RESET TOAN BO DU LIEU")
    print("=" * 50)

    with httpx.Client(timeout=30) as c:
        # ---- XOA theo thu tu phu thuoc khoa ngoai ----
        print("\n[1] Xoa du lieu lien quan den nguoi dung...")
        for bang in [
            "lich_su_cap_nhat",
            "thong_bao",
            "nhat_ky_hoat_dong",
            "danh_gia_cuoi_ky",
            "muc_tieu",
            "mau_muc_tieu",
            "ky_danh_gia",
        ]:
            xoa_bang(c, bang)

        print("\n[2] Xoa tat ca nguoi dung (tru admin neu co)...")
        xoa_bang(c, "nguoi_dung")

        # ---- TAO ADMIN ----
        print("\n[3] Tao tai khoan quan tri vien...")
        admin_data = {
            "ho_ten": "Quan Tri Vien",
            "email": "admin@truong.edu.vn",
            "mat_khau_hash": hash_pw("Admin@2025"),
            "vai_tro": "quan_tri",
            "dang_hoat_dong": True,
            "bat_buoc_doi_mat_khau": False,
        }
        r = c.post(
            f"{SUPABASE_URL}/rest/v1/nguoi_dung",
            headers=HEADERS,
            json=admin_data,
        )
        if r.status_code in (200, 201):
            data = r.json()
            admin_id = (data[0] if isinstance(data, list) else data).get("id", "?")
            print(f"  [OK] admin@truong.edu.vn / Admin@2025  (id={admin_id[:8]}...)")
        else:
            print(f"  [FAIL] {r.status_code}: {r.text[:200]}")
            return

    print("\n" + "=" * 50)
    print("HOAN THANH!")
    print("  Quan tri vien: admin@truong.edu.vn / Admin@2025")
    print("  (Khong bat buoc doi mat khau)")
    print("=" * 50)
    print()
    print("Huong dan tiep theo:")
    print("  1. Dang nhap bang admin@truong.edu.vn / Admin@2025")
    print("  2. Vao Quan tri > Giao vien > Them moi de tao GV + phan lop")
    print("  3. GV dang nhap lan dau, doi mat khau, roi vao Danh sach HS > Them moi")
    print("  4. HS dang nhap lan dau, doi mat khau, bat dau tao OKR")

if __name__ == "__main__":
    main()
