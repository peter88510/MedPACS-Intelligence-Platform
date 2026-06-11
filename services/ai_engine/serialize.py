"""把 EngineResult 序列化成 ai_results.result_json envelope（design §4）。

抽出 main.py 之外，讓 API handler 保持精簡、envelope 形狀貼著 engine 契約。
schema_version 固定為 1；新增 measurement type 時只在各 measurement 物件內加欄位，
不需 bump envelope（「新類型零 migration」特性，design §2/§4）。
"""
from typing import Optional, Tuple

from services.ai_engine.base import EngineResult, Measurement

SCHEMA_VERSION = 1

# 各 measurement type 的 headline 指標。excursion 與 sniff 都以垂直 excursion 為
# headline 數字；sniff 另在各 measurement 內帶 time_sec / velocity。thickness 不在
# 此產生（上游已 501 擋掉），列出僅為其 engine 將來落地時對齊。
_PRIMARY_LABEL = "excursion_cm"
_PRIMARY_UNIT = "cm"


def _measurement_dict(m: Measurement) -> dict:
    return {
        "batch_index": m.batch_index,
        "excursion_cm": m.excursion_cm,
        "excursion_pixel": m.excursion_pixel,
        "time_pixel": m.time_pixel,
        "time_sec": m.time_sec,
        "velocity": m.velocity,
        "crest": m.crest,
        "trough": m.trough,
    }


def primary_value_unit(result: EngineResult) -> Tuple[Optional[float], Optional[str]]:
    """供 ai_results.primary_* 欄位用的 denormalized headline (value, unit)。

    沒偵測到任何結果時回 (None, None)，讓欄位保持 NULL。
    """
    p = result.primary
    if p is None or p.excursion_cm is None:
        return None, None
    return p.excursion_cm, _PRIMARY_UNIT


def to_result_json(result: EngineResult) -> dict:
    """ai_results.result_json（JSONB）的完整結構化 payload。"""
    value, unit = primary_value_unit(result)
    return {
        "schema_version": SCHEMA_VERSION,
        "measurement_type": result.measurement_type.value,
        "pipeline_mode": result.pipeline_mode,
        "model_name": result.model_name,
        "model_version": result.model_version,
        "measurements": [_measurement_dict(m) for m in result.measurements],
        "primary": {"label": _PRIMARY_LABEL, "value": value, "unit": unit},
    }
