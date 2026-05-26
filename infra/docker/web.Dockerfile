# Image Next.js — multi-stage : dev / prod (standalone).
# Activé par `output: 'standalone'` dans next.config.mjs.

# --- deps : install une fois, partagé ---
FROM node:20-alpine AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# --- dev : code monté en volume ---
FROM deps AS dev
COPY apps/web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
EXPOSE 3000
CMD ["npm", "run", "dev"]

# --- builder : compile l'app ---
FROM deps AS builder
COPY apps/web/ ./
# NEXT_PUBLIC_* est figé dans le bundle client au build : il faut donc le
# fournir ici. DO App Platform passe les env build-time en --build-arg.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# --- prod : runtime minimaliste, image légère ---
FROM node:20-alpine AS prod
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
