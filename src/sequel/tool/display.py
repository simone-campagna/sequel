"""
Print utils
"""

import collections
import contextlib
import enum
import functools
import io
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
from ..sequence import (
    Sequence, SequenceUnboundError,
    compile_sequence,
    inspect_sequence,
    classify as classify_sequence,
    Trait,
)



__all__ = [
    'display_config',
    'Printer',
]


UNDEF = object()
QUIT = object()
HINT = object()

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


def evaluate(expr):
    try:
        return eval(expr)
    except:
        return compile_sequence(expr)


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

    @contextlib.contextmanager
    def set_ios(self):
        ios = io.StringIO()
        with self.set_file(ios):
            yield ios

    def _colored(self, string, color):
        if self.colored:
            return termcolor.colored(string, color)
        else:
            return string

    def blue(self, string):
        return self._colored(string, "blue")

    def red(self, string):
        return self._colored(string, "red")

    def green(self, string):
        return self._colored(string, "green")

    def guess(self, string):
        return string

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

    def print_items(self, items, item_types=KNOWN, item_mode=None, header=""):
        if item_mode is None:
            item_mode = self.item_mode
        if item_mode == "oneline":
            data = self._oneline_items(items, item_types=item_types)
            if False and self.wraps:
                data = textwrap.fill(data, initial_indent=header, subsequent_indent=header + '    ', break_long_words=False)
            self(data)
        elif item_mode == "multiline":
            for index, (item, item_type) in enumerate(zip(items, item_types())):
                self(header + self.item_format.format(index=index, item=self.colorize_item(item, item_type)))
                
    def print_doc(self, sources=None, num_items=None, traits=False, classify=False, simplify=False):
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
            self(self.bold(str(sequence)) + " : " + sequence.doc())
            if traits or classify:
                self.print_sequence_traits(sequence, classify=classify)
            self.print_sequence_items(sequence, num_items)

    def print_sequence(self, sequence, num_items=None, tree=False, traits=False, classify=False, inspect=False, doc=False, item_types=KNOWN, header=""):
        """Print a sequence.
    
           Parameters
           ----------
           sequence: Sequence
               the sequence
           doc: bool, optional
               print sequence doc (defaults to False)
           num_items: int, optional
               number of items to be shown (defaults to ``10``)
           tree: bool, optional
               print sequence tree (defaults to False)
           traits: bool, optional
               print sequence traits (defaults to False)
           classify: bool, optional
               classify sequence traits (defaults to False)
           inspect: bool, optional
               inspect sequence (defaults to False)
        """
        s_sequence = str(sequence)
        s_sequence = self.bold(str(sequence))
        if doc:
            s_doc = " : " + sequence.doc()
        else:
            s_doc = ""
        self("{}{}{}".format(header, s_sequence, s_doc))
        self.print_sequence_items(sequence, num_items, item_types=item_types, header=header + "    ")
        if traits or classify:
            self.print_sequence_traits(sequence, classify=classify, header=header + "    ")
        if inspect:
            self.print_sequence_info(sequence, header + "    ")
        if tree:
            self(header + "    tree:")
            self.print_tree(sequence, header=header + "        ")
    
    def print_sequence_traits(self, sequence, classify=False, header=""):
        sequence_traits = set(sequence.traits)
        if classify:
            classified_traits_d = classify_sequence(sequence)
            colored_traits = []
            self(header + "   {:30s} DECLARED CLASSIFIED".format("TRAIT"))
            on_txt = self.bold('X')
            off_txt = ' '
            for trait in sorted(Trait, key=lambda x: x.value):
                show = False
                c_value = classified_traits_d[trait]
                if trait in sequence_traits:
                    d_txt = 'X'
                    show = True
                    if c_value is None:
                        c_txt = '?'
                        color = self.color
                    elif c_value:
                        c_txt = 'X'
                        color = self.green
                    else:
                        c_txt = '-'
                        color = self.red
                else:
                    d_txt = '-'
                    if c_value is None:
                        c_txt = '?'
                        color = self.color
                    elif c_value:
                        c_txt = 'X'
                        color = self.blue
                        show = True
                    else:
                        c_txt = '-'
                        color = self.green
                if show:
                    trait_txt = color("{:30s}".format(trait))
                    self(header + "   + " + trait_txt + "      " + d_txt + "          " + c_txt)
        else:
            colored_traits = []
            for trait in sorted(sequence_traits, key=lambda x: x.value):
                colored_traits.append(trait.name)
            self(header + "traits: {}".format("|".join(colored_traits)))

    def print_sequence_info(self, sequence, header=""):
        info = inspect_sequence(sequence)
        self(header + "contains: " + " ".join(self.bold(str(seq)) for seq in info.contains))
        self(header + "flags: " + " " .join(self.blue(flag.name) for flag in info.flags))

    def print_sequence_items(self, sequence, num_items, item_types=KNOWN, header=""):
        if num_items is None:
            num_items = self.num_items
        if num_items:
            try:
                items = sequence.get_values(num_items)
                self.print_items(items, item_types=item_types, header=header)
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


    def print_tree(self, sequence, header=""):
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
            hdr = "{}{} ".format(header, self.blue(complexity)) + ("  " * depth)
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
