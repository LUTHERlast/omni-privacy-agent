import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from database import Base

class PrivacyAudit(Base):
    __tablename__ = "privacy_audits"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    company_name = Column(String(255), nullable=True)
    overall_score = Column(Integer, default=0)  # 0 to 100
    compliance_grade = Column(String(10), default="F")  # A+, A, B, C, D, F
    risk_level = Column(String(50), default="CRITICAL")  # COMPLIANT, LOW, MODERATE, HIGH, CRITICAL
    fine_exposure_est = Column(String(100), default="AED 50,000 – AED 250,000")

    # Trackers & Pre-Consent Data Gathering
    trackers_count = Column(Integer, default=0)
    trackers_json = Column(Text, default="[]")  # List of detected tracker objects
    
    # Consent Management Platform (CMP) Banner
    cmp_status = Column(String(50), default="MISSING")  # COMPLIANT, INADEQUATE, MISSING
    cmp_name = Column(String(100), nullable=True)  # OneTrust, Cookiebot, CookieScript, etc.
    cookie_blocking_enabled = Column(Boolean, default=False)
    
    # UAE PDPL Privacy Policy
    policy_status = Column(String(50), default="MISSING")  # COMPLIANT, DEFICIENT, MISSING
    policy_url = Column(String(500), nullable=True)
    has_pdpl_reference = Column(Boolean, default=False)
    has_dpo_reference = Column(Boolean, default=False)
    has_rights_reference = Column(Boolean, default=False)
    has_cross_border_reference = Column(Boolean, default=False)
    has_arabic_version = Column(Boolean, default=False)
    
    # Forms & Consent Checkboxes
    forms_status = Column(String(50), default="UNKNOWN")  # COMPLIANT, NON_COMPLIANT, NO_FORMS
    forms_count = Column(Integer, default=0)
    forms_lacking_consent = Column(Integer, default=0)
    
    # SSL & Transport Security
    ssl_status = Column(String(50), default="SECURE")  # SECURE, INSECURE
    
    # Legal Violations & Blueprint
    issues_json = Column(Text, default="[]")  # Specific UAE PDPL Article violations
    remediation_blueprint_json = Column(Text, default="[]")  # 3-step action plan
    audit_token = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    company_name = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    location = Column(String(255), default="Dubai, UAE")
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_role = Column(String(255), default="Managing Director / CEO / Legal Counsel")
    phone = Column(String(100), nullable=True)  # WhatsApp / Phone
    
    # Pipeline & Deal
    status = Column(String(50), default="DISCOVERED")  # DISCOVERED, AUDITED, CONTACTED, REPLIED_INTERESTED, WON, PAID
    deal_value = Column(Float, default=2200.0)  # in AED
    audit_id = Column(Integer, ForeignKey("privacy_audits.id"), nullable=True)
    
    # Outreach Tracker
    emails_sent_count = Column(Integer, default=0)
    whatsapp_sent_count = Column(Integer, default=0)
    last_contacted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class PrivacyEvent(Base):
    __tablename__ = "privacy_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50))  # AUDIT_RUN, WHATSAPP_CLICKED, PROPOSAL_VIEWED, WON
    domain = Column(String(255), nullable=True)
    severity = Column(String(20), default="INFO")  # INFO, WARNING, CRITICAL, SUCCESS
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    domain = Column(String(255))
    recipient = Column(String(255))
    subject = Column(String(255))
    status = Column(String(50))  # SENT, FAILED, SIMULATED
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    error_message = Column(Text, nullable=True)
