"""
main.py
=======
FastAPI uygulamasi: TradingView webhook alici + arka planda pozisyon yonetim
dongusu. Railway'de "web" process olarak calisir (bkz Procfile).

Alert formati (TradingView Pine'dan, degistirilmeden):
  {"action":"buy"/"sell","symbol":"...","volume":...,"sl":...,"tp":...}

NOT: "volume" alani Pine'dan gelse de BURADA KULLANILMAZ - lot buyuklugu
GUVENLIK ICIN sunucu tarafinda (MetaApi'den canli equity + alert'teki sl
mesafesi ile) YENIDEN hesaplanir (bkz risk.calc_lot). Boylece TradingView'in
syminfo.pointvalue kaynakli olceklendirme belirsizligi (daha once GrafikOku
Pine portunda karsilasilan "lot hep tavanda" sorunu) canli hesaba SIZMAZ.
"""
import asyncio
import logging
import traceback
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import config
import metaapi_client as mt
import position_manager
import risk
from state import state

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")

app = FastAPI(title="XAUUSD LiveBot Webhook")


class Alert(BaseModel):
    action: str
    symbol: str
    volume: float = 0.0   # gelir ama KULLANILMAZ (yukaridaki nota bkz)
    sl: float
    tp: float
    secret: str = ""


@app.on_event("startup")
async def on_startup():
    log.info("Baslatiliyor... DRY_RUN=%s", config.DRY_RUN)
    await mt.connect()
    asyncio.create_task(position_manager.run_forever())
    log.info("Webhook sunucusu ve pozisyon yonetim dongusu hazir.")


@app.get("/health")
async def health():
    return {"status": "ok", "dry_run": config.DRY_RUN,
            "hard_halted": state.dd_guard.hard_halted,
            "halted": state.dd_guard.halted,
            "tracked_positions": list(state.positions.keys())}


@app.post("/webhook")
async def webhook(alert: Alert, x_webhook_secret: str = Header(default="")):
    log.info(">>> GELEN ALERT: %s", alert.model_dump())

    secret = alert.secret or x_webhook_secret
    if config.WEBHOOK_SECRET and secret != config.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Gecersiz webhook secret.")

    if alert.symbol.upper() not in (config.SYMBOL.upper(), "XAUUSD"):
        log.warning("Beklenmeyen sembol: %s (bekleniyordu: %s) - reddedildi.", alert.symbol, config.SYMBOL)
        raise HTTPException(status_code=400, detail="Sembol uyusmuyor.")

    if alert.action not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="action 'buy' ya da 'sell' olmali.")

    # --- GUVENLIK GATE'LERI ---
    if state.dd_guard.hard_halted:
        log.warning("Sinyal reddedildi: MUTLAK DD tavani asilmis, bot kalici duruyor.")
        return {"status": "rejected", "reason": "hard_halted"}
    if state.dd_guard.halted:
        log.warning("Sinyal reddedildi: periyot-ici DD tavani asilmis.")
        return {"status": "rejected", "reason": "halted"}

    # NOT: Buradan sonrasi MetaApi'ye gercek agirlikli cagrilar yapiyor -
    # herhangi biri patlarsa TAM TRACEBACK'i loglayip 500'u ANLAMLI bir JSON
    # olarak donuyoruz (onceki "Internal Server Error" bos govdesi yerine).
    try:
        spread_points = await mt.get_spread_points(config.SYMBOL)
        if spread_points > config.MAX_SPREAD_POINTS:
            log.warning("Sinyal reddedildi: spread=%.1f > MaxSpreadPoints=%.1f",
                        spread_points, config.MAX_SPREAD_POINTS)
            return {"status": "rejected", "reason": "spread_too_wide", "spread_points": spread_points}

        # --- LOT BUYUKLUGU: sunucu tarafinda YENIDEN hesaplanir (Pine'in volume'u YOK SAYILIR) ---
        price = await mt.get_price(config.SYMBOL)
        proxy_entry = price["ask"] if alert.action == "buy" else price["bid"]
        sl_distance = abs(proxy_entry - alert.sl)
        if sl_distance <= 0:
            raise HTTPException(status_code=400, detail="Gecersiz SL mesafesi (sl==entry?).")

        account_info = await mt.get_account_info()
        equity = account_info.get("equity", account_info.get("balance"))
        lot = risk.calc_lot(equity, sl_distance)
        if lot <= 0:
            log.warning("Hesaplanan lot 0 - islem acilmadi (equity=%.2f sl_dist=%.4f)", equity, sl_distance)
            return {"status": "rejected", "reason": "zero_lot"}

        log.info("Emir gonderiliyor: %s %s lot=%.2f sl=%.2f tp=%.2f", alert.action, config.SYMBOL,
                  lot, alert.sl, alert.tp)
        result = await mt.create_market_order(config.SYMBOL, alert.action, lot, alert.sl, alert.tp,
                                               comment="webhook")
        log.info("MetaApi sonucu: %s", result)

        if config.DRY_RUN:
            return {"status": "dry_run", "would_open": {"direction": alert.action, "lot": lot,
                                                          "sl": alert.sl, "tp": alert.tp}}

        # NOT: MetatraderTradeResponse'ta dolum fiyati YOK (sadece numericCode/
        # stringCode/message/orderId/positionId) - gercek acilis fiyatini almak
        # icin pozisyonu ayrica cekiyoruz.
        position_id = result.get("positionId") or result.get("orderId")
        filled_price = proxy_entry
        if position_id:
            try:
                positions = await mt.get_positions()
                match = next((p for p in positions if str(p.get("id")) == str(position_id)), None)
                if match:
                    filled_price = match.get("openPrice", proxy_entry)
            except Exception as ex:
                log.warning("Acilis fiyati dogrulanamadi, proxy fiyat kullanildi: %s", ex)

            state.track_position(position_id, alert.action, filled_price, alert.sl, alert.tp,
                                  datetime.now(timezone.utc).isoformat())
            log.info("Pozisyon acildi ve takibe alindi: id=%s %s lot=%.2f fiyat=%.2f",
                      position_id, alert.action, lot, filled_price)
        else:
            log.warning("MetaApi sonucunda position_id bulunamadi - SDK dokumantasyonunu kontrol et: %s", result)

        return {"status": "opened", "lot": lot, "result": result}

    except HTTPException:
        raise  # 400/401 gibi kasitli HTTP hatalari oldugu gibi gecsin
    except Exception as ex:
        tb = traceback.format_exc()
        details = getattr(ex, "details", None)  # MetaApi ValidationException._details
        log.error(">>> WEBHOOK HATASI: %s | details=%s\n%s", ex, details, tb)
        return JSONResponse(status_code=500, content={"error": str(ex), "type": type(ex).__name__,
                                                        "details": details})
