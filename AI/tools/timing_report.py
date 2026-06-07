"""跨 run REALTIME timing aggregation → markdown final report。

Usage:
    python -m tools.timing_report
    python -m tools.timing_report --jsonl output/timing/runs.jsonl --out output/timing/report.md
    python -m tools.timing_report --dedup last    # 同 source_stem 只留最新

讀 `output/timing/runs.jsonl`（visualization.timing_record 寫出）跨多 run 聚合：
  §1 Run inventory             — N runs / time range / source 分佈 / config 一致性 / dedup 狀態
  §2 總時間 ranking + outlier  — loop_total 排序、>2σ 標記
  §3 Layer per_frame breakdown — 各 stage avg ± std + 占比
  §4 Layer heavy internal      — % heavy
  §5 Layer roi / detect drill  — % roi
  §6 Layer light internal      — % light
  §7 變異來源 top-N            — 按 CV (σ/μ) 排序，類比 realtime_speed_analysis.md §6
  §8 heavy/light cadence       — heavy_n / light_n / skip_n 比例 + per-run 差異
  §9 跨 run 趨勢               — 按 timestamp 排序看是否退化
  §10 觀察與建議

去重 mode（`--dedup`）：寫入端 append-only 保留 event log；讀取端可選去重：
  - `all`   ：（預設）全收，同 source 多次當獨立 sample（量同源重跑變異用）
  - `last`  ：同 `source_stem` 只留最新 timestamp（debug 期間誤觸多次時用）
  - `first` ：同 `source_stem` 只留最早 timestamp

設計：純 stdlib（json + statistics + argparse），無 pandas 依賴；< 5 runs 仍可跑，
但 §7 變異 / §9 趨勢需 ≥ 5 runs 才標註為「可信」。
"""
import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_JSONL = Path("output/timing/runs.jsonl")
DEFAULT_OUT = Path("output/timing/report.md")
TRUST_THRESHOLD = 5   # < 5 runs 時 §7 / §9 標 (低信心)
DEFAULT_TARGET_FPS = 15.0   # 超音波輸入 FPS，每幀預算 = 1000 / FPS ms


def section_legend() -> str:
    """報告頂部名詞釋義（Patch 26B）— 一次定義跨章節欄位語意。"""
    return (
        "## 名詞釋義（Legend）\n\n"
        "| 欄位 | 意義 |\n"
        "|---|---|\n"
        "| 樣本數 | 本報告納入的 run 總數 |\n"
        "| 有效樣本 | 該 stage 實際被觸發的 run 數（`<` 樣本數 → 條件式 stage）|\n"
        "| 執行次數 μ | 該 stage 在一個 run 內被呼叫次數 — 跨 run 平均（μ）|\n"
        "| 總耗時 μ (s) | 該 stage 在一個 run 內累計總秒數 — 跨 run 平均 |\n"
        "| 平均耗時 μ (ms) | 該 stage 單次呼叫耗時（per-run = total_s / count × 1000）— 跨 run 平均 |\n"
        "| 標準差 σ | 跨 run 平均耗時的母體標準差（pstdev）|\n"
        "| 變異係數 CV% | σ / μ × 100，反映跨 run 穩定度 |\n"
        "| 占層比例 % | 該 stage 總耗時 / 該 layer rollup 總耗時 × 100 — 每 run 算後跨 run 平均 |\n"
        "| 每幀耗時 ms | 該 stage 對「每幀 wallclock」的攤銷貢獻 = total_s × 1000 / n_frames |\n"
        "| 上層鏈 | drill-down 路徑（看到同 chain 多階共現 = 同源變異）|\n"
        "| ⚠️ | 條件式 stage（部分 run 未觸發；CV / 平均僅基於有效樣本）|\n"
        "\n"
        "**μ / σ 命名約定**：μ(X) = 跨 run 對 X 取平均；σ(X) = 跨 run 對 X 取標準差。"
        "「per-call」= 單次呼叫平均（per-run 內部 = total_s / count）；"
        "「per-run」= 該 run 的總值；「per-frame」= 攤銷至每幀（÷ n_frames）。\n\n---\n"
    )


def load_runs(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"jsonl 不存在：{path}")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def dedup_runs(
    runs: List[Dict[str, Any]], mode: str
) -> Tuple[List[Dict[str, Any]], int]:
    """同 `source_stem` 依 mode 去重；回傳 (kept_runs, dropped_count)。

    - all   ：全收（pass-through）
    - last  ：每 source_stem 留 timestamp 最大者
    - first ：每 source_stem 留 timestamp 最小者
    """
    if mode == "all":
        return runs, 0
    if mode not in ("last", "first"):
        raise ValueError(f"未知 dedup mode：{mode}（可選 all / last / first）")

    kept: Dict[str, Dict[str, Any]] = {}
    for r in runs:
        key = r.get("metadata", {}).get("source_stem", "?")
        ts = r.get("timestamp", "")
        if key not in kept:
            kept[key] = r
            continue
        prev_ts = kept[key].get("timestamp", "")
        if mode == "last" and ts > prev_ts:
            kept[key] = r
        elif mode == "first" and ts < prev_ts:
            kept[key] = r
    return list(kept.values()), len(runs) - len(kept)


def _stats(values: List[float]) -> Tuple[float, float, float]:
    """回傳 (mean, std, cv%)；cv = std/mean*100。N=1 時 std=0、cv=0。"""
    if not values:
        return 0.0, 0.0, 0.0
    mean = statistics.fmean(values)
    std = statistics.pstdev(values) if len(values) > 1 else 0.0
    cv = (std / mean * 100) if mean else 0.0
    return mean, std, cv


def _collect_stage_values(
    runs: List[Dict[str, Any]], layer: str, stage: str, field: str = "avg_ms"
) -> List[float]:
    """跨 run 拉同 (layer, stage) 的 field 值；缺值跳過。"""
    return [
        r["layers"][layer][stage][field]
        for r in runs
        if layer in r.get("layers", {}) and stage in r["layers"][layer]
    ]


def _layer_denom_per_run(run: Dict[str, Any], layer: str) -> float:
    """% within layer 的分母 — 該 layer 的 rollup total（per-run）。"""
    if layer == "per_frame":
        return run.get("loop_total_s", 0.0)
    layers = run.get("layers", {})
    if layer == "heavy":
        return layers.get("per_frame", {}).get("heavy", {}).get("total_s", 0.0)
    if layer == "roi":
        return layers.get("heavy", {}).get("roi", {}).get("total_s", 0.0)
    if layer == "detect":
        # detect 為 roi 子層；分母對齊 roi 維持 drill-down 一致
        return layers.get("heavy", {}).get("roi", {}).get("total_s", 0.0)
    if layer == "light":
        return layers.get("per_frame", {}).get("light", {}).get("total_s", 0.0)
    return 0.0


# Patch 26A：parent chain — 同源變異辨識（§7 variance 用）
# detect 為「兩 pass 累計」層，parent 同時是 detect_p1 / detect_p2 兩個 wrapper
_PARENT_CHAIN = {
    "per_frame": "",
    "heavy":     "per_frame",
    "roi":       "per_frame.heavy",
    "detect":    "per_frame.heavy.roi.{detect_p1|detect_p2}",
    "light":     "per_frame",
}


def _stage_chain(layer: str, stage: str) -> str:
    """組 stage 完整 drill-down 鏈，便於識別同源變異。"""
    parent = _PARENT_CHAIN.get(layer, "")
    if parent:
        return f"{parent}.{layer}.{stage}"
    return f"{layer}.{stage}"


def _all_layer_stages(runs: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """聯集所有 run 出現過的 (layer, stage)，保 LAYERS 原順序。"""
    order: Dict[str, List[str]] = defaultdict(list)
    seen: Dict[str, set] = defaultdict(set)
    for r in runs:
        for layer, stages in r.get("layers", {}).items():
            for stage in stages:
                if stage not in seen[layer]:
                    order[layer].append(stage)
                    seen[layer].add(stage)
    return dict(order)


def section_realtime_assessment(
    runs: List[Dict[str, Any]], target_fps: float = DEFAULT_TARGET_FPS
) -> str:
    """§1 即時性評估：跨 run 每幀耗時 vs Budget（1000/FPS ms）→ PASS/FAIL。

    每幀耗時 = loop_total_s × 1000 / n_frames（per-run），跨 run 看 μ / 最壞 / Margin。

    註：真 per-frame P95 需要 per-frame timing schema（目前只有 per-stage 累計）；
    本節用「最壞 run 的平均每幀」作 run-level 壞情況指標。
    """
    budget_ms = 1000.0 / target_fps if target_fps > 0 else 0.0
    per_frame_values = []
    for r in runs:
        nf = r["metadata"].get("n_frames", 0)
        if nf > 0:
            per_frame_values.append(r.get("loop_total_s", 0.0) * 1000 / nf)
    if not per_frame_values:
        return ("## §1 即時性評估（Realtime Assessment）\n\n"
                "_無有效 run（n_frames=0）_\n")

    mean_ms = statistics.fmean(per_frame_values)
    worst_ms = max(per_frame_values)
    usage_pct = (mean_ms / budget_ms * 100) if budget_ms else 0.0
    worst_usage_pct = (worst_ms / budget_ms * 100) if budget_ms else 0.0
    margin_ms = budget_ms - mean_ms
    worst_margin_ms = budget_ms - worst_ms

    avg_status = "✅ PASS" if mean_ms <= budget_ms else "❌ FAIL"
    worst_status = "✅ PASS" if worst_ms <= budget_ms else "❌ FAIL"

    if mean_ms > budget_ms:
        excess_ms = mean_ms - budget_ms
        excess_pct = excess_ms / budget_ms * 100
        conclusion = (f"❌ **未達 {target_fps} FPS 即時性**：平均每幀超支 "
                      f"{excess_ms:.1f} ms（+{excess_pct:.1f}%）；需減 "
                      f"{excess_ms:.1f} ms/frame")
    elif worst_ms > budget_ms:
        conclusion = (f"⚠️ **臨界**：平均達標但最壞 run 每幀超支 "
                      f"{worst_ms - budget_ms:.1f} ms — 部分情境會掉幀")
    else:
        conclusion = (f"✅ **達 {target_fps} FPS 即時性**：Margin "
                      f"+{margin_ms:.1f} ms，跨 run 都有餘裕")

    lines = [f"## §1 即時性評估（Realtime Assessment）\n",
             f"目標：**{target_fps} FPS**，每幀預算 = 1000 / {target_fps} = "
             f"**{budget_ms:.1f} ms/frame**\n",
             "| 指標 | 值 | 狀態 |",
             "|---|---|---|",
             f"| 每幀預算 (Frame Budget) | {budget_ms:.1f} ms | — |",
             f"| 平均每幀耗時（跨 run μ） | **{mean_ms:.1f} ms** | {avg_status} |",
             f"| 最壞 run 每幀耗時 | {worst_ms:.1f} ms | {worst_status} |",
             f"| Budget 使用率（平均）| {usage_pct:.1f}% | "
             + ("超出 ❌" if usage_pct > 100 else "可接受 ✓") + " |",
             f"| Budget 使用率（最壞）| {worst_usage_pct:.1f}% | "
             + ("超出 ❌" if worst_usage_pct > 100 else "可接受 ✓") + " |",
             f"| Margin（平均）| {margin_ms:+.1f} ms | "
             + ("不足" if margin_ms < 0 else "充足") + " |",
             f"| Margin（最壞）| {worst_margin_ms:+.1f} ms | "
             + ("不足" if worst_margin_ms < 0 else "充足") + " |",
             f"| 達 {target_fps} FPS Status | **{avg_status.split()[1]}** | — |",
             "",
             f"**結論**：{conclusion}\n",
             "> 註：P95/P99 per-frame 需 per-frame timing schema（目前 jsonl 只存"
             " per-stage 累計）；「最壞 run」為跨 run avg 的最大值，反映 run-level "
             "壞情況而非單 frame 壞情況。\n",
             "---\n"]
    return "\n".join(lines)


# Patch 27C：假設情境（exclude stages）
def _excluded_total_per_run(run: Dict[str, Any], excluded: List[str]) -> float:
    """跨所有 layer 搜匹配 stage 名，加總 total_s。

    跨層匹配規則：stage 名相同視為同一個被排除目標。目前 LAYERS 設計無同名衝突，
    但若未來新增同名 sub-stage（如 heavy/light 都有 motion_curve）會被同時扣除 —
    這正是「假設該演算法步驟全部 → 0」的語意，符合預期。
    """
    total = 0.0
    for layer_stages in run.get("layers", {}).values():
        for stage_name, data in layer_stages.items():
            if stage_name in excluded:
                total += data.get("total_s", 0.0)
    return total


def _all_stage_names(runs: List[Dict[str, Any]]) -> set:
    """聯集所有 run / layer 出現過的 stage 名（CLI validate 用）。"""
    names = set()
    for r in runs:
        for ls in r.get("layers", {}).values():
            names.update(ls.keys())
    return names


def section_realtime_assessment_excluded(
    runs: List[Dict[str, Any]],
    target_fps: float,
    excluded: List[str],
) -> str:
    """§1.1 假設量化後 / 排除指定 stage 後的對照表。

    excluded 為空 → 回空字串（caller 不應該叫此函式）
    """
    if not excluded:
        return ""

    seen = _all_stage_names(runs)
    missing = [s for s in excluded if s not in seen]
    excluded_present = [s for s in excluded if s in seen]

    if not excluded_present:
        return (f"## §1.1 假設情境（exclude）\n\n"
                f"⚠️ 指定的 stage `{', '.join(excluded)}` 在資料中皆不存在 — "
                f"跳過假設情境。\n\n"
                f"可用 stage：`{', '.join(sorted(seen))}`\n\n---\n")

    budget_ms = 1000.0 / target_fps if target_fps > 0 else 0.0
    real_pf, adj_pf = [], []
    for r in runs:
        nf = r["metadata"].get("n_frames", 0)
        if nf <= 0:
            continue
        loop = r.get("loop_total_s", 0.0)
        exc = _excluded_total_per_run(r, excluded_present)
        real_pf.append(loop * 1000 / nf)
        adj_pf.append((loop - exc) * 1000 / nf)

    if not real_pf:
        return ""

    real_mean = statistics.fmean(real_pf)
    real_worst = max(real_pf)
    adj_mean = statistics.fmean(adj_pf)
    adj_worst = max(adj_pf)

    real_status_mean = "❌ FAIL" if real_mean > budget_ms else "✅ PASS"
    real_status_worst = "❌ FAIL" if real_worst > budget_ms else "✅ PASS"
    adj_status_mean = "❌ FAIL" if adj_mean > budget_ms else "✅ PASS"
    adj_status_worst = "❌ FAIL" if adj_worst > budget_ms else "✅ PASS"

    # 個別 stage 平均總耗時（佐證表）
    stage_stats = []
    loop_means = [r.get("loop_total_s", 0.0) for r in runs
                  if r["metadata"].get("n_frames", 0) > 0]
    loop_mean_s = statistics.fmean(loop_means) if loop_means else 0.0
    for s in excluded_present:
        totals = []
        for r in runs:
            for ls in r.get("layers", {}).values():
                if s in ls:
                    totals.append(ls[s].get("total_s", 0.0))
                    break
        if totals:
            t_mean = statistics.fmean(totals)
            pct = (t_mean / loop_mean_s * 100) if loop_mean_s else 0.0
            stage_stats.append((s, t_mean, pct))

    excluded_label = ", ".join(f"`{s}`" for s in excluded_present)
    lines = [f"## §1.1 假設情境：排除 stage {excluded_label}\n",
             "> ⚠️ **假設指定 stage 量化 / 移除後耗時 → 0**，重算每幀預算。",
             "> 為**樂觀上限**（實際量化後仍有 inference / memory copy overhead）；",
             "> 用於評估「撇除特定瓶頸後，演算法純成本能否達 budget」。\n",
             "| 指標 | 實測 | 假設排除後 | Δ |",
             "|---|---|---|---|"]
    lines.append(f"| 平均每幀耗時 | {real_mean:.1f} ms {real_status_mean} "
                 f"| **{adj_mean:.1f} ms** {adj_status_mean} "
                 f"| {adj_mean - real_mean:+.1f} ms |")
    lines.append(f"| 最壞 run 每幀耗時 | {real_worst:.1f} ms {real_status_worst} "
                 f"| **{adj_worst:.1f} ms** {adj_status_worst} "
                 f"| {adj_worst - real_worst:+.1f} ms |")
    lines.append(f"| Budget 使用率（平均）| {real_mean/budget_ms*100:.1f}% "
                 f"| **{adj_mean/budget_ms*100:.1f}%** "
                 f"| {(adj_mean - real_mean)/budget_ms*100:+.1f}pp |")
    lines.append(f"| Margin（平均）| {budget_ms - real_mean:+.1f} ms "
                 f"| **{budget_ms - adj_mean:+.1f} ms** "
                 f"| {real_mean - adj_mean:+.1f} ms |")
    lines.append(f"| 達 {target_fps} FPS Status | "
                 f"{real_status_mean.split()[1]} | "
                 f"**{adj_status_mean.split()[1]}** | — |")
    lines.append("")

    if stage_stats:
        lines.append("**被排除 stage 平均耗時**：\n")
        lines.append("| Stage | 平均總耗時 (s/run) | 占 loop μ % |")
        lines.append("|---|---|---|")
        for s, t, pct in stage_stats:
            lines.append(f"| `{s}` | {t:.3f} | {pct:.1f}% |")
        lines.append("")

    # 結論
    if adj_mean <= budget_ms < real_mean:
        conclusion = (f"✅ **撇除指定 stage 後可達 {target_fps} FPS**："
                      f"演算法純成本 {adj_mean:.1f} ms/frame，"
                      f"Margin +{budget_ms - adj_mean:.1f} ms — "
                      f"被排除 stage 是達標關鍵瓶頸")
    elif adj_mean > budget_ms:
        excess = adj_mean - budget_ms
        conclusion = (f"❌ **即使排除指定 stage 仍未達 {target_fps} FPS**："
                      f"演算法純成本 {adj_mean:.1f} ms/frame，"
                      f"仍超 budget {excess:.1f} ms — "
                      f"需從其他 stage 找優化空間")
    else:
        conclusion = (f"✅ 實測已達 {target_fps} FPS；排除指定 stage 後 margin "
                      f"從 {budget_ms - real_mean:+.1f} ms 擴大到 "
                      f"{budget_ms - adj_mean:+.1f} ms")
    lines.append(f"**結論**：{conclusion}\n")

    if missing:
        lines.append(f"> ⚠️ 以下 stage 在資料中不存在，已忽略：`{', '.join(missing)}`")
        lines.append(f"> 可用 stage：`{', '.join(sorted(seen))}`\n")

    lines.append("---\n")
    return "\n".join(lines)


# Patch 27B：per-frame 分佈分析（schema 1.1）
def _collect_per_frame_pool(
    runs: List[Dict[str, Any]],
) -> Tuple[List[float], int, int]:
    """Pool 所有 schema 1.1 run 的 per_frame_ms array；回傳 (pool, n_1.1_runs, n_1.0_runs)。"""
    pool: List[float] = []
    n_v11 = 0
    n_v10 = 0
    for r in runs:
        pfm = r.get("per_frame_ms")
        if pfm:
            pool.extend(pfm)
            n_v11 += 1
        else:
            n_v10 += 1
    return pool, n_v11, n_v10


def _quantiles_pct(values: List[float], qs: List[float]) -> Dict[float, float]:
    """算 quantile（method='inclusive'，標準 percentile interpolation）。"""
    if not values:
        return {q: 0.0 for q in qs}
    sorted_v = sorted(values)
    n = len(sorted_v)
    out = {}
    for q in qs:
        # inclusive method: rank = q × (n-1)
        rank = q * (n - 1)
        lo = int(rank)
        hi = min(lo + 1, n - 1)
        frac = rank - lo
        out[q] = sorted_v[lo] * (1 - frac) + sorted_v[hi] * frac
    return out


# 累計桶定義（27B）：每個區間是「超出 budget X% 以上」的累計幀數
_OVERSHOOT_BUCKETS = [
    ("≤ Budget",    -1,   "✓ 多數達標"),    # 特殊處理：≤ budget
    ("> Budget",     0,   "—"),
    ("> 10% over",   10,  "—"),
    ("> 20% over",   20,  "—"),
    ("> 50% over",   50,  "—"),
    ("> 100% over",  100, "嚴重（雙倍預算）"),
    ("> 500% over",  500, "極端離群（cold start 級）"),
]


def _overshoot_buckets(
    values: List[float], budget_ms: float
) -> List[Tuple[str, float, int, float, str]]:
    """回傳 [(label, threshold_ms, count, pct, status_note)]；count 為累計。"""
    n = len(values)
    if n == 0 or budget_ms <= 0:
        return []
    rows = []
    for label, pct_over, status in _OVERSHOOT_BUCKETS:
        if pct_over < 0:   # ≤ budget 特殊處理
            threshold = budget_ms
            count = sum(1 for v in values if v <= budget_ms)
        else:
            threshold = budget_ms * (1 + pct_over / 100)
            count = sum(1 for v in values if v > threshold)
        rows.append((label, threshold, count, count / n * 100, status))
    return rows


def section_per_frame_distribution(
    runs: List[Dict[str, Any]], target_fps: float
) -> str:
    """§1.2 每幀耗時分佈（schema 1.1 限定）— 分位數 + 累計桶 + per-run 摘要。"""
    pool, n_v11, n_v10 = _collect_per_frame_pool(runs)
    if not pool:
        if n_v10 > 0:
            return (f"## §1.2 每幀耗時分佈（Per-Frame Distribution）\n\n"
                    f"⚠️ 所有 {n_v10} 個 run 為 schema 1.0（無 `per_frame_ms`）— "
                    f"per-frame 統計不可用。\n"
                    f"跑 1 次新 REALTIME run（schema 1.1）後重生報表即可解鎖。\n\n---\n")
        return ""

    budget_ms = 1000.0 / target_fps if target_fps > 0 else 0.0
    n_frames = len(pool)
    mean = statistics.fmean(pool)
    q = _quantiles_pct(pool, [0.5, 0.9, 0.95, 0.99])
    max_v = max(pool)

    buckets = _overshoot_buckets(pool, budget_ms)

    lines = [f"## §1.2 每幀耗時分佈（Per-Frame Distribution）\n",
             f"> 來源：**{n_v11}** runs (schema 1.1) × per-frame 累計 = **{n_frames}** frames"
             + (f"；另 {n_v10} run 為 schema 1.0 未計入" if n_v10 else "")
             + f"\n> Budget = **{budget_ms:.1f} ms** ({target_fps} FPS)\n",
             "### 分位數（pooled 跨 run）\n",
             "| 平均 | P50 | P90 | P95 | P99 | Max |",
             "|---|---|---|---|---|---|",
             f"| {mean:.1f} ms | {q[0.5]:.1f} ms | {q[0.9]:.1f} ms "
             f"| **{q[0.95]:.1f} ms** | {q[0.99]:.1f} ms | {max_v:.1f} ms |\n"]

    # 桶統計
    lines.append("### 超出率累計桶\n")
    lines.append("_累計式：每行包含下一行（如「> Budget」含所有更嚴重區間）_\n")
    lines.append("| 區間 | 門檻 (ms) | 幀數 | % | 備註 |")
    lines.append("|---|---|---|---|---|")
    for label, threshold, count, pct, status in buckets:
        lines.append(f"| {label} | {threshold:.1f} | {count} | {pct:.1f}% | {status} |")
    lines.append("")

    # Per-run 摘要
    lines.append("### Per-run 摘要\n")
    lines.append("| 來源 | 幀數 | P50 | P95 | Max | > Budget % | > 100% over % |")
    lines.append("|---|---|---|---|---|---|---|")
    per_run_rows = []
    for r in runs:
        pfm = r.get("per_frame_ms")
        if not pfm:
            continue
        src = r["metadata"].get("source_stem", "?")
        nf = len(pfm)
        rq = _quantiles_pct(pfm, [0.5, 0.95])
        rmax = max(pfm)
        n_over = sum(1 for v in pfm if v > budget_ms)
        n_2x = sum(1 for v in pfm if v > budget_ms * 2)
        per_run_rows.append((src, nf, rq[0.5], rq[0.95], rmax,
                             n_over / nf * 100, n_2x / nf * 100))
    # 限制顯示（超過 20 runs 截斷）
    if len(per_run_rows) > 20:
        for src, nf, p50, p95, mx, over, x2 in per_run_rows[:10]:
            lines.append(f"| {src} | {nf} | {p50:.1f} | {p95:.1f} | {mx:.1f} "
                         f"| {over:.1f}% | {x2:.1f}% |")
        lines.append(f"| _...(中略 {len(per_run_rows) - 20} runs)..._ | | | | | | |")
        for src, nf, p50, p95, mx, over, x2 in per_run_rows[-10:]:
            lines.append(f"| {src} | {nf} | {p50:.1f} | {p95:.1f} | {mx:.1f} "
                         f"| {over:.1f}% | {x2:.1f}% |")
    else:
        for src, nf, p50, p95, mx, over, x2 in per_run_rows:
            lines.append(f"| {src} | {nf} | {p50:.1f} | {p95:.1f} | {mx:.1f} "
                         f"| {over:.1f}% | {x2:.1f}% |")
    lines.append("")

    # 解讀
    in_budget_pct = buckets[0][3] if buckets else 0.0
    over_2x_pct = next((p for lbl, _, _, p, _ in buckets if lbl == "> 100% over"), 0.0)
    over_500_pct = next((p for lbl, _, _, p, _ in buckets if lbl == "> 500% over"), 0.0)
    interp = []
    if in_budget_pct >= 80:
        interp.append(f"- ✅ **{in_budget_pct:.1f}% 達 budget** — 穩態大多數情境符合 {target_fps} FPS")
    elif in_budget_pct >= 50:
        interp.append(f"- ⚠️ **僅 {in_budget_pct:.1f}% 達 budget** — 穩態臨界")
    else:
        interp.append(f"- ❌ **{in_budget_pct:.1f}% 達 budget** — 多數情境未達標")
    if over_500_pct > 0:
        interp.append(f"- ⚠️ **{over_500_pct:.1f}% 極端離群（> 500%）** — "
                      "可能含 paddle cold start / model load 等首幀效應")
    if over_2x_pct > 1.0:
        interp.append(f"- 嚴重超支（> 100%）占 {over_2x_pct:.1f}% — "
                      "非偶發，需檢視 heavy frame 路徑")
    lines.append("**解讀**：")
    lines.extend(interp)
    lines.append("")
    lines.append("> 註：第一幀 paddle cold start / model load 通常爆量，"
                 "若要看穩態建議跑 `--warmup-skip N` 排除首 N 幀（27D 候選）。")
    lines.append("\n---\n")
    return "\n".join(lines)


# Patch 27D'：慢幀來源歸因（統計推論，schema 1.1）
# 分類門檻：以 heavy_μ 為核心做相對門檻；100ms 為 light 異常上界（固定）
_HEAVY_LOW_RATIO = 0.7       # heavy_μ × 0.7：heavy 正常下界
_HEAVY_HIGH_RATIO = 1.3      # heavy_μ × 1.3：heavy 正常上界
_HEAVY_SLOW_RATIO = 3.0      # heavy_μ × 3.0：heavy 慢上界
_LIGHT_ANOMALY_MAX = 100.0   # ms（light_μ 通常 20ms，> 100ms 視為異常）


def section_slow_frame_attribution(
    runs: List[Dict[str, Any]], target_fps: float
) -> str:
    """§1.2.1 慢幀來源歸因 — 用 Layer μ ± σ 統計推論 > Budget 幀主因。

    限制：runs.jsonl 目前無 per-frame per-stage breakdown；本節為統計推論，
    非每幀真值。`frame_ms ≈ heavy_μ × 0.7~1.3` → 推測 heavy 路徑。
    """
    pool, n_v11, _ = _collect_per_frame_pool(runs)
    if not pool:
        return ""

    budget_ms = 1000.0 / target_fps if target_fps > 0 else 0.0
    if budget_ms <= 0:
        return ""

    slow_pool = [v for v in pool if v > budget_ms]
    if not slow_pool:
        return ("## §1.2.1 慢幀來源歸因（Slow Frame Attribution）\n\n"
                "✅ 無 > Budget 幀，無需歸因分析。\n\n---\n")

    # 取 Layer per_frame heavy / light μ 當基準
    heavy_avgs = _collect_stage_values(runs, "per_frame", "heavy", "avg_ms")
    light_avgs = _collect_stage_values(runs, "per_frame", "light", "avg_ms")
    if not heavy_avgs or not light_avgs:
        return ("## §1.2.1 慢幀來源歸因（Slow Frame Attribution）\n\n"
                "⚠️ Layer per_frame heavy / light 資料缺失，無法推論。\n\n---\n")

    heavy_mu = statistics.fmean(heavy_avgs)
    heavy_sigma = statistics.pstdev(heavy_avgs) if len(heavy_avgs) > 1 else 0.0
    light_mu = statistics.fmean(light_avgs)

    seg_avgs = _collect_stage_values(runs, "heavy", "seg_predict", "avg_ms")
    seg_mu = statistics.fmean(seg_avgs) if seg_avgs else 0.0

    # 計算門檻
    heavy_normal_low = heavy_mu * _HEAVY_LOW_RATIO
    heavy_normal_high = heavy_mu * _HEAVY_HIGH_RATIO
    heavy_slow_high = heavy_mu * _HEAVY_SLOW_RATIO

    seg_reason = (f"heavy 典型（seg_predict {seg_mu:.0f} ms 主導）"
                  if seg_mu > 0 else "heavy 典型路徑")

    bands = [
        ("Light 異常", budget_ms, _LIGHT_ANOMALY_MAX,
         "light 偶發 (motion_curve / blur / GC spike)"),
        ("Heavy 邊緣", _LIGHT_ANOMALY_MAX, heavy_normal_low,
         "heavy 加速路徑（24A skip pass2 / 25A short-circuit 生效）"),
        ("Heavy 正常", heavy_normal_low, heavy_normal_high, seg_reason),
        ("Heavy 慢", heavy_normal_high, heavy_slow_high,
         "heavy + jitter (paddle inference 變慢 / GC / IO)"),
        ("極端", heavy_slow_high, float('inf'),
         "cold start / model load 首幀"),
    ]

    n_slow = len(slow_pool)
    band_counts = {}
    band_rows = []
    for label, lo, hi, reason in bands:
        if hi == float('inf'):
            count = sum(1 for v in slow_pool if v > lo)
            range_str = f"> {lo:.0f}"
        else:
            count = sum(1 for v in slow_pool if lo < v <= hi)
            range_str = f"{lo:.0f}-{hi:.0f}"
        pct = count / n_slow * 100
        band_counts[label] = pct
        band_rows.append((label, range_str, count, pct, reason))

    lines = [f"## §1.2.1 慢幀來源歸因（Slow Frame Attribution）\n",
             f"> 跨 run pool：**{n_slow} frames > Budget**（占全部 "
             f"{len(pool)} frames 的 {n_slow / len(pool) * 100:.1f}%）"
             "；依時間帶 + Layer μ 推論主因",
             "> ⚠️ **統計推論**，非精確（per-frame per-stage 真值需 schema 1.2 升級）\n",
             "**參考基準**（取自 §3-§4 Layer 統計）：\n",
             f"- heavy μ = **{heavy_mu:.0f} ms** (σ = {heavy_sigma:.1f})"
             f"；heavy ±2σ = {heavy_mu - 2*heavy_sigma:.0f}-{heavy_mu + 2*heavy_sigma:.0f} ms"]
    lines.append(f"- light μ = **{light_mu:.0f} ms**")
    if seg_mu > 0:
        lines.append(f"- seg_predict μ = **{seg_mu:.0f} ms**"
                     f"（占 heavy μ 約 {seg_mu / heavy_mu * 100:.0f}%）")
    lines.append("")
    lines.append("**門檻**：heavy 正常區 = heavy_μ × "
                 f"[{_HEAVY_LOW_RATIO}, {_HEAVY_HIGH_RATIO}]；"
                 f"heavy 慢上界 = heavy_μ × {_HEAVY_SLOW_RATIO}；"
                 f"light 異常上界 = {_LIGHT_ANOMALY_MAX:.0f} ms\n")
    lines.append("| 歸因類別 | 時間範圍 (ms) | 幀數 | % of slow | 推測主因 |")
    lines.append("|---|---|---|---|---|")
    for label, range_str, count, pct, reason in band_rows:
        lines.append(f"| **{label}** | {range_str} | {count} | "
                     f"{pct:.1f}% | {reason} |")
    lines.append("")

    # 條件式結論
    interp = ["**結論**：\n"]
    heavy_normal_pct = band_counts.get("Heavy 正常", 0.0)
    heavy_slow_pct = band_counts.get("Heavy 慢", 0.0)
    heavy_edge_pct = band_counts.get("Heavy 邊緣", 0.0)
    light_pct = band_counts.get("Light 異常", 0.0)
    extreme_pct = band_counts.get("極端", 0.0)
    heavy_total_pct = heavy_edge_pct + heavy_normal_pct + heavy_slow_pct

    if heavy_total_pct > 70:
        interp.append(f"- **Heavy 路徑為主流瓶頸**（{heavy_total_pct:.1f}%）"
                      "→ 優化 heavy 是達標關鍵")
    if heavy_normal_pct + heavy_slow_pct > 50:
        interp.append(f"- Heavy 正常 + Heavy 慢 占 "
                      f"{heavy_normal_pct + heavy_slow_pct:.1f}% → "
                      "**seg_predict 量化**為單一最大效益優化（與 §1.1 一致）")
    if heavy_edge_pct > 10:
        interp.append(f"- Heavy 邊緣 占 {heavy_edge_pct:.1f}% → "
                      "**Patch 24A / 25A 短路在實機生效**（heavy 路徑部分加速）")
    if extreme_pct > 0:
        interp.append(f"- 極端離群 {extreme_pct:.1f}% → "
                      "**cold start / model load** 一次性影響（預熱機制可緩解）")
    if light_pct > 5:
        interp.append(f"- Light 異常 {light_pct:.1f}% → "
                      "**light 路徑偶有 spike**，建議監測 motion_curve / blur")
    elif light_pct > 0:
        interp.append(f"- Light 異常 {light_pct:.1f}% → 罕見，不需立即處理")

    lines.extend(interp)
    lines.append("")
    lines.append("> 註：本節為統計推論，假設「frame_ms 落 heavy_μ × "
                 f"[{_HEAVY_LOW_RATIO}, {_HEAVY_HIGH_RATIO}] → heavy 正常路徑」。"
                 "真精確（哪 stage 拖累哪幀）需 schema 1.2 升級。")
    lines.append("\n---\n")
    return "\n".join(lines)


def section_inventory(
    runs: List[Dict[str, Any]], dedup_mode: str, dropped: int, raw_n: int
) -> str:
    n = len(runs)
    timestamps = sorted(r.get("timestamp", "") for r in runs)
    sources = defaultdict(int)
    for r in runs:
        sources[r["metadata"].get("source_stem", "?")] += 1
    cfg_keys = set()
    cfg_diff: Dict[str, set] = defaultdict(set)
    for r in runs:
        cfg = r["metadata"].get("config", {})
        for k, v in cfg.items():
            cfg_keys.add(k)
            cfg_diff[k].add(str(v))

    dedup_line = (f"- **去重模式**：`{dedup_mode}`"
                  + (f"（原 {raw_n} runs → {n} runs，drop {dropped}）"
                     if dropped else "（無去重）"))
    lines = [f"## §2 Run 清單（Run Inventory）\n",
             f"- **總 run 數**：{n}",
             f"- **時間範圍**：{timestamps[0] if timestamps else 'n/a'} → "
             f"{timestamps[-1] if timestamps else 'n/a'}",
             f"- **資料來源分佈**：{dict(sources)}",
             dedup_line,
             ""]
    lines.append("**Config 一致性檢查**：\n")
    lines.append("| 參數 | 是否一致 | 出現值 |")
    lines.append("|---|---|---|")
    for k in sorted(cfg_keys):
        vals = sorted(cfg_diff[k])
        consistent = "✓" if len(vals) == 1 else "✗"
        lines.append(f"| `{k}` | {consistent} | {', '.join(vals)} |")
    lines.append("")
    return "\n".join(lines)


def section_total_ranking(runs: List[Dict[str, Any]]) -> str:
    """總時間 ranking + outlier 標記（> mean + 2*std 為 high outlier）。"""
    rows = [(r["metadata"].get("source_stem", "?"),
             r.get("timestamp", ""),
             r.get("loop_total_s", 0.0),
             r["metadata"].get("n_frames", 0),
             r["metadata"].get("heavy_n", 0),
             r["metadata"].get("light_n", 0),
             r["metadata"].get("skip_n", 0)) for r in runs]
    totals = [r[2] for r in rows]
    mean, std, cv = _stats(totals)

    lines = [f"## §3 系統總時間排名 + 異常標記\n",
             f"- 跨 run 平均 = **{mean:.2f}s**，標準差 σ = {std:.2f}s，CV = **{cv:.1f}%**",
             "- 異常標記規則：|x - mean| > 2σ → ⚠️",
             "",
             "| 來源 | 時間戳 | 總耗時 (s) | 幀數 | heavy | light | skip | 異常 |",
             "|---|---|---|---|---|---|---|---|"]
    rows_sorted = sorted(rows, key=lambda x: x[2], reverse=True)
    for src, ts, tot, nf, h, l, sk in rows_sorted:
        mark = " ⚠️" if std and abs(tot - mean) > 2 * std else ""
        lines.append(f"| {src} | {ts} | {tot:.2f} | {nf} | {h} | {l} | {sk} |{mark} |")
    lines.append("")
    return "\n".join(lines)


def _layer_breakdown_section(
    runs: List[Dict[str, Any]], layer: str, title: str, denom_note: str
) -> str:
    stages = _all_layer_stages(runs).get(layer, [])
    n_total = len(runs)
    lines = [f"## {title}\n",
             f"_分母：{denom_note}（每 run 計算後跨 run 取 μ）。"
             "`⚠️` 表示條件式 stage（部分 run 未觸發；統計僅基於有效樣本）。_\n",
             "| 階段 | 樣本數 | 有效樣本 | 執行次數 μ | 總耗時 μ (s) "
             "| 平均耗時 μ (ms) | 標準差 σ | CV% | 占層比例 μ % |",
             "|---|---|---|---|---|---|---|---|---|"]
    for stage in stages:
        avg_values = _collect_stage_values(runs, layer, stage, "avg_ms")
        tot_values = _collect_stage_values(runs, layer, stage, "total_s")
        cnt_values = _collect_stage_values(runs, layer, stage, "count")
        if not avg_values:
            continue
        n_eff = len(avg_values)
        cond_flag = " ⚠️" if n_eff < n_total else ""

        a_mean, a_std, a_cv = _stats(avg_values)
        t_mean, _, _ = _stats(tot_values)
        c_mean, _, _ = _stats(cnt_values)

        # 占層比例：每 run 各自算 (stage_total / layer_denom) 後跨 run μ
        pct_values: List[float] = []
        for r in runs:
            if (layer in r.get("layers", {})
                    and stage in r["layers"][layer]):
                denom = _layer_denom_per_run(r, layer)
                if denom > 0:
                    pct_values.append(
                        r["layers"][layer][stage]["total_s"] / denom * 100)
        pct_mean = statistics.fmean(pct_values) if pct_values else 0.0

        lines.append(
            f"| `{stage}`{cond_flag} | {n_total} | {n_eff} | {c_mean:.1f} "
            f"| {t_mean:.3f} | {a_mean:.2f} | {a_std:.2f} | {a_cv:.1f} "
            f"| {pct_mean:.1f} |"
        )
    lines.append("")
    return "\n".join(lines)


# Patch 26C：層級驗證
# 父子關係定義：每 layer 的「層總耗時（Parent）」與「子 stage 加總（Children）」對照
# detect 為特例：父為 roi.detect_p1 + roi.detect_p2 兩 wrapper 總和（兩 pass 累計）
_HIERARCHY_PARENTS = [
    ("per_frame", "loop_total"),
    ("heavy",     "per_frame.heavy"),
    ("roi",       "heavy.roi"),
    ("detect",    "roi.detect_p1 + roi.detect_p2"),
    ("light",     "per_frame.light"),
]


def _layer_parent_total_per_run(run: Dict[str, Any], layer: str) -> float:
    """取該 layer 的「父」總耗時（每 run）— 用於 hierarchy 一致性對照。"""
    layers = run.get("layers", {})
    if layer == "per_frame":
        return run.get("loop_total_s", 0.0)
    if layer == "heavy":
        return layers.get("per_frame", {}).get("heavy", {}).get("total_s", 0.0)
    if layer == "roi":
        return layers.get("heavy", {}).get("roi", {}).get("total_s", 0.0)
    if layer == "detect":
        # 兩 pass 累計：detect 內部 sub-stages 為 detect_p1 + detect_p2 累加
        p1 = layers.get("roi", {}).get("detect_p1", {}).get("total_s", 0.0)
        p2 = layers.get("roi", {}).get("detect_p2", {}).get("total_s", 0.0)
        return p1 + p2
    if layer == "light":
        return layers.get("per_frame", {}).get("light", {}).get("total_s", 0.0)
    return 0.0


def _layer_children_sum_per_run(run: Dict[str, Any], layer: str) -> float:
    """取該 layer 內所有 sub-stage 的 total_s 加總（每 run）。"""
    stages = run.get("layers", {}).get(layer, {})
    return sum(s.get("total_s", 0.0) for s in stages.values())


def section_hierarchy(runs: List[Dict[str, Any]]) -> str:
    """§4 Layer 層級驗證：Parent ≈ Children + Self；自頂向下對照看上下層加總是否合理。"""
    lines = [f"## §5 Layer 層級驗證（Hierarchy Validation）\n",
             "_每 layer：自身（Parent）總耗時 vs 子 stage 加總（Children），"
             "Self = Parent − Children = layer 本身的 wrapper/orchestration 額外開銷。_\n",
             "_一致性 = Children / Parent × 100（越接近 100% 表示 sub-stages 涵蓋越完整）。_\n",
             "| Layer | Parent 來源 | Parent μ (s) | Children μ (s) | Self μ (s) | 一致性 % |",
             "|---|---|---|---|---|---|"]
    for layer, parent_label in _HIERARCHY_PARENTS:
        parent_vals = [_layer_parent_total_per_run(r, layer) for r in runs]
        children_vals = [_layer_children_sum_per_run(r, layer) for r in runs]
        if not parent_vals:
            continue
        p_mean = statistics.fmean(parent_vals)
        c_mean = statistics.fmean(children_vals)
        self_mean = p_mean - c_mean
        consistency = (c_mean / p_mean * 100) if p_mean else 0.0
        flag = ""
        if consistency < 90 and p_mean > 0:
            flag = " ⚠️"
        elif consistency > 105:
            flag = " ❗"  # children 超過 parent 罕見（記錄重疊或 timing 錯誤）
        lines.append(
            f"| {layer}{flag} | `{parent_label}` | {p_mean:.3f} "
            f"| {c_mean:.3f} | {self_mean:+.3f} | {consistency:.1f} |"
        )

    lines.append("")
    lines.append("**符號**：⚠️ = 一致性 < 90%（子 stage 漏記範圍大）；"
                 "❗ = > 105%（可能記錄重疊或 timer 衝突）。")
    lines.append("")
    return "\n".join(lines)


def section_variance_sources(runs: List[Dict[str, Any]]) -> str:
    """跨 run 變異 top-N（按 avg_ms 的 CV 排序）。

    Patch 26A：
    - N eff < 2 直接排除（單樣本 CV 永遠 0，無變異意義）
    - 加 parent chain 欄識別同源變異（heavy.roi / roi.detect_p1 / detect.curve_fit
      若同時上榜代表是 *一條鏈* 變異，不是三個獨立熱點）
    - 條件式 stage（N eff < N runs）標 ⚠️ 提醒 CV 基於 subset
    """
    layer_stages = _all_layer_stages(runs)
    n_total = len(runs)
    rows = []
    for layer, stages in layer_stages.items():
        for stage in stages:
            vals = _collect_stage_values(runs, layer, stage, "avg_ms")
            if len(vals) < 2:
                continue
            m, s, cv = _stats(vals)
            chain = _stage_chain(layer, stage)
            rows.append((layer, stage, m, s, cv, len(vals), chain))

    rows.sort(key=lambda x: x[4], reverse=True)

    trust_note = ("✓ 樣本數 ≥ 5，變異具參考性"
                  if n_total >= TRUST_THRESHOLD
                  else f"⚠️ 樣本數 < {TRUST_THRESHOLD}，CV 數字僅供觀察")
    lines = [f"## §9 變異來源 Top-N（按 CV 排序）\n",
             f"_{trust_note}。同 chain 上下層共現 = 同源變異，不算多個熱點。_\n",
             "| 排名 | Layer | 階段 | 平均耗時 μ (ms) | 標準差 σ | CV% | 有效樣本 | 上層鏈 |",
             "|---|---|---|---|---|---|---|---|"]
    for rank, (layer, stage, m, s, cv, n_eff, chain) in enumerate(rows[:15], 1):
        cond_flag = " ⚠️" if n_eff < n_total else ""
        lines.append(f"| {rank} | {layer} | `{stage}`{cond_flag} | {m:.2f} | "
                     f"{s:.2f} | **{cv:.1f}** | {n_eff}/{n_total} | `{chain}` |")
    lines.append("")
    return "\n".join(lines)


def section_cadence(runs: List[Dict[str, Any]]) -> str:
    rows = []
    for r in runs:
        md = r["metadata"]
        nf = md.get("n_frames", 0)
        h = md.get("heavy_n", 0)
        l = md.get("light_n", 0)
        sk = md.get("skip_n", 0)
        ingested = h + l
        rows.append((md.get("source_stem", "?"), nf, h, l, sk, ingested))

    h_ratios = [(h / ing * 100) for _, _, h, _, _, ing in rows if ing]
    l_ratios = [(l / ing * 100) for _, _, _, l, _, ing in rows if ing]
    sk_ratios = [(sk / nf * 100) for _, nf, _, _, sk, _ in rows if nf]
    h_m, h_s, h_cv = _stats(h_ratios)
    l_m, l_s, l_cv = _stats(l_ratios)
    sk_m, sk_s, sk_cv = _stats(sk_ratios)

    lines = [f"## §10 heavy / light / skip 節奏（Cadence）\n",
             "**跨 run 平均比例**：",
             f"- heavy / ingested = **{h_m:.1f}%** ± {h_s:.1f} (CV {h_cv:.1f}%)",
             f"- light / ingested = **{l_m:.1f}%** ± {l_s:.1f} (CV {l_cv:.1f}%)",
             f"- skip / total    = **{sk_m:.1f}%** ± {sk_s:.1f} (CV {sk_cv:.1f}%)",
             "",
             "| 來源 | 幀數 | heavy | light | skip | heavy% | skip% |",
             "|---|---|---|---|---|---|---|"]
    for src, nf, h, l, sk, ing in rows:
        h_pct = (h / ing * 100) if ing else 0.0
        sk_pct = (sk / nf * 100) if nf else 0.0
        lines.append(f"| {src} | {nf} | {h} | {l} | {sk} | {h_pct:.1f} | {sk_pct:.1f} |")
    lines.append("")
    return "\n".join(lines)


def section_trend(runs: List[Dict[str, Any]]) -> str:
    """按 timestamp 排序看 loop_total 趨勢（簡易：頭尾差、線性遞增/遞減判斷）。"""
    by_ts = sorted(runs, key=lambda r: r.get("timestamp", ""))
    totals = [(r.get("timestamp", ""),
               r["metadata"].get("source_stem", "?"),
               r.get("loop_total_s", 0.0)) for r in by_ts]
    trust = (f"✓ N ≥ {TRUST_THRESHOLD}，趨勢具參考性"
             if len(runs) >= TRUST_THRESHOLD
             else f"⚠️ N < {TRUST_THRESHOLD}，趨勢僅供觀察")

    lines = [f"## §11 跨 Run 趨勢\n",
             f"_{trust}_\n"]
    if len(totals) >= 2:
        first_t = totals[0][2]
        last_t = totals[-1][2]
        delta = last_t - first_t
        direction = "↑ 變慢" if delta > 0 else ("↓ 變快" if delta < 0 else "→ 持平")
        pct = (delta / first_t * 100) if first_t else 0.0
        lines.append(f"- 首 run 總耗時 = {first_t:.2f}s → 末 run 總耗時 = "
                     f"{last_t:.2f}s（{direction}，Δ = {delta:+.2f}s / {pct:+.1f}%）")
        lines.append("")
    lines.append("| # | 時間戳 | 來源 | 總耗時 (s) |")
    lines.append("|---|---|---|---|")
    for i, (ts, src, tot) in enumerate(totals, 1):
        lines.append(f"| {i} | {ts} | {src} | {tot:.2f} |")
    lines.append("")
    return "\n".join(lines)


def section_observations(runs: List[Dict[str, Any]]) -> str:
    """條件式建議：N 不足 / CV 過大 / cadence 異常 / detect_roi 主導等規則。"""
    notes = []
    if len(runs) < TRUST_THRESHOLD:
        notes.append(f"- ⚠️ **樣本不足**：N = {len(runs)} < {TRUST_THRESHOLD}，"
                     "變異與趨勢分析需更多 run（建議跑 ≥ 5 次同 source 不同條件）。")

    layer_stages = _all_layer_stages(runs)
    # detect_roi 主導判斷：roi mean 占 per_frame.heavy 比例 > 50%
    roi_means = _collect_stage_values(runs, "heavy", "roi", "avg_ms")
    heavy_means = _collect_stage_values(runs, "per_frame", "heavy", "avg_ms")
    if roi_means and heavy_means:
        ratio = statistics.fmean(roi_means) / statistics.fmean(heavy_means) * 100
        if ratio > 50:
            notes.append(f"- **roi 主導 heavy 路徑**：roi avg / heavy avg ≈ {ratio:.0f}%。"
                         "若進一步優化，drill into Layer roi 與 detect。")

    # curve_fit 顯著（avg > 50 ms 或 CV > 30%）
    cf_avgs = _collect_stage_values(runs, "detect", "curve_fit", "avg_ms")
    if cf_avgs:
        m, _, cv = _stats(cf_avgs)
        if m > 50 or cv > 30:
            notes.append(f"- **curve_fit 為熱點**：mean avg = {m:.1f}ms, CV = {cv:.1f}%。"
                         "curve_fit_maxfev 上限已套（5000），如仍高考慮 candidates 過濾收緊。")

    # heavy cadence 異常：heavy_n 比例 > 預期上限（K_max=60 → ~1.7%）或 < 5%
    cad_h_pct = []
    for r in runs:
        md = r["metadata"]
        ing = md.get("heavy_n", 0) + md.get("light_n", 0)
        if ing:
            cad_h_pct.append(md.get("heavy_n", 0) / ing * 100)
    if cad_h_pct:
        m, _, cv = _stats(cad_h_pct)
        if cv > 30:
            notes.append(f"- **cadence 變異大**：heavy / ingested CV = {cv:.1f}%，"
                         "可能反映 source 內波形差異（峰觸發頻率不同）。")

    if not notes:
        notes.append("- 無明顯異常。")

    return "## §12 觀察與建議\n\n" + "\n".join(notes) + "\n"


def build_report(
    runs: List[Dict[str, Any]], dedup_mode: str = "all",
    dropped: int = 0, raw_n: Optional[int] = None,
    target_fps: float = DEFAULT_TARGET_FPS,
    excluded_stages: Optional[List[str]] = None,
) -> str:
    if raw_n is None:
        raw_n = len(runs)
    excluded_stages = excluded_stages or []
    parts = [
        f"# REALTIME 效能分析報表（跨 Run Aggregation）\n",
        f"_生成時間：{datetime.now().isoformat(timespec='seconds')}_  ",
        f"_資料源：`output/timing/runs.jsonl`（{len(runs)} runs，去重模式 = {dedup_mode}）_\n",
        section_legend(),
        section_realtime_assessment(runs, target_fps),
        section_realtime_assessment_excluded(runs, target_fps, excluded_stages),
        section_per_frame_distribution(runs, target_fps),
        section_slow_frame_attribution(runs, target_fps),
        section_inventory(runs, dedup_mode, dropped, raw_n),
        section_total_ranking(runs),
        _layer_breakdown_section(runs, "per_frame",
                                 "§4 Layer per_frame 分解",
                                 "loop_total（系統總耗時）"),
        section_hierarchy(runs),
        _layer_breakdown_section(runs, "heavy",
                                 "§6 Layer heavy 內部",
                                 "heavy 總耗時"),
        _layer_breakdown_section(runs, "roi",
                                 "§7 Layer roi 細項",
                                 "roi 總耗時"),
        _layer_breakdown_section(runs, "detect",
                                 "§7.1 Layer detect 內部（兩 pass 累計）",
                                 "roi 總耗時"),
        _layer_breakdown_section(runs, "light",
                                 "§8 Layer light 內部",
                                 "light 總耗時"),
        section_variance_sources(runs),
        section_cadence(runs),
        section_trend(runs),
        section_observations(runs),
    ]
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL,
                        help=f"輸入 jsonl 路徑 (default: {DEFAULT_JSONL})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"輸出 markdown 路徑 (default: {DEFAULT_OUT})")
    parser.add_argument("--dedup", choices=["all", "last", "first"], default="all",
                        help="同 source_stem 去重：all=全收（預設）/ last=留最新 / first=留最早")
    parser.add_argument("--fps", type=float, default=DEFAULT_TARGET_FPS,
                        help=f"目標 FPS（即時性評估用）(default: {DEFAULT_TARGET_FPS})")
    parser.add_argument("--exclude", type=str, default="",
                        help="假設情境：排除指定 stage（CSV，如 'seg_predict' 或 "
                             "'seg_predict,pv_render'）→ 生成 §1.1 對照表")
    args = parser.parse_args()

    excluded = [s.strip() for s in args.exclude.split(",") if s.strip()]

    raw_runs = load_runs(args.jsonl)
    if not raw_runs:
        raise SystemExit(f"無 run 紀錄：{args.jsonl}")
    runs, dropped = dedup_runs(raw_runs, args.dedup)
    report = build_report(runs, dedup_mode=args.dedup,
                          dropped=dropped, raw_n=len(raw_runs),
                          target_fps=args.fps,
                          excluded_stages=excluded)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    msg = f"[timing_report] {len(runs)} runs"
    if dropped:
        msg += f" (dedup={args.dedup} dropped {dropped})"
    print(f"{msg} → {args.out}")


if __name__ == "__main__":
    main()
