"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";

const MENU = [
  { href: "/giao-vien", label: "Bảng theo dõi lớp" },
  { href: "/giao-vien/hoc-sinh", label: "Danh sách học sinh" },
  { href: "/giao-vien/mau", label: "Mẫu mục tiêu" },
  { href: "/giao-vien/bao-cao", label: "Xuất báo cáo" },
];

const LOAI_OKR: Record<string, string> = { ca_nhan: "Cá nhân", nhom: "Nhóm", lop: "Cả lớp" };
const EMPTY = { ten_mau: "", muc_tieu_lon_mau: "", ket_qua_then_chot_mau: "", don_vi_mac_dinh: "", loai_okr: "ca_nhan" };

export default function MauGVPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [mauList, setMauList] = useState<any[]>([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => { khoiTao(); }, []);

  useEffect(() => {
    if (!nguoiDung) return;
    if (!["giao_vien", "quan_tri"].includes(nguoiDung.vai_tro)) { router.push("/dang-nhap"); return; }
    fetchMau();
  }, [nguoiDung]);

  async function fetchMau() {
    const r = await api.get("/api/v1/mau-muc-tieu/");
    setMauList(r.data);
  }

  function moTao() { setEditing(null); setForm(EMPTY); setShowDialog(true); }
  function moSua(m: any) {
    setEditing(m);
    setForm({
      ten_mau: m.ten_mau, muc_tieu_lon_mau: m.muc_tieu_lon_mau,
      ket_qua_then_chot_mau: m.ket_qua_then_chot_mau,
      don_vi_mac_dinh: m.don_vi_mac_dinh, loai_okr: m.loai_okr,
    });
    setShowDialog(true);
  }

  async function luu() {
    if (!form.ten_mau || !form.muc_tieu_lon_mau) { toast.error("Điền tên mẫu và mục tiêu"); return; }
    setSaving(true);
    try {
      const data = { ...form, ten_lop: nguoiDung?.ten_lop };
      if (editing) {
        await api.put(`/api/v1/mau-muc-tieu/${editing.id}`, data);
        toast.success("Đã cập nhật mẫu!");
      } else {
        await api.post("/api/v1/mau-muc-tieu/", data);
        toast.success("Đã tạo mẫu mới!");
      }
      setShowDialog(false); fetchMau();
    } catch (err: any) { toast.error(err.response?.data?.detail || "Lỗi"); }
    finally { setSaving(false); }
  }

  async function xoa(id: string) {
    if (!confirm("Ẩn mẫu mục tiêu này?")) return;
    await api.delete(`/api/v1/mau-muc-tieu/${id}`);
    toast.success("Đã ẩn mẫu");
    fetchMau();
  }

  const filtered = mauList.filter(m =>
    m.ten_mau.toLowerCase().includes(search.toLowerCase()) ||
    m.muc_tieu_lon_mau.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Layout menu={MENU} tieuDe="Giáo viên chủ nhiệm">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">📋 Mẫu mục tiêu</h2>
          <Button onClick={moTao} className="bg-orange-600 hover:bg-orange-700">+ Tạo mẫu mới</Button>
        </div>
        <p className="text-sm text-gray-500 mb-4">Tạo mẫu để học sinh tham khảo khi đặt mục tiêu</p>

        <Input className="mb-4 max-w-sm" placeholder="🔍 Tìm kiếm mẫu..."
          value={search} onChange={e => setSearch(e.target.value)} />

        {filtered.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <div className="text-4xl mb-3">📋</div>
              <p className="text-gray-500">Chưa có mẫu mục tiêu nào</p>
              <Button onClick={moTao} className="mt-4 bg-orange-600 hover:bg-orange-700">Tạo mẫu đầu tiên</Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filtered.map(m => (
              <Card key={m.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-800">{m.ten_mau}</h3>
                      <span className="text-xs px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full">
                        {LOAI_OKR[m.loai_okr] || m.loai_okr}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => moSua(m)} className="text-xs text-orange-600 hover:underline">Sửa</button>
                      <button onClick={() => xoa(m.id)} className="text-xs text-red-500 hover:underline">Ẩn</button>
                    </div>
                  </div>
                  <div className="mt-2 space-y-1 text-sm text-gray-600">
                    <div><span className="font-medium">Mục tiêu:</span> {m.muc_tieu_lon_mau}</div>
                    <div><span className="font-medium">KR:</span> {m.ket_qua_then_chot_mau}</div>
                    <div><span className="font-medium">Đơn vị:</span> {m.don_vi_mac_dinh}</div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editing ? "Sửa mẫu" : "Tạo mẫu mục tiêu mới"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 mt-2">
            <div>
              <Label>Tên mẫu *</Label>
              <Input className="mt-1" placeholder="VD: Cải thiện điểm số môn Toán"
                value={form.ten_mau} onChange={e => setForm({ ...form, ten_mau: e.target.value })} />
            </div>
            <div>
              <Label>Loại mục tiêu</Label>
              <select className="w-full border rounded-md px-3 py-2 text-sm mt-1"
                value={form.loai_okr} onChange={e => setForm({ ...form, loai_okr: e.target.value })}>
                <option value="ca_nhan">Cá nhân</option>
                <option value="nhom">Nhóm</option>
                <option value="lop">Cả lớp</option>
              </select>
            </div>
            <div>
              <Label>Mục tiêu lớn *</Label>
              <Input className="mt-1" placeholder="VD: Nâng cao kết quả học tập môn Toán"
                value={form.muc_tieu_lon_mau} onChange={e => setForm({ ...form, muc_tieu_lon_mau: e.target.value })} />
            </div>
            <div>
              <Label>Kết quả then chốt</Label>
              <Input className="mt-1" placeholder="VD: Đạt điểm TB từ 7.0 trở lên"
                value={form.ket_qua_then_chot_mau} onChange={e => setForm({ ...form, ket_qua_then_chot_mau: e.target.value })} />
            </div>
            <div>
              <Label>Đơn vị mặc định</Label>
              <Input className="mt-1" placeholder="điểm / cuốn / buổi / %"
                value={form.don_vi_mac_dinh} onChange={e => setForm({ ...form, don_vi_mac_dinh: e.target.value })} />
            </div>
            <div className="flex gap-3 pt-2">
              <Button onClick={luu} disabled={saving} className="flex-1 bg-orange-600 hover:bg-orange-700">
                {saving ? "Đang lưu..." : editing ? "Cập nhật" : "Tạo mẫu"}
              </Button>
              <Button variant="outline" onClick={() => setShowDialog(false)} className="flex-1">Hủy</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
