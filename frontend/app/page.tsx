"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const token = localStorage.getItem("okr_token");
    const user = localStorage.getItem("okr_user");
    if (token && user) {
      const u = JSON.parse(user);
      const map: Record<string, string> = {
        quan_tri: "/quan-tri", giao_vien: "/giao-vien",
        hoc_sinh: "/hoc-sinh", phu_huynh: "/phu-huynh"
      };
      router.push(map[u.vai_tro] || "/dang-nhap");
    } else {
      router.push("/dang-nhap");
    }
  }, []);
  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-gray-400">Äang táº£i...</p>
    </div>
  );
}

