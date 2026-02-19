# CFAI Backend (Motia)
# Multi-stage build for smaller image

FROM node:20-alpine AS base
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app

# Dependencies
FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/backend/package.json ./apps/backend/
COPY packages/db/package.json ./packages/db/
COPY packages/types/package.json ./packages/types/
RUN pnpm install --frozen-lockfile

# Build
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm install
WORKDIR /app/apps/backend
RUN pnpm exec prisma generate --schema=../../packages/db/prisma/schema.prisma || true
RUN pnpm exec motia build || true
# Motia may not have a build step - dev mode runs directly
WORKDIR /app

# Runner
FROM base AS runner
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json
COPY --from=deps /app/pnpm-workspace.yaml ./
COPY --from=deps /app/pnpm-lock.yaml ./
COPY packages ./packages
COPY apps/backend ./apps/backend
WORKDIR /app/apps/backend
RUN pnpm exec prisma generate --schema=../../packages/db/prisma/schema.prisma
EXPOSE 3001
CMD ["pnpm", "run", "dev"]
