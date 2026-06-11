"""
tests/test_measurement_type.py
==============================
MeasurementType resolver 單元測試（design §5/§9）。

scope：
- 純邏輯，無 DB / HTTP / pydicom
- 用注入的 test mapping 測 MachineModelResolver；production MACHINE_MODEL_MAP
  仍保持空（待工程師填機型表）
"""
import pytest

from services.measurement_type import (
    MACHINE_MODEL_MAP,
    ImageContentResolver,
    MachineModelResolver,
    MeasurementType,
    ResolveContext,
)

# key 在 model（ManufacturerModelName）—— manufacturer 不參與查表（2026-06-10 改）。
_TEST_MAP = {
    "DiaphragmScan 3000": MeasurementType.EXCURSION,
    "SniffMaster X": MeasurementType.SNIFF,
}


def test_known_device_resolves_to_mapped_type():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="AcmeUS", device_model="DiaphragmScan 3000")
    assert resolver.resolve(ctx) == MeasurementType.EXCURSION


def test_known_device_sniff():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="AcmeUS", device_model="SniffMaster X")
    assert resolver.resolve(ctx) == MeasurementType.SNIFF


def test_unknown_model_resolves_to_unknown():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="AcmeUS", device_model="Model Z")
    assert resolver.resolve(ctx) == MeasurementType.UNKNOWN


def test_resolves_by_model_even_when_manufacturer_missing():
    """key 只看 model；manufacturer 缺值不影響命中（2026-06-10 行為變更）。"""
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer=None, device_model="DiaphragmScan 3000")
    assert resolver.resolve(ctx) == MeasurementType.EXCURSION


def test_missing_model_resolves_to_unknown():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    assert resolver.resolve(ResolveContext()) == MeasurementType.UNKNOWN
    assert resolver.resolve(
        ResolveContext(device_manufacturer="AcmeUS", device_model=None)
    ) == MeasurementType.UNKNOWN


def test_model_is_whitespace_normalized():
    """DICOM strings are space-padded; lookup must still hit."""
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="AcmeUS", device_model="DiaphragmScan 3000 ")
    assert resolver.resolve(ctx) == MeasurementType.EXCURSION


def test_empty_string_model_resolves_to_unknown():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="AcmeUS", device_model="")
    assert resolver.resolve(ctx) == MeasurementType.UNKNOWN


def test_production_map_c62_is_excursion():
    """預設 production MACHINE_MODEL_MAP：C62 → excursion（工程師 2026-06-10 裁示）。"""
    resolver = MachineModelResolver()
    ctx = ResolveContext(device_manufacturer="AnyVendor", device_model="C62")
    assert resolver.resolve(ctx) == MeasurementType.EXCURSION


def test_production_map_l154_is_thickness():
    resolver = MachineModelResolver()
    ctx = ResolveContext(device_manufacturer="AnyVendor", device_model="L154")
    assert resolver.resolve(ctx) == MeasurementType.THICKNESS


def test_production_map_unknown_model_is_unknown():
    resolver = MachineModelResolver()
    ctx = ResolveContext(device_manufacturer="AnyVendor", device_model="NoSuchProbe")
    assert resolver.resolve(ctx) == MeasurementType.UNKNOWN


def test_production_map_contains_expected_models():
    assert MACHINE_MODEL_MAP["C62"] == MeasurementType.EXCURSION
    assert MACHINE_MODEL_MAP["L154"] == MeasurementType.THICKNESS


def test_measurement_type_enum_is_str_serializable():
    assert MeasurementType.EXCURSION == "excursion"
    assert MeasurementType.EXCURSION.value == "excursion"


def test_image_content_resolver_is_stub():
    with pytest.raises(NotImplementedError):
        ImageContentResolver().resolve(ResolveContext())
