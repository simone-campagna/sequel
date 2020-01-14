"""
Print utils
"""

import collections
import contextlib
import enum
import functools
import itertools
import os
import readline
import shutil
import sys
import textwrap

import termcolor

from ..config import get_config, register_config
from ..item import Item
from ..lazy import gmpy2
from ..sequence import Sequence, SequenceUnboundError, compile_sequence



__all__ = [
    'display_config',
    'Printer',
]


UNDEF = object()

register_config(
    name="display",
    default={
        "colored": True,
        "base": 10,
        "max_full_digits": 16,
        "max_compact_digits": 1000000,
        "big_int": "<BIG>",
        "ellipsis": "..",
        "item_mode": "oneline",
        "separator": " ",
        "wraps": True,
        "item_format": "    {index:4d}: {item}",
        "num_items": 10,
    })


class ItemType(enum.Enum):
    KNOWN = 0
    PATTERN = 1
    GUESS = 2


KNOWN = lambda : itertools.repeat(ItemType.KNOWN)
GUESS = lambda : itertools.repeat(ItemType.GUESS)
PATTERN = lambda : itertools.repeat(ItemType.PATTERN)


def iter_item_types(items):
    def item_types():
        for item in items:
            if isinstance(item, Item):
                if item.is_known():
                    yield ItemType.KNOWN
                else:
                    yield ItemType.PATTERN
            else:
                yield ItemType.KNOWN
        yield from GUESS()
    return item_types

    
class Printer(object):
    def __init__(self, base=None, max_full_digits=None, max_compact_digits=None,
                 big_int=None, ellipsis=None, item_mode=None, num_items=None,
                 separator=None, wraps=None, item_format=None, colored=None,
                 file=sys.stdout):
        kwargs = {
            'colored': colored,
            'base': base,
            'max_full_digits': max_full_digits,
            'max_compact_digits': max_compact_digits,
            'big_int': big_int,
            'ellipsis': ellipsis,
            'item_mode': item_mode,
            'separator': separator,
            'wraps': wraps,
            'item_format': item_format,
            'num_items': num_items,
        }
        config = get_config()["display"]
        for key, value in kwargs.items():
            if value is None:
                value = config[key]
            setattr(self, key, value)
        self.file = file

    def __call__(self, *args, **kwargs):
        if not 'file' in kwargs:
            kwargs['file'] = self.file
        print(*args, **kwargs)

    @contextlib.contextmanager
    def set_file(self, file):
        old_file = self.file
        self.file = file
        try:
            yield self
        finally:
            self.file = old_file

    def _colored(self, string, color):
        if self.colored:
            return termcolor.colored(string, color)
        else:
            return string

    def blue(self, string):
        return self._colored(string, "blue")

    def red(self, string):
        return self._colored(string, "red")

    def guess(self, string):
        return string
        #return termcolor.colored(string, attrs=["underline"])

    def bold(self, string):
        if self.colored:
            return termcolor.colored(string, attrs=["bold"])
        else:
            return string

    def color(self, string, *attrs):
        if self.colored:
            arglist = []
            attrlist = []
            for attr in  attrs:
                if attr in termcolor.ATTRIBUTES:
                    attrlist.append(attr)
                else:
                    arglist.append(attr)
            return termcolor.colored(string, *arglist, attrs=attrlist)
        else:
            return string
      
    def repr_items(self, items):
        return [self.repr_item(i) for i in items]

    def colorize_item(self, item, item_type):
        if item_type is ItemType.KNOWN:
            fn_color = self.blue
        elif item_type is ItemType.GUESS:
            fn_color = self.red
        else:
            fn_color = self.guess
        return fn_color(self.repr_item(item))

    def repr_item(self, item):
        item = gmpy2.mpz(item)
        num_digits = item.num_digits(self.base)
        if num_digits >= self.max_compact_digits:
            return self.big_int
        else:
            digits = item.digits(self.base)
            exc_digits = len(digits) - self.max_full_digits
            if exc_digits > 0:
                sep = self.ellipsis
                exc_digits = max(len(sep), exc_digits)
                nleft = (len(digits) - exc_digits) // 2
                nright = len(digits) - (exc_digits + nleft)
                return digits[:nleft] + sep + digits[-nright:]
            else:
                return digits

    def _oneline_items(self, items, item_types=KNOWN):
        r_items = []
        for item, item_type in zip(items, item_types()):
            r_items.append(self.colorize_item(item, item_type))
        data = "    {} ...".format(self.separator.join(r_items))
        return data

    def print_items(self, items, item_types=KNOWN, item_mode=None):
        if item_mode is None:
            item_mode = self.item_mode
        if item_mode == "oneline":
            data = self._oneline_items(items, item_types=item_types)
            if False and self.wraps:
                data = textwrap.fill(data, subsequent_indent='    ', break_long_words=False)
            self(data)
        elif item_mode == "multiline":
            for index, (item, item_type) in enumerate(zip(items, item_types())):
                # if index < num_known:
                #    fn = self.bold
                # else:
                #    fn = self.blue
                # item = fn(self.repr_item(item))
                # self(self.item_format.format(index=index, item=item))
                self(self.item_format.format(index=index, item=self.colorize_item(item, item_type)))
                
    def print_doc(self, sources=None, num_items=None, full=False, simplify=False):
        if sources is None:
            sources = sorted([str(sequence) for sequence in Sequence.get_registry().values() if sequence.is_bound()])
        first = True
        for source in sources:
            if not first:
                self()
            first = False
            if isinstance(source, Sequence):
                sequence = source
            else:
                sequence = Sequence.compile(source, simplify=simplify)
            if num_items is None:
                num_items = self.num_items
            self(self.bold(str(sequence)) + " : " + sequence.doc())
            if full:
                self(" " + self.bold("*") + " traits: {}".format("|".join(self.bold(trait.name) for trait in sequence.traits)))
            if num_items:
                try:
                    items = sequence.get_values(num_items)
                    self.print_items(items)
                except SequenceUnboundError:
                    pass

    def print_sequence(self, sequence, num_items=None, item_types=KNOWN, header=""):
        """Print a sequence.
    
           Parameters
           ----------
           sequence: Sequence
               the sequence
           num_items: int, optional
               number of items to be shown (defaults to ``10``)
        """
        if num_items is None:
            num_items = self.num_items
        s_sequence = str(sequence)
        s_sequence = self.bold(str(sequence))
        self("{}{}".format(header, s_sequence))
        if num_items:
            try:
                items = sequence.get_values(num_items)
                self.print_items(items, item_types=item_types)
            except SequenceUnboundError:
                pass
    
    
    def print_sequences(self, sequences, num_items=None, item_types=KNOWN, header="", target_sequence=None):
        best_match, best_match_complexity = None, 1000000
        if target_sequence is not None:
            found = False
        try:
            for count, sequence in enumerate(sequences):
                header = "{:>5d}] ".format(count)
                if target_sequence is not None:
                    if sequence.equals(target_sequence):
                        found = True
                        header += "[*] "
                    else:
                        header += "    "
                complexity = sequence.complexity()
                if best_match_complexity > complexity:
                    best_match, best_match_complexity = sequence, complexity
                self.print_sequence(sequence, header=header, item_types=item_types)
        except KeyboardInterrupt:
            self(self.red("[search interrupted]"))
        if target_sequence is not None:
            if found:
                self("sequence {}: found".format(target_sequence))
            else:
                if best_match is not None:
                    self("sequence {}: found as {}".format(target_sequence, best_match))
                else:
                    self("sequence {}: *not* found".format(target_sequence))
        else:
            self("best match: {}".format(self.bold(str(best_match))))


    def print_tree(self, sequence):
        max_complexity = sequence.complexity()
        max_len = 1
        while True:
            if 10 ** max_len > max_complexity:
                break
            max_len += 1
        if max_complexity < 10:
            max_len = 1
        elif max_complexity < 100:
            max_len = 2
        for depth, child in sequence.walk():
            rchild = repr(child)
            schild = str(child)
            complexity = str(child.complexity())
            if len(complexity) < max_len:
                complexity = (" " * (max_len - len(complexity))) + complexity
            lst = [self.bold(schild)]
            if schild != rchild:
                lst.append(":")
                lst.append(rchild)
            hdr = "{} ".format(self.blue(complexity)) + ("  " * depth)
            self(hdr + " ".join(lst))
    
    
    def print_stats(self, stats):
        self("## Stats:")
        table = [('ALGORITHM', 'COUNT', 'TOTAL_TIME', 'AVERAGE_TIME')]
        lstats = list(stats.items())
        lstats.sort(key=lambda x: x[1].total_time)
        for key, stats in lstats:
            s_key = str(key)
            if stats.count == 0:
                ave = ""
            else:
                ave = "{:8.2f}".format(stats.average_time)
            tot = "{:8.2f}".format(stats.total_time)
            count = "{:8d}".format(stats.count)
            table.append((s_key, count, tot, ave))
        lengths = [max(len(row[i]) for row in table) for i in range(len(table[0]))]
        aligns = ['<', '>', '>', '>']
        fmt = " ".join("{{:{a}{l}s}}".format(a=a, l=l) for a, l in zip(aligns, lengths))
        for row in table:
            self(fmt.format(*row))

    def print_rsearch(self, source, sequence, items, sequences):
        self(self.bold("###") + " compiling " + self.bold(str(source)) + " ...")
        self.print_sequence(sequence)
        self(self.bold("###") + " searching " + self.bold(" ".join(self.repr_items(items))) + " ...")
        self.print_sequences(sequences, num_items=0, target_sequence=sequence)

    @contextlib.contextmanager
    def overwrite(self, **kwargs):
        old_values = {key: getattr(self, key) for key in kwargs}
        try:
            for key, value in kwargs.items():
                setattr(self, key, value)
            yield self
        finally:
            for key, value in old_values.items():
                setattr(self, key, value)

    def print_quiz(self, source, tries=None):
        item_format = "    {index:4d}: {item:20s}"
        def show_items(items):
            with self.overwrite(max_full_digits=10 ** 100, max_compact_digits=10 ** 100):
                for index, item in enumerate(items):
                    item = self.bold(self.repr_item(item))
                    self(item_format.format(index=index, item=item))

        items_format = "    {index:4d}: {item:20s} {user_item:20s} {equals}"
        def compare_items(items, user_items):
            with self.overwrite(max_full_digits=10 ** 100, max_compact_digits=10 ** 100):
                nexact = 0
                ndiff = 0
                for index, (item, user_item) in enumerate(zip(items, user_items)):
                    s_item = self.bold(self.repr_item(item))
                    s_user_item = self.repr_item(user_item)
                    if user_item == item:
                        s_user_item = self.blue(s_user_item)
                        equals = "[ok]"
                        nexact += 1
                    else:
                        s_user_item = self.red(s_user_item)
                        equals = "!!!"
                        ndiff += 1
                    self(items_format.format(index=index, item=s_item, user_item=s_user_item, equals=equals))
                return nexact, ndiff

        if isinstance(source, str):
            sequence = Sequence.compile(source, simplify=True)
        else:
            sequence = source
       
        commands = collections.OrderedDict()
        
        def _show_help(command, args, items, sequence):
            for key, (doc, function) in commands.items():
                self("{:20s} {}".format(self.bold(key), doc))

        def _get_tag(command, args, items, sequence):
            return command

        def _print_doc(command, args, items, sequence):
            self.print_doc()

        def _spoiler(command, args, items, sequence):
            self("The hidden sequence is: " + self.bold(sequence))

        def _show_items(command, args, items, sequence):
            show_items(items)

        def _calc(command, args, items, sequence):
            expr = args
            self(self.bold(">>>"), self.blue(expr))
            try:
                res = eval(expr)
            except:
                res = compile_sequence(expr)
            if isinstance(res, Sequence):
                self.print_sequence(res)
            else:
                self(self.bold(res))

        def _get_answer(msg):
            return input(msg).strip()

        if tries is not None:
            def _make_get_stacked_answer(tries):
                stack = list(tries)
                def _get_stacked_answer(msg):
                    if stack:
                        ans = stack.pop(0)
                        self(msg + ans)
                        return ans
                    else:
                        return _get_answer(msg)
                return _get_stacked_answer
            get_answer = _make_get_stacked_answer(tries)
        else:
            get_answer = _get_answer

        commands['quit'] = ("quit", _get_tag)
        commands['items'] = ("items", _show_items)
        commands['spoiler'] = ("show the hidden sequences", _spoiler)
        commands['doc'] = ("show available sequences", _print_doc)
        commands['calc'] = ("calculate expression", _calc)
        commands['help'] = ("show available commands", _show_help)

        # self(str(sequence))
        num_items = self.num_items
        item_mode = 'multiline'
        items = []
        ntries = 0
        self("(enter ':help' to show commands)")
        while True:
            if len(items) != num_items:
                items = sequence.get_values(num_items)
            show_items(items)
            while True:
                hdr = "[{}] ".format(ntries)
                try:
                    ans = get_answer(hdr + "sequence > ").strip()
                except EOFError:
                    self('')
                    return
                if not ans:
                    continue
                if ans.startswith(":"):
                    lst = ans[1:].split(None, 1)
                    if len(lst) < 2:
                        lst.append("")
                    command, args = lst
                    fn = commands[command][1]
                    result = fn(command, args, items, sequence)
                    if result == 'quit':
                        return
                else:
                    ntries += 1
                    hdr = "[{}] ".format(ntries)
                    try:
                        user_sequence = Sequence.compile(ans, simplify=True)
                    except Exception as err:
                        self(hdr + self.red("ERROR:") + str(err))
                        continue
                    user_items = user_sequence.get_values(num_items)
                    nexact, ndiff = compare_items(items, user_items)
                    if ndiff:
                        self(hdr + "{} errors - try again".format(ndiff))
                    else:
                        if user_sequence.equals(sequence):
                            self(hdr + "Wow! You found the exact solution {}".format(self.bold(str(user_sequence))))
                        else:
                            self(hdr + "Good! You found the solution {}; the exact solution was {}".format(self.bold(str(user_sequence)), self.bold(str(sequence))))
                        return
    def pager(self, *args, **kwargs):
        return Pager(self, *args, **kwargs)
      

class Pager(object):
    def __init__(self, printer, max_lines=None, interactive=True, continue_text=None):
        self.printer = printer
        if max_lines is None:
            max_lines = shutil.get_terminal_size((80, 20)).lines
        self.max_lines = max_lines
        self.num_lines = 0
        self.interactive = interactive
        if continue_text is None:
            continue_text = printer.bold("⟪ press ") + printer.blue("ENTER") + printer.bold(" to continue ⟫") + ' '
        self.continue_text = continue_text

    def interrupt(self):
        input(self.continue_text)
        self.printer('\r' + ' ' * len(self.continue_text) + '\r')

    def __call__(self, text):
        num_new_lines = text.count('\n') + 1
        if self.interactive:
            if self.num_lines > 0 and self.num_lines + num_new_lines >= self.max_lines:
                self.interrupt()
                self.num_lines = 0
        printer = self.printer
        printer(text)
        self.num_lines += num_new_lines
