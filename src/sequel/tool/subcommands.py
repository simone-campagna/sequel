"""
Main tool.
"""

import collections
import json
import shlex

from io import StringIO

from shells_kitchen import (
    Interpreter, argument, command, group, topic,
    filter_completion,
    QUIT, IGNORE, HISTORY,
)

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
)
from ..item import make_item
from ..items import make_items
from ..search import create_manager
from ..sequence import compile_sequence, Sequence
from ..profiler import Profiler
from ..utils import assert_sequence_matches

from .display import Printer

__all__ = [
    'main',
]


def make_printer(display_kwargs=None):
    if display_kwargs is None:
        display_kwargs = {}
    return Printer(**display_kwargs)


class SequelShell(Interpreter):
    __example_line_prefix__ = "  "
    __simplify_argument__ = argument('-s', '--simplify', action='store_true', default=False, help='simplify expressions')

    def __init__(self, printer=None):
        if printer is None:
            printer = make_printer()
        config = get_config()
        colored = config['display']['colored']
        self.line_prefix = "    "
        super().__init__(
            color=colored,
            history_filename=get_rl_history_filename(),
            init_filename=get_rl_init_filename(),
            default=IGNORE,
            content={
                'quit': QUIT,
                'history': HISTORY,
            },
        )
        self.banner = self.__class__.show_banner
        self.doc = self.__class__.show_documentation
        self.prompt = self.colored('SEQUEL> ', style='bold')
        self.printer = printer

        config = get_config()
        def _yield_keys(prefix, dct):
            for key, val in dct.items():
                fq_key = prefix + key
                if isinstance(val, collections.Mapping):
                    yield from _yield_keys(fq_key + ".", val)
                else:
                    yield fq_key
        self._config_keys = list(_yield_keys("", config))
        self._core_sequences = [str(sequence) for sequence in Sequence.get_registry().values()]

    ### config:
    _config_group = group(name="config", default="show", doc="""\
Show/write/reset sequel config""")

    def get_banner_text(self):
        return "Sequel " + self.colored("v{version}".format(version=VERSION), style="bold") + " - integer sequence finder\n"

    def show_banner(self):
        self.output(self.get_banner_text())

    def _title(self, text):
        self.output("")
        self.output(self.colored(text, style="reverse"))
        self.output("")

    def show_documentation(self):
        self.show_banner()
        self.output("""\
Sequel is a tool to search integer sequences.

The main sequel subcommands are:
 * {c_search}: search a sequence matching the given values
 * {c_compile}: compile a sequence expression and show its first values
 * {c_doc}: print documentation about core sequences
 * {c_help}: show help about commands

Sequel can be used as a command shell or as a command line tool; see
{help_usage} for information.
""".format(
    c_search=self.colored("search", "blue"),
    c_compile=self.colored("compile", "blue"),
    c_doc=self.colored("doc", "blue"),
    c_help=self.colored("help", "blue"),
    help_usage=self.colored("help usage", style="underline")))

    @topic(name='usage')
    def _topic_usage(self):
        self.output("""\
The sequel program can be used as a command shell or as a CLI (command line
interface) tool. In the first case the program is run without arguments; an
interactive shell accepting sequel commands is open. In the second case a single
command is passed as argument.""")
        self._title("Interactive shell")
        self.output(self._search_example(
            items=[2, 3, 5, 7],
            sequences=[compile_sequence('p'), compile_sequence('m_exp')],
            shell=True,
        ))
        self._title("Command line interface")
        self.output(self._search_example(
            items=[2, 3, 5, 7],
            sequences=[compile_sequence('p'), compile_sequence('m_exp')],
            shell=False,
        ))

    @argument('-s', '--sort-keys', action='store_true', default=False, help="sort keys")
    @argument('keys', nargs='*', metavar='K', help="key")
    @_config_group.command(name="show")
    def _config_show_command(self, keys, sort_keys):
        function_config_show(keys, sort_keys=sort_keys)

    @argument('-o', '--output-config-filename', metavar='F', default=None, help="output config filename")
    @argument('-r', '--reset', action='store_true', default=False, help="reset config")
    @_config_group.command(name="write")
    def _config_write_command(self, output_config_filename, reset):
        function_config_write(output_config_filename=output_config_filename, reset=reset)

    @_config_group.command(name="reset")
    def _config_reset_command(self):
        function_config_reset()

    @argument('value', metavar='V', help="value")
    @argument('key', metavar='K', help="key")
    @_config_group.command(name="update")
    def _config_update_command(self, key, value):
        config = get_config()
        value = eval(value)
        update_config(config, key, value)
        set_config(config)

    @_config_show_command.completer
    @_config_update_command.completer
    def _config_update_completer(self, text, line, begidx, endidx):
        return filter_completion(text, self._config_keys)

    ### search:
    @argument('items', type=make_item, nargs='+', help="sequence items")
    @command(name='search')
    def _search_command(self, items):
        """Search a sequence matching the given items"""
        function_search(items)

    @_search_command.document
    def _search_help(self):
        self.output("Search a sequence matching the given items; for instance:\n")
        text = self._search_example(
            items=[2, 3, 5, 7],
            sequences=[compile_sequence('p'), compile_sequence('m_exp')])
        self.output(text)

    ### doc:
    @__simplify_argument__
    @argument('--full', action='store_true', default=False, help="show full documentation")
    @argument('sources', type=str, nargs='*', help="sequence expressions")
    @command(name='doc')
    def _doc_command(self, sources, simplify, full):
        function_doc(sources, simplify=simplify, full=full)

    @_doc_command.completer
    def _doc_completer(self, text, line, begidx, endidx):
        return filter_completion(text, self._core_sequences)

    @_doc_command.document
    def _doc_help(self):
        self.output("Show documentation about sequences; for instance:\n")
        text = self._doc_example(sources=['m_exp', 'p'])
        self.output(text)
        self.output("Without arguments all core sequences are shown:\n")
        text = self._doc_example(sources=None, max_lines=7)
        self.output(text)

    ### compile:
    @__simplify_argument__
    @argument('-t', '--tree', action='store_true', default=False, help="show sequence tree")
    @argument('source', type=str, help="sequence source")
    @command(name='compile')
    def _compile_command(self, source, simplify, tree):
        function_compile([source], simplify=simplify, tree=tree)

    @_compile_command.document
    def _compile_help(self):
        self.output("Compile a sequence expression and shows the first items; for instance:\n")
        text = self._compile_example(
            sources=['p * zero_one'])
        self.output(text)

    ### test:
    @__simplify_argument__
    @argument('source', type=str, help="sequence source")
    @command(name='test')
    def _test_command(self, source, simplify):
        function_test([source], simplify=simplify)

    @_test_command.document
    def _test_help(self):
        self.output("Compile a sequence expression and searches its first items; for instance:\n")
        text = self._test_example( source='p * zero_one', sequences=None)
        self.output(text)

    ### utils:
    def _text_lines(self, text, max_lines=None):
        lines = text.split('\n')
        if max_lines is not None:
            if len(lines) > max_lines:
                del lines[max_lines:]
                lines.append("...")
        return lines
    
    def _make_text(self, lines):
        return '\n'.join(self.line_prefix + line for line in lines)

    def _add_end_line(self, lines, shell):
        if shell:
            lines.append(self.prompt)
        else:
            lines.append("$")

    def _add_begin_line(self, lines, cmd, shell):
        if shell:
            lines.append("$ sequel ")
            lines.append(self.get_banner_text())
            lines.append(self.prompt + cmd)
        else:
            lines.append("$ sequel " + cmd)

    def _search_example(self, items, sequences, max_lines=None, shell=False):
        printer = self.printer
        orig_items = tuple(items)
        items = make_items(items)
        sequences = tuple(sequences)
        for sequence in sequences:
            assert_sequence_matches(sequence, items)
        ios = StringIO()
        with printer.set_file(ios):
            printer.print_sequences(sequences, num_known=len(items))
        lines = []
        self._add_begin_line(lines, "search " + " ".join(str(item) for item in orig_items), shell=shell)
        lines.extend(self._text_lines(ios.getvalue(), max_lines=max_lines))
        self._add_end_line(lines, shell=shell)
        return self._make_text(lines)

    def _compile_example(self, sources, simplify=False, max_lines=None, shell=False):
        printer = self.printer
        ios = StringIO()
        with printer.set_file(ios):
            for source in sources:
                sequence = compile_sequence(source, simplify=simplify)
                printer.print_sequence(sequence)
        args = []
        if simplify:
            args.append("--simplify")
        if sources:
            args.extend(sources)
        lines = []
        self._add_begin_line(lines, "compile " + " ".join(shlex.quote(arg) for arg in args), shell=shell)
        lines.extend(self._text_lines(ios.getvalue(), max_lines=max_lines))
        self._add_end_line(lines, shell=shell)
        return self._make_text(lines)

    def _test_example(self, source, sequences, simplify=False, max_lines=None, shell=False):
        printer = self.printer
        ios = StringIO()
        with printer.set_file(ios):
            sequence = compile_sequence(source, simplify=simplify)
            items = sequence.get_values(printer.num_items)
            sequences = sequences
            if sequences is None:
                sequences = [sequence]
            printer.print_test(source, sequence, items, sequences)
        args = []
        if simplify:
            args.append("--simplify")
        args.extend(shlex.quote(source))
        lines = []
        self._add_begin_line(lines, "test " + " ".join(args), shell=shell)
        lines.extend(self._text_lines(ios.getvalue(), max_lines=max_lines))
        self._add_end_line(lines, shell=shell)
        return self._make_text(lines)

    def _doc_example(self, sources, simplify=False, max_lines=None, shell=False):
        printer = self.printer
        ios = StringIO()
        with printer.set_file(ios):
            printer.print_doc(sources=sources, simplify=simplify)
        args = []
        if simplify:
            args.append("--simplify")
        if sources:
            args.extend(sources)
        lines = []
        self._add_begin_line(lines, "doc " + " ".join(args), shell=shell)
        lines.extend(self._text_lines(ios.getvalue(), max_lines=max_lines))
        self._add_end_line(lines, shell=shell)
        return self._make_text(lines)


def iter_selected_sequences(found_sequences, sort=False, limit=None):
    if sort:
        found_sequences = sorted(found_sequences, key=lambda x: x.complexity(), reverse=reverse)
    if limit is None:
        yield from found_sequences
    else:
        for sequence, _ in zip(found_sequences, range(limit)):
            yield sequence

    
def function_shell(display_kwargs=None):
    printer = make_printer(display_kwargs)
    cmd = SequelShell(printer=printer)
    cmd.run()


def function_test(sources, simplify=False, sort=False, reverse=False, limit=None, display_kwargs=None, handler=None, profile=False):
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
        printer.print_test(source, sequence, items, sequences)
    if profile:
        printer.print_stats(profiler)
            

def function_config_show(keys=None, sort_keys=False):
    config = get_config()
    show_config(config, keys=keys, sort_keys=sort_keys)


def function_config_write(output_config_filename=None, reset=False):
    if reset:
        config = default_config()
    else:
        config = get_config()
    write_config(config, output_config_filename)


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


def function_search(items, limit=None, sort=False, reverse=False, display_kwargs=None, handler=None, profile=False):
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
    printer.print_sequences(sequences, num_known=len(items))
    if profile:
        printer.print_stats(profiler)
