import uvicorn
from config import settings

if __name__ == "__main__":
    print(f"[*] Starting {settings.APP_NAME} v{settings.APP_VERSION} on {settings.HOST}:{settings.PORT}")
    print(f"[*] Operator: {settings.OPERATOR_NAME} | WhatsApp: {settings.OPERATOR_WHATSAPP}")
    print(f"[*] Offering: {settings.OFFERING_NAME}")
    uvicorn.run("web.app:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
