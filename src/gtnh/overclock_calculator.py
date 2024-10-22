import math
from dataclasses import KW_ONLY, InitVar, dataclass, field
from typing import ClassVar

from . import values


@dataclass
class OverclockCalculatorResult:
    duration: int
    recipe_voltage: int
    overclock_count: int


@dataclass(eq=False)
class OverclockCalculator:
    """
    Calculates overclocking of a recipe.

    Instantiate this class with proper arguments,
    and call `calculate()` to get results.
    After that, if we want to change calculation parameters,
    modify public members (those without leading `_`),
    call public method, and etc,
    verify the changes by calling `validate()`,
    and finally call `calculate()` again.

    Different from Java code, instantiation is not done by
    calling various setters and then calling `calculate()`.
    Instead, all init arguments are passed into constructor.
    As special cases,
    some setters in Java modify more than one member variables:
    1. `enablePerfectOC()`.
        Use boolean constructor argument `enables_perfect_oc` or
        call method `enable_perfect_oc()`
    2. `limitOverclockCount()`.
        Use int constructor argument `limitOverclockCount` or
        call method `limit_overclock_counts()`

    Also different from Java code,
    calculation results are not stored by changing inner states.
    Results are in return value instead.
    The major benefit is that it makes it easier
    to figure out what the code is doing.

    A rewrite of the following class in GT5-Unofficial repo:
    - gregtech/api/util/GT_OverclockCalculator.java
    - GTNH version: 2.6.1
    - GT5-Unofficial version: 5.09.45.168
    - GT5-Unofficial commit: 9ec067dc13f9ef7aff30fcc0ee3244f22bd76dd7
    """

    # Only code changed from source is documented.
    # Refer to Java code for more documentation.

    # `@dataclass` decorator helps generate an `__init__` method
    # automatically from member variable declaration.
    # Private Java methods are prefixed with an underscore in Python.
    # Most of Java methods "calculateX" are shortened to "X" in Python.
    HEAT_DISCOUNT_THRESHOLD: ClassVar[int] = 900
    HEAT_PERFECT_OVERCLOCK_THRESHOLD: ClassVar[int] = 1800

    # required arguments in __init__
    recipe_voltage: int
    duration: int
    machine_voltage: int

    # Keyword-only arguments in __init__
    _: KW_ONLY
    recipe_amperage: int = 1
    machine_amperage: int = 1
    parallel: int = 1
    speed_boost: float = 1.0
    does_not_overclock: bool = False
    eut_discount: float = 1.0
    eut_increase_per_oc: int = 4
    duration_decrease_per_oc: int = 2
    has_one_tick_discount: bool = False

    does_amperage_oc: bool = False
    does_laser_oc: bool = False
    laser_oc_penalty: float = 0.3

    does_heat_oc: bool = False
    recipe_heat: int = 0
    machine_heat: int = 0
    duration_decrease_per_heat_oc: int = 4
    has_heat_discount: bool = False
    # In Java, it is called heatDiscountExponent,
    # but it is actually the base in exponentiation
    heat_discount_multi: float = 0.95

    # Init-only variables
    # Complements `enable_perfect_oc()`
    enables_perfect_oc: InitVar[bool] = False
    # Complements `limit_overclock_counts()`
    max_oc_count: InitVar[int] = -1
    # Removed from members (see calculate())
    # _overclock_count
    # Removed from members (see calculate())

    # The following variables are removed from members
    # as they are only used locally
    # heat_overclock_count
    # overclock_count

    # Private variables
    _limits_overclocks: bool = field(default=False, init=False)
    _max_overclocks: int = field(default=0, init=False)
    # _overclock_count

    def enable_perfect_oc(self):
        self.duration_decrease_per_oc = 4

    def limit_overclock_counts(self, max_overclocks: int):
        self._limits_overclocks = True
        self._max_overclocks = max_overclocks

    def __post_init__(self, enables_perfect_oc, max_oc_count) -> None:
        if enables_perfect_oc:
            self.enable_perfect_oc()
        if max_oc_count >= 0:
            self.limit_overclock_counts(max_oc_count)
        self.validate()

    def validate(self) -> None:
        """
        Validates parameters for `calculate()`.
        """
        if self.does_laser_oc and self.does_amperage_oc:
            raise ValueError(
                "Tried to create an OverclockHandler "
                "with both laser and amperage overclocking"
            )
        if self.duration_decrease_per_oc <= 0:
            raise ValueError("Duration decrease can't be a negative number or zero")
        if self.duration_decrease_per_heat_oc <= 0:
            raise ValueError("Heat OC can't be a negative number or zero")
        if self.eut_increase_per_oc <= 0:
            raise ValueError("EUt increase can't be a negative number or zero")

    def calculate(self) -> OverclockCalculatorResult:
        """
        Does the calculation.

        Call `validate()` before this to verify parameters.

        Equivalent to the methods in Java:
        - calculate()
        - calculateOverclock()
        """
        # Some comments indicate which Java code is skipped

        duration = math.ceil(self.duration * self.speed_boost)
        recipe_voltage = self.recipe_voltage
        heat_overclock_count = 0

        if self.does_not_overclock:
            recipe_voltage = self._final_recipe_eut(
                recipe_voltage, self._heat_discount_multiplier()
            )
            return OverclockCalculatorResult(
                duration=duration, recipe_voltage=recipe_voltage, overclock_count=0
            )

        # "laserOC && amperageOC" check moved to __post_init__

        heat_discount_multiplier = self._heat_discount_multiplier()
        if self.does_heat_oc:
            heat_overclock_count = self._amount_of_heat_overclocks()

        recipe_power_tier = self._recipe_power_tier(heat_discount_multiplier)
        machine_power_tier = self._machine_power_tier()

        overclock_count = self._amount_of_needed_overclocks(
            machine_power_tier, recipe_power_tier
        )
        if not self.does_amperage_oc:
            overclock_count = min(
                overclock_count, self._recipe_to_machine_voltage_diff()
            )
        overclock_count = max(overclock_count, 0)
        if self._limits_overclocks:
            overclock_count = min(self._max_overclocks, overclock_count)

        heat_overclock_count = min(heat_overclock_count, overclock_count)
        recipe_voltage = math.floor(
            recipe_voltage * math.pow(self.eut_increase_per_oc, overclock_count)
        )
        duration = math.floor(
            duration
            / math.pow(
                self.duration_decrease_per_oc,
                overclock_count - heat_overclock_count,
            )
        )
        duration = math.floor(
            duration
            / math.pow(self.duration_decrease_per_heat_oc, heat_overclock_count)
        )
        if self.has_one_tick_discount:
            self.recipe_voltage = math.floor(
                self.recipe_voltage
                / math.pow(
                    self.duration_decrease_per_oc,
                    int(machine_power_tier - recipe_power_tier - overclock_count),
                )
            )
            if self.recipe_voltage < 1:
                self.recipe_voltage = 1

        if self.does_laser_oc:
            duration, recipe_voltage = self._do_laser_oc(duration, recipe_voltage)

        if duration < 1:
            duration = 1

        recipe_voltage = self._final_recipe_eut(
            recipe_voltage, heat_discount_multiplier
        )

        return OverclockCalculatorResult(
            duration=duration,
            recipe_voltage=recipe_voltage,
            overclock_count=overclock_count,
        )

    def calculate_duration_under_one_tick(self) -> float:
        # TODO: support duration under one tick supplier
        if self.does_not_overclock:
            return float(self.duration)
        normal_overclocks = self._amount_of_overclocks(
            self._machine_power_tier(),
            self._recipe_power_tier(self._heat_discount_multiplier()),
        )
        if self._limits_overclocks:
            normal_overclocks = min(normal_overclocks, self._max_overclocks)
        heat_overclocks = min(self._amount_of_heat_overclocks(), normal_overclocks)
        return (self.duration * self.speed_boost) / (
            math.pow(self.duration_decrease_per_oc, normal_overclocks - heat_overclocks)
            * math.pow(self.duration_decrease_per_heat_oc, heat_overclocks)
        )

    def calculate_eut_consumption_under_one_tick(
        self, original_max_parallel: int, current_parallel: int
    ) -> int:
        if self.does_not_overclock:
            return self.recipe_voltage

        heat_discount_multiplier = self._heat_discount_multiplier()

        parallel_multiplier_from_overclocks = current_parallel / original_max_parallel
        amount_parallel_heat_oc = min(
            math.log(
                parallel_multiplier_from_overclocks, self.duration_decrease_per_heat_oc
            ),
            self._amount_of_heat_overclocks(),
        )
        amount_parallel_oc = math.log(
            parallel_multiplier_from_overclocks,
            self.duration_decrease_per_oc,
        ) - amount_parallel_heat_oc * (
            self.duration_decrease_per_heat_oc - self.duration_decrease_per_oc
        )
        machine_tier = self._machine_power_tier()
        recipe_tier = self._recipe_power_tier(heat_discount_multiplier)
        amount_total_oc = self._amount_of_overclocks(machine_tier, recipe_tier)
        if self.recipe_voltage <= values.VoltageTier[0]:
            amount_total_oc = min(
                amount_total_oc, self._recipe_to_machine_voltage_diff()
            )
        if self._limits_overclocks:
            amount_total_oc = min(amount_total_oc, self._max_overclocks)
        return math.ceil(
            self.recipe_voltage
            * math.pow(
                self.eut_increase_per_oc,
                amount_parallel_oc + amount_parallel_heat_oc,
            )
            * math.pow(
                self.eut_increase_per_oc,
                amount_total_oc - (amount_parallel_oc + amount_parallel_heat_oc),
            )
            * original_max_parallel
            * self.eut_discount
            * self.recipe_amperage
            * heat_discount_multiplier
        )

    def _heat_discount_multiplier(self):
        heat_discounts = 0
        if self.has_heat_discount:
            heat_discounts = (
                self.machine_heat - self.recipe_heat
            ) // self.HEAT_DISCOUNT_THRESHOLD
        return math.pow(self.heat_discount_multi, heat_discounts)

    @staticmethod
    def _amount_of_overclocks(machine_power_tier: float, recipe_power_tier: float):
        return int(machine_power_tier - recipe_power_tier)

    def _amount_of_heat_overclocks(self) -> int:
        return min(
            (self.machine_heat - self.recipe_heat)
            // self.HEAT_PERFECT_OVERCLOCK_THRESHOLD,
            self._amount_of_overclocks(
                self._machine_power_tier(),
                self._recipe_power_tier(self._heat_discount_multiplier()),
            ),
        )

    def _amount_of_needed_overclocks(
        self, machine_power_tier: float, recipe_power_tier: float
    ):
        return min(
            self._amount_of_overclocks(machine_power_tier, recipe_power_tier),
            math.ceil(math.log(self.duration, self.duration_decrease_per_oc)),
        )

    def _machine_power_tier(self):
        amp = self.machine_amperage
        if not self.does_amperage_oc:
            amp = min(self.machine_amperage, self.parallel)
        return self._power_tier(self.machine_voltage * amp)

    def _recipe_power_tier(self, heat_discount_multiplier: float):
        return self._power_tier(
            self.recipe_voltage
            * self.parallel
            * self.eut_discount
            * heat_discount_multiplier
            * self.recipe_amperage
        )

    def _recipe_to_machine_voltage_diff(self) -> int:
        return math.ceil(self._power_tier(self.machine_voltage)) - math.ceil(
            self._power_tier(self.recipe_voltage)
        )

    def _do_laser_oc(self, duration: int, recipe_voltage: int):
        res_duration = duration
        res_recipe_voltage = recipe_voltage
        input_eut = self.machine_voltage * self.machine_amperage
        current_penalty = self.eut_increase_per_oc + self.laser_oc_penalty
        while (
            input_eut > res_recipe_voltage * current_penalty
            and res_recipe_voltage * current_penalty > 0
            and res_duration > 1
        ):
            res_duration //= self.duration_decrease_per_oc
            res_recipe_voltage = int(res_recipe_voltage * current_penalty)
            current_penalty += self.laser_oc_penalty
        return res_duration, res_recipe_voltage

    def _final_recipe_eut(self, recipe_voltage: int, heat_discount_multiplier: float):
        return math.ceil(
            recipe_voltage
            * self.eut_discount
            * heat_discount_multiplier
            * self.parallel
            * self.recipe_amperage
        )

    @staticmethod
    def _power_tier(voltage):
        return 1 + max(0, math.log(voltage, 2) - 5) / 2
