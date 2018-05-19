"""
Main tool.
"""

import shlex
import sys

from .subcommands import SequelShell, make_printer

__all__ = [
    'main',
]


def main():
    cmd = SequelShell(printer=make_printer())
    if sys.argv[1:]:
        cmd.cli()
    else:
        cmd.run()
