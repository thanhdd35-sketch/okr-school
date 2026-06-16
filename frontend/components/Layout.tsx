"use client";
import { useRouter, usePathname } from "next/navigation";
import { useStore } from "@/lib/store";

interface MenuItem { href: string; label: string; icon?: string; }
interface LayoutProps { children: React.ReactNode; menu: MenuItem[]; tieuDe: string; }

export default function Layout({ children, menu, tieuDe }: LayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { nguoiDung, dangXuat } = useStore();
  function xuLyDangXuat() { dangXuat(); router.push("/dang-nhap"); }
  return (
    <div className="flex h-screen bg-gray-50">
      <div className="w-56 bg-orange-700 text-white flex flex-col shadow-xl flex-shrink-0">
        <div className="p-3 border-b border-orange-600 flex items-center justify-center">
          <img src="/logo-fpt.jpg" alt="FPT Schools" className="w-full max-w-[180px] object-contain rounded" />
        </div>
        <div className="px-4 py-3 border-b border-orange-600 bg-orange-800">
          <div className="text-xs text-orange-300">Xin chào,</div>
          <div className="text-sm font-semibold truncate">{nguoiDung?.ho_ten}</div>
          <div className="text-xs text-orange-300 mt-0.5 font-medium">{tieuDe}</div>
        </div>
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          {menu.map(item => {
            const active = pathname === item.href;
            return (
              <button key={item.href} onClick={() => router.push(item.href)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${active ? "bg-white text-orange-700 shadow-sm" : "text-orange-100 hover:bg-orange-600 hover:text-white"}`}>
                {item.label}
              </button>
            );
          })}
        </nav>
        <div className="p-3 border-t border-orange-600">
          <button onClick={xuLyDangXuat} className="w-full text-xs text-orange-200 hover:text-white hover:bg-orange-600 py-2 px-3 rounded-lg transition-colors text-left">
            Đăng xuất
          </button>
        </div>
      </div>
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <header className="bg-white border-b px-6 py-3 flex items-center justify-between shadow-sm flex-shrink-0">
          <h1 className="text-base font-semibold text-gray-800">{tieuDe}</h1>
          <div className="text-sm text-gray-400">{nguoiDung?.ten_lop && `Lớp ${nguoiDung.ten_lop}`}</div>
        </header>
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
