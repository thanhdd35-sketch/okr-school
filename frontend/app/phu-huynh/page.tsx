"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

const MENU = [
  { href: "/phu-huynh", label: "Tổng quan" },
  { href: "/phu-huynh/muc-tieu", label: "Mục tiêu của con" },
  { href: "/phu-huynh/phan-hoi", label: "Phản hồi gia đình" },
];

export default function PhuHuynhPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [mucTieuList, setMucTieuList] = useState<any[]>([]);
  const [mucTieuChon, setMucTieuChon] = useState<any>(null);
  const [yKien, setYKien] = useState("");
  const [kyList, setKyList] = useState<any[]>([]);
  const [kyChon, setKyChon] = useState("");

  useEffect(() => { khoiTao(); }, []);

  useEffect(() => {
    if (!nguoiDung) return;
    if (nguoiDung.vai_tro !== "phu_huynh") { router.push("/dang-nhap"); return; }
    api.get("/api/v1/ky-danh-gia/").then(r => {
      setKyList(r.data);
      const kyMo = r.data.find((k: any) => k.trang_thai === "mo");
      if (kyMo) setKyChon(kyMo.id);
    });
  }, [nguoiDung]);

  useEffect(() => {
    if (!kyChon) return;
    api.get(`/api/v1/muc-tieu/?ky_id=${kyChon}`).then(r => setMucTieuList(r.data));
  }, [kyChon]);

  async function chamSao(mt_id: string, diem: number) {
    await api.put(`/api/v1/muc-tieu/${mt_id}/danh-gia`, { diem });
    toast.success("Đã đánh giá sao");
    const r = await api.get(`/api/v1/muc-tieu/?ky_id=${kyChon}`);
    setMucTieuList(r.data);
  }

  async function guiYKien() {
    if (!yKien) { toast.error("Vui lòng nhập ý kiến"); return; }
    const hs_id = nguoiDung?.hoc_sinh_id || nguoiDung?.id;
    await api.put(`/api/v1/danh-gia-cuoi-ky/${hs_id}/y-kien?ky_id=${kyChon}`, { phan_hoi_ph: yKien });
    toast.success("Đã gửi ý kiến gia đình!");
    setYKien("");
  }

  const tienDoTB = mucTieuList.length > 0
    ? Math.round(mucTieuList.reduce((s, m) => s + (m.tien_do_phan_tram || 0), 0) / mucTieuList.length)
    : 0;

  return (
    <Layout menu={MENU} tieuDe="Phụ huynh">
      <div className="p-6 max-w-2xl mx-auto">
        <div className="mb-6 p-4 bg-orange-50 rounded-xl border border-orange-100">
          <h2 className="text-lg font-bold text-orange-700">
            Theo dõi tiến độ của {nguoiDung?.ho_ten_con || "con"}
          </h2>
          <div className="text-sm text-gray-500 mt-1">
            Lớp: {nguoiDung?.ten_lop} · Tiến độ trung bình: <strong className="text-orange-600">{tienDoTB}%</strong>
          </div>
          <div className="mt-2 bg-gray-200 rounded-full h-2">
            <div className="bg-orange-500 h-2 rounded-full transition-all" style={{ width: `${tienDoTB}%` }} />
          </div>
        </div>

        <div className="mb-4">
          <select className="border rounded-lg px-3 py-1.5 text-sm"
            value={kyChon} onChange={e => setKyChon(e.target.value)}>
            {kyList.map((k: any) => <option key={k.id} value={k.id}>{k.ten_ky}</option>)}
          </select>
        </div>

        {/* Danh sách mục tiêu */}
        <div className="space-y-3 mb-6">
          {mucTieuList.map(mt => (
            <Card key={mt.id}
              className={`cursor-pointer hover:shadow-md transition-shadow ${mucTieuChon?.id === mt.id ? "ring-2 ring-orange-400" : ""}`}
              onClick={() => setMucTieuChon(mucTieuChon?.id === mt.id ? null : mt)}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="font-medium text-sm flex-1 mr-2">{mt.muc_tieu_lon}</div>
                  <span className="text-orange-600 font-bold text-sm">{mt.tien_do_phan_tram}%</span>
                </div>
                <div className="bg-gray-200 rounded-full h-2 mb-3">
                  <div className="bg-orange-500 h-2 rounded-full"
                    style={{ width: `${Math.min(mt.tien_do_phan_tram, 100)}%` }} />
                </div>

                {/* Chấm sao */}
                <div className="flex items-center justify-between">
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map(s => (
                      <button key={s} onClick={e => { e.stopPropagation(); chamSao(mt.id, s); }}
                        className={`text-xl transition-colors ${s <= (mt.diem_phu_huynh || 0) ? "text-yellow-400" : "text-gray-300 hover:text-yellow-300"}`}>
                        ★
                      </button>
                    ))}
                  </div>
                  {mt.han_hoan_thanh && (
                    <span className="text-xs text-gray-400">
                      Hạn: {new Date(mt.han_hoan_thanh).toLocaleDateString("vi-VN")}
                    </span>
                  )}
                </div>

                {/* Chi tiết mở rộng */}
                {mucTieuChon?.id === mt.id && (
                  <div className="mt-3 pt-3 border-t space-y-2">
                    <div className="text-xs text-gray-500">
                      <span className="font-medium">Kết quả then chốt:</span> {mt.ket_qua_then_chot}
                    </div>
                    <div className="text-xs text-gray-500">
                      <span className="font-medium">Thực đạt:</span> {mt.thuc_dat} / {mt.chi_tieu} {mt.don_vi}
                    </div>
                    {mt.nhan_xet_giao_vien && (
                      <div className="p-2 bg-orange-50 rounded text-xs text-orange-700">
                        <span className="font-medium">Nhận xét GV:</span> {mt.nhan_xet_giao_vien}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
          {mucTieuList.length === 0 && (
            <div className="text-center py-10 bg-white rounded-xl border">
              <p className="text-gray-400">Chưa có mục tiêu trong kỳ này</p>
            </div>
          )}
        </div>

        {/* Gửi ý kiến gia đình */}
        <Card>
          <CardHeader><CardTitle className="text-base">Ý kiến của gia đình</CardTitle></CardHeader>
          <CardContent>
            <Textarea value={yKien} onChange={e => setYKien(e.target.value)} rows={4}
              placeholder="Nhập ý kiến, nhận xét của gia đình về quá trình học tập của con..." />
            <Button onClick={guiYKien} className="mt-3 bg-green-600 hover:bg-green-700">
              Gửi ý kiến
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
