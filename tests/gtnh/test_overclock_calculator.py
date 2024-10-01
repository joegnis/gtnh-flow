import math

import pytest
from pytest_check import check

from src.gtnh.overclock_calculator import OverclockCalculator
from src.gtnh.values import VoltageTier


@pytest.mark.parametrize(
    (
        "recipe_eut,recipe_dur,recipe_heat,"
        "machine_voltage,machine_heat,"
        "expected_dur,expected_eut"
    ),
    [
        # perfect OC: at recipe heat requirement + 1800 * 4
        (
            VoltageTier.LV.practical(),
            1024,
            1800,
            VoltageTier.IV,
            1800 * 5,
            1024 >> 8,
            math.ceil(VoltageTier.IV.practical() * math.pow(0.95, (1800 * 4) / 900)),
        ),
        # imperfect OC: at recipe heat requirement + 900
        (
            VoltageTier.LV.practical(),
            1024,
            1800,
            VoltageTier.IV,
            2700,
            1024 >> 4,
            math.ceil(VoltageTier.IV.practical() * math.pow(0.95, 1)),
        ),
        # imperfect OC: only at recipe heat requirement
        (
            VoltageTier.LV.practical(),
            1024,
            1800,
            VoltageTier.IV,
            1800,
            1024 >> 4,
            math.ceil(VoltageTier.IV.practical() * math.pow(0.95, 0)),
        ),
        # perfect OC: at recipe heat requirement + 1800
        (
            VoltageTier.LV.practical(),
            1024,
            1800,
            VoltageTier.IV,
            3600,
            1024 >> 5,
            math.ceil(VoltageTier.IV.practical() * math.pow(0.95, 2)),
        ),
    ],
)
def test_calculate_EBF(
    recipe_eut,
    recipe_dur,
    recipe_heat,
    machine_voltage,
    machine_heat,
    expected_dur,
    expected_eut,
):
    calculator = OverclockCalculator(
        recipe_eut,
        recipe_dur,
        machine_voltage,
        does_heat_oc=True,
        has_heat_discount=True,
        recipe_heat=recipe_heat,
        machine_heat=machine_heat,
    )
    calculator.validate()
    res = calculator.calculate()

    check.equal(expected_dur, res.duration)
    check.equal(expected_eut, res.recipe_voltage)
