from collections import namedtuple
from queue import deque

from .base import Iterator, StashMixin
from .trait import Trait


__all__ = [
    'Somos',
]


SomosData = namedtuple(
    'SomosData', ['oeis_id', 'stash'],
)


class somos(Iterator):
    """Somos-k sequence is defined as follows:

         a(n) = 1 for n <= k, then:
         a(n) * a(n-k) = a(n-1)*a(n-k+1) + a(n-2)*a(n-k+2) + ... + a(n-k//2)*a(n-k+k//2)
    """
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING]
    __somos__ = {
        4: SomosData(oeis_id='A006720', stash=[
             1, 1, 1, 1, 2, 3, 7, 23, 59, 314, 1529, 8209, 83313, 620297, 7869898, 126742987, 1687054711, 47301104551,
             1123424582771, 32606721084786, 1662315215971057, 61958046554226593, 4257998884448335457,
             334806306946199122193, 23385756731869683322514, 3416372868727801226636179]),
        5: SomosData(oeis_id='A006721', stash=[
             1, 1, 1, 1, 1, 2, 3, 5, 11, 37, 83, 274, 1217, 6161, 22833, 165713, 1249441, 9434290, 68570323,
             1013908933, 11548470571, 142844426789, 2279343327171, 57760865728994, 979023970244321, 23510036246274433,
             771025645214210753]),
        6: SomosData(oeis_id='A006722', stash=[
             1, 1, 1, 1, 1, 1, 3, 5, 9, 23, 75, 421, 1103, 5047, 41783, 281527, 2534423, 14161887, 232663909,
             3988834875, 45788778247, 805144998681, 14980361322965, 620933643034787, 16379818848380849, 369622905371172929,
             20278641689337631649, 995586066665500470689]),
        7: SomosData(oeis_id='A006723', stash=[
             1, 1, 1, 1, 1, 1, 1, 3, 5, 9, 17, 41, 137, 769, 1925, 7203, 34081, 227321, 1737001, 14736001, 63232441,
             702617001, 8873580481, 122337693603, 1705473647525, 22511386506929, 251582370867257, 9254211194697641,
             215321535159114017]),
    }

    def __init__(self, k=4):
        self.k = k
        super().__init__()

    def __iter__(self):
        k = self.k
        if k <= 3:
            while True:
                yield 1
        else:
            queue = deque(maxlen=k)
            idx = 0
            stash = self.__somos__.get(k, SomosData(None, [])).stash
            for n in stash:
                yield n
                idx += 1
                queue.append(n)
            while idx < k:
                yield 1
                idx += 1
                queue.append(1)

            coeffs = []
            for i in range(k // 2):
                coeffs.append((k - 1 - i, 1 + i))

            while True:
                n = 0
                for i, j in coeffs:
                    n += queue[i] * queue[j]
                nq, nr = divmod(n, queue[0])
                if nr:
                    raise ValueError(f'somos({k})[{idx}]: non-integer value: {n}/{queue[0]}')
                yield nq
                queue.append(nq)
                idx += 1

    @classmethod
    def register(cls):
        def somos_builder(k):
            return lambda: cls(k)

        for k, sd in cls.__somos__.items():
            cls.register_factory(f'somos({k})', somos_builder(k),
                oeis=sd.oeis_id,
                description=f'f(n) := the n-th Somos-{k} number',
            )


class somos_break(StashMixin, Iterator):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING]
    __stash__ = [
        17, 19, 20, 22, 24, 27, 28, 30, 33, 34, 36, 39, 41, 42, 44, 46, 48, 51, 52, 55, 56, 58, 60, 62, 65, 66, 68, 70,
        72, 75, 76, 78, 81, 82, 84, 86, 88, 90, 92, 94, 96, 98, 100, 102, 104, 107, 108, 110, 112, 114, 116, 118, 120,
        123, 124, 126, 129, 130, 132, 134, 136, 138]

    def __iter__(self):
        k = 8
        for item in self.get_stash():
            yield item
            k += 1
        while True:
            somos = iter(Somos(k))
            i = 0
            while True:
                try:
                    next(somos)
                except ValueError:
                    yield i
                    break
                i += 1
            k += 1

    @classmethod
    def register(cls):
        cls.register_factory(f'somos_break', cls,
            oeis='A030127',
            description=f'f(n) := the first index at which (8+n)-Somos sequence first becomes nonintegral',
        )
