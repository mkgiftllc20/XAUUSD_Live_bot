"""
metaapi_client.py
=================
MetaApi Python SDK (metaapi-cloud-sdk) etrafinda ince bir sarmalayici.

!!! ONEMLI DURUSTLUK NOTU !!!
Bu dosyayi GERCEK bir MetaApi hesabina/token'ina karsi CALISTIRAMADIM (bu
ortamda MetaApi erisimim yok). Asagidaki metod adlari/imzalari MetaApi'nin
Python SDK'sinin bilinen genel kullanim sekline gore yazildi, ama SDK
versiyonlar arasi degisebilir. DEPLOY ETMEDEN ONCE:
  1) pip install metaapi-cloud-sdk (guncel surum)
  2) Resmi dokumantasyonla (https://metaapi.cloud/docs/client/python/)
     asagidaki cagrilari (create_market_buy_order/sell_order, modify_position,
     close_position_partially, get_symbol_price, get_historical_candles)
     KARSILASTIR - parametre adlari (stop_loss vs stopLoss gibi) SDK
     versiyonuna gore degisebilir.
  3) DRY_RUN=true ile once test et (config.py).
"""
import asyncio
import logging

from metaapi_cloud_sdk import MetaApi

import config

log = logging.getLogger("metaapi_client")

_api = None
_account = None
_connection = None


async def connect():
    """MetaApi'ye baglanir, hesabi deploy/senkronize eder, RPC baglantisi doner."""
    global _api, _account, _connection

    if not config.METAAPI_TOKEN or not config.METAAPI_ACCOUNT_ID:
        raise RuntimeError("METAAPI_TOKEN / METAAPI_ACCOUNT_ID env degiskenleri eksik.")

    _api = MetaApi(config.METAAPI_TOKEN)
    _account = await _api.metatrader_account_api.get_account(config.METAAPI_ACCOUNT_ID)

    # GUVENLIK: hesap etiketi/adi beklenen "DEMO" isaretiyle uyusuyor mu kontrol et.
    # MetaApi hesap nesnesinin "name"/"type" alanlari saglayiciya gore degisebilir -
    # burada sadece BILGI amacli logluyoruz; asil guvence senin dogru
    # METAAPI_ACCOUNT_ID'yi (DEMO hesabin) girmis olmandir.
    log.info("MetaApi hesabi: id=%s name=%s type=%s",
             getattr(_account, "id", "?"), getattr(_account, "name", "?"),
             getattr(_account, "type", "?"))

    if _account.state != "DEPLOYED":
        await _account.deploy()
    await _account.wait_connected()

    _connection = _account.get_rpc_connection()
    await _connection.connect()
    await _connection.wait_synchronized()
    log.info("MetaApi RPC baglantisi senkronize oldu.")
    return _connection


def get_connection():
    if _connection is None:
        raise RuntimeError("MetaApi baglantisi henuz kurulmadi - once connect() cagir.")
    return _connection


async def get_account_info() -> dict:
    conn = get_connection()
    return await conn.get_account_information()


async def get_positions() -> list:
    conn = get_connection()
    return await conn.get_positions()


async def get_price(symbol: str) -> dict:
    conn = get_connection()
    return await conn.get_symbol_price(symbol)


async def get_spread_points(symbol: str) -> float:
    """Guncel spread'i (puan) dondurur. price['bid']/['ask'] + symbol point buyuklugu gerekir."""
    price = await get_price(symbol)
    bid = price.get("bid")
    ask = price.get("ask")
    if bid is None or ask is None:
        return 0.0
    # GOLD icin point=0.01 (XM'de dogrulandi) - farkli sembol/broker icin degisebilir.
    point = 0.01
    return (ask - bid) / point


async def get_recent_candles(symbol: str, timeframe: str, limit: int = 60) -> list:
    """Son N mumu dondurur (en eski -> en yeni sirali bekleniyor)."""
    if _account is None:
        raise RuntimeError("Hesap baglantisi yok.")
    candles = await _account.get_historical_candles(symbol, timeframe, None, limit)
    return candles


async def create_market_order(symbol: str, direction: str, volume: float,
                               stop_loss: float, take_profit: float, comment: str = "") -> dict:
    """direction: 'buy' ya da 'sell'. DRY_RUN=true ise emir GONDERILMEZ, sadece loglanir."""
    if config.DRY_RUN:
        log.info("[DRY_RUN] Emir GONDERILMEDI: %s %s vol=%.2f sl=%.2f tp=%.2f",
                  direction.upper(), symbol, volume, stop_loss, take_profit)
        return {"dry_run": True}

    conn = get_connection()
    options = {"comment": comment, "magic": str(config.MAGIC)}
    if direction == "buy":
        return await conn.create_market_buy_order(symbol, volume, stop_loss=stop_loss,
                                                    take_profit=take_profit, options=options)
    elif direction == "sell":
        return await conn.create_market_sell_order(symbol, volume, stop_loss=stop_loss,
                                                     take_profit=take_profit, options=options)
    raise ValueError(f"Gecersiz direction: {direction}")


async def modify_position_sl(position_id: str, new_sl: float, take_profit=None) -> dict:
    if config.DRY_RUN:
        log.info("[DRY_RUN] SL guncellenmedi: pos=%s yeni_sl=%.2f", position_id, new_sl)
        return {"dry_run": True}
    conn = get_connection()
    return await conn.modify_position(position_id, stop_loss=new_sl, take_profit=take_profit)


async def close_position_partial(position_id: str, volume: float) -> dict:
    if config.DRY_RUN:
        log.info("[DRY_RUN] Kismi kapama yapilmadi: pos=%s vol=%.2f", position_id, volume)
        return {"dry_run": True}
    conn = get_connection()
    return await conn.close_position_partially(position_id, volume)


async def close_position(position_id: str) -> dict:
    if config.DRY_RUN:
        log.info("[DRY_RUN] Pozisyon kapatilmadi: pos=%s", position_id)
        return {"dry_run": True}
    conn = get_connection()
    return await conn.close_position(position_id)
