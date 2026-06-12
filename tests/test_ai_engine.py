"""
tests/test_ai_engine.py
=======================
AI engine 抽象層測試（serialize / guard / factory）。

scope：
- 純邏輯，完全不載入 paddle / vendored AI source
- engine 的真實推論路徑（_load_ai → AI.run）由工程師在裝好 paddle 後手動驗證，
  不在單元測試範圍（環境相依）
"""
import pytest

from services.measurement_type import MeasurementType
from services.ai_engine import (
    DiaphragmEngine,
    DiaphragmExcursionEngine,
    EngineError,
    EngineResult,
    Measurement,
    get_engine,
    primary_value_unit,
    to_result_json,
)


def _excursion_result(measurements):
    return EngineResult(
        measurement_type=MeasurementType.EXCURSION,
        model_name="diaphragm_excursion",
        model_version="6139799",
        pipeline_mode="legacy",
        measurements=measurements,
    )


# --- serialize ---

def test_to_result_json_envelope_shape():
    result = _excursion_result([
        Measurement(batch_index=0, excursion_cm=2.31, excursion_pixel=120,
                    time_pixel=45, crest=[320, 110], trough=[365, 230]),
    ])
    envelope = to_result_json(result)
    assert envelope["schema_version"] == 1
    assert envelope["measurement_type"] == "excursion"
    assert envelope["pipeline_mode"] == "legacy"
    assert envelope["model_version"] == "6139799"
    assert len(envelope["measurements"]) == 1
    assert envelope["measurements"][0]["excursion_cm"] == 2.31
    assert envelope["primary"] == {"label": "excursion_cm", "value": 2.31, "unit": "cm"}


def test_primary_value_unit_with_measurement():
    result = _excursion_result([Measurement(batch_index=0, excursion_cm=1.8)])
    assert primary_value_unit(result) == (1.8, "cm")


def test_primary_value_unit_no_measurements_is_none():
    result = _excursion_result([])
    assert primary_value_unit(result) == (None, None)
    assert to_result_json(result)["primary"]["value"] is None


def test_primary_value_unit_none_excursion_cm_is_none():
    """無 PhysicalDeltaY → excursion_cm=None → primary 不報數字。"""
    result = _excursion_result([Measurement(batch_index=0, excursion_cm=None,
                                            excursion_pixel=120)])
    assert primary_value_unit(result) == (None, None)


def test_engine_result_primary_property():
    m0 = Measurement(batch_index=0, excursion_cm=2.0)
    assert _excursion_result([m0, Measurement(batch_index=1)]).primary is m0
    assert _excursion_result([]).primary is None


# --- DiaphragmExcursionEngine guards（不觸發 paddle 載入）---

def test_engine_is_diaphragm_engine_subtype():
    assert isinstance(DiaphragmExcursionEngine(), DiaphragmEngine)


def test_engine_rejects_unsupported_type_before_loading_ai():
    """thickness 沒有對應 Phase → guard 在 _load_ai 之前就拋 EngineError。"""
    engine = DiaphragmExcursionEngine()
    with pytest.raises(EngineError):
        engine.analyze(__file__, MeasurementType.THICKNESS)
    with pytest.raises(EngineError):
        engine.analyze(__file__, MeasurementType.UNKNOWN)


def test_engine_missing_file_raises_before_loading_ai():
    engine = DiaphragmExcursionEngine()
    with pytest.raises(EngineError):
        engine.analyze("/no/such/file.dcm", MeasurementType.EXCURSION)


def test_engine_metadata():
    engine = DiaphragmExcursionEngine()
    assert engine.model_name == "diaphragm_excursion"
    # model_version 改由 facade(inference.MODEL_VERSION) 提供；未載入前回 "unknown"
    # （載入需 paddle，不在單元測試範圍）。
    assert engine.model_version == "unknown"


# --- factory ---

def test_get_engine_returns_singleton():
    assert get_engine() is get_engine()
    assert isinstance(get_engine(), DiaphragmExcursionEngine)


# --- warmup（不觸發 paddle 載入）---

def test_base_warmup_default_is_noop():
    """ABC 預設 warmup 為 no-op：fake / 輕量 engine 繼承後呼叫不拋、回 None。"""
    class _FakeEngine(DiaphragmEngine):
        @property
        def model_name(self):
            return "fake"

        @property
        def model_version(self):
            return "0"

        def analyze(self, image_path, measurement_type):
            return _excursion_result([])

    assert _FakeEngine().warmup() is None


def test_excursion_engine_overrides_warmup():
    """DiaphragmExcursionEngine 真的 override 了 warmup（非繼承的 no-op）。

    此處不實際呼叫——觸發會載 paddle / weights（環境相依，不在單元測試範圍）。
    """
    assert DiaphragmExcursionEngine.warmup is not DiaphragmEngine.warmup
