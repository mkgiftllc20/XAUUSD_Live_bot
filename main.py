import logging
import traceback
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import config
import position_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s")
log = logging.getLogger("main")
app = FastAPI(title="XAUUSD Livebot Webhook")


class Alert(BaseModel):
    action: str
    symbol: str
    volume: float = 0.0
    sl: float
    tp: float
    secret: str = ""


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/webhook")
async def webhook(alert: Alert, x_webhook_secret: str = Header(None)):
    if alert.secret != config.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")
    try:
        log.info(f"Signal received: {alert.action} {alert.symbol}")
        result = await position_manager.handle_alert(alert)
        return {"status": "ok", "result": result}
    except Exception as e:
        log.error(f"Error: {e}")
        log.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
