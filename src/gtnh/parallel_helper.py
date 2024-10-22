import math
from dataclasses import KW_ONLY, dataclass, field

from src.data.basicTypes import IngredientCollection

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
    Calculates the number of parallel and changes to overclocking after parallel.

    Instantiate this class with proper arguments,
    and call `calculate()` to get results.
    After that, if we want to change calculation parameters,
    change public members (those without leading `_`),
    call public method, and etc,
    verify the changes by calling `validate()`,
    and finally call `calculate()` again.

    Design philosophy is similar to that of `OverclockCalculator`.

    A rewrite of the following class in GT5-Unofficial repo:
    - gregtech/api/util/GT_ParallelHelper.java
    - GTNH version: 2.6.1
    - GT5-Unofficial version: 5.09.45.168
    - GT5-Unofficial Commit: 9ec067dc13f9ef7aff30fcc0ee3244f22bd76dd7
    """

    # Only code changed from source is documented.
    # Refer to Java code for more documentation.
    # Batch mode related code is skipped for now.

    # Refer to OverclockCalculator's documents and comments to see
    # what and why I change from Java source code.

    # required arguments in __init__
    calculator: OverclockCalculator
    ingredient_inputs: IngredientCollection
    recipe_inputs: IngredientCollection

    _: KW_ONLY
    eut_modifier: float = 1.0
    max_parallel: int = 1

    # Init-only variables
    # Private variables
    _actual_recipe_eut: int = field(init=False)
    _available_eut: int = field(init=False)
    _duration_multiplier: float = field(default=1.0, init=False)
    # Removed since it is only used in build()
    # current_parallel: int = -1
    # Removed since it is only used in build()
    # max_parallel: int = 1

    def __post_init__(self) -> None:
        self.validate()

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

        Equivalent to the methods in Java:
        - `build()`
        - `determineParallel()`
        """
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

        # SingleRecipeCheck is for machines locked into a recipe,
        # which we should not worry about
        # if (recipeCheck != null)
        current_parallel = self.max_parallel_calculated_by_inputs(actual_max_parallel)
        # current_parallel = actual_max_parallel
        eut_use_after_oc = self.calculator.calculate_eut_consumption_under_one_tick(
            ORIG_MAX_PARALLEL, current_parallel
        )
        self.calculator.parallel = min(current_parallel, ORIG_MAX_PARALLEL)
        self.calculator.validate()
        res_calc = self.calculator.calculate()
        # In Java, calculator results might be changed here:
        #     calculator.setRecipeEUt(eutUseAfterOC);
        # Here we don't modify calculator object directly,
        # but instead we include the changed values in the return value
        recipe_voltage = res_calc.recipe_voltage
        if current_parallel > ORIG_MAX_PARALLEL:
            recipe_voltage = eut_use_after_oc

        duration_multiplier = 1.0

        # if (calculateOutputs && currentParallel > 0)
        # ..
        return ParallelHelperResult(
            parallel=current_parallel,
            recipe_voltage=recipe_voltage,
            duration_multiplier=duration_multiplier,
            calculator_result=res_calc,
        )

    def max_parallel_calculated_by_inputs(self, max_parallel: int) -> int:
        """
        Calculates max parallel by considering `max_parallel` argument,
        the quantities of input ingredients, and the quantities of recipe input.

        Equivalent to the Java implementation of
        `GT_Recipe.maxParallelCalculatedByInputs()`.
        This rewrite does not try to follow the implementation exactly,
        only simulating its results.
        In `determineParallel()` in Java, its return value is cast to `int`,
        so it actually doesn't need to return a double.
        """
        # find the smallest input/recipe_input ratio
        smallest_ratio = math.inf
        for ing_recipe in self.recipe_inputs:
            if ing_recipe.name not in self.ingredient_inputs:
                return 0
            ing_input = self.ingredient_inputs[ing_recipe.name]
            recipe_input = self.recipe_inputs[ing_recipe.name]
            ratio = sum(ing_input) / sum(recipe_input)
            if ratio < smallest_ratio:
                smallest_ratio = ratio
        return min(
            max_parallel,
            math.floor(smallest_ratio) if smallest_ratio != math.inf else max_parallel,
        )
