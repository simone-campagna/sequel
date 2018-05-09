import sympy


__all__ = [
    "MOCK_CLASSES",
]


# class SympyMock(sympy.Function):
#     def __new__(cls, *args, **kwargs):
#         return super().__new__(cls)
# 
#     def __init__(self, *args, **kwargs):
#         pass
# 

# class compose(SympyMock):
#     pass
# 
# 
# class summation(SympyMock):
#     pass
# 
# 
# class product(SympyMock):
#     pass
# 
# 
# class integral(SympyMock):
#     pass
# 
# 
# class derivative(SympyMock):
#     pass
# 
# 
# class roundrobin(SympyMock):
#     pass
# 

# class Geometric(SympyMock):
#     pass


class integral(sympy.Function):
    def __new__(cls, base=None):
        return super().__new__(cls, base)

    def __init__(self, base=None):
        pass


class Geometric(sympy.Function):
    def __new__(cls, base=None):
        return super().__new__(cls, base)

    def __init__(self, base=None):
        pass


MOCK_CLASSES = {
    'Geometric': Geometric,
}
