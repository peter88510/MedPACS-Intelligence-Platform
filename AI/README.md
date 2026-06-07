# diaphragm_excursion

> M-mode 超音波橫膈膜 excursion 自動量測管線：DICOM → motion curve → peak/trough → 物理距離（cm）。

---

## 文件元資料

| 項目 | 值 |
|---|---|
| Tier | STABLE |
| 版本 | v1.1 |
| 最後更新 | 2026-06-03 |
| 適用 | 接手工程師、新加入 AI agent、回顧自己進度 |

---

## §1 專案簡述

兩層架構：

- **Input 層**：DICOM / PNG → 統一 `FrameSequence`（含 N×H×W frames、metadata、scale_x/y）
- **Algorithm 層**：segmentation → diaphragm_detection → ROI band → motion_curve → excursion → measurement；multiframe dispatch（LEGACY / GLOBAL_WINDOW / REALTIME 三 mode）
- **Visualization 層**：debug per-stage + final overlay + REALTIME mp4 video + canvas PNG + timing record（五條獨立 track）
- **Profiling 層**：REALTIME mode `RealtimeTiming` per-stage 計時 + JSONL 跨 run 累積 + `tools/timing_report.py` 跨 run aggregation

**技術棧**：

| 維度 | 內容 |
|---|---|
| Python | 3.8 |
| 核心依賴 | `paddleseg`（vendored）/ `pydicom` / `numpy` / `scipy` / `scikit-image` / `opencv-python` / `Pillow` / `pywt` / `bresenham` |
| 影像來源 | DICOM single-frame / multi-frame；PNG single / dir |
| 輸出 | excursion 物理距離（cm）+ 可選 viz overlay PNG |

---

## §2 現況

| 維度 | 狀態 |
|---|---|
| Refactor 進度 | Step 1-10 完成（三 mode 全落地）；增量優化階段（Patch 19-24 已落地） |
| Git | 上 origin/master；Conventional Commits + 中文 |
| 待續 | Patch 20B regression（curve_fit_maxfev=5000 vs 10M）；pass1 內部優化方向（24A 後續） |

詳細狀態與里程碑見 [`PROGRESS.md`](PROGRESS.md)。

---

## §3 Quick Start

### 環境

需要 Python 3.8 + paddle 安裝環境（含 vendored `paddleseglibs/`）。

### 取得模型權重

`paddleseglibs/output/model/*/best_model/model.pdparams`（5 × 323 MB）**未入 git**（.gitignore 排除）。

clone 後請另外取得：

- 路徑：`paddleseglibs/output/model/<model_name>/best_model/model.pdparams`
- 來源：自 Paddle model zoo 或內部 lab 儲存
- 預設 cfg 走 `paddleseglibs.predict.DEFAULT_MODEL_PATH`；如改路徑請同步 `PaddleSegSegmenterConfig.model_path`

缺模型 → main.py 跑到 segmenter.load() 會報錯。

### 編輯 DCM 路徑

`main.py` 末尾預設值：

```python
image_path = (
    r"E:\PeterMC_Tsai\Diaphragm_data\Quality_Classification_base_up_down\Dicom_ex"
    r"\Excursion-QB\1017(new))\Peter\Peter_Quiet_1.dcm"
)
run(image_path)
```

改為自己 DCM 路徑後執行：

```bash
python main.py
```

### 預期 log

每 10 frame 印一行：

```
[input] source_type=dcm_multi, frames.shape=(N, H, W), fps=...
[preprocess] cropped frames.shape=(N, H, W)
[frame 1/N] best=(top, bottom), y_band=(min, max), source=segment/classical, target=True, broken=K, batches=B, excursion_cm=X.XX
...
[done] N frames, target_binary=N, excursion_runs=M
```

`excursion_cm` 合理範圍：橫膈膜典型 1–7 cm。

### 開啟 viz

預設不存圖。手動把 `main.py` 內這行：

```python
viz_cfg = VisualizationConfig()
```

改成：

```python
viz_cfg = VisualizationConfig(enabled=True, save_final=True, save_debug=True)
```

輸出位置（全 mode）：

- `output/final/{i:04d}.png` — 綜合成果圖（crest/trough marker + excursion_cm 文字 + motion curve 軌跡）
- `output/debug/{stage}/{i:04d}.png` — 9 個 stage 各自目錄（detection / motion / excursion brightness 波形 / 等）

### REALTIME mode 額外輸出

`MultiframeConfig.mode = MultiframeMode.REALTIME` 時自動產：

- `output/realtime/{stem}_realtime.mp4` — canvas → mp4（imageio-ffmpeg libx264；`save_realtime_video=True` 預設）
- `output/realtime/canvas/{i:04d}.png` — 每幀 canvas PNG（`save_realtime_canvas_png=False` 預設關，debug 用）
- `output/timing/runs.jsonl` — 每 run 1 行 JSON timing record（`save_timing_record=True` 預設）

跨 run timing 聚合分析：

```bash
python -m tools.timing_report             # 預設讀 output/timing/runs.jsonl → output/timing/report.md
python -m tools.timing_report --dedup last # 同 source_stem 只留最新（debug 重跑去重）
```

報告含：總時間 ranking + outlier、5 層 stage breakdown（per_frame / heavy / roi / detect / light）、變異來源 top-N（CV 排序）、heavy/light cadence、跨 run 趨勢。

---

## §4 Repo 結構

```
diaphragm_excursion/
├── main.py                          orchestration（per-frame loop）
├── CLAUDE.md                        AI 行為合約（STABLE）
├── PROGRESS.md                      進度紀錄（LIVING）
├── algorithm/
│   ├── diaphragm_detection/         橫膈膜 ROI 偵測
│   ├── excursion/                   peak/trough 找峰算法 + 物理量計算
│   ├── motion_curve/                時間軸軌跡擷取
│   ├── multiframe/                  Multi-frame 模式（Step 10 進行中）
│   ├── roi_band/                    ROI 擴張 + enhanced search
│   ├── segmentation/                PaddleSegSegmenter wrapper
│   ├── signal_processing/           wavelet 等 signal helpers
│   └── frame_result.py              FrameResult dataclass（每 frame 整合）
├── config/                          所有 dataclass config（per-layer）
├── input/                           DCM/PNG reader + FrameSequence
├── visualization/                   debug 與 final overlay viz
├── paddleseglibs/                   vendored PaddleSeg（含 Patch 2A-2C 改動）
├── docs/
│   ├── STYLE.md                     文件格式規範（STABLE）
│   └── notes/                       SNAPSHOT 文件
├── tools/                           CLI 工具
│   └── timing_report.py             REALTIME 跨 run timing 聚合（讀 jsonl → md）
├── experiments/                     驗證 script
├── font/                            自訂字型（viz 用 Altinn-DIN Bold.otf）
└── output/                          viz 輸出（gitignored）
    ├── final/                       all-mode 綜合成果圖
    ├── debug/                       all-mode 9 stage debug 圖
    ├── realtime/                    REALTIME mode 專用 mp4 + canvas PNG
    └── timing/                      REALTIME run 紀錄 + aggregation report
```

---

## §5 文件索引

完整 14 份文件清單見 [`docs/INDEX.md`](docs/INDEX.md)（依 Tier 分組、含 SNAPSHOT 狀態 audit）。

新人優先看：

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — 跨層架構與設計決策
- [`docs/pipeline.md`](docs/pipeline.md) — per-frame data flow
- [`docs/modules/`](docs/modules/) — 各 layer 內部設計（algorithm / input / visualization）
- [`CLAUDE.md`](CLAUDE.md) — AI 行為合約（協作慣例）
- [`PROGRESS.md`](PROGRESS.md) — 進度紀錄 / Session 重啟接續點

---

## §6 已知限制

| 限制 | 影響 | 處理 |
|---|---|---|
| PaddleSeg 環境依賴重 | `python main.py` 必須在 paddle env 跑 | vendored `paddleseglibs/`；env 設定靠使用者 |
| 無 unit test 套件 | 驗證靠 `main.py` log 對照預期 + REALTIME timing report 數字 | `experiments/verify_segmenter_equivalence.py` + `tools/timing_report.py` |
| 無 git tag / version | 無正式版本標記 | 待大階段收尾後加 tag |
| `area_ratio` numerator hardcode | `DiaphragmDetectionConfig.area_ratio = 10000 / (955 * 1500)`：分子 10000 是 canonical pixel 數，異尺寸 input 邏輯仍正確但設計史不明顯 | `docs/notes/size_normalization_pre_ratio_audit.md` §2.3 已標 |
| Patch 20B regression 未跑 | `curve_fit_maxfev=5000` vs 原 10M 的 byte-identical 驗證待跑 | PROGRESS.md 待辦 |
| timing 跨 run 累積 < 5 | 變異 / 趨勢分析需累積樣本 | PROGRESS.md 待辦 |

---

## §7 變更紀錄

| 日期 | 版本 | 變更 | 動因 |
|---|---|---|---|
| 2026-05-24 | v1.0 | 初版建立；§1-§6 全部章節定義 | 文件化專案啟動，提供 onboarding 入口 |
| 2026-05-24 | — | §5 文件索引簡化：移除全表，改連 `docs/INDEX.md` + 列「新人優先看」5 條 | INDEX.md 已成為單一真實來源；避免兩處索引 sync 麻煩 |
| 2026-05-25 | — | §3 加「取得模型權重」子節；.gitignore 排除 paddleseglibs/output/ 與 paddle artifacts | 首次 git commit 前 pre-cleanup；1.7GB 模型權重不入 git |
| 2026-06-03 | v1.1 | §1 viz 兩 track → 五 track + 加 Profiling 層；§2 現況更新（Step 10 ✅、Patch 19-24 落地）；§3 加 REALTIME mode 輸出 + `tools/timing_report.py` 用法；§4 repo 結構加 `tools/` + `output/` 子目錄；§6 已知限制更新 | Patch 22 mp4 + Patch 23 timing record + aggregation + Patch 24A skip pass2；STABLE tier 里程碑 sync |
