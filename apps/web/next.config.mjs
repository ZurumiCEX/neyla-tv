/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Build standalone : crée .next/standalone (Node server minimal) pour l'image prod.
  output: "standalone",
};

export default nextConfig;
