"""
Classify sequences
"""

import time

from .base import Sequence, SequenceUnknownValueError
from .trait import Trait

__all__ = [
    'classify',
    'make_stop_condition',
    'stop_condition',
]


def make_stop_condition(min_items=20, max_items=1000, max_item=10e100, max_time=5.0):
    def stop_condition(num_items, last_item, t0):
        if num_items == 0:
            return False
        if num_items < min_items:
            return False
        return num_items >= max_items or abs(last_item) >= max_item or time.time() > t0 + max_time

    return stop_condition
        

stop_condition = make_stop_condition()

def items_iterator(sequence, stop_condition=stop_condition):
    iseq = iter(sequence)
    last_item = None
    num_items = 0
    tstart = time.time()
    while not stop_condition(num_items, last_item, tstart):
        try:
            last_item = next(iseq)
        except SequenceUnknownValueError:
            break
        yield last_item
        num_items += 1


def classify(sequence, stop_condition=stop_condition):
    if isinstance(sequence, str):
        sequence = Sequence.make_sequence(sequence)
    items = items_iterator(sequence, stop_condition)
    return classify_items(items)


def get_sign(item):
    if item > 0:
        return 1
    elif item < 0:
        return -1
    else:
        return 0


def classify_items(items):
    prev_item = None
    prev_sign = None
    all_items = set()
    injective = True
    positive = True
    negative = True
    non_zero = True
    alternating = True
    increasing = True
    decreasing = True
    for item in items:
        if injective:
            if item in all_items:
                injective = False
            else:
                all_items.add(item)
        item_sign = get_sign(item)
        if item_sign == 0:
            alternating = False
            non_zero = False
        elif item_sign < 0:
            positive = False
        elif item_sign > 0:
            negative = False
        if prev_item is None:
           prev_item_sign = get_sign(item)
        else:
           if alternating:
               if item_sign == 0 or item_sign == prev_item_sign:
                   alternating = False
               prev_item_sign = item_sign
           if increasing and item < prev_item:
               increasing = False
           if decreasing and item > prev_item:
               decreasing = False
        prev_item = item
    traits = {trait: None for trait in Trait}
    traits[Trait.INJECTIVE] = injective
    traits[Trait.POSITIVE] = positive
    traits[Trait.NEGATIVE] = negative
    traits[Trait.NON_ZERO] = non_zero
    traits[Trait.ALTERNATING] = alternating
    traits[Trait.INCREASING] = increasing
    traits[Trait.DECREASING] = decreasing
    return traits
        
        
    
