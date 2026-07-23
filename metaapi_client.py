import logging
import config

log = logging.getLogger("metaapi_client")


async def connect():
    if not config.METAAPI_TOKEN or not config.METAAPI_ACCOUNT_ID:
        raise RuntimeError("METAAPI credentials are missing")
    log.info("MetaAPI connection stub initialized")
    return None


def get_connection():
    return None


async def get_account_info() -> dict:
    return {"equity": 1000.0, "balance": 1000.0}


async def get_positions() -> list:
    return []


async def get_price(symbol: str) -> dict:
    return {"bid": 100.0, "ask": 101.0}


async def get_spread_points(symbol: str) -> float:
    return 0.0


async def get_recent_candles(symbol: str, timeframe: str, limit: int = 60) -> list:
    return []


async def create_market_order(symbol: str, direction: str, volume: float, stop_loss: float, take_profit: float, comment: str = "") -> dict:
    return {"dry_run": True, "direction": direction, "symbol": symbol, "volume": volume}


async def modify_position_sl(position_id: str, new_sl: float, take_profit=None) -> dict:
    return {"dry_run": True, "position_id": position_id, "new_sl": new_sl}


async def close_position_partial(position_id: str, volume: float) -> dict:
    return {"dry_run": True, "position_id": position_id, "volume": volume}


async def close_position(position_id: str) -> dict:
    return {"dry_run": True, "position_id": position_id}
