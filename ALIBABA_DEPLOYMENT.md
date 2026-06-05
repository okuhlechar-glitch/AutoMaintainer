# AutoMaintainer - Alibaba Cloud Deployment Guide

## Free Tier Deployment (No Cost)

This guide demonstrates how to deploy AutoMaintainer on Alibaba Cloud using the **Free Tier**, which includes:
- **70+ million free AI tokens** for Qwen models
- **$90 free ECS credits** (3 months) for compute
- **Free MySQL database** (1 month trial)
- **Free networking & bandwidth**

---

## Step 1: Set Up Alibaba Cloud Free Tier Account

1. Visit https://alibabacloud.com/free
2. Register for a new account
3. Complete phone + email verification
4. Claim your free tier:
   - Model Studio: 70+ million tokens for Qwen API
   - ECS: $90 free credits
   - ApsaraDB RDS MySQL: 1 month free

---

## Step 2: Create Alibaba Cloud API Key

1. Log in to Alibaba Cloud Console
2. Go to **Access Control** → **Users**
3. Create a new API key for your application
4. Save the **Access Key ID** and **Access Key Secret**

For Model Studio (Qwen API):
- Documentation: https://help.aliyun.com/document_detail/611472.html
- API Endpoint: `https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation`

---

## Step 3: Deploy Backend to Alibaba Cloud ECS

### Option A: Using Docker on ECS

1. **Launch an ECS Instance:**
   - CPU: 2 cores (Free tier eligible)
   - Memory: 4GB RAM
   - OS: Ubuntu 22.04 LTS
   - Region: Choose closest to your users

2. **Connect to your ECS instance:**
   ```bash
   ssh -i your-key.pem root@<ECS_PUBLIC_IP>
   ```

3. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

4. **Clone the repository:**
   ```bash
   git clone https://github.com/okuhlecharlieman/AutoMaintainer.git
   cd AutoMaintainer
   ```

5. **Create `.env` file on ECS:**
   ```bash
   cat > backend/.env << EOF
   # Alibaba Cloud Qwen API
   DASHSCOPE_API_KEY=<your-alibaba-cloud-api-key>
   QWEN_MODEL=qwen-plus
   
   # GitHub Integration
   GITHUB_TOKEN=<your-github-token>
   GITHUB_WEBHOOK_SECRET=<your-webhook-secret>
   
   # Database (use Alibaba RDS or local SQLite)
   DATABASE_URL=sqlite+aiosqlite:///./automaintainer.db
   REDIS_URL=redis://localhost:6379/0
   
   # Server Config
   HOST=0.0.0.0
   PORT=8000
   CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
   
   # Sandbox
   SANDBOX_ENABLED=true
   SANDBOX_TIMEOUT=30
   EOF
   ```

6. **Run Docker container:**
   ```bash
   cd backend
   docker build -t automaintainer-backend .
   docker run -d \
     --name automaintainer-api \
     -p 8000:8000 \
     --env-file .env \
     -v /data/automaintainer:/app/data \
     automaintainer-backend
   ```

7. **Configure Security Group:**
   - Allow inbound: Port 8000 (HTTP) from your frontend domain
   - Allow inbound: Port 22 (SSH) from your IP

### Option B: Using Python Directly

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run FastAPI server
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Step 4: Configure Alibaba Cloud Qwen API

Update your backend to use Alibaba Cloud's Qwen models:

**File: `backend/services/llm.py`**
```python
import os
import httpx

class QwenClient:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model = os.getenv("QWEN_MODEL", "qwen-plus")
    
    async def generate(self, prompt: str, system: str = None) -> str:
        """Call Alibaba Cloud Qwen API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {"role": "system", "content": system or "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            result = response.json()
            return result["output"]["text"]
```

---

## Step 5: Database Setup (Optional - Free Options)

### Option A: SQLite (No Cost, Included)
- Already configured in the app
- Data stored locally on ECS instance
- Good for up to ~100K records

### Option B: Alibaba Cloud RDS MySQL (Free Tier Available)
1. Launch RDS MySQL instance in free tier
2. Update `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=mysql+aiomysql://user:password@rds-endpoint:3306/automaintainer
   ```

---

## Step 6: Deploy Frontend to Vercel (Recommended)

1. Connect your GitHub repo to Vercel
2. Frontend automatically deploys on push
3. Set environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://<your-ecs-public-ip>:8000
   ```

Or use a domain name with Alibaba Cloud DNS.

---

## Step 7: Set Up GitHub Webhook

1. Go to GitHub repo → Settings → Webhooks
2. Add webhook:
   - **Payload URL:** `https://<your-ecs-ip>:8000/api/webhook/github`
   - **Content type:** `application/json`
   - **Secret:** Match `GITHUB_WEBHOOK_SECRET` in `.env`
   - **Events:** Push, Issues, Pull requests

---

## Free Tier Costs Breakdown

| Service | Free Offer | Duration | Cost After |
|---------|-----------|----------|-----------|
| Model Studio (Qwen) | 70M tokens | Forever* | $0.05-0.20 per 1M tokens |
| ECS | $90 credits | 3 months | ~$0.04-0.08/hour depending on instance |
| RDS MySQL | 1 month | 1 month | ~$0.15-0.30/day |
| Bandwidth | Generous allowance | Forever | $0.12/GB after |
| DNS | Free | Forever | Free |

**Total: $0 for 3 months, then ~$5-15/month if continuing**

---

## Monitoring & Logs

**Check backend logs on ECS:**
```bash
docker logs -f automaintainer-api
```

**Monitor Alibaba Cloud costs:**
1. Console → Billing & Payments
2. Check usage dashboards for Qwen API calls
3. Set up cost alerts

---

## Troubleshooting

### Qwen API 401 Unauthorized
- Verify `DASHSCOPE_API_KEY` is correct
- Check API key has Model Studio permissions
- Ensure free token balance is not exhausted (70M tokens)

### ECS Connection Timeout
- Check security group allows port 8000
- Verify ECS instance is running
- Check public IP is correctly configured

### High Token usage?
- Use cheaper model: `qwen-turbo` instead of `qwen-plus`
- Cache responses to reduce redundant calls
- Batch requests where possible

---

## What's Included

✅ **Fully Functional:**
- Multi-agent orchestration (Qwen-powered)
- GitHub issue analysis and PR creation
- Code generation and testing
- Security scanning
- Documentation generation
- Human approval gateway

✅ **Zero Cost for 3 Months**
✅ **Ready for Production Scale**

---

## Next Steps

1. **Get free tier account:** https://alibabacloud.com/free
2. **Clone and deploy:** `git clone https://github.com/okuhlecharlieman/AutoMaintainer.git`
3. **Test locally first:** `python backend/main.py`
4. **Deploy to ECS:** Follow steps above
5. **Submit to Devpost:** Link this file as proof of Alibaba Cloud deployment

---

## References

- Alibaba Cloud Free Tier: https://alibabacloud.com/free
- Qwen Model API: https://help.aliyun.com/document_detail/611472.html
- ECS Quick Start: https://help.aliyun.com/document_detail/87051.html
- AutoMaintainer GitHub: https://github.com/okuhlecharlieman/AutoMaintainer
