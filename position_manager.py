"""
position_manager.py
====================
Arka planda surekli calisan dongu: acik pozisyonlari yonetir.
  - TP1 (%60) kismi kapama
  - TP1 sonrasi runner (%40) icin ATR-trailing + GERCEK hard-cap
    (MQL5 v3_1_40_RunnerCapFix.mq5 ile AYNI, duzeltilmis mantik - base_sl
    ep'ye sabitlenmez, cap_sl gercekten bir taban olarak calisir)
  - Zaman-stopu (MAX_HOLD_MINUTES)
  - EMA8/21 ters-cross erken cikis (TP1 sonrasi)
  - Iki katmanli DD korumasi (periyodik + kalici hard-floor)

Pine/TradingView SADECE giris sinyalini (webhook alert) uretir; TUM pozisyon
yonetimi BURADA, MetaApi uzerinden CANLI olarak yapilir.
"""
import asyncio
import logging
from datetime import datetime, timezone

import config
import metaapi_client as mt
from state import state

log = logging.getLogger("position_manager")


def _today_week_keys(dt: datetime):
    today_key = dt.year * 10000 + dt.month * 100 + dt.day
    week_key = dt.isocalendar()[1] + dt.year * 100
    return today_key, week_key


def _wilder_atr(candles: list, period: int) -> float:
    """candles: EN ESKI -> EN YENI sirali varsayilir (dogrulanmadi - DRY_RUN'da
    ilk calistirmada candles[-1]['time']'in gercekten EN YENI bar oldugunu
    logla/kontrol et; MetaApi dokumantasyonu siralamayi acikca belirtmiyor).
    Her biri dict {'high','low','close',...}."""
    if len(candles) <= period:
        return 0.0
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]["high"], candles[i]["low"], candles[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr


def _ema_series(closes: list, period: int) -> list:
    if len(closes) < period:
        return [None] * len(closes)
    k = 2.0 / (period + 1)
    out = [None] * len(closes)
    sma = sum(closes[:period]) / period
    out[period - 1] = sma
    prev = sma
    for i in range(period, len(closes)):
        prev = closes[i] * k + prev * (1 - k)
        out[i] = prev
    return out


async def _check_ema_exit(direction: str) -> bool:
    """TP1 sonrasi EMA8/21 ters-cross erken cikis kontrolu (son 2 kapanmis M5 mum)."""
    try:
        candles = await mt.get_recent_candles(config.SYMBOL, config.CANDLE_TIMEFRAME, limit=80)
    except Exception as ex:
        log.warning("EMA-exit icin mum verisi alinamadi: %s", ex)
        return False
    if len(candles) < 60:
        return False
    closes = [c["close"] for c in candles]
    ema8 = _ema_series(closes, 8)
    ema21 = _ema_series(closes, 21)
    if ema8[-2] is None or ema21[-2] is None or ema8[-3] is None or ema21[-3] is None:
        return False
    # cross_bear (long icin cikis): ema8 yukaridan asagi ema21'i keser
    cross_bear = ema8[-3] >= ema21[-3] and ema8[-2] < ema21[-2]
    cross_bull = ema8[-3] <= ema21[-3] and ema8[-2] > ema21[-2]
    if direction == "buy":
        return cross_bear
    return cross_bull


async def _manage_one_position(pos: dict, tracked: dict):
    position_id = str(pos["id"])   # SDK 'id'yi int dondurur, trading cagrilari str bekler
    direction = "buy" if pos["type"] == "POSITION_TYPE_BUY" else "sell"
    volume = pos["volume"]
    entry_price = tracked["entry_price"]
    rd_open = tracked["rd_open"]
    tp1_price = tracked["tp1_price"]

    price = await mt.get_price(config.SYMBOL)
    bid, ask = price["bid"], price["ask"]
    cur_price = bid if direction == "buy" else ask

    # --- Zaman-stopu ---
    opened_at = datetime.fromisoformat(tracked["opened_at"])
    held_minutes = (datetime.now(timezone.utc) - opened_at).total_seconds() / 60.0
    if held_minutes >= config.MAX_HOLD_MINUTES:
        await mt.close_position(position_id)
        log.info("TIME_STOP: pos=%s %s dakikadir acik, kapatildi.", position_id, round(held_minutes))
        state.forget_position(position_id)
        return

    # --- TP1 tespiti + kismi kapama ---
    if not tracked["tp1_hit"]:
        hit = (direction == "buy" and bid >= tp1_price) or (direction == "sell" and ask <= tp1_price)
        if hit:
            close_vol = round(volume * (config.TP1_CLOSE_PCT / 100.0) / config.LOT_STEP) * config.LOT_STEP
            close_vol = max(config.LOT_STEP, min(volume, close_vol))
            await mt.close_position_partial(position_id, close_vol)
            tracked["tp1_hit"] = True
            state.save()
            log.info("TP1: pos=%s %%%s (%.2f lot) kapatildi.", position_id, config.TP1_CLOSE_PCT, close_vol)
        return  # TP1 henuz vurulmadiysa (ya da bu barda vurulduysa) trailing'e gecme

    # --- TP1 sonrasi: EMA ters-cross erken cikis ---
    if await _check_ema_exit(direction):
        await mt.close_position(position_id)
        log.info("EMA_EXIT: pos=%s kapatildi.", position_id)
        state.forget_position(position_id)
        return

    # --- TP1 sonrasi: ATR-trailing + GERCEK hard-cap [MQL5 v3_1_40 ile AYNI] ---
    try:
        candles = await mt.get_recent_candles(config.SYMBOL, config.CANDLE_TIMEFRAME,
                                               limit=config.TRAIL_LEN_BARS + config.ATR_PERIOD + 5)
    except Exception as ex:
        log.warning("Trailing icin mum verisi alinamadi: %s", ex)
        return
    if len(candles) < config.TRAIL_LEN_BARS + 2:
        return

    atr = _wilder_atr(candles, config.ATR_PERIOD)
    if atr <= 0:
        return

    recent = candles[-config.TRAIL_LEN_BARS:]
    if direction == "buy":
        trail = min(c["low"] for c in recent) - atr * config.TRAIL_BUF_ATR
        base_sl = trail if config.USE_TRAILING else entry_price
        cap_sl = entry_price - rd_open * config.RUNNER_CAP_R
        new_sl = max(base_sl, cap_sl)   # cap_sl GERCEKTEN bir taban (ep'ye sabitlenmedigi icin)
    else:
        trail = max(c["high"] for c in recent) + atr * config.TRAIL_BUF_ATR
        base_sl = trail if config.USE_TRAILING else entry_price
        cap_sl = entry_price + rd_open * config.RUNNER_CAP_R
        new_sl = min(base_sl, cap_sl)

    cur_sl = pos.get("stopLoss")
    if cur_sl is None or abs(new_sl - cur_sl) > 0.01:
        await mt.modify_position_sl(position_id, new_sl)
        log.info("Trailing: pos=%s yeni_sl=%.2f (trail=%.2f cap=%.2f)", position_id, new_sl, trail, cap_sl)


async def run_forever():
    """Ana arka plan dongusu - main.py'nin startup event'inde baslatilir."""
    log.info("Pozisyon yonetim dongusu basladi (poll=%ss).", config.POLL_SEC)
    while True:
        try:
            await _tick()
        except Exception as ex:
            log.exception("Dongu icinde hata (devam ediliyor): %s", ex)
        await asyncio.sleep(config.POLL_SEC)


async def _tick():
    info = await mt.get_account_info()
    equity = info.get("equity", info.get("balance"))
    now = datetime.now(timezone.utc)
    today_key, week_key = _today_week_keys(now)

    dd_result = state.dd_guard.update(equity, today_key, week_key)
    state.save()

    if dd_result["just_hard_halted"]:
        log.warning("MUTLAK DD tavani asildi (%%%.1f). TUM pozisyonlar kapatiliyor, bot KALICI duruyor.",
                    dd_result["abs_dd_pct"])
        positions = await mt.get_positions()
        for p in positions:
            await mt.close_position(p["id"])
        return

    if state.dd_guard.hard_halted:
        return  # kalici durdu, hicbir sey yapma

    positions = await mt.get_positions()
    live_ids = {str(p["id"]) for p in positions}

    # Artik MetaApi'de olmayan (kapanmis) pozisyonlari takipten dus
    for pid in list(state.positions.keys()):
        if pid not in live_ids:
            state.forget_position(pid)

    for pos in positions:
        pid = str(pos["id"])
        if pos.get("symbol") != config.SYMBOL or pos.get("magic") != config.MAGIC:
            continue
        tracked = state.positions.get(pid)
        if tracked is None:
            # Bu bot tarafindan acilmamis/takip edilmeyen bir pozisyon - dokunma.
            continue
        await _manage_one_position(pos, tracked)
