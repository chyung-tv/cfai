# CFAI Deployment Guide

## Architecture Overview

**⚠️ Critical**: This monorepo requires **separate deployment** of frontend and backend due to Motia's architectural requirements.

```
┌─────────────────────┐         ┌──────────────────────┐
│   Vercel (Web)      │         │  Docker/Railway      │
│   ===============   │         │  ================    │
│   Next.js 15 App    │◄───────►│  Motia Backend       │
│   NextAuth          │  HTTP   │  + BullMQ Workers    │
│   Port 3000         │  + WS   │  + Redis             │
└─────────────────────┘         │  Port 3001           │
         │                      └──────────────────────┘
         │                               │
         └───────────────┬───────────────┘
                         ▼
                ┌────────────────┐
                │ Vercel Postgres│
                │ (Shared DB)    │
                └────────────────┘
```

### Why Separate Deployments?

**Motia Backend Requirements:**

- ✅ Persistent WebSocket connections (streams)
- ✅ Long-running background workers (BullMQ)
- ✅ Redis for state management and job queues
- ❌ **Cannot run on Vercel** (serverless functions timeout after 60s-300s)

**Next.js Frontend:**

- ✅ Serverless-friendly (no persistent connections)
- ✅ Perfect for Vercel deployment
- ✅ Uses Vercel Postgres for database

## Option 1: Recommended Production Setup (Motia Cloud)

### Frontend: Vercel

### Backend: Motia Cloud (Managed Motia Hosting)

**Why Motia Cloud:**

- ✅ Built specifically for Motia applications
- ✅ Redis, BullMQ, and WebSocket support included
- ✅ One-click deployment from Workbench
- ✅ Free tier available
- ✅ Auto-scaling and monitoring
- ✅ No Docker configuration needed

## Option 2: Self-Hosted with Railway

### Frontend: Vercel

### Backend: Railway (with Redis)

---

## 1. Backend Deployment (Motia Cloud)

### Prerequisites

- Motia version 0.6.4 or higher (check `apps/backend/package.json`)
- Motia Cloud account ([motia.cloud](https://motia.cloud))
- Local backend running (`cd apps/backend && pnpm dev`)

### Method 1: One-Click Web Deployment (Recommended)

**Steps:**

1. **Start your local Motia backend**

   ```bash
   cd apps/backend
   pnpm dev
   # Backend runs on http://localhost:3001
   ```

2. **Go to Motia Cloud**
   - Visit [motia.cloud](https://motia.cloud)
   - Sign in with your account
   - Navigate to **"Import from Workbench"**

3. **Configure deployment**
   - **Port**: `3001` (your local backend port)
   - **Project name**: `cfai-backend` (or your choice)
   - **Environment name**: `production` (or `staging`)

4. **Add environment variables**
   - Option A: Upload `.env` file from `apps/backend`
   - Option B: Paste environment variables manually:
     ```bash
     DATABASE_URL=<vercel-postgres-url>
     GOOGLE_API_KEY=your-google-ai-api-key
     FMP_API_KEY=your-fmp-api-key
     FMP_BASE_URL=https://financialmodelingprep.com/api/v3
     ```

5. **Click Deploy**
   - Motia Cloud will:
     - Bundle your steps and streams
     - Set up Redis automatically
     - Configure BullMQ workers
     - Deploy with WebSocket support
   - Watch deployment progress in real-time

6. **Get your backend URL**
   - After deployment: `https://your-project.motia.cloud`
   - Save this for frontend configuration

### Method 2: CLI Deployment

**Setup:**

```bash
# Install Motia CLI globally (if not already)
npm install -g motia

# Get API key from Motia Cloud dashboard
export MOTIA_API_KEY="your-motia-cloud-api-key"
```

**Deploy:**

```bash
cd apps/backend

# Basic deployment
motia cloud deploy \
  --api-key $MOTIA_API_KEY \
  --version-name 1.0.0

# With environment file
motia cloud deploy \
  --api-key $MOTIA_API_KEY \
  --version-name 1.0.0 \
  --env-file .env.production

# To specific environment
motia cloud deploy \
  --api-key $MOTIA_API_KEY \
  --version-name 1.0.0 \
  --environment-id your-env-id \
  --env-file .env.production
```

### Including Static Files

If you have template files or binaries in your steps:

```typescript
// In your step config
export const config: EventConfig = {
  name: "MyStep",
  type: "event",
  includeFiles: [
    "./templates/email.mustache", // Relative to step file
    "./binaries/ffmpeg", // Binary (linux_amd64, <100MB)
  ],
  // ... rest of config
};
```

**Verify bundling:**

```bash
cd apps/backend
npx motia build

# Check dist/ folder to ensure files are included
ls -la dist/node/steps/**/*.zip
```

### Troubleshooting Motia Cloud Deployment

**"Build failed"**

- Run `npx motia build` locally to check for errors
- Ensure all step configs are valid
- Check that `includeFiles` paths are correct

**"Environment variables not working"**

- Verify you uploaded/pasted `.env` correctly
- Check variable names match exactly (case-sensitive)
- Test locally with same `.env` first

**"WebSocket connection failed"**

- Ensure frontend uses Motia Cloud backend URL
- Check CORS settings if applicable
- Verify stream subscriptions use correct `address`

---

## 2. Frontend Deployment (Vercel)

### Step 1: Connect Your Repository

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Vercel will auto-detect the Turborepo monorepo

### Step 2: Configure Project Settings

- **Framework Preset**: Next.js
- **Root Directory**: `apps/web`
- **Build Command**: `cd ../.. && turbo build --filter=web` (auto-detected)
- **Output Directory**: `.next` (default)
- **Install Command**: `pnpm install` (auto-detected)

### Step 3: Add Environment Variables

Go to **Project Settings → Environment Variables** and add:

```bash
# Database (use Vercel Postgres)
DATABASE_URL=<from-vercel-postgres>

# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# NextAuth Configuration
NEXTAUTH_URL=https://yourdomain.vercel.app
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>
```

**🔒 Security**: Generate `NEXTAUTH_SECRET` with:

```bash
openssl rand -base64 32
```

### Step 4: Connect Vercel Postgres

1. Go to **Storage** tab
2. Create **Postgres** database
3. Database URL will auto-populate in `DATABASE_URL`
4. Run migrations (see below)

### Step 5: Deploy

1. Click **Deploy**
2. After successful deployment, run Prisma migrations (one-time):
   ```bash
   # From your local machine
   cd packages/db
   DATABASE_URL="<vercel-postgres-url>" npx prisma migrate deploy
   ```

## 2. Frontend Deployment (Vercel)

### Step 1: Connect Your Repository

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Vercel will auto-detect the Turborepo monorepo

### Step 2: Configure Project Settings

- **Framework Preset**: Next.js
- **Root Directory**: `apps/web`
- **Build Command**: `cd ../.. && turbo build --filter=web` (auto-detected)
- **Output Directory**: `.next` (default)
- **Install Command**: `pnpm install` (auto-detected)

### Step 3: Add Environment Variables

Go to **Project Settings → Environment Variables** and add:

```bash
# Database (use Vercel Postgres)
DATABASE_URL=<from-vercel-postgres>

# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# NextAuth Configuration
NEXTAUTH_URL=https://yourdomain.vercel.app
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>

# Backend API (from Motia Cloud deployment)
NEXT_PUBLIC_BACKEND_URL=https://your-project.motia.cloud
```

**🔒 Security**: Generate `NEXTAUTH_SECRET` with:

```bash
openssl rand -base64 32
```

### Step 4: Connect Vercel Postgres

1. Go to **Storage** tab
2. Create **Postgres** database
3. Database URL will auto-populate in `DATABASE_URL`
4. Run migrations (see below)

### Step 5: Deploy

1. Click **Deploy**
2. After successful deployment, run Prisma migrations (one-time):
   ```bash
   # From your local machine
   cd packages/db
   DATABASE_URL="<vercel-postgres-url>" npx prisma migrate deploy
   ```

---

## 3. Alternative: Self-Hosted Backend (Railway)

Only use this if you prefer self-hosting over Motia Cloud.

### Why Railway?

- ✅ Native Docker support
- ✅ Built-in Redis (single click)
- ✅ PostgreSQL support (can use same Vercel Postgres)
- ✅ Persistent processes for Motia
- ✅ WebSocket support
- ✅ Free tier available

### Step 1: Setup Railway Project

1. Go to [railway.app](https://railway.app)
2. Create new project
3. Add **Redis** service (from template)
4. Add **Web Service** (from GitHub)

### Step 2: Configure Backend Service

- **Root Directory**: `apps/backend`
- **Build Command**: `pnpm install && pnpm run build` (Railway auto-detects)
- **Start Command**: `pnpm run dev` (Motia doesn't need build for production)

### Step 3: Add Environment Variables

In Railway dashboard, add:

```bash
# Database (use Vercel Postgres connection string)
DATABASE_URL=<vercel-postgres-url>

# API Keys
GOOGLE_API_KEY=your-google-ai-api-key
FMP_API_KEY=your-fmp-api-key
FMP_BASE_URL=https://financialmodelingprep.com/api/v3

# Redis (Railway auto-provides these)
REDIS_HOST=redis
REDIS_PORT=6379
```

### Step 4: Connect Services

1. Railway Redis is auto-connected via internal network
2. Backend automatically connects to Vercel Postgres via `DATABASE_URL`
3. Expose backend service publicly for frontend API calls

### Step 5: Update Frontend Environment

Add backend URL to Vercel:

```bash
NEXT_PUBLIC_BACKEND_URL=https://your-backend.railway.app
```

---

## Alternative: Backend on Render.com

Similar to Railway, but different pricing:

1. Create **Web Service** from GitHub
2. Add **Redis** instance ($7/month minimum)
3. Set Environment Variables (same as Railway)
4. Deploy

**Render Config:**

- **Build Command**: `pnpm install`
- **Start Command**: `pnpm run dev`
- **Root Directory**: `apps/backend`

---

## Alternative: Self-Hosted Docker

### Option A: Docker Compose (All Services)

```yaml
# docker-compose.yml
version: "3.8"

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: changeme
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

  backend:
    build:
      context: .
      dockerfile: apps/backend/Dockerfile
    ports:
      - "3001:3001"
    environment:
      - DATABASE_URL=postgresql://postgres:changeme@postgres:5432/postgres
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - FMP_API_KEY=${FMP_API_KEY}
    depends_on:
      - postgres
      - redis

volumes:
  postgres-data:
  redis-data:
```

Deploy web to Vercel, run backend locally/VPS.

---

## Database Migrations

**Important**: Only run migrations from ONE location to avoid conflicts.

### First-Time Setup (Production)

```bash
# From local machine with Vercel Postgres URL
cd packages/db
DATABASE_URL="<vercel-postgres-url>" npx prisma migrate deploy
```

### Future Migrations

1. Develop migration locally
2. Commit migration files
3. Deploy frontend (triggers auto-migration via Prisma)
4. Backend auto-connects to updated schema

---

## Environment Variable Checklist

### Vercel (Frontend)

- [ ] `DATABASE_URL` (from Vercel Postgres)
- [ ] `GOOGLE_CLIENT_ID`
- [ ] `GOOGLE_CLIENT_SECRET`
- [ ] `NEXTAUTH_URL` (production domain)
- [ ] `NEXTAUTH_SECRET` (generated for production)
- [ ] `NEXT_PUBLIC_BACKEND_URL` (Motia Cloud backend URL)

### Motia Cloud (Backend)

- [ ] `DATABASE_URL` (same as Vercel Postgres)
- [ ] `GOOGLE_API_KEY`
- [ ] `FMP_API_KEY`
- [ ] `FMP_BASE_URL`

**Note**: Redis and BullMQ are auto-configured by Motia Cloud - no manual env vars needed!

---

## Turborepo Caching on Vercel

**Already configured!** `turbo.json` now includes:

- App-specific `env` arrays for cache invalidation
- `globalEnv` for `DATABASE_URL`
- `globalDependencies` for Prisma schema changes

This prevents cache poisoning and ensures correct builds.

---

## Cost Estimates

### Recommended Stack (Vercel + Motia Cloud)

- **Vercel**: $0/month (Hobby) or $20/month (Pro)
- **Vercel Postgres**: $0.25/month (Hobby) or $40/month (Pro)
- **Motia Cloud**: Free tier available, check [motia.cloud/pricing](https://motia.cloud/pricing)
- **Total**: ~$0-60/month depending on usage

### Alternative (Vercel + Railway Self-Hosted)

- **Vercel**: Same as above
- **Railway**: $5/month (credit-based, includes Redis)
- **Total**: ~$5-65/month

---

## Troubleshooting

### "Cannot connect to backend"

- Check `NEXT_PUBLIC_BACKEND_URL` is set in Vercel
- Verify Motia Cloud backend is running (check dashboard)
- Test backend directly: `curl https://your-project.motia.cloud/hello`
- Ensure CORS is configured if needed

### "Motia Cloud deployment stuck"

- Check build logs in Motia Cloud dashboard
- Run `npx motia build` locally to verify no errors
- Ensure all dependencies are in `package.json`
- Check that `motia` package version is 0.6.4+

### "Stream connection failed"

- Verify `NEXT_PUBLIC_BACKEND_URL` includes protocol (https://)
- Check Motia Cloud WebSocket endpoint is accessible
- Test stream connection in browser console
- Ensure stream client uses correct `address` parameter

### "Database connection error"

- Ensure `DATABASE_URL` is identical in Vercel and Railway
- Check Vercel Postgres is running
- Verify network access (Vercel Postgres allows external connections)

### "NextAuth callback error"

- Verify `NEXTAUTH_URL` matches your Vercel domain exactly
- Check Google OAuth redirect URIs include Vercel domain
- Generate new `NEXTAUTH_SECRET` if migrating from local

### "Turborepo cache miss"

- Normal after env var changes (intentional cache invalidation)
- Check `turbo.json` env arrays include all inlined variables
- View Run Summary in Vercel deployment details

---

## Security Checklist

- [ ] Different `NEXTAUTH_SECRET` for production vs staging
- [ ] Google OAuth restricted to production domains
- [ ] Database URL uses SSL (`?sslmode=require`)
- [ ] API keys rotated periodically
- [ ] `.env` files never committed to git
- [ ] Vercel environment variables marked as "sensitive"
- [ ] Railway environment variables encrypted

---

## Next Steps After Deployment

1. **Setup monitoring**: Add Vercel Analytics, Railway logging
2. **Configure domains**: Custom domain in Vercel + Railway
3. **Enable caching**: Add Vercel KV for API response caching
4. **Setup alerts**: Error tracking (Sentry, LogRocket)
5. **Performance**: Enable Vercel Edge Functions for `/api` routes
6. **Backup**: Schedule Postgres backups (Vercel automatic)

---

## Questions?

See `.env.example` for all environment variable documentation.

Check `.github/copilot-instructions.md` for development patterns.
