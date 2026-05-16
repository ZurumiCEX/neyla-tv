# Image Next.js (dev). Build prod (multi-stage) à venir en Phase 6.
FROM node:20-alpine

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY apps/web/ ./

EXPOSE 3000

CMD ["npm", "run", "dev"]
