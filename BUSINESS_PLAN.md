# AutoMaintainer — Business & Pricing Plan (ZAR)

## Can You Make Money?

**Yes, but with realistic expectations.** This is a specialized B2B developer tool, not a mass-market product. Success depends on finding the right niche.

### Target Customers
1. **Open-source maintainers** with popular repos (1K+ stars) drowning in issues
2. **Small dev teams** (2-10 devs) maintaining internal tools
3. **Enterprise teams** managing multiple repos
4. **Freelancers** juggling multiple client projects

---

## Pricing Tiers (Monthly, ZAR)

| Tier | Price | Pipelines/Month | Target |
|------|-------|-----------------|--------|
| **Free** | R0 | 5 | Individual maintainers, hobbyists |
| **Starter** | R199 | 50 | Solo devs, small OSS projects |
| **Pro** | R499 | 200 | Active maintainers, freelancers |
| **Team** | R1,499 | 1,000 | Small teams, startups |
| **Enterprise** | R4,999+ | Unlimited + self-hosted | Companies with 5+ repos |

### Feature Differentiation
- **Free:** Basic pipeline, community support
- **Starter:** Priority queue, email support, webhook integration
- **Pro:** Advanced agents, custom memory, priority support
- **Team:** Multi-repo, team dashboard, audit logs
- **Enterprise:** Self-hosted, SSO, SLA, dedicated support

---

## Cost Breakdown (Monthly)

### Per Pipeline Run (Variable Cost)
```
LLM tokens (qwen-plus):
  - 35K tokens avg per run
  - Input (60%): 21K tokens × $0.60/M = $0.0126
  - Output (40%): 14K tokens × $1.50/M = $0.021
  - Total: $0.034 per run × R18/USD = R0.61

Rounded: R0.65 per pipeline run
```

### Fixed Infrastructure (Monthly)
```
Alibaba Cloud ECS (2vCPU/4GB):     R540
Bandwidth/transfer:                 R150
Domain (amortized):                 R25
Monitoring/logging:                 R50
                                    ----
Total fixed:                        R765/month
```

### Per-User Costs (At Scale)
| Users | Fixed/User | Variable (avg 50 runs) | Total Cost/User |
|-------|-----------|----------------------|-----------------|
| 10    | R76       | R33                  | R109            |
| 50    | R15       | R33                  | R48             |
| 100   | R8        | R33                  | R41             |
| 500   | R2        | R33                  | R35             |

---

## Revenue vs Cost vs Profit

### Scenario: 20 Paying Customers (Mixed Tiers)
```
Revenue (monthly):
  - 10 × Starter (R199):          R1,990
  - 6 × Pro (R499):               R2,994
  - 3 × Team (R1,499):            R4,497
  - 1 × Enterprise (R4,999):      R4,999
                                  --------
  Total Revenue:                  R14,480/month

Costs (monthly):
  - Fixed infrastructure:         R765
  - LLM tokens (avg 80 runs/user):
    20 users × 80 × R0.65 =       R1,040
  - Support/time (10 hrs @ R150): R1,500
                                  --------
  Total Costs:                    R3,305/month

Profit:                           R11,175/month (77% margin)
```

### Scenario: 50 Paying Customers
```
Revenue:                          R36,200/month
Costs:                            R5,200/month
Profit:                           R31,000/month (86% margin)
```

### Break-Even Point
```
With R765 fixed costs:
  - Need 5 × Starter customers = R995 revenue → R230 profit
  - OR 2 × Pro customers = R998 revenue → R233 profit
  - OR 1 × Team customer = R1,499 revenue → R734 profit

Break-even: ~3-5 paying customers
```

---

## Honest Challenges

### Why This Is Hard
1. **Niche market:** Open-source maintainers are often unpaid volunteers — they may not pay for tools
2. **Competition:** GitHub Copilot (R180-340/month), Cursor, Devin already have market share
3. **Customer acquisition:** Developers are skeptical, require proof before paying
4. **Support burden:** Each customer needs onboarding, debugging failed pipelines
5. **Enterprise sales cycle:** R4,999+ contracts take 3-6 months to close

### What You Need to Succeed
1. **Free tier traction:** Get 100+ free users first, convert 5-10% to paid
2. **Case studies:** Show real repos where AutoMaintainer saved 10+ hours/month
3. **GitHub marketplace listing:** Discoverability where devs already are
4. **Integration depth:** Webhooks, CI/CD integration, Slack notifications
5. **Reliability:** 99.5%+ uptime, fast pipeline execution, good error handling

---

## Realistic Timeline & Projections

### Year 1: Validation
```
Months 1-3:   Free tier launch, 50-100 users, 0 revenue
Months 4-6:   Paid launch, 5-10 customers, R1,000-5,000/month
Months 7-12:  Growth to 20-30 customers, R5,000-15,000/month
Year 1 Total: R30,000-80,000 revenue (part-time effort)
```

### Year 2: Scale (If Product-Market Fit)
```
50-100 paying customers
R20,000-50,000/month revenue
Consider: hire part-time support, add features
```

### Year 3+: Options
- **Stay small:** R50K/month profit as lifestyle business
- **Scale up:** Raise funding, hire team, target enterprise
- **Acquisition:** Get acquired by GitHub/GitLab/Vercel for R2-10M

---

## Monetization Strategies Beyond Subscriptions

### 1. Bounty Platform (15-20% Commission)
- Connect maintainers with AI-generated fixes
- Maintainer posts bounty (R500-5,000)
- AutoMaintainer solves it, takes 15-20% cut
- **Potential:** R5,000-20,000/month in commissions

### 2. Open-Source Sponsorship Matching
- Partner with GitHub Sponsors, Open Collective
- Take 5-10% of donations to repos using AutoMaintainer
- **Potential:** R2,000-10,000/month

### 3. Enterprise Consulting
- Custom deployments, training, integration
- R500-1,500/hour consulting rate
- **Potential:** R10,000-50,000/month (project-based)

### 4. White-Label Licensing
- License to dev agencies, outsourcing companies
- R5,000-20,000/month per license
- **Potential:** R20,000-100,000/month (2-10 licenses)

---

## Key Metrics to Track

| Metric | Target | Why |
|--------|--------|-----|
| **Pipelines per user/month** | 30-80 | Shows value, justifies price |
| **Success rate** | >80% | Failed pipelines = churn |
| **Time saved per pipeline** | 2-4 hours | Core value proposition |
| **Free→Paid conversion** | 5-10% | Industry standard for dev tools |
| **Monthly churn** | <5% | Retention is cheaper than acquisition |
| **Customer acquisition cost** | <R500 | Pay back in <3 months |

---

## Bottom Line

**Can you make money?** Yes, but:
- **Realistic Year 1:** R30-80K revenue (R2,500-6,500/month avg)
- **Realistic Year 2:** R200-500K revenue if you find product-market fit
- **Ceiling without team:** R500K-1M/year as a solo/2-person operation
- **With team/funding:** R5-20M/year potential

**Biggest risk:** Building something developers want but won't pay for. Validate with 10 paying customers before investing heavily.

**Fastest path to revenue:** Target freelancers and small agencies managing 3-10 client repos. They have budget and feel the pain of maintenance work.
