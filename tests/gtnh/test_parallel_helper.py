import math

import pytest
from pytest_check import check

from src.data.basicTypes import Ingredient, IngredientCollection
from src.gtnh.overclock_calculator import OverclockCalculator
from src.gtnh.parallel_helper import ParallelHelper
from src.gtnh.values import VoltageTier

recipe_input_ebf_steel_ingot = IngredientCollection(
    Ingredient("iron dust", 1),
    Ingredient("oxygen gas", 1000),
)


# Credit to: @Hermanoid, https://github.com/OrderedSet86/gtnh-flow/pull/39
@pytest.mark.parametrize(
    "machine_voltage,machine_heat,expected_eut,expected_dur,expected_parallel",
    [
        # No Overclocks (800K over recipe - no bonuses)
        (VoltageTier.MV, 1801, math.ceil(120 * 0.9), math.ceil(25 * 20 / 2.2), 1),
        # No Overclocks (1700K over recipe - one 5% heat bonus)
        (
            VoltageTier.MV,
            2701,
            math.ceil(120 * 0.9 * 0.95),
            math.ceil(25 * 20 / 2.2),
            1,
        ),
        # 4x voltage for volcanus is 4x parallels
        (VoltageTier.HV, 1801, math.ceil(120 * 4 * 0.9), math.ceil(25 * 20 / 2.2), 4),
        # EBF heat bonuses are applied after parallels are calculated
        # (so still only 4 parallels)
        (
            VoltageTier.HV,
            5401,
            math.ceil(120 * 4 * 0.9 * 0.95**4),
            math.ceil(25 * 20 / 2.2),
            4,
        ),
        # EV is enough for 16x parallels but capped to 8x. Not enough for overclock.
        (VoltageTier.EV, 1801, math.ceil(120 * 8 * 0.9), math.ceil(25 * 20 / 2.2), 8),
        # IV is enough for 8 parallels and 1 normal overclock.
        (
            VoltageTier.IV,
            1801,
            math.ceil(120 * 8 * 4 * 0.9),
            math.ceil(25 * 20 / 2.2 / 2),
            8,
        ),
        # 8 Parallel, 1 perfect oc (two 5% heat eut bonuses)
        (
            VoltageTier.IV,
            3601,
            math.ceil(120 * 8 * 4 * 0.9 * 0.95**2),
            math.ceil(25 * 20 / 2.2 / 4),
            8,
        ),
        # 8 Parallel, 1 perfect oc, 1 normal oc (two 5% heat eut bonuses)
        (
            VoltageTier.LUV,
            3601,
            math.ceil(120 * 8 * 4 * 4 * 0.9 * 0.95**2),
            math.floor(25 * 20 / 2.2 / 4 / 2),  # in game data
            8,
        ),
    ],
)
def test_volcanus_ebf_iron_dust_recipe(
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
    helper = ParallelHelper(
        calculator,
        IngredientCollection(
            Ingredient("iron dust", math.inf),
            Ingredient("oxygen gas", math.inf),
        ),
        recipe_input_ebf_steel_ingot,
        eut_modifier=0.9,
        max_parallel=8,
    )
    res_helper = helper.build()
    res_calc = res_helper.calculator_result
    dur = int(res_helper.duration_multiplier * res_calc.duration)
    eut = res_helper.recipe_voltage
    parallel = res_helper.parallel

    check.equal(eut, expected_eut)
    check.equal(dur, expected_dur)
    check.equal(parallel, expected_parallel)


recipe_centrifuge_black_granite = IngredientCollection(
    Ingredient("black granite dust", 5)
)


@pytest.mark.parametrize(
    "machine_voltage,input_amount,expected_eut,expected_dur,expected_parallel",
    [
        # Just enough input for 18 parallel
        (VoltageTier.HV, 90, 162, 178, 18),
        (VoltageTier.HV, 64, 432, 89, 12),
        # Just enough input for 24 parallel
        (VoltageTier.EV, 120, 864, 89, 24),
        (VoltageTier.EV, 100, 720, 89, 20),
        (VoltageTier.EV, 60, 1728, 44, 12),
        # Just enough input for 60 parallel
        (VoltageTier.UEV, 300, 2_211_840, 2, 60),
        (VoltageTier.UEV, 290, 2_138_112, 2, 58),
        (VoltageTier.UEV, 100, 2_949_120, 1, 20),
        # Just enough input for 66 parallel
        (VoltageTier.UIV, 330, 9_732_096, 1, 66),
        # Just enough input for 103 parallel
        (VoltageTier.UMV, 515, 42_467_328, 1, 103),
    ],
)
def test_industrial_centrifuge_black_granite_recipe(
    machine_voltage, input_amount, expected_eut, expected_dur, expected_parallel
):
    calculator = OverclockCalculator(
        10,
        20 * 20,
        machine_voltage,
        eut_discount=0.9,
        speed_boost=1 / 2.25,
    )
    helper = ParallelHelper(
        calculator,
        IngredientCollection(Ingredient("black granite dust", input_amount)),
        recipe_centrifuge_black_granite,
        eut_modifier=0.9,
        max_parallel=6 * VoltageTier(machine_voltage).number(),
    )
    res_helper = helper.build()
    res_calc = res_helper.calculator_result
    dur = int(res_helper.duration_multiplier * res_calc.duration)

    check.equal(expected_eut, res_helper.recipe_voltage)
    check.equal(expected_dur, dur)
    check.equal(expected_parallel, res_helper.parallel)


# LCR Recipe: 16x Biotite Dust + 16x Sodium Hydroxide Dust x16 + 4000x Water
#               -> 64x Sodium Aluminate Dust
recipe_input_lcr_sodium_al = IngredientCollection(
    Ingredient("biotite dust", 16),
    Ingredient("sodium hydroxide dust", 16),
    Ingredient("water", 4000),
)


@pytest.mark.parametrize(
    "max_parallel,biotite_amount,sodium_hydroxide_amount,water_amount,expected_parallel",
    (  # Enough for exactly 1
        (100, 16, 16, 4000, 1),
        # Enough for exactly 2
        (100, 32, 32, 8000, 2),
        # Enough for exactly 36
        (100, 576, 576, 144000, 36),
        # Not enough for 1, missing 1st dust input
        (100, 15, 16, 4000, 0),
        # Not enough for 1, missing 2nd dust input
        (100, 16, 15, 4000, 0),
        # Not enough for 1, missing fluid input
        (100, 16, 16, 3999, 0),
        # Not enough for 1, missing from both dust input
        (100, 15, 15, 4000, 0),
        # Not enough for 1, missing something from all input
        (100, 15, 15, 3999, 0),
        # more than 1 but not enough for 2 recipe
        (100, 16, 16, 5000, 1),
        (100, 20, 20, 5000, 1),
        # limited by max_parallel
        (1, 32, 32, 8000, 1),
        (20, 576, 576, 144000, 20),
    ),
)
def test_max_parallel_calculated_by_inputs(
    max_parallel,
    biotite_amount,
    sodium_hydroxide_amount,
    water_amount,
    expected_parallel,
):
    calculator = OverclockCalculator(480, 20 * 20, 512)
    helper = ParallelHelper(
        calculator,
        IngredientCollection(
            Ingredient("biotite dust", biotite_amount),
            Ingredient("sodium hydroxide dust", sodium_hydroxide_amount),
            Ingredient("water", water_amount),
        ),
        recipe_input_lcr_sodium_al,
    )

    assert expected_parallel == helper.max_parallel_calculated_by_inputs(max_parallel)
