"""
Main tool.
"""

import argparse
import collections
import itertools
import json
import os
import sys
import textwrap

from .item import make_item
from .catalog import create_catalog
from .config import (
    default_config,
    get_config,
    set_config,
    load_config,
    dump_config,
    write_config,
    reset_config,
    update_config,
    setup_config,
)
from .display import Printer
from .modules import load_ref
from .hierarchical_search import search, create_algorithm
from .search import (
    create_manager,
    StopAtFirst,
    StopAtLast,
    StopBelowComplexity,
)
from .sequence import Sequence
from .profiler import Profiler


__all__ = [
    'main',
]


def make_printer(display_kwargs):
    if display_kwargs is None:
        display_kwargs = {}
    return Printer(**display_kwargs)

    
def function_test(sources, simplify=False, sort=False, reverse=False, limit=None, display_kwargs=None, handler=None):
    printer = make_printer(display_kwargs)
    config = get_config()
    size = printer.num_items
    manager = create_manager(size, config=config)
    for source in sources:
        print(printer.bold("###") + " compiling " + printer.bold(str(source)) + " ...")
        sequence = Sequence.compile(source, simplify=simplify)
        printer.print_sequence(sequence)
        items = sequence.get_values(printer.num_items)
        print(printer.bold("###") + " searching " + printer.bold(" ".join(printer.repr_items(items))) + " ...")
        if limit is None:
            counter = itertools.count()
        else:
            counter = range(limit)
        found_sequences = manager.search(items, handler=handler)
        if sort:
            found_sequences = sorted(found_sequences, key=lambda x: x.complexity(), reverse=reverse)
        found = False
        best_match, best_match_complexity = None, 1000000
        for count, found_sequence in zip(counter, found_sequences):
            header = "{:>5d}] ".format(count)
            if sequence.equals(found_sequence):
                found = True
                header += "[*] "
            else:
                header += "    "
            complexity = found_sequence.complexity()
            if best_match_complexity > complexity:
                best_match, best_match_complexity = found_sequence, complexity
            printer.print_sequence(found_sequence, num_items=0, header=header)
        if found:
            print("sequence {}: found".format(sequence))
        else:
            if best_match is not None:
                print("sequence {}: found as {}".format(sequence, best_match))
            else:
                print("sequence {}: *not* found".format(sequence))
            

def function_htest(sources, simplify=False, sort=False, reverse=False, limit=None, max_depth=10, max_rank=10, log=False, profile=False, display_kwargs=None):
    printer = make_printer(display_kwargs)
    config = get_config()
    size = printer.num_items
    catalog = create_catalog(size)
    algorithm = create_algorithm(size=size, config=config)
    if profile:
        profiler = Profiler()
    else:
        profiler = None
    for source in sources:
        print(printer.bold("###") + " compiling " + printer.bold(str(source)) + " ...")
        sequence = Sequence.compile(source, simplify=simplify)
        printer.print_sequence(sequence)
        items = sequence.get_values(printer.num_items)
        print(printer.bold("###") + " searching " + printer.bold(" ".join(printer.repr_items(items))) + " ...")
        if limit is None:
            counter = itertools.count()
        else:
            counter = range(limit)
        found_sequences = algorithm.search(catalog, items, max_depth=max_depth, max_rank=max_rank, log=log, profiler=profiler)
        if sort:
            found_sequences = sorted(found_sequences, key=lambda x: x.complexity(), reverse=reverse)
        found = False
        best_match, best_match_complexity = None, 1000000
        for count, found_sequence in zip(counter, found_sequences):
            header = "{:>5d}] ".format(count)
            if sequence.equals(found_sequence):
                found = True
                header += "[*] "
            else:
                header += "    "
            complexity = found_sequence.complexity()
            if best_match_complexity > complexity:
                best_match, best_match_complexity = found_sequence, complexity
            printer.print_sequence(found_sequence, num_items=0, header=header)
        if found:
            print("sequence {}: found".format(sequence))
        else:
            if best_match is not None:
                print("sequence {}: found as {}".format(sequence, best_match))
            else:
                print("sequence {}: *not* found".format(sequence))
    if profile:
        printer.print_stats(profiler)
            

def function_config_show():
    config = get_config()
    print(json.dumps(config, indent=4))


def function_config_write(output_config_filename=None, reset=False):
    if reset:
        config = default_config()
    else:
        config = get_config()
    write_config(config, output_config_filename)


def function_config_reset():
    reset_config()


def function_compile(sources, simplify=False, display_kwargs=None):
    printer = make_printer(display_kwargs)
    for source in sources:
        sequence = Sequence.compile(source, simplify=simplify)
        printer.print_sequence(sequence)

    
def function_tree(sources, simplify=False, display_kwargs=None):
    printer = make_printer(display_kwargs)
    for source in sources:
        sequence = Sequence.compile(source, simplify=simplify)
        printer.print_tree(sequence)

    
def function_doc(sources, simplify=False, full=False, display_kwargs=None):
    printer = make_printer(display_kwargs)
    if not sources:
        sources = [str(sequence) for sequence in Sequence.get_registry().values()]
    first = True
    for source in sorted(sources):
        if not first:
            print()
        first = False
        sequence = Sequence.compile(source, simplify=simplify)
        printer.print_doc(sequence, full=full)


def function_search(items, limit=None, sort=False, reverse=False, display_kwargs=None, handler=None):
    printer = make_printer(display_kwargs)
    if limit is None:
        counter = itertools.count()
    else:
        counter = range(limit)
    config = get_config()
    size = len(items)
    manager = create_manager(size, config=config)
    found_sequences = manager.search(items, handler=handler)
    if sort:
        found_sequences = sorted(found_sequences, key=lambda x: x.complexity(), reverse=reverse)
    for count, sequence in zip(counter, found_sequences):
        header = "{:>5d}] ".format(count)
        printer.print_sequence(sequence, header=header, num_known=len(items))


def function_hsearch(items, limit=None, sort=False, reverse=False, max_depth=10, max_rank=10, log=False, profile=False, display_kwargs=None):
    printer = make_printer(display_kwargs)
    if limit is None:
        counter = itertools.count()
    else:
        counter = range(limit)
    config = get_config()
    size = len(items)
    catalog = create_catalog(size)
    algorithm = create_algorithm(size=size, config=config)
    if profile:
        profiler = Profiler()
    else:
        profiler = None
    found_sequences = algorithm.search(catalog, items, max_depth=max_depth, max_rank=max_rank, log=log, profiler=profiler)
    if sort:
        found_sequences = sorted(found_sequences, key=lambda x: x.complexity(), reverse=reverse)
    for count, sequence in zip(counter, found_sequences):
        header = "{:>5d}] ".format(count)
        printer.print_sequence(sequence, header=header, num_known=len(items))
    if profile:
        printer.print_stats(profiler)


def type_stop_below_complexity(string):
    return StopBelowComplexity(int(string))


def type_config_key_value(string):
    key, value = string.split("=", 1)
    value = eval(value)
    return (key, value)


def main():
    """Main function"""
    top_level_parser = argparse.ArgumentParser(
        description="""\
Sequitur
""")
    top_level_parser.set_defaults(
        function=top_level_parser.print_help,
        function_args=[])

    top_level_parser.add_argument(
        "-l", "--load",
        metavar="F",
        dest="pymodules", default=[], type=str, action="append",
        help="python module")

    top_level_parser.add_argument(
        "-c", "--config",
        metavar="F",
        dest="config_filename", default=None, type=str,
        help="config filename")

    top_level_parser.add_argument(
        "-k", "--set-key",
        metavar="K=V",
        dest="config_keys", default=[], type=type_config_key_value,
        action="append",
        help="set config key")

    subparsers = top_level_parser.add_subparsers()

    common_display_args = [
        'num_items', 'item_mode', 'separator', 'item_format', 'base', 'wraps',
        'max_compact_digits', 'max_full_digits', 'colored',
    ]
    common_hsearch_args = [
        'max_depth', 'max_rank', 'log', 'profile',
    ]
    common_search_args = [
        'handler',
    ]
    search_description="""\
Search sequence matching items {}

For instance:

$ sequel search 2 3 5 7 11
    0] p
    2 3 5 7 11 13 17 19 23 29 ...

The '??' symbol matches with any value:

$ sequel search 2 3 5 7 ??
    0] p
    2 3 5 7 11 13 17 19 23 29 ...
    1] m_exp
    2 3 5 7 13 17 19 31 61 89 ...

A value MIN..MAX matches with any value with MIN <= value <= MAX:

$ sequel search 2 3 5 7 12..20
    0] m_exp
    2 3 5 7 13 17 19 31 61 89 ...

"""
    search_parser = subparsers.add_parser(
        'search',
        description=search_description.format("")
    )
    search_parser.set_defaults(
        function=function_search,
        function_args=['items', 'limit', 'sort', 'reverse'] + common_search_args + ['display_kwargs'])

    hsearch_parser = subparsers.add_parser(
        'hsearch',
        description=search_description.format("using the hierarchical algorithm")
    )
    hsearch_parser.set_defaults(
        function=function_hsearch,
        function_args=['items', 'limit', 'sort', 'reverse'] + common_hsearch_args + ['display_kwargs'])

    doc_parser = subparsers.add_parser(
        'doc',
        description="""\
Show sequence documentation""")
    doc_parser.set_defaults(
        function=function_doc,
        function_args=['sources', 'simplify', 'full'] + ['display_kwargs'])

    compile_parser = subparsers.add_parser(
        'compile',
        description="""\
Compile a sequence""")
    compile_parser.set_defaults(
        function=function_compile,
        function_args=['sources', 'simplify'] + ['display_kwargs'])

    tree_parser = subparsers.add_parser(
        'tree',
        description="""\
Compile a sequence and show it as a tree""")
    tree_parser.set_defaults(
        function=function_tree,
        function_args=['sources', 'simplify'] + ['display_kwargs'])

    config_parser = subparsers.add_parser(
        'config',
        description="""\
Show config file""")
    config_parser.set_defaults(
        function=function_config_show,
        function_args=[])

    config_subparsers = config_parser.add_subparsers()

    config_show_parser = config_subparsers.add_parser(
        'show',
        description="""\
Show config file""")
    config_show_parser.set_defaults(
        function=function_config_show,
        function_args=[])

    config_write_parser = config_subparsers.add_parser(
        'write',
        description="""\
Write config file""")
    config_write_parser.set_defaults(
        function=function_config_write,
        function_args=["output_config_filename", "reset"])

    config_write_parser.add_argument(
        "-r", "--reset",
        action="store_true",
        default=False,
        help="reset to default values")

    config_write_parser.add_argument(
        "-o", "--output-config-filename",
        type=str,
        default=None,
        help="output config filename")

    config_reset_parser = config_subparsers.add_parser(
        'reset',
        description="""\
Reset config file""")
    config_reset_parser.set_defaults(
        function=function_config_reset,
        function_args=[])

    test_parser = subparsers.add_parser(
        'test',
        description="""\
Compile a sequence and tries to search it""")
    test_parser.set_defaults(
        function=function_test,
        function_args=['sources', 'simplify', 'limit', 'sort', 'reverse'] + common_search_args + ['display_kwargs'])

    htest_parser = subparsers.add_parser(
        'htest',
        description="""\
Compile a sequence and tries to search it using the hierarchical algorithm""")
    htest_parser.set_defaults(
        function=function_htest,
        function_args=['sources', 'simplify', 'limit', 'sort', 'reverse'] + common_hsearch_args + ['display_kwargs'])

    for parser in compile_parser, htest_parser, test_parser, doc_parser, tree_parser:
        parser.add_argument(
            "-s", "--simplify",
            action="store_true",
            default=False,
            help="simplify expression")

    for parser in hsearch_parser, search_parser, compile_parser, htest_parser, test_parser, doc_parser, tree_parser:
        parser.add_argument(
            "-n", "--num-items",
            metavar="N",
            type=int,
            default=10,
            help="num items to show")

        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            "-m", "--multiline",
            dest="item_mode", action="store_const", const="multiline",
            default=None,
            help="multiline item mode")

        mode_group.add_argument(
            "-o", "--oneline",
            dest="item_mode", action="store_const", const="oneline",
            default=None,
            help="oneline item mode")

        wraps_group = parser.add_mutually_exclusive_group()
        wraps_group.add_argument(
            "-w", "--wraps",
            dest="wraps", action="store_true",
            default=None,
            help="wraps items line (oneline mode only)")

        wraps_group.add_argument(
            "-W", "--no-wraps",
            dest="wraps", action="store_false",
            default=None,
            help="no wraps items line (oneline mode only)")

        colored_group = parser.add_mutually_exclusive_group()
        colored_group.add_argument(
            "-x", "--colored",
            dest="colored", action="store_true",
            default=None,
            help="enables colored output")

        colored_group.add_argument(
            "-X", "--no-colored",
            dest="colored", action="store_false",
            default=None,
            help="disable colored output")

        parser.add_argument(
            "-z", "--separator",
            metavar="S",
            type=str,
            default=None,
            help="item separator (oneline mode only)")

        parser.add_argument(
            "-f", "--item-format",
            metavar="F",
            type=str,
            default=None,
            help="item format")

        parser.add_argument(
            "-b", "--base",
            metavar="B",
            type=int,
            default=None,
            help="set base")

        parser.add_argument(
            "-C", "--max-compact-digits",
            metavar="N",
            type=int,
            default=None,
            help="maximum number of digits for compact item display")

        parser.add_argument(
            "-F", "--max-full-digits",
            metavar="N",
            type=int,
            default=None,
            help="maximum number of digits for full item display")

    for parser in hsearch_parser, htest_parser, search_parser, test_parser:
        parser.add_argument(
            "-l", "--limit",
            metavar="L",
            type=int,
            default=None,
            help="max number of results")

        parser.add_argument(
            "-t", "--sort",
            action="store_true",
            default=False,
            help="sort by complexity")

        parser.add_argument(
            "-R", "--reverse",
            action="store_true",
            default=False,
            help="reverse sorting")

    for parser in hsearch_parser, htest_parser:
        parser.add_argument(
            "-d", "--max-depth",
            metavar="D",
            default=10,
            type=int,
            help="max search depth")

        parser.add_argument(
            "-k", "--max-rank",
            metavar="R",
            default=10,
            type=int,
            help="max search rank")

        parser.add_argument(
            "-p", "--profile",
            action="store_true",
            default=False,
            help="show timing stats")

        parser.add_argument(
            "-L", "--log",
            default=False,
            action="store_true",
            help="enable logging")

    for parser in hsearch_parser, search_parser:
        parser.add_argument(
            "items",
            nargs='+',
            type=make_item,
            help="sequence items")

    for parser in htest_parser, test_parser, compile_parser, tree_parser:
        parser.add_argument(
            "sources",
            type=str,
            nargs='+',
            help="sequence source")

    for parser in doc_parser,:
        parser.add_argument(
            "sources",
            type=str,
            nargs='*',
            help="sequence source")

        parser.add_argument(
            "-t", "--full",
            default=False,
            action="store_true",
            help="full output")

    for parser in search_parser, test_parser:
        handler_group = parser.add_mutually_exclusive_group()
        handler_group.add_argument(
            "--first",
            dest="handler", default=None,
            action="store_const",
            const=StopAtFirst(),
            help="stop search at first results")

        handler_group.add_argument(
            "--last",
            dest="handler", default=None,
            action="store_const",
            const=StopAtLast(),
            help="never stops search")

        handler_group.add_argument(
            "--complexity",
            dest="handler", default=None,
            type=type_stop_below_complexity,
            help="stop when below complexity")

    namespace = top_level_parser.parse_args()
    if 'display_kwargs' in namespace.function_args:
        display_kwargs = {}
        for arg in common_display_args:
            display_kwargs[arg] = getattr(namespace, arg)
        namespace.display_kwargs = display_kwargs

    config = load_config(namespace.config_filename)
    setup_config(config)

    for pymodule in namespace.pymodules:
        load_ref(pymodule)

    for key, value in namespace.config_keys:
        update_config(config, key, value)
    set_config(config)
    kwargs = {arg: getattr(namespace, arg) for arg in namespace.function_args}
    result = namespace.function(**kwargs)
    return result


if __name__ == "__main__":
    main()
