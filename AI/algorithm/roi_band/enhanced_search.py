"""Enhanced search：強化 ROI band → median blur → 第二次 detect。

對應原 patch_code 兩次 detect_diaphragm 中的第二次：
  - 不用 use_segment（走 classical 路徑）
  - filter_top_ratio=0、median_blur=False（強化與 blur 已外部處理；
    若再 filter 上方 100 行會把 band 切空）

回傳 RoiSearchResult 取代原版散落的命名 (diaphragm_mask / target_binary_fun /
detect_diaphragm_image / padded_image / padded_image2)。
"""
import time
from dataclasses import dataclass, replace
from typing import Tuple

import cv2
import numpy as np

from algorithm.diaphragm_detection import DetectionResult, detect
from algorithm.roi_band.enhancement import enhance_band
from config import DiaphragmDetectionConfig, RoiBandConfig


@dataclass
class RoiSearchResult:
    detection: DetectionResult      # 第二次 detect 的完整輸出
    enhanced_band: np.ndarray       # 強化後小尺寸 (band_h, w)
    enhanced_padded: np.ndarray     # 強化後 zero-pad 回原圖大小 (h, w)（給合成 viz / 後續處理）
    padded_mask: np.ndarray         # detection.filtered_binary 還原到原圖大小 (h, w)
    padded_overlay: np.ndarray      # detection.debug_overlay 還原到原圖大小 (h, w, 3)


def enhanced_search(
    image_gray: np.ndarray,
    y_band: Tuple[int, int],
    detection_config: DiaphragmDetectionConfig,
    roi_band_config: RoiBandConfig,
    timing=None,
    skip_detect: bool = False,
) -> RoiSearchResult:
    """強化 ROI band 後在 band 內再做一次 detect，把結果還原回原圖大小。

    Args:
        image_gray: 2D gray uint8 原圖
        y_band: compute_target_y_range 算出的 (y_min, y_max)
        detection_config: 主 DiaphragmDetectionConfig。內部會 replace 出
                          filter_top_ratio=0、median_blur=False 的 second pass 變體，
                          不污染外部 config 物件
        roi_band_config: 提供 enhance_num_segments、enhance_blur_kernel
        timing: 可選的計時累計器（duck-typed，需有 record(stage, dt)）。非 None 時
                記錄 enhance / detect_p2 子步驟（REALTIME Layer roi profiling）；None 零影響
        skip_detect: True 時跳過 median blur + 第二次 detect（Patch 24A：caller
                     確定不消費 pass2 mask 時用；enhance 仍跑保 viz overlay）。
                     stub 回傳：detection.target_binary=None、padded_mask/overlay=zeros

    Returns:
        RoiSearchResult
    """
    # 1. 強化（無論 skip 與否都跑，給 viz 用，~0.5 ms 開銷）
    t = time.perf_counter()
    enhanced_padded, enhanced = enhance_band(
        image_gray, y_band, num_segments=roi_band_config.enhance_num_segments)
    if timing is not None:
        timing.record("enhance", time.perf_counter() - t)

    h, w = image_gray.shape[:2]

    # 2. skip 短路：caller（如 paddle pass1 已成功）不消費 pass2 mask 時
    if skip_detect:
        stub_detection = DetectionResult(
            best_region=(0, 0),
            filtered_binary=np.zeros((h, w), dtype=np.uint8),
            target_binary=None,
            potential_binary=None,
            debug_overlay=np.zeros((h, w, 3), dtype=np.uint8),
        )
        return RoiSearchResult(
            detection=stub_detection,
            enhanced_band=enhanced,
            enhanced_padded=enhanced_padded,
            padded_mask=np.zeros((h, w), dtype=np.uint8),
            padded_overlay=np.zeros((h, w, 3), dtype=np.uint8),
        )

    # 3. median blur + 第二次 detect 的 config 變體（不重複 preprocessing）
    t = time.perf_counter()
    enhanced_blurred = cv2.medianBlur(enhanced, roi_band_config.enhance_blur_kernel)
    second_pass_cfg = replace(
        detection_config, filter_top_ratio=0, median_blur=False)
    detection = detect(enhanced_blurred, second_pass_cfg, timing=timing)
    if timing is not None:
        timing.record("detect_p2", time.perf_counter() - t)

    # 4. Zero-pad 還原到原圖大小
    y_min, y_max = y_band
    padded_mask = np.zeros((h, w), dtype=np.uint8)
    padded_overlay = np.zeros((h, w, 3), dtype=np.uint8)
    padded_mask[y_min:y_max, :] = detection.filtered_binary
    padded_overlay[y_min:y_max, :, :] = detection.debug_overlay

    return RoiSearchResult(
        detection=detection,
        enhanced_band=enhanced,
        enhanced_padded=enhanced_padded,
        padded_mask=padded_mask,
        padded_overlay=padded_overlay,
    )
