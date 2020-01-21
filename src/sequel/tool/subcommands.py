"""
Main tool.
"""

import collections
import json
import shlex

from io import StringIO

from .. import VERSION
from ..config import (
    default_config,
    get_rl_history_filename,
    get_rl_init_filename,
    get_config,
    get_config_key,
    set_config,
    update_config,
    write_config,
    reset_config,
    show_config,
    edit_config,
)
from ..declaration import declared

from ..item import make_item
from ..items import make_items
from ..search import (
    create_manager,
    StopAtFirst,
    StopAtLast,
    # StopAtNum,
    StopBelowComplexity,
)
from ..sequence import compile_sequence, Sequence, generate, generate_sequences
from ..profiler import Profiler
from ..utils import assert_sequence_matches

from .display import Printer, iter_item_types
from .help_pages import create_help
from .quiz import QuizShell
from .shell import SequelShell

__all__ = [
    'main',
]


RANDOM_SEQUENCE = object()


def type_stop_below_complexity(string):
    return StopBelowComplexity(int(string))


class declist(object):
    def __init__(self, decorators):
        self.decorators = decorators

    def __call__(self, function):
        for decorator in self.decorators:
            function = decorator(function)
        return function
            

def iter_selected_sequences(found_sequences, sort=False, limit=None):
    if sort:
        found_sequences = sorted(found_sequences, key=lambda x: x.complexity())
    if limit is None:
        yield from found_sequences
    else:
        for sequence, _ in zip(found_sequences, range(limit)):
            yield sequence


def function_config_show(keys=None, sort_keys=False):
    config = get_config()
    show_config(config, keys=keys, sort_keys=sort_keys)


def function_config_write(output_config_filename=None, reset=False):
    if reset:
        config = default_config()
    else:
        config = get_config()
    write_config(config, output_config_filename)


def function_config_edit(output_config_filename=None, reset=False):
    if reset:
        config = default_config()
    else:
        config = get_config()
    config = edit_config(config)
    write_config(config, output_config_filename)
    set_config(config)


def function_config_reset():
    reset_config()


def function_show(sequence, level=None, algorithm=None, simplify=False, tree=False, inspect=False, traits=False, classify=False, doc=False):
    printer = Printer()
    if sequence is RANDOM_SEQUENCE:
        sequence = generate(level=level, algorithm=algorithm)
    else:
        sequence = compile_sequence(sequence, simplify=simplify)
    printer.print_sequence(sequence, tree=tree, inspect=inspect, traits=traits, classify=classify, doc=doc)

    
def function_doc(sequences, simplify=False, traits=False, classify=False):
    if not sequences:
        sequences = None
    else:
        for value in sequences:
            lst = []
            if isinstance(value, (list, tuple)):
                lst.extend(Sequence.iter_sequences_by_traits(*value))
            else:
                lst.append(value)
            sequences = lst
    printer = Printer()
    printer.print_doc(sources=sequences, simplify=simplify, traits=traits, classify=classify)


def function_search(sequence, limit=None, sort=False, reverse=False, handler=None, profile=False, declarations=None, simplify=False, level=None, algorithm=None):
    if sequence is RANDOM_SEQUENCE:
        rev_search = True
        sequence = generate(level=level, algorithm=algorithm)
        source = str(sequence)
        items = None
    elif isinstance(sequence, str):
        rev_search = True
        source = sequence
        sequence = compile_sequence(sequence, simplify=simplify)
        items = None
    else:
        items = sequence
        sequence = None
        source = None
        rev_search = False
    if declarations is None:
        declarations = ()
    with declared(*declarations):
        printer = Printer()
        if profile:
            profiler = Profiler()
        else:
            profiler = None
        config = get_config()
        num_items = printer.num_items
        if rev_search:
            items = sequence.get_values(num_items)
            manager = create_manager(len(items), config=config)
            found_sequences = manager.search(items, handler=handler, profiler=profiler)
            sequences = iter_selected_sequences(found_sequences, sort=sort, limit=limit)
            printer.print_rsearch(source, sequence, items, sequences)
        else:
            manager = create_manager(num_items, config=config)
            found_sequences = manager.search(items, handler=handler, profiler=profiler)
            sequences = iter_selected_sequences(found_sequences, sort=sort, limit=limit)
            printer.print_sequences(sequences, item_types=iter_item_types(items))
        if profile:
            printer.print_stats(profiler)


def function_rsearch(sources, simplify=False, sort=False, reverse=False, limit=None, handler=None, profile=False, declarations=None):
    if declarations is None:
        declarations = ()
    with declared(*declarations):
        printer = Printer()
        config = get_config()
        size = printer.num_items
        manager = create_manager(size, config=config)
        if profile:
            profiler = Profiler()
        else:
            profiler = None
        for source in sources:
            sequence = compile_sequence(source, simplify=simplify)
            items = sequence.get_values(printer.num_items)
            found_sequences = manager.search(items, handler=handler, profiler=profiler)
            sequences = iter_selected_sequences(found_sequences, sort=sort, limit=limit)
            printer.print_rsearch(source, sequence, items, sequences)
        if profile:
            printer.print_stats(profiler)
            

def function_play(level, algorithm):
    printer = Printer()
    sequence_iterator = generate_sequences(level=level, algorithm=algorithm)
    quiz_shell = QuizShell(sequence_iterator=sequence_iterator)
    quiz_shell.interact()


def function_shell():
    printer = Printer()
    shell = SequelShell(printer=printer)
    shell.interact()


def function_help(link=None, home=None, interactive=None):
    help_pages = create_help()
    help_pages.navigate(home=home, start_links=link, interactive=interactive)
