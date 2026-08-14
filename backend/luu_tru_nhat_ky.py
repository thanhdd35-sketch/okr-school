"""
LUU TRU NHAT KY KIEM TOAN RA OBJECT STORE — v2.6

Muc dich (theo yeu cau cua bo phan IT nha truong):
  - Tach nhat ky kiem toan KHOI cơ so du lieu nghiep vu.
  - Bao dam luu tru toi thieu 12-24 thang.
  - Nhat ky phai "chi ghi them" (append-only), khong bi sua/xoa tuy tien.

CACH LAM
  Hang thang, xuat cac ban ghi CHUA luu tru ra file NDJSON roi tai len
  Supabase Storage (object store) trong bucket rieng. Sau khi tai len
  thanh cong moi danh dau da_luu_tru = TRUE trong CSDL.

  File tren object store la ban goc phuc vu kiem toan. Du lieu trong CSDL
  chi la ban tien tra cuu nhanh.

CHUAN BI MOT LAN (lam trong Supabase Dashboard):
  Storage -> New bucket -> ten: "nhat-ky-kiem-toan" -> KHONG tick Public.
  Nen bat thêm quy tac chi cho phep ghi, khong cho xoa doi voi khoa ung dung.

BIEN MOI TRUONG (tuy chon):
  BUCKET_NHAT_KY        mac dinh "nhat-ky-kiem-toan"
  GIU_NHAT_KY_THANG     mac dinh 24 (thang giu trong CSDL)
  CHO_PHEP_DON_NHAT_KY  mac dinh "khong" — chi khi dat "co" moi don ban ghi
                        DA luu tru va qua han giu. Mac dinh KHONG xoa gi.
"""

import os
import json
import httpx
from datetime import datetime, timedelta, timezone

from database import SUPABASE_URL, SUPABASE_KEY, supabase

BUCKET = os.getenv("BUCKET_NHAT_KY", "nhat-ky-kiem-toan")
GIU_THANG = int(os.getenv("GIU_NHAT_KY_THANG", 24))
CHO_PHEP_DON = os.getenv("CHO_PHEP_DON_NHAT_KY", "khong").strip().lower() == "co"

SO_BAN_GHI_MOI_LAN = 1000


def _tai_len_object_store(duong_dan: str, noi_dung: str) -> bool:
    """Tai file len Supabase Storage. Tra ve True neu thanh cong."""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{duong_dan}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/x-ndjson",
        "x-upsert": "false",          # khong ghi de file da co -> bao ve tinh toan ven
    }
    try:
        with httpx.Client(timeout=60) as c:
            r = c.post(url, headers=headers, content=noi_dung.encode("utf-8"))
        if r.status_code in (200, 201):
            return True
        print(f"[LUU TRU] Tai len that bai {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"[LUU TRU] Loi tai len: {str(e)[:200]}")
        return False


def xuat_nhat_ky_ra_object_store():
    """Xuat cac ban ghi chua luu tru ra object store, sau do danh dau da luu tru."""
    print("[LUU TRU] Bat dau xuat nhat ky kiem toan...")
    try:
        res = (supabase.table("nhat_ky_hoat_dong")
               .select("*")
               .eq("da_luu_tru", False)
               .order("thoi_diem")
               .limit(SO_BAN_GHI_MOI_LAN)
               .execute())
    except Exception as e:
        print(f"[LUU TRU] Chua doc duoc nhat ky (co the chua chay migration v2.6): {str(e)[:150]}")
        return

    ban_ghi = res.data or []
    if not ban_ghi:
        print("[LUU TRU] Khong co ban ghi moi can luu tru.")
        return

    now = datetime.now(timezone.utc)
    duong_dan = f"{now:%Y}/{now:%Y-%m}/nhat-ky-{now:%Y%m%d-%H%M%S}.ndjson"
    noi_dung = "\n".join(json.dumps(b, ensure_ascii=False, default=str) for b in ban_ghi)

    if not _tai_len_object_store(duong_dan, noi_dung):
        print("[LUU TRU] Dung lai — KHONG danh dau da_luu_tru de lan sau thu lai.")
        return

    ids = [b["id"] for b in ban_ghi if b.get("id")]
    da_danh_dau = 0
    for i in range(0, len(ids), 100):
        lo = ids[i:i + 100]
        try:
            supabase.table("nhat_ky_hoat_dong").update({"da_luu_tru": True}).in_("id", lo).execute()
            da_danh_dau += len(lo)
        except Exception as e:
            print(f"[LUU TRU] Loi danh dau: {str(e)[:150]}")
    print(f"[LUU TRU] Da luu {len(ban_ghi)} ban ghi -> {BUCKET}/{duong_dan} (danh dau {da_danh_dau})")


def don_nhat_ky_qua_han():
    """Chi don ban ghi DA luu tru ra object store VA da qua thoi han giu.

    MAC DINH KHONG CHAY (CHO_PHEP_DON_NHAT_KY != 'co') de tranh mat du lieu
    kiem toan ngoai y muon. Thoi han giu toi thieu theo yeu cau la 12-24 thang.
    """
    if not CHO_PHEP_DON:
        return
    if GIU_THANG < 12:
        print(f"[LUU TRU] Tu choi don: GIU_NHAT_KY_THANG={GIU_THANG} < 12 thang (vi pham thoi han luu toi thieu).")
        return

    moc = (datetime.now(timezone.utc) - timedelta(days=GIU_THANG * 30)).isoformat()
    try:
        supabase.table("nhat_ky_hoat_dong").delete() \
            .eq("da_luu_tru", True).lt("thoi_diem", moc).execute()
        print(f"[LUU TRU] Da don ban ghi DA luu tru va cu hon {GIU_THANG} thang.")
    except Exception as e:
        print(f"[LUU TRU] Loi khi don: {str(e)[:150]}")
