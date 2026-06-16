"use client";
import { useEffect, useState } from "react";
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
  { href: "/hoc-sinh", label: "Mục tiêu OKR" },
  { href: "/hoc-sinh/tong-quan", label: "Tổng quan kỳ" },
  { href: "/hoc-sinh/mau", label: "Mẫu tham khảo" },
];

const TT_STYLE: Record<string, { label: string; cls: string }> = {
  nhap:        { label: "Nháp",       cls: "bg-gray-100 text-gray-500 border-gray-300" },
  cho_duyet:   { label: "Chờ duyệt",  cls: "bg-amber-100 text-amber-700 border-amber-300" },
  da_duyet:    { label: "Đã duyệt",   cls: "bg-green-100 text-green-700 border-green-300" },
  yeu_cau_sua: { label: "Cần sửa",    cls: "bg-red-100 text-red-700 border-red-300" },
  xin_xoa:     { label: "Chờ xóa",    cls: "bg-gray-100 text-gray-500 border-gray-300" },
};

const TIEN_DO_STYLE: Record<string, { label: string; cls: string; bg: string }> = {
  xuat_sac:   { label: "✦ Xuất sắc",    cls: "text-white", bg: "bg-[#1B5E20]" },
  tot:        { label: "✓ Tốt",          cls: "text-white", bg: "bg-[#388E3C]" },
  dung_huong: { label: "→ Đúng hướng",  cls: "text-white", bg: "bg-[#F9A825]" },
  can_chu_y:  { label: "⚠ Cần chú ý",  cls: "text-white", bg: "bg-[#E65100]" },
  chech_huong:{ label: "✗ Chệch hướng", cls: "text-white", bg: "bg-[#B71C1C]" },
};

const TAN_SUAT: Record<string, string> = {
  hang_tuan: "Hàng tuần", hai_tuan: "2 tuần/lần", hang_thang: "Hàng tháng"
};

const CHECKLIST_HS = [
  "Mục tiêu lớn của bạn có rõ ràng và truyền cảm hứng không?",
  "Các kết quả then chốt có đo lường được bằng con số cụ thể không?",
  "Mục tiêu có thực tế, có thể đạt được trong kỳ này không?",
  "Bạn có thể theo dõi và cập nhật tiến độ thường xuyên không?",
];
const CHECKLIST_OPT = ["Chưa rõ", "Tạm được", "Rõ ràng", "Rất rõ"];

export default function HocSinhPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();

  const [mucTieuList, setMucTieuList] = useState<any[]>([]);
  const [kyList, setKyList] = useState<any[]>([]);
  const [sel, setSel] = useState<any>(null);
  const [krsOfSel, setKrsOfSel] = useState<any[]>([]);
  const [lichSu, setLichSu] = useState<any[]>([]);
  const [danhGia, setDanhGia] = useState<any>(null);
  const [tab, setTab] = useState<"info" | "lich-su" | "danh-gia">("info");

  // Dialog states
  const [showTao, setShowTao] = useState(false);
  const [showChecklist, setShowChecklist] = useState(false);
  const [showCapNhat, setShowCapNhat] = useState(false);
  const [showHoanThanh, setShowHoanThanh] = useState(false);
  const [showNhanBan, setShowNhanBan] = useState(false);
  const [showXinXoa, setShowXinXoa] = useState(false);

  // Form: tạo OKR
  const [formMT, setFormMT] = useState({
    ky_danh_gia_id: "", loai_okr: "ca_nhan", muc_tieu_lon: "",
    tan_suat: "hang_thang", nhan: "", cau_chuyen: "", han_hoan_thanh: ""
  });
  const EMPTY_KR = { noi_dung: "", loai_kr: "so", gia_tri_khoi_diem: "0", gia_tri_muc_tieu: "", don_vi: "điểm", xu_huong: "tang", han_hoan_thanh: "" };
  const [krsForm, setKrsForm] = useState([{ ...EMPTY_KR }]);

  // Cập nhật tiến độ
  const [krChon, setKrChon] = useState<any>(null);
  const [giaTri, setGiaTri] = useState("");
  const [trangThaiTD, setTrangThaiTD] = useState("dung_huong");
  const [tuNhanXet, setTuNhanXet] = useState("");

  // Hoàn thành OKR
  const [ttHoanThanh, setTtHoanThanh] = useState("tot");
  const [nxHoanThanh, setNxHoanThanh] = useState("");

  // Checklist trước nộp
  const [checklistAns, setChecklistAns] = useState<Record<number, number>>({});
  const [pendingNopId, setPendingNopId] = useState<string | null>(null); // null = tạo mới

  // AI gợi ý
  const [goiY, setGoiY] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  // Nhân bản
  const [nhanBanTarget, setNhanBanTarget] = useState<any>(null);

  useEffect(() => { khoiTao(); }, []);
  useEffect(() => {
    if (!nguoiDung) return;
    if (nguoiDung.vai_tro !== "hoc_sinh") { router.push("/dang-nhap"); return; }
    fetchMT();
    api.get("/api/v1/ky-danh-gia/").then(r =>
      setKyList(r.data.filter((k: any) => k.trang_thai === "mo"))
    );
  }, [nguoiDung]);

  async function fetchMT(reselect?: string) {
    const r = await api.get("/api/v1/muc-tieu/");
    setMucTieuList(r.data);
    if (reselect) {
      const updated = r.data.find((x: any) => x.id === reselect);
      if (updated) { setSel(updated); fetchKRs(updated.id); }
    }
  }

  async function fetchKRs(mtId: string) {
    const r = await api.get(`/api/v1/kr/muc-tieu/${mtId}`);
    setKrsOfSel(r.data);
  }

  async function fetchDanhGia(mt: any) {
    if (!nguoiDung) return;
    try {
      const r = await api.get(`/api/v1/danh-gia-cuoi-ky/${nguoiDung.id}?ky_id=${mt.ky_danh_gia_id}`);
      setDanhGia(r.data?.nhan_xet_gv ? r.data : null);
    } catch { setDanhGia(null); }
  }

  async function chonMT(mt: any) {
    setSel(mt);
    setTab("info");
    fetchKRs(mt.id);
    const r = await api.get(`/api/v1/muc-tieu/${mt.id}/lich-su`);
    setLichSu(r.data);
    fetchDanhGia(mt);
  }

  // Tạo OKR - lưu nháp
  async function luuNhap() {
    if (!formMT.ky_danh_gia_id || !formMT.muc_tieu_lon.trim()) {
      toast.error("Chọn kỳ đánh giá và nhập mục tiêu lớn"); return;
    }
    if (!krsForm[0].noi_dung || !krsForm[0].gia_tri_muc_tieu) {
      toast.error("Thêm ít nhất 1 KR đầy đủ nội dung và chỉ tiêu"); return;
    }
    setSaving(true);
    try {
      const r = await api.post("/api/v1/muc-tieu/", {
        ...formMT, la_nhap: true,
        han_hoan_thanh: formMT.han_hoan_thanh || undefined,
        nhan: formMT.nhan || undefined,
        cau_chuyen: formMT.cau_chuyen || undefined,
      });
      const mtId = r.data.id;
      for (let i = 0; i < krsForm.length; i++) {
        const kr = krsForm[i];
        if (!kr.noi_dung || !kr.gia_tri_muc_tieu) continue;
        await api.post(`/api/v1/kr/muc-tieu/${mtId}`, {
          ...kr, thu_tu: i + 1,
          gia_tri_khoi_diem: parseFloat(kr.gia_tri_khoi_diem) || 0,
          gia_tri_muc_tieu: parseFloat(kr.gia_tri_muc_tieu),
          han_hoan_thanh: kr.han_hoan_thanh || undefined,
        });
      }
      toast.success("Đã lưu nháp OKR!");
      setShowTao(false);
      resetForm();
      fetchMT();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || e.message || "Lỗi khi lưu nháp");
    } finally { setSaving(false); }
  }

  // Mở checklist trước khi nộp mới
  function moNop() {
    if (!formMT.ky_danh_gia_id || !formMT.muc_tieu_lon.trim()) {
      toast.error("Chọn kỳ đánh giá và nhập mục tiêu lớn"); return;
    }
    if (!krsForm[0].noi_dung || !krsForm[0].gia_tri_muc_tieu) {
      toast.error("Thêm ít nhất 1 KR đầy đủ"); return;
    }
    setChecklistAns({});
    setPendingNopId(null); // null = tạo mới
    setShowChecklist(true);
  }

  // Nộp OKR đang ở nháp
  function moNopNhap(mtId: string) {
    setChecklistAns({});
    setPendingNopId(mtId);
    setShowChecklist(true);
  }

  // Xác nhận nộp (từ checklist popup)
  async function xacNhanNop() {
    setSaving(true);
    try {
      if (pendingNopId) {
        // Nộp OKR nháp sẵn có
        await api.post(`/api/v1/muc-tieu/${pendingNopId}/nop`, { ket_qua_checklist_hs: checklistAns });
        toast.success("Đã nộp OKR cho giáo viên duyệt!");
        setShowChecklist(false);
        fetchMT(pendingNopId);
      } else {
        // Tạo mới rồi nộp
        const r = await api.post("/api/v1/muc-tieu/", {
          ...formMT, la_nhap: true,
          han_hoan_thanh: formMT.han_hoan_thanh || undefined,
          nhan: formMT.nhan || undefined,
          cau_chuyen: formMT.cau_chuyen || undefined,
        });
        const mtId = r.data.id;
        for (let i = 0; i < krsForm.length; i++) {
          const kr = krsForm[i];
          if (!kr.noi_dung || !kr.gia_tri_muc_tieu) continue;
          await api.post(`/api/v1/kr/muc-tieu/${mtId}`, {
            ...kr, thu_tu: i + 1,
            gia_tri_khoi_diem: parseFloat(kr.gia_tri_khoi_diem) || 0,
            gia_tri_muc_tieu: parseFloat(kr.gia_tri_muc_tieu),
            han_hoan_thanh: kr.han_hoan_thanh || undefined,
          });
        }
        await api.post(`/api/v1/muc-tieu/${mtId}/nop`, { ket_qua_checklist_hs: checklistAns });
        toast.success("Đã nộp OKR cho giáo viên duyệt!");
        setShowChecklist(false);
        setShowTao(false);
        resetForm();
        fetchMT();
      }
    } catch (e: any) {
      toast.error(e.response?.data?.detail || e.message || "Lỗi khi nộp OKR");
    } finally { setSaving(false); }
  }

  // Cập nhật tiến độ KR
  async function capNhatKR() {
    if (!giaTri) { toast.error("Nhập giá trị thực đạt"); return; }
    setSaving(true);
    try {
      const pct = tinhTienDo(krChon, parseFloat(giaTri));
      const autoStatus = tinhTrangThaiTD(pct);
      await api.post(`/api/v1/kr/${krChon.id}/cap-nhat`, {
        gia_tri_hien_tai: parseFloat(giaTri),
        trang_thai_tu_danh_gia: autoStatus,
        tu_nhan_xet: tuNhanXet || undefined,
      });
      toast.success("Đã cập nhật tiến độ!");
      setShowCapNhat(false);
      setGiaTri(""); setTuNhanXet("");
      if (sel) { fetchKRs(sel.id); fetchMT(sel.id); }
    } catch (e: any) {
      toast.error(e.response?.data?.detail || e.message || "Lỗi cập nhật");
    } finally { setSaving(false); }
  }

  // Hoàn thành OKR
  async function hoanThanh() {
    if (!sel) return;
    setSaving(true);
    try {
      await api.post(`/api/v1/muc-tieu/${sel.id}/hoan-thanh`, {
        trang_thai_tu_danh_gia: ttHoanThanh,
        tu_nhan_xet: nxHoanThanh || undefined,
      });
      toast.success("Đã đánh dấu hoàn thành OKR!");
      setShowHoanThanh(false);
      fetchMT(sel.id);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || e.message || "Lỗi");
    } finally { setSaving(false); }
  }

  // Nhân bản OKR
  async function nhanBanOKR() {
    if (!sel) return;
    setSaving(true);
    try {
      const r = await api.post(`/api/v1/muc-tieu/${sel.id}/nhan-ban`);
      toast.success("Đã nhân bản! Mở bản nháp để chỉnh sửa...");
      setShowNhanBan(false);
      fetchMT(r.data.id);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || e.message || "Lỗi");
    } finally { setSaving(false); }
  }

  // Xin xóa OKR
  async function xinXoa() {
    if (!sel) return;
    try {
      if (sel.trang_thai === "nhap") {
        await api.delete(`/api/v1/muc-tieu/${sel.id}`);
        toast.success("Đã xóa bản nháp");
      } else {
        await api.post(`/api/v1/muc-tieu/${sel.id}/xin-xoa`);
        toast.success("Đã gửi yêu cầu xóa đến giáo viên");
      }
      setShowXinXoa(false);
      setSel(null);
      fetchMT();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || e.message || "Lỗi");
    }
  }

  function resetForm() {
    setFormMT({ ky_danh_gia_id: "", loai_okr: "ca_nhan", muc_tieu_lon: "", tan_suat: "hang_thang", nhan: "", cau_chuyen: "", han_hoan_thanh: "" });
    setKrsForm([{ ...EMPTY_KR }]);
    setGoiY([]);
  }

  function updateKR(i: number, field: string, val: string) {
    setKrsForm(p => p.map((k, j) => j === i ? { ...k, [field]: val } : k));
  }

  function tinhTienDo(kr: any, val: number) {
    const kd = parseFloat(kr.gia_tri_khoi_diem) || 0;
    const mt = parseFloat(kr.gia_tri_muc_tieu) || 100;
    if (kr.xu_huong === "giam") {
      if (kd === mt) return 100;
      if (kd > mt) {
        // Đúng hướng: khởi điểm cao hơn mục tiêu (VD: 100 → 20)
        return Math.max(0, Math.min(100, Math.round((kd - val) / (kd - mt) * 100)));
      } else {
        // Khởi điểm thấp hơn mục tiêu (setup không hợp lệ cho "giảm")
        return val <= mt ? 100 : 0;
      }
    }
    if (mt === kd) return 100;
    return Math.max(0, Math.min(100, Math.round((val - kd) / (mt - kd) * 100)));
  }

  function tinhTrangThaiTD(pct: number): string {
    if (pct >= 80) return "xuat_sac";
    if (pct >= 60) return "tot";
    if (pct >= 40) return "dung_huong";
    if (pct >= 20) return "can_chu_y";
    return "chech_huong";
  }

  const TD_NHAN: Record<string, { label: string; desc: string }> = {
    xuat_sac:    { label: "✦ Vượt mục tiêu",    desc: "80 – 100%" },
    tot:         { label: "✓ Hoàn thành tốt",    desc: "60 – 79%" },
    dung_huong:  { label: "→ Đúng tiến độ",      desc: "40 – 59%" },
    can_chu_y:   { label: "⚠ Cần hỗ trợ",       desc: "20 – 39%" },
    chech_huong: { label: "✗ Cần điều chỉnh",   desc: "0 – 19%" },
  };

  async function layGoiY() {
    if (!formMT.muc_tieu_lon || formMT.muc_tieu_lon.length < 5) return;
    try {
      const r = await api.post("/api/v1/ai/goi-y-kr", { muc_tieu_lon: formMT.muc_tieu_lon, loai_okr: formMT.loai_okr });
      setGoiY(r.data.goi_y || []);
    } catch (e: any) {
      // AI gợi ý là tùy chọn - chỉ log lỗi, không hiện toast
      console.warn("AI goi y:", e.response?.data?.detail || e.message);
    }
  }

  const nhapList = mucTieuList.filter(m => m.trang_thai === "nhap");
  const activeList = mucTieuList.filter(m => m.trang_thai !== "nhap");

  return (
    <Layout menu={MENU} tieuDe="Học sinh">
      <div className="flex h-full">
        {/* Panel trái */}
        <div className="w-72 border-r bg-white flex flex-col h-full overflow-hidden">
          <div className="p-3 border-b flex items-center justify-between">
            <h2 className="font-semibold text-sm text-gray-700">Mục tiêu OKR của tôi</h2>
            <button onClick={() => { resetForm(); setShowTao(true); }}
              className="text-xs bg-orange-600 text-white px-2 py-1 rounded-lg hover:bg-orange-700">
              + Tạo mới
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {mucTieuList.length === 0 && (
              <div className="text-center py-8 text-gray-400 text-xs">Chưa có mục tiêu nào</div>
            )}
            {nhapList.length > 0 && (
              <div className="text-xs font-bold text-gray-400 uppercase px-2 py-1">Bản nháp</div>
            )}
            {nhapList.map(mt => (
              <button key={mt.id} onClick={() => chonMT(mt)}
                className={`w-full text-left p-2 rounded-lg transition-colors ${sel?.id === mt.id ? "bg-orange-50 border border-orange-300" : "hover:bg-gray-50"}`}>
                <div className="flex items-center gap-1 mb-0.5">
                  <span className="text-xs px-1.5 py-0.5 rounded-full border bg-gray-100 text-gray-500 border-gray-300">Nháp</span>
                </div>
                <p className="text-xs font-medium text-gray-800 line-clamp-2">{mt.muc_tieu_lon}</p>
                <p className="text-xs text-gray-400">{mt.ky_danh_gia?.ten_ky}</p>
              </button>
            ))}
            {activeList.length > 0 && (
              <div className="text-xs font-bold text-gray-400 uppercase px-2 py-1 mt-2">Đã nộp</div>
            )}
            {activeList.map(mt => {
              const tt = TT_STYLE[mt.trang_thai] || TT_STYLE.cho_duyet;
              const tdStyle = mt.trang_thai_tien_do ? TIEN_DO_STYLE[mt.trang_thai_tien_do] : null;
              return (
                <button key={mt.id} onClick={() => chonMT(mt)}
                  className={`w-full text-left p-2 rounded-lg transition-colors ${sel?.id === mt.id ? "bg-orange-50 border border-orange-300" : "hover:bg-gray-50"}`}>
                  <div className="flex items-center gap-1 mb-0.5 flex-wrap">
                    <span className={`text-xs px-1.5 py-0.5 rounded-full border ${tt.cls}`}>{tt.label}</span>
                    {tdStyle && <span className={`text-xs px-1.5 py-0.5 rounded-full ${tdStyle.bg} ${tdStyle.cls}`}>{tdStyle.label}</span>}
                  </div>
                  <p className="text-xs font-medium text-gray-800 line-clamp-2">{mt.muc_tieu_lon}</p>
                  {mt.trang_thai === "da_duyet" && (
                    <div className="mt-1">
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div className="bg-orange-500 h-1.5 rounded-full" style={{ width: `${mt.tien_do_tong || 0}%` }} />
                      </div>
                      <span className="text-xs text-gray-400">{mt.tien_do_tong || 0}%</span>
                    </div>
                  )}
                  <p className="text-xs text-gray-400">{mt.ky_danh_gia?.ten_ky}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Panel phải: Chi tiết */}
        <div className="flex-1 overflow-y-auto p-6">
          {!sel ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-400">
              <div className="text-5xl mb-3">🎯</div>
              <p className="font-medium">Chọn mục tiêu để xem chi tiết</p>
              <p className="text-sm">hoặc tạo mục tiêu OKR mới</p>
              <button onClick={() => router.push("/hoc-sinh/tong-quan")}
                className="mt-4 text-sm text-orange-600 underline">
                Xem tổng quan kỳ học →
              </button>
            </div>
          ) : (
            <div className="max-w-2xl mx-auto">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${TT_STYLE[sel.trang_thai]?.cls}`}>
                      {TT_STYLE[sel.trang_thai]?.label}
                    </span>
                    {sel.trang_thai_tien_do && TIEN_DO_STYLE[sel.trang_thai_tien_do] && (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${TIEN_DO_STYLE[sel.trang_thai_tien_do].bg} ${TIEN_DO_STYLE[sel.trang_thai_tien_do].cls}`}>
                        {TIEN_DO_STYLE[sel.trang_thai_tien_do].label}
                      </span>
                    )}
                    {sel.da_hoan_thanh && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">✓ Hoàn thành</span>
                    )}
                  </div>
                  <h2 className="text-xl font-bold text-gray-800">{sel.muc_tieu_lon}</h2>
                  <p className="text-sm text-gray-500 mt-0.5">
                    {sel.ky_danh_gia?.ten_ky} · {sel.loai_okr === "ca_nhan" ? "Cá nhân" : sel.loai_okr === "nhom" ? "Nhóm" : "Lớp"} · {TAN_SUAT[sel.tan_suat] || "Hàng tháng"}
                  </p>
                  {sel.nhan && <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full mt-1 inline-block">{sel.nhan}</span>}
                </div>
                <div className="flex gap-2 flex-shrink-0 ml-2 flex-wrap justify-end">
                  {sel.trang_thai === "nhap" && (
                    <>
                      <button onClick={() => moNopNhap(sel.id)}
                        className="text-xs bg-orange-600 text-white px-3 py-1.5 rounded-lg hover:bg-orange-700">
                        📤 Nộp cho GV
                      </button>
                      <button onClick={() => setShowXinXoa(true)}
                        className="text-xs border border-red-300 text-red-600 px-3 py-1.5 rounded-lg hover:bg-red-50">
                        Xóa nháp
                      </button>
                    </>
                  )}
                  {sel.trang_thai === "yeu_cau_sua" && (
                    <button onClick={() => setShowNhanBan(true)}
                      className="text-xs bg-orange-600 text-white px-3 py-1.5 rounded-lg hover:bg-orange-700">
                      Khai báo lại →
                    </button>
                  )}
                  {sel.trang_thai === "da_duyet" && !sel.da_hoan_thanh && (
                    <button onClick={() => setShowHoanThanh(true)}
                      className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700">
                      Hoàn thành OKR
                    </button>
                  )}
                  {["cho_duyet", "da_duyet"].includes(sel.trang_thai) && !sel.da_hoan_thanh && (
                    <button onClick={() => setShowXinXoa(true)}
                      className="text-xs border border-gray-300 text-gray-500 px-3 py-1.5 rounded-lg hover:bg-gray-50">
                      Xin xóa
                    </button>
                  )}
                </div>
              </div>

              {/* Nhận xét GV */}
              {sel.nhan_xet_giao_vien && (
                <div className={`p-3 rounded-xl border mb-4 text-sm ${sel.trang_thai === "yeu_cau_sua" ? "bg-red-50 border-red-200 text-red-800" : "bg-green-50 border-green-200 text-green-800"}`}>
                  <p className="font-semibold text-xs mb-1">💬 Nhận xét giáo viên:</p>
                  <p>{sel.nhan_xet_giao_vien}</p>
                </div>
              )}

              {/* Tiến độ tổng */}
              {sel.trang_thai === "da_duyet" && (
                <div className="bg-gray-50 rounded-xl p-4 mb-4 border">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-sm">Tiến độ tổng hợp</span>
                    <span className="font-bold text-orange-600 text-lg">{sel.tien_do_tong || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-orange-500 h-3 rounded-full transition-all" style={{ width: `${sel.tien_do_tong || 0}%` }} />
                  </div>
                </div>
              )}

              {/* Tabs */}
              <div className="flex gap-4 border-b mb-4">
                {(["info", "lich-su", ...(danhGia ? ["danh-gia"] : [])] as const).map(t => (
                  <button key={t} onClick={() => setTab(t as any)}
                    className={`pb-2 text-sm font-medium transition-colors ${tab === t ? "border-b-2 border-orange-600 text-orange-600" : "text-gray-500 hover:text-gray-700"}`}>
                    {t === "info" ? "Kết quả then chốt" : t === "lich-su" ? "Lịch sử cập nhật" : "⭐ Đánh giá cuối kỳ"}
                  </button>
                ))}
              </div>

              {tab === "info" && (
                <div className="space-y-3">
                  {krsOfSel.length === 0 && (
                    <div className="text-center py-6">
                      <p className="text-gray-400 text-sm mb-2">Chưa có kết quả then chốt nào</p>
                      {sel.trang_thai === "nhap" && (
                        <p className="text-xs text-gray-400">Thêm KR khi tạo hoặc chỉnh sửa OKR</p>
                      )}
                    </div>
                  )}
                  {krsOfSel.map((kr, idx) => {
                    const td = kr.tien_do_phan_tram || 0;
                    const barColor = td >= 80 ? "bg-green-500" : td >= 60 ? "bg-amber-500" : td >= 40 ? "bg-orange-400" : "bg-red-500";
                    return (
                      <div key={kr.id} className="border rounded-xl p-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-bold text-orange-600 bg-orange-50 px-2 py-0.5 rounded-full">KR {idx + 1}</span>
                              <span className="text-xs text-gray-400">{kr.xu_huong === "tang" ? "↑ Càng cao" : "↓ Càng thấp"}</span>
                            </div>
                            <p className="font-medium text-sm">{kr.noi_dung}</p>
                            <p className="text-xs text-gray-500 mt-0.5">
                              {kr.gia_tri_khoi_diem} → <strong>{kr.gia_tri_muc_tieu}</strong> {kr.don_vi}
                              {kr.gia_tri_hien_tai > 0 && ` · Hiện tại: ${kr.gia_tri_hien_tai} ${kr.don_vi}`}
                            </p>
                          </div>
                          <div className="ml-3 text-right flex-shrink-0">
                            <p className="font-bold text-lg text-gray-800">{td}%</p>
                            {sel.trang_thai === "da_duyet" && !sel.da_hoan_thanh && (
                              <button onClick={() => {
                                setKrChon(kr);
                                setGiaTri(String(kr.gia_tri_hien_tai || kr.gia_tri_khoi_diem || ""));
                                setTrangThaiTD("dung_huong");
                                setTuNhanXet("");
                                setShowCapNhat(true);
                              }}
                                className="text-xs bg-green-600 text-white px-2 py-1 rounded-lg mt-1 hover:bg-green-700">
                                📊 Báo cáo
                              </button>
                            )}
                          </div>
                        </div>
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className={`${barColor} h-2 rounded-full transition-all`} style={{ width: `${td}%` }} />
                          </div>
                        </div>
                        {kr.nhan_xet_gv && (
                          <p className="text-xs text-green-700 mt-2 bg-green-50 rounded p-1.5">💬 GV: {kr.nhan_xet_gv}</p>
                        )}
                      </div>
                    );
                  })}
                  {sel.cau_chuyen && (
                    <div className="bg-blue-50 border border-blue-100 rounded-xl p-3 mt-2">
                      <p className="text-xs font-semibold text-blue-600 mb-1">📖 Câu chuyện OKR</p>
                      <p className="text-sm text-blue-800">{sel.cau_chuyen}</p>
                    </div>
                  )}
                </div>
              )}

              {tab === "lich-su" && (
                <div className="space-y-2">
                  {lichSu.length === 0 && <p className="text-gray-400 text-sm text-center py-4">Chưa có lịch sử</p>}
                  {lichSu.map((ls, i) => {
                    const tdStyle = ls.trang_thai_tu_danh_gia ? TIEN_DO_STYLE[ls.trang_thai_tu_danh_gia] : null;
                    return (
                      <div key={i} className="flex gap-3 items-start">
                        <div className="w-2 h-2 rounded-full bg-orange-400 mt-2 flex-shrink-0" />
                        <div className="flex-1 bg-gray-50 rounded-lg p-3 text-sm">
                          <div className="flex justify-between items-start">
                            <div>
                              <span className="font-medium">Giá trị: {ls.gia_tri_dat_duoc}</span>
                              <span className="text-gray-500 text-xs ml-1">→ {ls.tien_do}%</span>
                            </div>
                            <div className="flex items-center gap-2">
                              {tdStyle && <span className={`text-xs px-1.5 py-0.5 rounded-full ${tdStyle.bg} ${tdStyle.cls}`}>{tdStyle.label}</span>}
                              <span className="text-xs text-gray-400">
                                {new Date(ls.thoi_diem || ls.ngay_tao).toLocaleDateString("vi-VN")}
                              </span>
                            </div>
                          </div>
                          {ls.tu_nhan_xet && <p className="text-gray-600 text-xs mt-1">{ls.tu_nhan_xet}</p>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {tab === "danh-gia" && danhGia && (
                <div className="space-y-4">
                  <div className="bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-200 rounded-2xl p-5">
                    <h3 className="font-bold text-orange-800 mb-3">📋 Đánh giá cuối kỳ từ giáo viên</h3>

                    {danhGia.diem_so != null && (
                      <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-500 mb-1">Điểm đánh giá</p>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">
                            {Array.from({ length: 5 }, (_, i) => (
                              <span key={i} className={i < Math.floor(danhGia.diem_so) ? "text-amber-400" : "text-gray-300"}>★</span>
                            ))}
                          </span>
                          <span className="font-bold text-orange-600 text-lg">{danhGia.diem_so}/5</span>
                        </div>
                      </div>
                    )}

                    {danhGia.trien_khai_xuat_sac && (
                      <div className="mb-3 bg-yellow-100 border border-yellow-300 rounded-lg px-3 py-2 text-sm text-yellow-800 font-semibold">
                        🏆 Được giáo viên ghi nhận triển khai xuất sắc!
                      </div>
                    )}

                    <div className="mb-3">
                      <p className="text-xs font-semibold text-gray-500 mb-1">Nhận xét của giáo viên</p>
                      <p className="text-sm text-gray-800 bg-white rounded-lg p-3 border">{danhGia.nhan_xet_gv}</p>
                    </div>

                    {danhGia.ky_vong_ky_tiep && (
                      <div>
                        <p className="text-xs font-semibold text-gray-500 mb-1">🔭 Kỳ vọng kỳ tiếp theo</p>
                        <p className="text-sm text-blue-800 bg-blue-50 rounded-lg p-3 border border-blue-100">{danhGia.ky_vong_ky_tiep}</p>
                      </div>
                    )}
                  </div>

                  {danhGia.phan_hoi_ph && (
                    <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
                      <p className="text-xs font-semibold text-purple-600 mb-1">👨‍👩‍👦 Ý kiến gia đình</p>
                      <p className="text-sm text-purple-800">{danhGia.phan_hoi_ph}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* DIALOG: Tạo OKR mới */}
      <Dialog open={showTao} onOpenChange={v => { if (!v) { setShowTao(false); resetForm(); } }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Tạo mục tiêu OKR mới</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Kỳ đánh giá <span className="text-red-500">*</span></Label>
                <select className="w-full border rounded-lg px-3 py-2 text-sm mt-1"
                  value={formMT.ky_danh_gia_id} onChange={e => setFormMT({ ...formMT, ky_danh_gia_id: e.target.value })}>
                  <option value="">-- Chọn kỳ --</option>
                  {kyList.map(k => <option key={k.id} value={k.id}>{k.ten_ky}</option>)}
                </select>
              </div>
              <div>
                <Label>Loại OKR</Label>
                <select className="w-full border rounded-lg px-3 py-2 text-sm mt-1"
                  value={formMT.loai_okr} onChange={e => setFormMT({ ...formMT, loai_okr: e.target.value })}>
                  <option value="ca_nhan">Cá nhân</option>
                  <option value="nhom">Nhóm</option>
                  <option value="lop">Lớp</option>
                </select>
              </div>
            </div>

            <div>
              <Label>Mục tiêu lớn (Objective) <span className="text-red-500">*</span></Label>
              <Textarea className="mt-1" rows={2} placeholder="Ví dụ: Cải thiện kết quả học tập học kỳ này..."
                value={formMT.muc_tieu_lon}
                onChange={e => setFormMT({ ...formMT, muc_tieu_lon: e.target.value })}
                onBlur={layGoiY} />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Tần suất cập nhật</Label>
                <div className="flex gap-3 mt-1">
                  {Object.entries(TAN_SUAT).map(([v, l]) => (
                    <label key={v} className="flex items-center gap-1 text-sm cursor-pointer">
                      <input type="radio" name="tan_suat" value={v} checked={formMT.tan_suat === v}
                        onChange={() => setFormMT({ ...formMT, tan_suat: v })} />
                      {l}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <Label>Hạn hoàn thành</Label>
                <div className="flex gap-2 mt-1">
                  <Input type="date" className="flex-1" value={formMT.han_hoan_thanh}
                    onChange={e => setFormMT({ ...formMT, han_hoan_thanh: e.target.value })} />
                  {(() => {
                    const kyChon = kyList.find(k => k.id === formMT.ky_danh_gia_id);
                    return kyChon?.ngay_ket_thuc ? (
                      <button type="button"
                        onClick={() => setFormMT({ ...formMT, han_hoan_thanh: kyChon.ngay_ket_thuc })}
                        className="text-xs bg-gray-100 border border-gray-300 text-gray-700 px-2 py-1 rounded-lg hover:bg-gray-200 whitespace-nowrap">
                        📅 Ngày cuối kỳ
                      </button>
                    ) : null;
                  })()}
                </div>
              </div>
            </div>

            {/* KRs */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Kết quả then chốt (KR) <span className="text-red-500">*</span></Label>
                {krsForm.length < 5 && (
                  <button onClick={() => setKrsForm(p => [...p, { ...EMPTY_KR }])}
                    className="text-xs text-orange-600 border border-orange-300 px-2 py-1 rounded-lg hover:bg-orange-50">
                    + Thêm KR ({krsForm.length}/5)
                  </button>
                )}
              </div>

              {goiY.length > 0 && (
                <div className="mb-2 p-2 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-xs font-semibold text-amber-700 mb-1">✨ AI gợi ý KR:</p>
                  {goiY.map((g, i) => (
                    <button key={i} onClick={() => setKrsForm(p => {
                      const idx = p.findIndex(k => !k.noi_dung);
                      if (idx >= 0) { const n = [...p]; n[idx] = { ...n[idx], noi_dung: g }; return n; }
                      return p.length < 5 ? [...p, { ...EMPTY_KR, noi_dung: g }] : p;
                    })} className="block w-full text-left text-xs text-amber-800 hover:bg-amber-100 rounded p-1">
                      → {g}
                    </button>
                  ))}
                </div>
              )}

              <div className="space-y-3">
                {krsForm.map((kr, i) => (
                  <div key={i} className="border rounded-xl p-3 bg-gray-50">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-bold text-orange-600">KR {i + 1}</span>
                      {krsForm.length > 1 && (
                        <button onClick={() => setKrsForm(p => p.filter((_, j) => j !== i))}
                          className="text-xs text-red-400 hover:text-red-600">✕ Xóa</button>
                      )}
                    </div>
                    <Input className="mb-2 text-sm" placeholder="Nội dung kết quả then chốt..."
                      value={kr.noi_dung} onChange={e => updateKR(i, "noi_dung", e.target.value)} />
                    <div className="grid grid-cols-2 gap-2 mb-2">
                      <div>
                        <label className="text-xs text-gray-500">Loại KR</label>
                        <select className="w-full border rounded px-2 py-1 text-xs mt-0.5"
                          value={kr.loai_kr} onChange={e => updateKR(i, "loai_kr", e.target.value)}>
                          <option value="so">Số (VD: 8.0 điểm)</option>
                          <option value="phan_tram">Phần trăm (%)</option>
                          <option value="moc_viec">Mốc việc (0/100%)</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">Xu hướng</label>
                        <div className="flex gap-2 mt-1">
                          <label className="flex items-center gap-1 text-xs cursor-pointer">
                            <input type="radio" checked={kr.xu_huong === "tang"} onChange={() => updateKR(i, "xu_huong", "tang")} />
                            ↑ Tăng
                          </label>
                          <label className="flex items-center gap-1 text-xs cursor-pointer">
                            <input type="radio" checked={kr.xu_huong === "giam"} onChange={() => updateKR(i, "xu_huong", "giam")} />
                            ↓ Giảm
                          </label>
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <label className="text-xs text-gray-500">Khởi điểm</label>
                        <Input type="number" className="text-xs mt-0.5" placeholder="0"
                          value={kr.gia_tri_khoi_diem} onChange={e => updateKR(i, "gia_tri_khoi_diem", e.target.value)} />
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">Chỉ tiêu <span className="text-red-500">*</span></label>
                        <Input type="number" className="text-xs mt-0.5" placeholder="100"
                          value={kr.gia_tri_muc_tieu} onChange={e => updateKR(i, "gia_tri_muc_tieu", e.target.value)} />
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">Đơn vị <span className="text-red-500">*</span></label>
                        <Input className="text-xs mt-0.5" placeholder="điểm/cuốn..."
                          value={kr.don_vi} onChange={e => updateKR(i, "don_vi", e.target.value)} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Nhãn (tùy chọn)</Label>
                <Input className="mt-1 text-sm" placeholder="VD: Học tập, Thể thao..."
                  value={formMT.nhan} onChange={e => setFormMT({ ...formMT, nhan: e.target.value })} />
              </div>
              <div>
                <Label>Câu chuyện (tùy chọn)</Label>
                <Input className="mt-1 text-sm" placeholder="Mô tả thêm về mục tiêu..."
                  value={formMT.cau_chuyen} onChange={e => setFormMT({ ...formMT, cau_chuyen: e.target.value })} />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button onClick={luuNhap} disabled={saving}
                className="flex-1 border-2 border-orange-600 text-orange-600 py-2.5 rounded-xl font-semibold hover:bg-orange-50 disabled:opacity-50">
                {saving ? "Đang lưu..." : "💾 Lưu nháp"}
              </button>
              <button onClick={moNop} disabled={saving}
                className="flex-1 bg-orange-600 text-white py-2.5 rounded-xl font-semibold hover:bg-orange-700 disabled:opacity-50">
                {saving ? "Đang xử lý..." : "📤 Xác nhận & Nộp"}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Checklist tự kiểm trước nộp */}
      <Dialog open={showChecklist} onOpenChange={v => { if (!v) setShowChecklist(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>✅ Kiểm tra chất lượng mục tiêu</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <p className="text-sm text-gray-500">Vui lòng xem lại các câu hỏi dưới đây trước khi nộp:</p>
            {CHECKLIST_HS.map((q, i) => (
              <div key={i} className="border rounded-lg p-3">
                <p className="text-sm font-medium mb-2">{i + 1}. {q}</p>
                <div className="flex gap-3 flex-wrap">
                  {CHECKLIST_OPT.map((opt, j) => (
                    <label key={j} className="flex items-center gap-1 text-xs cursor-pointer">
                      <input type="radio" name={`q${i}`} checked={checklistAns[i] === j}
                        onChange={() => setChecklistAns(p => ({ ...p, [i]: j }))} />
                      {opt}
                    </label>
                  ))}
                </div>
              </div>
            ))}
            <p className="text-xs text-gray-400">ℹ Trả lời trung thực giúp giáo viên hỗ trợ bạn tốt hơn. Checklist không ảnh hưởng đến duyệt OKR.</p>
            <div className="flex gap-3">
              <button onClick={() => setShowChecklist(false)}
                className="flex-1 border rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Quay lại</button>
              <button onClick={xacNhanNop} disabled={saving}
                className="flex-1 bg-orange-600 text-white py-2 rounded-xl text-sm font-semibold hover:bg-orange-700 disabled:opacity-50">
                {saving ? "Đang nộp..." : "Xác nhận & Nộp"}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Cập nhật tiến độ KR */}
      <Dialog open={showCapNhat} onOpenChange={setShowCapNhat}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>📊 Báo cáo tiến độ</DialogTitle></DialogHeader>
          {krChon && (
            <div className="space-y-3 mt-2">
              <div className="p-3 bg-orange-50 rounded-xl border border-orange-200 text-sm">
                <p className="font-medium">{krChon.noi_dung}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {krChon.gia_tri_khoi_diem} → {krChon.gia_tri_muc_tieu} {krChon.don_vi}
                  {krChon.xu_huong === "giam" ? " (càng thấp càng tốt)" : " (càng cao càng tốt)"}
                </p>
              </div>
              <div>
                <Label>Giá trị hiện tại ({krChon.don_vi})</Label>
                <Input type="number" className="mt-1"
                  placeholder={`${krChon.gia_tri_khoi_diem} → ${krChon.gia_tri_muc_tieu}`}
                  value={giaTri} onChange={e => setGiaTri(e.target.value)} />
                {giaTri && (
                  <p className="text-xs text-orange-600 mt-1">
                    Tiến độ ước tính: {tinhTienDo(krChon, parseFloat(giaTri))}%
                  </p>
                )}
              </div>
              {giaTri && (() => {
                const pct = tinhTienDo(krChon, parseFloat(giaTri));
                const status = tinhTrangThaiTD(pct);
                const s = TIEN_DO_STYLE[status];
                const td = TD_NHAN[status];
                return (
                  <div className="bg-gray-50 border rounded-xl p-3">
                    <p className="text-xs text-gray-500 mb-1">Nhận xét tự động</p>
                    <div className="flex items-center gap-2">
                      <span className={`text-sm px-3 py-1 rounded-full font-medium ${s.bg} ${s.cls}`}>{td.label}</span>
                      <span className="text-xs text-gray-400">{td.desc}</span>
                    </div>
                  </div>
                );
              })()}
              <div>
                <Label>Tự nhận xét (tùy chọn)</Label>
                <Textarea className="mt-1" rows={2} placeholder="Chia sẻ những gì bạn đã làm được..."
                  value={tuNhanXet} onChange={e => setTuNhanXet(e.target.value)} />
              </div>
              <button onClick={capNhatKR} disabled={saving}
                className="w-full bg-green-600 text-white py-2.5 rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50">
                {saving ? "Đang lưu..." : "Lưu cập nhật"}
              </button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* DIALOG: Hoàn thành OKR */}
      <Dialog open={showHoanThanh} onOpenChange={setShowHoanThanh}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>🏁 Hoàn thành OKR cuối kỳ</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-2 text-sm">
            <p className="text-gray-500">Đánh dấu OKR này đã hoàn thành. Giáo viên sẽ có thể chấm điểm sau khi bạn xác nhận.</p>
            <div>
              <Label>Đánh giá tổng kết của bạn</Label>
              <div className="grid grid-cols-1 gap-1 mt-1">
                {Object.entries(TIEN_DO_STYLE).map(([v, s]) => (
                  <label key={v} className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer border-2 transition-all ${ttHoanThanh === v ? "border-blue-400 bg-blue-50" : "border-transparent"}`}>
                    <input type="radio" name="tt_hoan_thanh" value={v} checked={ttHoanThanh === v}
                      onChange={() => setTtHoanThanh(v)} className="sr-only" />
                    <span className={`text-xs px-2 py-0.5 rounded-full ${s.bg} ${s.cls}`}>{s.label}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <Label>Tự nhận xét cuối kỳ (tùy chọn)</Label>
              <Textarea rows={3} className="mt-1" placeholder="Chia sẻ cảm nhận về hành trình thực hiện OKR..."
                value={nxHoanThanh} onChange={e => setNxHoanThanh(e.target.value)} />
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={() => setShowHoanThanh(false)}
                className="flex-1 border rounded-xl py-2 text-gray-600 hover:bg-gray-50">Hủy</button>
              <button onClick={hoanThanh} disabled={saving}
                className="flex-1 bg-blue-600 text-white py-2 rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50">
                {saving ? "Đang lưu..." : "Xác nhận hoàn thành"}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Nhân bản OKR */}
      <Dialog open={showNhanBan} onOpenChange={setShowNhanBan}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Khai báo lại OKR</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-2 text-sm">
            {sel?.nhan_xet_giao_vien && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-red-700 mb-1">⚠ Nhận xét từ chối của giáo viên:</p>
                <p className="text-red-800">{sel.nhan_xet_giao_vien}</p>
              </div>
            )}
            <p className="text-gray-600">Nhân bản sẽ tạo bản sao OKR này ở trạng thái nháp để bạn chỉnh sửa và nộp lại.</p>
            <div className="flex gap-3 pt-1">
              <button onClick={() => setShowNhanBan(false)}
                className="flex-1 border rounded-xl py-2 text-gray-600 hover:bg-gray-50">Hủy</button>
              <button onClick={nhanBanOKR} disabled={saving}
                className="flex-1 bg-orange-600 text-white py-2 rounded-xl font-semibold hover:bg-orange-700 disabled:opacity-50">
                {saving ? "Đang nhân bản..." : "Nhân bản & Chỉnh sửa"}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Xóa / Xin xóa */}
      <Dialog open={showXinXoa} onOpenChange={setShowXinXoa}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{sel?.trang_thai === "nhap" ? "Xóa bản nháp?" : "Gửi yêu cầu xóa?"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 mt-2 text-sm text-gray-600">
            {sel?.trang_thai === "nhap"
              ? <p>Bản nháp sẽ bị xóa vĩnh viễn. Thao tác không thể hoàn tác.</p>
              : <p>Yêu cầu xóa sẽ được gửi đến giáo viên. OKR vẫn hiển thị cho đến khi GV đồng ý.</p>
            }
            <div className="flex gap-3">
              <button onClick={() => setShowXinXoa(false)}
                className="flex-1 border rounded-xl py-2 hover:bg-gray-50">Hủy</button>
              <button onClick={xinXoa}
                className="flex-1 bg-red-600 text-white py-2 rounded-xl hover:bg-red-700">
                {sel?.trang_thai === "nhap" ? "Xóa" : "Gửi yêu cầu"}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
