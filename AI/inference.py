"""程式化推論入口（facade）：consumer（MedPACS 等）用單一 function 拿 native 結果。

與 main.py 並列的新增入口，不取代 CLI。對外公開：
    analyze / InferenceResult / ExcursionMeasurement   — 量測主入口 + 結果型別
    prepare_segmenter                                  — service 啟動時預載 warm segmenter

內部複用 algorithm.single_frame.run_single_frame 的純量 pipeline（無 viz / 無 timing /
無 print），跨 frame 把每個 PeakInfo 攤平成 measurements。回傳全 native Python 型別
（int / float / None / (int,int)）——consumer 直接序列化進 JSONB，不再做 numpy 正規化。

長駐 service 用法：啟動時 seg = prepare_segmenter()（model load 一次），每 request
analyze(path, segmenter=seg)（跳過重載）。契約見 docs/ai_inference_contract.md（v1.1）。
"""
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

from algorithm.multiframe import get_legacy_frame_indices
from algorithm.segmentation import PaddleSegSegmenter
from algorithm.single_frame import run_single_frame
from config import DiaphragmDetectionConfig, Phase, RunBundle
from config.multiframe_config import MultiframeMode
from input import apply_dicom_crop, load


# 演算法 snapshot 版本：vendored 進下游後 .git 可能不在，故用常數而非 git SHA；
# 演算法/權重變更時手動 bump（= 落地當下 repo HEAD short SHA）。
MODEL_VERSION = "5adfeaa"

_PHASE_MAP = {
    "excursion": Phase.EXCURSION,
    "sniff": Phase.SNIFF,
}


@dataclass
class ExcursionMeasurement:
    """單一 peak/trough 量測。全部 native Python 型別（無 numpy 純量）。"""
    excursion_cm: Optional[float]      # 無 scale_y → None
    excursion_pixel: int
    time_pixel: int
    time_sec: Optional[float]          # excursion phase → None；sniff(有 scale_x) → 有值
    velocity: Optional[float]
    crest: Tuple[int, int]             # (x, y)
    trough: Tuple[int, int]


@dataclass
class InferenceResult:
    measurements: List[ExcursionMeasurement]
    mask_path: Optional[str]           # save_mask_dir 有給且檔案存在才回；否則 None
    model_version: str
    frame_count: int                   # 處理的 frame 數（debug/audit）


def _resolve_phase(phase: str) -> Phase:
    """字串 → Phase enum；非法值 raise ValueError。"""
    try:
        return _PHASE_MAP[phase]
    except KeyError:
        raise ValueError(
            f"Unknown phase {phase!r}; expected 'excursion' or 'sniff'"
        )


def build_api_bundle(phase: Phase) -> RunBundle:
    """建 API-safe bundle：run_config（若存在）為 tuning 基底，強制 LEGACY + viz off。

    save_predictions 不在此決定——由 analyze() / prepare_segmenter() 依需求設。
    """
    try:
        import run_config as rc
        bundle = rc.build_bundle()              # run_config 為唯一 tuning 入口
        if bundle.detection.phase != phase:     # 基底 phase 與請求不同 → 對齊
            bundle.detection = DiaphragmDetectionConfig.for_phase(phase)
    except ImportError:
        bundle = RunBundle.for_phase(phase)
    bundle.multiframe.mode = MultiframeMode.LEGACY
    bundle.viz.enabled = False
    return bundle


def prepare_segmenter(
    phase: str = "excursion",
    *,
    warmup_image_path: Optional[str] = None,
) -> PaddleSegSegmenter:
    """Service 啟動時預載 warm segmenter；之後傳給 analyze(segmenter=...) 重用。

    model load（秒級）在此一次完成、確定性。segmenter 與 phase 無關（同一橫膈膜分割
    模型），一個 instance 兩 phase 共用——phase 僅用於透過 build_api_bundle 取 run_config
    的 segmenter override（model path / device 等）。

    Args:
        phase: "excursion" / "sniff"（影響取得的 segmenter cfg 來源；非法 → ValueError）
        warmup_image_path: 給樣本 DICOM 時額外跑一次 predict 觸發 paddle lazy init
            （CUDA graph compile），消第一個真實 request 的 cold start。不給則只 load。

    Returns:
        已 load 的 PaddleSegSegmenter（save_predictions 預設 False，warm 不寫檔）
    """
    phase_enum = _resolve_phase(phase)
    bundle = build_api_bundle(phase_enum)
    bundle.segmenter.save_predictions = False    # warm 預設不寫檔（mask 輸出由 analyze 控）
    segmenter = PaddleSegSegmenter(bundle.segmenter)
    segmenter.load()
    if warmup_image_path is not None:
        seq = apply_dicom_crop(load(warmup_image_path), bundle.dicom_crop)
        segmenter.predict(image_path=seq.source_path, dcm_array=seq.frames[0])
    return segmenter


def _to_measurement(p) -> ExcursionMeasurement:
    """PeakInfo → ExcursionMeasurement，numpy 純量轉 native（None 不轉）。"""
    return ExcursionMeasurement(
        excursion_cm=None if p.excursion_cm is None else float(p.excursion_cm),
        excursion_pixel=int(p.excursion_pixel),
        time_pixel=int(p.time_pixel),
        time_sec=None if p.time_sec is None else float(p.time_sec),
        velocity=None if p.velocity is None else float(p.velocity),
        crest=(int(p.crest[0]), int(p.crest[1])),
        trough=(int(p.trough[0]), int(p.trough[1])),
    )


def _resolve_mask_path(save_mask_dir: str, source_path: Optional[str]) -> Optional[str]:
    """paddleseg 寫出慣例：{save_dir}/pseudo_color_prediction/{stem}.png。

    檔案不存在（如 predict 未寫出）→ None。multi-frame DCM 因檔名不含 frame index
    會互相覆蓋，此路徑指向最後寫出的一張（已知低優先 bug，見 PROGRESS）。
    """
    if not source_path:
        return None
    stem = os.path.splitext(os.path.basename(source_path))[0]
    path = os.path.join(save_mask_dir, "pseudo_color_prediction", stem + ".png")
    return path if os.path.exists(path) else None


def analyze(
    image_path: str,
    *,
    phase: str = "excursion",
    save_mask_dir: Optional[str] = None,
    segmenter: Optional[PaddleSegSegmenter] = None,
) -> InferenceResult:
    """單一程式化入口：DICOM → native excursion 量測。

    Args:
        image_path: DICOM 檔絕對路徑（consumer 傳已儲存的 .dcm）
        phase: "excursion" / "sniff"；其他值 raise ValueError
        save_mask_dir: 給定時開啟 segmenter mask 輸出到此資料夾並回寫 mask_path；
            未給則不寫檔、mask_path=None
        segmenter: 注入 prepare_segmenter() 預載的 warm segmenter（跳過重載 model）；
            None 則內部 build+load（back-compat，適合一次性呼叫）

    Returns:
        InferenceResult（measurements 全 native；偵測不到 peak 回空 list，非錯誤）

    Raises:
        ValueError: phase 非法
        其他: 影像無法讀 / 非 DICOM 等由下層 load 拋出
    """
    phase_enum = _resolve_phase(phase)
    bundle = build_api_bundle(phase_enum)
    want_mask = save_mask_dir is not None

    if segmenter is None:
        # 內建路徑：config 設好再 load（back-compat）
        bundle.segmenter.save_predictions = want_mask
        if want_mask:
            bundle.segmenter.save_dir = save_mask_dir
        segmenter = PaddleSegSegmenter(bundle.segmenter)
        segmenter.load()
    else:
        # 注入的 warm segmenter：不重載，per-call 覆寫 mask 輸出設定
        segmenter.configure_output(
            save_predictions=want_mask,
            save_dir=save_mask_dir if want_mask else None,
        )

    seq = load(image_path)
    seq = apply_dicom_crop(seq, bundle.dicom_crop)
    if seq.source_type == "png_dir":
        raise NotImplementedError(
            "PNG dir → segmenter 整合尚未完成；analyze 目前只支援單檔 DICOM/PNG"
        )

    is_excursion = (phase_enum == Phase.EXCURSION)
    scale_y = seq.metadata.get("physical_delta_y")
    gray_frames = seq.as_gray()
    indices = get_legacy_frame_indices(bundle.multiframe, seq)

    measurements: List[ExcursionMeasurement] = []
    for i in indices:
        result = run_single_frame(
            seq, i, gray_frames[i], segmenter, bundle, is_excursion, scale_y,
        )
        measurements.extend(_to_measurement(p) for p in result.measurements)

    mask_path = (
        _resolve_mask_path(save_mask_dir, seq.source_path) if want_mask else None
    )
    return InferenceResult(
        measurements=measurements,
        mask_path=mask_path,
        model_version=MODEL_VERSION,
        frame_count=len(indices),
    )
