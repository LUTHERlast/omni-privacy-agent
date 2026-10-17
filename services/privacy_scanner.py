import re
import uuid
import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup

class PrivacyScanner:
    """
    Non-intrusive public scanner for UAE Federal Decree-Law No. 45 of 2021 (PDPL)
    and bilingual cookie consent compliance.
    """

    KNOWN_TRACKERS = [
        {
            "id": "meta_pixel",
            "name": "Meta / Facebook Pixel",
            "category": "Targeted Advertising & Profiling",
            "risk": "HIGH",
            "patterns": [r"connect\.facebook\.net", r"fbq\s*\(", r"fbevents\.js"],
            "legal_note": "Harvests visitor behavioral identity before consent. Violates UAE PDPL Article 5 & 6."
        },
        {
            "id": "google_analytics",
            "name": "Google Analytics (GA4 / Universal)",
            "category": "Behavioral Web Telemetry",
            "risk": "MODERATE",
            "patterns": [r"google-analytics\.com", r"googletagmanager\.com/gtag/js", r"gtag\s*\(\s*['\"]config['\"]", r"ga\s*\(\s*['\"]create['\"]"],
            "legal_note": "Transfers telemetry to US/EU cloud without prior explicit opt-in. Violates UAE PDPL Article 22."
        },
        {
            "id": "tiktok_pixel",
            "name": "TikTok Pixel",
            "category": "Cross-Platform Ad Retargeting",
            "risk": "CRITICAL",
            "patterns": [r"analytics\.tiktok\.com", r"ttq\.load", r"ttq\.page"],
            "legal_note": "Aggressive cross-app tracking without prior explicit consent. High regulatory penalty risk."
        },
        {
            "id": "linkedin_insight",
            "name": "LinkedIn Insight Tag",
            "category": "B2B Profiling & Firmographics",
            "risk": "HIGH",
            "patterns": [r"snap\.licdn\.com", r"_linkedin_partner_id"],
            "legal_note": "Profiles corporate visitor identities without consent. Violates UAE PDPL Article 6."
        },
        {
            "id": "ms_clarity",
            "name": "Microsoft Clarity (Session Recording)",
            "category": "Keystroke & Session Replay",
            "risk": "CRITICAL",
            "patterns": [r"clarity\.ms/tag", r"clarity\s*\(\s*['\"]set['\"]"],
            "legal_note": "Records screen interactions & keystrokes without explicit biometric/behavioral consent."
        },
        {
            "id": "hotjar",
            "name": "Hotjar Session Recorder",
            "category": "User Session Replay & Heatmaps",
            "risk": "HIGH",
            "patterns": [r"static\.hotjar\.com", r"_hjSettings"],
            "legal_note": "Captures user form input interactions prior to consent under UAE PDPL."
        },
        {
            "id": "snap_pixel",
            "name": "Snapchat Pixel",
            "category": "Social Media Retargeting",
            "risk": "HIGH",
            "patterns": [r"sc-static\.net/scevent\.min\.js", r"snaptr\s*\("],
            "legal_note": "Monitors mobile audience identifiers without prior consent."
        },
        {
            "id": "criteo",
            "name": "Criteo Dynamic Retargeting",
            "category": "Third-Party Ad Network Tracker",
            "risk": "CRITICAL",
            "patterns": [r"dynamic\.criteo\.com", r"criteo_q"],
            "legal_note": "Tracks shopping intent across external networks without consent."
        }
    ]

    KNOWN_CMPS = [
        {"name": "OneTrust", "patterns": [r"onetrust", r"otSDKStub", r"cdn\.cookielaw\.org"]},
        {"name": "Cookiebot", "patterns": [r"cookiebot\.com", r"consent\.cookiebot\.com"]},
        {"name": "CookieScript", "patterns": [r"cookie-script\.com", r"cdn\.cookie-script\.com"]},
        {"name": "CookieYes", "patterns": [r"cookieyes\.com", r"cdn-cookieyes\.com"]},
        {"name": "Klaro", "patterns": [r"klaro\.js", r"klaro-consent"]},
        {"name": "Iubenda", "patterns": [r"iubenda\.com", r"iubenda_cs"]},
        {"name": "Complianz", "patterns": [r"complianz\.min\.js", r"cmplz-banner"]},
        {"name": "Termly", "patterns": [r"termly\.js", r"app\.termly\.io"]},
        {"name": "Osano", "patterns": [r"cmp\.osano\.com"]},
        {"name": "Usercentrics", "patterns": [r"usercentrics\.eu", r"app\.usercentrics\.eu"]}
    ]

    def clean_domain(self, raw: str) -> str:
        raw = raw.strip().lower()
        raw = re.sub(r"^https?://", "", raw)
        raw = raw.split("/")[0].split(":")[0]
        return raw

    def extract_whatsapp_phone(self, html: str) -> Optional[str]:
        """Strictly extracts official WhatsApp or UAE mobile phone numbers (+971 5X)."""
        if not html:
            return None
        try:
            # 1. Look for direct wa.me link
            wa_match = re.search(r'wa\.me/(\d{10,15})', html, re.IGNORECASE)
            if wa_match:
                return wa_match.group(1)

            # 2. Look for api.whatsapp.com link
            wa_api = re.search(r'api\.whatsapp\.com/send\?[^"\']*phone=(\d{10,15})', html, re.IGNORECASE)
            if wa_api:
                return wa_api.group(1)

            # 3. Look for UAE mobile pattern: +971 50/52/54/55/56/58 XXXXXXX
            uae_mob = re.search(r'(?:\+?971|00971|0)?\s*(5[024568]\d{7})', html)
            if uae_mob:
                return f"971{uae_mob.group(1)}"

            # 4. Look for tel: link with UAE mobile digits
            tel_matches = re.findall(r'href=["\']tel:([^"\']+)["\']', html, re.IGNORECASE)
            for tel in tel_matches:
                clean = re.sub(r'[^\d]', '', tel)
                if clean.startswith("9715") and len(clean) == 12:
                    return clean
                if clean.startswith("05") and len(clean) == 10:
                    return f"971{clean[1:]}"
                if clean.startswith("5") and len(clean) == 9:
                    return f"971" + clean
        except Exception:
            pass
        return None

    async def scan(self, domain: str) -> Dict[str, Any]:
        """Executes a full non-intrusive UAE PDPL & Cookie audit."""
        clean_d = self.clean_domain(domain)
        audit_token = uuid.uuid4().hex[:12]
        base_url = f"https://{clean_d}"
        
        result = {
            "domain": clean_d,
            "company_name": clean_d.split(".")[0].capitalize(),
            "audit_token": audit_token,
            "overall_score": 100,
            "compliance_grade": "A+",
            "risk_level": "COMPLIANT",
            "fine_exposure_est": "None (Low Risk)",
            "trackers_count": 0,
            "trackers_json": [],
            "cmp_status": "MISSING",
            "cmp_name": None,
            "cookie_blocking_enabled": False,
            "policy_status": "MISSING",
            "policy_url": None,
            "has_pdpl_reference": False,
            "has_dpo_reference": False,
            "has_rights_reference": False,
            "has_cross_border_reference": False,
            "has_arabic_version": False,
            "forms_status": "NO_FORMS",
            "forms_count": 0,
            "forms_lacking_consent": 0,
            "ssl_status": "SECURE",
            "issues_json": [],
            "remediation_blueprint_json": [],
            "extracted_phone": None,
            "raw_html": ""
        }

        html = ""
        headers = {}
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
            try:
                resp = await client.get(base_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                })
                html = resp.text
                headers = dict(resp.headers)
                result["raw_html"] = html
            except Exception:
                # Try plain HTTP fallback if HTTPS fails
                try:
                    resp = await client.get(f"http://{clean_d}", timeout=8.0, follow_redirects=True)
                    html = resp.text
                    headers = dict(resp.headers)
                    result["ssl_status"] = "INSECURE"
                    result["overall_score"] -= 20
                except Exception:
                    html = ""

        if not html:
            # Domain completely unreachable
            result["overall_score"] = 10
            result["compliance_grade"] = "F"
            result["risk_level"] = "CRITICAL"
            result["issues_json"].append({
                "title": "Site Unreachable / Insecure Protocol",
                "severity": "CRITICAL",
                "pdpl_article": "Article 32 (Technical & Organizational Measures)",
                "description": f"Domain {clean_d} failed to establish a secure HTTPS connection."
            })
            return result

        soup = BeautifulSoup(html, "html.parser")
        result["extracted_phone"] = self.extract_whatsapp_phone(html)

        # 1. SCAN FOR THIRD-PARTY TRACKERS FIRING PRE-CONSENT
        detected_trackers = []
        for trk in self.KNOWN_TRACKERS:
            found = False
            for pat in trk["patterns"]:
                if re.search(pat, html, re.IGNORECASE):
                    found = True
                    break
            if found:
                detected_trackers.append({
                    "id": trk["id"],
                    "name": trk["name"],
                    "category": trk["category"],
                    "risk": trk["risk"],
                    "legal_note": trk["legal_note"]
                })

        result["trackers_count"] = len(detected_trackers)
        result["trackers_json"] = detected_trackers

        # 2. SCAN FOR CONSENT MANAGEMENT PLATFORM (CMP)
        detected_cmp = None
        for cmp_candidate in self.KNOWN_CMPS:
            for pat in cmp_candidate["patterns"]:
                if re.search(pat, html, re.IGNORECASE):
                    detected_cmp = cmp_candidate["name"]
                    break
            if detected_cmp:
                break

        # Check for generic banner in DOM
        if not detected_cmp:
            banner_indicators = soup.find_all(lambda tag: tag.name in ["div", "section", "aside"] and (
                "cookie" in tag.get("id", "").lower() or
                "cookie" in " ".join(tag.get("class", [])).lower() or
                "consent" in tag.get("id", "").lower() or
                "consent" in " ".join(tag.get("class", [])).lower()
            ))
            if banner_indicators:
                detected_cmp = "Custom Banner (Notice-only)"

        if detected_cmp:
            result["cmp_name"] = detected_cmp
            if "Notice-only" in detected_cmp or (detected_trackers and not re.search(r'type=["\']text/plain["\'].*cookie', html, re.IGNORECASE)):
                result["cmp_status"] = "INADEQUATE"
                result["cookie_blocking_enabled"] = False
            else:
                result["cmp_status"] = "COMPLIANT"
                result["cookie_blocking_enabled"] = True
        else:
            result["cmp_status"] = "MISSING"
            result["cookie_blocking_enabled"] = False

        # 3. SCAN FOR PRIVACY POLICY & UAE PDPL PROVISIONS
        policy_link = None
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text().strip().lower()
            if any(k in href.lower() or k in text for k in ["privacy", "خصوصية", "pdpl", "gdpr", "data-protection"]):
                policy_link = urljoin(base_url, href)
                break

        if policy_link:
            result["policy_url"] = policy_link
            policy_html = ""
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, verify=False) as client:
                try:
                    p_resp = await client.get(policy_link)
                    policy_html = p_resp.text
                except Exception:
                    policy_html = ""

            if policy_html:
                # Check for PDPL reference
                if re.search(r'(?:Decree-Law|Decree\s+Law|PDPL|No\.\s*45\s+of\s+2021|Federal\s+Law\s+No\.\s*45|UAE\s+Data\s+Office|مرسوم\s+بقانون\s+اتحادي\s+رقم\s+45)', policy_html, re.IGNORECASE):
                    result["has_pdpl_reference"] = True

                # Check for DPO or Privacy Contact
                if re.search(r'(?:Data\s+Protection\s+Officer|DPO|privacy@|dpo@|compliance@|مسؤول\s+حماية\s+البيانات)', policy_html, re.IGNORECASE):
                    result["has_dpo_reference"] = True

                # Check for Subject Rights
                if re.search(r'(?:Right\s+to\s+Erasure|Right\s+to\s+Access|Right\s+to\s+Rectification|Withdraw\s+Consent|حق\s+الوصول|حق\s+المحو)', policy_html, re.IGNORECASE):
                    result["has_rights_reference"] = True

                # Check for Cross-border transfer
                if re.search(r'(?:Cross-border|transfer.*outside.*UAE|international\s+transfers|خارج\s+الدولة)', policy_html, re.IGNORECASE):
                    result["has_cross_border_reference"] = True

                # Check for Arabic presence
                if re.search(r'[\u0600-\u06FF]', policy_html):
                    result["has_arabic_version"] = True

                if result["has_pdpl_reference"] and result["has_dpo_reference"]:
                    result["policy_status"] = "COMPLIANT"
                else:
                    result["policy_status"] = "DEFICIENT"
            else:
                result["policy_status"] = "DEFICIENT"
        else:
            result["policy_status"] = "MISSING"

        # 4. SCAN FORMS & CONSENT CHECKBOXES
        forms = soup.find_all("form")
        lead_forms = []
        for f in forms:
            inputs = f.find_all(["input", "textarea"])
            has_personal_field = False
            for inp in inputs:
                name_attr = (inp.get("name") or "").lower()
                type_attr = (inp.get("type") or "").lower()
                placeholder = (inp.get("placeholder") or "").lower()
                if any(x in name_attr or x in placeholder for x in ["email", "phone", "tel", "mobile", "name"]):
                    has_personal_field = True
                    break
            if has_personal_field:
                lead_forms.append(f)

        result["forms_count"] = len(lead_forms)
        if lead_forms:
            lacking_consent = 0
            for f in lead_forms:
                checkboxes = f.find_all("input", type="checkbox")
                has_consent_checkbox = False
                for cb in checkboxes:
                    label_text = ""
                    parent = cb.find_parent(["label", "div", "p"])
                    if parent:
                        label_text = parent.get_text().lower()
                    if any(c in label_text for c in ["agree", "consent", "terms", "privacy", "أوافق", "الشروط", "الخصوصية"]):
                        has_consent_checkbox = True
                        break
                if not has_consent_checkbox:
                    lacking_consent += 1
            result["forms_lacking_consent"] = lacking_consent
            result["forms_status"] = "NON_COMPLIANT" if lacking_consent > 0 else "COMPLIANT"
        else:
            result["forms_status"] = "NO_FORMS"

        # 5. DEDUCT COMPLIANCE POINTS
        score = 100

        # Unlawful Trackers deduction
        if result["trackers_count"] > 0:
            score -= min(40, result["trackers_count"] * 10)
            result["issues_json"].append({
                "title": f"{result['trackers_count']} Third-Party Tracking Scripts Firing Without Prior Consent",
                "severity": "CRITICAL",
                "pdpl_article": "UAE PDPL Article 5 (Lawful Processing) & Article 6 (Consent Provisions)",
                "description": f"Found active tracking beacons ({', '.join([t['name'] for t in detected_trackers[:3]])}) harvesting user session data on cold page load before user consent is granted."
            })

        # CMP Banner deduction
        if result["cmp_status"] == "MISSING":
            score -= 25
            result["issues_json"].append({
                "title": "Absence of Consent Management Platform (CMP)",
                "severity": "CRITICAL",
                "pdpl_article": "UAE PDPL Article 6 (Prior Explicit Opt-In Requirement)",
                "description": "No recognized cookie consent mechanism detected. Visitors are not provided an opt-in/reject preference center."
            })
        elif result["cmp_status"] == "INADEQUATE":
            score -= 15
            result["issues_json"].append({
                "title": "Inadequate / Non-Blocking Cookie Banner",
                "severity": "HIGH",
                "pdpl_article": "UAE PDPL Article 6 (Consent Validity)",
                "description": "Cookie banner is present but purely informational; it does not mechanically block marketing cookies prior to affirmative user consent."
            })

        # Privacy Policy deduction
        if result["policy_status"] == "MISSING":
            score -= 20
            result["issues_json"].append({
                "title": "No Public Privacy Policy Discovered",
                "severity": "CRITICAL",
                "pdpl_article": "UAE PDPL Article 13 (Mandatory Data Subject Notifications)",
                "description": "Could not identify a clear, reachable Privacy Policy link in navigation or footer."
            })
        elif result["policy_status"] == "DEFICIENT":
            score -= 15
            details = []
            if not result["has_pdpl_reference"]:
                details.append("Lacks explicit reference to UAE Federal Decree-Law No. 45/2021")
            if not result["has_dpo_reference"]:
                details.append("Lacks designated Data Protection Officer (DPO) contact")
            if not result["has_arabic_version"]:
                details.append("Lacks mandatory Arabic translation")
            result["issues_json"].append({
                "title": "Privacy Policy Deficiencies Under UAE Law",
                "severity": "HIGH",
                "pdpl_article": "UAE PDPL Article 13 & Executive Regulations",
                "description": "; ".join(details)
            })

        # Form Consent deduction
        if result["forms_status"] == "NON_COMPLIANT":
            score -= 15
            result["issues_json"].append({
                "title": f"{result['forms_lacking_consent']} Lead Capture Forms Missing Explicit Consent Checkboxes",
                "severity": "HIGH",
                "pdpl_article": "UAE PDPL Article 5 (Lawful Processing of Contact Data)",
                "description": "Inquiry or contact forms collect name, email, or telephone numbers without an explicit, unticked consent checkbox linked to the privacy policy."
            })

        score = max(5, min(100, score))
        result["overall_score"] = score

        # Determine Grade & Risk Level
        if score >= 90:
            result["compliance_grade"] = "A"
            result["risk_level"] = "COMPLIANT"
            result["fine_exposure_est"] = "Minimal Risk"
        elif score >= 75:
            result["compliance_grade"] = "B"
            result["risk_level"] = "LOW"
            result["fine_exposure_est"] = "AED 25,000 – AED 50,000"
        elif score >= 50:
            result["compliance_grade"] = "C"
            result["risk_level"] = "MODERATE"
            result["fine_exposure_est"] = "AED 50,000 – AED 150,000"
        elif score >= 30:
            result["compliance_grade"] = "D"
            result["risk_level"] = "HIGH"
            result["fine_exposure_est"] = "AED 100,000 – AED 300,000"
        else:
            result["compliance_grade"] = "F"
            result["risk_level"] = "CRITICAL"
            result["fine_exposure_est"] = "AED 250,000 – AED 500,000+"

        # 3-Step Remediation Action Blueprint
        result["remediation_blueprint_json"] = [
            {
                "step": "Phase 1: Automated Script Quarantine & CMP Integration",
                "action": "Deploy bilingual (Arabic/English) Consent Management Shield configured with strict prior-blocking. Halts Meta Pixel, GA4, and TikTok tags until affirmative opt-in.",
                "timeline": "Within 4 Hours",
                "impact": "Eliminates 100% of unlawful tracker violations."
            },
            {
                "step": "Phase 2: UAE PDPL Regulatory Policy Hardening",
                "action": "Deploy compliant bilingual Privacy & Cookie Policy referencing Federal Decree-Law No. 45/2021, DPO appointment, and explicit cross-border data transfer disclosures.",
                "timeline": "Within 12 Hours",
                "impact": "Satisfies mandatory Article 13 & 22 disclosures."
            },
            {
                "step": "Phase 3: Lead Form Consent Checkbox Injection",
                "action": "Embed required affirmative opt-in checkboxes across all inquiry and contact forms, recording proof of consent timestamps in database.",
                "timeline": "Within 24 Hours",
                "impact": "Guarantees full compliance for inbound marketing leads."
            }
        ]

        return result

privacy_scanner = PrivacyScanner()
