import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  // Enable transpilation for video.js and other packages
  transpilePackages: ["video.js"],

  // Turbopack configuration (Next.js 16+ uses Turbopack by default)
  turbopack: {},

  // Webpack configuration for video.js (fallback if using --webpack flag)
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
    }
    return config;
  },
};

export default nextConfig;
