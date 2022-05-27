"""
"""

import collections
import contextlib
import enum

from .sequence import compile_sequence, Sequence

__all__ = [
    'Declaration',
    'DeclarationType',
    'SequenceDeclaration',
    'parse_declaration',
    'load_catalog_file',
    'iter_declarations',
    'declare',
    'declared',
]


Declaration = collections.namedtuple(
    "Declaration", "decl_type name source")


class DeclarationType(enum.Enum):
    SEQUENCE = 0
    CONST = 1
    CATALOG = 2


def parse_declaration(value):
    if '::' in value:
        name, source = value.split("::")
        name = name.strip()
        source = source.strip()
        return Declaration(DeclarationType.CONST, name, source)
    if ':=' in value:
        name, source = value.split(":=")
        name = name.strip()
    else:
        name, source = None, value
    return Declaration(DeclarationType.SEQUENCE, name, source)


def load_catalog_file(filename):
    declarations = []
    with open(filename, 'r') as f_in:
        for line in f_in:
            line = line.strip()
            if line and not line.startswith('#'):
                declarations.append(parse_declaration(line))
    return declarations


def iter_declarations(declaration):
    if declaration.decl_type is DeclarationType.CATALOG:
        yield from load_catalog_file(declaration.source)
    else:
        yield declaration


@contextlib.contextmanager
def declared(*declarations):
    sequences = []
    variables = {}
    with Sequence.set_variables(variables):
        try:
            for declaration in declarations:
                _declare(declaration, sequences, variables)
            yield tuple(sequences)
        finally:
            for sequence in reversed(sequences):
                sequence.forget()


def declare(declaration):
    seq = []
    _declare(declaration, seq)
    return seq


def _declare(declaration, sequences, variables):
    for declaration in iter_declarations(declaration):
        name = declaration.name
        if declaration.decl_type is DeclarationType.SEQUENCE:
            sequence = compile_sequence(declaration.source)
            if name is None:
                name = str(sequence)
            sequence.register(name)
            sequences.append(sequence)
        elif declaration.decl_type is DeclarationType.CONST:
            value = int(declaration.source)
            variables[name] = value


def catalog_declaration(value):
    return Declaration(DeclarationType.CATALOG, None, value)
