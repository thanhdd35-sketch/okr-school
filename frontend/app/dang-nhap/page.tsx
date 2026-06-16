"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";
import api from "@/lib/api";
import { useStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function DangNhapPage() {
  const router = useRouter();
  const { datNguoiDung } = useStore();
  const [dangTai, setDangTai] = useState(false);
  const [hienMatKhau, setHienMatKhau] = useState(false);
  const [hienMatKhauPH, setHienMatKhauPH] = useState(false);
  const [resetingAdmin, setResetingAdmin] = useState(false);

  async function khoiPhucAdmin() {
    if (!confirm("Reset mật khẩu admin về Admin@2025?")) return;
    setResetingAdmin(true);
    try {
      await api.post("/api/v1/xac-thuc/khoi-phuc-admin", {});
      toast.success("Đã reset! Đăng nhập với: admin@truong.edu.vn / Admin@2025");
    } catch { toast.error("Không thể reset admin"); }
    finally { setResetingAdmin(false); }
  }

  const [form, setForm] = useState({ email: "", mat_khau: "" });
  const [formPH, setFormPH] = useState({ email_phu_huynh: "", mat_khau_hoc_sinh: "" });

  async function xuLyDangNhap(e: React.FormEvent) {
    e.preventDefault();
    setDangTai(true);
    try {
      const res = await api.post("/api/v1/xac-thuc/dang-nhap", form);
      const { token, vai_tro, ho_ten, bat_buoc_doi_mat_khau, ten_lop, id } = res.data;
      datNguoiDung({ id: id || "", email: form.email, vai_tro, ho_ten, ten_lop }, token);
      if (bat_buoc_doi_mat_khau) {
        router.push("/doi-mat-khau");
      } else {
        chuyenHuong(vai_tro);
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Đăng nhập thất bại");
    } finally { setDangTai(false); }
  }

  async function xuLyDangNhapPH(e: React.FormEvent) {
    e.preventDefault();
    setDangTai(true);
    try {
      const res = await api.post("/api/v1/xac-thuc/dang-nhap-phu-huynh", formPH);
      const { token, ho_ten_con, lop } = res.data;
      datNguoiDung({
        id: "", email: formPH.email_phu_huynh, vai_tro: "phu_huynh",
        ho_ten: `Phụ huynh của ${ho_ten_con}`, ten_lop: lop, ho_ten_con,
      }, token);
      router.push("/phu-huynh");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Đăng nhập thất bại");
    } finally { setDangTai(false); }
  }

  function chuyenHuong(vai_tro: string) {
    const map: Record<string, string> = {
      quan_tri: "/quan-tri", giao_vien: "/giao-vien",
      hoc_sinh: "/hoc-sinh", phu_huynh: "/phu-huynh",
    };
    router.push(map[vai_tro] || "/");
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 to-orange-100 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-orange-700">Hệ thống OKR</h1>
          <p className="text-gray-500 mt-1">Quản lý mục tiêu học sinh</p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-center text-gray-700">Đăng nhập</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="nguoidung">
              <TabsList className="w-full mb-6">
                <TabsTrigger value="nguoidung" className="flex-1">Giáo viên / Học sinh</TabsTrigger>
                <TabsTrigger value="phuhuynh" className="flex-1">Phụ huynh</TabsTrigger>
              </TabsList>

              {/* Tab Giáo viên / Học sinh / Quản trị */}
              <TabsContent value="nguoidung">
                <form onSubmit={xuLyDangNhap} className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium">Email</Label>
                    <Input type="email" placeholder="email@truong.edu.vn"
                      value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
                      className="mt-1" required />
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Mật khẩu</Label>
                    <div className="relative mt-1">
                      <Input type={hienMatKhau ? "text" : "password"} placeholder="Nhập mật khẩu"
                        value={form.mat_khau} onChange={e => setForm({ ...form, mat_khau: e.target.value })}
                        className="pr-10" required />
                      <button type="button" onClick={() => setHienMatKhau(!hienMatKhau)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                        {hienMatKhau ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>
                  <Button type="submit" className="w-full bg-orange-600 hover:bg-orange-700 h-11 text-base" disabled={dangTai}>
                    {dangTai ? "Đang đăng nhập..." : "Đăng nhập"}
                  </Button>
                  <p className="text-center text-xs text-gray-400 mt-2">
                    Quên mật khẩu?{" "}
                    <span className="text-orange-600 font-medium">
                      Học sinh liên hệ giáo viên · Giáo viên liên hệ quản trị viên
                    </span>
                  </p>
                </form>

                {/* Tài khoản mẫu */}
                <div className="mt-6 p-4 bg-orange-50 rounded-xl border border-orange-200">
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-xs font-semibold text-orange-700">Tài khoản mẫu:</p>
                    <button type="button" onClick={khoiPhucAdmin} disabled={resetingAdmin}
                      className="text-xs text-red-500 hover:text-red-700 underline disabled:opacity-50">
                      {resetingAdmin ? "Đang reset..." : "Reset admin"}
                    </button>
                  </div>
                  <div className="space-y-1 text-xs text-orange-600">
                    <div className="flex justify-between">
                      <span>Quản trị:</span>
                      <span className="font-mono">admin@truong.edu.vn / Admin@2025</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Giáo viên:</span>
                      <span className="font-mono">giaovien1@truong.edu.vn / Gv@123456</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Học sinh:</span>
                      <span className="font-mono">hocsinh1@truong.edu.vn / Hs@123456</span>
                    </div>
                  </div>
                </div>
              </TabsContent>

              {/* Tab Phụ huynh */}
              <TabsContent value="phuhuynh">
                <form onSubmit={xuLyDangNhapPH} className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium">Email phụ huynh</Label>
                    <Input type="email" placeholder="email phụ huynh"
                      value={formPH.email_phu_huynh}
                      onChange={e => setFormPH({ ...formPH, email_phu_huynh: e.target.value })}
                      className="mt-1" required />
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Mật khẩu của con</Label>
                    <div className="relative mt-1">
                      <Input type={hienMatKhauPH ? "text" : "password"} placeholder="Mật khẩu học sinh"
                        value={formPH.mat_khau_hoc_sinh}
                        onChange={e => setFormPH({ ...formPH, mat_khau_hoc_sinh: e.target.value })}
                        className="pr-10" required />
                      <button type="button" onClick={() => setHienMatKhauPH(!hienMatKhauPH)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                        {hienMatKhauPH ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>
                  <Button type="submit" className="w-full bg-green-600 hover:bg-green-700 h-11 text-base" disabled={dangTai}>
                    {dangTai ? "Đang đăng nhập..." : "Đăng nhập (Phụ huynh)"}
                  </Button>
                </form>

                {/* Tài khoản mẫu phụ huynh */}
                <div className="mt-6 p-4 bg-green-50 rounded-xl border border-green-200">
                  <p className="text-xs font-semibold text-green-700 mb-2">Tài khoản mẫu phụ huynh:</p>
                  <div className="space-y-1 text-xs text-green-600">
                    <div className="flex justify-between">
                      <span>Email phụ huynh:</span>
                      <span className="font-mono">phuhuynh1@gmail.com</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Mật khẩu của con:</span>
                      <span className="font-mono">Hs@123456</span>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-gray-400 mt-4">
          © 2025 Hệ thống OKR Trường học
        </p>
      </div>
    </div>
  );
}
