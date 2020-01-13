"""
"""

import collections
import contextlib
import enum

from .sequence import compile_sequence

__all__ = [
    'Declaration',
    'DeclarationType',
    'SequenceDeclaration',
    'parse_sequence_declaration',
    'load_catalog_file',
    'make_sequence_declarations',
    'iter_sequence_declarations',
    'declare',
    'declared',
    'sequence_declaration',
    'catalog_declaration',
]


SequenceDeclaration = collections.namedtuple(
    "SequenceDeclaration", "name source")


Declaration = collections.namedtuple(
    "Declaration", "decl_type value")


class DeclarationType(enum.Enum):
    SEQUENCE = 0
    CATALOG = 1


def parse_sequence_declaration(value):
    if ':=' in value:
        name, source = value.split(":=")
        name = name.strip()
    else:
        name, source = None, value
    return SequenceDeclaration(name, source)


def load_catalog_file(filename):
    declarations = []
    with open(filename, 'r') as f_in:
        for line in f_in:
            line = line.strip()
            if line and not line.startswith('#'):
                declarations.append(parse_sequence_declaration(line))
    return declarations


def iter_sequence_declarations(declaration):
    if declaration.decl_type is DeclarationType.SEQUENCE:
        yield parse_sequence_declaration(declaration.value)
    elif declaration.decl_type is DeclarationType.CATALOG:
        yield from load_catalog_file(declaration.value)


@contextlib.contextmanager
def declared(*declarations):
    sequences = []
    try:
        for declaration in declarations:
            _declare(declaration, sequences)
        yield tuple(sequences)
    finally:
        for sequence in reversed(sequences):
            sequence.forget()


def declare(declaration):
    seq = []
    _declare(declaration, seq)
    return seq


def _declare(declaration, sequences):
    for sequence_declaration in iter_sequence_declarations(declaration):
        sequence = compile_sequence(sequence_declaration.source)
        name = sequence_declaration.name
        if name is None:
            name = str(sequence)
        sequence.register_instance(name, sequence)
        sequences.append(sequence)


def sequence_declaration(value):
    return Declaration(DeclarationType.SEQUENCE, value)


def catalog_declaration(value):
    return Declaration(DeclarationType.CATALOG, value)
