"""單 frame pipeline 純量核心（load/crop 已在外；本函式從 gray + segmenter 跑到 measurements）。

main.py（viz/timing wrapper）與 inference.py（facade）共用此核心：
    segment → detect → roi_band → motion_curve → excursion → compute_peak_info

本核心不碰 visualization、不 print。timing 為 duck-typed 可選參數（None 零影響），
不 import main（避免循環依賴）。seg_mask 寫入 FrameResult 供呼叫端 viz 使用。
"""
import time
from typing import Optional

import cv2
import numpy as np

from algorithm.diaphragm_detection import detect
from algorithm.excursion import brightness_way, compute_peak_info
from algorithm.frame_result import FrameResult
from algorithm.motion_curve import extract_motion_curve
from algorithm.roi_band import (
    compute_target_y_range,
    enhanced_search,
    select_target,
)
from algorithm.segmentation import PaddleSegSegmenter
from config import RunBundle


def run_single_frame(
    seq,
    i: int,
    gray: np.ndarray,
    segmenter: PaddleSegSegmenter,
    bundle: RunBundle,
    is_excursion: bool,
    scale_y,
    timing: Optional[object] = None,
) -> FrameResult:
    """LEGACY / GLOBAL_WINDOW / REALTIME-heavy 共用的純量單幀 pipeline。

    timing 非 None（REALTIME heavy 幀）時記錄 Layer heavy 各子步驟耗時；None 時零影響。
    viz 由呼叫端負責（seg_mask 回寫在 FrameResult）。
    """
    frame = seq.frames[i]

    t0 = time.perf_counter()
    mask_pil = segmenter.predict(
        image_path=seq.source_path,
        dcm_array=frame,
    )
    seg_mask = np.array(mask_pil.convert("L"), dtype=np.uint8)
    if timing is not None:
        timing.record("seg_predict", time.perf_counter() - t0)
        t0 = time.perf_counter()

    detection = detect(gray, bundle.detection, use_segment=seg_mask, timing=timing)

    y_band = compute_target_y_range(
        target_y_range=detection.best_region,
        image_height=gray.shape[0],
        reserve_ratio=bundle.roi_band.reserve_ratio,
    )
    if timing is not None:
        timing.record("detect_p1", time.perf_counter() - t0)

    # Patch 24A: use_segment_label=True 且 paddle pass1 成功時跳過 pass2 detect
    # （pass2 mask 在此 cfg 下不被 select_target 消費，省 ~36 ms/heavy frame）；
    # paddle 失敗（target_binary=None）或 use_segment_label=False 仍走完整 pass2
    skip_pass2 = (
        bundle.roi_band.use_segment_label
        and detection.target_binary is not None
    )
    refined = enhanced_search(           # 內部記 enhance / detect_p2（Layer roi）
        image_gray=gray,
        y_band=y_band,
        detection_config=bundle.detection,
        roi_band_config=bundle.roi_band,
        timing=timing,
        skip_detect=skip_pass2,
    )

    t_sel = time.perf_counter()
    selection = select_target(
        detection_pass1=detection,
        refined=refined,
        y_band=y_band,
        image_shape=gray.shape[:2],
        use_segment_label=bundle.roi_band.use_segment_label,
    )
    if timing is not None:
        now = time.perf_counter()
        timing.record("select", now - t_sel)
        timing.record("roi", now - t0)   # rollup（Layer heavy 的 roi 子層總計）
        t0 = now

    motion_curve = extract_motion_curve(
        image=cv2.medianBlur(gray, 7),
        y_range=y_band,
        config=bundle.motion_curve,
    )
    if timing is not None:
        timing.record("motion_curve", time.perf_counter() - t0)
        t0 = time.perf_counter()

    excursion = None
    measurements = []
    if is_excursion:
        excursion = brightness_way(
            diaphragm_mask=selection.diaphragm_mask,
            diaphragm_p_4crest=motion_curve.diaphragm_p_crest,
            diaphragm_p_4trough=motion_curve.diaphragm_p_trough,
            diaphragm_ori_y_value=motion_curve.init_diaphragm,
            config=bundle.excursion,
        )
        measurements = [
            compute_peak_info(
                crest=batch.crest_position,
                trough=batch.trough_position,
                scale_y=scale_y,
            )
            for batch in excursion.batches
        ]
    if timing is not None:
        timing.record("excursion_sf", time.perf_counter() - t0)

    return FrameResult(
        detection=detection,
        y_band=y_band,
        refined=refined,
        selection=selection,
        motion_curve=motion_curve,
        excursion=excursion,
        measurements=measurements,
        seg_mask=seg_mask,
    )
