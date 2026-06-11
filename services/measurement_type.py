"""Measurement-type resolution (service layer).

Decides which diaphragm measurement a DICOM instance represents
(excursion / sniff / thickness) so the AI pipeline can pick the right
AI Phase downstream. Plugin architecture: the dispatch surface
(`MeasurementTypeResolver.resolve`) is stable; the MVP implementation
keys off device make/model, but an image-content classifier can be
swapped in later without changing callers.

Design: .work/ai_result_design.md §5. No FastAPI imports here (CLAUDE.md §6).
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Protocol

logger = logging.getLogger(__name__)


class MeasurementType(str, Enum):
    """Discriminator stored on ai_results.measurement_type."""
    EXCURSION = "excursion"
    SNIFF = "sniff"
    THICKNESS = "thickness"
    UNKNOWN = "unknown"


@dataclass
class ResolveContext:
    """Inputs a resolver may consult.

    MVP resolvers use the device fields only. pixel_array / extra are
    reserved forward-design slots for a future image-content classifier
    (excursion vs sniff vs thickness from the image itself) and carry no
    behaviour yet.
    """
    device_manufacturer: Optional[str] = None
    device_model: Optional[str] = None
    pixel_array: Optional[Any] = None  # reserved (ImageContentResolver)
    extra: Dict[str, Any] = field(default_factory=dict)


class MeasurementTypeResolver(Protocol):
    """Stable dispatch surface — implementations are interchangeable."""
    def resolve(self, ctx: ResolveContext) -> MeasurementType: ...


def _norm(value: Optional[str]) -> Optional[str]:
    """DICOM strings are space-padded; normalize before map lookup."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


# model (ManufacturerModelName, 0008,1090) -> MeasurementType。key 經 _norm 正規化。
# 只 key 在 model（不是 (manufacturer, model)）—— 工程師 2026-06-10 確認 0008,1090
# 內的 probe/model 代號就是判別依據；manufacturer 在此不是可靠 key。
# device_manufacturer 仍存進 Instance 供 audit，只是不用於查表。
#
# C62（convex probe）臨床上同時涵蓋 excursion 與 sniff；光靠 probe 代號無法區分
# 兩者（design §10 —— 需靠 image-content resolver）。依工程師 2026-06-10 裁示，
# C62 暫解析為 EXCURSION；sniff 的區分延到未來的 ImageContentResolver。
MACHINE_MODEL_MAP: Dict[str, MeasurementType] = {
    "C62": MeasurementType.EXCURSION,   # convex probe — 橫膈膜 excursion（M-mode）
    "L154": MeasurementType.THICKNESS,  # linear probe — 橫膈膜 thickness（B-mode）
}


class MachineModelResolver:
    """從 device model 解析 measurement type（MVP）。

    只 key 在正規化後的 ManufacturerModelName。未知或缺 model 一律解析為 UNKNOWN，
    AI endpoint 必須拒絕而非猜測（醫療安全，CLAUDE.md §10/§13）。
    """

    def __init__(
        self,
        mapping: Optional[Dict[str, MeasurementType]] = None,
    ) -> None:
        self._mapping = mapping if mapping is not None else MACHINE_MODEL_MAP

    def resolve(self, ctx: ResolveContext) -> MeasurementType:
        model = _norm(ctx.device_model)
        if model is None:
            logger.warning(
                "MeasurementType UNKNOWN: device_model missing "
                "(manufacturer=%r, model=%r)",
                ctx.device_manufacturer, ctx.device_model,
            )
            return MeasurementType.UNKNOWN

        mtype = self._mapping.get(model)
        if mtype is None:
            logger.warning(
                "MeasurementType UNKNOWN: model %r not in MACHINE_MODEL_MAP",
                model,
            )
            return MeasurementType.UNKNOWN
        return mtype


class ImageContentResolver:
    """Forward-design swap point: classify from pixel data, not device tags.

    Not implemented this round (design §8 downstream). Kept as an interface
    stub so dispatch wiring can target it later without churn.
    """

    def resolve(self, ctx: ResolveContext) -> MeasurementType:
        raise NotImplementedError(
            "ImageContentResolver is a forward-design stub; "
            "use MachineModelResolver for now (design §5/§8)."
        )
