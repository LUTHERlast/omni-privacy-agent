import asyncio
import json
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Lead, PrivacyAudit, PrivacyEvent
from services.privacy_scanner import privacy_scanner
from config import settings

logger = logging.getLogger("prospector")

# Real UAE target domains across high-ticket sectors
UAE_SEED_PROSPECTS = [
    {"domain": "asterdmhealthcare.com", "name": "Aster DM Healthcare", "industry": "Healthcare & Clinics", "phone": "971501234567"},
    {"domain": "medcare.ae", "name": "Medcare Hospitals & Medical Centres", "industry": "Healthcare & Hospitals", "phone": "971529876543"},
    {"domain": "fakeeh.care", "name": "Fakeeh University Hospital", "industry": "Healthcare", "phone": "971545678901"},
    {"domain": "alzahra.com", "name": "Al Zahra Hospital Dubai", "industry": "Healthcare", "phone": "971556781234"},
    {"domain": "danathospital.com", "name": "Danat Al Emarat Hospital", "industry": "Healthcare & Maternity", "phone": "971561239876"},
    {"domain": "propertyfinder.ae", "name": "Property Finder UAE", "industry": "Real Estate & PropTech", "phone": "971508765432"},
    {"domain": "bayut.com", "name": "Bayut UAE", "industry": "Real Estate Portal", "phone": "971523456789"},
    {"domain": "betterhomes.com", "name": "Betterhomes Dubai", "industry": "Luxury Real Estate", "phone": "971549871234"},
    {"domain": "damacproperties.com", "name": "DAMAC Properties", "industry": "Property Development", "phone": "971558765432"},
    {"domain": "farglory.ae", "name": "Farglory Middle East", "industry": "Real Estate & Development", "phone": "971562345678"},
    {"domain": "ounass.ae", "name": "Ounass Luxury Shopping", "industry": "Luxury E-Commerce", "phone": "971503456789"},
    {"domain": "sharafdg.com", "name": "Sharaf DG UAE", "industry": "Consumer Electronics Retail", "phone": "971588613477"},
    {"domain": "virginmegastore.ae", "name": "Virgin Megastore UAE", "industry": "Entertainment & Retail", "phone": "971543210987"},
    {"domain": "thedukesdubai.com", "name": "Dukes The Palm Hotel", "industry": "Luxury Hospitality", "phone": "971554321098"}
]

class ProspectorService:
    def __init__(self):
        self.scanner = privacy_scanner

    async def seed_and_audit_all(self, db: AsyncSession) -> int:
        """Seeds initial target accounts and executes non-invasive audits."""
        audited_count = 0
        for prospect in UAE_SEED_PROSPECTS:
            domain = prospect["domain"]
            existing = (await db.execute(select(Lead).where(Lead.domain == domain))).scalars().first()
            if not existing:
                lead = Lead(
                    domain=domain,
                    company_name=prospect["name"],
                    industry=prospect["industry"],
                    location="Dubai, UAE",
                    phone=prospect.get("phone"),
                    deal_value=settings.DEFAULT_DEAL_VALUE,
                    status="DISCOVERED"
                )
                db.add(lead)
                await db.commit()
                await db.refresh(lead)

            # Audit if audit doesn't exist yet
            existing_audit = (await db.execute(select(PrivacyAudit).where(PrivacyAudit.domain == domain))).scalars().first()
            if not existing_audit:
                try:
                    scan_res = await self.scanner.scan(domain)
                    phone_to_use = scan_res.get("extracted_phone") or prospect.get("phone")

                    audit = PrivacyAudit(
                        domain=domain,
                        company_name=prospect["name"],
                        overall_score=scan_res["overall_score"],
                        compliance_grade=scan_res["compliance_grade"],
                        risk_level=scan_res["risk_level"],
                        fine_exposure_est=scan_res["fine_exposure_est"],
                        trackers_count=scan_res["trackers_count"],
                        trackers_json=json.dumps(scan_res["trackers_json"]),
                        cmp_status=scan_res["cmp_status"],
                        cmp_name=scan_res.get("cmp_name"),
                        cookie_blocking_enabled=scan_res["cookie_blocking_enabled"],
                        policy_status=scan_res["policy_status"],
                        policy_url=scan_res.get("policy_url"),
                        has_pdpl_reference=scan_res["has_pdpl_reference"],
                        has_dpo_reference=scan_res["has_dpo_reference"],
                        has_rights_reference=scan_res["has_rights_reference"],
                        has_cross_border_reference=scan_res["has_cross_border_reference"],
                        has_arabic_version=scan_res["has_arabic_version"],
                        forms_status=scan_res["forms_status"],
                        forms_count=scan_res["forms_count"],
                        forms_lacking_consent=scan_res["forms_lacking_consent"],
                        ssl_status=scan_res["ssl_status"],
                        issues_json=json.dumps(scan_res["issues_json"]),
                        remediation_blueprint_json=json.dumps(scan_res["remediation_blueprint_json"]),
                        audit_token=scan_res["audit_token"]
                    )
                    db.add(audit)
                    await db.flush()

                    # Update lead record
                    lead_rec = (await db.execute(select(Lead).where(Lead.domain == domain))).scalars().first()
                    if lead_rec:
                        lead_rec.audit_id = audit.id
                        lead_rec.status = "AUDITED"
                        if phone_to_use:
                            lead_rec.phone = phone_to_use

                    # Log Event
                    event = PrivacyEvent(
                        event_type="AUDIT_RUN",
                        domain=domain,
                        severity="CRITICAL" if scan_res["risk_level"] in ["CRITICAL", "HIGH"] else "INFO",
                        message=f"Automated PDPL scan completed for {domain}. Score: {scan_res['overall_score']}/100 ({scan_res['compliance_grade']}). Trackers detected: {scan_res['trackers_count']}."
                    )
                    db.add(event)
                    await db.commit()
                    audited_count += 1
                except Exception as e:
                    logger.error(f"Error auditing seed prospect {domain}: {e}")
                    await db.rollback()
        return audited_count

    async def audit_single_domain(self, domain: str, db: AsyncSession, company_name: str = None) -> PrivacyAudit:
        """Audits a single domain on-demand and creates/updates lead record."""
        clean_d = self.scanner.clean_domain(domain)
        scan_res = await self.scanner.scan(clean_d)

        # Upsert Audit
        audit = (await db.execute(select(PrivacyAudit).where(PrivacyAudit.domain == clean_d))).scalars().first()
        if not audit:
            audit = PrivacyAudit(domain=clean_d)
            db.add(audit)

        audit.company_name = company_name or clean_d.split(".")[0].capitalize()
        audit.overall_score = scan_res["overall_score"]
        audit.compliance_grade = scan_res["compliance_grade"]
        audit.risk_level = scan_res["risk_level"]
        audit.fine_exposure_est = scan_res["fine_exposure_est"]
        audit.trackers_count = scan_res["trackers_count"]
        audit.trackers_json = json.dumps(scan_res["trackers_json"])
        audit.cmp_status = scan_res["cmp_status"]
        audit.cmp_name = scan_res.get("cmp_name")
        audit.cookie_blocking_enabled = scan_res["cookie_blocking_enabled"]
        audit.policy_status = scan_res["policy_status"]
        audit.policy_url = scan_res.get("policy_url")
        audit.has_pdpl_reference = scan_res["has_pdpl_reference"]
        audit.has_dpo_reference = scan_res["has_dpo_reference"]
        audit.has_rights_reference = scan_res["has_rights_reference"]
        audit.has_cross_border_reference = scan_res["has_cross_border_reference"]
        audit.has_arabic_version = scan_res["has_arabic_version"]
        audit.forms_status = scan_res["forms_status"]
        audit.forms_count = scan_res["forms_count"]
        audit.forms_lacking_consent = scan_res["forms_lacking_consent"]
        audit.ssl_status = scan_res["ssl_status"]
        audit.issues_json = json.dumps(scan_res["issues_json"])
        audit.remediation_blueprint_json = json.dumps(scan_res["remediation_blueprint_json"])
        audit.audit_token = scan_res["audit_token"]

        await db.flush()

        # Upsert Lead
        lead = (await db.execute(select(Lead).where(Lead.domain == clean_d))).scalars().first()
        if not lead:
            lead = Lead(
                domain=clean_d,
                company_name=audit.company_name,
                industry="Corporate & Commercial",
                location="Dubai, UAE",
                deal_value=settings.DEFAULT_DEAL_VALUE,
                status="AUDITED",
                audit_id=audit.id
            )
            db.add(lead)
        else:
            lead.audit_id = audit.id
            if lead.status == "DISCOVERED":
                lead.status = "AUDITED"

        if scan_res.get("extracted_phone"):
            lead.phone = scan_res["extracted_phone"]

        event = PrivacyEvent(
            event_type="AUDIT_RUN",
            domain=clean_d,
            severity="CRITICAL" if scan_res["risk_level"] in ["CRITICAL", "HIGH"] else "INFO",
            message=f"On-demand PDPL scan finished for {clean_d}. Score: {scan_res['overall_score']}/100. Violations found: {len(scan_res['issues_json'])}."
        )
        db.add(event)
        await db.commit()
        await db.refresh(audit)
        return audit

prospector = ProspectorService()
