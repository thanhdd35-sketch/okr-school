"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";

const MENU = [
  { href: "/hoc-sinh", label: "Mục tiêu OKR" },
  { href: "/hoc-sinh/tong-quan", label: "Tổng quan kỳ" },
  { href: "/hoc-sinh/mau", label: "Mẫu tham khảo" },
];

const TT_STYLE: Record<string, { label: string; cls: string }> = {
  nhap:        { label: "Nháp",       cls: "bg-gray-100 text-gray-500" },
  cho_duyet:   { label: "Chờ duyệt",  cls: "bg-amber-100 text-amber-700" },
  da_duyet:    { label: "Đã duyệt",   cls: "bg-green-100 text-green-700" },
  yeu_cau_sua: { label: "Cần sửa",    cls: "bg-red-100 text-red-700" },
  xin_xoa:     { label: "Chờ xóa",    cls: "bg-gray-100 text-gray-500" },
};

const TIEN_DO_STYLE: Record<string, { label: string; bg: string; cls: string }> = {
  xuat_sac:   { label: "Xuất sắc",    bg: "bg-[#1B5E20]", cls: "text-white" },
  tot:        { label: "Tốt",          bg: "bg-[#388E3C]", cls: "text-white" },
  dung_huong: { label: "Đúng hướng",  bg: "bg-[#F9A825]", cls: "text-white" },
  can_chu_y:  { label: "Cần chú ý",   bg: "bg-[#E65100]", cls: "text-white" },
  chech_huong:{ label: "Chệch hướng", bg: "bg-[#B71C1C]", cls: "text-white" },
};

export default function TongQuanKyPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();

  const [kyList, setKyList] = useState<any[]>([]);
  const [kyChon, setKyChon] = useState<any>(null);
  const [mucTieuList, setMucTieuList] = useState<any[]>([]);
  const [danhGia, setDanhGia] = useState<any>(null);
  const [krsMap, setKrsMap] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => { khoiTao(); }, []);
  useEffect(() => {
    if (!nguoiDung) return;
    if (nguoiDung.vai_tro !== "hoc_sinh") { router.push("/dang-nhap"); return; }
    // Lấy tất cả kỳ có OKR
    fetchKyCoOKR();
  }, [nguoiDung]);

  async function fetchKyCoOKR() {
    try {
      // Lấy tất cả mục tiêu của HS (không lọc kỳ)
      const mtRes = await api.get("/api/v1/muc-tieu/");
      const kyIds = [...new Set(mtRes.data.map((m: any) => m.ky_danh_gia_id))] as string[];

      // Lấy thông tin kỳ
      const kyRes = await api.get("/api/v1/ky-danh-gia/");
      const kyCoOKR = kyRes.data.filter((k: any) => kyIds.includes(k.id));
      // Sắp xếp mới nhất lên đầu
      kyCoOKR.sort((a: any, b: any) => new Date(b.ngay_bat_dau || b.ngay_tao || 0).getTime() - new Date(a.ngay_bat_dau || a.ngay_tao || 0).getTime());
      setKyList(kyCoOKR);

      if (kyCoOKR.length > 0) {
        chonKy(kyCoOKR[0], mtRes.data);
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function chonKy(ky: any, allMT?: any[]) {
    setKyChon(ky);
    setLoading(true);
    try {
      // Lấy OKRs của kỳ này (không kể nháp)
      const mtRes = allMT
        ? allMT.filter((m: any) => m.ky_danh_gia_id === ky.id && m.trang_thai !== "nhap")
        : (await api.get(`/api/v1/muc-tieu/?ky_id=${ky.id}`)).data.filter((m: any) => m.trang_thai !== "nhap");
      setMucTieuList(mtRes);

      // Lấy KRs cho từng OKR
      const map: Record<string, any[]> = {};
      await Promise.all(mtRes.map(async (mt: any) => {
        const r = await api.get(`/api/v1/kr/muc-tieu/${mt.id}`);
        map[mt.id] = r.data;
      }));
      setKrsMap(map);

      // Lấy đánh giá cuối kỳ
      if (nguoiDung) {
        try {
          const dg = await api.get(`/api/v1/danh-gia-cuoi-ky/${nguoiDung.id}?ky_id=${ky.id}`);
          setDanhGia(dg.data?.nhan_xet_gv ? dg.data : null);
        } catch { setDanhGia(null); }
      }
    } finally { setLoading(false); }
  }

  // Tính % tổng kỳ = trung bình tien_do_tong các OKR đã duyệt
  const daDuyetList = mucTieuList.filter(m => m.trang_thai === "da_duyet");
  const pctKy = daDuyetList.length > 0
    ? Math.round(daDuyetList.reduce((s, m) => s + (m.tien_do_tong || 0), 0) / daDuyetList.length)
    : 0;

  const barColor = pctKy >= 80 ? "bg-green-500" : pctKy >= 60 ? "bg-amber-500" : pctKy >= 40 ? "bg-orange-400" : "bg-red-500";

  return (
    <Layout menu={MENU} tieuDe="Học sinh">
      <div className="flex h-full">
        {/* Panel trái: Danh sách kỳ */}
        <div className="w-64 border-r bg-white flex flex-col overflow-hidden">
          <div className="p-3 border-b">
            <h2 className="font-semibold text-sm text-gray-700">📚 Các kỳ học</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {kyList.length === 0 && (
              <div className="text-center py-8 text-gray-400 text-xs">Chưa có kỳ nào</div>
            )}
            {kyList.map(ky => (
              <button key={ky.id} onClick={() => chonKy(ky)}
                className={`w-full text-left p-3 rounded-xl transition-colors border ${kyChon?.id === ky.id ? "bg-orange-50 border-orange-300" : "border-transparent hover:bg-gray-50"}`}>
                <p className="font-semibold text-sm text-gray-800">{ky.ten_ky}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${ky.trang_thai === "mo" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                    {ky.trang_thai === "mo" ? "Đang mở" : ky.trang_thai === "khoa" ? "Đã khóa" : ky.trang_thai}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Panel phải: Nội dung kỳ */}
        <div className="flex-1 overflow-y-auto p-6">
          {!kyChon ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-400">
              <div className="text-5xl mb-3">📊</div>
              <p className="font-medium">Chọn kỳ học để xem tổng quan</p>
            </div>
          ) : loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin w-8 h-8 border-2 border-orange-600 border-t-transparent rounded-full" />
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {/* Header kỳ */}
              <div>
                <h2 className="text-2xl font-bold text-gray-800">{kyChon.ten_ky}</h2>
                <p className="text-sm text-gray-500 mt-1">
                  {mucTieuList.length} mục tiêu đã nộp · {daDuyetList.length} đã duyệt
                </p>
              </div>

              {/* % tổng kỳ */}
              {daDuyetList.length > 0 && (
                <div className="bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-200 rounded-2xl p-5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-orange-800">Tiến độ trung bình cả kỳ</span>
                    <span className="font-bold text-orange-600 text-2xl">{pctKy}%</span>
                  </div>
                  <div className="w-full bg-orange-100 rounded-full h-4">
                    <div className={`${barColor} h-4 rounded-full transition-all`} style={{ width: `${pctKy}%` }} />
                  </div>
                  <p className="text-xs text-orange-600 mt-2">
                    Tính từ trung bình tiến độ của {daDuyetList.length} mục tiêu đã duyệt
                  </p>
                </div>
              )}

              {/* Đánh giá cuối kỳ của GV */}
              {danhGia && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-5">
                  <h3 className="font-bold text-blue-800 mb-3">⭐ Đánh giá cuối kỳ từ giáo viên</h3>

                  {danhGia.diem_so != null && (
                    <div className="mb-4 flex items-center gap-3">
                      <div className="flex">
                        {Array.from({ length: 5 }, (_, i) => (
                          <span key={i} className={`text-2xl ${i < Math.floor(danhGia.diem_so) ? "text-amber-400" : "text-gray-300"}`}>★</span>
                        ))}
                      </div>
                      <span className="font-bold text-blue-600 text-xl">{danhGia.diem_so}/5</span>
                    </div>
                  )}

                  {danhGia.trien_khai_xuat_sac && (
                    <div className="mb-3 bg-yellow-100 border border-yellow-300 rounded-lg px-3 py-2 text-sm text-yellow-800 font-semibold">
                      🏆 Được ghi nhận triển khai xuất sắc!
                    </div>
                  )}

                  {danhGia.nhan_xet_gv && (
                    <div className="mb-3">
                      <p className="text-xs font-semibold text-blue-600 mb-1">Nhận xét giáo viên</p>
                      <p className="text-sm text-gray-800 bg-white rounded-lg p-3 border border-blue-100">{danhGia.nhan_xet_gv}</p>
                    </div>
                  )}

                  {danhGia.ky_vong_ky_tiep && (
                    <div>
                      <p className="text-xs font-semibold text-blue-600 mb-1">🔭 Kỳ vọng kỳ tiếp theo</p>
                      <p className="text-sm text-indigo-800 bg-indigo-50 rounded-lg p-3 border border-indigo-100">{danhGia.ky_vong_ky_tiep}</p>
                    </div>
                  )}

                  {danhGia.phan_hoi_ph && (
                    <div className="mt-3 bg-purple-50 border border-purple-100 rounded-lg p-3">
                      <p className="text-xs font-semibold text-purple-600 mb-1">👨‍👩‍👦 Ý kiến gia đình</p>
                      <p className="text-sm text-purple-800">{danhGia.phan_hoi_ph}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Danh sách mục tiêu */}
              {mucTieuList.length === 0 ? (
                <div className="text-center py-10 text-gray-400">
                  <div className="text-4xl mb-2">📋</div>
                  <p>Chưa có mục tiêu nào được nộp trong kỳ này</p>
                  <button onClick={() => router.push("/hoc-sinh")}
                    className="mt-3 text-sm text-orange-600 underline">
                    Tạo mục tiêu OKR mới →
                  </button>
                </div>
              ) : (
                <div>
                  <h3 className="font-bold text-gray-700 mb-3">📋 Danh sách mục tiêu ({mucTieuList.length})</h3>
                  <div className="space-y-4">
                    {mucTieuList.map((mt, idx) => {
                      const tt = TT_STYLE[mt.trang_thai] || TT_STYLE.cho_duyet;
                      const td = mt.tien_do_tong || 0;
                      const tdBar = td >= 80 ? "bg-green-500" : td >= 60 ? "bg-amber-500" : td >= 40 ? "bg-orange-400" : "bg-red-500";
                      const krs = krsMap[mt.id] || [];

                      return (
                        <div key={mt.id} className="border rounded-2xl p-4 bg-white hover:shadow-sm transition-shadow">
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1 flex-wrap">
                                <span className="text-xs font-bold text-orange-600 bg-orange-50 px-2 py-0.5 rounded-full">O{idx + 1}</span>
                                <span className={`text-xs px-2 py-0.5 rounded-full ${tt.cls}`}>{tt.label}</span>
                                {mt.trang_thai_tien_do && TIEN_DO_STYLE[mt.trang_thai_tien_do] && (
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${TIEN_DO_STYLE[mt.trang_thai_tien_do].bg} ${TIEN_DO_STYLE[mt.trang_thai_tien_do].cls}`}>
                                    {TIEN_DO_STYLE[mt.trang_thai_tien_do].label}
                                  </span>
                                )}
                                {mt.da_hoan_thanh && (
                                  <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">✓ Hoàn thành</span>
                                )}
                              </div>
                              <p className="font-semibold text-gray-800">{mt.muc_tieu_lon}</p>
                              {mt.nhan && <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full mt-1 inline-block">{mt.nhan}</span>}
                            </div>
                            {mt.trang_thai === "da_duyet" && (
                              <div className="ml-3 text-right">
                                <p className="font-bold text-2xl text-orange-600">{td}%</p>
                                <p className="text-xs text-gray-400">tiến độ</p>
                              </div>
                            )}
                          </div>

                          {mt.trang_thai === "da_duyet" && (
                            <div className="mb-3">
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div className={`${tdBar} h-2 rounded-full`} style={{ width: `${td}%` }} />
                              </div>
                            </div>
                          )}

                          {/* KRs */}
                          {krs.length > 0 && (
                            <div className="space-y-2 mt-2">
                              {krs.map((kr, ki) => (
                                <div key={kr.id} className="flex items-center gap-3 bg-gray-50 rounded-lg px-3 py-2">
                                  <span className="text-xs font-bold text-gray-400 w-6">KR{ki + 1}</span>
                                  <p className="text-xs text-gray-700 flex-1">{kr.noi_dung}</p>
                                  <div className="text-right flex-shrink-0">
                                    <p className="text-xs font-bold text-gray-600">{kr.tien_do_phan_tram || 0}%</p>
                                    <p className="text-xs text-gray-400">{kr.gia_tri_hien_tai}/{kr.gia_tri_muc_tieu} {kr.don_vi}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {mt.nhan_xet_giao_vien && (
                            <div className={`mt-3 text-xs rounded-lg p-2 ${mt.trang_thai === "yeu_cau_sua" ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"}`}>
                              💬 {mt.nhan_xet_giao_vien}
                            </div>
                          )}

                          <div className="mt-3 flex justify-end">
                            <button onClick={() => router.push("/hoc-sinh")}
                              className="text-xs text-orange-600 hover:underline">
                              Xem chi tiết →
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
