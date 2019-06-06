__all__ = [
    'gmpy2',
    'sympy',
    'numpy',
]


def _lazy_method(instance, name):
    def _lazy(*args, **kwargs):
        instance._init()
        actual_method = getattr(instance, name)
        return actual_method(*args, **kwargs)
    _lazy.__name__ = name + "__lazy"
    return _lazy


def _lazy_method_positionals_only(instance, name):
    def _lazy(*args):
        instance._init()
        actual_method = getattr(instance, name)
        return actual_method(*args)
    _lazy.__name__ = name + "__lazy"
    return _lazy


class _Gmpy2(object):
    def __init__(self):
        self.__module = None
        self.module = self._module_lazy
        self.is_integer = self._is_integer_lazy
        self.mpz = _lazy_method_positionals_only(self, 'mpz')
        self.gcd = _lazy_method(self, 'gcd')
        self.lcm = _lazy_method(self, 'lcm')
        self.fac = _lazy_method(self, 'fac')
        self.fib = _lazy_method(self, 'fib')
        self.lucas = _lazy_method(self, 'lucas')
        self.next_prime = _lazy_method(self, 'next_prime')
        self.remove = _lazy_method(self, 'remove')

    def _init(self):
        # print(">>> import gmpy2")
        import gmpy2 as gmpy2_module
        self.__gmpy2 = gmpy2_module

        def make_functions(gmpy2_module):
            mpz = gmpy2_module.mpz
            mpz_class = type(mpz(1))
            def module():
                return gmpy2_module
            def is_integer(value):
                return isinstance(value, (int, mpz_class))
            return module, is_integer
            
        self.module, self.is_integer = make_functions(gmpy2_module)
        self.mpz = gmpy2_module.mpz
        self.gcd = gmpy2_module.gcd
        self.lcm = gmpy2_module.lcm
        self.fac = gmpy2_module.fac
        self.fib = gmpy2_module.fib
        self.lucas = gmpy2_module.lucas
        self.next_prime = gmpy2_module.next_prime
        self.remove = gmpy2_module.remove

    def _is_integer_lazy(self, value):
        self._init()
        return self.is_integer(value)

    def _module_lazy(self):
        self._init()
        return self.module()


class _Sympy(object):
    def __init__(self):
        self.__module = None
        self.module = self._module_lazy
        self.symbols = _lazy_method(self, 'symbols')
        self.simplify = _lazy_method(self, 'simplify')
        self.sympify = _lazy_method(self, 'sympify')
        self.factorint = _lazy_method(self, 'factorint')
        self.divisors = _lazy_method(self, 'divisors')
        self.mobius = _lazy_method(self, 'mobius')

    def _init(self):
        # print(">>> import sympy")
        import sympy as sympy_module
        self.__sympy = sympy_module

        def make_module_function(sympy_module):
            def module():
                return sympy_module
            return module
            
        self.module = make_module_function(sympy_module)
        self.symbols = sympy_module.symbols
        self.simplify = sympy_module.simplify
        self.sympify = sympy_module.sympify
        self.factorint = sympy_module.factorint
        self.divisors = sympy_module.divisors
        self.mobius = sympy_module.mobius

    def _module_lazy(self):
        self._init()
        return self.module()


class _Numpy(object):
    def __init__(self):
        self.__module = None
        self.module = self._module_lazy
        self.ndarray = _lazy_method(self, 'ndarray')

    def _init(self):
        # print(">>> import numpy")
        import numpy as numpy_module
        self.__numpy = numpy_module

        def make_module_function(numpy_module):
            def module():
                return numpy_module
            return module
            
        self.module = make_module_function(numpy_module)
        self.ndarray = numpy_module.ndarray

    def _module_lazy(self):
        self._init()
        return self.module()


gmpy2 = _Gmpy2()
sympy = _Sympy()
numpy = _Numpy()
