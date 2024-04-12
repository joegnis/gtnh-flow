from copy import deepcopy

import pytest

from data.basicTypes import Ingredient as Ing, Recipe as Rec, IngredientCollection as IngCol
from gtnh.overclocks import OverclockHandler
from factory_graph import ProgramContext


def mod_recipe(recipe, **kwargs):
    modded = deepcopy(recipe)
    for k, v in kwargs.items():
        setattr(modded, k, v)
    return modded


@pytest.fixture
def overclock_handler():
    return OverclockHandler(ProgramContext())


recipe_sb_centrifuge = Rec(
    'centrifuge',
    'lv',
    IngCol(Ing('glass dust', 1)),
    IngCol(Ing('silicon dioxide', 1)),
    5,
    80
)


@pytest.mark.parametrize('recipe,expected', [
    (
        mod_recipe(recipe_sb_centrifuge, user_voltage='mv'),
        mod_recipe(recipe_sb_centrifuge, eut=20, dur=40),
    ),
    (
        mod_recipe(recipe_sb_centrifuge, user_voltage='hv'),
        mod_recipe(recipe_sb_centrifuge, eut=80, dur=20),
    )
])
def test_standardOverclock(recipe, expected, overclock_handler):
    overclocked = overclock_handler.overclockRecipe(recipe)
    assert overclocked.eut == expected.eut
    assert overclocked.dur == expected.dur


recipe_lcr = Rec(
    'large chemical reactor',
    'lv',
    IngCol(Ing('glass dust', 1)),
    IngCol(Ing('silicon dioxide', 1)),
    5,
    80
)


@pytest.mark.parametrize('recipe,expected', [
    (
        mod_recipe(recipe_lcr, user_voltage='mv'),
        mod_recipe(recipe_lcr, eut=20, dur=20)
    ),
    (
        mod_recipe(recipe_lcr, user_voltage='hv'),
        mod_recipe(recipe_lcr, eut=80, dur=5)
    ),
])
def test_perfectOverclock(recipe, expected, overclock_handler):
    overclocked = overclock_handler.overclockRecipe(recipe)
    assert overclocked.eut == expected.eut
    assert overclocked.dur == expected.dur


recipe_ebf = Rec(
    'electric blast furnace',
    'mv',
    IngCol(
        Ing('iron dust', 1),
        Ing('oxygen gas', 1000),
    ),
    IngCol(
        Ing('steel ingot', 1),
        Ing('tiny pile of ashes', 1),
    ),
    120,
    25,
    coils='cupronickel',
    heat=1000,
    circuit=11,
)


@pytest.mark.parametrize('recipe,expected', [
    # one normal OC
    (
        mod_recipe(recipe_ebf, user_voltage='hv', coils='kanthal'),  # 2701K
        mod_recipe(recipe_ebf, eut=120 * 4 * .95, dur=25 / 2)
    ),
    # one perfect OC
    (
        mod_recipe(recipe_ebf, user_voltage='hv', coils='nichrome'),  # 3601K
        mod_recipe(recipe_ebf, eut=120 * 4 * .95 ** 2, dur=25 / 4)
    ),
    # one normal OC plus one perfect OC
    (
        mod_recipe(recipe_ebf, user_voltage='ev', coils='nichrome'),  # 3601K
        mod_recipe(recipe_ebf, eut=120 * 16 * .95 ** 2, dur=25 / 4 / 2)
    ),
])
def test_EBFOverclock(recipe, expected, overclock_handler):
    overclocked = overclock_handler.overclockRecipe(recipe)
    assert overclocked.eut == expected.eut
    assert overclocked.dur == expected.dur


recipe_pyrolyse_oven = Rec(
    'pyrolyse oven',
    'mv',
    IngCol(
        Ing('oak wood', 16),
        Ing('nitrogen', 1000),
    ),
    IngCol(
        Ing('charcoal', 20),
        Ing('wood tar', 1500),
    ),
    96,
    16,
    coils='cupronickel',
    circuit=10
)


@pytest.mark.parametrize('recipe,expected', [
    # speed penalty
    (
        mod_recipe(recipe_pyrolyse_oven),
        mod_recipe(recipe_pyrolyse_oven, dur=16 / 0.5)
    ),
    # no penalty & no bonus
    (
        mod_recipe(recipe_pyrolyse_oven, coils='kanthal'),
        mod_recipe(recipe_pyrolyse_oven, dur=16)
    ),
    # speed bonus
    (
        mod_recipe(recipe_pyrolyse_oven, coils='nichrome'),
        mod_recipe(recipe_pyrolyse_oven, dur=16 / 1.5)
    ),
    # speed bonus & OC
    (
        mod_recipe(recipe_pyrolyse_oven, coils='nichrome', user_voltage='hv'),
        mod_recipe(recipe_pyrolyse_oven, eut=96 * 4, dur=16 / 2 / 1.5)
    )
])
def test_pyrolyseOverclock(recipe, expected, overclock_handler):
    overclocked = overclock_handler.overclockRecipe(recipe)
    assert overclocked.eut == expected.eut
    assert overclocked.dur == expected.dur
