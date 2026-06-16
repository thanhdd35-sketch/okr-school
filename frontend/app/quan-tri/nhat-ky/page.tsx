"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const MENU = [
  { href: "/quan-tri", label: "Tổng quan" },
  { href: "/quan-tri/giao-vien", label: "Giáo viên" },
  { href: "/quan-tri/ky-danh-gia", label: "Kỳ đánh giá" },
  { href: "/quan-tri/nhat-ky", label: "Nhật ký" },
];

export default function NhatKyPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [trang, setTrang] = useState(1);
  const MOI_TRANG = 30;

  useEffect(() => { khoiTao(); }, []);

  useEffect(() => {
    if (!nguoiDung) return;
    if (nguoiDung.vai_tro !== "quan_tri") { router.push("/dang-nhap"); return; }
    fetchLogs();
  }, [nguoiDung]);

  async function fetchLogs() {
    setLoading(true);
    try {
      const r = await api.get("/api/v1/quan-tri/nhat-ky-hoat-dong?limit=200");
      setLogs(r.data);
    } catch {
      setLogs([]);
      toast.error("Chưa có dữ liệu nhật ký");
    } finally { setLoading(false); }
  }

  const filtered = logs.filter(l =>
    !search ||
    l.ho_ten?.toLowerCase().includes(search.toLowerCase()) ||
    l.hanh_dong?.toLowerCase().includes(search.toLowerCase()) ||
    l.mo_ta?.toLowerCase().includes(search.toLowerCase())
  );

  const totalTrang = Math.ceil(filtered.length / MOI_TRANG);
  const hienThi = filtered.slice((trang - 1) * MOI_TRANG, trang * MOI_TRANG);

  function formatThoiGian(str: string) {
    if (!str) return "—";
    const d = new Date(str);
    return d.toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  const VAI_TRO_LABEL: Record<string, string> = {
    quan_tri: "Quản trị",
    giao_vien: "Giáo viên",
    hoc_sinh: "Học sinh",
    phu_huynh: "Phụ huynh",
  };

  return (
    <Layout menu={MENU} tieuDe="Quản trị viên">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">Nhật ký hoạt động</h2>
          <span className="text-sm text-gray-500">{filtered.length} hoạt động</span>
        </div>

        <Input className="mb-4 max-w-sm" placeholder="Tìm theo tên, hành động..."
          value={search} onChange={e => { setSearch(e.target.value); setTrang(1); }} />

        {loading ? (
          <div className="text-center py-12 text-gray-400">Đang tải nhật ký...</div>
        ) : hienThi.length === 0 ? (
          <Card>
            <CardContent className="text-center py-16">
              <p className="text-gray-500 text-lg font-medium">Chưa có nhật ký hoạt động</p>
              <p className="text-gray-400 text-sm mt-1">
                Các hoạt động của người dùng sẽ được ghi lại tại đây
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            <Card>
              <CardContent className="p-0">
                <div className="divide-y">
                  {hienThi.map((log, i) => (
                    <div key={i} className="flex items-start gap-3 px-4 py-3 hover:bg-orange-50/30 transition-colors">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-sm text-gray-800">{log.ho_ten || "Hệ thống"}</span>
                          <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
                            {VAI_TRO_LABEL[log.vai_tro] || log.vai_tro}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-0.5">{log.mo_ta || log.hanh_dong}</p>
                      </div>
                      <span className="text-xs text-gray-400 whitespace-nowrap mt-0.5">
                        {formatThoiGian(log.thoi_gian || log.ngay_tao)}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Phân trang */}
            {totalTrang > 1 && (
              <div className="flex justify-center gap-2 mt-4">
                <button onClick={() => setTrang(Math.max(1, trang - 1))} disabled={trang === 1}
                  className="px-3 py-1 rounded-lg border text-sm disabled:opacity-40 hover:bg-gray-50">
                  Trước
                </button>
                <span className="px-3 py-1 text-sm text-gray-600">Trang {trang}/{totalTrang}</span>
                <button onClick={() => setTrang(Math.min(totalTrang, trang + 1))} disabled={trang === totalTrang}
                  className="px-3 py-1 rounded-lg border text-sm disabled:opacity-40 hover:bg-gray-50">
                  Sau
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
