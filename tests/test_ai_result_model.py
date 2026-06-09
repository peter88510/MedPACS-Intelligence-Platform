"""
tests/test_ai_result_model.py
=============================
AIResult ORM model 層測試（Phase 3 task #10）。

scope：
- 純 ORM-level，不觸發 FastAPI endpoint
- 用 conftest.py 的 in-memory SQLite + `db` fixture
- 不測 AI 推論邏輯（task #11/#12 範圍、且工程師親自接演算法）
"""
from datetime import datetime

from models import AIResult, Instance, Patient, Study


def _seed_instance(db):
    """建一個最小的 Patient -> Study -> Instance chain，回傳 instance.id。"""
    patient = Patient(patient_id="TEST_PATIENT_AI")
    db.add(patient)
    db.commit()
    study = Study(
        study_instance_uid="1.2.3.AI",
        patient_id="TEST_PATIENT_AI",
        modality="US",
    )
    db.add(study)
    db.commit()
    instance = Instance(
        file_path="TEST_PATIENT_AI/1.2.3.AI/dummy.dcm",
        study_instance_uid="1.2.3.AI",
        sop_instance_uid="1.2.3.AI.SOP",
    )
    db.add(instance)
    db.commit()
    return instance.id


def test_create_ai_result_with_all_fields(db):
    instance_id = _seed_instance(db)
    result = AIResult(
        instance_id=instance_id,
        model_name="unet_breast_v1",
        model_version="0.1.0",
        status="completed",
        mask_path="TEST_PATIENT_AI/1.2.3.AI/ai/1_unet_breast_v1_mask.png",
        confidence=0.87,
        error_message=None,
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    assert result.id is not None
    assert result.instance_id == instance_id
    assert result.model_name == "unet_breast_v1"
    assert result.model_version == "0.1.0"
    assert result.status == "completed"
    assert result.mask_path.endswith("_mask.png")
    assert result.confidence == 0.87
    assert result.error_message is None
    assert isinstance(result.created_at, datetime)


def test_create_ai_result_with_nullable_fields_omitted(db):
    """status='queued' 階段尚無 mask/confidence/error — 全可為 None。"""
    instance_id = _seed_instance(db)
    result = AIResult(
        instance_id=instance_id,
        model_name="unet_breast_v1",
        model_version="0.1.0",
        status="queued",
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    assert result.mask_path is None
    assert result.confidence is None
    assert result.error_message is None


def test_ai_result_relationship_with_instance(db):
    """Instance.ai_results back-relationship 雙向可走。"""
    instance_id = _seed_instance(db)
    db.add_all([
        AIResult(instance_id=instance_id, model_name="m", model_version="1", status="completed"),
        AIResult(instance_id=instance_id, model_name="m", model_version="2", status="failed",
                 error_message="cuda oom"),
    ])
    db.commit()

    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    assert len(instance.ai_results) == 2
    versions = {r.model_version for r in instance.ai_results}
    assert versions == {"1", "2"}

    failed = [r for r in instance.ai_results if r.status == "failed"][0]
    assert failed.instance.id == instance_id
    assert failed.error_message == "cuda oom"


# --- Measurement-result fields (added 2026-06-09, design §3.1/§4) ---

def test_measurement_type_defaults_to_excursion(db):
    """server_default='excursion' applies when measurement_type omitted."""
    instance_id = _seed_instance(db)
    result = AIResult(
        instance_id=instance_id,
        model_name="diaphragm_excursion",
        model_version="6139799",
        status="completed",
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    assert result.measurement_type == "excursion"


def test_result_json_round_trips_as_dict(db):
    """JSONB/JSON variant must store and return a nested dict unchanged."""
    instance_id = _seed_instance(db)
    envelope = {
        "schema_version": 1,
        "measurement_type": "excursion",
        "pipeline_mode": "global_window",
        "model_name": "diaphragm_excursion",
        "model_version": "6139799",
        "measurements": [
            {
                "batch_index": 0,
                "excursion_cm": 2.31,
                "excursion_pixel": 120,
                "time_pixel": 45,
                "time_sec": None,
                "velocity": None,
                "crest": [320, 110],
                "trough": [365, 230],
            }
        ],
        "primary": {"label": "excursion_cm", "value": 2.31, "unit": "cm"},
    }
    result = AIResult(
        instance_id=instance_id,
        model_name="diaphragm_excursion",
        model_version="6139799",
        status="completed",
        measurement_type="excursion",
        result_json=envelope,
        primary_value=2.31,
        primary_unit="cm",
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    assert result.result_json == envelope
    assert result.result_json["measurements"][0]["excursion_cm"] == 2.31
    assert result.primary_value == 2.31
    assert result.primary_unit == "cm"


def test_result_json_nullable_when_queued(db):
    """status='queued' has no result yet — measurement fields are nullable."""
    instance_id = _seed_instance(db)
    result = AIResult(
        instance_id=instance_id,
        model_name="diaphragm_excursion",
        model_version="6139799",
        status="queued",
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    assert result.result_json is None
    assert result.primary_value is None
    assert result.primary_unit is None
