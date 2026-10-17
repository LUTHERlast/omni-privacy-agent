# OmniPrivacy AI — Autonomous UAE PDPL Compliance & Consent Engine

OmniPrivacy AI is **Agent 4** in the **OmniFleet Multi-Agent Empire**, built specifically for the United Arab Emirates regulatory market.

## 🇦🇪 Mission & Regulatory Framework
Under **UAE Federal Decree-Law No. 45 of 2021 on Personal Data Protection (PDPL)** and its Executive Regulations:
1. Third-party marketing & telemetry cookies (Meta Pixel, GA4, TikTok, Clarity) must **NOT** fire prior to explicit opt-in consent.
2. Websites must deploy a bilingual (Arabic & English) Consent Management Platform (CMP).
3. Contact and inquiry forms collecting personal consumer data must have explicit, unticked consent checkboxes linked to a certified UAE PDPL privacy policy.
4. Non-compliance exposes businesses to regulatory fines between **AED 50,000 and AED 500,000+**.

OmniPrivacy AI crawls target UAE domains non-invasively, identifies illegal pre-consent telemetry, generates a public diagnostic scorecard with statutory citations, and equips you with 1-click WhatsApp outreach.

---

## 💰 Turnkey Service Packages
- **Tier 1: PDPL Express Compliance — AED 2,200**
  - Bilingual (Arabic/English) Consent Shield
  - Automated Prior-Blocking of Meta Pixel, GA4, TikTok
  - Compliant PDPL Privacy Policy & Cookie Policy
  - Form consent checkboxes
  - 24h delivery with zero downtime
- **Tier 2: Enterprise PDPL Protection & DPO Shield — AED 4,500**
  - Everything in Tier 1
  - Full third-party vendor data processing register
  - Cross-Border Transfer Register (AWS/Google offshore compliance under Article 22)
  - Subject Rights (DSAR) intake portal
  - 12-Month Ongoing Regulatory Warranty

---

## 🚀 Running Locally
```bash
cd "C:\Users\ATHUL IT\.gemini\antigravity\scratch\privacy-agent"
pip install -r requirements.txt
python run.py
```
Open [http://127.0.0.1:8788](http://127.0.0.1:8788) in your browser.

---

## 💬 1-Click WhatsApp Outreach Flow
1. Open the Dashboard at `http://127.0.0.1:8788` (or deployed Render URL).
2. The agent automatically detects active UAE mobile numbers (`+971 50`, `52`, `54`, `55`, `56`, `58`).
3. Click **`[💬 Pitch on WhatsApp]`** to instantly open WhatsApp Web with a pre-filled diagnostic message citing the exact number of illegal trackers found and their live audit link.
4. Or click **`[📋 Copy Pitch Text]`** to copy the text to your clipboard.

---

## 🚢 Deploying to Render
1. Push this repository to GitHub (e.g. `LUTHERlast/omni-privacy-agent`).
2. In Render, create a new Web Service pointing to the repository.
3. Set Environment to `Python 3`, build command `pip install -r requirements.txt`, and start command `uvicorn web.app:app --host 0.0.0.0 --port $PORT`.
4. Add `PUBLIC_APP_URL` environment variable: `https://omni-privacy-agent.onrender.com`.
