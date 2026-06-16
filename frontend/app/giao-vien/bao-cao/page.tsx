"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

const MENU = [
  { href: "/giao-vien", label: "Bảng theo dõi lớp" },
  { href: "/giao-vien/hoc-sinh", label: "Danh sách học sinh" },
  { href: "/giao-vien/mau", label: "Mẫu mục tiêu" },
  { href: "/giao-vien/bao-cao", label: "Xuất báo cáo" },
];

export default function BaoCaoGVPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [kyList, setKyList] = useState<any[]>([]);
  const [kyChon, setKyChon] = useState("");
  const [dsHS, setDsHS] = useState<any[]>([]);
  const [dangXuat, setDangXuat] = useState(false);

  useEffect(() => { khoiTao(); }, []);

  useEffect(() => {
    if (!nguoiDung) return;
    if (!["giao_vien", "quan_tri"].includes(nguoiDung.vai_tro)) { router.push("/dang-nhap"); return; }
    api.get("/api/v1/ky-danh-gia/").then(r => {
      setKyList(r.data);
      const kyMo = r.data.find((k: any) => k.trang_thai === "mo");
      if (kyMo) setKyChon(kyMo.id);
    });
    if (nguoiDung.ten_lop) {
      api.get(`/api/v1/nguoi-dung/hoc-sinh/${nguoiDung.ten_lop}`).then(r => setDsHS(r.data));
    }
  }, [nguoiDung]);

  async function xuatBaoCaoHS(hs_id: string, hs_ten: string) {
    if (!kyChon) { toast.error("Vui lòng chọn kỳ đánh giá"); return; }
    setDangXuat(true);
    try {
      const token = localStorage.getItem("okr_token");
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/bao-cao/hoc-sinh/${hs_id}?ky_id=${kyChon}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) { toast.error("Không xuất được báo cáo"); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `BaoCao_${hs_ten}.docx`; a.click();
      URL.revokeObjectURL(url);
      toast.success(`Đã tải báo cáo của ${hs_ten}`);
    } catch { toast.error("Lỗi xuất báo cáo"); }
    finally { setDangXuat(false); }
  }

  async function xuatBaoCaoCaLop() {
    if (!kyChon || !nguoiDung?.ten_lop) { toast.error("Chưa đủ thông tin"); return; }
    setDangXuat(true);
    try {
      const token = localStorage.getItem("okr_token");
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/bao-cao/ca-lop/${nguoiDung.ten_lop}?ky_id=${kyChon}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) { toast.error("Không xuất được báo cáo"); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `BaoCao_CaLop_${nguoiDung.ten_lop}.docx`; a.click();
      URL.revokeObjectURL(url);
      toast.success("Đã tải báo cáo cả lớp!");
    } catch { toast.error("Lỗi xuất báo cáo"); }
    finally { setDangXuat(false); }
  }

  return (
    <Layout menu={MENU} tieuDe="Giáo viên chủ nhiệm">
      <div className="p-6 max-w-3xl">
        <h2 className="text-xl font-bold text-gray-800 mb-2">Xuất báo cáo Word</h2>
        <p className="text-sm text-gray-500 mb-6">
          Tải file Word (.docx) chứa phiếu đánh giá mục tiêu của học sinh
        </p>

        {/* Chọn kỳ */}
        <div className="mb-6">
          <label className="text-sm font-medium text-gray-700 mb-1 block">Kỳ đánh giá</label>
          <select className="border rounded-lg px-3 py-2 text-sm min-w-64"
            value={kyChon} onChange={e => setKyChon(e.target.value)}>
            <option value="">-- Chọn kỳ --</option>
            {kyList.map((k: any) => <option key={k.id} value={k.id}>{k.ten_ky}</option>)}
          </select>
        </div>

        {/* Xuất cả lớp */}
        <Card className="mb-6 border-orange-200 bg-orange-50">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <div className="font-semibold text-orange-800">Báo cáo cả lớp {nguoiDung?.ten_lop}</div>
              <div className="text-sm text-orange-600 mt-1">
                Xuất 1 file Word chứa phiếu của tất cả {dsHS.length} học sinh
              </div>
            </div>
            <Button onClick={xuatBaoCaoCaLop} disabled={dangXuat || !kyChon}
              className="bg-orange-600 hover:bg-orange-700 shrink-0">
              {dangXuat ? "Đang tạo..." : "Tải cả lớp"}
            </Button>
          </CardContent>
        </Card>

        {/* Xuất từng học sinh */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Xuất theo từng học sinh</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {dsHS.length === 0 ? (
              <p className="text-center text-gray-400 py-8">Chưa có học sinh</p>
            ) : (
              <div className="divide-y">
                {dsHS.map(hs => (
                  <div key={hs.id} className="flex items-center justify-between px-4 py-3 hover:bg-orange-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center text-sm font-bold text-orange-600">
                        {hs.ho_ten?.[0] || "?"}
                      </div>
                      <div>
                        <span className="font-medium text-sm">{hs.ho_ten}</span>
                        <span className="text-xs text-gray-400 ml-2">{hs.email}</span>
                      </div>
                    </div>
                    <Button size="sm" variant="outline" disabled={dangXuat || !kyChon}
                      onClick={() => xuatBaoCaoHS(hs.id, hs.ho_ten)}
                      className="text-xs border-orange-300 text-orange-600 hover:bg-orange-50">
                      Tải Word
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
