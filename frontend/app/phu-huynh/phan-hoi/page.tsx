"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

const MENU = [
  { href: "/phu-huynh", label: "Tổng quan" },
  { href: "/phu-huynh/muc-tieu", label: "Mục tiêu của con" },
  { href: "/phu-huynh/phan-hoi", label: "Phản hồi gia đình" },
];

export default function PhanHoiPHPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [kyList, setKyList] = useState<any[]>([]);
  const [kyChon, setKyChon] = useState("");
  const [yKien, setYKien] = useState("");
  const [phanHoiCu, setPhanHoiCu] = useState("");
  const [danhGiaCu, setDanhGiaCu] = useState<any>(null);
  const [dangGui, setDangGui] = useState(false);

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
    if (!kyChon || !nguoiDung) return;
    const hs_id = nguoiDung?.hoc_sinh_id || nguoiDung?.id;
    api.get(`/api/v1/danh-gia-cuoi-ky/${hs_id}?ky_id=${kyChon}`)
      .then(r => {
        setDanhGiaCu(r.data);
        setPhanHoiCu(r.data?.phan_hoi_ph || "");
        setYKien(r.data?.phan_hoi_ph || "");
      }).catch(() => { setDanhGiaCu(null); setPhanHoiCu(""); });
  }, [kyChon, nguoiDung]);

  async function guiYKien() {
    if (!yKien.trim()) { toast.error("Vui lòng nhập ý kiến"); return; }
    setDangGui(true);
    try {
      const hs_id = nguoiDung?.hoc_sinh_id || nguoiDung?.id;
      await api.put(`/api/v1/danh-gia-cuoi-ky/${hs_id}/y-kien?ky_id=${kyChon}`, { phan_hoi_ph: yKien });
      toast.success("Đã gửi ý kiến gia đình thành công!");
      setPhanHoiCu(yKien);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Lỗi gửi ý kiến");
    } finally { setDangGui(false); }
  }

  return (
    <Layout menu={MENU} tieuDe="Phụ huynh">
      <div className="p-6 max-w-2xl mx-auto">
        <h2 className="text-xl font-bold text-gray-800 mb-2">Phản hồi gia đình</h2>
        <p className="text-sm text-gray-500 mb-6">
          Gửi ý kiến, nhận xét của gia đình về quá trình học tập của <strong>{nguoiDung?.ho_ten_con}</strong>
        </p>

        <div className="mb-6">
          <label className="text-sm font-medium text-gray-700 mb-1 block">Kỳ đánh giá</label>
          <select className="border rounded-lg px-3 py-1.5 text-sm"
            value={kyChon} onChange={e => setKyChon(e.target.value)}>
            <option value="">-- Chọn kỳ --</option>
            {kyList.map((k: any) => <option key={k.id} value={k.id}>{k.ten_ky}</option>)}
          </select>
        </div>

        {/* Nhận xét của giáo viên */}
        {danhGiaCu?.nhan_xet_gv && (
          <Card className="mb-6 border-orange-200 bg-orange-50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-orange-700">Nhận xét tổng kết của giáo viên</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-orange-800">{danhGiaCu.nhan_xet_gv}</p>
              {danhGiaCu.diem_ren_luyen && (
                <div className="mt-2 text-sm">
                  <span className="font-medium text-orange-700">Điểm rèn luyện: </span>
                  <span className="text-orange-800 font-bold">{danhGiaCu.diem_ren_luyen}/10</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Form gửi phản hồi */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Ý kiến của gia đình</CardTitle>
          </CardHeader>
          <CardContent>
            {phanHoiCu && (
              <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-200 text-sm text-green-700">
                <span className="font-medium">Đã gửi lần trước:</span> {phanHoiCu}
              </div>
            )}
            <Textarea
              value={yKien}
              onChange={e => setYKien(e.target.value)}
              rows={6}
              placeholder="Nhập ý kiến của gia đình về việc học, tiến độ đạt mục tiêu, và những đề xuất, mong muốn...

Ví dụ: Con đã có nhiều tiến bộ trong học kỳ này, đặc biệt là môn Toán. Gia đình rất vui khi thấy con chủ động đặt mục tiêu và theo dõi tiến độ..."
              className="mb-4"
            />
            <div className="flex gap-3">
              <Button onClick={guiYKien} disabled={dangGui || !kyChon}
                className="flex-1 bg-green-600 hover:bg-green-700">
                {dangGui ? "Đang gửi..." : phanHoiCu ? "Cập nhật ý kiến" : "Gửi ý kiến"}
              </Button>
              {yKien !== phanHoiCu && (
                <Button variant="outline" onClick={() => setYKien(phanHoiCu)} className="shrink-0">
                  Hủy thay đổi
                </Button>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">
              Ý kiến sẽ được gửi đến giáo viên chủ nhiệm để tổng hợp đánh giá
            </p>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
