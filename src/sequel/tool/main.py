"""
Main tool.
"""

import shlex
import sys

from .sequel_shell import SequelShell

__all__ = [
    'main',
]


def main():
    cmd = SequelShell()
    if sys.argv[1:]:
        cmd.cli()
    else:
        cmd.run()
