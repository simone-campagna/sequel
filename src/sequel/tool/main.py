"""
Main tool.
"""

import argparse
import functools

import argcomplete

from .. import VERSION
from ..config import (
    set_config,
    load_config,
    update_config,
    merge_config,
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
    Trait,
)
from ..declaration import (
    sequence_declaration,
    catalog_declaration,
)
from .subcommands import (
    RANDOM_SEQUENCE,
    function_search,
    function_rsearch,
    function_show,
    function_doc,
    function_config_show,
    function_config_write,
    function_config_reset,
    function_config_edit,
    function_shell,
    function_play,
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


def create_parser(*args, function, function_args, subparsers=None, **kwargs):
    if subparsers:
        parser = subparsers.add_parser(*args, **kwargs)
    else:
        parser = argparse.ArgumentParser(*args, **kwargs)
    f_args = []
    for arg in function_args:
        _ARGS[arg](parser)
        f_args.append(arg.split(":", 1)[0])
    if function is _HELP:
        function = parser.print_help
        f_args = []
    parser.set_defaults(
        function=function,
        function_args=f_args)
    return parser


_HELP = object()
_ARGS = {}

def arg(name, **kwargs):
    def arg_decorator(fun):
        if kwargs:
            fun = functools.partial(fun, **kwargs)
        _ARGS[name] = fun
        return fun
    return arg_decorator
    

@arg('pymodules')
def add_load_argument(parser):
    parser.add_argument(
        "-l", "--load",
        metavar="F",
        dest="pymodules", default=[], type=str, action="append",
        help="python module")


@arg('config')
def add_config_argument(parser):
    parser.add_argument(
        "-c", "--config",
        metavar="F",
        dest="config_filename", default=None, type=str,
        help="config filename")


@arg('config_keys')
def add_config_keys_argument(parser):
    parser.add_argument(
        "-k", "--set-key",
        metavar="K=V",
        dest="config_keys", default=[], type=type_config_key_value,
        action="append",
        help="set config key")


@arg('reset')
def add_reset_argument(parser):
    parser.add_argument(
        "-r", "--reset",
        action="store_true",
        default=False,
        help="reset to default values")


@arg('output_config_filename')
def add_output_config_filename_argument(parser):
    parser.add_argument(
        "-o", "--output-config-filename",
        type=str,
        default=None,
        help="output config filename")


@arg('simplify')
def add_simplify_argument(parser):
    parser.add_argument(
        "-s", "--simplify",
        action="store_true",
        default=False,
        help="simplify expression")


@arg('handler')
def add_handler_argument(parser):
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


@arg('profile')
def add_profile_argument(parser):
    parser.add_argument(
        "-p", "--profile",
        action="store_true",
        default=False,
        help="show timing stats")


@arg('interactive')
def add_interactive_argument(parser):
    int_grp = parser.add_mutually_exclusive_group()
    int_grp.add_argument(
        '-i', '--interactive',
        dest='interactive', default=None,
        action='store_true',
        help='interactive mode')
    int_grp.add_argument(
        '-I', '--no-interactive',
        dest='interactive', default=None,
        action='store_false',
        help='non interactive mode')


@arg('home')
def add_home_argument(parser):
    parser.add_argument(
        '-H', '--home',
        type=str,
        default=None,
        help="set home page")


@arg('link')
def add_link_argument(parser):
    parser.add_argument(
        'link',
        type=str,
        default=None,
        nargs="*",
        help='go to page (not interactive)')


# REM @arg('items')
# REM def add_items_argument(parser):
# REM     parser.add_argument(
# REM         "items",
# REM         nargs='+',
# REM         type=make_item,
# REM         help="sequence items")


@arg('limit')
def add_limit_argument(parser):
    parser.add_argument(
        "-L", "--limit",
        metavar="L",
        type=int,
        default=None,
        help="max number of results")


@arg('sort')
def add_sort_argument(parser):
    parser.add_argument(
        "-t", "--sort",
        action="store_true",
        default=False,
        help="sort by complexity")


@arg('reverse')
def add_reverse_argument(parser):
    parser.add_argument(
        "-R", "--reverse",
        action="store_true",
        default=False,
        help="reverse sorting")


@arg('declarations')
def add_declarations_argument(parser):
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


@arg('num_items')
def add_num_items_argument(parser):
    parser.add_argument(
        "-n", "--num-items",
        metavar="N",
        type=int,
        default=10,
        help="num items to show")


@arg('item_mode')
def add_item_mode_argument(parser):
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


@arg('wraps')
def add_wraps_argument(parser):
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


@arg('colored')
def add_colored_argument(parser):
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


@arg('separator')
def add_separator_argument(parser):
    parser.add_argument(
        "-z", "--separator",
        metavar="S",
        type=str,
        default=None,
        help="item separator (oneline mode only)")


@arg('item_format')
def add_item_format_argument(parser):
    parser.add_argument(
        "-f", "--item-format",
        metavar="F",
        type=str,
        default=None,
        help="item format")


@arg('base')
def add_base_argument(parser):
    parser.add_argument(
        "-b", "--base",
        metavar="B",
        type=int,
        default=None,
        help="set base")


@arg('max_compact_digits')
def add_max_compact_digits_argument(parser):
    parser.add_argument(
        "-C", "--max-compact-digits",
        metavar="N",
        type=int,
        default=None,
        help="maximum number of digits for compact item display")


@arg('max_full_digits')
def add_max_full_digits_argument(parser):
    parser.add_argument(
        "-F", "--max-full-digits",
        metavar="N",
        type=int,
        default=None,
        help="maximum number of digits for full item display")


@arg('tree')
def add_base_argument(parser):
    parser.add_argument(
        '-t', '--tree',
        action='store_true',
        default=False,
        help="show sequence tree")


@arg('inspect')
def add_inspect_argument(parser):
    parser.add_argument(
        '-i', '--inspect',
        action='store_true',
        default=False,
        help="inspect sequence")


@arg('traits')
def add_traits_argument(parser):
    parser.add_argument(
        '-T', '--traits',
        action='store_true',
        default=False,
        help="show sequence traits")


@arg('classify')
def add_classify_argument(parser):
    parser.add_argument(
        '-c', '--classify',
        action='store_true',
        default=False,
        help="classify sequence by traits")


@arg('doc')
def add_doc_argument(parser):
    parser.add_argument(
        '-d', '--doc',
        action='store_true',
        default=False,
        help="print sequence doc")


@arg('sequences')
def add_sequences_argument(parser):
    parser.add_argument(
        "-e", "--expressions",
        dest='sequences',
        metavar='EXPR',
        default=None,
        action="append", type=str,
        help="sequence expression").completer = sequence_completer
    parser.add_argument(
        "-b", "--by-traits",
        dest='sequences',
        metavar='TRAIT[,TRAIT,...]',
        default=None,
        choices=list(Trait),
        action="append", type=Trait.__getitem__, nargs='+',
        help="sequence expression").completer = sequence_completer


@arg('sequence:required', required=True, items=False, gname="sequence")
@arg('sequence:with-items', required=False, items=True, gname="input")
def add_sequence_argument(parser, required, items=False, gname=""):
    group = parser.add_argument_group(gname)
    mgroup = group.add_mutually_exclusive_group(required=required)
    default = None
    mgroup.add_argument(
        "-e", "--expression",
        dest="sequence",
        metavar='EXPR',
        default=default,
        action="store", type=str, nargs='?',
        help="sequence expression").completer = sequence_completer
    mgroup.add_argument(
        "-r", "--random",
        dest="sequence", default=default,
        action="store_const", const=RANDOM_SEQUENCE,
        help="generate a random sequence")
    if items:
        mgroup.add_argument(
            "-i", "--items",
            metavar='INT',
            dest="sequence", default=default,
            type=int, nargs='+',
            help="sequence items")
    


@arg('level')
def add_level_argument(parser):
    parser.add_argument(
        "-l", "--level",
        default=None,
        type=type_range,
        help="set level, e.g. '2', ':3', '2:5'")


@arg('algorithm')
def add_algorithm_argument(parser):
    parser.add_argument(
        "-a", "--algorithm",
        default=None,
        type=str,
        help="set algorithm name")

def main():
    """Main function"""
    common_parser_kwargs = {
        'formatter_class': argparse.RawDescriptionHelpFormatter,
    }
    common_display_args = [
        'num_items', 'item_mode', 'separator', 'item_format', 'base', 'wraps',
        'max_compact_digits', 'max_full_digits', 'colored',
    ]

    # TOP-LEVEL
    parser = create_parser(
        description="""\
Sequel v{version} - integer sequence finder

To enable completion run the following command:

  $ eval "$(register-python-argcomplete sequel)"
""".format(version=VERSION),
        function=_HELP, function_args=['pymodules', 'config', 'config_keys'] + common_display_args,
        **common_parser_kwargs)

    parser.add_argument(
        "--version",
        action="version",
        version=VERSION)

    subparsers = parser.add_subparsers()

    ### HELP
    help_parser = create_parser(
        'help',
        subparsers=subparsers,
        description="show help",
        function=function_help,
        function_args=['home', 'link', 'interactive'],
        **common_parser_kwargs)

    # SHELL
    shell_parser = create_parser(
        'shell',
        description="open a Sequel Shell",
        subparsers=subparsers,
        function=function_shell,
        function_args=[],
        **common_parser_kwargs)


    # SEARCH:
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
    search_parser = create_parser(
        'search',
        description=search_description.format(""),
        subparsers=subparsers,
        function=function_search,
        function_args=['sequence:with-items', 'limit', 'sort', 'reverse', 'simplify',
                       'handler', 'profile', 'declarations', 'level', 'algorithm'],
        **common_parser_kwargs)

    # DOC
    doc_parser = create_parser(
        'doc',
        description="""\
Show sequence documentation""",
        subparsers=subparsers,
        function=function_doc,
        function_args=['sequences', 'simplify', 'traits', 'classify'],
        **common_parser_kwargs)

    # SHOW
    show_parser = create_parser(
        'show',
        description="""\
Show a sequence""",
        subparsers=subparsers,
        function=function_show,
        function_args=['sequence:required', 'simplify', 'tree', 'inspect', 'traits', 'classify', 'doc', 'level', 'algorithm'],
        **common_parser_kwargs)

    # PLAY
    play_parser = create_parser(
        'play',
        description="""\
Play the sequence game. Sequel will generate a random sequence and make you a quiz""",
        subparsers=subparsers,
        function=function_play,
        function_args=['level', 'algorithm'],
        **common_parser_kwargs)

    # CONFIG
    config_parser = create_parser(
        'config',
        description="""\
Show config file""",
        subparsers=subparsers,
        function=function_config_show,
        function_args=[],
        **common_parser_kwargs)

    config_subparsers = config_parser.add_subparsers()

    # CONFIG SHOW
    config_show_parser = create_parser(
        'show',
        description="""\
Show config file""",
        subparsers=config_subparsers,
        function=function_config_show,
        function_args=[],
        **common_parser_kwargs)

    # CONFIG WRITE
    config_write_parser = create_parser(
        'write',
        description="""\
Write config file""",
        subparsers=config_subparsers,
        function=function_config_write,
        function_args=["output_config_filename", "reset"],
        **common_parser_kwargs)

    # CONFIG EDIT
    config_edit_parser = create_parser(
        'edit',
        description="""\
Edit config file""",
        subparsers=config_subparsers,
        function=function_config_edit,
        function_args=["output_config_filename", "reset"],
        **common_parser_kwargs)

    # CONFIG RESET
    config_reset_parser = create_parser(
        'reset',
        description="""\
Reset config file""",
        subparsers=config_subparsers,
        function=function_config_reset,
        function_args=[],
        **common_parser_kwargs)


    argcomplete.autocomplete(parser)
    namespace = parser.parse_args()

    config = load_config(namespace.config_filename)
    setup_config(config)

    for pymodule in namespace.pymodules:
        load_ref(pymodule)

    display_kwargs = {}
    for arg in common_display_args:
        value = getattr(namespace, arg)
        if value is not None:
            display_kwargs[arg] = value

    for key, value in namespace.config_keys:
        update_config(config, key, value)

    merge_config(config['display'], display_kwargs)

    set_config(config)
    kwargs = {arg: getattr(namespace, arg) for arg in namespace.function_args}
    result = namespace.function(**kwargs)
    return result


if __name__ == "__main__":
    main()
