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
    ImageContentResolver,
    MachineModelResolver,
    MeasurementType,
    ResolveContext,
)

_TEST_MAP = {
    ("AcmeUS", "DiaphragmScan 3000"): MeasurementType.EXCURSION,
    ("AcmeUS", "SniffMaster X"): MeasurementType.SNIFF,
}


def test_known_device_resolves_to_mapped_type():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="AcmeUS", device_model="DiaphragmScan 3000")
    assert resolver.resolve(ctx) == MeasurementType.EXCURSION


def test_known_device_sniff():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="AcmeUS", device_model="SniffMaster X")
    assert resolver.resolve(ctx) == MeasurementType.SNIFF


def test_unknown_device_resolves_to_unknown():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="NoSuch", device_model="Model Z")
    assert resolver.resolve(ctx) == MeasurementType.UNKNOWN


def test_missing_device_tags_resolve_to_unknown():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    assert resolver.resolve(ResolveContext()) == MeasurementType.UNKNOWN
    assert resolver.resolve(
        ResolveContext(device_manufacturer="AcmeUS", device_model=None)
    ) == MeasurementType.UNKNOWN


def test_device_tags_are_whitespace_normalized():
    """DICOM strings are space-padded; lookup must still hit."""
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="  AcmeUS ", device_model="DiaphragmScan 3000 ")
    assert resolver.resolve(ctx) == MeasurementType.EXCURSION


def test_empty_string_device_tags_resolve_to_unknown():
    resolver = MachineModelResolver(mapping=_TEST_MAP)
    ctx = ResolveContext(device_manufacturer="   ", device_model="")
    assert resolver.resolve(ctx) == MeasurementType.UNKNOWN


def test_default_production_map_is_empty_so_everything_unknown():
    """No injected mapping → uses (empty) MACHINE_MODEL_MAP → UNKNOWN."""
    resolver = MachineModelResolver()
    ctx = ResolveContext(device_manufacturer="AcmeUS", device_model="DiaphragmScan 3000")
    assert resolver.resolve(ctx) == MeasurementType.UNKNOWN


def test_measurement_type_enum_is_str_serializable():
    assert MeasurementType.EXCURSION == "excursion"
    assert MeasurementType.EXCURSION.value == "excursion"


def test_image_content_resolver_is_stub():
    with pytest.raises(NotImplementedError):
        ImageContentResolver().resolve(ResolveContext())
