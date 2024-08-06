# It tries to mirror the corresponding class in Java source code line by line.
# - Source: gregtech/api/enums/GT_Values.java
# - GTNH version: 2.6.1
# - Commit: 9ec067dc13f9ef7aff30fcc0ee3244f22bd76dd7
V = [
    8,
    32,
    128,
    512,
    2048,
    8192,
    32_768,
    131_072,
    524_288,
    2_097_152,
    8_388_608,
    33_554_432,
    134_217_728,
    536_870_912,
    2_147_483_648,
    8_589_934_592,
]
VP = [int(v * 30 / 32) for v in V]
