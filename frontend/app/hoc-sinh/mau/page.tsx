"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";

const MENU = [
  { href: "/hoc-sinh", label: "Mục tiêu OKR" },
  { href: "/hoc-sinh/mau", label: "Mẫu tham khảo" },
];

const LOAI_OKR: Record<string, string> = { ca_nhan: "Cá nhân", nhom: "Nhóm", lop: "Cả lớp" };

export default function MauHSPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [mauList, setMauList] = useState<any[]>([]);
  const [kyList, setKyList] = useState<any[]>([]);
  const [kyChon, setKyChon] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => { khoiTao(); }, []);

  useEffect(() => {
    if (!nguoiDung) return;
    if (nguoiDung.vai_tro !== "hoc_sinh") { router.push("/dang-nhap"); return; }
    api.get("/api/v1/ky-danh-gia/").then(r => {
      setKyList(r.data.filter((k: any) => k.trang_thai === "mo"));
      const kyMo = r.data.find((k: any) => k.trang_thai === "mo");
      if (kyMo) setKyChon(kyMo.id);
    });
    api.get(`/api/v1/mau-muc-tieu/?ten_lop=${nguoiDung.ten_lop || ""}`)
      .then(r => { setMauList(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [nguoiDung]);

  async function apDungMau(m: any) {
    if (!kyChon) { toast.error("Vui lòng chọn kỳ đánh giá"); return; }
    try {
      await api.post("/api/v1/muc-tieu/", {
        ky_danh_gia_id: kyChon,
        loai_okr: m.loai_okr,
        muc_tieu_lon: m.muc_tieu_lon_mau,
        ket_qua_then_chot: m.ket_qua_then_chot_mau,
        chi_tieu: 10,
        don_vi: m.don_vi_mac_dinh,
        han_hoan_thanh: null,
      });
      toast.success(`Đã áp dụng mẫu "${m.ten_mau}" — vào "Mục tiêu OKR" để chỉnh sửa thêm!`);
      setTimeout(() => router.push("/hoc-sinh"), 1500);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Lỗi áp dụng mẫu");
    }
  }

  return (
    <Layout menu={MENU} tieuDe="Học sinh">
      <div className="p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-2">📋 Mẫu mục tiêu tham khảo</h2>
        <p className="text-sm text-gray-500 mb-4">Chọn mẫu từ giáo viên để tạo mục tiêu nhanh</p>

        <div className="mb-4 flex items-center gap-3">
          <label className="text-sm font-medium text-gray-700">Kỳ đánh giá:</label>
          <select className="border rounded-lg px-3 py-1.5 text-sm"
            value={kyChon} onChange={e => setKyChon(e.target.value)}>
            <option value="">-- Chọn kỳ --</option>
            {kyList.map((k: any) => <option key={k.id} value={k.id}>{k.ten_ky}</option>)}
          </select>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">Đang tải...</div>
        ) : mauList.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <div className="text-4xl mb-3">📋</div>
              <p className="text-gray-500">Giáo viên chưa tạo mẫu mục tiêu nào</p>
              <Button className="mt-4 bg-orange-600 hover:bg-orange-700" onClick={() => router.push("/hoc-sinh")}>
                Tự tạo mục tiêu
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mauList.map(m => (
              <Card key={m.id} className="hover:shadow-md transition-shadow border-l-4 border-l-orange-400">
                <CardContent className="p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-800">{m.ten_mau}</h3>
                      <span className="text-xs px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full mt-1 inline-block">
                        {LOAI_OKR[m.loai_okr] || m.loai_okr}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-1 text-sm text-gray-600 mb-4">
                    <div><span className="font-medium text-gray-700">🎯 Mục tiêu:</span> {m.muc_tieu_lon_mau}</div>
                    <div><span className="font-medium text-gray-700">🔑 KR:</span> {m.ket_qua_then_chot_mau}</div>
                    <div><span className="font-medium text-gray-700">📐 Đơn vị:</span> {m.don_vi_mac_dinh}</div>
                  </div>
                  <Button onClick={() => apDungMau(m)} className="w-full bg-green-600 hover:bg-green-700" disabled={!kyChon}>
                    ✅ Áp dụng mẫu này
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
