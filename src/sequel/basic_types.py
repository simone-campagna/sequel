"""
Basic types
"""

__all__ = [
    "make_integer",
]


def make_integer(value):
    if isinstance(value, str):
        value = eval(value)
    return int(value)
