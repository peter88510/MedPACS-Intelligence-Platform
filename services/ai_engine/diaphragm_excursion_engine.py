"""包裝 vendored ./AI 橫膈膜 pipeline 的 concrete engine（paddle 平台）。

AI source vendored 在 ./AI，是個 NON-package，用 sys.path 式絕對 import
（`from config import ...`、`from algorithm import ...`）。要從後端驅動它，必須把
./AI 插進 sys.path 並以「獨立模組名」載入它的 main.py —— 因為模組名 `main` 與後端
自己的 FastAPI main.py（已在 sys.modules）撞名。AI 其餘 top-level 名稱
（config / algorithm / input / visualization）皆 AI 專有、無衝突。

所有 AI import 都 LAZY（在 analyze 內），讓本模組與 66 個後端測試在沒裝
paddle / paddleseglibs / model weights 時也能乾淨 import。缺相依時以
EngineUnavailableError（→ 503）呈現，絕不在 import 期 crash。

替換點：要換平台時實作另一個 DiaphragmEngine 子類，並改 get_engine()
（services/ai_engine/__init__.py）即可，endpoint 程式碼不動。
本層不可 import FastAPI（CLAUDE.md §6）。
"""
import importlib.util
import logging
import os
import sys
import threading
from typing import List, Optional

from services.measurement_type import MeasurementType
from services.ai_engine.base import (
    DiaphragmEngine,
    EngineError,
    EngineResult,
    EngineUnavailableError,
    Measurement,
)

logger = logging.getLogger(__name__)

# repo root = 本檔往上三層（services/ai_engine/<本檔>.py）。
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_AI_DIR = os.path.join(_REPO_ROOT, "AI")

# measurement_type -> AI Phase enum 的 NAME（lazy import 後再轉成 enum）。
_PHASE_NAME_BY_TYPE = {
    MeasurementType.EXCURSION: "EXCURSION",
    MeasurementType.SNIFF: "SNIFF",
}

_MODEL_NAME = "diaphragm_excursion"
_MODEL_VERSION = "6139799"  # vendored snapshot commit（design §4）


class DiaphragmExcursionEngine(DiaphragmEngine):
    """以 LEGACY 單幀模式驅動 AI.main.run、關閉 viz（無磁碟 I/O）。

    REALTIME / GLOBAL_WINDOW 不在同步 endpoint 範圍（它們的正解活在 run-loop state，
    run() 不回傳）；留作未來 streaming / demo 路徑。LEGACY 的選擇封裝在這裡，讓
    endpoint 完全不需要去判斷 multiframe mode。
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()  # AI run() 未知是否 thread-safe；序列化呼叫

    @property
    def model_name(self) -> str:
        return _MODEL_NAME

    @property
    def model_version(self) -> str:
        return _MODEL_VERSION

    def analyze(
        self, image_path: str, measurement_type: MeasurementType
    ) -> EngineResult:
        phase_name = _PHASE_NAME_BY_TYPE.get(measurement_type)
        if phase_name is None:
            # endpoint 已擋 unknown/thickness；此處防禦性再擋一次。
            raise EngineError(
                f"DiaphragmExcursionEngine cannot run measurement_type="
                f"{measurement_type.value!r}"
            )
        if not os.path.exists(image_path):
            raise EngineError(f"DICOM file not found for inference: {image_path}")

        ai = _load_ai()
        phase = ai.Phase[phase_name]
        bundle = self._build_bundle(ai, phase)

        try:
            with self._lock:
                _seq, results = ai.run(image_path, phase=phase, bundle=bundle)
        except EngineUnavailableError:
            raise
        except Exception as e:  # pipeline 失敗 → 500，並留 audit log（§14）
            logger.exception("AI inference failed for %s", image_path)
            raise EngineError(f"AI inference failed: {e}") from e

        measurements = _flatten_measurements(results)
        logger.info(
            "AI inference ok: type=%s frames=%d measurements=%d",
            measurement_type.value, len(results), len(measurements),
        )
        return EngineResult(
            measurement_type=measurement_type,
            model_name=_MODEL_NAME,
            model_version=_MODEL_VERSION,
            pipeline_mode="legacy",
            measurements=measurements,
        )

    @staticmethod
    def _build_bundle(ai, phase):
        """組 RunBundle：以工程師個人調參 run_config.build_bundle() 為基底（在則用、
        不在則 RunBundle.for_phase fallback），再強制覆蓋 API 必要項。

        強制項（不論 run_config 怎麼設）：
          - multiframe.mode = LEGACY：同步單次量測、run() 才會回傳可讀 measurements
            （GLOBAL_WINDOW / REALTIME 的正解活在 run-loop state、run() 不回傳）
          - viz.enabled = False / segmenter.save_predictions = False：API 不寫視覺化/seg PNG

        繼承自 run_config：detection 調參、segmenter model 設定、excursion / motion_curve
        config 等。resolved phase 與 run_config 基底 phase 不同時，重建 detection 對齊。
        """
        if ai.build_bundle is not None:
            try:
                bundle = ai.build_bundle()
            except Exception as e:  # run_config 調參本身有錯 → 明確指回 run_config
                raise EngineError(
                    f"run_config.build_bundle() failed (check AI/run_config.py overrides): {e}"
                ) from e
            if bundle.detection.phase != phase:
                bundle.detection = ai.DiaphragmDetectionConfig.for_phase(phase)
        else:
            bundle = ai.RunBundle.for_phase(phase)

        bundle.multiframe.mode = ai.MultiframeMode.LEGACY
        bundle.viz.enabled = False
        bundle.segmenter.save_predictions = False
        return bundle


class _AIModules:
    """存放 lazy 載入後的 AI callable/enum/個人調參入口。"""

    def __init__(self, run, Phase, RunBundle, MultiframeMode,
                 DiaphragmDetectionConfig, build_bundle):
        self.run = run
        self.Phase = Phase
        self.RunBundle = RunBundle
        self.MultiframeMode = MultiframeMode
        self.DiaphragmDetectionConfig = DiaphragmDetectionConfig
        # run_config.build_bundle（個人 per-machine 調參入口）；run_config.py 不存在則 None
        self.build_bundle = build_bundle


_ai_cache: Optional["_AIModules"] = None
_load_lock = threading.Lock()


def _load_ai() -> _AIModules:
    """只 import 一次 vendored AI pipeline（cached）。paddle / paddleseglibs /
    model weights 未安裝時拋 EngineUnavailableError。"""
    global _ai_cache
    if _ai_cache is not None:
        return _ai_cache
    with _load_lock:
        if _ai_cache is not None:
            return _ai_cache
        if not os.path.isdir(_AI_DIR):
            raise EngineUnavailableError(
                f"Vendored AI source not found at {_AI_DIR}. "
                f"Complete README Step 7 (AI inference setup)."
            )
        if _AI_DIR not in sys.path:
            sys.path.insert(0, _AI_DIR)
        try:
            # config / algorithm / ... 從 sys.path 上的 AI/ 解析（名稱皆唯一）。
            from config import Phase, RunBundle, DiaphragmDetectionConfig
            from config.multiframe_config import MultiframeMode
            # AI/main.py 模組名是 'main' —— 與後端 FastAPI main（已在 sys.modules）
            # 撞名。以檔案路徑用獨立模組名載入，確保拿到的是 AI 的 run() 而非 FastAPI app。
            spec = importlib.util.spec_from_file_location(
                "ai_pipeline_main", os.path.join(_AI_DIR, "main.py")
            )
            ai_main = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ai_main)
        except ImportError as e:
            raise EngineUnavailableError(
                "AI inference deps unavailable (paddle / paddleseglibs / model "
                "weights). Install requirements-ai.txt and complete README Step 7. "
                f"Underlying import error: {e}"
            ) from e

        # run_config.py：工程師個人 per-machine 調參入口（gitignored、可能不存在）。
        # 只 import 模組（不呼叫 build_bundle），缺檔則 build_bundle=None → fallback for_phase。
        try:
            import run_config as _rc
            build_bundle = getattr(_rc, "build_bundle", None)
        except ImportError:
            build_bundle = None

        _ai_cache = _AIModules(
            ai_main.run, Phase, RunBundle, MultiframeMode,
            DiaphragmDetectionConfig, build_bundle,
        )
        logger.info(
            "Vendored AI pipeline loaded from %s (run_config tuning: %s)",
            _AI_DIR, "on" if build_bundle is not None else "off (fallback for_phase)",
        )
        return _ai_cache


# AI pipeline 回傳 numpy 純量（np.int64 / np.float64）；DB 的 result_json 走
# stdlib json.dumps 不認得 numpy 型別。在 AI(numpy) → 平台中立 contract(native
# Python) 的邊界統一正規化，讓 Measurement 真正符合 Optional[int]/[float]/List[int]。
def _opt_int(v) -> Optional[int]:
    return int(v) if v is not None else None


def _opt_float(v) -> Optional[float]:
    return float(v) if v is not None else None


def _opt_point(p) -> Optional[List[int]]:
    return [int(x) for x in p] if p is not None else None


def _flatten_measurements(results) -> List[Measurement]:
    """AI FrameResult[].measurements（PeakInfo）-> 平台中立 Measurement[]。

    LEGACY mode 產生 per-frame results；把跨 frame 的每個 PeakInfo 攤平成單一
    batch-indexed list（envelope 的 measurements[]，design §4）。所有數值在此
    從 numpy 純量轉成原生 Python（見上方註解）。
    """
    out: List[Measurement] = []
    idx = 0
    for r in results:
        for m in getattr(r, "measurements", []) or []:
            out.append(
                Measurement(
                    batch_index=idx,
                    excursion_cm=_opt_float(m.excursion_cm),
                    excursion_pixel=_opt_int(m.excursion_pixel),
                    time_pixel=_opt_int(m.time_pixel),
                    time_sec=_opt_float(m.time_sec),
                    velocity=_opt_float(m.velocity),
                    crest=_opt_point(getattr(m, "crest", None)),
                    trough=_opt_point(getattr(m, "trough", None)),
                )
            )
            idx += 1
    return out
