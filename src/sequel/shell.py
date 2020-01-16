"""
Shell class
"""

from code import InteractiveConsole
import readline

from .sequence import Sequence, compile_sequence

__all__ = [
    'SequelShell',
]


class SequelShell(InteractiveConsole):
    def __init__(self, locals=None):
        s_locals = self.get_locals()
        if locals:
            s_locals.update(locals)
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

    def interact(self):
        super().interact(banner=self.banner())
