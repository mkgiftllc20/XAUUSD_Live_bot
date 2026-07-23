import math
import config


def calc_lot(equity: float, sl_distance_price: float, risk_pct: float = None) -> float:
    risk_pct = config.RISK_PCT if risk_pct is None else risk_pct
    if sl_distance_price <= 0:
        return 0.0
    risk_money = equity * (risk_pct / 100.0)
    raw_lot = risk_money / (sl_distance_price * config.CONTRACT_VALUE)
    lot = math.floor(raw_lot / config.LOT_STEP) * config.LOT_STEP
    lot = max(0.0, min(config.MAX_LOTS, lot))
    return round(lot, 2)


class DrawdownGuard:
    def __init__(self):
        self.halted = False
        self.hard_halted = False

    def to_dict(self):
        return {"halted": self.halted, "hard_halted": self.hard_halted}

    def from_dict(self, d: dict):
        self.halted = d.get("halted", False)
        self.hard_halted = d.get("hard_halted", False)

    def update(self, equity: float, today_key: int, week_key: int) -> dict:
        return {"hard_halted": self.hard_halted, "halted": self.halted, "just_hard_halted": False}

    def can_open_new_trade(self) -> bool:
        return not self.hard_halted and not self.halted
