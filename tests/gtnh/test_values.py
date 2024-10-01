import pytest

from src.gtnh.values import VoltageTier


@pytest.mark.parametrize(
    "tier,expected_voltage",
    [
        (1, VoltageTier.LV),
        (15, VoltageTier.MAX_PLUS),
        (4, VoltageTier.EV),
        ("LV", VoltageTier.LV),
        ("LuV", VoltageTier.LUV),
        ("ev", VoltageTier.EV),
    ],
)
def test_voltage_tier_get_by_index(tier, expected_voltage):
    assert expected_voltage == VoltageTier[tier]


@pytest.mark.parametrize(
    "tier,expected_err",
    [
        ("abc", KeyError),
        (-1, KeyError),
        (16, KeyError),
        (20, KeyError),
        (-10, KeyError),
    ],
)
def test_voltage_tier_get_by_index_errors(tier, expected_err):
    with pytest.raises(expected_err):
        VoltageTier[tier]


@pytest.mark.parametrize(
    "voltage,expected_tier",
    [
        (1, VoltageTier.ULV),
        (8_589_934_592, VoltageTier.MAX_PLUS),
        (50, VoltageTier.MV),
        (3000, VoltageTier.IV),
        (33_554_432, VoltageTier.UIV),
        (33_554_433, VoltageTier.UMV),
    ],
)
def test_voltage_tier_get_voltage_tier(voltage, expected_tier):
    assert expected_tier == VoltageTier(voltage)


@pytest.mark.parametrize(
    "voltage,expected_error",
    [
        (0, ValueError),
        (8_589_934_593, ValueError),
    ],
)
def test_voltage_tier_get_voltage_tier_errors(voltage, expected_error):
    with pytest.raises(expected_error):
        VoltageTier(voltage)


@pytest.mark.parametrize(
    "voltage,expected_num",
    [
        (VoltageTier.ULV, 0),
        (VoltageTier.MAX_PLUS, 15),
        (VoltageTier.EV, 4),
    ],
)
def test_voltage_tier_to_number(voltage, expected_num):
    assert expected_num == voltage.number()
