# Reference to
# - Source: gregtech/api/enums/GT_Values.java
# - GTNH version: 2.6.1
# - Commit: 9ec067dc13f9ef7aff30fcc0ee3244f22bd76dd7
import enum
import math
from enum import IntEnum


# To customize __getitem__, I have to inherit Enum's metaclass
class VoltageTierMeta(enum.EnumMeta):
    def __getitem__(cls, name):
        try:
            return super().__getitem__(name)
        except KeyError as err:
            return cls._custom_getitem(name, err)

    @classmethod
    def _custom_getitem(cls, name, origin_error: KeyError):
        raise origin_error


class VoltageTier(IntEnum, metaclass=VoltageTierMeta):
    """Voltage constants.

    Using it like a number:
    >>> VoltageTier.IV * 2
    16384

    Getting a tier by its name:
    >>> VoltageTier["max+"]
    <VoltageTier.MAX_PLUS: 8589934592>
    >>> VoltageTier["LuV"]
    <VoltageTier.LUV: 32768>

    Getting a tier by its number (0-15):
    >>> VoltageTier[4]
    <VoltageTier.EV: 2048>

    Finding the tier a voltage is in:
    >>> VoltageTier(200)
    <VoltageTier.HV: 512>
    """

    ULV = 8  # 0
    LV = 32  # 1
    MV = 128  # 2
    HV = 512  # 3
    EV = 2048  # 4
    IV = 8192  # 5
    LUV = 32_768  # 6
    ZPM = 131_072  # 7
    UV = 524_288  # 8
    UHV = 2_097_152  # 9
    UEV = 8_388_608  # 10
    UIV = 33_554_432  # 11
    UMV = 134_217_728  # 12
    UXV = 536_870_912  # 13
    MAX = 2_147_483_648  # 14
    MAX_PLUS = 8_589_934_592  # 15

    def practical(self):
        return int(self * 30 / 32)

    @classmethod
    def _missing_(cls, value):
        if type(value) is int and value >= 1 and value < cls.MAX_PLUS * 4:
            tier_number = max(0, math.ceil((math.log(value, 2) - 3) / 2))
            return cls._from_number(tier_number)
        return None

    @classmethod
    def _custom_getitem(cls, name, origin_error: KeyError):
        if type(name) is int:
            tier = name
            if tier < 0 or tier > 15:
                raise KeyError("Tier number is out of range.")
            return cls._from_number(tier)
        elif type(name) is str:
            name = name.upper()
            if name == "MAX+":
                name = "MAX_PLUS"
            for tier in cls:
                if tier.name == name:
                    return tier
        raise origin_error

    @staticmethod
    def _from_number(tier: int) -> "VoltageTier":
        return VoltageTier(int(math.pow(2, 3 + 2 * tier)))
