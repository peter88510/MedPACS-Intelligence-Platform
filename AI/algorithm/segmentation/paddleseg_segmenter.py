"""PaddleSeg 的 SegmenterBase 實作。

封裝 paddleseglibs.predict.build_predictor + predict_one：
  - Model weights 在 load() 時載入一次
  - predict() 重複呼叫共用同一份權重（不再每次重 load）
  - 透過 PaddleSegSegmenterConfig 注入所有可控參數，與 algorithm 邏輯解耦
"""
from typing import Optional

import numpy as np
from PIL import Image

from algorithm.segmentation.base import SegmenterBase
from config.paddleseg_config import PaddleSegSegmenterConfig
from paddleseglibs.predict import build_predictor, predict_one


class PaddleSegSegmenter(SegmenterBase):
    def __init__(self, config: PaddleSegSegmenterConfig):
        self._cfg = config
        self._predictor = None

    def load(self) -> None:
        if self._predictor is not None:
            return
        self._predictor = build_predictor(
            config_path=self._cfg.config_path,
            model_path=self._cfg.model_path,
            device=self._cfg.device,
            save_dir=self._cfg.save_dir,
            resize_ratio=self._cfg.resize_ratio,
            aug_pred=self._cfg.aug_pred,
            scales=self._cfg.scales,
            flip_horizontal=self._cfg.flip_horizontal,
            flip_vertical=self._cfg.flip_vertical,
            is_slide=self._cfg.is_slide,
            stride=self._cfg.stride,
            crop_size=self._cfg.crop_size,
            custom_color=self._cfg.custom_color,
            save_predictions=self._cfg.save_predictions,
        )

    def configure_output(
        self,
        save_predictions: bool,
        save_dir: Optional[str] = None,
    ) -> None:
        """不重載模型，per-call 覆寫 mask 輸出設定（save_predictions / save_dir）。

        model 權重在 predictor['model']，與輸出無關，故覆寫不需重 build。供 warm
        segmenter（load 一次、跨呼叫共用）依每次請求切換 mask 輸出目的地用。

        注意：對共用 segmenter 並發呼叫不具 thread-safety（mutate predictor dict）；
        並發場景呼叫端需序列化，或每 worker 一個 segmenter。
        """
        self._cfg.save_predictions = save_predictions
        if save_dir is not None:
            self._cfg.save_dir = save_dir
        if self._predictor is not None:
            self._predictor['save_predictions'] = save_predictions
            if save_dir is not None:
                self._predictor['save_dir'] = save_dir

    def predict(
        self,
        image_path: str,
        dcm_array: Optional[np.ndarray] = None,
    ) -> Image.Image:
        if self._predictor is None:
            self.load()
        return predict_one(
            self._predictor,
            image_path=image_path,
            dcm_array=dcm_array,
            image_dir=None,
        )
