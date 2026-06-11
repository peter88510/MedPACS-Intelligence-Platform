"""AI 推論引擎 package。

對外公開：抽象介面 / 例外 / 資料結構 + `get_engine()` factory。
`get_engine()` 是「換平台/換模型」的唯一注入點：endpoint 透過 FastAPI 依賴注入
取得 engine，測試則用 app.dependency_overrides 換成 fake，不碰 paddle。
"""
import threading

from services.ai_engine.base import (
    DiaphragmEngine,
    EngineError,
    EngineResult,
    EngineUnavailableError,
    Measurement,
)
from services.ai_engine.diaphragm_excursion_engine import DiaphragmExcursionEngine
from services.ai_engine.serialize import primary_value_unit, to_result_json

__all__ = [
    "DiaphragmEngine",
    "EngineError",
    "EngineResult",
    "EngineUnavailableError",
    "Measurement",
    "DiaphragmExcursionEngine",
    "get_engine",
    "to_result_json",
    "primary_value_unit",
]

# process 級單例：engine 持有 lazy-loaded AI modules 快取，重複建構沒有意義。
_engine_singleton = None
_singleton_lock = threading.Lock()


def get_engine() -> DiaphragmEngine:
    """回傳當前設定的引擎（MVP 固定 paddle 的 DiaphragmExcursionEngine）。

    換平台時改這裡指向新的 DiaphragmEngine 子類即可，endpoint 不動。
    """
    global _engine_singleton
    if _engine_singleton is None:
        with _singleton_lock:
            if _engine_singleton is None:
                _engine_singleton = DiaphragmExcursionEngine()
    return _engine_singleton
