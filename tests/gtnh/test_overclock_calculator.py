import math

import pytest

from src.gtnh.overclock_calculator import OverclockCalculator
from src.gtnh.values import Voltage


@pytest.mark.parametrize(
    (
        "recipe_eut,recipe_dur,recipe_heat,"
        "machine_voltage,machine_heat,"
        "expected_dur,expected_eut"
    ),
    [
        # perfect OC: at recipe heat requirement + 1800 * 4
        (
            Voltage.LV.practical(),
            1024,
            1800,
            Voltage.IV,
            1800 * 5,
            1024 >> 8,
            math.ceil(Voltage.IV.practical() * math.pow(0.95, (1800 * 4) / 900)),
        ),
        # imperfect OC: at recipe heat requirement + 900
        (
            Voltage.LV.practical(),
            1024,
            1800,
            Voltage.IV,
            2700,
            1024 >> 4,
            math.ceil(Voltage.IV.practical() * math.pow(0.95, 1)),
        ),
        # imperfect OC: only at recipe heat requirement
        (
            Voltage.LV.practical(),
            1024,
            1800,
            Voltage.IV,
            1800,
            1024 >> 4,
            math.ceil(Voltage.IV.practical() * math.pow(0.95, 0)),
        ),
        # perfect OC: at recipe heat requirement + 1800
        (
            Voltage.LV.practical(),
            1024,
            1800,
            Voltage.IV,
            3600,
            1024 >> 5,
            math.ceil(Voltage.IV.practical() * math.pow(0.95, 2)),
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

    assert res.duration == expected_dur
    assert res.recipe_voltage == expected_eut
