# CFAI VPS Deployment (Hetzner / Vultr)

## Architecture

```
Internet → Caddy (:80/:443) → Next.js (:3000)
                ↓
         Backend (:3001, internal)
                ↓
    Postgres (:5432) + Redis (:6379)
```

- **Caddy**: Reverse proxy, SSL termination
- **Web**: Next.js (NextAuth, server actions)
- **Backend**: Motia (Redis state, BullMQ, SSE)
- **Postgres**: Docker volume persistence
- **Redis**: State, queues, FMP cache, status pub/sub

## Prerequisites

- VPS (2GB+ RAM recommended, e.g. Hetzner CPX11, Vultr)
- Domain pointing to VPS (optional, for HTTPS)

## Quick Start

```bash
# 1. Clone and configure
git clone <repo>
cd cfai
cp .env.example .env
# Edit .env: POSTGRES_PASSWORD, BACKEND_API_KEY, NEXTAUTH_*, GOOGLE_*, FMP_*

# 2. Generate secrets
openssl rand -hex 32   # → BACKEND_API_KEY
openssl rand -base64 32  # → NEXTAUTH_SECRET

# 3. Run
docker compose up -d

# 4. Migrations (first run)
docker compose exec web pnpm exec prisma migrate deploy --schema=../../packages/db/prisma/schema.prisma
```

## Caddy with Custom Domain

Edit `Caddyfile`:

```caddy
cfai.example.com {
    reverse_proxy web:3000
}
```

Caddy will auto-provision HTTPS via Let's Encrypt.

## Environment Checklist

- [ ] `POSTGRES_PASSWORD`
- [ ] `BACKEND_API_KEY` (same in web and backend)
- [ ] `NEXTAUTH_URL` (https://your-domain.com)
- [ ] `NEXTAUTH_SECRET`
- [ ] `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- [ ] `GOOGLE_API_KEY` (Gemini)
- [ ] `FMP_API_KEY`

## Local Development (without Docker)

```bash
# Terminal 1: Postgres + Redis
docker compose up postgres redis -d

# Terminal 2: Backend
cd apps/backend && pnpm dev
# DATABASE_URL=postgresql://cfai:changeme@localhost:5432/cfai
# REDIS_URL=redis://localhost:6379
# BACKEND_API_KEY=<generated>

# Terminal 3: Web
cd apps/web && pnpm dev
# BACKEND_URL=http://localhost:3001
# BACKEND_API_KEY=<same as backend>
```
