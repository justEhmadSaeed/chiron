/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true
  },
  output: "standalone",
  typedRoutes: true,
  transpilePackages: ["@chiron/contracts", "@chiron/ui"]
};

export default nextConfig;
