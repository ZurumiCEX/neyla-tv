// En-têtes de sécurité : CSP stricte sur les scripts (seul Turnstile est externe),
// pas d'objets, pas d'intégration dans un iframe tiers, pas de sniffing MIME.
// Les connexions restent ouvertes en https/wss : API, Bunny (HLS) et R2 varient
// selon l'environnement.
const isDev = process.env.NODE_ENV !== "production";

// Origine de l'API (et son équivalent WebSocket), autorisée même en http (local, Docker).
function apiOrigins() {
  try {
    const url = new URL(process.env.NEXT_PUBLIC_API_URL || "");
    const ws = url.protocol === "https:" ? "wss:" : "ws:";
    return ` ${url.origin} ${ws}//${url.host}`;
  } catch {
    return "";
  }
}

const csp = [
  "default-src 'self'",
  // Next.js injecte des scripts inline ; 'unsafe-eval' uniquement en dev (HMR).
  `script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https: http:",
  "media-src 'self' blob: https: http:",
  "font-src 'self' data:",
  `connect-src 'self' https: wss:${apiOrigins()}${isDev ? " http: ws:" : ""}`,
  "frame-src https://challenges.cloudflare.com",
  "worker-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'self'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "SAMEORIGIN" },
  {
    key: "Permissions-Policy",
    value:
      "camera=(), microphone=(), geolocation=(), payment=(), publickey-credentials-get=(self), publickey-credentials-create=(self)",
  },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Build standalone (.next/standalone, serveur Node minimal) pour l'image Docker prod.
  // Sur Vercel, on laisse la plateforme gérer la sortie (VERCEL=1 fourni au build).
  output: process.env.VERCEL ? undefined : "standalone",
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
