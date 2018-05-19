"""
Print utils
"""

import contextlib
import functools
import sys
import textwrap

import termcolor

import gmpy2

from ..config import get_config, register_config

from ..sequence import Sequence


__all__ = [
    'display_config',
    'Printer',
]


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

    def _oneline_items(self, items, num_known=0):
        known_items = [
            self.blue(self.repr_item(item)) for item in items[:num_known]
        ]
        unknown_items = [
            self.red(self.repr_item(item)) for item in items[num_known:]
        ]
        r_items = known_items + unknown_items
        data = "    {} ...".format(self.separator.join(known_items + unknown_items))
        return data

    def print_items(self, items, num_known=0):
        if self.item_mode == "oneline":
            data = self._oneline_items(items, num_known=num_known)
            if False and self.wraps:
                data = textwrap.fill(data, subsequent_indent='    ', break_long_words=False)
            self(data)
        elif self.item_mode == "multiline":
            for index, item in enumerate(items):
                if index < num_known:
                   fn = self.bold
                else:
                   fn = self.blue
                item = fn(self.repr_item(item))
                self(self.item_format.format(index=index, item=item))
                
    def print_doc(self, sources=None, num_items=None, full=False, simplify=False):
        if sources is None:
            sources = [str(sequence) for sequence in Sequence.get_registry().values()]
        first = True
        for source in sorted(sources):
            if not first:
                self()
            first = False
            sequence = Sequence.compile(source, simplify=simplify)
            if num_items is None:
                num_items = self.num_items
            self(self.bold(str(sequence)) + " : " + sequence.doc())
            if full and sequence.traits:
                self(" " + self.bold("*") + " traits: {}".format("|".join(self.bold(trait.name) for trait in sequence.traits)))
            if num_items:
                items = sequence.get_values(num_items)
                self.print_items(items)

    
    def print_sequence(self, sequence, num_items=None, num_known=0, header=""):
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
            items = sequence.get_values(num_items)
            self.print_items(items, num_known=num_known)
    
    
    def print_sequences(self, sequences, num_items=None, num_known=0, header="", target_sequence=None):
        if target_sequence is not None:
            best_match, best_match_complexity = None, 1000000
            found = False
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
            self.print_sequence(sequence, header=header, num_known=num_known)
        if target_sequence is not None:
            if found:
                self("sequence {}: found".format(target_sequence))
            else:
                if best_match is not None:
                    self("sequence {}: found as {}".format(target_sequence, best_match))
                else:
                    self("sequence {}: *not* found".format(target_sequence))


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

    def print_test(self, source, sequence, items, sequences):
        self(self.bold("###") + " compiling " + self.bold(str(source)) + " ...")
        self.print_sequence(sequence)
        self(self.bold("###") + " searching " + self.bold(" ".join(self.repr_items(items))) + " ...")
        self.print_sequences(sequences, num_items=0, num_known=0, target_sequence=sequence)

    @contextlib.contextmanager
    def overwrite(self, base=None, num_items=None):
        old_base = self.base
        old_num_items = self.num_items
        try:
            if base is not None:
                self.base = base
            if num_items is not None:
                self.num_items = num_items
            yield self
        finally:
            self.num_items = old_num_items
            self.base = old_base
