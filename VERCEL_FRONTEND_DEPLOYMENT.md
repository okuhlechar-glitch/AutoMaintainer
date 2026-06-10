# Deploy AutoMaintainer Frontend to Vercel

This guide deploys the **frontend only** to Vercel while keeping the **backend on Render**.

## Prerequisites

1. **Vercel account** (free) — https://vercel.com
2. **GitHub account** with the AutoMaintainer repository forked
3. **Render backend URL** — e.g., `https://automaintainer-backend.onrender.com`

## Step 1: Deploy Frontend to Vercel

1. Go to https://vercel.com
2. Click **"Add New..." → "Project"**
3. Select your **AutoMaintainer** GitHub repository
4. Configure:
   - **Project Name**: `automaintainer-frontend` (or your choice)
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `./frontend`
5. Click **"Deploy"**

Vercel will auto-build and deploy. You'll get a live URL like `https://automaintainer-frontend.vercel.app`

## Step 2: Set Backend API URL

1. In Vercel dashboard, click your project
2. Go to **Settings → Environment Variables**
3. Add:
   - **Name**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://automaintainer-backend.onrender.com/api`
   - **Environment**: Production
4. Click **"Save"**
5. Trigger a redeploy: **Deployments → Redeploy**

## Step 3: Update Backend CORS Settings

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click your **automaintainer-backend** service
3. Go to **Environment** tab
4. Update `CORS_ORIGINS`:
   ```
   https://automaintainer-frontend.vercel.app,http://localhost:3000
   ```
5. Click **Save Changes** (backend will restart)

## Step 4: Keep Backend Awake with UptimeRobot

Follow the [UptimeRobot Setup Guide](./UPTIMEROBOT_SETUP.md) to keep your Render backend from sleeping.

## Verification

1. Open your Vercel frontend URL in a browser
2. You should see the AutoMaintainer dashboard
3. Click **"Run Demo Pipeline"** to test the full workflow
4. Check [UptimeRobot Dashboard](https://uptimerobot.com) to confirm backend is "Up"

## Cost Summary

| Service | Cost | Notes |
|---------|------|-------|
| Vercel Frontend | **Free** | Pro-tier features available ($20/month) |
| Render Backend | **Free** | 0.5 CPU, 512 MB RAM |
| UptimeRobot | **Free** | Pings every 5 min to keep backend awake |
| **Total** | **$0/month** | 100% free tier |

## Troubleshooting

**Frontend shows blank page or errors:**
- Check browser console (F12) for CORS errors
- Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel environment
- Ensure backend CORS includes your Vercel frontend URL

**Backend not responding:**
- Check Render backend logs
- Verify UptimeRobot is pinging the health endpoint
- Ensure backend service is "Live" in Render dashboard

**Pipeline stuck or failing:**
- Check backend logs on Render
- Verify API keys are set in backend environment variables
- Ensure GitHub token has appropriate permissions

## Auto-Deployment

**Frontend:**
- Push changes to `main` → Vercel auto-deploys

**Backend:**
- Push changes to `main` → Render auto-deploys
- To manually trigger: Render Dashboard → **Manual Deploy**

## Next Steps

- [UptimeRobot Setup Guide](./UPTIMEROBOT_SETUP.md)
- [Render Backend Deployment Guide](./RENDER_DEPLOYMENT.md)
- [GitHub Repository](https://github.com/okuhlecharlieman/AutoMaintainer)
