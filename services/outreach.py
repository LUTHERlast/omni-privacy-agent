import urllib.parse
import json
from typing import Dict, Any, Optional
from config import settings
from models import Lead, PrivacyAudit

class OutreachService:
    def build_whatsapp_pitch(self, lead: Lead, audit: Optional[PrivacyAudit], base_url: str) -> Dict[str, str]:
        """Generates a high-converting, UAE-tailored WhatsApp pitch citing PDPL."""
        company = lead.company_name or lead.domain
        clean_base = base_url.rstrip("/")
        scorecard_url = f"{clean_base}/privacy-audit/{lead.domain}"

        score = audit.overall_score if audit else 45
        grade = audit.compliance_grade if audit else "D"
        trackers = audit.trackers_count if audit else 3
        cmp_stat = audit.cmp_status if audit else "MISSING"
        exposure = audit.fine_exposure_est if audit else "AED 50,000 – AED 250,000"

        # WhatsApp formatted text with bolding
        message = (
            f"Salam {company} Leadership,\n\n"
            f"Our autonomous compliance scanner recently reviewed *{lead.domain}* for adherence to the *UAE Federal Decree-Law No. 45 of 2021 on Personal Data Protection (PDPL)*.\n\n"
            f"⚠️ *Key Diagnostic Findings:*\n"
            f"• *PDPL Compliance Score:* {score}/100 (Grade: {grade})\n"
            f"• *Unlawful Pre-Consent Trackers:* {trackers} scripts firing on page load\n"
            f"• *Cookie Consent Shield:* {cmp_stat}\n"
            f"• *Estimated Regulatory Fine Exposure:* {exposure}\n\n"
            f"Under UAE Executive Regulations, firing marketing trackers before explicit affirmative opt-in exposes businesses to severe regulatory penalties.\n\n"
            f"📊 *Review Your Confidential Live Scorecard:*\n"
            f"{scorecard_url}\n\n"
            f"We can deploy a certified bilingual (Arabic & English) Consent Shield and PDPL policy hardening within 24 hours without any website downtime.\n\n"
            f"Would you be open to a 5-minute briefing this week?\n\n"
            f"— *{settings.OPERATOR_NAME}*\n"
            f"{settings.OPERATOR_TITLE}\n"
            f"WhatsApp: {settings.OPERATOR_WHATSAPP}"
        )

        # Build direct wa.me link
        phone_target = ""
        if lead.phone:
            clean_digits = "".join(filter(str.isdigit, lead.phone))
            if clean_digits.startswith("05"):
                phone_target = "971" + clean_digits[1:]
            elif clean_digits.startswith("5"):
                phone_target = "971" + clean_digits
            elif clean_digits.startswith("9715"):
                phone_target = clean_digits
            else:
                phone_target = clean_digits

        encoded_text = urllib.parse.quote(message)
        wa_link = f"https://wa.me/{phone_target}?text={encoded_text}" if phone_target else f"https://wa.me/?text={encoded_text}"

        return {
            "message": message,
            "encoded_message": encoded_text,
            "phone": phone_target,
            "wa_link": wa_link,
            "scorecard_url": scorecard_url
        }

    def build_email_pitch(self, lead: Lead, audit: Optional[PrivacyAudit], base_url: str) -> Dict[str, str]:
        """Generates fallback email subject and HTML content."""
        company = lead.company_name or lead.domain
        clean_base = base_url.rstrip("/")
        scorecard_url = f"{clean_base}/privacy-audit/{lead.domain}"
        score = audit.overall_score if audit else 45

        subject = f"URGENT: UAE PDPL Data Protection Compliance Audit for {lead.domain} [Score: {score}/100]"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b;">
            <p>Dear {company} Leadership,</p>
            <p>Our regulatory compliance engine conducted an automated, non-invasive privacy inspection of <strong>{lead.domain}</strong> in relation to <strong>UAE Federal Decree-Law No. 45 of 2021 on Personal Data Protection (PDPL)</strong>.</p>
            <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; margin: 15px 0;">
                <p style="margin: 0; font-weight: bold; color: #b91c1c;">⚠️ Compliance Score: {score}/100 — High Regulatory Risk</p>
                <p style="margin: 5px 0 0 0; font-size: 14px;">We identified marketing and analytics telemetry firing before affirmative user consent, violating Article 5 & 6 of UAE PDPL.</p>
            </div>
            <p>Access your confidential diagnostic report and remediation blueprint here:<br>
            <a href="{scorecard_url}" style="color: #2563eb; font-weight: bold;">{scorecard_url}</a></p>
            <p>We deploy turnkey bilingual consent shields in under 24 hours.</p>
            <p>Sincerely,<br>
            <strong>{settings.OPERATOR_NAME}</strong><br>
            {settings.OPERATOR_TITLE}<br>
            Direct WhatsApp: {settings.OPERATOR_WHATSAPP}</p>
        </body>
        </html>
        """
        return {"subject": subject, "html": html_body}

outreach = OutreachService()
