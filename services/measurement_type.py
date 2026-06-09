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
from typing import Any, Dict, Optional, Protocol, Tuple

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


# (manufacturer, model) -> MeasurementType. Keys are normalized via _norm.
# Intentionally empty for now: the engineer supplies the real ultrasound
# machine -> measurement-type table (待澄清, design §10). Until filled,
# every device resolves to UNKNOWN, which the AI endpoint must reject
# rather than guess (medical safety, CLAUDE.md §10/§13).
MACHINE_MODEL_MAP: Dict[Tuple[str, str], MeasurementType] = {}


class MachineModelResolver:
    """Resolve measurement type from device make/model (MVP)."""

    def __init__(
        self,
        mapping: Optional[Dict[Tuple[str, str], MeasurementType]] = None,
    ) -> None:
        self._mapping = mapping if mapping is not None else MACHINE_MODEL_MAP

    def resolve(self, ctx: ResolveContext) -> MeasurementType:
        manufacturer = _norm(ctx.device_manufacturer)
        model = _norm(ctx.device_model)
        if manufacturer is None or model is None:
            logger.warning(
                "MeasurementType UNKNOWN: device tags missing "
                "(manufacturer=%r, model=%r)",
                ctx.device_manufacturer, ctx.device_model,
            )
            return MeasurementType.UNKNOWN

        mtype = self._mapping.get((manufacturer, model))
        if mtype is None:
            logger.warning(
                "MeasurementType UNKNOWN: device (%r, %r) not in MACHINE_MODEL_MAP",
                manufacturer, model,
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
