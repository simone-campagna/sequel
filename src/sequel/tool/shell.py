"""
Shell class
"""

from code import InteractiveConsole
import readline
import sys

from ..sequence import Sequence, compile_sequence
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
        super().__init__(s_locals)

    @classmethod
    def get_locals(cls):
        locals = {
            'compile_sequence': compile_sequence,
        }
        locals.update(Sequence.get_locals())
        return locals


    def banner(self):
        return """\
SequelShell
"""

    def interact(self, banner=None):
        if banner is None:
            banner = self.banner()
        super().interact(banner=banner)

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
