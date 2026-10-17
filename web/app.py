import os
import json
import datetime
import urllib.parse
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from config import settings
from database import get_db, init_db, AsyncSessionLocal
from models import Lead, PrivacyAudit, PrivacyEvent, EmailLog
from services.privacy_scanner import privacy_scanner
from services.prospector import prospector
from services.scheduler import start_scheduler
from services.outreach import outreach
from services.notifier import notifier

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.on_event("startup")
async def startup_event():
    await init_db()
    start_scheduler()
    # Auto-seed and perform initial baseline audit on startup if fresh
    async with AsyncSessionLocal() as db:
        count = (await db.execute(select(func.count(Lead.id)))).scalar() or 0
        if count == 0:
            await prospector.seed_and_audit_all(db)

@app.get("/api/ping")
@app.get("/api/health")
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint for Render and external keepalive daemons."""
    total_audits = (await db.execute(select(func.count(PrivacyAudit.id)))).scalar() or 0
    total_leads = (await db.execute(select(func.count(Lead.id)))).scalar() or 0
    return {
        "status": "HEALTHY",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "port": settings.PORT,
        "database": "CONNECTED",
        "total_audits": total_audits,
        "total_leads": total_leads,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request, db: AsyncSession = Depends(get_db)):
    """Executive Dashboard View for OmniPrivacy AI."""
    total_audits = (await db.execute(select(func.count(PrivacyAudit.id)))).scalar() or 0
    critical_risks = (await db.execute(select(func.count(PrivacyAudit.id)).where(PrivacyAudit.risk_level.in_(["CRITICAL", "HIGH"])))).scalar() or 0
    total_leads = (await db.execute(select(func.count(Lead.id)))).scalar() or 0
    paid_count = (await db.execute(select(func.count(Lead.id)).where(Lead.status == "PAID"))).scalar() or 0
    actual_revenue = (await db.execute(select(func.sum(Lead.deal_value)).where(Lead.status == "PAID"))).scalar() or 0.0
    total_pipeline = (await db.execute(select(func.sum(Lead.deal_value)))).scalar() or 0.0

    audits = (await db.execute(select(PrivacyAudit).order_by(desc(PrivacyAudit.id)).limit(40))).scalars().all()
    leads = (await db.execute(select(Lead))).scalars().all()
    leads_map = {l.domain: l for l in leads}
    events = (await db.execute(select(PrivacyEvent).order_by(desc(PrivacyEvent.id)).limit(20))).scalars().all()

    base_url = str(request.base_url).rstrip("/")

    leads_data = []
    for audit in audits:
        lead = leads_map.get(audit.domain)
        pitch_info = outreach.build_whatsapp_pitch(lead or Lead(domain=audit.domain, company_name=audit.company_name), audit, base_url)
        
        # Clean pitch for JS inline escape
        clean_js_pitch = pitch_info["message"].replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

        leads_data.append({
            "domain": audit.domain,
            "company_name": audit.company_name or audit.domain,
            "industry": lead.industry if lead else "Corporate & Commercial",
            "score": audit.overall_score,
            "grade": audit.compliance_grade,
            "fine_exposure": audit.fine_exposure_est,
            "trackers_count": audit.trackers_count,
            "cmp_status": audit.cmp_status,
            "cmp_name": audit.cmp_name,
            "phone": lead.phone if lead else None,
            "status": lead.status if lead else "AUDITED",
            "wa_link": pitch_info["wa_link"],
            "encoded_pitch": pitch_info["encoded_message"],
            "raw_pitch_escaped": clean_js_pitch
        })

    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request,
        "total_audits": total_audits,
        "critical_risks": critical_risks,
        "total_leads": total_leads,
        "total_pipeline": total_pipeline,
        "paid_count": paid_count,
        "actual_revenue": actual_revenue,
        "leads_data": leads_data,
        "events": events
    })

@app.get("/privacy-audit/{domain}", response_class=HTMLResponse)
async def public_audit_scorecard(domain: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Public, high-conversion visual diagnostic scorecard for UAE PDPL."""
    clean_d = privacy_scanner.clean_domain(domain)
    audit = (await db.execute(select(PrivacyAudit).where(PrivacyAudit.domain == clean_d))).scalars().first()
    
    if not audit:
        # Run live audit if not in DB
        audit = await prospector.audit_single_domain(clean_d, db)

    lead = (await db.execute(select(Lead).where(Lead.domain == clean_d))).scalars().first()
    base_url = str(request.base_url).rstrip("/")
    pitch_info = outreach.build_whatsapp_pitch(lead or Lead(domain=clean_d, company_name=audit.company_name), audit, base_url)

    # Parse JSON fields
    try:
        trackers = json.loads(audit.trackers_json)
    except Exception:
        trackers = []

    try:
        issues = json.loads(audit.issues_json)
    except Exception:
        issues = []

    try:
        blueprint = json.loads(audit.remediation_blueprint_json)
    except Exception:
        blueprint = []

    wa_text = urllib.parse.quote(f"Salam Athul, I am reviewing our UAE PDPL audit report for {audit.domain} (Score: {audit.overall_score}/100). We need to remediate these {audit.trackers_count} tracking violations.")

    return templates.TemplateResponse(request, "privacy_scorecard.html", {
        "request": request,
        "audit": audit,
        "lead": lead,
        "trackers": trackers,
        "issues": issues,
        "blueprint": blueprint,
        "wa_text": wa_text
    })

@app.get("/privacy-checkout/{domain}", response_class=HTMLResponse)
async def checkout_view(domain: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Pricing and turnkey packages page."""
    clean_d = privacy_scanner.clean_domain(domain)
    
    wa_pitch_tier1 = urllib.parse.quote(
        f"Salam Athul, we want to book the PDPL Express Compliance Package (AED 2,200) for {clean_d}. Please confirm onboarding details."
    )
    wa_pitch_tier2 = urllib.parse.quote(
        f"Salam Athul, we want to book the Enterprise PDPL Shield & DPO Advisory Package (AED 4,500) for {clean_d}. Please confirm onboarding details."
    )

    return templates.TemplateResponse(request, "checkout.html", {
        "request": request,
        "domain": clean_d,
        "wa_pitch_tier1": wa_pitch_tier1,
        "wa_pitch_tier2": wa_pitch_tier2
    })

@app.post("/api/audit/scan")
async def trigger_manual_scan(domain: str = Form(...), company_name: str = Form(None), db: AsyncSession = Depends(get_db)):
    """Trigger an on-demand audit for a given domain and redirect to scorecard."""
    clean_d = privacy_scanner.clean_domain(domain)
    audit = await prospector.audit_single_domain(clean_d, db, company_name=company_name)
    return RedirectResponse(url=f"/privacy-audit/{audit.domain}", status_code=303)

@app.post("/api/lead/update-status")
async def update_lead_status(domain: str = Form(...), status: str = Form(...), db: AsyncSession = Depends(get_db)):
    """Update lead status in CRM pipeline."""
    clean_d = privacy_scanner.clean_domain(domain)
    lead = (await db.execute(select(Lead).where(Lead.domain == clean_d))).scalars().first()
    if lead:
        lead.status = status
        await db.commit()
        return {"status": "SUCCESS", "domain": clean_d, "new_status": status}
    return JSONResponse(status_code=404, content={"status": "ERROR", "message": "Lead not found"})

@app.get("/master")
async def redirect_to_master():
    """Helper link to Master Fleet Command."""
    return RedirectResponse(url="https://omni-revenue-uae.onrender.com/master", status_code=302)
