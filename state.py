"""
state.py
========
Paylasilan durum: DD guard + acik pozisyonlarin runner-yonetim bilgisi
(rd_open, tp1 seviyesi, tp1 vurulmus mu). JSON dosyasina kalicilastirilir ki
Railway servisi yeniden baslarsa (deploy/crash) kaldigi yerden devam edebilsin.

NOT: Railway'in varsayilan dosya sistemi EPHEMERAL'dir (redeploy'da sifirlanir).
Gercekten kalici durum istiyorsan bir Railway Volume baglamalisin, aksi halde
her redeploy'da DD-tepe takibi ve acik-pozisyon runner durumu sifirlanir
(acik pozisyonlarin KENDISI MT5'te/MetaApi'de kalir, kaybolmaz - sadece bu
scriptin ONLARI nasil yonetecegini hatirlamasi sifirlanir).
"""
import json
import threading
from pathlib import Path

import config
from risk import DrawdownGuard

_lock = threading.Lock()


class LiveState:
    def __init__(self):
        self.dd_guard = DrawdownGuard()
        self.positions: dict = {}   # position_id(str) -> {...}
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

    def track_position(self, position_id: str, direction: str, entry_price: float,
                        sl: float, tp1_price: float, opened_at: str):
        self.positions[str(position_id)] = {
            "direction": direction,
            "entry_price": entry_price,
            "rd_open": abs(entry_price - sl),
            "tp1_price": tp1_price,
            "tp1_hit": False,
            "opened_at": opened_at,
        }
        self.save()

    def forget_position(self, position_id: str):
        self.positions.pop(str(position_id), None)
        self.save()


state = LiveState()
