"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DoiMatKhauPage() {
  const router = useRouter();
  const { nguoiDung, khoiTao } = useStore();
  const [form, setForm] = useState({ mat_khau_cu: "", mat_khau_moi: "", xac_nhan: "" });
  const [show, setShow] = useState({ cu: false, moi: false, xn: false });
  const [dangTai, setDangTai] = useState(false);

  useEffect(() => { khoiTao(); }, []);

  async function xuLy(e: React.FormEvent) {
    e.preventDefault();
    if (form.mat_khau_moi !== form.xac_nhan) {
      toast.error("Mật khẩu xác nhận không khớp");
      return;
    }
    setDangTai(true);
    try {
      await api.post("/api/v1/xac-thuc/doi-mat-khau", {
        mat_khau_cu: form.mat_khau_cu,
        mat_khau_moi: form.mat_khau_moi,
      });
      toast.success("Đổi mật khẩu thành công!");
      const vai_tro = nguoiDung?.vai_tro;
      const map: Record<string, string> = {
        quan_tri: "/quan-tri", giao_vien: "/giao-vien", hoc_sinh: "/hoc-sinh",
      };
      router.push(map[vai_tro || ""] || "/dang-nhap");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Đổi mật khẩu thất bại");
    } finally { setDangTai(false); }
  }

  function EyeBtn({ field }: { field: "cu" | "moi" | "xn" }) {
    return (
      <button type="button" onClick={() => setShow(s => ({ ...s, [field]: !s[field] }))}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700">
        {show[field] ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 to-orange-100 p-4">
      <Card className="w-full max-w-md shadow-lg border-0">
        <CardHeader>
          <CardTitle className="text-center text-orange-700">Đổi mật khẩu lần đầu</CardTitle>
          <p className="text-center text-sm text-gray-500">
            Bạn cần đổi mật khẩu trước khi sử dụng hệ thống
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={xuLy} className="space-y-4">
            <div>
              <Label>Mật khẩu hiện tại</Label>
              <div className="relative mt-1">
                <Input type={show.cu ? "text" : "password"} value={form.mat_khau_cu}
                  onChange={e => setForm({ ...form, mat_khau_cu: e.target.value })} required />
                <EyeBtn field="cu" />
              </div>
            </div>
            <div>
              <Label>Mật khẩu mới</Label>
              <div className="relative mt-1">
                <Input type={show.moi ? "text" : "password"} placeholder="Tối thiểu 8 ký tự, có chữ hoa và số"
                  value={form.mat_khau_moi}
                  onChange={e => setForm({ ...form, mat_khau_moi: e.target.value })} required />
                <EyeBtn field="moi" />
              </div>
            </div>
            <div>
              <Label>Xác nhận mật khẩu mới</Label>
              <div className="relative mt-1">
                <Input type={show.xn ? "text" : "password"} value={form.xac_nhan}
                  onChange={e => setForm({ ...form, xac_nhan: e.target.value })} required />
                <EyeBtn field="xn" />
              </div>
            </div>
            <Button type="submit" className="w-full bg-orange-600 hover:bg-orange-700 h-11" disabled={dangTai}>
              {dangTai ? "Đang lưu..." : "Đổi mật khẩu"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
