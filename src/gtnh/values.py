# Reference to
# - Source: gregtech/api/enums/GT_Values.java
# - GTNH version: 2.6.1
# - Commit: 9ec067dc13f9ef7aff30fcc0ee3244f22bd76dd7
from enum import IntEnum


class Voltage(IntEnum):
    ULV = 8  # 0
    LV = 32  # 1
    MV = 128  # 2
    HV = 512  # 3
    EV = 2048  # 4
    IV = 8192  # 5
    LuV = 32_768  # 6
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
