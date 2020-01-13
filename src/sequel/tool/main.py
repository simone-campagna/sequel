"""
Main tool.
"""

import argparse

import argcomplete

from .. import VERSION
from ..config import (
    set_config,
    load_config,
    update_config,
    setup_config,
)
from ..item import make_item
from ..modules import load_ref
from ..search import (
    StopAtFirst,
    StopAtLast,
    StopBelowComplexity,
)

from ..sequence import (
    Sequence,
)
from ..declaration import (
    sequence_declaration,
    catalog_declaration,
)
from .subcommands import (
    function_search,
    function_rsearch,
    function_compile,
    function_doc,
    function_tree,
    function_config_show,
    function_config_write,
    function_config_reset,
    function_config_edit,
    function_generate,
    function_quiz,
    function_help,
)

__all__ = [
    'main',
]


def sequence_completer(prefix, action, parser, parsed_args):
    return list(Sequence.get_registry())


def type_stop_below_complexity(string):
    return StopBelowComplexity(int(string))


def type_config_key_value(string):
    key, value = string.split("=", 1)
    value = eval(value)
    return (key, value)


def type_range(string):
    if ':'  in string:
        left, right = string.split(":", 1)
        if left:
            left = int(left)
        else:
            left = None
        if right:
            right = int(right)
        else:
            right = None
    else:
        left = int(string)
        right = left + 1
    return (left, right)


def main():
    """Main function"""
    common_parser_kwargs = {
        'formatter_class': argparse.RawDescriptionHelpFormatter,
    }
    top_level_parser = argparse.ArgumentParser(
        description="""\
Sequel v{version} - integer sequence finder

To enable completion run the following command:

  $ eval "$(register-python-argcomplete sequel)"
""".format(version=VERSION),
        **common_parser_kwargs)

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

    top_level_parser.add_argument(
        "--version",
        action="version",
        version=VERSION)

    subparsers = top_level_parser.add_subparsers()

    common_display_args = [
        'num_items', 'item_mode', 'separator', 'item_format', 'base', 'wraps',
        'max_compact_digits', 'max_full_digits', 'colored',
    ]
    common_search_args = [
        'handler', 'profile', 'declarations',
    ]

    help_parser = subparsers.add_parser(
        'help',
        description="show help",
        **common_parser_kwargs,
    )
    help_parser.set_defaults(
        function=function_help,
        function_args=['link'],
    )
    help_parser.add_argument(
        'link',
        type=str,
        default=None,
        nargs="*",
        help='start from link')

    search_description="""\
Search sequence matching items {}

For instance:

$ sequel search 2 3 5 7 11
    0] p
    2 3 5 7 11 13 17 19 23 29 ...

The 'ANY' symbol matches with any value:

$ sequel search 2 3 5 7 ANY
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
        description=search_description.format(""),
        **common_parser_kwargs,
    )
    search_parser.set_defaults(
        function=function_search,
        function_args=['items', 'limit', 'sort', 'reverse'] + common_search_args + ['display_kwargs'])

    doc_parser = subparsers.add_parser(
        'doc',
        description="""\
Show sequence documentation""",
        **common_parser_kwargs,
    )
    doc_parser.set_defaults(
        function=function_doc,
        function_args=['sources', 'simplify', 'full'] + ['display_kwargs'])

    compile_parser = subparsers.add_parser(
        'compile',
        description="""\
Compile a sequence""",
        **common_parser_kwargs)
    compile_parser.set_defaults(
        function=function_compile,
        function_args=['sources', 'simplify', 'tree'] + ['display_kwargs'])

    generate_parser = subparsers.add_parser(
        'generate',
        description="""\
Generate a random sequence""",
        **common_parser_kwargs)
    generate_parser.set_defaults(
        function=function_generate,
        function_args=['level', 'algorithm'] + ['display_kwargs'])

    quiz_parser = subparsers.add_parser(
        'quiz',
        description="""\
Generate a random sequence and make a quiz""",
        **common_parser_kwargs)
    quiz_parser.set_defaults(
        function=function_quiz,
        function_args=['level', 'algorithm'] + ['display_kwargs'])

    tree_parser = subparsers.add_parser(
        'tree',
        description="""\
Compile a sequence and show it as a tree""",
        **common_parser_kwargs)
    tree_parser.set_defaults(
        function=function_tree,
        function_args=['sources', 'simplify'] + ['display_kwargs'])

    config_parser = subparsers.add_parser(
        'config',
        description="""\
Show config file""",
        **common_parser_kwargs)
    config_parser.set_defaults(
        function=function_config_show,
        function_args=[])

    config_subparsers = config_parser.add_subparsers()

    config_show_parser = config_subparsers.add_parser(
        'show',
        description="""\
Show config file""",
        **common_parser_kwargs)
    config_show_parser.set_defaults(
        function=function_config_show,
        function_args=[])

    config_write_parser = config_subparsers.add_parser(
        'write',
        description="""\
Write config file""",
        **common_parser_kwargs)
    config_write_parser.set_defaults(
        function=function_config_write,
        function_args=["output_config_filename", "reset"])

    config_edit_parser = config_subparsers.add_parser(
        'edit',
        description="""\
Edit config file""",
        **common_parser_kwargs)
    config_edit_parser.set_defaults(
        function=function_config_edit,
        function_args=["output_config_filename", "reset"])

    for parser in config_write_parser, config_edit_parser:
        parser.add_argument(
            "-r", "--reset",
            action="store_true",
            default=False,
            help="reset to default values")

        parser.add_argument(
            "-o", "--output-config-filename",
            type=str,
            default=None,
            help="output config filename")

    config_reset_parser = config_subparsers.add_parser(
        'reset',
        description="""\
Reset config file""",
        **common_parser_kwargs)
    config_reset_parser.set_defaults(
        function=function_config_reset,
        function_args=[])

    rsearch_parser = subparsers.add_parser(
        'rsearch',
        description="""\
Reverse search: compile a sequence and tries to search it""",
        **common_parser_kwargs)
    rsearch_parser.set_defaults(
        function=function_rsearch,
        function_args=['sources', 'simplify', 'limit', 'sort', 'reverse'] + common_search_args + ['display_kwargs'])

    for parser in compile_parser, rsearch_parser, doc_parser, tree_parser:
        parser.add_argument(
            "-s", "--simplify",
            action="store_true",
            default=False,
            help="simplify expression")

    for parser in search_parser, compile_parser, rsearch_parser, doc_parser, tree_parser, generate_parser, quiz_parser:
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

    for parser in search_parser, rsearch_parser:
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

        parser.add_argument(
            "-d", "--declare-sequence",
            dest="declarations",
            metavar="[N:=]SEQ",
            action="append",
            type=sequence_declaration,
            help="declare a new sequence, i.e. newseq=ifelse(pentagonal%%2==0, p, 1000-m_exp)")

        parser.add_argument(
            "-c", "--catalog-file",
            dest="declarations",
            metavar="FILE",
            action="append",
            type=catalog_declaration,
            help="add a catalog file containing additional sequence declarations")

    for parser in search_parser, rsearch_parser:
        parser.add_argument(
            "-p", "--profile",
            action="store_true",
            default=False,
            help="show timing stats")

    for parser in search_parser,:
        parser.add_argument(
            "items",
            nargs='+',
            type=make_item,
            help="sequence items")

    compile_parser.add_argument(
        '-t', '--tree',
        action='store_true',
        default=False,
        help="show sequence tree")

    for parser in rsearch_parser, compile_parser, tree_parser:
        parser.add_argument(
            "sources",
            type=str,
            nargs='+',
            help="sequence source").completer = sequence_completer

    for parser in doc_parser,:
        parser.add_argument(
            "sources",
            type=str,
            nargs='*',
            help="sequence source").completer = sequence_completer

        parser.add_argument(
            "-t", "--full",
            default=False,
            action="store_true",
            help="full output")

    for parser in search_parser, rsearch_parser:
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
            dest="handler", default=None, metavar='C',
            type=type_stop_below_complexity,
            help="stop when below complexity")

    for parser in generate_parser, quiz_parser:
        parser.add_argument(
            "--level",
            default=None,
            type=type_range,
            help="set level, e.g. '2', ':3', '2:5'")
        parser.add_argument(
            "--algorithm",
            default=None,
            type=str,
            help="set algorithm name")

    argcomplete.autocomplete(top_level_parser)
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
