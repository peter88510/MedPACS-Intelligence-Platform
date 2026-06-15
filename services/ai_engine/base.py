"""AI 推論引擎抽象介面（service layer）。

可替換式介面：endpoint 只依賴抽象 `DiaphragmEngine`，不認識任何特定平台。未來換
模型 / 平台（ONNX / TensorRT / 不同演算法）只要實作新的 `DiaphragmEngine` 子類，
並在 `get_engine()`（見 __init__.py）換注入點即可，呼叫端與 endpoint 完全不動。

平台中立資料結構（`Measurement` / `EngineResult`）讓 endpoint 的序列化邏輯
（→ ai_results.result_json envelope，design §4）與底層 AI 輸出型別解耦。

本層不可 import FastAPI（CLAUDE.md §6）。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from services.measurement_type import MeasurementType


class EngineUnavailableError(RuntimeError):
    """AI 執行期相依（paddle / paddleseglibs / model weights）未安裝。

    與「真正的推論失敗」區分：endpoint 將此映射為 503（服務未佈建）而非 500。
    讓後端與測試套件不需安裝整套 AI stack 也能跑（requirements-ai.txt 為獨立安裝）。
    """


class EngineError(RuntimeError):
    """推論有嘗試但失敗（影像無法讀 / 找不到橫膈膜 / pipeline 拋例外…）。
    endpoint 將此映射為 500。"""


@dataclass
class Measurement:
    """單一 peak/trough 量測，平台中立。

    對應 vendored AI 的 `PeakInfo` 形狀，但由 service layer 擁有，讓不同 engine
    可以填同一份契約。欄位皆為 optional：DICOM 無 PhysicalDeltaY（無 cm scale）時
    excursion_cm 為 None；time_sec / velocity 僅 sniff（有 scale_x）時才有值。
    """
    batch_index: int
    excursion_cm: Optional[float] = None
    excursion_pixel: Optional[int] = None
    time_pixel: Optional[int] = None
    time_sec: Optional[float] = None
    velocity: Optional[float] = None
    crest: Optional[List[int]] = None     # [x, y]
    trough: Optional[List[int]] = None    # [x, y]


@dataclass
class EngineResult:
    """單一 instance 的引擎中立分析輸出。

    一次 run 產生 N 個 measurement（每個偵測到的 peak/trough batch 一個）。下游
    序列化成 ai_results.result_json envelope（design §4）。
    """
    measurement_type: MeasurementType
    model_name: str
    model_version: str
    pipeline_mode: str                    # legacy | global_window | realtime
    measurements: List[Measurement] = field(default_factory=list)
    mask_path: Optional[str] = None       # 預留；mask PNG 屬下游（design §8）

    @property
    def primary(self) -> Optional[Measurement]:
        """headline 量測（第一個 batch）；沒偵測到任何結果時為 None。"""
        return self.measurements[0] if self.measurements else None


class DiaphragmEngine(ABC):
    """AI endpoint 依賴的穩定介面；實作可替換。"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @property
    @abstractmethod
    def model_version(self) -> str:
        ...

    @abstractmethod
    def analyze(
        self,
        image_path: str,
        measurement_type: MeasurementType,
        save_mask_dir: Optional[str] = None,
    ) -> EngineResult:
        """對單一 DICOM 檔跑推論。

        Args:
            image_path: 已儲存 .dcm 檔的絕對路徑。
            measurement_type: 已解析的類型（excursion / sniff）。unknown / thickness
                由 endpoint 在進入這裡之前就擋掉。
            save_mask_dir: 給定時開啟 segmenter mask 輸出到此目錄，並在
                EngineResult.mask_path 回寫實際 PNG 路徑；未給（None）則不寫檔、
                mask_path 為 None。caller（endpoint）負責決定目錄落點。

        Returns:
            EngineResult（平台中立）。

        Raises:
            EngineUnavailableError: AI 相依未安裝 → 503。
            EngineError: 有嘗試推論但失敗 → 500。
        """
        ...

    def warmup(self) -> None:
        """選擇性預載重型資源（模型權重等），消除第一次 analyze 的冷啟延遲。

        預設 no-op：輕量 / fake engine 不需實作。重型 engine 覆寫。
        缺相依時由實作拋 EngineUnavailableError，降級由呼叫端（startup）負責。
        """
        return None
