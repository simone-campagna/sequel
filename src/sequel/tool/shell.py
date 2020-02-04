"""
Shell class
"""

from code import InteractiveConsole
import readline
import sys
from pathlib import Path

from ..config import get_rl_history_filename, get_rl_init_filename
from ..sequence import Sequence, compile_sequence, inspect_sequence, generate, classify
from .display import Printer

__all__ = [
    'SequelShell',
]


class SequelShell(InteractiveConsole):
    def __init__(self, locals=None, printer=None):
        s_locals = self.get_locals()
        if locals:
            s_locals.update(locals)
        if printer is None:
            printer = Printer()
        self.printer = printer
        s_locals['_print'] = print
        s_locals['print'] = printer
        s_locals['printer'] = printer
        s_locals['print_sequence'] = printer.print_sequence
        s_locals['inspect_sequence'] = inspect_sequence
        s_locals['classify'] = classify
        s_locals['generate'] = generate
        super().__init__(s_locals)

    def history_filename(self):
        return get_rl_history_filename()

    @classmethod
    def get_locals(cls):
        locals = {
            'compile_sequence': compile_sequence,
        }
        locals.update(Sequence.get_locals())
        return locals


    def banner(self):
        return """\
Sequel shell
"""

    def exitmsg(self):
        return ""

    def interact(self, banner=None, exitmsg=None):
        if banner is None:
            banner = self.banner()
        if exitmsg is None:
            exitmsg = self.exitmsg()
        init_filename = get_rl_init_filename()
        if init_filename.is_file():
            readline.read_init_file(init_filename)
        history_filename = self.history_filename()
        if history_filename.is_file():
            readline.read_history_file(history_filename)
        try:
            super().interact(banner=banner, exitmsg=exitmsg)
        finally:
            readline.write_history_file(history_filename)

    def run_commands(self, commands, banner=None, echo=False):
        printer = self.printer
        prompt = ">>> "
        if banner is None:
            banner = self.banner()
        if banner:
            printer(banner)
        for command in commands:
            if echo:
                printer(prompt + command)
            self.push(command)
