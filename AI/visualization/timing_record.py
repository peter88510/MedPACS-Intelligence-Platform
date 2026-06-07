"""REALTIME run-level timing record（JSONL append-only）。

每次 REALTIME run 結束時 append 1 行 JSON 到 `output/timing/runs.jsonl`，
供 `tools/timing_report.py` 跨 run 聚合分析（變異來源 / 趨勢 / outlier / P95）。

設計重點：
  - append-only：不讀現有 JSONL，無 race / migration 成本
  - schema_version：未來 RealtimeTiming 命名再改時舊資料不壞
  - source_stem：不寫絕對路徑（醫療資料 indirect leak 防範）
  - 寫入時機：`_run_realtime` 全部計算結束後執行，loop 零干擾

Schema 版本對應（Patch 27A）：
  - 1.0：layers + metadata + loop_total_s 三層（per-stage 累計）
  - 1.1：新增 `per_frame_ms: List[float]` — per-frame loop wallclock array
         （含 skip 幀；frame 0 為 probe init，跳過不記）
         → 解鎖 P50/P90/P95/P99/max + 超出率桶統計
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "1.1"
DEFAULT_JSONL_PATH = Path("output/timing/runs.jsonl")


def _build_payload(timing) -> Dict[str, Dict[str, Any]]:
    """RealtimeTiming.LAYERS schema → nested {layer: {stage: {total_s, count, avg_ms}}}."""
    payload: Dict[str, Dict[str, Any]] = {}
    for layer, stages in timing.LAYERS.items():
        layer_payload: Dict[str, Any] = {}
        for stage in stages:
            n = timing.counts.get(stage, 0)
            if n == 0:
                continue
            tot = timing.totals.get(stage, 0.0)
            layer_payload[stage] = {
                "total_s": round(tot, 6),
                "count": int(n),
                "avg_ms": round(tot / n * 1000, 4),
            }
        if layer_payload:
            payload[layer] = layer_payload
    return payload


def record_run(
    timing,
    loop_total: float,
    metadata: Dict[str, Any],
    per_frame_ms: Optional[List[float]] = None,
    jsonl_path: Path = DEFAULT_JSONL_PATH,
) -> None:
    """Append 1 row JSON。timing 為 duck-typed RealtimeTiming（需 LAYERS / totals / counts）。

    Args:
        timing: RealtimeTiming（duck-typed）
        loop_total: loop wallclock 秒
        metadata: 至少含 source_stem / n_frames / fps / heavy_n / light_n / skip_n / config
        per_frame_ms: per-frame loop wallclock ms array（Patch 27A schema 1.1）；
                      None 或空 list 寫 [] — reader 端遇 [] 視為 schema 1.0 行為
        jsonl_path: 輸出 jsonl 路徑
    """
    row = {
        "schema_version": SCHEMA_VERSION,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "loop_total_s": round(loop_total, 6),
        "metadata": metadata,
        "layers": _build_payload(timing),
        "per_frame_ms": [round(t, 4) for t in (per_frame_ms or [])],
    }
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
