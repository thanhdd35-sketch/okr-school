import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://okr-backend-production-8e69.up.railway.app",
  },
};

export default nextConfig;
