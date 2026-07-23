"""
risk.py
=======
Pozisyon buyuklugu ve iki katmanli DD (drawdown) koruma mantigi.
XAUUSDBot projesindeki (backtest) ayni mantigin canli/webhook karsiligidir.

SL YERLESIMI (ATR-bazli) ve LOT BUYUKLUGU (%risk-bazli) BIRBIRINI TAMAMLAR:
  - ATR, SL'nin FIYAT SEVIYESINI belirler (piyasanin gercek volatilitesine gore).
  - RiskPercent, o ATR-bazli SL mesafesine gore LOT BUYUKLUGUNU belirler
    (SL'e carpinca kayip TAM OLARAK hesabin %RiskPercent'i olacak sekilde).
  Bu ikisini birbirinin YERINE kullanma - biri "nerede", digeri "ne kadar".
"""
import math

import config

<<<<<<< HEAD

=======
>>>>>>> 4be91a9 (ilk sürüm)
def calc_lot(equity: float, sl_distance_price: float, risk_pct: float = None) -> float:
    """Risk-bazli lot hesabi. XM GOLD: 1.0 lot = $100 / $1 fiyat hareketi (dogrulandi)."""
    risk_pct = config.RISK_PCT if risk_pct is None else risk_pct
    if sl_distance_price <= 0:
        return 0.0
    risk_money = equity * (risk_pct / 100.0)
    raw_lot = risk_money / (sl_distance_price * config.CONTRACT_VALUE)
    lot = math.floor(raw_lot / config.LOT_STEP) * config.LOT_STEP
    lot = max(0.0, min(config.MAX_LOTS, lot))
    return round(lot, 2)

<<<<<<< HEAD

=======
>>>>>>> 4be91a9 (ilk sürüm)
class DrawdownGuard:
    """Iki katmanli DD korumasi: periyodik (resetlenir) + kalici hard-floor.
    XAUUSDBot'taki (MQL5/Python) ayni mantigin bagimsiz-proje kopyasi."""

    def __init__(self):
        self.peak_equity = None
        self.abs_peak_equity = None
        self.halted = False
        self.hard_halted = False
        self.day_start_equity = None
        self.cur_day = None
        self.dd_reset_day = None
        self.dd_reset_week = None

    def to_dict(self):
        return self.__dict__.copy()

    def from_dict(self, d: dict):
        self.__dict__.update(d)

    def update(self, equity: float, today_key: int, week_key: int) -> dict:
        """Her dongude cagir. Donen dict: {'hard_halted':bool,'halted':bool,'just_hard_halted':bool}"""
        if self.peak_equity is None:
            self.peak_equity = equity
            self.abs_peak_equity = equity
            self.day_start_equity = equity
            self.cur_day = today_key

        if today_key != self.cur_day:
            self.cur_day = today_key
            self.day_start_equity = equity

        # DD reset (periyodik halt icin)
        if config.DD_RESET_MODE != 0:
            new_period = False
            if config.DD_RESET_MODE == 1:
                if today_key != self.dd_reset_day:
                    self.dd_reset_day = today_key
                    new_period = True
            else:
                if week_key != self.dd_reset_week:
                    self.dd_reset_week = week_key
                    new_period = True
            if new_period and self.halted:
                self.halted = False
                self.peak_equity = equity

        just_hard_halted = False

        self.abs_peak_equity = max(self.abs_peak_equity, equity)
        abs_dd = (self.abs_peak_equity - equity) / self.abs_peak_equity * 100.0
        if abs_dd >= config.HARD_MAX_DD_PCT and not self.hard_halted:
            self.hard_halted = True
            just_hard_halted = True

        self.peak_equity = max(self.peak_equity, equity)
        total_dd = (self.peak_equity - equity) / self.peak_equity * 100.0
        if total_dd >= config.MAX_TOTAL_DD_PCT:
            self.halted = True

        day_pl_pct = (equity - self.day_start_equity) / self.day_start_equity * 100.0
        daily_loss_hit = day_pl_pct <= -config.MAX_DAILY_LOSS_PCT

        return {
            "hard_halted": self.hard_halted,
            "halted": self.halted,
            "just_hard_halted": just_hard_halted,
            "daily_loss_hit": daily_loss_hit,
            "abs_dd_pct": abs_dd,
            "total_dd_pct": total_dd,
        }

    def can_open_new_trade(self) -> bool:
        return not self.hard_halted and not self.halted
