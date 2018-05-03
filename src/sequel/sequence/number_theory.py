"""
Prime Sequence
"""

import itertools

import gmpy2
import sympy

from .base import Sequence, Iterator, StashedFunction, EnumeratedSequence
from .trait import Trait
from ..utils import divisors

__all__ = [
    'Prime',
    'MersenneExponent',
    'MersennePrime',
    'Pi',
    'Phi',
    'Tau',
    'Sigma',
    'Euler',
    'Bell',
    'Genocchi',
]


class Prime(Iterator):
    __stash__ = [gmpy2.mpz(x) for x in (
        2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73,
        79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157,
        163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241,
        251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347,
        349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439,
        443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521, 523, 541, 547,
        557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643,
        647, 653, 659, 661, 673, 677, 683, 691, 701, 709, 719, 727, 733, 739, 743, 751,
        757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827, 829, 839, 853, 857, 859,
        863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953, 967, 971, 977,
        983, 991, 997, 1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051, 1061,
        1063, 1069, 1087, 1091, 1093, 1097, 1103, 1109, 1117, 1123, 1129, 1151, 1153,
        1163, 1171, 1181, 1187, 1193, 1201, 1213, 1217, 1223, 1229, 1231, 1237, 1249,
        1259, 1277, 1279, 1283, 1289, 1291, 1297, 1301, 1303, 1307, 1319, 1321, 1327,
        1361, 1367, 1373, 1381, 1399, 1409, 1423, 1427, 1429, 1433, 1439, 1447, 1451,
        1453, 1459, 1471, 1481, 1483, 1487, 1489, 1493, 1499, 1511, 1523, 1531, 1543,
        1549, 1553, 1559, 1567, 1571, 1579, 1583, 1597, 1601, 1607, 1609, 1613, 1619,
        1621, 1627, 1637, 1657, 1663, 1667, 1669, 1693, 1697, 1699, 1709, 1721, 1723,
        1733, 1741, 1747, 1753, 1759, 1777, 1783, 1787, 1789, 1801, 1811, 1823, 1831,
        1847, 1861, 1867, 1871, 1873, 1877, 1879, 1889, 1901, 1907, 1913, 1931, 1933,
        1949, 1951, 1973, 1979, 1987, 1993, 1997, 1999, 2003, 2011, 2017, 2027, 2029,
        2039, 2053, 2063, 2069, 2081, 2083, 2087, 2089, 2099, 2111, 2113, 2129, 2131,
        2137, 2141, 2143, 2153, 2161, 2179, 2203, 2207, 2213, 2221, 2237, 2239, 2243,
        2251, 2267, 2269, 2273, 2281, 2287, 2293, 2297, 2309, 2311, 2333, 2339, 2341,
        2347, 2351, 2357, 2371, 2377, 2381, 2383, 2389, 2393, 2399, 2411, 2417, 2423,
        2437, 2441, 2447, 2459, 2467, 2473, 2477, 2503, 2521, 2531, 2539, 2543, 2549,
        2551, 2557, 2579, 2591, 2593, 2609, 2617, 2621, 2633, 2647, 2657, 2659, 2663,
        2671, 2677, 2683, 2687, 2689, 2693, 2699, 2707, 2711, 2713, 2719, 2729, 2731,
        2741, 2749, 2753, 2767, 2777, 2789, 2791, 2797, 2801, 2803, 2819, 2833, 2837,
        2843, 2851, 2857, 2861, 2879, 2887, 2897, 2903, 2909, 2917, 2927, 2939, 2953,
        2957, 2963, 2969, 2971, 2999, 3001, 3011, 3019, 3023, 3037, 3041, 3049, 3061,
        3067, 3079, 3083, 3089, 3109, 3119, 3121, 3137, 3163, 3167, 3169, 3181, 3187,
        3191, 3203, 3209, 3217, 3221, 3229, 3251, 3253, 3257, 3259, 3271, 3299, 3301,
        3307, 3313, 3319, 3323, 3329, 3331, 3343, 3347, 3359, 3361, 3371, 3373, 3389,
        3391, 3407, 3413, 3433, 3449, 3457, 3461, 3463, 3467, 3469, 3491, 3499, 3511,
        3517, 3527, 3529, 3533, 3539, 3541, 3547, 3557, 3559, 3571, 3581, 3583, 3593,
        3607, 3613, 3617, 3623, 3631, 3637, 3643, 3659, 3671, 3673, 3677, 3691, 3697,
        3701, 3709, 3719, 3727, 3733, 3739, 3761, 3767, 3769, 3779, 3793, 3797, 3803,
        3821, 3823, 3833, 3847, 3851, 3853, 3863, 3877, 3881, 3889, 3907, 3911, 3917,
        3919, 3923, 3929, 3931, 3943, 3947, 3967, 3989, 4001, 4003, 4007, 4013, 4019,
        4021, 4027, 4049, 4051, 4057, 4073, 4079, 4091, 4093, 4099, 4111, 4127, 4129,
        4133, 4139, 4153, 4157, 4159, 4177, 4201, 4211, 4217, 4219, 4229, 4231, 4241,
        4243, 4253, 4259, 4261, 4271, 4273, 4283, 4289, 4297, 4327, 4337, 4339, 4349,
        4357, 4363, 4373, 4391, 4397, 4409, 4421, 4423, 4441, 4447, 4451, 4457, 4463,
        4481, 4483, 4493, 4507, 4513, 4517, 4519, 4523, 4547, 4549, 4561, 4567, 4583,
        4591, 4597, 4603, 4621, 4637, 4639, 4643, 4649, 4651, 4657, 4663, 4673, 4679,
        4691, 4703, 4721, 4723, 4729, 4733, 4751, 4759, 4783, 4787, 4789, 4793, 4799,
        4801, 4813, 4817, 4831, 4861, 4871, 4877, 4889, 4903, 4909, 4919, 4931, 4933,
        4937, 4943, 4951, 4957, 4967, 4969, 4973, 4987, 4993, 4999, 5003, 5009, 5011,
        5021, 5023, 5039, 5051, 5059, 5077, 5081, 5087, 5099, 5101, 5107, 5113, 5119,
        5147, 5153, 5167, 5171, 5179, 5189, 5197, 5209, 5227, 5231, 5233, 5237, 5261,
        5273, 5279, 5281, 5297, 5303, 5309, 5323, 5333, 5347, 5351, 5381, 5387, 5393,
        5399, 5407, 5413, 5417, 5419, 5431, 5437, 5441, 5443, 5449, 5471, 5477, 5479,
        5483, 5501, 5503, 5507, 5519, 5521, 5527, 5531, 5557, 5563, 5569, 5573, 5581,
        5591, 5623, 5639, 5641, 5647, 5651, 5653, 5657, 5659, 5669, 5683, 5689, 5693,
        5701, 5711, 5717, 5737, 5741, 5743, 5749, 5779, 5783, 5791, 5801, 5807, 5813,
        5821, 5827, 5839, 5843, 5849, 5851, 5857, 5861, 5867, 5869, 5879, 5881, 5897,
        5903, 5923, 5927, 5939, 5953, 5981, 5987, 6007, 6011, 6029, 6037, 6043, 6047,
        6053, 6067, 6073, 6079, 6089, 6091, 6101, 6113, 6121, 6131, 6133, 6143, 6151,
        6163, 6173, 6197, 6199, 6203, 6211, 6217, 6221, 6229, 6247, 6257, 6263, 6269,
        6271, 6277, 6287, 6299, 6301, 6311, 6317, 6323, 6329, 6337, 6343, 6353, 6359,
        6361, 6367, 6373, 6379, 6389, 6397, 6421, 6427, 6449, 6451, 6469, 6473, 6481,
        6491, 6521, 6529, 6547, 6551, 6553, 6563, 6569, 6571, 6577, 6581, 6599, 6607,
        6619, 6637, 6653, 6659, 6661, 6673, 6679, 6689, 6691, 6701, 6703, 6709, 6719,
        6733, 6737, 6761, 6763, 6779, 6781, 6791, 6793, 6803, 6823, 6827, 6829, 6833,
        6841, 6857, 6863, 6869, 6871, 6883, 6899, 6907, 6911, 6917, 6947, 6949, 6959,
        6961, 6967, 6971, 6977, 6983, 6991, 6997, 7001, 7013, 7019, 7027, 7039, 7043,
        7057, 7069, 7079, 7103, 7109, 7121, 7127, 7129, 7151, 7159, 7177, 7187, 7193,
        7207, 7211, 7213, 7219, 7229, 7237, 7243, 7247, 7253, 7283, 7297, 7307, 7309,
        7321, 7331, 7333, 7349, 7351, 7369, 7393, 7411, 7417, 7433, 7451, 7457, 7459,
        7477, 7481, 7487, 7489, 7499, 7507, 7517, 7523, 7529, 7537, 7541, 7547, 7549,
        7559, 7561, 7573, 7577, 7583, 7589, 7591, 7603, 7607, 7621, 7639, 7643, 7649,
        7669, 7673, 7681, 7687, 7691, 7699, 7703, 7717, 7723, 7727, 7741, 7753, 7757,
        7759, 7789, 7793, 7817, 7823, 7829, 7841, 7853, 7867, 7873, 7877, 7879, 7883,
        7901, 7907, 7919, 7927, 7933, 7937, 7949, 7951, 7963, 7993, 8009, 8011, 8017,
        8039, 8053, 8059, 8069, 8081, 8087, 8089, 8093, 8101, 8111, 8117, 8123, 8147,
        8161)]

    def __iter__(self):
        yield from self.__stash__
        p = self.__stash__[-1]
        while True:
            p = gmpy2.next_prime(p)
            yield int(p)

    def description(self):
        return """f(n) := the n-th prime number"""


Prime().register('p').set_traits(Trait.INJECTIVE, Trait.POSITIVE, Trait.NON_ZERO)


_MERSENNE_EXPONENTS = [gmpy2.mpz(x) for x in (
    2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127, 521, 607, 1279,
    2203, 2281, 3217, 4253, 4423, 9689, 9941, 11213, 19937, 21701,
    23209, 44497, 86243, 110503, 132049, 216091, 756839, 859433,
    1257787, 1398269, 2976221, 3021377, 6972593, 13466917, 20996011,
    24036583, 25964951, 30402457, 32582657, 37156667, 42643801,
    43112609)]


class MersenneExponent(EnumeratedSequence):
    __stash__ = _MERSENNE_EXPONENTS

    def description(self):
        return """f(n) := the n-th Mersenne exponent"""


MersenneExponent().register("m_exp").set_traits(Trait.POSITIVE, Trait.NON_ZERO, Trait.PARTIALLY_KNOWN)


class MersennePrime(EnumeratedSequence):
    __stash__ = [(gmpy2.mpz(2) ** n - 1) for n in _MERSENNE_EXPONENTS]

    def description(self):
        return """f(n) := the n-th Mersenne prime"""


MersennePrime().register("m_primes").set_traits(Trait.POSITIVE, Trait.NON_ZERO, Trait.PARTIALLY_KNOWN, Trait.FAST_GROWING)


class Pi(Iterator):
    def __iter__(self):
        prev = 1
        count = 0
        for p in Prime():
            yield from itertools.repeat(count, p - prev)
            count += 1
            prev = p

    def description(self):
        return """f(n) := count prime numbers <= n"""


Pi().register('pi').set_traits(Trait.POSITIVE)


class Phi(StashedFunction):
    __stash__ = [gmpy2.mpz(x) for x in (
        1, 1, 2, 2, 4, 2, 6, 4, 6, 4, 10, 4, 12, 6, 8, 8, 16, 6, 18, 8, 12, 10, 22, 8,
        20, 12, 18, 12, 28, 8, 30, 16, 20, 16, 24, 12, 36, 18, 24, 16, 40, 12, 42, 20,
        24, 22, 46, 16, 42, 20, 32, 24, 52, 18, 40, 24, 36, 28, 58, 16, 60, 30, 36, 32,
        48, 20, 66, 32, 44, 24, 70, 24, 72, 36, 40, 36, 60, 24, 78, 32, 54, 40, 82, 24,
        64, 42, 56, 40, 88, 24, 72, 44, 60, 46, 72, 32, 96, 42, 60, 40, 100, 32, 102,
        48, 48, 52, 106, 36, 108, 40, 72, 48, 112, 36, 88, 56, 72, 58, 96, 32, 110, 60,
        80, 60, 100, 36, 126, 64, 84, 48, 130, 40, 108, 66, 72, 64, 136, 44, 138, 48,
        92, 70, 120, 48, 112, 72, 84, 72, 148, 40, 150, 72, 96, 60, 120, 48, 156, 78,
        104, 64, 132, 54, 162, 80, 80, 82, 166, 48, 156, 64, 108, 84, 172, 56, 120, 80,
        116, 88, 178, 48, 180, 72, 120, 88, 144, 60, 160, 92, 108, 72, 190, 64, 192,
        96, 96, 84, 196, 60, 198, 80, 132, 100, 168, 64, 160, 102, 132, 96, 180, 48,
        210, 104, 140, 106, 168, 72, 180, 108, 144, 80, 192, 72, 222, 96, 120, 112,
        226, 72, 228, 88, 120, 112, 232, 72, 184, 116, 156, 96, 238, 64, 240, 110, 162,
        120, 168, 80, 216, 120, 164, 100, 250, 72, 220, 126, 128, 128, 256, 84, 216,
        96, 168, 130, 262, 80, 208, 108, 176, 132, 268, 72, 270, 128, 144, 136, 200,
        88, 276, 138, 180, 96, 280, 92, 282, 140, 144, 120, 240, 96, 272, 112, 192,
        144, 292, 84, 232, 144, 180, 148, 264, 80, 252, 150, 200, 144, 240, 96, 306,
        120, 204, 120, 310, 96, 312, 156, 144, 156, 316, 104, 280, 128, 212, 132, 288,
        108, 240, 162, 216, 160, 276, 80, 330, 164, 216, 166, 264, 96, 336, 156, 224,
        128, 300, 108, 294, 168, 176, 172, 346, 112, 348, 120, 216, 160, 352, 116, 280,
        176, 192, 178, 358, 96, 342, 180, 220, 144, 288, 120, 366, 176, 240, 144, 312,
        120, 372, 160, 200, 184, 336, 108, 378, 144, 252, 190, 382, 128, 240, 192, 252,
        192, 388, 96, 352, 168, 260, 196, 312, 120, 396, 198, 216, 160, 400, 132, 360,
        200, 216, 168, 360, 128, 408, 160, 272, 204, 348, 132, 328, 192, 276, 180, 418,
        96, 420, 210, 276, 208, 320, 140, 360, 212, 240, 168, 430, 144, 432, 180, 224,
        216, 396, 144, 438, 160, 252, 192, 442, 144, 352, 222, 296, 192, 448, 120, 400,
        224, 300, 226, 288, 144, 456, 228, 288, 176, 460, 120, 462, 224, 240, 232, 466,
        144, 396, 184, 312, 232, 420, 156, 360, 192, 312, 238, 478, 128, 432, 240, 264,
        220, 384, 162, 486, 240, 324, 168, 490, 160, 448, 216, 240, 240, 420, 164, 498,
        200, 332, 250, 502, 144, 400, 220, 312, 252, 508, 128, 432, 256, 324, 256, 408,
        168, 460, 216, 344, 192, 520, 168, 522, 260, 240, 262, 480, 160, 506, 208, 348,
        216, 480, 176, 424, 264, 356, 268, 420, 144, 540, 270, 360, 256, 432, 144, 546,
        272, 360, 200, 504, 176, 468, 276, 288, 276, 556, 180, 504, 192, 320, 280, 562,
        184, 448, 282, 324, 280, 568, 144, 570, 240, 380, 240, 440, 192, 576, 272, 384,
        224, 492, 192, 520, 288, 288, 292, 586, 168, 540, 232, 392, 288, 592, 180, 384,
        296, 396, 264, 598, 160, 600, 252, 396, 300, 440, 200, 606, 288, 336, 240, 552,
        192, 612, 306, 320, 240, 616, 204, 618, 240, 396, 310, 528, 192, 500, 312, 360,
        312, 576, 144, 630, 312, 420, 316, 504, 208, 504, 280, 420, 256, 640, 212, 642,
        264, 336, 288, 646, 216, 580, 240, 360, 324, 652, 216, 520, 320, 432, 276, 658,
        160, 660, 330, 384, 328, 432, 216, 616, 332, 444, 264, 600, 192, 672, 336, 360,
        312, 676, 224, 576, 256, 452, 300, 682, 216, 544, 294, 456, 336, 624, 176, 690,
        344, 360, 346, 552, 224, 640, 348, 464, 240, 700, 216, 648, 320, 368, 352, 600,
        232, 708, 280, 468, 352, 660, 192, 480, 356, 476, 358, 718, 192, 612, 342, 480,
        360, 560, 220, 726, 288, 486, 288, 672, 240, 732, 366, 336, 352, 660, 240, 738,
        288, 432, 312, 742, 240, 592, 372, 492, 320, 636, 200, 750, 368, 500, 336, 600,
        216, 756, 378, 440, 288, 760, 252, 648, 380, 384, 382, 696, 256, 768, 240, 512,
        384, 772, 252, 600, 384, 432, 388, 720, 192, 700, 352, 504, 336, 624, 260, 786,
        392, 524, 312, 672, 240, 720, 396, 416, 396, 796, 216, 736, 320, 528, 400, 720,
        264, 528, 360, 536, 400, 808, 216, 810, 336, 540, 360, 648, 256, 756, 408, 432,
        320, 820, 272, 822, 408, 400, 348, 826, 264, 828, 328, 552, 384, 672, 276, 664,
        360, 540, 418, 838, 192, 812, 420, 560, 420, 624, 276, 660, 416, 564, 320, 792,
        280, 852, 360, 432, 424, 856, 240, 858, 336, 480, 430, 862, 288, 688, 432, 544,
        360, 780, 224, 792, 432, 576, 396, 600, 288, 876, 438, 584, 320, 880, 252, 882,
        384, 464, 442, 886, 288, 756, 352, 540, 444, 828, 296, 712, 384, 528, 448, 840,
        240, 832, 400, 504, 448, 720, 300, 906, 452, 600, 288, 910, 288, 820, 456, 480,
        456, 780, 288, 918, 352, 612, 460, 840, 240, 720, 462, 612, 448, 928, 240, 756,
        464, 620, 466, 640, 288, 936, 396, 624, 368, 940, 312, 880, 464, 432, 420, 946,
        312, 864, 360, 632, 384, 952, 312, 760, 476, 560, 478, 816, 256, 930, 432, 636,
        480, 768, 264, 966, 440, 576, 384, 970, 324, 828, 486, 480, 480, 976, 324, 880,
        336, 648, 490, 982, 320, 784, 448, 552, 432, 924, 240, 990, 480, 660, 420, 792,
        328, 996, 498, 648, 400, 720, 332, 928, 500, 528, 502, 936, 288, 1008, 400,
        672, 440, 1012, 312, 672, 504, 672, 508, 1018, 256, 1020, 432, 600, 512)]

    def __call__(self, i):
        n = i + 1  # Phi is defined in [1, inf]
        value = 0
        for i in range(1, n + 1):
            if gmpy2.gcd(n, i) == 1:
                value += 1
        return value

    def priority(self):
        return self.PRIORITY_CALL

    def description(self):
        return """f(n) := count numbers <= n and prime to n (Euler's totient function)"""


Phi().register('phi').set_traits(Trait.POSITIVE, Trait.NON_ZERO)


class Tau(StashedFunction):
    __stash__ = [gmpy2.mpz(x) for x in (
        1, 2, 2, 3, 2, 4, 2, 4, 3, 4, 2, 6, 2, 4, 4, 5, 2, 6, 2, 6, 4, 4, 2, 8, 3, 4,
        4, 6, 2, 8, 2, 6, 4, 4, 4, 9, 2, 4, 4, 8, 2, 8, 2, 6, 6, 4, 2, 10, 3, 6, 4, 6,
        2, 8, 4, 8, 4, 4, 2, 12, 2, 4, 6, 7, 4, 8, 2, 6, 4, 8, 2, 12, 2, 4, 6, 6, 4, 8,
        2, 10, 5, 4, 2, 12, 4, 4, 4, 8, 2, 12, 4, 6, 4, 4, 4, 12, 2, 6, 6, 9, 2, 8, 2,
        8, 8, 4, 2, 12, 2, 8, 4, 10, 2, 8, 4, 6, 6, 4, 4, 16, 3, 4, 4, 6, 4, 12, 2, 8,
        4, 8, 2, 12, 4, 4, 8, 8, 2, 8, 2, 12, 4, 4, 4, 15, 4, 4, 6, 6, 2, 12, 2, 8, 6,
        8, 4, 12, 2, 4, 4, 12, 4, 10, 2, 6, 8, 4, 2, 16, 3, 8, 6, 6, 2, 8, 6, 10, 4, 4,
        2, 18, 2, 8, 4, 8, 4, 8, 4, 6, 8, 8, 2, 14, 2, 4, 8, 9, 2, 12, 2, 12, 4, 4, 4,
        12, 4, 4, 6, 10, 4, 16, 2, 6, 4, 4, 4, 16, 4, 4, 4, 12, 4, 8, 2, 12, 9, 4, 2,
        12, 2, 8, 8, 8, 2, 12, 4, 6, 4, 8, 2, 20, 2, 6, 6, 6, 6, 8, 4, 8, 4, 8, 2, 18,
        4, 4, 8, 9, 2, 8, 4, 12, 6, 4, 2, 16, 4, 8, 4, 6, 2, 16, 2, 10, 8, 4, 6, 12, 2,
        4, 6, 16, 2, 8, 2, 6, 8, 8, 4, 18, 3, 8, 4, 6, 2, 12, 4, 8, 8, 4, 4, 18, 4, 4,
        4, 10, 4, 12, 2, 12, 4, 8, 2, 16, 2, 4, 12, 6, 2, 8, 4, 14, 4, 8, 4, 15, 6, 4,
        4, 8, 4, 16, 2, 6, 6, 4, 4, 20, 2, 6, 4, 12, 4, 12, 4, 8, 8, 4, 2, 12, 2, 12,
        8, 12, 2, 8, 4, 6, 8, 4, 2, 24, 3, 4, 6, 12, 4, 8, 2, 10, 6, 8, 4, 12, 2, 8, 8,
        8, 4, 16, 2, 12, 4, 4, 2, 16, 8, 4, 6, 6, 2, 16, 4, 12, 4, 4, 4, 18, 2, 4, 8,
        15, 2, 8, 4, 6, 10, 8, 4, 16, 2, 8, 4, 6, 4, 12, 4, 12, 4, 8, 2, 24, 2, 4, 6,
        8, 6, 8, 4, 6, 8, 8, 2, 20, 2, 8, 8, 6, 4, 8, 2, 16, 9, 8, 2, 12, 4, 4, 4, 14,
        2, 18, 4, 6, 4, 4, 8, 16, 2, 4, 8, 12, 2, 16, 2, 10, 8, 4, 2, 18, 4, 8, 4, 8,
        4, 8, 6, 12, 6, 4, 2, 24, 4, 4, 8, 9, 4, 12, 2, 8, 4, 12, 2, 12, 4, 8, 12, 10,
        4, 8, 2, 12, 4, 4, 2, 24, 4, 8, 6, 6, 2, 16, 4, 10, 8, 4, 4, 12, 4, 8, 4, 16,
        2, 12, 2, 6, 12, 4, 4, 20, 3, 8, 6, 12, 4, 8, 4, 8, 4, 4, 6, 24, 2, 4, 4, 12,
        4, 16, 2, 6, 6, 12, 4, 16, 4, 4, 8, 6, 2, 12, 4, 20, 8, 4, 2, 12, 4, 4, 10, 8,
        2, 16, 2, 12, 4, 8, 6, 21, 2, 6, 4, 12, 4, 8, 4, 8, 12, 4, 2, 18, 4, 8, 4, 10,
        2, 16, 8, 6, 4, 8, 2, 24, 2, 8, 6, 6, 6, 8, 2, 12, 8, 8, 4, 18, 2, 4, 8, 16, 2,
        8, 2, 12, 8, 4, 4, 20, 5, 4, 8, 6, 4, 24, 2, 8, 4, 4, 4, 12, 6, 8, 6, 16, 2, 8,
        2, 12, 8, 8, 2, 20, 4, 12, 8, 6, 2, 8, 4, 10, 6, 8, 2, 24, 2, 4, 8, 8, 8, 12,
        4, 6, 4, 8, 4, 24, 2, 4, 12, 9, 2, 8, 4, 16, 4, 8, 2, 18, 4, 8, 4, 10, 4, 16,
        2, 6, 12, 4, 4, 16, 4, 4, 4, 18, 2, 16, 4, 14, 8, 4, 4, 12, 2, 8, 6, 8, 4, 16,
        8, 6, 4, 4, 2, 30, 4, 6, 4, 6, 6, 12, 2, 16, 7, 8, 4, 12, 2, 4, 12, 12, 4, 12,
        2, 12, 8, 8, 2, 16, 4, 4, 6, 12, 4, 16, 2, 10, 4, 8, 4, 24, 2, 4, 8, 16, 2, 8,
        4, 6, 12, 4, 4, 18, 2, 16, 4, 6, 2, 12, 6, 8, 8, 4, 4, 24, 4, 8, 8, 15, 4, 8,
        2, 6, 4, 8, 4, 24, 4, 4, 8, 6, 2, 16, 4, 18, 6, 4, 4, 12, 8, 8, 4, 8, 2, 20, 2,
        12, 4, 8, 4, 20, 4, 4, 12, 12, 2, 8, 2, 8, 12, 8, 2, 18, 2, 8, 4, 14, 6, 8, 4,
        12, 8, 4, 2, 32, 3, 4, 4, 6, 6, 12, 6, 10, 4, 12, 4, 12, 2, 8, 12, 8, 2, 16, 2,
        12, 8, 4, 2, 24, 4, 4, 6, 12, 4, 16, 4, 8, 6, 8, 8, 12, 2, 4, 4, 20, 2, 18, 2,
        12, 8, 4, 2, 16, 4, 8, 10, 6, 4, 8, 4, 16, 8, 4, 4, 27, 4, 8, 8, 8, 4, 8, 2, 6,
        6, 16, 2, 20, 4, 4, 8, 6, 4, 16, 2, 16, 4, 4, 4, 24, 6, 4, 6, 12, 2, 16, 6, 6,
        4, 4, 8, 24, 2, 8, 4, 12, 2, 8, 4, 10, 16, 8, 2, 12, 4, 12, 4, 16, 2, 12, 4, 6,
        8, 4, 4, 28, 3, 8, 6, 6, 4, 16, 2, 12, 8, 8, 2, 18, 4, 4, 12, 10, 2, 8, 4, 18,
        6, 4, 2, 16, 4, 8, 8, 12, 4, 24, 2, 12, 4, 8, 4, 12, 2, 4, 8, 16, 8, 8, 4, 6,
        8, 4, 4, 30, 2, 8, 4, 12, 2, 12, 8, 8, 6, 4, 2, 24, 2, 8, 8, 11)]

    def __call__(self, i):
        return len(tuple(divisors(i + 1)))

    def description(self):
        return """f(n) := count divisors of n"""


Tau().register('tau').set_traits(Trait.POSITIVE, Trait.NON_ZERO)


class Sigma(StashedFunction):
    __stash__ = [gmpy2.mpz(x) for x in (
        1, 3, 4, 7, 6, 12, 8, 15, 13, 18, 12, 28, 14, 24, 24, 31, 18, 39, 20, 42, 32,
        36, 24, 60, 31, 42, 40, 56, 30, 72, 32, 63, 48, 54, 48, 91, 38, 60, 56, 90, 42,
        96, 44, 84, 78, 72, 48, 124, 57, 93, 72, 98, 54, 120, 72, 120, 80, 90, 60, 168,
        62, 96, 104, 127, 84, 144, 68, 126, 96, 144, 72, 195, 74, 114, 124, 140, 96,
        168, 80, 186, 121, 126, 84, 224, 108, 132, 120, 180, 90, 234, 112, 168, 128,
        144, 120, 252, 98, 171, 156, 217, 102, 216, 104, 210, 192, 162, 108, 280, 110,
        216, 152, 248, 114, 240, 144, 210, 182, 180, 144, 360, 133, 186, 168, 224, 156,
        312, 128, 255, 176, 252, 132, 336, 160, 204, 240, 270, 138, 288, 140, 336, 192,
        216, 168, 403, 180, 222, 228, 266, 150, 372, 152, 300, 234, 288, 192, 392, 158,
        240, 216, 378, 192, 363, 164, 294, 288, 252, 168, 480, 183, 324, 260, 308, 174,
        360, 248, 372, 240, 270, 180, 546, 182, 336, 248, 360, 228, 384, 216, 336, 320,
        360, 192, 508, 194, 294, 336, 399, 198, 468, 200, 465, 272, 306, 240, 504, 252,
        312, 312, 434, 240, 576, 212, 378, 288, 324, 264, 600, 256, 330, 296, 504, 252,
        456, 224, 504, 403, 342, 228, 560, 230, 432, 384, 450, 234, 546, 288, 420, 320,
        432, 240, 744, 242, 399, 364, 434, 342, 504, 280, 480, 336, 468, 252, 728, 288,
        384, 432, 511, 258, 528, 304, 588, 390, 396, 264, 720, 324, 480, 360, 476, 270,
        720, 272, 558, 448, 414, 372, 672, 278, 420, 416, 720, 282, 576, 284, 504, 480,
        504, 336, 819, 307, 540, 392, 518, 294, 684, 360, 570, 480, 450, 336, 868, 352,
        456, 408, 620, 372, 702, 308, 672, 416, 576, 312, 840, 314, 474, 624, 560, 318,
        648, 360, 762, 432, 576, 360, 847, 434, 492, 440, 630, 384, 864, 332, 588, 494,
        504, 408, 992, 338, 549, 456, 756, 384, 780, 400, 660, 576, 522, 348, 840, 350,
        744, 560, 756, 354, 720, 432, 630, 576, 540, 360, 1170, 381, 546, 532, 784,
        444, 744, 368, 744, 546, 684, 432, 896, 374, 648, 624, 720, 420, 960, 380, 840,
        512, 576, 384, 1020, 576, 582, 572, 686, 390, 1008, 432, 855, 528, 594, 480,
        1092, 398, 600, 640, 961, 402, 816, 448, 714, 726, 720, 456, 1080, 410, 756,
        552, 728, 480, 936, 504, 882, 560, 720, 420, 1344, 422, 636, 624, 810, 558,
        864, 496, 756, 672, 792, 432, 1240, 434, 768, 720, 770, 480, 888, 440, 1080,
        741, 756, 444, 1064, 540, 672, 600, 1016, 450, 1209, 504, 798, 608, 684, 672,
        1200, 458, 690, 720, 1008, 462, 1152, 464, 930, 768, 702, 468, 1274, 544, 864,
        632, 900, 528, 960, 620, 1008, 702, 720, 480, 1512, 532, 726, 768, 931, 588,
        1092, 488, 930, 656, 1026, 492, 1176, 540, 840, 936, 992, 576, 1008, 500, 1092,
        672, 756, 504, 1560, 612, 864, 732, 896, 510, 1296, 592, 1023, 800, 774, 624,
        1232, 576, 912, 696, 1260, 522, 1170, 524, 924, 992, 792, 576, 1488, 553, 972,
        780, 1120, 588, 1080, 648, 1020, 720, 810, 684, 1680, 542, 816, 728, 1134, 660,
        1344, 548, 966, 806, 1116, 600, 1440, 640, 834, 912, 980, 558, 1248, 616, 1488,
        864, 846, 564, 1344, 684, 852, 968, 1080, 570, 1440, 572, 1176, 768, 1008, 744,
        1651, 578, 921, 776, 1260, 672, 1176, 648, 1110, 1092, 882, 588, 1596, 640,
        1080, 792, 1178, 594, 1440, 864, 1050, 800, 1008, 600, 1860, 602, 1056, 884,
        1064, 798, 1224, 608, 1260, 960, 1116, 672, 1638, 614, 924, 1008, 1440, 618,
        1248, 620, 1344, 960, 936, 720, 1736, 781, 942, 960, 1106, 684, 1872, 632,
        1200, 848, 954, 768, 1512, 798, 1080, 936, 1530, 642, 1296, 644, 1344, 1056,
        1080, 648, 1815, 720, 1302, 1024, 1148, 654, 1320, 792, 1302, 962, 1152, 660,
        2016, 662, 996, 1008, 1260, 960, 1482, 720, 1176, 896, 1224, 744, 2016, 674,
        1014, 1240, 1281, 678, 1368, 784, 1620, 912, 1152, 684, 1820, 828, 1200, 920,
        1364, 756, 1728, 692, 1218, 1248, 1044, 840, 1800, 756, 1050, 936, 1736, 702,
        1680, 760, 1524, 1152, 1062, 816, 1680, 710, 1296, 1040, 1350, 768, 1728, 1008,
        1260, 960, 1080, 720, 2418, 832, 1143, 968, 1274, 930, 1596, 728, 1680, 1093,
        1332, 792, 1736, 734, 1104, 1368, 1512, 816, 1638, 740, 1596, 1120, 1296, 744,
        1920, 900, 1122, 1092, 1512, 864, 1872, 752, 1488, 1008, 1260, 912, 2240, 758,
        1140, 1152, 1800, 762, 1536, 880, 1344, 1404, 1152, 840, 2044, 770, 1728, 1032,
        1358, 774, 1716, 992, 1470, 1216, 1170, 840, 2352, 864, 1296, 1200, 1767, 948,
        1584, 788, 1386, 1056, 1440, 912, 2340, 868, 1194, 1296, 1400, 798, 1920, 864,
        1953, 1170, 1206, 888, 1904, 1152, 1344, 1080, 1530, 810, 2178, 812, 1680,
        1088, 1368, 984, 2232, 880, 1230, 1456, 1764, 822, 1656, 824, 1560, 1488, 1440,
        828, 2184, 830, 1512, 1112, 1778, 1026, 1680, 1008, 1680, 1280, 1260, 840,
        2880, 871, 1266, 1128, 1484, 1098, 1872, 1064, 1674, 1136, 1674, 912, 2016,
        854, 1488, 1560, 1620, 858, 2016, 860, 1848, 1344, 1296, 864, 2520, 1044, 1302,
        1228, 1792, 960, 2160, 952, 1650, 1274, 1440, 1248, 2072, 878, 1320, 1176,
        2232, 882, 2223, 884, 1764, 1440, 1332, 888, 2280, 1024, 1620, 1452, 1568, 960,
        1800, 1080, 2040, 1344, 1350, 960, 2821, 972, 1512, 1408, 1710, 1092, 1824,
        908, 1596, 1326, 2016, 912, 2480, 1008, 1374, 1488, 1610, 1056, 2160, 920,
        2160, 1232, 1386, 1008, 2688, 1178, 1392, 1352, 1890, 930, 2304, 1140, 1638,
        1248, 1404, 1296, 2730, 938, 1632, 1256, 2016, 942, 1896, 1008, 1860, 1920,
        1584, 948, 2240, 1036, 1860, 1272, 2160, 954, 2106, 1152, 1680, 1440, 1440,
        1104, 3048, 993, 1596, 1404, 1694, 1164, 2304, 968, 1995, 1440, 1764, 972,
        2548, 1120, 1464, 1736, 1922, 978, 1968, 1080, 2394, 1430, 1476, 984, 2520,
        1188, 1620, 1536, 1960, 1056, 2808, 992, 2016, 1328, 1728, 1200, 2352, 998,
        1500, 1520, 2340, 1344, 2016, 1080, 1764, 1632, 1512, 1080, 3224, 1010, 1836,
        1352, 2016, 1014, 2196, 1440, 1920, 1482, 1530, 1020, 3024, 1022, 1776, 1536,
        2047)]

    def __call__(self, i):
        return sum(divisors(i + 1))

    def description(self):
        return """f(n) := sum divisors of n"""


Sigma().register('sigma').set_traits(Trait.POSITIVE, Trait.NON_ZERO)


# class Delegate(Iterator):
#     __stash__ = None
#     __function__ = None
#     __description__ = ""
# 
#     def __call__(self, i):
#         stash = self.__stash__
#         if i < len(stash):
#             return stash[i]
#         else:
#             return int(self.__function__(i))
# 
#     def __iter__(self):
#         stash = self.__stash__
#         yield from stash
#         function = self.__function__
#         for i in itertools.count(start=len(stash)):
#             yield int(function(i))
# 
#     def description(self):
#         return self.__description__


class Euler(EnumeratedSequence):
    __stash__ = [1, 0, -1, 0, 5, 0, -61, 0, 1385, 0, -50521, 0, 2702765, 0, -199360981, 0, 19391512145, 0, -2404879675441, 0, 370371188237525, 0, -69348874393137901, 0,
15514534163557086905, 0, -4087072509293123892361, 0, 1252259641403629865468285, 0, -441543893249023104553682821, 0, 177519391579539289436664789665, 0,
-80723299235887898062168247453281, 0, 41222060339517702122347079671259045, 0, -23489580527043108252017828576198947741, 0,
14851150718114980017877156781405826684425, 0, -10364622733519612119397957304745185976310201, 0, 7947579422597592703608040510088070619519273805, 0,
-6667537516685544977435028474773748197524107684661, 0, 6096278645568542158691685742876843153976539044435185, 0,
-6053285248188621896314383785111649088103498225146815121, 0, 6506162486684608847715870634080822983483644236765385576565, 0,
-7546659939008739098061432565889736744212240024711699858645581, 0, 9420321896420241204202286237690583227209388852599646009394905945, 0,
-12622019251806218719903409237287489255482341061191825594069964920041, 0, 18108911496579230496545807741652158688733487349236314106008095454231325, 0,
-27757101702071580597366980908371527449233019594800917578033782766889782501, 0, 45358103330017889174746887871567762366351861519470368881468843837919695760705,
0, -78862842066617894181007207422399904239478162972003768932709757494857167945376961, 0,
145618443801396315007150470094942326661860812858314932986447697768064595488862902085, 0,
-285051783223697718732198729556739339504255241778255239879353211106980427546235397447421, 0,
590574720777544365455135032296439571372033016181822954929765972153659805050264501891063465, 0,
-1292973664187864170497603235938698754076170519123672606411370597343787035331808195731850937881, 0,
2986928183284576950930743652217140605692922369370680702813812833466898038172015655808960288452845, 0,
-7270601714016864143803280651699281851647234288049207905108309583687335688017641546191095009395592341, 0,
18622915758412697044482492303043126011920010194518556063577101095681956123546201442832293837005396878225, 0,
-50131049408109796612908693678881009420083336722220539765973596236561571401154699761552253189084809951554801, 0,
141652557597856259916722069410021670405475845492837912390700146845374567994390844977125987675020436380612547605, 0,
-419664316404024471322573414069418891818962628391683907039212228549032921853217838146608053808786365440570254969261, 0,
1302159590524046398125858691330818681356757613986610030678095758242404286633729262297123677199743591748006204646868985, 0]

    def descrition(self):
        return "E(n) - Euler (or secant) numbers"


Euler().register('euler')


class Bell(EnumeratedSequence):
    __stash__ = [1, 1, 2, 5, 15, 52, 203, 877, 4140, 21147, 115975, 678570, 4213597, 27644437, 190899322, 1382958545, 10480142147, 82864869804, 682076806159, 5832742205057,
51724158235372, 474869816156751, 4506715738447323, 44152005855084346, 445958869294805289, 4638590332229999353, 49631246523618756274, 545717047936059989389,
6160539404599934652455, 71339801938860275191172, 846749014511809332450147, 10293358946226376485095653, 128064670049908713818925644,
1629595892846007606764728147, 21195039388640360462388656799, 281600203019560266563340426570, 3819714729894818339975525681317, 52868366208550447901945575624941,
746289892095625330523099540639146, 10738823330774692832768857986425209, 157450588391204931289324344702531067, 2351152507740617628200694077243788988,
35742549198872617291353508656626642567, 552950118797165484321714693280737767385, 8701963427387055089023600531855797148876,
139258505266263669602347053993654079693415, 2265418219334494002928484444705392276158355, 37450059502461511196505342096431510120174682,
628919796303118415420210454071849537746015761, 10726137154573358400342215518590002633917247281, 185724268771078270438257767181908917499221852770,
3263983870004111524856951830191582524419255819477, 58205338024195872785464627063218599149503972126463, 1052928518014714166107781298021583534928402714242132,
19317287589145618265728950069285503257349832850302011, 359334085968622831041960188598043661065388726959079837,
6775685320645824322581483068371419745979053216268760300, 129482661947506964462616580633806000917491602609372517195,
2507136358984296114560786627437574942253015623445622326263, 49176743336309621659000944152624896853591018248919168867818,
976939307467007552986994066961675455550246347757474482558637, 19652364471547941482114228389322789963345673460673370562378245,
400237304821454786230522819234667544935526963060240082269259738, 8250771700405624889912456724304738028450190134337110943817172961,
172134143357358850934369963665272571125557575184049758045339873395, 3633778785457899322415257682767737441410036994560435982365219287372,
77605907238843669482155930857960017792778059887519278038000759795263, 1676501284301523453367212880854005182365748317589888660477021013719409,
36628224206696135478834640618028539032699174847931909480671725803995436, 809212768387947836336846277707066239391942323998649273771736744420003007,
18075003898340511237556784424498369141305841234468097908227993035088029195, 408130093410464274259945600962134706689859323636922532443365594726056131962,
9314528182092653288251451483527341806516792394674496725578935706029134658745, 214834623568478894452765605511928333367140719361291003997161390043701285425833,
5006908024247925379707076470957722220463116781409659160159536981161298714301202,
117896026920858300966730642538212084059025603061199813571998059942386637656568797,
2804379077740744643020190973126488180455295657360401565474468309847623573788115607,
67379449595254843852699636792665969652321946648374400833740986348378276368807261348,
1635000770532737216633829256032779450518375544542935181844299348876855151241590189395,
40064166844084356404509204005730815621427040237270563024820379702392240194729249115029,
991267988808424794443839434655920239360814764000951599022939879419136287216681744888844,
24761288718465863816962119279306788401954401906692653427329808967315171931611751006838915,
624387454429479848302014120414448006907125370284776661891529899343806658375826740689137423,
15892292813296951899433594303207669496517041849871581501737510069308817348770226226653966474,
408248141291805738980141314733701533991578374164094348787738475995651988600158415299211778933,
10583321873228234424552137744344434100391955309436425797852108559510434249855735357360593574749,
276844443054160876160126038812506987515878490163433019207947986484590126191194780416973565092618,
7306720755827530589639480511232846731775215754200303890190355852772713202556415109429779445622537,
194553897403965647871786295024290690576513032341195649821051001205884166153194143340809062985041067,
5225728505358477773256348249698509144957920836936865715700797250722975706153317517427783066539250012,
141580318123392930464192819123202606981284563291786545804370223525364095085412667328027643050802912567,
3868731362280702160655673912482765098905555785458740412264329844745080937342264610781770223818259614025,
106611797892739782364113678801520610524431974731789913132104301942153476208366519192812848588253648356364,
2962614388531218251190227244935749736828675583113926711461226180042633884248639975904464409686755210349399,
83012043550967281787120476720274991081436431402381752242504514629481800064636673934392827445150961387102019,
2345129936856330144543337656630809098301482271000632150222900693128839447045930834163493232282141300734566042,
66790853422797408533421892496106177820862555650400879850993569405575404871887998514898872210341414631481213729,
1917593350464112616752757157565032460248311804906650215954187246738986739924580790084847891233423398173059771233,
55494677927746340698788238667452126040563242441827634980157203368430358083090722409217101274455481270374885095618,
1618706027446068305855680628161135741330684513088812399898409470089128730792407044351108134019449028191480663320741]

    def descrition(self):
        return "Bell numbers"



Bell().register('bell')


class Genocchi(EnumeratedSequence):
    __stash__ = [1, -1, 0, 1, 0, -3, 0, 17, 0, -155, 0, 2073, 0, -38227, 0, 929569, 0, -28820619, 0, 1109652905, 0, -51943281731, 0, 2905151042481, 0, -191329672483963, 0,
14655626154768697, 0, -1291885088448017715, 0, 129848163681107301953, 0, -14761446733784164001387, 0, 1884515541728818675112649, 0,
-268463531464165471482681379, 0, 42433626725491925313195071185, 0, -7403610342602172448449261632091, 0, 1419269729459188512167209628047961, 0,
-297670324015849154718455710038555923, 0, 68041658377475993470566379406771713377, 0, -16890450341293965779175629389101669683275, 0,
4538527836046550440396187741233670828537833, 0, -1316087873322616222841347092534788263777772547, 0, 410710549795313669217134138031963472719424991729, 0,
-137574822905104349609548817079959649852879425710139, 0, 49344923392300818057578095725014316473251327377945465, 0,
-18908812621616649183271809171695618975850862983391710451, 0, 7724760729208487305545342963324697288405380586579904269441, 0,
-3357705352875811848662095280572437749931198053194672582115883, 0, 1549981637157991147753728983071773842929179505474331216569634057, 0,
-758532054906555708755238170363742617219468112432191792931477796835, 0, 392884629119918983400935638299706389275635619402512124261430072509713, 0,
-215040307620794439929965340620002043432417400913894279210272856070151707, 0, 124192389444022524121261318746701948240520188895960369330946488147959366809, 0,
-75575419306418253752786501324360147497334263198344892577773556317253502706899, 0,
48394710730639230937887116828365313836223426717242049788508195351187052567075745, 0,
-32568445057172408608837238670273033649252438327487869865710361646535847211594316811, 0,
23006717362809746150569854630614058026497702556621678568743571595626221869384888506921, 0,
-17040105873298878946124251190036035934422606062586512112334721340063184012128852579963843, 0,
13218265420200305682970449079175488578441372369270527631439318392777237582779922611657330737, 0,
-10727715287566958551214038600946703877155524594108495518119365379361759439218142773868765158395, 0,
9099901955300003753464428120483100601655776907796672920640721817145157395051329162472671748017593, 0,
-8060236222279805360203045875718710392840346979127991560050678520437317382910243591334313424349938867, 0,
7448054791241503276935934856991203956593951760700545612772609367246193232907656329398835700797987037889, 0,
-7173662283538643080098758544310321295850624414486460340224702639079585599047598111918284641754917438471659, 0,
7195755140823456775156973913946816533999691473304266185799465673914549220730458291517541658523714553671262025, 0,
-7511007173963433762003914319938830458773349540196381911443782593501430235458924413752380592051457064129210251171, 0,
8152090557815645817365302196725301060580449650858909184728710868588856606487908275562992606729338781555129489560401, 0,
-9193151439633537813558191869742158866222956701334000604661885515562311067823685766599709007427334516516639923388899803, 0,
10763963145744660945867769375817008284327714808962808241603662287226003669041713791766524328627438302037778399196143603417, 0,
-13076503664446113237311657248040134719631221951911491366286971503090540488883186838809257405173512975573468662489058504567955, 0,
16471490340428509961236507242866651008373787469735033062325977212414293239234497731500911762756631541105125868488657460763861473, 0]

    def descrition(self):
        return "Genocchi numbers"

Genocchi().register('genocchi')
