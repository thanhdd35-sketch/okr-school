"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const MENU = [
  { href: "/quan-tri", label: "Tổng quan" },
  { href: "/quan-tri/giao-vien", label: "Giáo viên" },
  { href: "/quan-tri/ky-danh-gia", label: "Kỳ đánh giá" },
  { href: "/quan-tri/nhat-ky", label: "Nhật ký" },
];

export default function QuanTriGiaoVienPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [gvList, setGvList] = useState<any[]>([]);
  const [selGV, setSelGV] = useState<any>(null);
  const [hsList, setHsList] = useState<any[]>([]);
  const [showThem, setShowThem] = useState(false);
  const [showSua, setShowSua] = useState(false);
  const [showMK, setShowMK] = useState(false);
  const [form, setForm] = useState({ ho_ten: "", email: "", mat_khau: "", ten_lop: "", si_so: "" });
  const [formSua, setFormSua] = useState({ ho_ten: "", email: "", ten_lop: "", si_so: "" });
  const [search, setSearch] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { khoiTao(); }, []);
  useEffect(() => {
    if (!nguoiDung) return;
    if (nguoiDung.vai_tro !== "quan_tri") { router.push("/dang-nhap"); return; }
    fetchGV();
  }, [nguoiDung]);

  function fetchGV() {
    api.get("/api/v1/quan-tri/danh-sach-nguoi-dung?vai_tro=giao_vien")
      .then(r => setGvList(r.data)).catch(() => setGvList([]));
  }

  async function chonGV(gv: any) {
    setSelGV(gv);
    if (gv.ten_lop) {
      try {
        const r = await api.get(`/api/v1/nguoi-dung/hoc-sinh/${encodeURIComponent(gv.ten_lop)}`);
        setHsList(r.data);
      } catch { setHsList([]); }
    } else {
      setHsList([]);
    }
  }

  async function themGV() {
    if (!form.ho_ten || !form.email || !form.mat_khau) {
      toast.error("Điền đầy đủ họ tên, email, mật khẩu"); return;
    }
    try {
      await api.post("/api/v1/quan-tri/tao-giao-vien", {
        ho_ten: form.ho_ten, email: form.email, mat_khau: form.mat_khau,
        ten_lop: form.ten_lop || null, si_so: form.si_so ? parseInt(form.si_so) : null,
      });
      toast.success("Đã thêm giáo viên!");
      setShowThem(false); setForm({ ho_ten: "", email: "", mat_khau: "", ten_lop: "", si_so: "" });
      fetchGV();
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi thêm giáo viên"); }
  }

  async function suaGV() {
    if (!selGV) return;
    try {
      await api.put(`/api/v1/quan-tri/cap-nhat-nguoi-dung/${selGV.id}`, {
        ho_ten: formSua.ho_ten, ten_lop: formSua.ten_lop,
        si_so: formSua.si_so ? parseInt(formSua.si_so) : null,
      });
      toast.success("Đã cập nhật!");
      setShowSua(false);
      fetchGV();
      const r = await api.get("/api/v1/quan-tri/danh-sach-nguoi-dung?vai_tro=giao_vien");
      const updated = r.data.find((g: any) => g.id === selGV.id);
      if (updated) chonGV(updated);
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi cập nhật"); }
  }

  async function resetMKGV(id: string, ten: string) {
    if (!confirm(`Reset mật khẩu của ${ten} về mặc định Okr@12345?`)) return;
    try {
      await api.put(`/api/v1/nguoi-dung/${id}/reset-mat-khau`);
      toast.success(`Đã reset mật khẩu ${ten} về: Okr@12345`);
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi reset"); }
  }

  async function xoaGV(id: string) {
    if (!confirm("Xác nhận xóa tài khoản giáo viên này?")) return;
    try {
      await api.delete(`/api/v1/nguoi-dung/${id}`);
      toast.success("Đã xóa tài khoản giáo viên");
      setSelGV(null); setHsList([]);
      fetchGV();
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi xóa"); }
  }

  async function xoaHS(id: string) {
    if (!confirm("Xác nhận xóa tài khoản học sinh này?")) return;
    try {
      await api.delete(`/api/v1/nguoi-dung/${id}`);
      toast.success("Đã xóa tài khoản học sinh");
      if (selGV) chonGV(selGV);
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi xóa"); }
  }

  async function uploadExcel(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]; if (!file) return;
    setUploading(true);
    const fd = new FormData(); fd.append("file", file);
    try {
      const r = await api.post("/api/v1/nguoi-dung/nhap-danh-sach?vai_tro=giao_vien", fd, { headers: { "Content-Type": "multipart/form-data" } });
      const sl = r.data.thanh_cong || 0;
      const loi = r.data.loi || [];
      toast.success(`Đã nhập ${sl} giáo viên từ Excel!${loi.length ? ` (${loi.length} dòng lỗi)` : ""}`);
      fetchGV();
    } catch (e: any) { toast.error(e.response?.data?.detail || "Lỗi nhập Excel"); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  const filtered = gvList.filter(gv =>
    gv.ho_ten?.toLowerCase().includes(search.toLowerCase()) ||
    gv.email?.toLowerCase().includes(search.toLowerCase()) ||
    gv.ten_lop?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Layout menu={MENU} tieuDe="Quản trị viên">
      <div className="flex h-full">
        {/* LEFT: Danh sách giáo viên */}
        <div className="w-80 border-r bg-white flex flex-col flex-shrink-0">
          <div className="p-4 bg-orange-700 text-white">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="font-bold text-sm">Danh sách giáo viên</h2>
                <p className="text-xs text-orange-200 mt-0.5">{gvList.length} giáo viên</p>
              </div>
              <button onClick={() => setShowThem(true)}
                className="bg-white text-orange-700 text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-orange-50">
                Thêm mới
              </button>
            </div>
            <div>
              <input ref={fileRef} type="file" accept=".xlsx,.xls" className="hidden" onChange={uploadExcel} />
              <button onClick={() => fileRef.current?.click()} disabled={uploading}
                className="w-full border border-white/40 text-white text-xs py-1.5 rounded-lg hover:bg-white/10 disabled:opacity-50 mb-1">
                {uploading ? "Đang nhập..." : "Nhập từ Excel"}
              </button>
              <a href="/mau-giao-vien.xlsx" download
                className="block w-full text-center border border-white/30 text-orange-200 text-xs py-1.5 rounded-lg hover:bg-white/10">
                Tải file mẫu Excel
              </a>
            </div>
          </div>
          <div className="p-2 border-b">
            <Input placeholder="Tìm kiếm..." value={search}
              onChange={e => setSearch(e.target.value)} className="text-sm h-8" />
          </div>
          <div className="flex-1 overflow-y-auto divide-y">
            {filtered.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">Chưa có giáo viên</div>
            ) : filtered.map(gv => (
              <div key={gv.id} onClick={() => chonGV(gv)}
                className={`p-3 cursor-pointer hover:bg-orange-50 transition-colors ${selGV?.id === gv.id ? "bg-orange-50 border-l-4 border-orange-600" : "border-l-4 border-transparent"}`}>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-orange-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                    {gv.ho_ten?.[0] || "?"}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">{gv.ho_ten}</div>
                    <div className="text-xs text-gray-400 truncate">
                      {gv.ten_lop ? `Lớp ${gv.ten_lop}` : "Chưa phân lớp"} {gv.si_so ? `· ${gv.si_so} HS` : ""}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT: Chi tiết giáo viên + học sinh */}
        <div className="flex-1 overflow-y-auto bg-gray-50">
          {!selGV ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-400">
                <p className="font-medium">Chọn giáo viên để xem chi tiết</p>
                <p className="text-sm mt-1">và danh sách học sinh trong lớp</p>
              </div>
            </div>
          ) : (
            <div className="p-6">
              {/* GV info card */}
              <div className="bg-white rounded-xl border shadow-sm p-5 mb-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-full bg-orange-600 flex items-center justify-center text-white text-2xl font-bold">
                      {selGV.ho_ten?.[0] || "?"}
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-gray-900">{selGV.ho_ten}</h2>
                      <p className="text-sm text-gray-500">{selGV.email}</p>
                      <div className="flex gap-3 mt-1 text-xs text-gray-500">
                        <span>Lớp chủ nhiệm: <strong className="text-orange-700">{selGV.ten_lop || "Chưa phân công"}</strong></span>
                        {selGV.si_so && <span>Sĩ số: <strong>{selGV.si_so}</strong></span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => { setFormSua({ ho_ten: selGV.ho_ten, email: selGV.email, ten_lop: selGV.ten_lop || "", si_so: selGV.si_so?.toString() || "" }); setShowSua(true); }}
                      className="text-xs border border-orange-300 text-orange-600 px-3 py-1.5 rounded-lg hover:bg-orange-50">
                      Sửa thông tin
                    </button>
                    <button onClick={() => resetMKGV(selGV.id, selGV.ho_ten)}
                      className="text-xs border border-blue-300 text-blue-500 px-3 py-1.5 rounded-lg hover:bg-blue-50">
                      Reset mật khẩu
                    </button>
                    <button onClick={() => xoaGV(selGV.id)}
                      className="text-xs border border-red-300 text-red-500 px-3 py-1.5 rounded-lg hover:bg-red-50">
                      Xóa tài khoản
                    </button>
                  </div>
                </div>
              </div>

              {/* Danh sách học sinh */}
              <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
                <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
                  <h3 className="font-semibold text-gray-800 text-sm">
                    Danh sách học sinh lớp {selGV.ten_lop || "?"}
                    <span className="ml-2 text-gray-400 font-normal">({hsList.length} học sinh)</span>
                  </h3>
                </div>
                {!selGV.ten_lop ? (
                  <div className="text-center py-8 text-gray-400 text-sm">Giáo viên chưa được phân lớp</div>
                ) : hsList.length === 0 ? (
                  <div className="text-center py-8 text-gray-400 text-sm">Lớp này chưa có học sinh</div>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Họ tên</th>
                        <th className="text-left px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Email</th>
                        <th className="text-right px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {hsList.map(hs => (
                        <tr key={hs.id} className="hover:bg-gray-50">
                          <td className="px-4 py-2.5 font-medium text-gray-900">{hs.ho_ten}</td>
                          <td className="px-4 py-2.5 text-gray-500">{hs.email}</td>
                          <td className="px-4 py-2.5 text-right">
                            <button onClick={() => xoaHS(hs.id)}
                              className="text-xs text-red-500 border border-red-200 px-2 py-1 rounded hover:bg-red-50">
                              Xóa
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* DIALOG: Thêm GV */}
      <Dialog open={showThem} onOpenChange={setShowThem}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Thêm giáo viên mới</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-2">
            <div><Label>Họ tên *</Label><Input className="mt-1" value={form.ho_ten} onChange={e => setForm({...form, ho_ten: e.target.value})} /></div>
            <div><Label>Email *</Label><Input className="mt-1" type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} /></div>
            <div>
              <Label>Mật khẩu *</Label>
              <div className="relative mt-1">
                <Input type={showMK ? "text" : "password"} value={form.mat_khau}
                  onChange={e => setForm({...form, mat_khau: e.target.value})} />
                <button type="button" onClick={() => setShowMK(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700">
                  {showMK ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Lớp chủ nhiệm</Label><Input className="mt-1" placeholder="10A1" value={form.ten_lop} onChange={e => setForm({...form, ten_lop: e.target.value})} /></div>
              <div><Label>Sĩ số</Label><Input className="mt-1" type="number" placeholder="35" value={form.si_so} onChange={e => setForm({...form, si_so: e.target.value})} /></div>
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={themGV} className="flex-1 bg-orange-600 hover:bg-orange-700 text-white py-2.5 rounded-xl font-semibold text-sm">Thêm</button>
              <button onClick={() => setShowThem(false)} className="flex-1 border rounded-xl py-2.5 text-gray-600 hover:bg-gray-50 text-sm">Hủy</button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Sửa GV */}
      <Dialog open={showSua} onOpenChange={setShowSua}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Sửa thông tin giáo viên</DialogTitle></DialogHeader>
          <div className="space-y-3 mt-2">
            <div><Label>Họ tên</Label><Input className="mt-1" value={formSua.ho_ten} onChange={e => setFormSua({...formSua, ho_ten: e.target.value})} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Lớp CN</Label><Input className="mt-1" value={formSua.ten_lop} onChange={e => setFormSua({...formSua, ten_lop: e.target.value})} /></div>
              <div><Label>Sĩ số</Label><Input className="mt-1" type="number" value={formSua.si_so} onChange={e => setFormSua({...formSua, si_so: e.target.value})} /></div>
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={suaGV} className="flex-1 bg-orange-600 hover:bg-orange-700 text-white py-2.5 rounded-xl font-semibold text-sm">Lưu</button>
              <button onClick={() => setShowSua(false)} className="flex-1 border rounded-xl py-2.5 text-gray-600 hover:bg-gray-50 text-sm">Hủy</button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
