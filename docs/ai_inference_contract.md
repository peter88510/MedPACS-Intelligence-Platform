# AI Inference Contract — `inference.py` facade 施工圖

> **定位**：MedPACS 與 `diaphragm_excursion`（上游 AI repo）之間的**整合介面契約**。
> **狀態**：契約定案，待上游實作。
> **交付對象**：上游 `diaphragm_excursion` repo 的 AI agent。
> **流程**：上游依本契約實作 `inference.py` → 工程師把 `inference.py` 貼進 MedPACS `./AI/` → 主 Agent re-vendor + 簡化 engine。
> **日期**：2026-06-11
> **git**：本檔 git-track（durable 整合契約；非一次性設計備忘）。
>
> **路徑慣例**：本檔所有 `xxx.py` / `config/` / `algorithm/` 路徑皆相對 **diaphragm_excursion repo root**
> （= MedPACS 內的 `AI/`）。上游 agent 在自己 repo root 施工即可。

---

## 1. 背景與目標

MedPACS 的 `POST /ai/segment/{id}` 目前是這樣接演算法的（不好維護）：

- 用 `importlib.util.spec_from_file_location` 把 `main.py` 以獨立名載入（因為模組名 `main` 與後端 FastAPI `main.py` 撞名）。
- 直接呼叫 `main.run()`，並伸手進 `RunBundle` 內部強制 `multiframe.mode=LEGACY`、`viz.enabled=False`、`segmenter.save_predictions=False`。
- `main.run()` 夾帶 viz / timing / multiframe dispatch，且回傳 **numpy 純量**（MedPACS 端要再手動轉 native 才能寫進 JSONB）。

**目標**：上游提供一個**乾淨、穩定的程式化入口** `inference.py`，讓 MedPACS 只需呼叫一個 function 拿到 native 結果。達成後 MedPACS engine 從 ~250 行縮到十幾行、importlib hack 消失、numpy 正規化移到上游。

**非目標**：不改演算法本身、不改 `main.py` 的 CLI 行為（`python main.py` 仍可跑）。`inference.py` 是**新增的並列入口**，不是取代 `main.py`。

---

## 2. 契約：`inference.py` public API

新增檔案 `inference.py`（repo root，與 `main.py` 並列）。對外只公開以下三個名稱。

```python
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ExcursionMeasurement:
    """單一 peak/trough 量測。全部 native Python 型別（不可有 numpy 純量）。"""
    excursion_cm: Optional[float]      # 無 PhysicalDeltaY(scale_y) → None
    excursion_pixel: int
    time_pixel: int
    time_sec: Optional[float]          # excursion phase → None；sniff(有 scale_x) → 有值
    velocity: Optional[float]
    crest: Tuple[int, int]             # (x, y)
    trough: Tuple[int, int]


@dataclass
class InferenceResult:
    measurements: List[ExcursionMeasurement]
    mask_path: Optional[str]           # save_mask_dir 有給才回；否則 None
    model_version: str                 # 例："6139799"（snapshot commit）
    frame_count: int                   # 處理的 frame 數（debug/audit）


def analyze(
    image_path: str,
    *,
    phase: str = "excursion",          # "excursion" | "sniff"
    save_mask_dir: Optional[str] = None,
) -> InferenceResult:
    ...
```

### `analyze()` 參數語義

| 參數 | 說明 |
|---|---|
| `image_path` | DICOM 檔絕對路徑（MedPACS 會傳已儲存的 `.dcm`） |
| `phase` | `"excursion"` / `"sniff"` 字串。內部映射到 `Phase` enum（不外露 enum）。其他值 → `raise ValueError` |
| `save_mask_dir` | 給定時：開啟 segmenter mask 輸出到此資料夾，並在 `InferenceResult.mask_path` 回寫實際檔案路徑。未給（None）：不寫任何檔、`mask_path=None` |

---

## 3. 行為規格（必須遵守）

1. **回傳全 native Python 型別**：`ExcursionMeasurement` 內所有數值必須是 `int`/`float`/`None`，`crest`/`trough` 是 `(int, int)`。**在 facade 內把 numpy 純量轉掉**（`int(...)`/`float(...)`，None 不轉）。這是契約的硬性要求——MedPACS 直接把它序列化進 JSONB，不再做型別正規化。

2. **tuning 100% 由 `run_config` 管**：MedPACS **不傳任何調參**。facade 內部用 `build_api_bundle(phase)`（見 §4）建 bundle，調參完全來自上游 `run_config.py`（你的個人/部署統一入口）。

3. **強制 API-safe 設定**（不論 run_config 怎麼設，facade 內強制）：
   - `multiframe.mode = LEGACY` — 同步單次量測；`GLOBAL_WINDOW`/`REALTIME` 的正解活在 run-loop state、不被回傳，**不可**用於本契約。
   - `viz.enabled = False` — 不產生 debug/final 視覺化檔。
   - `segmenter.save_predictions`：**僅當 `save_mask_dir` 有給時才 True**（且 `save_dir = save_mask_dir`），否則 False。

4. **無副作用（預設）**：不寫檔、不印 timing、不開 video writer。`main.py` 的 `RealtimeTiming` / `record_run` / `print` 噪音都不要進這條路。

5. **錯誤行為**：
   - 影像無法讀 / 非 DICOM → `raise` 明確例外（例 `ValueError`/`FileNotFoundError`），訊息可讀。
   - 跑完但偵測不到任何 peak/trough → 回 `InferenceResult(measurements=[], ...)`（**不是**錯誤；MedPACS 會記為 completed、primary 為 None）。
   - `phase` 非法 → `raise ValueError`。

6. **LEGACY 單幀路徑**：等同現有 `_run_legacy` 的演算法，但去掉 logging/viz。複用 `_run_single_frame` 的 pipeline（load → crop → segment → detect → roi → motion_curve → excursion → compute_peak_info），跨 frame 把每個 `PeakInfo` 攤平成 `measurements[]`。

---

## 4. 內部實作指引

### 4.1 抽取必要 function（順手改名）

facade 應**只依賴量測必要路徑**，不 import viz/timing/experiments：

| 需要 | 來源（現況） |
|---|---|
| load + crop | `input.load` / `input.apply_dicom_crop` |
| segmenter | `algorithm.segmentation.PaddleSegSegmenter` |
| 單幀 pipeline | `main._run_single_frame` 的核心（去掉 `pv.render_frame`、timing、print） |
| 物理量 | `algorithm.excursion.compute_peak_info`（已回 `PeakInfo` dataclass） |
| frame 選取 | `algorithm.multiframe.get_legacy_frame_indices`（LEGACY） |

建議把 `_run_single_frame` 去 viz/timing 後的純量版抽成 `inference._infer_frame(...)`，或在上游把 `main.py` 的共用核心抽到 `algorithm/` 層、`main.py` 與 `inference.py` 各自薄包。**抽取/改名請在上游做**，MedPACS 不碰。

### 4.2 `build_api_bundle(phase)` 規格

```python
def build_api_bundle(phase: Phase) -> RunBundle:
    # 1) 基底：個人/部署調參統一入口（在則用、不在則 canonical default）
    try:
        import run_config as rc
        bundle = rc.build_bundle()              # run_config 為唯一 tuning 入口
        if bundle.detection.phase != phase:     # run_config 基底 phase 與請求不同 → 對齊
            bundle.detection = DiaphragmDetectionConfig.for_phase(phase)
    except ImportError:
        bundle = RunBundle.for_phase(phase)
    # 2) 強制 API-safe（§3.3）
    bundle.multiframe.mode = MultiframeMode.LEGACY
    bundle.viz.enabled = False
    return bundle
```

> `save_predictions` 不在這裡決定——由 `analyze()` 依 `save_mask_dir` 設（§3.3）。
> run_config 內若設了 `save_predictions=True`，facade 在 `save_mask_dir=None` 時仍要蓋回 False。

### 4.3 mask 輸出

`save_mask_dir` 有給時：設 `bundle.segmenter.save_predictions=True` + `bundle.segmenter.save_dir=save_mask_dir`，跑完後**回寫 segmenter 實際寫出的 PNG 路徑**到 `InferenceResult.mask_path`（需確認 paddleseg 的輸出檔名慣例）。MedPACS 之後的 mask PNG endpoint 會靠這個路徑供前端 overlay。

---

## 5. Vendoring scope（給 re-vendor 用）

re-vendor 時，MedPACS 只需「量測必要 + facade」。請在上游標明哪些是 API-necessary：

| 類別 | dir / 檔 | re-vendor |
|---|---|---|
| **必要** | `inference.py`(新) / `main.py` / `config/` / `algorithm/` / `input/` / `paddleseglibs/`(gitignore) / `run_config.example.py` | 保留 |
| **可不 vendor** | `visualization/` / `tools/`(timing) / `experiments/` / `font/` | 排除（API 不走 viz） |

> ⚠️ **相依連帶**：砍 `visualization/` 後，`requirements-ai.txt` 的 `visualdl`/`matplotlib`/`imageio`/`imageio-ffmpeg` **不一定能移除**——paddleseg `cvlibs/callbacks.py` 在 package 載入時可能 transitively import `visualdl`。**Phase 2 re-vendor 時實測**：裝最小集合跑一次 `inference.analyze` smoke，能過才砍。不可先砍。

---

## 6. MedPACS 消費端（re-vendor 後，主 Agent 做）

讓上游理解 consumer 形狀——`services/ai_engine/diaphragm_excursion_engine.py` 會簡化成：

```python
def analyze(self, image_path, measurement_type):
    inf = self._load_inference()                 # sys.path 插 AI/ + `import inference`
                                                  # （inference 不撞名 → importlib spec hack 消失）
    res = inf.analyze(image_path, phase=measurement_type.value,
                      save_mask_dir=<可選>)
    return EngineResult(                          # res.measurements 已 native，直接帶
        measurement_type=measurement_type,
        model_name="diaphragm_excursion",
        model_version=res.model_version,
        pipeline_mode="legacy",
        measurements=[Measurement(batch_index=i, ...) for i, m in enumerate(res.measurements)],
        mask_path=res.mask_path,
    )
```

消失的東西：`importlib` spec 載入、`_build_bundle` 伸手進 AI config、`_opt_int/_opt_float/_opt_point` numpy 正規化（移到上游 §3.1）。

---

## 7. 驗收 / smoke test（上游實作後自驗）

1. `from inference import analyze, InferenceResult, ExcursionMeasurement` 可 import。
2. 對一張 excursion DICOM：`analyze(path, phase="excursion")` 回 `InferenceResult`，`measurements` 非空、`excursion_cm` 在合理範圍（~1–7 cm）。
3. **型別檢查**：`type(m.excursion_pixel) is int`、`type(m.excursion_cm) is float`（或 None）——**不可是 numpy**。`import json; json.dumps([m.__dict__ for m in res.measurements])` 不報錯。
4. `analyze(path, save_mask_dir="/tmp/mask")` → `mask_path` 指向實際存在的 PNG。
5. `analyze(path, phase="bogus")` → `ValueError`。
6. 無副作用：預設呼叫不在 cwd 產生 `output/` 檔、不印 timing。

---

## 8. 開放問題 / 非目標

- **sniff 量測路徑待確認**：現有 `_run_single_frame` 以 `is_excursion = (phase == Phase.EXCURSION)` gate 量測，`Phase.SNIFF` 時 `excursion=None`、`measurements=[]`。契約簽名保留 `phase="sniff"`（forward-design），但**上游需確認/補上 sniff 真的會產出 measurements**，否則 sniff 會回空。MVP 只用 excursion（MedPACS 目前只有 C62→excursion 一個機型映射），sniff 不阻擋本契約。
- **thickness 不在此契約**：thickness 演算法尚不存在；MedPACS 在呼叫 `analyze` 之前就以 501 擋掉 thickness，facade 不需處理。
- **viz 相依砍除**：見 §5 ⚠️，Phase 2 實測決定，不在本契約承諾。
- **`model_version` 來源**：建議用 vendored snapshot 的 git short SHA 或 repo 內某個版本常數；MedPACS 目前 hardcode `"6139799"`，上游回傳值會覆蓋之。
