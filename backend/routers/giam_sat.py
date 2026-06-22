from fastapi import APIRouter, Depends
from typing import Optional
import re
from database import supabase
from auth import chi_pho_ht_tro_len

router = APIRouter()


def _khoi_tu_lop(lop: str) -> str:
    if not lop:
        return "?"
    m = re.match(r"^(\d+)", lop)
    return m.group(1) if m else lop[:1].upper()


def _gom_du_lieu(ky_id: Optional[str]):
    hs = supabase.table("nguoi_dung").select("id, ho_ten, ten_lop, so_thu_tu")\
        .eq("vai_tro", "hoc_sinh").eq("dang_hoat_dong", True).execute().data
    gv = supabase.table("nguoi_dung").select("id, ho_ten, ten_lop")\
        .eq("vai_tro", "giao_vien").eq("dang_hoat_dong", True).execute().data
    mt_q = supabase.table("muc_tieu").select("hoc_sinh_id, tien_do_tong, trang_thai")\
        .neq("trang_thai", "nhap")
    if ky_id:
        mt_q = mt_q.eq("ky_danh_gia_id", ky_id)
    mt = mt_q.execute().data
    dggk_q = supabase.table("danh_gia_giua_ky").select("hoc_sinh_id, trang_thai_nhanh")
    if ky_id:
        dggk_q = dggk_q.eq("ky_danh_gia_id", ky_id)
    dggk = {d["hoc_sinh_id"]: d.get("trang_thai_nhanh") for d in dggk_q.execute().data}
    return hs, gv, mt, dggk


@router.get("/tong-quan-truong")
def tong_quan_truong(ky_id: Optional[str] = None, nguoi_dung=Depends(chi_pho_ht_tro_len)):
    """Cấp 1: thống kê theo từng lớp."""
    hs, gv, mt, dggk = _gom_du_lieu(ky_id)
    gv_theo_lop = {g["ten_lop"]: g["ho_ten"] for g in gv if g.get("ten_lop")}
    mt_theo_hs: dict = {}
    for m in mt:
        mt_theo_hs.setdefault(m["hoc_sinh_id"], []).append(m)

    lop_map: dict = {}
    # Tao truoc tat ca lop tu GVCN (de lop chua co HS van hien)
    for ten_lop in gv_theo_lop:
        if ten_lop:
            lop_map.setdefault(ten_lop, [])
    for h in hs:
        lop = h.get("ten_lop") or "?"
        lop_map.setdefault(lop, []).append(h)

    out = []
    for lop, ds in lop_map.items():
        si_so = len(ds)
        da_nop = sum(1 for h in ds if mt_theo_hs.get(h["id"]))
        da_duyet = sum(1 for h in ds if any(m["trang_thai"] == "da_duyet" for m in mt_theo_hs.get(h["id"], [])))
        tds = [m.get("tien_do_tong") or 0 for h in ds for m in mt_theo_hs.get(h["id"], []) if m["trang_thai"] == "da_duyet"]
        td_tb = round(sum(tds) / len(tds), 1) if tds else 0
        out.append({
            "khoi": _khoi_tu_lop(lop), "lop": lop,
            "gvcn": gv_theo_lop.get(lop, "—"),
            "si_so": si_so, "da_nop": da_nop, "da_duyet": da_duyet, "tien_do_tb": td_tb,
        })
    out.sort(key=lambda x: (x["khoi"], x["lop"]))
    return out


@router.get("/tong-quan-cac-khoi")
def tong_quan_cac_khoi(ky_id: Optional[str] = None, nguoi_dung=Depends(chi_pho_ht_tro_len)):
    """Phó HT: gộp theo khối."""
    lops = tong_quan_truong(ky_id, nguoi_dung)
    khoi_map: dict = {}
    for r in lops:
        k = khoi_map.setdefault(r["khoi"], {"khoi": r["khoi"], "si_so": 0, "da_nop": 0, "da_duyet": 0, "_td": []})
        k["si_so"] += r["si_so"]; k["da_nop"] += r["da_nop"]; k["da_duyet"] += r["da_duyet"]
        if r["tien_do_tb"]:
            k["_td"].append(r["tien_do_tb"])
    out = []
    for k in khoi_map.values():
        td = k.pop("_td")
        k["tien_do_tb"] = round(sum(td) / len(td), 1) if td else 0
        out.append(k)
    out.sort(key=lambda x: x["khoi"])
    return out


@router.get("/lop/{lop}/danh-sach-hs")
def danh_sach_hs_lop(lop: str, ky_id: Optional[str] = None, nguoi_dung=Depends(chi_pho_ht_tro_len)):
    """Cấp 2: HS trong lớp + số OKR, tiến độ, giữa kỳ, duyệt."""
    hs, _, mt, dggk = _gom_du_lieu(ky_id)
    hs = [h for h in hs if h.get("ten_lop") == lop]
    mt_theo_hs: dict = {}
    for m in mt:
        mt_theo_hs.setdefault(m["hoc_sinh_id"], []).append(m)
    out = []
    for h in sorted(hs, key=lambda x: x.get("so_thu_tu") or 9999):
        ms = mt_theo_hs.get(h["id"], [])
        tds = [m.get("tien_do_tong") or 0 for m in ms if m["trang_thai"] == "da_duyet"]
        out.append({
            "id": h["id"], "ho_ten": h["ho_ten"], "so_thu_tu": h.get("so_thu_tu"),
            "so_okr": len(ms),
            "tien_do_tb": round(sum(tds) / len(tds), 1) if tds else 0,
            "giua_ky": dggk.get(h["id"]),
            "da_duyet": any(m["trang_thai"] == "da_duyet" for m in ms),
        })
    return out


@router.get("/hoc-sinh/{hs_id}/toan-bo")
def toan_bo_okr_hs(hs_id: str, ky_id: Optional[str] = None, nguoi_dung=Depends(chi_pho_ht_tro_len)):
    """Cấp 3: chi tiết 1 HS (chỉ xem)."""
    hs = supabase.table("nguoi_dung").select("id, ho_ten, ten_lop, email, email_phu_huynh").eq("id", hs_id).execute().data
    mt_q = supabase.table("muc_tieu").select("*").eq("hoc_sinh_id", hs_id).neq("trang_thai", "nhap")
    if ky_id:
        mt_q = mt_q.eq("ky_danh_gia_id", ky_id)
    mts = mt_q.order("ngay_tao").execute().data
    krs_by_mt: dict = {}
    for m in mts:
        krs_by_mt[m["id"]] = supabase.table("ket_qua_then_chot").select("*").eq("muc_tieu_id", m["id"]).order("thu_tu").execute().data
    dgck_q = supabase.table("danh_gia_cuoi_ky").select("*").eq("hoc_sinh_id", hs_id)
    dggk_q = supabase.table("danh_gia_giua_ky").select("*").eq("hoc_sinh_id", hs_id)
    if ky_id:
        dgck_q = dgck_q.eq("ky_danh_gia_id", ky_id)
        dggk_q = dggk_q.eq("ky_danh_gia_id", ky_id)
    dgck = dgck_q.execute().data
    dggk = dggk_q.execute().data
    return {
        "hoc_sinh": hs[0] if hs else None,
        "muc_tieu": mts,
        "krs": krs_by_mt,
        "danh_gia_cuoi_ky": dgck[0] if dgck else None,
        "danh_gia_giua_ky": dggk[0] if dggk else None,
    }
