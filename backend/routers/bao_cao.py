from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
from datetime import date
from database import supabase
from auth import chi_giao_vien

router = APIRouter()

TRANG_THAI_TD = {
    "xuat_sac":   "Xuất sắc (≥ 100%)",
    "tot":        "Tốt (≥ 80%)",
    "dung_huong": "Đúng hướng (≥ 60%)",
    "can_chu_y":  "Cần chú ý (≥ 40%)",
    "chech_huong":"Chệch hướng (< 40%)",
}

def tao_phieu_hoc_sinh(doc: Document, hs: dict, muc_tieu_list: list,
                       krs_by_mt: dict, danh_gia: dict,
                       ten_truong: str, ten_ky: str, ten_gv: str):
    # Tiêu đề
    h1 = doc.add_heading(ten_truong, level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    h2 = doc.add_heading(f"PHIEU DANH GIA MUC TIEU — {ten_ky}", level=2)
    h2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Thông tin học sinh
    info = doc.add_paragraph()
    info.add_run(f"Ho ten: {hs['ho_ten']}    Lop: {hs.get('ten_lop', '')}    Ngay xuat: {date.today().strftime('%d/%m/%Y')}")
    info.add_run(f"\nGiao vien chu nhiem: {ten_gv}    Ky danh gia: {ten_ky}")

    if not muc_tieu_list:
        doc.add_paragraph("Chua co muc tieu nao trong ky nay.")
    else:
        # Tính % tổng kỳ
        tds = [mt.get("tien_do_tong") or 0 for mt in muc_tieu_list if mt.get("trang_thai") == "da_duyet"]
        pct_ky = round(sum(tds) / len(tds), 1) if tds else 0

        p_pct = doc.add_paragraph()
        p_pct.add_run(f"Tien do tong ky: {pct_ky}% — Da nop {len(muc_tieu_list)} muc tieu").bold = True

        doc.add_heading("BANG MUC TIEU & KET QUA THEN CHOT", level=3)

        for idx, mt in enumerate(muc_tieu_list, 1):
            # Tiêu đề mục tiêu
            p_mt = doc.add_paragraph()
            r = p_mt.add_run(f"{idx}. {mt.get('muc_tieu_lon', '')}  —  {mt.get('tien_do_tong') or 0}%")
            r.bold = True
            r.font.size = Pt(12)

            tt = mt.get("trang_thai", "")
            tt_text = {"da_duyet": "Da duyet", "cho_duyet": "Cho duyet",
                       "yeu_cau_sua": "Can sua", "nhap": "Nhap"}.get(tt, tt)
            p_mt.add_run(f"  [{tt_text}]")

            krs = krs_by_mt.get(mt["id"], [])
            if krs:
                # Bảng KR
                table = doc.add_table(rows=1, cols=6)
                table.style = "Table Grid"
                headers = ["KR", "Noi dung", "Khoi diem → Muc tieu", "Hien tai", "Don vi", "Tien do"]
                for i, h in enumerate(headers):
                    c = table.rows[0].cells[i]
                    c.text = h
                    c.paragraphs[0].runs[0].bold = True

                for kr_idx, kr in enumerate(krs, 1):
                    row = table.add_row()
                    row.cells[0].text = str(kr_idx)
                    row.cells[1].text = kr.get("noi_dung", "")
                    row.cells[2].text = f"{kr.get('gia_tri_khoi_diem', 0)} → {kr.get('gia_tri_muc_tieu', '')}"
                    row.cells[3].text = str(kr.get("gia_tri_hien_tai", 0))
                    row.cells[4].text = kr.get("don_vi", "")
                    row.cells[5].text = f"{kr.get('tien_do_phan_tram', 0)}%"
            else:
                doc.add_paragraph("  Chua co ket qua then chot.")

            # Nhận xét GV về OKR
            if mt.get("nhan_xet_giao_vien"):
                p_nx = doc.add_paragraph()
                p_nx.add_run("  Nhan xet GV: ").bold = True
                p_nx.add_run(mt["nhan_xet_giao_vien"])

            # Trạng thái tiến độ
            if mt.get("trang_thai_tien_do"):
                p_td = doc.add_paragraph()
                p_td.add_run("  Trang thai tien do: ").bold = True
                p_td.add_run(TRANG_THAI_TD.get(mt["trang_thai_tien_do"], mt["trang_thai_tien_do"]))

            doc.add_paragraph()

    # Đánh giá cuối kỳ của GV
    if danh_gia and danh_gia.get("nhan_xet_gv"):
        doc.add_heading("NHAN XET TONG KET CUA GIAO VIEN", level=3)

        # Điểm sao
        diem = danh_gia.get("diem_so")
        if diem is not None:
            p_star = doc.add_paragraph()
            p_star.add_run("Diem danh gia: ").bold = True
            stars = "★" * int(diem) + ("½" if diem % 1 >= 0.5 else "") + "☆" * (5 - int(diem) - (1 if diem % 1 >= 0.5 else 0))
            p_star.add_run(f"{stars}  ({diem}/5)")

        doc.add_paragraph(danh_gia.get("nhan_xet_gv") or "")

        if danh_gia.get("ky_vong_ky_tiep"):
            p_kv = doc.add_paragraph()
            p_kv.add_run("Ky vong ky tiep: ").bold = True
            p_kv.add_run(danh_gia["ky_vong_ky_tiep"])

        if danh_gia.get("trien_khai_xuat_sac"):
            p_xuat_sac = doc.add_paragraph()
            p_xuat_sac.add_run("✦ Hoc sinh trien khai xuat sac — duoc de cu khen thuong").bold = True

    # Ý kiến gia đình
    if danh_gia and danh_gia.get("phan_hoi_ph"):
        doc.add_heading("Y KIEN GIA DINH", level=3)
        doc.add_paragraph(danh_gia.get("phan_hoi_ph") or "")

    # Chữ ký
    doc.add_paragraph()
    ky_ten = doc.add_paragraph()
    ky_ten.add_run("Giao vien chu nhiem" + " " * 30 + "Phu huynh hoc sinh")


@router.get("/hoc-sinh/{id}")
def xuat_bao_cao_hoc_sinh(id: str, ky_id: str, nguoi_dung=Depends(chi_giao_vien)):
    hs = supabase.table("nguoi_dung").select("*").eq("id", id).execute()
    if not hs.data:
        raise HTTPException(status_code=404, detail="Khong tim thay hoc sinh")

    mt_res = supabase.table("muc_tieu").select("*").eq("hoc_sinh_id", id).eq("ky_danh_gia_id", ky_id)\
        .neq("trang_thai", "nhap").order("ngay_tao").execute()
    dg = supabase.table("danh_gia_cuoi_ky").select("*").eq("hoc_sinh_id", id).eq("ky_danh_gia_id", ky_id).execute()
    ky = supabase.table("ky_danh_gia").select("ten_ky").eq("id", ky_id).execute()
    gv = supabase.table("nguoi_dung").select("ho_ten").eq("id", nguoi_dung["id"]).execute()

    ten_ky = ky.data[0]["ten_ky"] if ky.data else ""
    ten_gv = gv.data[0]["ho_ten"] if gv.data else ""
    ten_truong = "Truong THPT FPT"

    # Lấy KRs cho từng mục tiêu
    krs_by_mt: dict = {}
    for mt in mt_res.data:
        kr_res = supabase.table("ket_qua_then_chot").select("*").eq("muc_tieu_id", mt["id"]).order("thu_tu").execute()
        krs_by_mt[mt["id"]] = kr_res.data

    doc = Document()
    for section in doc.sections:
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(13)

    tao_phieu_hoc_sinh(doc, hs.data[0], mt_res.data, krs_by_mt,
                       dg.data[0] if dg.data else {}, ten_truong, ten_ky, ten_gv)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    ten_file = f"BaoCao_{hs.data[0]['ho_ten'].replace(' ', '_')}_{ten_ky.replace(' ', '_')}.docx"
    return StreamingResponse(buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={ten_file}"})


@router.get("/ca-lop/{ten_lop}")
def xuat_bao_cao_ca_lop(ten_lop: str, ky_id: str, nguoi_dung=Depends(chi_giao_vien)):
    hs_res = supabase.table("nguoi_dung").select("*").eq("ten_lop", ten_lop)\
        .eq("vai_tro", "hoc_sinh").order("ho_ten").execute()
    ky = supabase.table("ky_danh_gia").select("ten_ky").eq("id", ky_id).execute()
    gv = supabase.table("nguoi_dung").select("ho_ten").eq("id", nguoi_dung["id"]).execute()

    ten_ky = ky.data[0]["ten_ky"] if ky.data else ""
    ten_gv = gv.data[0]["ho_ten"] if gv.data else ""
    ten_truong = "Truong THPT FPT"

    doc = Document()
    for section in doc.sections:
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(13)

    for i, hs in enumerate(hs_res.data):
        if i > 0:
            doc.add_page_break()
        mt_res = supabase.table("muc_tieu").select("*").eq("hoc_sinh_id", hs["id"])\
            .eq("ky_danh_gia_id", ky_id).neq("trang_thai", "nhap").order("ngay_tao").execute()
        dg = supabase.table("danh_gia_cuoi_ky").select("*").eq("hoc_sinh_id", hs["id"])\
            .eq("ky_danh_gia_id", ky_id).execute()

        krs_by_mt: dict = {}
        for mt in mt_res.data:
            kr_res = supabase.table("ket_qua_then_chot").select("*").eq("muc_tieu_id", mt["id"]).order("thu_tu").execute()
            krs_by_mt[mt["id"]] = kr_res.data

        tao_phieu_hoc_sinh(doc, hs, mt_res.data, krs_by_mt,
                           dg.data[0] if dg.data else {}, ten_truong, ten_ky, ten_gv)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    ten_file = f"BaoCao_CaLop_{ten_lop}_{ten_ky.replace(' ', '_')}.docx"
    return StreamingResponse(buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={ten_file}"})
