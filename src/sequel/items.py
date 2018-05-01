"""
Items class
"""


from .item import Value, Item, ANY, make_item

___all__ = [
    "Items",
    "make_items",
]


def _compute_size(items):
    size = 0
    for item in items:
        if isinstance(item, Item):
            isize = item.size
            if isize is None:
                return None
            else:
                size += isize
        else:
            size += 1
    return size


class Items(tuple):
    def __new__(cls, items):
        instance = super().__new__(cls, items)
        instance.__size = _compute_size(instance)
        instance.__derivative = None
        instance.__integral = None
        return instance

    def is_fully_defined(self):
        return self.__size == len(self)

    def is_finite(self):
        return self.__size is not None

    def make_derivative(self):
        derivative = []
        values = self
        if values:
            prev = values[0]
            for value in values[1:]:
                derivative.append(value - prev)
                prev = value
        return  tuple(derivative)

    def make_integral(self):
        values = self
        cumulated_value = values[0]
        integral = [0]
        for value in values[1:]:
            integral.append(cumulated_value)
            cumulated_value += value
        return tuple(integral)

    @property
    def size(self):
        return self.__size

    @property
    def integral(self):
        if self.__integral is None:
            self.__integral = self.make_integral()
        return self.__integral

    @property
    def derivative(self):
        if self.__derivative is None:
            self.__derivative = self.make_derivative()
        return self.__derivative

    def equals(self, other):
        if len(self) != len(other):
            return False
        for s_item, o_item in zip(self, other):
            if isinstance(s_item, Item):
                if not s_item.equals(o_item):
                    return False
            elif isinstance(o_item, Item):
                if not o_item.equals(s_item):
                    return False
            else:
                if s_item != o_item:
                    return False
        return True
            

def make_items(items, simplify=True):
    lst = []
    for item in items:
        lst.append(make_item(item, simplify=simplify))
    #print(simplify, lst, Items(lst))
    return Items(lst)
