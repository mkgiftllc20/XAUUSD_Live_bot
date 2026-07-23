import os


def _bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _float(name: str, default: float) -> float:
    v = os.environ.get(name)
    return float(v) if v else default


def _int(name: str, default: int) -> int:
    v = os.environ.get(name)
    return int(v) if v else default


DRY_RUN = _bool("DRY_RUN", True)
EXPECTED_ACCOUNT_LABEL = os.environ.get("EXPECTED_ACCOUNT_LABEL", "XM_DEMO")
METAAPI_TOKEN = os.environ.get("METAAPI_TOKEN", "")
METAAPI_ACCOUNT_ID = os.environ.get("METAAPI_ACCOUNT_ID", "")
SYMBOL = os.environ.get("SYMBOL", "GOLD")
MAGIC = _int("MAGIC", 20260722)
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
RISK_PCT = _float("RISK_PCT", 2.0)
CONTRACT_VALUE = _float("CONTRACT_VALUE", 100.0)
MAX_LOTS = _float("MAX_LOTS", 0.10)
LOT_STEP = _float("LOT_STEP", 0.01)
MAX_DAILY_LOSS_PCT = _float("MAX_DAILY_LOSS_PCT", 3.0)
MAX_TOTAL_DD_PCT = _float("MAX_TOTAL_DD_PCT", 15.0)
HARD_MAX_DD_PCT = _float("HARD_MAX_DD_PCT", 25.0)
DD_RESET_MODE = _int("DD_RESET_MODE", 1)
MAX_SPREAD_POINTS = _float("MAX_SPREAD_POINTS", 65.0)
TP1_CLOSE_PCT = _float("TP1_CLOSE_PCT", 60.0)
USE_TRAILING = _bool("USE_TRAILING", True)
TRAIL_LEN_BARS = _int("TRAIL_LEN_BARS", 6)
TRAIL_BUF_ATR = _float("TRAIL_BUF_ATR", 0.2)
RUNNER_CAP_R = _float("RUNNER_CAP_R", 1.5)
MAX_HOLD_MINUTES = _int("MAX_HOLD_MINUTES", 1000)
ATR_PERIOD = _int("ATR_PERIOD", 14)
POLL_SEC = _int("POLL_SEC", 10)
CANDLE_TIMEFRAME = os.environ.get("CANDLE_TIMEFRAME", "5m")
STATE_FILE = os.environ.get("STATE_FILE", "live_bot_state.json")
