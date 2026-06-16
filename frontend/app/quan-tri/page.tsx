"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";

const MENU = [
  { href: "/quan-tri", label: "Tổng quan" },
  { href: "/quan-tri/giao-vien", label: "Giáo viên" },
  { href: "/quan-tri/ky-danh-gia", label: "Kỳ đánh giá" },
  { href: "/quan-tri/nhat-ky", label: "Nhật ký" },
];

interface LopRow {
  ten_lop: string;
  giao_vien: string;
  so_hs: number;
  da_nop: number;
  da_duyet: number;
  tien_do_tb: number;
}

export default function QuanTriPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [lopData, setLopData] = useState<LopRow[]>([]);
  const [thongKe, setThongKe] = useState({ tong_hs: 0, tong_gv: 0, tong_okr: 0, tong_duyet: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => { khoiTao(); }, []);
  useEffect(() => {
    if (!nguoiDung) return;
    if (nguoiDung.vai_tro !== "quan_tri") { router.push("/dang-nhap"); return; }
    fetchData();
  }, [nguoiDung]);

  async function fetchData() {
    setLoading(true);
    try {
      const [gvRes, hsRes, mtRes] = await Promise.all([
        api.get("/api/v1/quan-tri/danh-sach-nguoi-dung?vai_tro=giao_vien"),
        api.get("/api/v1/quan-tri/danh-sach-nguoi-dung?vai_tro=hoc_sinh"),
        api.get("/api/v1/muc-tieu/"),
      ]);
      const gvList: any[] = gvRes.data;
      const hsList: any[] = hsRes.data;
      const mtList: any[] = mtRes.data;

      setThongKe({
        tong_hs: hsList.length,
        tong_gv: gvList.length,
        tong_okr: mtList.length,
        tong_duyet: mtList.filter(m => m.trang_thai === "da_duyet").length,
      });

      // Build per-class rows
      const lopMap: Record<string, LopRow> = {};
      gvList.forEach(gv => {
        if (!gv.ten_lop) return;
        if (!lopMap[gv.ten_lop]) {
          lopMap[gv.ten_lop] = { ten_lop: gv.ten_lop, giao_vien: gv.ho_ten, so_hs: 0, da_nop: 0, da_duyet: 0, tien_do_tb: 0 };
        }
      });
      hsList.forEach(hs => {
        const lop = hs.ten_lop || "Chưa xếp lớp";
        if (!lopMap[lop]) {
          lopMap[lop] = { ten_lop: lop, giao_vien: "—", so_hs: 0, da_nop: 0, da_duyet: 0, tien_do_tb: 0 };
        }
        lopMap[lop].so_hs += 1;
      });
      mtList.forEach(mt => {
        const hs = hsList.find(h => h.id === mt.hoc_sinh_id);
        const lop = hs?.ten_lop || "Chưa xếp lớp";
        if (lopMap[lop]) {
          lopMap[lop].da_nop += 1;
          if (mt.trang_thai === "da_duyet") lopMap[lop].da_duyet += 1;
          lopMap[lop].tien_do_tb = Math.round(
            (lopMap[lop].tien_do_tb * (lopMap[lop].da_nop - 1) + (mt.tien_do_phan_tram || 0)) / lopMap[lop].da_nop
          );
        }
      });
      setLopData(Object.values(lopMap).sort((a, b) => a.ten_lop.localeCompare(b.ten_lop)));
    } catch (err) {
      console.error("Lỗi tải dữ liệu:", err);
    } finally { setLoading(false); }
  }

  function mauTienDo(p: number) {
    if (p >= 80) return "bg-green-500";
    if (p >= 50) return "bg-orange-500";
    return "bg-red-400";
  }

  return (
    <Layout menu={MENU} tieuDe="Quản trị viên">
      <div className="p-6">
        {/* Stats row */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { l: "Tổng học sinh", v: thongKe.tong_hs, c: "from-orange-500 to-orange-600" },
            { l: "Giáo viên", v: thongKe.tong_gv, c: "from-blue-500 to-blue-600" },
            { l: "Mục tiêu OKR", v: thongKe.tong_okr, c: "from-purple-500 to-purple-600" },
            { l: "Đã duyệt", v: thongKe.tong_duyet, c: "from-green-500 to-green-600" },
          ].map(s => (
            <div key={s.l} className={`bg-gradient-to-br ${s.c} rounded-2xl p-5 text-white shadow-sm`}>
              <div className="text-3xl font-bold">{s.v}</div>
              <div className="text-sm opacity-90 mt-0.5">{s.l}</div>
            </div>
          ))}
        </div>

        {/* Tiêu đề bảng */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Tổng quan theo lớp</h2>
          <button onClick={fetchData} className="text-sm text-orange-600 border border-orange-300 px-4 py-2 rounded-xl hover:bg-orange-50 transition-colors">
            Làm mới
          </button>
        </div>

        {/* Bảng lớp - GV - HS */}
        <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
          {loading ? (
            <div className="text-center py-16">
              <p className="text-gray-400">Đang tải dữ liệu...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-orange-50 border-b border-orange-100">
                  <tr>
                    {[
                      "Lớp",
                      "Giáo viên CN",
                      "Số HS",
                      "Đã nộp OKR",
                      "Đã duyệt",
                      "Tiến độ TB",
                    ].map(h => (
                      <th key={h} className="text-left px-5 py-3.5 text-xs font-bold text-orange-700 uppercase tracking-wider">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {lopData.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-12 text-gray-400">
                        <p>Chưa có dữ liệu lớp học</p>
                      </td>
                    </tr>
                  ) : lopData.map(row => (
                    <tr key={row.ten_lop} className="hover:bg-orange-50/40 transition-colors">
                      <td className="px-5 py-4">
                        <span className="font-bold text-orange-700 bg-orange-100 px-2.5 py-1 rounded-lg text-sm">
                          {row.ten_lop}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-xs font-bold text-white">
                            {row.giao_vien !== "—" ? row.giao_vien[0] : "?"}
                          </div>
                          <span className="text-sm text-gray-700">{row.giao_vien}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-sm font-semibold text-gray-800">{row.so_hs}</span>
                        <span className="text-xs text-gray-400 ml-1">học sinh</span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-800">{row.da_nop}</span>
                          {row.so_hs > 0 && (
                            <span className="text-xs text-gray-400">
                              ({Math.round((row.da_nop / row.so_hs) * 100)}%)
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className={`text-sm font-semibold px-2.5 py-1 rounded-full ${row.da_duyet > 0 ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                          {row.da_duyet}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3 min-w-[120px]">
                          <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                            <div className={`h-2.5 rounded-full ${mauTienDo(row.tien_do_tb)}`}
                              style={{ width: `${Math.min(row.tien_do_tb, 100)}%` }} />
                          </div>
                          <span className={`text-sm font-bold w-10 text-right ${row.tien_do_tb >= 80 ? "text-green-600" : row.tien_do_tb >= 50 ? "text-orange-600" : "text-red-500"}`}>
                            {row.tien_do_tb}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
                {lopData.length > 0 && (
                  <tfoot className="bg-orange-50 border-t-2 border-orange-200">
                    <tr>
                      <td className="px-5 py-3 font-bold text-gray-800 text-sm">Tổng cộng</td>
                      <td className="px-5 py-3 text-sm text-gray-500">{lopData.length} lớp</td>
                      <td className="px-5 py-3 font-bold text-gray-800 text-sm">{lopData.reduce((s, r) => s + r.so_hs, 0)}</td>
                      <td className="px-5 py-3 font-bold text-gray-800 text-sm">{lopData.reduce((s, r) => s + r.da_nop, 0)}</td>
                      <td className="px-5 py-3 font-bold text-green-700 text-sm">{lopData.reduce((s, r) => s + r.da_duyet, 0)}</td>
                      <td className="px-5 py-3 font-bold text-orange-600 text-sm">
                        {lopData.length ? Math.round(lopData.reduce((s, r) => s + r.tien_do_tb, 0) / lopData.length) : 0}%
                      </td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
