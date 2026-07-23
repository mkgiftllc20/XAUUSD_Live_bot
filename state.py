import json
import threading
from pathlib import Path
import config
from risk import DrawdownGuard

_lock = threading.Lock()


class LiveState:
    def __init__(self):
        self.dd_guard = DrawdownGuard()
        self.positions: dict = {}
        self._path = Path(config.STATE_FILE)
        self.load()

    def load(self):
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self.dd_guard.from_dict(data.get("dd_guard", {}))
                self.positions = data.get("positions", {})
            except Exception:
                pass

    def save(self):
        with _lock:
            data = {"dd_guard": self.dd_guard.to_dict(), "positions": self.positions}
            self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def track_position(self, position_id: str, direction: str, entry_price: float, sl: float, tp1_price: float, opened_at: str):
        self.positions[str(position_id)] = {
            "direction": direction,
            "entry_price": entry_price,
            "sl": sl,
            "tp1_price": tp1_price,
            "opened_at": opened_at,
        }
        self.save()

    def forget_position(self, position_id: str):
        self.positions.pop(str(position_id), None)
        self.save()


state = LiveState()
