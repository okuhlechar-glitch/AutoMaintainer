# Deploy AutoMaintainer — Vercel + Oracle Cloud (100% Free, Forever)

```
┌─────────────────┐         ┌──────────────────────┐
│   Vercel (free)  │  ──▶   │  Oracle Cloud (free)  │
│   Next.js UI     │  /api  │  FastAPI + SQLite     │
│   Global CDN     │         │  ARM / 24 GB RAM      │
└─────────────────┘         └──────────────────────┘
```

## Part 1: Oracle Cloud Backend

### 1a. Create Oracle Account & Instance

1. Go to https://cloud.oracle.com → **Sign Up** (free, requires credit card for verification only)
2. In the console: **Compute → Instances → Create Instance**
3. Configure:
   - **Name:** `automaintainer`
   - **Placement:** Always Free eligible
   - **Image:** Ubuntu 22.04 Minimal (Always Free)
   - **Shape:** VM.Standard.A1.Flex — **4 OCPUs, 24 GB RAM** (Always Free)
   - **SSH key:** Download the key pair
   - **Networking:** Create new VCN with public subnet
4. Click **Create** and wait ~2 minutes

### 1b. Open Port 80

Oracle has **two** firewalls. Open both:

**Cloud Security List:**
1. Console → Networking → Virtual Cloud Networks → your VCN
2. Click your **Subnet** → click the **Security List**
3. **Add Ingress Rule:**
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: TCP
   - Destination Port Range: `80`

**Instance iptables** (run on the server):
```bash
# This is done automatically by oracle-setup.sh
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save
```

### 1c. Deploy the Backend

SSH into your Oracle instance:
```bash
ssh -i ~/Downloads/ssh-key-*.key ubuntu@<YOUR_ORACLE_PUBLIC_IP>
```

Run the setup script:
```bash
curl -sL https://raw.githubusercontent.com/okuhlecharlieman/AutoMaintainer/main/oracle-setup.sh | bash
```

Or do it manually:
```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin git
sudo systemctl enable docker && sudo systemctl start docker

git clone https://github.com/okuhlecharlieman/AutoMaintainer.git
cd AutoMaintainer

# Add your API keys
nano .env
# Set: DASHSCOPE_API_KEY=sk-...
# Set: GITHUB_TOKEN=ghp_...

# Build and start
docker compose -f docker-compose.backend.yml up -d --build

# Verify
curl http://localhost/api/health
# → {"status":"healthy","service":"automaintainer-backend"}

# Get your public IP
curl -s ifconfig.me
```

**Save this IP** — you need it for Vercel.

---

## Part 2: Vercel Frontend

### 2a. Deploy to Vercel

1. Go to https://vercel.com → **Sign up with GitHub**
2. **Add New → Project**
3. Import `okuhlecharlieman/AutoMaintainer`
4. Configure:
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (auto-detected)
   - **Output Directory:** `.next` (auto-detected)
5. Add **Environment Variable:**
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `http://<YOUR_ORACLE_IP>/api`
6. Click **Deploy**

### 2b. Verify

Vercel gives you a URL like `automaintainer-xxxx.vercel.app`. Open it and:
- Dashboard should load
- Click **Run Demo Pipeline** — should start processing
- API calls go to your Oracle backend

---

## Updating After Code Changes

### Update Backend (Oracle):
```bash
ssh ubuntu@<ORACLE_IP>
cd AutoMaintainer
git pull
docker compose -f docker-compose.backend.yml up -d --build
```

### Update Frontend (Vercel):
Just push to `main` — Vercel auto-deploys on push.

---

## Cost Summary

| Service | Cost | Limits |
|---------|------|--------|
| Vercel | **R0** | 100 GB bandwidth/month, 100 builds/day |
| Oracle Cloud | **R0** | 4 ARM CPUs, 24 GB RAM, 200 GB disk, forever |
| DashScope | **R0** | 70M tokens free (1,700+ pipeline runs) |
| GitHub | **R0** | Public repos + PAT |
| **Total** | **R0/month** | **Forever** |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Can't reach Oracle IP from browser | Check BOTH security list AND iptables for port 80 |
| Vercel shows CORS errors | Backend `CORS_ORIGINS` is already set to `*` in docker-compose.backend.yml |
| Pipeline stuck | Check Oracle backend logs: `docker compose logs -f backend` |
| Oracle instance unreachable | Oracle sometimes reclaims idle free instances — just recreate |
| Vercel build fails | Check Root Directory is set to `frontend` |
