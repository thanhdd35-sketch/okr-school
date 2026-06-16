"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const MENU = [
  { href: "/quan-tri", label: "Tổng quan" },
  { href: "/quan-tri/giao-vien", label: "Giáo viên" },
  { href: "/quan-tri/ky-danh-gia", label: "Kỳ đánh giá" },
  { href: "/quan-tri/nhat-ky", label: "Nhật ký" },
];

const TRANG_THAI_LABEL: Record<string, { label: string; color: string }> = {
  khoa: { label: "Chưa mở", color: "bg-amber-100 text-amber-700" },
  mo:   { label: "Đang mở", color: "bg-green-100 text-green-700" },
};

const EMPTY_FORM = { ten_ky: "", ngay_bat_dau: "", ngay_ket_thuc: "" };

export default function KyDanhGiaPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [kyList, setKyList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => { khoiTao(); }, []);

  useEffect(() => {
    if (!nguoiDung) return;
    if (nguoiDung.vai_tro !== "quan_tri") { router.push("/dang-nhap"); return; }
    fetchKy();
  }, [nguoiDung]);

  async function fetchKy() {
    setLoading(true);
    try {
      const r = await api.get("/api/v1/ky-danh-gia/");
      setKyList(r.data);
    } catch { toast.error("Không tải được kỳ đánh giá"); }
    finally { setLoading(false); }
  }

  function moTaoMoi() { setEditing(null); setForm(EMPTY_FORM); setShowDialog(true); }

  function moSua(ky: any) {
    setEditing(ky);
    setForm({
      ten_ky: ky.ten_ky,
      ngay_bat_dau: ky.ngay_bat_dau?.slice(0, 10) || "",
      ngay_ket_thuc: ky.ngay_ket_thuc?.slice(0, 10) || "",
    });
    setShowDialog(true);
  }

  async function luuKy() {
    if (!form.ten_ky || !form.ngay_bat_dau || !form.ngay_ket_thuc) {
      toast.error("Vui lòng điền đầy đủ tên kỳ, ngày bắt đầu, ngày kết thúc"); return;
    }
    setSaving(true);
    try {
      if (editing) {
        await api.put(`/api/v1/ky-danh-gia/${editing.id}`, form);
        toast.success("Đã cập nhật kỳ đánh giá!");
      } else {
        await api.post("/api/v1/ky-danh-gia/", form);
        toast.success("Đã tạo kỳ đánh giá mới!");
      }
      setShowDialog(false); fetchKy();
    } catch (err: any) { toast.error(err.response?.data?.detail || "Lỗi lưu kỳ đánh giá"); }
    finally { setSaving(false); }
  }

  async function doiTrangThai(id: string, trangThai: string) {
    try {
      await api.patch(`/api/v1/ky-danh-gia/${id}/trang-thai`, { trang_thai: trangThai });
      toast.success("Đã cập nhật trạng thái!");
      fetchKy();
    } catch (err: any) { toast.error(err.response?.data?.detail || "Lỗi cập nhật trạng thái"); }
  }

  return (
    <Layout menu={MENU} tieuDe="Quản trị viên">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-800">Quản lý Kỳ đánh giá</h2>
          <Button onClick={moTaoMoi} className="bg-orange-600 hover:bg-orange-700">+ Tạo kỳ mới</Button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">Đang tải...</div>
        ) : kyList.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <p className="text-gray-500">Chưa có kỳ đánh giá nào</p>
              <Button onClick={moTaoMoi} className="mt-4 bg-orange-600 hover:bg-orange-700">Tạo kỳ đầu tiên</Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {kyList.map((ky) => {
              const tt = TRANG_THAI_LABEL[ky.trang_thai] || { label: ky.trang_thai, color: "bg-gray-100 text-gray-600" };
              return (
                <Card key={ky.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-lg text-gray-800">{ky.ten_ky}</h3>
                          <span className={`text-xs px-2 py-1 rounded-full font-medium ${tt.color}`}>{tt.label}</span>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 mt-1">
                          <div>
                            <span className="font-medium">Bắt đầu:</span>{" "}
                            {ky.ngay_bat_dau ? new Date(ky.ngay_bat_dau).toLocaleDateString("vi-VN") : "—"}
                          </div>
                          <div>
                            <span className="font-medium">Kết thúc:</span>{" "}
                            {ky.ngay_ket_thuc ? new Date(ky.ngay_ket_thuc).toLocaleDateString("vi-VN") : "—"}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col gap-2 ml-4">
                        <Button variant="outline" size="sm" onClick={() => moSua(ky)}>Sửa</Button>
                        {ky.trang_thai === "khoa" && (
                          <Button size="sm" className="bg-green-600 hover:bg-green-700 text-xs"
                            onClick={() => doiTrangThai(ky.id, "mo")}>
                            Mở kỳ
                          </Button>
                        )}
                        {ky.trang_thai === "mo" && (
                          <Button size="sm" className="bg-red-500 hover:bg-red-600 text-xs"
                            onClick={() => doiTrangThai(ky.id, "khoa")}>
                            Đóng kỳ
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Dialog tạo/sửa kỳ */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editing ? "Sửa kỳ đánh giá" : "Tạo kỳ đánh giá mới"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <Label>Tên kỳ đánh giá <span className="text-red-500">*</span></Label>
              <Input className="mt-1" placeholder="VD: Học kỳ 1 (2026-2027)"
                value={form.ten_ky} onChange={e => setForm({ ...form, ten_ky: e.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Ngày bắt đầu <span className="text-red-500">*</span></Label>
                <Input className="mt-1" type="date"
                  value={form.ngay_bat_dau} onChange={e => setForm({ ...form, ngay_bat_dau: e.target.value })} />
              </div>
              <div>
                <Label>Ngày kết thúc <span className="text-red-500">*</span></Label>
                <Input className="mt-1" type="date"
                  value={form.ngay_ket_thuc} onChange={e => setForm({ ...form, ngay_ket_thuc: e.target.value })} />
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <Button onClick={luuKy} disabled={saving} className="flex-1 bg-orange-600 hover:bg-orange-700">
                {saving ? "Đang lưu..." : editing ? "Cập nhật" : "Tạo kỳ"}
              </Button>
              <Button variant="outline" onClick={() => setShowDialog(false)} className="flex-1">Hủy</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
