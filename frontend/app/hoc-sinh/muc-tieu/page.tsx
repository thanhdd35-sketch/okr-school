"use client";
// Trang này chuyển thẳng về trang chính học sinh (đã có đầy đủ chức năng)
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function MucTieuHSPage() {
  const router = useRouter();
  useEffect(() => { router.replace("/hoc-sinh"); }, []);
  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-gray-400">Đang chuyển trang...</p>
    </div>
  );
}
