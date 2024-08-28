import math

import pytest

from src.gtnh.overclock_calculator import OverclockCalculator
from src.gtnh.parallel_helper import ParallelHelper
from src.gtnh.values import Voltage


@pytest.mark.parametrize(
    "machine_voltage,machine_heat,expected_eut,expected_dur,expected_parallel",
    [
        # No Overclocks (800K over recipe - no bonuses)
        (Voltage.MV, 1801, math.ceil(120 * 0.9), math.ceil(25 * 20 / 2.2), 1),
        # No Overclocks (1700K over recipe - one 5% heat bonus)
        (Voltage.MV, 2701, math.ceil(120 * 0.9 * 0.95), math.ceil(25 * 20 / 2.2), 1),
        # 4x voltage for volcanus is 4x parallels
        (Voltage.HV, 1801, math.ceil(120 * 4 * 0.9), math.ceil(25 * 20 / 2.2), 4),
        # EBF heat bonuses are applied after parallels are calculated
        # (so still only 4 parallels)
        (
            Voltage.HV,
            5401,
            math.ceil(120 * 4 * 0.9 * 0.95**4),
            math.ceil(25 * 20 / 2.2),
            4,
        ),
        # EV is enough for 16x parallels but capped to 8x. Not enough for overclock.
        (Voltage.EV, 1801, math.ceil(120 * 8 * 0.9), math.ceil(25 * 20 / 2.2), 8),
        # IV is enough for 8 parallels and 1 normal overclock.
        (
            Voltage.IV,
            1801,
            math.ceil(120 * 8 * 4 * 0.9),
            math.ceil(25 * 20 / 2.2 / 2),
            8,
        ),
        # 8 Parallel, 1 perfect oc (two 5% heat eut bonuses)
        (
            Voltage.IV,
            3601,
            math.ceil(120 * 8 * 4 * 0.9 * 0.95**2),
            math.ceil(25 * 20 / 2.2 / 4),
            8,
        ),
        # 8 Parallel, 1 perfect oc, 1 normal oc (two 5% heat eut bonuses)
        (
            Voltage.LuV,
            3601,
            math.ceil(120 * 8 * 4 * 4 * 0.9 * 0.95**2),
            math.floor(25 * 20 / 2.2 / 4 / 2),  # in game data
            8,
        ),
    ],
)
def test_build_volcanus_ebf_iron_dust_recipe(
    machine_voltage, machine_heat, expected_eut, expected_dur, expected_parallel
):
    calculator = OverclockCalculator(
        120,
        25 * 20,
        machine_voltage,
        does_heat_oc=True,
        has_heat_discount=True,
        recipe_heat=1000,
        machine_heat=machine_heat,
        eut_discount=0.9,
        speed_boost=1.0 / 2.2,
    )
    helper = ParallelHelper(calculator, eut_modifier=0.9, max_parallel=8)
    res_helper = helper.build()
    res_calc = res_helper.calculator_result
    dur = int(res_helper.duration_multiplier * res_calc.duration)
    eut = res_helper.recipe_voltage
    parallel = res_helper.parallel

    assert eut == expected_eut
    assert dur == expected_dur
    assert parallel == expected_parallel
