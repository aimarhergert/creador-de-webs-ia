import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Production: set NEXT_PUBLIC_API_URL to your backend URL
  // For Hostinger static deploy, use output: 'export' and set env vars
  // output: process.env.NEXT_EXPORT === "true" ? "export" : undefined,

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
