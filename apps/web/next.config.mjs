/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Build standalone (.next/standalone, serveur Node minimal) pour l'image Docker prod.
  // Sur Vercel, on laisse la plateforme gérer la sortie (VERCEL=1 fourni au build).
  output: process.env.VERCEL ? undefined : "standalone",
};

export default nextConfig;
