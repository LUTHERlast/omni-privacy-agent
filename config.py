import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "OmniPrivacy AI"
    APP_VERSION: str = "1.0.0"
    PORT: int = 8788
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'privacy_agent.db').replace(chr(92), '/')}"

    # Public URL
    PUBLIC_APP_URL: str = os.getenv("PUBLIC_APP_URL", "http://127.0.0.1:8788")
    
    # Offering & Pricing in AED
    OFFERING_NAME: str = "UAE Federal Decree-Law No. 45/2021 (PDPL) Privacy & Bilingual Cookie Consent Hardening Shield"
    OFFERING_DESCRIPTION: str = "Turnkey remediation for unlawful pre-consent tracking cookies, missing bilingual UAE PDPL privacy policies, cross-border data transfer disclosures, and missing form consent checkboxes."
    DEFAULT_DEAL_VALUE: float = 2200.0  # AED 2,200 (PDPL Express Compliance)
    ENTERPRISE_DEAL_VALUE: float = 4500.0  # AED 4,500 (Full Corporate PDPL Shield & DPO Advisory)
    
    # Operator
    OPERATOR_NAME: str = "Athul raj"
    OPERATOR_TITLE: str = "Data Privacy & Regulatory Compliance Specialist"
    OPERATOR_EMAIL: str = "athulaisolutions@gmail.com"
    OPERATOR_TELEGRAM: str = "@dreamer_comrade"
    OPERATOR_WHATSAPP: str = "+971547400174"
    
    # SMTP / Brevo Outbound (Fallback)
    SMTP_ENABLED: bool = True
    SMTP_HOST: str = "smtp-relay.brevo.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "athulaisolutions@gmail.com"
    SMTP_PASSWORD: str = os.getenv("BREVO_SMTP_KEY", "")
    FROM_EMAIL: str = "athulaisolutions@gmail.com"
    FROM_NAME: str = "Athul - UAE Privacy & PDPL Defense"
    
    # Operational Limits & Timing
    MAX_DAILY_AUDITS: int = 50
    OUTREACH_INTERVAL_MINUTES: int = 60
    AUTO_DISCOVERY_INTERVAL_HOURS: int = 4
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
