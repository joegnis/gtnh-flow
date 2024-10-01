import math
from dataclasses import KW_ONLY, InitVar, dataclass, field
from typing import ClassVar

from .overclock_calculator import OverclockCalculator, OverclockCalculatorResult


@dataclass
class ParallelHelperResult:
    parallel: int
    recipe_voltage: int
    duration_multiplier: float
    calculator_result: OverclockCalculatorResult


@dataclass(eq=False)
class ParallelHelper:
    """
    ParallelHelper
    """

    # Mirrors the following class in Java source code:
    # - Source: gregtech/api/util/GT_ParallelHelper.java
    # - GTNH version: 2.6.1
    # - Commit: 9ec067dc13f9ef7aff30fcc0ee3244f22bd76dd7
    # Only code changed from source is documented.
    # Refer to Java code for more documentation.

    # joegnis:
    # Refer to OverclockCalculator's documents and comments to see
    # what and why I change from Java source code.

    MAX_BATCH_MODE_TICK_TIME: ClassVar[int] = 128

    # required arguments in __init__
    calculator: OverclockCalculator

    _: KW_ONLY
    eut_modifier: float = 1.0
    max_parallel: int = 1

    # Init-only variables
    # Complements enable_batch_mode()
    batch_modifier: InitVar[int] = 1

    # Private variables
    _actual_recipe_eut: int = field(init=False)
    _available_eut: int = field(init=False)
    _duration_multiplier: float = field(default=1.0, init=False)
    _is_batch_mode_on: bool = field(default=False, init=False)
    _batch_modifier: int = field(default=1, init=False)
    # Removed since it is only used in build()
    # current_parallel: int = -1
    # Removed since it is only used in build()
    # max_parallel: int = 1

    def __post_init__(self, batch_modifier: int) -> None:
        self.enable_batch_mode(batch_modifier)
        self.validate()
        self.build()

    def enable_batch_mode(self, batch_modifier) -> None:
        if batch_modifier > 1:
            self._is_batch_mode_on = True
            self._batch_modifier = batch_modifier

    def validate(self) -> None:
        """
        Validates parameters for `build()`.
        """
        recipe_eut = self.calculator.recipe_voltage
        self._actual_recipe_eut = math.ceil(recipe_eut * self.eut_modifier)
        self._available_eut = (
            self.calculator.machine_voltage * self.calculator.machine_amperage
        )
        if self._actual_recipe_eut > self._available_eut:
            raise ValueError("Not enough machine power")

    def build(self) -> ParallelHelperResult:
        """
        Does the calculation.

        Call `validate()` before this to validate parameters.
        """
        # Mirrors Java implementation of:
        # - build()
        # - determineParallel()
        # Some comments indicate which Java code is skipped

        if self.max_parallel <= 0:
            return ParallelHelperResult(0, 0, 0.0, OverclockCalculatorResult(0, 0, 0))

        # Our inputs are assumed to be infinite
        # if (itemInputs == null)
        # if (fluidInputs == null)

        # Consuming or not doesn't matter in our calculation
        # if (!consume)

        # It assumes we always have a calculator,
        # since it is a required argument in __init__
        # if (calculator == null)

        # tRecipeEUt in Java
        # check moved to __post_init__
        # if (availableEUt < tRecipeEUt)

        ORIG_MAX_PARALLEL = self.max_parallel
        max_parallel = self.max_parallel
        self.calculator.parallel = ORIG_MAX_PARALLEL
        tick_time_after_oc = self.calculator.calculate_duration_under_one_tick()
        if tick_time_after_oc < 1:
            max_parallel = int(max_parallel / tick_time_after_oc)

        max_parallel_before_batch_mode = max_parallel
        if self._is_batch_mode_on:
            max_parallel *= self._batch_modifier

        # final ItemStack[] truncatedItemOutputs = recipe.mOutputs != null
        # final FluidStack[] truncatedFluidOutputs = ...

        # We don't have recipe check so it is skipped

        # We don't have void protection so it is skipped

        actual_max_parallel = max_parallel_before_batch_mode
        if self._actual_recipe_eut > 0:
            actual_max_parallel = min(
                max_parallel_before_batch_mode,
                int(self._available_eut / self._actual_recipe_eut),
            )

        # if (recipeCheck != null)
        # ...
        # It assumes that we have infinite input
        # joegnis:
        # This condition calls either
        # - gregtech/api/recipe/check/SingleRecipeCheck.java:checkRecipeInputs()
        # - gregtech/api/util/GT_Recipe.java:maxParallelCalculatedByInputs()
        # They both calculate parallel by getting the smallest of
        # `currentParallel` (argument) and item/fluid amount.
        # Therefore if we assume we have infinite input,
        # the result should always be `currentParallel`
        current_parallel = actual_max_parallel

        eut_use_after_oc = self.calculator.calculate_eut_consumption_under_one_tick(
            ORIG_MAX_PARALLEL, current_parallel
        )
        self.calculator.parallel = min(current_parallel, ORIG_MAX_PARALLEL)
        self.calculator.validate()
        res_calc = self.calculator.calculate()
        # In Java, calculator results might be changed here:
        #     calculator.setRecipeEUt(eutUseAfterOC);
        # Here we don't modify calculator object directly,
        # but instead we include the changed value in return value
        recipe_voltage = res_calc.recipe_voltage
        if current_parallel > ORIG_MAX_PARALLEL:
            recipe_voltage = eut_use_after_oc

        duration_multiplier = 1.0
        if (
            self._is_batch_mode_on
            and current_parallel > 0
            and res_calc.duration < self.MAX_BATCH_MODE_TICK_TIME
        ):
            batch_multiplier_max = int(
                self.MAX_BATCH_MODE_TICK_TIME / res_calc.duration
            )
            MAX_EXTRA_PARALLELS = math.floor(
                min(
                    current_parallel
                    * min(batch_multiplier_max - 1, self._batch_modifier - 1),
                    max_parallel - current_parallel,
                )
            )
            # Skipped recipe check
            extra_parallels = MAX_EXTRA_PARALLELS
            duration_multiplier = 1 + extra_parallels / current_parallel
            current_parallel += extra_parallels

        # if (calculateOutputs && currentParallel > 0)
        # ..
        return ParallelHelperResult(
            parallel=current_parallel,
            recipe_voltage=recipe_voltage,
            duration_multiplier=duration_multiplier,
            calculator_result=res_calc,
        )
