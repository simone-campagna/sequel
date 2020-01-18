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


def make_printer(display_kwargs=None):
    if display_kwargs is None:
        display_kwargs = {}
    return Printer(**display_kwargs)


# def type_stop_at_num(string):
#     return StopAtNum(int(string))


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


def function_compile(sources, simplify=False, tree=False, display_kwargs=None):
    printer = make_printer(display_kwargs)
    if tree:
        print_function = printer.print_tree
    else:
        print_function = printer.print_sequence
    for source in sources:
        sequence = compile_sequence(source, simplify=simplify)
        print_function(sequence)

    
def function_tree(sources, simplify=False, display_kwargs=None):
    printer = make_printer(display_kwargs)
    for source in sources:
        sequence = compile_sequence(source, simplify=simplify)
        printer.print_tree(sequence)

    
def function_doc(sources, simplify=False, full=False, display_kwargs=None):
    if not sources:
        sources = None
    printer = make_printer(display_kwargs)
    printer.print_doc(sources=sources, simplify=simplify, full=full)


def function_search(items, limit=None, sort=False, reverse=False, display_kwargs=None, handler=None, profile=False, declarations=None):
    if declarations is None:
        declarations = ()
    with declared(*declarations):
        printer = make_printer(display_kwargs)
        if profile:
            profiler = Profiler()
        else:
            profiler = None
        config = get_config()
        size = len(items)
        manager = create_manager(size, config=config)
        found_sequences = manager.search(items, handler=handler, profiler=profiler)
        sequences = iter_selected_sequences(found_sequences, sort=sort, limit=limit)
        printer.print_sequences(sequences, item_types=iter_item_types(items))
        if profile:
            printer.print_stats(profiler)


def function_rsearch(sources, simplify=False, sort=False, reverse=False, limit=None, display_kwargs=None, handler=None, profile=False, declarations=None):
    if declarations is None:
        declarations = ()
    with declared(*declarations):
        printer = make_printer(display_kwargs)
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
            

def function_generate(level, algorithm, display_kwargs=None):
    printer = make_printer(display_kwargs)
    sequence = generate(level=level, algorithm=algorithm)
    if sequence is not None:
        printer.print_doc(sources=[sequence])


def function_play(level, algorithm, display_kwargs=None):
    printer = make_printer(display_kwargs)
    sequence_iterator = generate_sequences(level=level, algorithm=algorithm)
    quiz_shell = QuizShell(sequence_iterator=sequence_iterator)
    quiz_shell.interact()


def function_shell(display_kwargs=None):
    printer = make_printer(display_kwargs)
    shell = SequelShell(printer=printer)
    shell.interact()


def function_help(link=None, home=None, interactive=None):
    help_pages = create_help()
    help_pages.navigate(home=home, start_links=link, interactive=interactive)
