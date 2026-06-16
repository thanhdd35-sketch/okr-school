"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import Layout from "@/components/Layout";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const MENU = [
  { href: "/giao-vien", label: "Bảng theo dõi lớp" },
  { href: "/giao-vien/hoc-sinh", label: "Danh sách học sinh" },
  { href: "/giao-vien/mau", label: "Mẫu mục tiêu" },
  { href: "/giao-vien/bao-cao", label: "Xuất báo cáo" },
];

const TRANG_THAI_LABEL: Record<string, { label: string; color: string }> = {
  cho_duyet:   { label: "Chờ duyệt",  color: "bg-amber-100 text-amber-700" },
  da_duyet:    { label: "Đã duyệt",   color: "bg-green-100 text-green-700" },
  yeu_cau_sua: { label: "Cần sửa",    color: "bg-red-100 text-red-700" },
  xin_xoa:     { label: "Chờ xóa",    color: "bg-gray-100 text-gray-500" },
};

export default function GiaoVienPage() {
  const { nguoiDung, khoiTao } = useStore();
  const router = useRouter();
  const [hocSinhList, setHocSinhList] = useState<any[]>([]);
  const [mucTieuList, setMucTieuList] = useState<any[]>([]);
  const [kyList, setKyList] = useState<any[]>([]);
  const [kyChon, setKyChon] = useState("");
  const [hocSinhChon, setHocSinhChon] = useState<any>(null);
  const [mucTieuHocSinh, setMucTieuHocSinh] = useState<any[]>([]);
  const [locTrangThai, setLocTrangThai] = useState("tat_ca");

  const [hienDuyet, setHienDuyet] = useState(false);
  const [hienSua, setHienSua] = useState(false);
  const [mucTieuHanhDong, setMucTieuHanhDong] = useState<any>(null);
  const [lyDo, setLyDo] = useState("");
  const [nhanXetGV, setNhanXetGV] = useState("");
  const [dangTaoNhanXet, setDangTaoNhanXet] = useState(false);

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
      api.get(`/api/v1/nguoi-dung/hoc-sinh/${nguoiDung.ten_lop}`).then(r => setHocSinhList(r.data));
    }
  }, [nguoiDung]);

  useEffect(() => {
    if (!nguoiDung?.ten_lop || !kyChon) return;
    api.get(`/api/v1/muc-tieu/theo-lop/${nguoiDung.ten_lop}?ky_id=${kyChon}`).then(r => setMucTieuList(r.data));
  }, [kyChon, nguoiDung]);

  function chonHocSinh(hs: any) {
    setHocSinhChon(hs);
    const mt = mucTieuList.filter(m => m.hoc_sinh_id === hs.id);
    setMucTieuHocSinh(mt);
  }

  async function laiDuLieu() {
    if (!nguoiDung?.ten_lop || !kyChon) return;
    const r = await api.get(`/api/v1/muc-tieu/theo-lop/${nguoiDung.ten_lop}?ky_id=${kyChon}`);
    setMucTieuList(r.data);
    if (hocSinhChon) {
      setMucTieuHocSinh(r.data.filter((m: any) => m.hoc_sinh_id === hocSinhChon.id));
    }
  }

  async function duyetMucTieu(id: string) {
    await api.post(`/api/v1/muc-tieu/${id}/duyet`);
    toast.success("Đã duyệt mục tiêu");
    laiDuLieu();
  }

  async function yeuCauSua() {
    if (!lyDo) { toast.error("Vui lòng nhập lý do"); return; }
    await api.post(`/api/v1/muc-tieu/${mucTieuHanhDong.id}/yeu-cau-sua`, { ly_do: lyDo });
    toast.success("Đã yêu cầu chỉnh sửa");
    setHienSua(false); setLyDo("");
    laiDuLieu();
  }

  async function dongYXoa(id: string) {
    if (!confirm("Xác nhận xóa mục tiêu này?")) return;
    await api.post(`/api/v1/muc-tieu/${id}/dong-y-xoa`);
    toast.success("Đã xóa mục tiêu");
    laiDuLieu();
  }

  async function taoNhanXetAI(mt: any) {
    setDangTaoNhanXet(true);
    try {
      const r = await api.post("/api/v1/ai/tao-nhan-xet", { hoc_sinh_id: hocSinhChon.id, muc_tieu_id: mt.id });
      setNhanXetGV(r.data.nhan_xet);
      setMucTieuHanhDong(mt);
      setHienDuyet(true);
    } catch { toast.error("Không tạo được nhận xét AI"); }
    finally { setDangTaoNhanXet(false); }
  }

  async function luuNhanXet(mt_id: string) {
    await api.put(`/api/v1/muc-tieu/${mt_id}/nhan-xet`, { nhan_xet: nhanXetGV });
    toast.success("Đã lưu nhận xét");
    setHienDuyet(false); setNhanXetGV("");
  }

  const danhSachLoc = hocSinhList.filter(hs => {
    if (locTrangThai === "tat_ca") return true;
    const mt = mucTieuList.filter(m => m.hoc_sinh_id === hs.id);
    if (locTrangThai === "cho_duyet") return mt.some(m => m.trang_thai === "cho_duyet");
    if (locTrangThai === "da_duyet") return mt.some(m => m.trang_thai === "da_duyet");
    return true;
  });

  const demChoduyet = mucTieuList.filter(m => m.trang_thai === "cho_duyet").length;

  return (
    <Layout menu={MENU} tieuDe="Giáo viên chủ nhiệm">
      <div className="flex h-full">
        {/* LEFT: Danh sách học sinh */}
        <div className="w-72 border-r border-gray-200 bg-white flex flex-col flex-shrink-0">
          <div className="p-3 bg-gradient-to-br from-orange-600 to-orange-700 text-white">
            <div className="font-bold mb-1">Lớp {nguoiDung?.ten_lop}</div>
            {demChoduyet > 0 && (
              <div className="text-xs bg-white/20 rounded-lg px-2 py-1 inline-block">
                {demChoduyet} mục tiêu chờ duyệt
              </div>
            )}
          </div>
          <div className="p-3 border-b space-y-2">
            <select className="w-full border rounded-lg px-2 py-1.5 text-sm"
              value={kyChon} onChange={e => setKyChon(e.target.value)}>
              <option value="">-- Chọn kỳ --</option>
              {kyList.map((k: any) => <option key={k.id} value={k.id}>{k.ten_ky}</option>)}
            </select>
            <select className="w-full border rounded-lg px-2 py-1.5 text-sm"
              value={locTrangThai} onChange={e => setLocTrangThai(e.target.value)}>
              <option value="tat_ca">Tất cả học sinh</option>
              <option value="cho_duyet">Có mục tiêu chờ duyệt</option>
              <option value="da_duyet">Đã duyệt</option>
            </select>
          </div>

          <div className="flex-1 overflow-y-auto">
            {danhSachLoc.map(hs => {
              const mtHS = mucTieuList.filter(m => m.hoc_sinh_id === hs.id);
              const coCho = mtHS.some(m => m.trang_thai === "cho_duyet");
              const tienDoTB = mtHS.length > 0
                ? Math.round(mtHS.reduce((s, m) => s + (m.tien_do_phan_tram || 0), 0) / mtHS.length)
                : 0;
              return (
                <div key={hs.id} onClick={() => chonHocSinh(hs)}
                  className={`p-3 border-b cursor-pointer hover:bg-orange-50 transition-colors ${hocSinhChon?.id === hs.id ? "bg-orange-50 border-l-4 border-l-orange-500" : "border-l-4 border-l-transparent"}`}>
                  <div className="flex justify-between items-start">
                    <div className="text-sm font-medium text-gray-800">{hs.ho_ten}</div>
                    {coCho && (
                      <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded-full">Chờ duyệt</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5">{mtHS.length} mục tiêu · {tienDoTB}% TB</div>
                  {mtHS.length > 0 && (
                    <div className="mt-1 bg-gray-100 rounded-full h-1">
                      <div className="bg-orange-400 h-1 rounded-full" style={{ width: `${tienDoTB}%` }} />
                    </div>
                  )}
                </div>
              );
            })}
            {danhSachLoc.length === 0 && (
              <div className="text-center py-8 text-gray-400 text-sm">Không có học sinh</div>
            )}
          </div>
        </div>

        {/* RIGHT: Chi tiết */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-5">
          {!hocSinhChon ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-400">
                <p className="font-medium">Chọn học sinh để xem mục tiêu</p>
                <p className="text-sm mt-1">và thực hiện duyệt / nhận xét</p>
              </div>
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-3 mb-5">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-xl font-bold text-white">
                  {hocSinhChon.ho_ten?.[0] || "?"}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-800">{hocSinhChon.ho_ten}</h2>
                  <p className="text-sm text-gray-400">{hocSinhChon.email}</p>
                </div>
              </div>

              <div className="space-y-3">
                {mucTieuHocSinh.length === 0 && (
                  <div className="text-center py-10 bg-white rounded-xl border">
                    <p className="text-gray-400">Học sinh chưa có mục tiêu</p>
                  </div>
                )}
                {mucTieuHocSinh.map(mt => {
                  const tt = TRANG_THAI_LABEL[mt.trang_thai] || { label: mt.trang_thai, color: "bg-gray-100 text-gray-600" };
                  return (
                    <Card key={mt.id} className="shadow-sm">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1 mr-3">
                            <div className="font-semibold text-sm text-gray-800">{mt.muc_tieu_lon}</div>
                            {mt.ket_qua_then_chot && (
                              <div className="text-xs text-gray-400 mt-0.5">{mt.ket_qua_then_chot}</div>
                            )}
                          </div>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${tt.color}`}>{tt.label}</span>
                        </div>
                        <div className="flex items-center gap-2 mb-3">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div className={`h-2 rounded-full ${mt.tien_do_phan_tram >= 80 ? "bg-green-500" : mt.tien_do_phan_tram >= 50 ? "bg-orange-500" : "bg-red-400"}`}
                              style={{ width: `${Math.min(mt.tien_do_phan_tram, 100)}%` }} />
                          </div>
                          <span className="text-xs text-gray-500">{mt.thuc_dat}/{mt.chi_tieu} {mt.don_vi}</span>
                          <span className="text-xs font-bold text-orange-600">{mt.tien_do_phan_tram}%</span>
                        </div>
                        <div className="flex gap-2 flex-wrap">
                          {mt.trang_thai === "cho_duyet" && (
                            <>
                              <Button size="sm" onClick={() => duyetMucTieu(mt.id)}
                                className="bg-green-600 hover:bg-green-700 text-xs h-7">
                                Duyệt
                              </Button>
                              <Button size="sm" variant="outline"
                                onClick={() => { setMucTieuHanhDong(mt); setHienSua(true); }}
                                className="text-red-600 border-red-300 text-xs h-7">
                                Yêu cầu sửa
                              </Button>
                            </>
                          )}
                          {mt.trang_thai === "xin_xoa" && (
                            <Button size="sm" onClick={() => dongYXoa(mt.id)}
                              className="bg-red-600 hover:bg-red-700 text-xs h-7">
                              Đồng ý xóa
                            </Button>
                          )}
                          <Button size="sm" variant="outline" onClick={() => taoNhanXetAI(mt)}
                            disabled={dangTaoNhanXet} className="text-xs h-7">
                            {dangTaoNhanXet ? "Đang tạo..." : "Nhận xét AI"}
                          </Button>
                        </div>
                        {mt.nhan_xet_giao_vien && (
                          <div className="mt-2 p-2 bg-orange-50 rounded-lg text-xs text-orange-700">
                            <span className="font-medium">Nhận xét: </span>{mt.nhan_xet_giao_vien}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Dialog nhận xét */}
      <Dialog open={hienDuyet} onOpenChange={setHienDuyet}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nhận xét mục tiêu</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <Label>Nhận xét của giáo viên</Label>
            <Textarea value={nhanXetGV} onChange={e => setNhanXetGV(e.target.value)} rows={4}
              placeholder="Nhập nhận xét..." />
            <Button onClick={() => luuNhanXet(mucTieuHanhDong?.id)} className="w-full bg-orange-600 hover:bg-orange-700">
              Lưu nhận xét
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog yêu cầu sửa */}
      <Dialog open={hienSua} onOpenChange={setHienSua}>
        <DialogContent>
          <DialogHeader><DialogTitle>Yêu cầu chỉnh sửa</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <Label>Lý do yêu cầu chỉnh sửa</Label>
            <Textarea value={lyDo} onChange={e => setLyDo(e.target.value)} rows={3}
              placeholder="Nhập lý do cụ thể..." />
            <Button onClick={yeuCauSua} className="w-full bg-red-600 hover:bg-red-700">
              Gửi yêu cầu sửa
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
