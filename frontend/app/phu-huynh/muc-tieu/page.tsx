"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";

const MENU = [
  { href: "/phu-huynh", label: "Tổng quan" },
  { href: "/phu-huynh/muc-tieu", label: "Mục tiêu của con" },
  { href: "/phu-huynh/phan-hoi", label: "Phản hồi gia đình" },
];

const TRANG_THAI_LABEL: Record<string, { label: string; color: string }> = {
  cho_duyet:   { label: "Chờ duyệt", color: "bg-amber-100 text-amber-700" },
  da_duyet:    { label: "Đã duyệt",  color: "bg-green-100 text-green-700" },
  yeu_cau_sua: { label: "Cần sửa",   color: "bg-red-100 text-red-700" },
  xin_xoa:     { label: "Chờ xóa",   color: "bg-gray-100 text-gray-500" },
};

export default function MucTieuPHPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [mucTieuList, setMucTieuList] = useState<any[]>([]);
  const [kyList, setKyList] = useState<any[]>([]);
  const [kyChon, setKyChon] = useState("");
  const [mucTieuChon, setMucTieuChon] = useState<any>(null);

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
    toast.success(`Đã đánh giá ${diem} sao!`);
    const r = await api.get(`/api/v1/muc-tieu/?ky_id=${kyChon}`);
    setMucTieuList(r.data);
  }

  return (
    <Layout menu={MENU} tieuDe="Phụ huynh">
      <div className="p-6 max-w-2xl mx-auto">
        <h2 className="text-xl font-bold text-gray-800 mb-2">Mục tiêu của {nguoiDung?.ho_ten_con}</h2>

        <div className="mb-4">
          <select className="border rounded-lg px-3 py-1.5 text-sm"
            value={kyChon} onChange={e => setKyChon(e.target.value)}>
            <option value="">-- Chọn kỳ --</option>
            {kyList.map((k: any) => <option key={k.id} value={k.id}>{k.ten_ky}</option>)}
          </select>
        </div>

        {mucTieuList.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <p className="text-gray-500">Con chưa có mục tiêu trong kỳ này</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {mucTieuList.map(mt => {
              const tt = TRANG_THAI_LABEL[mt.trang_thai] || { label: mt.trang_thai, color: "bg-gray-100 text-gray-500" };
              const isOpen = mucTieuChon?.id === mt.id;
              return (
                <Card key={mt.id}
                  className={`cursor-pointer hover:shadow-md transition-shadow ${isOpen ? "ring-2 ring-orange-400" : ""}`}
                  onClick={() => setMucTieuChon(isOpen ? null : mt)}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1 mr-2">
                        <div className="font-medium text-gray-800">{mt.muc_tieu_lon}</div>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${tt.color} mt-1 inline-block`}>
                          {tt.label}
                        </span>
                      </div>
                      <span className="font-bold text-orange-600 text-lg">{mt.tien_do_phan_tram}%</span>
                    </div>

                    <div className="bg-gray-200 rounded-full h-2 mb-3">
                      <div className="bg-orange-500 h-2 rounded-full"
                        style={{ width: `${Math.min(mt.tien_do_phan_tram, 100)}%` }} />
                    </div>

                    {/* Đánh giá sao */}
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-gray-400 mb-1">Đánh giá của phụ huynh:</p>
                        <div className="flex gap-1">
                          {[1, 2, 3, 4, 5].map(s => (
                            <button key={s} onClick={e => { e.stopPropagation(); chamSao(mt.id, s); }}
                              className={`text-2xl transition-transform hover:scale-110 ${s <= (mt.diem_phu_huynh || 0) ? "text-yellow-400" : "text-gray-300 hover:text-yellow-300"}`}>
                              ★
                            </button>
                          ))}
                        </div>
                      </div>
                      {mt.han_hoan_thanh && (
                        <span className="text-xs text-gray-400">
                          Hạn: {new Date(mt.han_hoan_thanh).toLocaleDateString("vi-VN")}
                        </span>
                      )}
                    </div>

                    {isOpen && (
                      <div className="mt-4 pt-4 border-t space-y-2 text-sm">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="bg-gray-50 rounded-lg p-2">
                            <div className="text-xs text-gray-400">Kết quả then chốt</div>
                            <div className="font-medium">{mt.ket_qua_then_chot}</div>
                          </div>
                          <div className="bg-gray-50 rounded-lg p-2">
                            <div className="text-xs text-gray-400">Thực đạt / Chỉ tiêu</div>
                            <div className="font-medium">{mt.thuc_dat} / {mt.chi_tieu} {mt.don_vi}</div>
                          </div>
                        </div>
                        {mt.nhan_xet_giao_vien && (
                          <div className="p-3 bg-orange-50 rounded-lg text-sm text-orange-700">
                            <span className="font-medium">Nhận xét GV:</span> {mt.nhan_xet_giao_vien}
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </Layout>
  );
}
