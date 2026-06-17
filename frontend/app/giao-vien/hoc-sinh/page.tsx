"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

const MENU = [
  { href: "/giao-vien", label: "Bảng theo dõi lớp" },
  { href: "/giao-vien/hoc-sinh", label: "Danh sách học sinh" },
  { href: "/giao-vien/mau", label: "Mẫu OKR" },
  { href: "/giao-vien/bao-cao", label: "Báo cáo" },
];

const TT: Record<string, { label: string; cls: string }> = {
  cho_duyet:   { label: "Chờ duyệt", cls: "bg-amber-100 text-amber-700" },
  da_duyet:    { label: "Đã duyệt",  cls: "bg-green-100 text-green-700" },
  yeu_cau_sua: { label: "Cần sửa",   cls: "bg-red-100 text-red-700" },
  xin_xoa:     { label: "Chờ xóa",   cls: "bg-gray-100 text-gray-500" },
};

const TIEN_DO_STYLE: Record<string, { label: string; bg: string }> = {
  xuat_sac:   { label: "✦ Xuất sắc",    bg: "bg-[#1B5E20] text-white" },
  tot:        { label: "✓ Tốt",          bg: "bg-[#388E3C] text-white" },
  dung_huong: { label: "→ Đúng hướng",  bg: "bg-[#F9A825] text-white" },
  can_chu_y:  { label: "⚠ Cần chú ý",  bg: "bg-[#E65100] text-white" },
  chech_huong:{ label: "✗ Chệch hướng", bg: "bg-[#B71C1C] text-white" },
};

// 4 tiêu chí đánh giá OKR
const TIEU_CHI = [
  "Mục tiêu thể hiện nhiệm vụ trọng tâm, phù hợp với học sinh và yêu cầu lớp/trường",
  "Kết quả then chốt đo lường được và có thể theo dõi thường xuyên",
  "Mục tiêu có tính thách thức, đủ khó để phấn đấu (Moonshot thinking)",
  "OKR giải quyết vấn đề thiết thực, cấp bách trong kỳ này",
];

const EMOJI_OPTS = [
  { v: 1, icon: "😟", label: "Không đồng ý" },
  { v: 2, icon: "😐", label: "Phân vân" },
  { v: 3, icon: "🙂", label: "Bình thường" },
  { v: 4, icon: "😊", label: "Đồng ý" },
];

function tinhTienDoKR(kr: any, val: number): number {
  const kd = parseFloat(kr.gia_tri_khoi_diem) || 0;
  const mt = parseFloat(kr.gia_tri_muc_tieu) || 100;
  if (kr.xu_huong === "giam") {
    if (kd === mt) return 100;
    if (kd > mt) return Math.max(0, Math.min(100, Math.round((kd - val) / (kd - mt) * 100)));
    return val <= mt ? 100 : 0;
  }
  if (mt === kd) return 100;
  return Math.max(0, Math.min(100, Math.round((val - kd) / (mt - kd) * 100)));
}

function calcOKRProgress(krs: any[]): number {
  if (!krs.length) return 0;
  return Math.round(krs.reduce((s, kr) => s + tinhTienDoKR(kr, kr.gia_tri_hien_tai ?? kr.gia_tri_khoi_diem ?? 0), 0) / krs.length);
}

export default function GiaoVienHocSinhPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [hsList, setHsList] = useState<any[]>([]);
  const [sel, setSel] = useState<any>(null);
  const [mucTieuHS, setMucTieuHS] = useState<any[]>([]);
  const [krsMap, setKrsMap] = useState<Record<string, any[]>>({});
  const [selMT, setSelMT] = useState<any>(null);

  const [showThem, setShowThem] = useState(false);
  const [showSua, setShowSua] = useState(false);
  const [showDuyet, setShowDuyet] = useState(false);     // Popup phê duyệt với checklist
  const [showTuChoi, setShowTuChoi] = useState(false);   // Popup từ chối với checklist
  const [showHuyDuyet, setShowHuyDuyet] = useState(false);
  const [showDanhGia, setShowDanhGia] = useState(false); // Đánh giá cuối kỳ

  const [formThem, setFormThem] = useState({ ho_ten: "", email: "", email_phu_huynh: "" });
  const [formSua, setFormSua] = useState({ ho_ten: "", email: "" });

  // Checklist duyệt
  const [checkTC, setCheckTC] = useState<Record<number,number>>({});
  const [nhanXetDuyet, setNhanXetDuyet] = useState("");
  const [lyDoTuChoi, setLyDoTuChoi] = useState("");

  // Đánh giá cuối kỳ
  const [danhGia, setDanhGia] = useState<any>(null);
  const [diemSo, setDiemSo] = useState(0);
  const [nhanXetGV, setNhanXetGV] = useState("");
  const [kyVong, setKyVong] = useState("");
  const [xuatSac, setXuatSac] = useState(false);
  const [kyDanhGiaId, setKyDanhGiaId] = useState("");

  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");
  const [saving, setSaving] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { khoiTao(); }, []);
  useEffect(() => {
    if (!nguoiDung) return;
    if (nguoiDung.vai_tro !== "giao_vien") { router.push("/dang-nhap"); return; }
    fetchHS();
    api.get("/api/v1/ky-danh-gia/").then(r => {
      const mo = r.data.find((k: any) => k.trang_thai === "mo");
      if (mo) setKyDanhGiaId(mo.id);
    });
  }, [nguoiDung]);

  function fetchHS() {
    const lop = (nguoiDung as any)?.ten_lop || "";
    if (!lop) { setHsList([]); return; }
    api.get(`/api/v1/nguoi-dung/hoc-sinh/${encodeURIComponent(lop)}`).then(r => setHsList(r.data)).catch(() => setHsList([]));
  }

  async function chonHS(hs: any) {
    setSel(hs);
    setSel(hs);
    fetchMucTieuHS(hs.id);
  }

  async function fetchMucTieuHS(hsId: string) {
    try {
      const r = await api.get(`/api/v1/muc-tieu/?hoc_sinh_id=${hsId}`);
      setMucTieuHS(r.data);
      // Fetch KRs for each OKR
      const map: Record<string, any[]> = {};
      await Promise.all(r.data.map(async (mt: any) => {
        const kr = await api.get(`/api/v1/kr/muc-tieu/${mt.id}`);
        map[mt.id] = kr.data;
      }));
      setKrsMap(map);
    } catch { setMucTieuHS([]); }
  }

  async function themHS() {
    if (!formThem.ho_ten || !formThem.email) {
      toast.error("Điền đầy đủ họ tên và email"); return;
    }
    try {
      await api.post("/api/v1/nguoi-dung/hoc-sinh", {
        ho_ten: formThem.ho_ten, email: formThem.email,
        email_phu_huynh: formThem.email_phu_huynh || null,
        ten_lop: (nguoiDung as any)?.ten_lop || "",
      });
      toast.success("Đã thêm học sinh! Mật khẩu mặc định: Okr@12345");
      setShowThem(false); setFormThem({ ho_ten: "", email: "", email_phu_huynh: "" });
      fetchHS();
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi thêm học sinh"); }
  }

  async function suaHS() {
    if (!sel) return;
    try {
      await api.put(`/api/v1/nguoi-dung/hoc-sinh/${sel.id}`, formSua);
      toast.success("Đã cập nhật!"); setShowSua(false); fetchHS();
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi"); }
  }

  async function resetMKHS(id: string, ten: string) {
    if (!confirm(`Reset mật khẩu của ${ten} về Okr@12345?`)) return;
    try {
      await api.put(`/api/v1/nguoi-dung/${id}/reset-mat-khau`);
      toast.success(`Đã reset mật khẩu ${ten}`);
    } catch { toast.error("Lỗi reset mật khẩu"); }
  }

  async function xoaHS(id: string, ten: string) {
    if (!confirm(`Xác nhận xóa tài khoản học sinh ${ten}?`)) return;
    try {
      await api.delete(`/api/v1/nguoi-dung/${id}`);
      toast.success("Đã xóa tài khoản"); setSel(null); setMucTieuHS([]); fetchHS();
    } catch { toast.error("Lỗi xóa tài khoản"); }
  }

  // Phê duyệt với checklist
  async function pheduyet() {
    if (!selMT) return;
    setSaving(true);
    try {
      await api.post(`/api/v1/muc-tieu/${selMT.id}/duyet`, {
        tieu_chi_1: checkTC[0] || null, tieu_chi_2: checkTC[1] || null,
        tieu_chi_3: checkTC[2] || null, tieu_chi_4: checkTC[3] || null,
        nhan_xet: nhanXetDuyet || null,
      });
      toast.success("Đã phê duyệt OKR!");
      setShowDuyet(false); setCheckTC({}); setNhanXetDuyet("");
      if (sel) fetchMucTieuHS(sel.id);
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi phê duyệt"); }
    finally { setSaving(false); }
  }

  // Từ chối với checklist
  async function tuChoi() {
    if (!lyDoTuChoi.trim()) { toast.error("Nhập lý do từ chối"); return; }
    if (!selMT) return;
    setSaving(true);
    try {
      await api.post(`/api/v1/muc-tieu/${selMT.id}/yeu-cau-sua`, {
        tieu_chi_1: checkTC[0] || null, tieu_chi_2: checkTC[1] || null,
        tieu_chi_3: checkTC[2] || null, tieu_chi_4: checkTC[3] || null,
        ly_do: lyDoTuChoi,
      });
      toast.success("Đã gửi yêu cầu chỉnh sửa!");
      setShowTuChoi(false); setCheckTC({}); setLyDoTuChoi("");
      if (sel) fetchMucTieuHS(sel.id);
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi"); }
    finally { setSaving(false); }
  }

  // Hủy duyệt
  async function huyDuyet() {
    if (!selMT) return;
    setSaving(true);
    try {
      await api.post(`/api/v1/muc-tieu/${selMT.id}/huy-duyet`);
      toast.success("Đã thu hồi phê duyệt!");
      setShowHuyDuyet(false);
      if (sel) fetchMucTieuHS(sel.id);
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi"); }
    finally { setSaving(false); }
  }

  // Mở dialog đánh giá cuối kỳ
  async function moDanhGia(hs: any) {
    if (!kyDanhGiaId) { toast.error("Không có kỳ đánh giá đang mở"); return; }
    try {
      const r = await api.get(`/api/v1/danh-gia-cuoi-ky/${hs.id}?ky_id=${kyDanhGiaId}`);
      setDanhGia(r.data);
      setDiemSo(r.data.diem_so || 0);
      setNhanXetGV(r.data.nhan_xet_gv || "");
      setKyVong(r.data.ky_vong_ky_tiep || "");
      setXuatSac(r.data.trien_khai_xuat_sac || false);
      setShowDanhGia(true);
    } catch { toast.error("Không tải được đánh giá"); }
  }

  async function luuDanhGia(hoanTat = false) {
    if (!sel || !kyDanhGiaId) return;
    setSaving(true);
    try {
      await api.put(`/api/v1/danh-gia-cuoi-ky/${sel.id}?ky_id=${kyDanhGiaId}`, {
        nhan_xet_gv: nhanXetGV,
        diem_so: diemSo || null,
        ky_vong_ky_tiep: kyVong || null,
        trien_khai_xuat_sac: xuatSac,
      });
      if (hoanTat) {
        await api.post(`/api/v1/danh-gia-cuoi-ky/${sel.id}/hoan-tat?ky_id=${kyDanhGiaId}`);
        toast.success("Đã hoàn tất đánh giá cuối kỳ!");
      } else {
        toast.success("Đã lưu đánh giá!");
      }
      if (hoanTat) setShowDanhGia(false);
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi lưu"); }
    finally { setSaving(false); }
  }

  async function uploadExcel(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const lop = (nguoiDung as any)?.ten_lop || "";
      const r = await api.post(
        `/api/v1/nguoi-dung/nhap-danh-sach?vai_tro=hoc_sinh&ten_lop=${encodeURIComponent(lop)}`,
        fd, { headers: { "Content-Type": "multipart/form-data" } }
      );
      const sl = r.data.thanh_cong || 0;
      const loi: string[] = r.data.loi || [];
      if (sl > 0) { toast.success(`Đã nhập ${sl} học sinh!`); fetchHS(); }
      else if (loi.length > 0 && loi.every(m => m.includes("da ton tai"))) {
        toast.warning(`Tất cả ${loi.length} email đã tồn tại trong hệ thống.`);
      } else if (sl === 0 && loi.length === 0) {
        toast.info("File không có dữ liệu");
      }
      const loiNghiem = loi.filter(m => !m.includes("da ton tai"));
      const loiTrung = loi.filter(m => m.includes("da ton tai"));
      loiNghiem.forEach((msg: string) => toast.error(msg, { duration: 6000 }));
      if (loiTrung.length > 0 && sl > 0) toast.warning(`${loiTrung.length} email đã tồn tại (bỏ qua)`, { duration: 4000 });
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi nhập Excel"); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  const filtered = hsList
    .filter(hs =>
      hs.ho_ten?.toLowerCase().includes(search.toLowerCase()) ||
      hs.email?.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => {
      const sa = a.so_thu_tu ?? 9999, sb = b.so_thu_tu ?? 9999;
      if (sa !== sb) return sa - sb;
      return (a.ho_ten || "").localeCompare(b.ho_ten || "", "vi", { sensitivity: "base" });
    });

  return (
    <Layout menu={MENU} tieuDe="Giáo viên">
      <div className="flex h-full">
        {/* LEFT: Danh sách học sinh */}
        <div className="w-80 border-r bg-white flex flex-col flex-shrink-0 h-full overflow-hidden">
          <div className="p-4 bg-gradient-to-br from-orange-600 to-orange-700 text-white">
            <div className="flex justify-between items-center mb-3">
              <div>
                <h2 className="font-bold">Danh sách học sinh</h2>
                <p className="text-xs text-orange-200 mt-0.5">
                  Lớp {(nguoiDung as any)?.ten_lop || "?"} — {hsList.length} học sinh
                </p>
              </div>
              <button onClick={() => setShowThem(true)}
                className="bg-white text-orange-600 rounded-lg px-2 py-1 text-xs font-bold hover:bg-orange-50">
                + Thêm
              </button>
            </div>
            <div className="bg-white/20 rounded-xl p-3">
              <p className="text-xs text-orange-100 mb-2 font-medium">Nhập danh sách từ Excel</p>
              <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={uploadExcel} />
              <button onClick={() => fileRef.current?.click()} disabled={uploading}
                className="w-full bg-white text-orange-700 text-xs font-bold py-2 rounded-lg hover:bg-orange-50 disabled:opacity-60 mb-1.5">
                {uploading ? "Đang nhập..." : "Chọn file Excel"}
              </button>
              <a href="/mau-hoc-sinh.xlsx" download
                className="block w-full text-center border border-white/40 text-orange-100 text-xs py-1.5 rounded-lg hover:bg-white/10">
                Tải file mẫu Excel
              </a>
            </div>
          </div>
          <div className="p-3 border-b">
            <Input placeholder="Tìm kiếm học sinh..." value={search}
              onChange={e => setSearch(e.target.value)} className="text-sm" />
          </div>
          <div className="flex-1 overflow-y-auto divide-y">
            {filtered.length === 0 && (
              <div className="text-center py-10 text-gray-400 text-sm">
                {(nguoiDung as any)?.ten_lop ? "Không có học sinh" : "Bạn chưa được phân lớp"}
              </div>
            )}
            {filtered.map((hs, idx) => (
              <div key={hs.id} onClick={() => chonHS(hs)}
                className={`p-3 cursor-pointer hover:bg-orange-50 transition-colors ${sel?.id === hs.id ? "bg-orange-50 border-l-4 border-orange-500" : "border-l-4 border-transparent"}`}>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 w-5 text-right flex-shrink-0">{hs.so_thu_tu ?? idx + 1}</span>
                  <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center text-sm font-bold text-orange-600 flex-shrink-0">
                    {hs.ho_ten?.[0] || "?"}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-gray-800 truncate">{hs.ho_ten}</div>
                    <div className="text-xs text-gray-400 truncate">{hs.email}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT: Chi tiết học sinh */}
        <div className="flex-1 overflow-y-auto bg-gray-50">
          {!sel ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-5xl mb-3">👩‍🎓</div>
                <p className="text-gray-500 font-medium">Chọn học sinh để xem chi tiết</p>
              </div>
            </div>
          ) : (
            <div className="p-6 max-w-2xl">
              {/* Card thông tin HS */}
              <div className="bg-white rounded-2xl p-5 shadow-sm border mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-2xl font-bold text-white">
                      {sel.ho_ten?.[0] || "?"}
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">{sel.ho_ten}</h2>
                      <p className="text-sm text-gray-500">{sel.email}</p>
                      {sel.ten_lop && <p className="text-xs text-orange-600 font-medium mt-0.5">Lớp {sel.ten_lop}</p>}
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    <button onClick={() => { setFormSua({ ho_ten: sel.ho_ten, email: sel.email }); setShowSua(true); }}
                      className="text-xs border border-orange-300 text-orange-600 px-3 py-1.5 rounded-lg hover:bg-orange-50">
                      Sửa thông tin
                    </button>
                    <button onClick={() => resetMKHS(sel.id, sel.ho_ten)}
                      className="text-xs border border-blue-300 text-blue-500 px-3 py-1.5 rounded-lg hover:bg-blue-50">
                      Reset mật khẩu
                    </button>
                    <button onClick={() => moDanhGia(sel)}
                      className="text-xs border border-green-300 text-green-600 px-3 py-1.5 rounded-lg hover:bg-green-50">
                      Đánh giá cuối kỳ ★
                    </button>
                    <button onClick={() => xoaHS(sel.id, sel.ho_ten)}
                      className="text-xs border border-red-300 text-red-500 px-3 py-1.5 rounded-lg hover:bg-red-50">
                      Xóa tài khoản
                    </button>
                  </div>
                </div>
              </div>

              <div className="mb-3 flex justify-between items-center">
                <h3 className="font-bold text-gray-700">Mục tiêu OKR ({mucTieuHS.length})</h3>
              </div>

              {mucTieuHS.length === 0 ? (
                <div className="text-center py-10 bg-white rounded-xl border">
                  <p className="text-gray-400 text-sm">Học sinh chưa có mục tiêu OKR nào được nộp</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {mucTieuHS.map((mt: any) => {
                    const tt = TT[mt.trang_thai] || { label: mt.trang_thai, cls: "bg-gray-100 text-gray-500" };
                    const tdStyle = mt.trang_thai_tien_do ? TIEN_DO_STYLE[mt.trang_thai_tien_do] : null;
                    const krs = krsMap[mt.id] || [];
                    const td = calcOKRProgress(krs);
                    return (
                      <div key={mt.id} className="bg-white rounded-xl border shadow-sm p-4">
                        <div className="flex items-start justify-between mb-2">
                          <p className="text-sm font-semibold text-gray-800 flex-1 mr-3">{mt.muc_tieu_lon}</p>
                          <div className="flex items-center gap-1 flex-shrink-0">
                            {tdStyle && <span className={`text-xs px-2 py-0.5 rounded-full ${tdStyle.bg}`}>{tdStyle.label}</span>}
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${tt.cls}`}>{tt.label}</span>
                            {mt.da_hoan_thanh && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">✓ HT</span>}
                          </div>
                        </div>

                        {/* Tiến độ tổng */}
                        <div className="flex items-center gap-3 mb-3">
                          <div className="flex-1 bg-gray-100 rounded-full h-2">
                            <div className={`h-2 rounded-full ${td >= 80 ? "bg-green-500" : td >= 50 ? "bg-orange-500" : "bg-red-400"}`}
                              style={{ width: `${Math.min(td, 100)}%` }} />
                          </div>
                          <span className="text-sm font-bold text-orange-600 w-10 text-right">{td}%</span>
                        </div>

                        {/* KRs */}
                        {krs.length > 0 && (
                          <div className="space-y-1 mb-3">
                            {krs.map((kr: any, idx: number) => (
                              <div key={kr.id} className="bg-gray-50 rounded-lg px-3 py-1.5 text-xs">
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-700 flex-1">
                                    <span className="font-semibold text-orange-600 mr-1">KR{idx+1}</span>
                                    {kr.noi_dung}
                                  </span>
                                  <span className="text-gray-500 ml-2 flex-shrink-0">
                                    {kr.gia_tri_hien_tai}/{kr.gia_tri_muc_tieu} {kr.don_vi}
                                    <span className="ml-1 font-bold text-orange-600">{tinhTienDoKR(kr, kr.gia_tri_hien_tai ?? kr.gia_tri_khoi_diem ?? 0)}%</span>
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Nút hành động GV */}
                        {mt.trang_thai === "cho_duyet" && (
                          <div className="flex gap-2 pt-2 border-t">
                            <button onClick={() => { setSelMT(mt); setCheckTC({}); setNhanXetDuyet(""); setShowDuyet(true); }}
                              className="flex-1 text-xs bg-green-600 hover:bg-green-700 text-white py-1.5 rounded-lg font-medium">
                              ✓ Phê duyệt
                            </button>
                            <button onClick={() => { setSelMT(mt); setCheckTC({}); setLyDoTuChoi(""); setShowTuChoi(true); }}
                              className="flex-1 text-xs border border-orange-300 text-orange-600 hover:bg-orange-50 py-1.5 rounded-lg font-medium">
                              ✗ Yêu cầu sửa
                            </button>
                          </div>
                        )}
                        {mt.trang_thai === "da_duyet" && !mt.da_hoan_thanh && (
                          <div className="flex gap-2 pt-2 border-t">
                            <button onClick={() => { setSelMT(mt); setShowHuyDuyet(true); }}
                              className="flex-1 text-xs border border-gray-300 text-gray-500 hover:bg-gray-50 py-1.5 rounded-lg">
                              Thu hồi phê duyệt
                            </button>
                            <button onClick={() => { setSelMT(mt); setCheckTC({}); setLyDoTuChoi(""); setShowTuChoi(true); }}
                              className="flex-1 text-xs border border-orange-300 text-orange-600 hover:bg-orange-50 py-1.5 rounded-lg">
                              Yêu cầu sửa lại
                            </button>
                          </div>
                        )}
                        {mt.trang_thai === "xin_xoa" && (
                          <div className="flex gap-2 pt-2 border-t">
                            <button onClick={async () => {
                              await api.post(`/api/v1/muc-tieu/${mt.id}/dong-y-xoa`);
                              toast.success("Đã xóa OKR");
                              fetchMucTieuHS(sel.id);
                            }} className="flex-1 text-xs bg-red-600 text-white hover:bg-red-700 py-1.5 rounded-lg">
                              Đồng ý xóa
                            </button>
                          </div>
                        )}
                        {mt.nhan_xet_giao_vien && (
                          <p className="text-xs text-orange-600 mt-2 bg-orange-50 px-2 py-1 rounded">
                            💬 Nhận xét: {mt.nhan_xet_giao_vien}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* DIALOG: Thêm học sinh */}
      <Dialog open={showThem} onOpenChange={setShowThem}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Thêm học sinh mới</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-2">
            <div><Label>Họ tên *</Label>
              <Input className="mt-1" placeholder="Nguyễn Văn A"
                value={formThem.ho_ten} onChange={e => setFormThem({ ...formThem, ho_ten: e.target.value })} /></div>
            <div><Label>Email *</Label>
              <Input className="mt-1" type="email" placeholder="email@truong.edu.vn"
                value={formThem.email} onChange={e => setFormThem({ ...formThem, email: e.target.value })} /></div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
              Mật khẩu mặc định: <strong>Okr@12345</strong>
            </div>
            <div><Label>Email phụ huynh</Label>
              <Input className="mt-1" type="email" placeholder="phuhuynh@gmail.com (tuỳ chọn)"
                value={formThem.email_phu_huynh} onChange={e => setFormThem({ ...formThem, email_phu_huynh: e.target.value })} /></div>
            <p className="text-xs text-gray-400">Lớp: <strong>{(nguoiDung as any)?.ten_lop || "?"}</strong></p>
            <div className="flex gap-3">
              <button onClick={themHS} className="flex-1 bg-orange-600 hover:bg-orange-700 text-white py-2.5 rounded-xl font-semibold">Thêm</button>
              <button onClick={() => setShowThem(false)} className="flex-1 border rounded-xl py-2.5 text-gray-600 hover:bg-gray-50">Hủy</button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Sửa học sinh */}
      <Dialog open={showSua} onOpenChange={setShowSua}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Sửa thông tin học sinh</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-2">
            <div><Label>Họ tên</Label><Input className="mt-1" value={formSua.ho_ten} onChange={e => setFormSua({ ...formSua, ho_ten: e.target.value })} /></div>
            <div><Label>Email</Label><Input className="mt-1" type="email" value={formSua.email} onChange={e => setFormSua({ ...formSua, email: e.target.value })} /></div>
            <div className="flex gap-3">
              <button onClick={suaHS} className="flex-1 bg-orange-600 hover:bg-orange-700 text-white py-2.5 rounded-xl font-semibold">Lưu</button>
              <button onClick={() => setShowSua(false)} className="flex-1 border rounded-xl py-2.5 text-gray-600 hover:bg-gray-50">Hủy</button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Phê duyệt OKR (checklist) */}
      <Dialog open={showDuyet} onOpenChange={setShowDuyet}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>✓ Phê duyệt mục tiêu OKR</DialogTitle></DialogHeader>
          {selMT && (
            <div className="space-y-4 mt-2">
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm font-medium text-green-800">
                {selMT.muc_tieu_lon}
              </div>
              {TIEU_CHI.map((tc, i) => (
                <div key={i} className="border rounded-lg p-3">
                  <p className="text-sm text-gray-700 mb-2">{i + 1}. {tc}</p>
                  <div className="flex gap-3">
                    {EMOJI_OPTS.map(opt => (
                      <button key={opt.v} onClick={() => setCheckTC(p => ({ ...p, [i]: opt.v }))}
                        className={`flex flex-col items-center p-2 rounded-xl border-2 transition-all flex-1 ${checkTC[i] === opt.v ? "border-green-500 bg-green-50" : "border-gray-200 hover:border-gray-300"}`}>
                        <span className="text-xl">{opt.icon}</span>
                        <span className="text-xs text-gray-500 mt-0.5">{opt.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              <div>
                <Label>Nhận xét cho học sinh (tùy chọn)</Label>
                <Textarea className="mt-1" rows={2} placeholder="Lời nhận xét về OKR này..."
                  value={nhanXetDuyet} onChange={e => setNhanXetDuyet(e.target.value)} />
              </div>
              <div className="flex gap-3">
                <button onClick={() => setShowDuyet(false)}
                  className="flex-1 border rounded-xl py-2.5 text-gray-600 hover:bg-gray-50">Hủy</button>
                <button onClick={pheduyet} disabled={saving}
                  className="flex-1 bg-green-600 text-white py-2.5 rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50">
                  {saving ? "Đang duyệt..." : "Chấp thuận"}
                </button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* DIALOG: Từ chối OKR (checklist) */}
      <Dialog open={showTuChoi} onOpenChange={setShowTuChoi}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>✗ Yêu cầu chỉnh sửa OKR</DialogTitle></DialogHeader>
          {selMT && (
            <div className="space-y-4 mt-2">
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm font-medium text-red-800">
                {selMT.muc_tieu_lon}
              </div>
              {TIEU_CHI.map((tc, i) => (
                <div key={i} className="border rounded-lg p-3">
                  <p className="text-sm text-gray-700 mb-2">{i + 1}. {tc}</p>
                  <div className="flex gap-3">
                    {EMOJI_OPTS.map(opt => (
                      <button key={opt.v} onClick={() => setCheckTC(p => ({ ...p, [i]: opt.v }))}
                        className={`flex flex-col items-center p-2 rounded-xl border-2 transition-all flex-1 ${checkTC[i] === opt.v ? "border-orange-500 bg-orange-50" : "border-gray-200 hover:border-gray-300"}`}>
                        <span className="text-xl">{opt.icon}</span>
                        <span className="text-xs text-gray-500 mt-0.5">{opt.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              <div>
                <Label>Lý do yêu cầu sửa <span className="text-red-500">*</span></Label>
                <Textarea className="mt-1" rows={3} placeholder="Ví dụ: KR cần có chỉ tiêu cụ thể hơn..."
                  value={lyDoTuChoi} onChange={e => setLyDoTuChoi(e.target.value)} />
              </div>
              <div className="flex gap-3">
                <button onClick={() => setShowTuChoi(false)}
                  className="flex-1 border rounded-xl py-2.5 text-gray-600 hover:bg-gray-50">Hủy</button>
                <button onClick={tuChoi} disabled={saving}
                  className="flex-1 bg-orange-600 text-white py-2.5 rounded-xl font-semibold hover:bg-orange-700 disabled:opacity-50">
                  {saving ? "Đang gửi..." : "Gửi yêu cầu sửa"}
                </button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* DIALOG: Hủy duyệt */}
      <Dialog open={showHuyDuyet} onOpenChange={setShowHuyDuyet}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Thu hồi phê duyệt</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-2 text-sm">
            <p className="text-gray-600">Thu hồi phê duyệt sẽ đưa OKR về trạng thái Chờ duyệt. Học sinh có thể chỉnh sửa và nộp lại.</p>
            <p className="text-amber-600 text-xs bg-amber-50 p-2 rounded">⚠ Chỉ thu hồi được khi học sinh chưa cập nhật tiến độ.</p>
            <div className="flex gap-3">
              <button onClick={() => setShowHuyDuyet(false)}
                className="flex-1 border rounded-xl py-2 hover:bg-gray-50">Hủy bỏ</button>
              <button onClick={huyDuyet} disabled={saving}
                className="flex-1 bg-red-600 text-white py-2 rounded-xl hover:bg-red-700 disabled:opacity-50">
                {saving ? "Đang xử lý..." : "Xác nhận thu hồi"}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Đánh giá cuối kỳ */}
      <Dialog open={showDanhGia} onOpenChange={setShowDanhGia}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>★ Đánh giá cuối kỳ — {sel?.ho_ten}</DialogTitle></DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <Label className="text-base font-semibold">Bước 1. Chấm điểm</Label>
              <p className="text-xs text-gray-500 mb-2">Phản ánh mức độ nỗ lực và kết quả của học sinh (1–5 sao)</p>
              <div className="flex items-center gap-1 text-yellow-400">
                {[1,2,3,4,5].map(s => (
                  <button key={s} onClick={() => setDiemSo(s)}
                    className="text-3xl transition-transform hover:scale-110">
                    {diemSo >= s ? "★" : "☆"}
                  </button>
                ))}
                <span className="ml-2 text-sm font-semibold text-gray-600">
                  {diemSo > 0 ? `${diemSo}/5` : "Chưa chấm"}
                </span>
              </div>
              <label className="flex items-center gap-2 mt-2 text-sm cursor-pointer">
                <input type="checkbox" checked={xuatSac} onChange={e => setXuatSac(e.target.checked)} />
                🏆 Nỗ lực xuất sắc — học sinh có thành tích vượt trội so với kỳ vọng
              </label>
            </div>
            <div>
              <Label className="text-base font-semibold">Bước 2. Nhận xét tổng kết <span className="text-red-500">*</span></Label>
              <Textarea className="mt-2" rows={4} placeholder="Nhận xét về quá trình thực hiện OKR của học sinh..."
                value={nhanXetGV} onChange={e => setNhanXetGV(e.target.value)} />
            </div>
            <div>
              <Label className="text-base font-semibold">Bước 3. Kỳ vọng kỳ tiếp theo (tùy chọn)</Label>
              <Textarea className="mt-2" rows={3} placeholder="Định hướng, kỳ vọng của giáo viên cho học sinh ở kỳ sau..."
                value={kyVong} onChange={e => setKyVong(e.target.value)} />
            </div>
            <div className="flex gap-3 pt-2">
              <button onClick={() => luuDanhGia(false)} disabled={saving}
                className="flex-1 border-2 border-orange-600 text-orange-600 py-2.5 rounded-xl font-semibold hover:bg-orange-50 disabled:opacity-50">
                Lưu nháp
              </button>
              <button onClick={() => luuDanhGia(true)} disabled={saving || !nhanXetGV.trim()}
                className="flex-1 bg-green-600 text-white py-2.5 rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50">
                {saving ? "Đang lưu..." : "Hoàn tất đánh giá"}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
