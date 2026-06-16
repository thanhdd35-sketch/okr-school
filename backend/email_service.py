import os
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
TEN_TRUONG = os.getenv("TEN_TRUONG", "Truong THPT")

def gui_email(den: str, tieu_de: str, noi_dung_html: str):
    if not RESEND_API_KEY or RESEND_API_KEY == "chua_co":
        print(f"[EMAIL BI TAT] Den: {den} | Tieu de: {tieu_de}")
        return

    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from": f"{TEN_TRUONG} <okr@{TEN_TRUONG.lower().replace(' ', '')}.edu.vn>",
            "to": [den],
            "subject": tieu_de,
            "html": noi_dung_html
        })
    except Exception as e:
        print(f"[LOI EMAIL] {e}")

def gui_email_duyet_muc_tieu(email: str, ho_ten: str, ten_muc_tieu: str):
    gui_email(
        den=email,
        tieu_de="[OKR] Muc tieu cua ban da duoc duyet",
        noi_dung_html=f"<p>Chao {ho_ten},</p><p>Muc tieu <b>{ten_muc_tieu}</b> cua ban da duoc giao vien duyet. Hay bat dau cap nhat tien do!</p>"
    )

def gui_email_yeu_cau_sua(email: str, ho_ten: str, ten_muc_tieu: str, ly_do: str):
    gui_email(
        den=email,
        tieu_de="[OKR] Muc tieu can duoc chinh sua",
        noi_dung_html=f"<p>Chao {ho_ten},</p><p>Muc tieu <b>{ten_muc_tieu}</b> can chinh sua.</p><p>Ly do: {ly_do}</p>"
    )

def gui_email_hoan_tat_danh_gia(email_ph: str, ho_ten_con: str, ten_ky: str):
    gui_email(
        den=email_ph,
        tieu_de="[OKR] Nhan xet cuoi ky cua con da san sang",
        noi_dung_html=f"<p>Kinh gui Quy phu huynh,</p><p>Giao vien da hoan tat danh gia cuoi ky <b>{ten_ky}</b> cho hoc sinh <b>{ho_ten_con}</b>. Vui long dang nhap de xem nhan xet.</p>"
    )

def gui_email_nhac_cap_nhat(email_ph: str, ho_ten_con: str, so_ngay: int):
    gui_email(
        den=email_ph,
        tieu_de=f"[OKR] Con ban chua cap nhat tien do {so_ngay} ngay",
        noi_dung_html=f"<p>Kinh gui Quy phu huynh,</p><p>Hoc sinh <b>{ho_ten_con}</b> chua cap nhat tien do muc tieu trong <b>{so_ngay} ngay</b>. Vui long nhac con cap nhat.</p>"
    )

def gui_email_sap_het_ky(email: str, ho_ten: str, ten_ky: str):
    gui_email(
        den=email,
        tieu_de=f"[OKR] Con 3 ngay ket thuc ky \"{ten_ky}\"",
        noi_dung_html=f"<p>Chao {ho_ten},</p><p>Chi con <b>3 ngay</b> nua la ket thuc ky danh gia <b>{ten_ky}</b>. Hay dam bao muc tieu duoc cap nhat day du.</p>"
    )

def gui_email_test(email: str):
    gui_email(
        den=email,
        tieu_de="[OKR] Email thu nghiem",
        noi_dung_html="<p>He thong email dang hoat dong binh thuong.</p>"
    )
