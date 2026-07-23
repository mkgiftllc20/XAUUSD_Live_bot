import logging
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import config
import metaapi_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s")
log = logging.getLogger("main")
app = FastAPI(title="XAUUSD Livebot Webhook")


class AlertPayload(BaseModel):
    symbol: str
    action: str
    lot: float = Field(..., gt=0)
    magic: int | None = None
    sl: float | None = None
    tp: float | None = None


def _resolve_mt5_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized in {"XAUUSD", "XAUUSDUSD", "XAUUSDM", "GOLD"}:
        return "GOLD"
    return normalized


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/webhook")
async def webhook(payload: AlertPayload, x_secret: str | None = Header(default=None, alias="X-Secret")):
    if not config.WEBHOOK_SECRET:
        log.error("WEBHOOK_SECRET is not configured")
        return JSONResponse(status_code=500, content={"status": "error", "message": "WEBHOOK_SECRET not configured"})

    if x_secret != config.WEBHOOK_SECRET:
        log.warning("Rejected webhook with invalid secret")
        return JSONResponse(status_code=403, content={"status": "error", "message": "Forbidden"})

    incoming_symbol = payload.symbol.upper()
    action = payload.action.lower()

    if incoming_symbol not in {"XAUUSD", "GOLD"}:
        log.warning("Rejected webhook for unsupported symbol: %s", incoming_symbol)
        return JSONResponse(status_code=400, content={"status": "error", "message": "Only XAUUSD/GOLD is supported"})

    if action not in {"buy", "sell"}:
        log.warning("Rejected webhook for unsupported action: %s", action)
        return JSONResponse(status_code=400, content={"status": "error", "message": "Action must be buy or sell"})

    mt5_symbol = _resolve_mt5_symbol(incoming_symbol)
    log.info("Webhook received: symbol=%s -> %s action=%s lot=%s magic=%s sl=%s tp=%s", incoming_symbol, mt5_symbol, action, payload.lot, payload.magic, payload.sl, payload.tp)

    try:
        await metaapi_client.connect()

        price = await metaapi_client.get_price(mt5_symbol)
        if not isinstance(price, dict):
            raise RuntimeError("No market price returned")

        bid = float(price.get("bid", 0.0))
        ask = float(price.get("ask", 0.0))
        if bid <= 0 or ask <= 0:
            raise RuntimeError("Invalid market price")

        spread_points = (ask - bid) / 0.01
        if spread_points > config.MAX_SPREAD_POINTS:
            return JSONResponse(status_code=400, content={"status": "error", "message": f"Spread too wide: {spread_points:.1f} pts"})

        entry_price = ask if action == "buy" else bid
        account = await metaapi_client.get_account_info()
        balance = float(account.get("balance") or account.get("equity") or 0.0)
        risk_usd = max(balance * (config.RISK_PCT / 100.0), 1.0)
        max_distance = max((risk_usd / max(float(payload.lot) * float(config.CONTRACT_VALUE), 0.01)), 0.01)

        if payload.sl is None:
            requested_sl = entry_price - max_distance if action == "buy" else entry_price + max_distance
        else:
            requested_sl = float(payload.sl)
            if action == "buy":
                if requested_sl >= entry_price:
                    requested_sl = entry_price - max_distance
                distance = entry_price - requested_sl
                if distance > max_distance:
                    requested_sl = entry_price - max_distance
            else:
                if requested_sl <= entry_price:
                    requested_sl = entry_price + max_distance
                distance = requested_sl - entry_price
                if distance > max_distance:
                    requested_sl = entry_price + max_distance

        if payload.tp is None:
            tp_distance = max_distance * 2.0
            requested_tp = entry_price + tp_distance if action == "buy" else entry_price - tp_distance
        else:
            requested_tp = float(payload.tp)
            if action == "buy":
                if requested_tp <= entry_price:
                    requested_tp = entry_price + (max_distance * 2.0)
            else:
                if requested_tp >= entry_price:
                    requested_tp = entry_price - (max_distance * 2.0)

        result = await metaapi_client.create_market_order(
            symbol=mt5_symbol,
            direction=action,
            volume=float(payload.lot),
            stop_loss=float(requested_sl),
            take_profit=float(requested_tp),
            comment="TV Signal",
        )
        ticket = None
        if isinstance(result, dict):
            ticket = result.get("ticket") or result.get("id") or result.get("positionId")
        log.info("Order submitted: %s | sl=%s tp=%s spread_pts=%.1f", result, requested_sl, requested_tp, spread_points)
        return {"status": "success", "ticket": ticket}
    except Exception as exc:
        log.exception("Webhook order failed")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})
