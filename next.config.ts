import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    MANIM_API_URL: process.env.MANIM_API_URL || "http://localhost:5000",
  },
};

export default nextConfig;
