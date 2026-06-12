"""包裝 vendored ./AI 的 `inference.py` facade（paddle 平台）的 concrete engine。

上游（diaphragm_excursion repo）已提供乾淨程式化入口 `inference.analyze()`，回傳
全 native 型別、tuning 由上游 run_config 統一管、強制 LEGACY/viz-off。MedPACS 這層
因此極薄：載入 facade（lazy）→ 預載 warm segmenter（一次）→ 每 request 呼叫 analyze。

`inference` 模組名不與後端任何模組撞名 → 直接 `import inference`，不需要先前對
`main` 撞名用的 importlib spec hack。AI import 仍 LAZY（缺 paddle/weights → 503），
讓後端與 66/82-test 套件無 paddle 也能乾淨 import。

替換點：要換平台時實作另一個 DiaphragmEngine 子類並改 get_engine()。
本層不可 import FastAPI（CLAUDE.md §6）。
"""
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

_MODEL_NAME = "diaphragm_excursion"
# facade 只接受 excursion / sniff；unknown/thickness 由 endpoint 在呼叫前擋掉。
_SUPPORTED = {MeasurementType.EXCURSION, MeasurementType.SNIFF}


class DiaphragmExcursionEngine(DiaphragmEngine):
    """驅動 `AI/inference.py` facade（LEGACY 同步量測）。

    warm segmenter（paddle model）lazy 載一次後快取、每次 analyze 重用。所有
    inference 呼叫以 _run_lock 序列化（AI pipeline 未知是否 thread-safe、且共用
    segmenter）。
    """

    def __init__(self) -> None:
        self._init_lock = threading.Lock()   # 保護 facade / segmenter 的 lazy 初始化
        self._run_lock = threading.Lock()    # 序列化 inference 呼叫
        self._inference = None               # lazy-loaded AI.inference 模組
        self._segmenter = None               # warm segmenter（載一次）

    @property
    def model_name(self) -> str:
        return _MODEL_NAME

    @property
    def model_version(self) -> str:
        # 由 facade 常數提供；facade 尚未載入前回 "unknown"。
        if self._inference is None:
            return "unknown"
        return getattr(self._inference, "MODEL_VERSION", "unknown")

    def analyze(
        self, image_path: str, measurement_type: MeasurementType
    ) -> EngineResult:
        if measurement_type not in _SUPPORTED:
            # endpoint 已擋 unknown/thickness；此處防禦性再擋一次。
            raise EngineError(
                f"DiaphragmExcursionEngine cannot run measurement_type="
                f"{measurement_type.value!r}"
            )
        if not os.path.exists(image_path):
            raise EngineError(f"DICOM file not found for inference: {image_path}")

        inference = self._load_inference()
        segmenter = self._get_warm_segmenter(inference, measurement_type)

        try:
            with self._run_lock:
                res = inference.analyze(
                    image_path,
                    phase=measurement_type.value,
                    segmenter=segmenter,
                )
        except EngineUnavailableError:
            raise
        except Exception as e:  # pipeline 失敗 → 500，並留 audit log（§14）
            logger.exception("AI inference failed for %s", image_path)
            raise EngineError(f"AI inference failed: {e}") from e

        measurements = [
            Measurement(
                batch_index=i,
                excursion_cm=m.excursion_cm,
                excursion_pixel=m.excursion_pixel,
                time_pixel=m.time_pixel,
                time_sec=m.time_sec,
                velocity=m.velocity,
                crest=list(m.crest),
                trough=list(m.trough),
            )
            for i, m in enumerate(res.measurements)
        ]
        logger.info(
            "AI inference ok: type=%s frames=%d measurements=%d",
            measurement_type.value, res.frame_count, len(measurements),
        )
        return EngineResult(
            measurement_type=measurement_type,
            model_name=_MODEL_NAME,
            model_version=res.model_version,
            pipeline_mode="legacy",
            measurements=measurements,
            mask_path=getattr(res, "mask_path", None),
        )

    def warmup(self) -> None:
        """啟動時預載 facade + warm segmenter 一次，消除第一個 request 的冷啟。

        重用 analyze 走的同一條 lazy 路徑（兩者共用 _segmenter 快取）。
        缺 paddle/weights → EngineUnavailableError（由 startup 端降級處理）。
        以 excursion 預載；segmenter 快取單一、後續 sniff 共用。

        不持有 _run_lock：ASGI lifespan 在 startup event 序列完成後才開放接收
        request，故 warmup 與第一個 analyze 不會並發進入 pipeline；segmenter 的
        初始化本身已由 _get_warm_segmenter 的 _init_lock 保護。
        """
        inference = self._load_inference()
        self._get_warm_segmenter(inference, MeasurementType.EXCURSION)

    def _get_warm_segmenter(self, inference, measurement_type: MeasurementType):
        """lazy 預載 paddle segmenter 一次並快取（model load 秒級、只做一次）。"""
        if self._segmenter is not None:
            return self._segmenter
        with self._init_lock:
            if self._segmenter is None:
                self._segmenter = inference.prepare_segmenter(
                    phase=measurement_type.value
                )
                logger.info("Warm segmenter prepared (phase=%s)", measurement_type.value)
        return self._segmenter

    def _load_inference(self):
        """lazy import `AI/inference.py`（cached）。缺 paddle/weights → EngineUnavailableError。

        把 ./AI 插上 sys.path 後直接 `import inference`（名稱不撞後端 main，
        不需要 importlib spec 載入）。
        """
        if self._inference is not None:
            return self._inference
        with self._init_lock:
            if self._inference is not None:
                return self._inference
            if not os.path.isdir(_AI_DIR):
                raise EngineUnavailableError(
                    f"Vendored AI source not found at {_AI_DIR}. "
                    f"Complete README Step 7 (AI inference setup)."
                )
            if _AI_DIR not in sys.path:
                sys.path.insert(0, _AI_DIR)
            try:
                import inference  # AI/inference.py — facade（名稱唯一、無撞名）
            except ImportError as e:
                raise EngineUnavailableError(
                    "AI inference deps unavailable (paddle / paddleseglibs / model "
                    "weights). Install requirements-ai.txt and complete README Step 7. "
                    f"Underlying import error: {e}"
                ) from e
            self._inference = inference
            logger.info("AI inference facade loaded from %s", _AI_DIR)
            return self._inference
