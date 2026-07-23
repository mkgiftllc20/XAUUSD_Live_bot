"""
config.py
=========
Tum ayarlar ENV DEGISKENLERINDEN okunur - hicbir sifre/token koda YAZILMAZ.
Railway'de bu degiskenleri "Variables" sekmesinden ayarla.
"""
import os

<<<<<<< HEAD

=======
>>>>>>> 4be91a9 (ilk sürüm)
def _bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")

<<<<<<< HEAD

=======
>>>>>>> 4be91a9 (ilk sürüm)
def _float(name: str, default: float) -> float:
    v = os.environ.get(name)
    return float(v) if v else default

<<<<<<< HEAD

=======
>>>>>>> 4be91a9 (ilk sürüm)
def _int(name: str, default: int) -> int:
    v = os.environ.get(name)
    return int(v) if v else default

<<<<<<< HEAD

=======
>>>>>>> 4be91a9 (ilk sürüm)
# ============================== GUVENLIK ==================================
# DRY_RUN=true iken hicbir gercek emir MetaApi'ye gonderilmez, sadece loglanir.
# Once DRY_RUN=true ile deploy et, webhook loglarini izle, SONRA false yap.
DRY_RUN = _bool("DRY_RUN", True)

# MetaApi hesabinin GERCEKTEN demo oldugunu dogrulamak icin: MetaApi hesap
# panelinde gordugun hesap ID'sini buraya da yaz - kod baslarken bu iki
# degerin (env + burada beklenen) AYNI oldugunu kontrol eder. Yanlislikla
# baska bir (canli) hesaba baglanmayi onlemek icin ekstra bir guvenlik katmani.
EXPECTED_ACCOUNT_LABEL = os.environ.get("EXPECTED_ACCOUNT_LABEL", "XM_DEMO")

# ============================== METAAPI ====================================
METAAPI_TOKEN      = os.environ.get("METAAPI_TOKEN", "")
METAAPI_ACCOUNT_ID = os.environ.get("METAAPI_ACCOUNT_ID", "")
SYMBOL             = os.environ.get("SYMBOL", "GOLD")   # XM'de dogrulanmis: GOLD (XAUUSD DEGIL)
MAGIC              = _int("MAGIC", 20260722)

# Webhook'u dogrulamak icin basit paylasilan sir (TradingView alert body'sine
# eklenip burada kontrol edilir - webhook URL'i tahmin edilirse bile bu
# olmadan emir acilamaz).
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# ============================== RISK / DD ==================================
RISK_PCT             = _float("RISK_PCT", 2.0)     # islem basi risk (%)
CONTRACT_VALUE       = _float("CONTRACT_VALUE", 100.0)  # $/1.0 lot/$1 fiyat hareketi (XM GOLD=100, MT5'ten dogrulandi)
MAX_LOTS             = _float("MAX_LOTS", 0.10)
LOT_STEP             = _float("LOT_STEP", 0.01)
MAX_DAILY_LOSS_PCT   = _float("MAX_DAILY_LOSS_PCT", 3.0)
MAX_TOTAL_DD_PCT     = _float("MAX_TOTAL_DD_PCT", 15.0)   # periyodik, resetlenir
HARD_MAX_DD_PCT      = _float("HARD_MAX_DD_PCT", 25.0)    # kalici kill-switch
DD_RESET_MODE        = _int("DD_RESET_MODE", 1)          # 0=hic 1=gunluk 2=haftalik

MAX_SPREAD_POINTS    = _float("MAX_SPREAD_POINTS", 65.0)  # kullanici talebi: max 65 puan

# ============================== POZISYON YONETIMI ============================
TP1_CLOSE_PCT       = _float("TP1_CLOSE_PCT", 60.0)   # TP1'de kapatilacak yuzde
USE_TRAILING        = _bool("USE_TRAILING", True)
TRAIL_LEN_BARS      = _int("TRAIL_LEN_BARS", 6)       # M5 bar
TRAIL_BUF_ATR       = _float("TRAIL_BUF_ATR", 0.2)
RUNNER_CAP_R        = _float("RUNNER_CAP_R", 1.5)     # runner en fazla rd_open*bu kadar geri verebilir
MAX_HOLD_MINUTES    = _int("MAX_HOLD_MINUTES", 1000)  # 200 M5-bar ~ 16.6 saat = 1000 dk
ATR_PERIOD          = _int("ATR_PERIOD", 14)

# ============================== POLLING ====================================
POLL_SEC              = _int("POLL_SEC", 10)   # pozisyon yonetimi dongu araligi
CANDLE_TIMEFRAME      = os.environ.get("CANDLE_TIMEFRAME", "5m")

STATE_FILE = os.environ.get("STATE_FILE", "live_bot_state.json")
