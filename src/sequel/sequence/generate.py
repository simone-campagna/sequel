"""
Generate random sequences
"""

import collections
import functools
import json
import random

from .base import compile_sequence, rseq, Const
from .roundrobin import roundrobin
from .miscellanea import (
    Geometric,
    Arithmetic,
)
from .sequence_utils import make_linear_combination


def pick(value):
    if isinstance(value, (list, tuple)):
        return random.choice(value)
    else:
        return value


CONFIG = """\
{
    "macros": {
        "g0_sequences": [
            "cube", "even", "factorial", "fib11", "i", "n",
            "odd", "p", "power_of_2", "power_of_3", "square",
            "triangular", "repunit"
        ],
        "g1_sequences": [
            "fib01", "lucas" 
        ],
        "g2_sequences": [
            "hexagonal", "look_and_say", "pentagonal"
        ],
        "g3_sequences": [
            "catalan", "demlo", "euler", "m_exp", "m_primes"
        ],
        "g4_sequences": [
            "genocchi", "phi", "pi", "sigma", "tau"
        ],
        "g0_functionals": [
            "summation", "product", "integral", "derivative"
        ],
        "g0_sides": [
            4, 7, 8, 9, 10
        ],
        "g0_sequence_groups": [
            ["p", "factorial", "square", "cube"],
            ["odd", "even", "p", "square", "cube"]
        ],
        "coeffs": [
            -10, -9, -8, -7, -6, -5, -4, -3, -2, -1,
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10
        ],
        "zero_coeffs": [
            -10, -9, -8, -7, -6, -5, -4, -3, -2, -1,
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
        ]
    },
    "algorithms": [
        {
            "level": 0,
            "algorithm": "choice",
            "weight": 1.0,
            "kwargs": {
                "sequences": "$g0_sequences"
            }
        },
        {
            "level": 0,
            "algorithm": "arithmetic",
            "weight": 1.0,
            "kwargs": {
                "start_values": [0, 1, 2, 3, 4, 5],
                "step_values": [1, 2, 3, 4, 5, 6, 7]
            }
        },
        {
            "level": 0,
            "algorithm": "recursive_sequence",
            "weight": 1.0,
            "kwargs": {
                "denom": [1],
                "sequences": [["5", "1", "2"], ["I0", "I0 ** 2"]],
                "coeffs": [[1], [1, 2, -1]],
                "known_items": [[-1, 2, 1]]
            }
        },
        {
            "level": 0,
            "algorithm": "recursive_sequence",
            "weight": 0.0,
            "kwargs": {
                "denom": [1],
                "sequences": ["I0", ["I1", "I1 ** 2"]],
                "coeffs": [[1, 0, -1], [1, 2]],
                "known_items": [[0, 1], [1, -1]]
            }
        },
        {
            "level": 1,
            "algorithm": "choice",
            "weight": 1.0,
            "kwargs": {
                "sequences": "$g1_sequences"
            }
        },
        {
            "level": 1,
            "algorithm": "binary",
            "weight": 1.0,
            "kwargs": {
                "operators": ["add", "sub"],
                "sequences": "$g0_sequences"
            }
        },
        {
            "level": 2,
            "algorithm": "choice",
            "weight": 1.0,
            "kwargs": {
                "sequences": "$g2_sequences"
            }
        },
        {
            "level": 1,
            "algorithm": "affine_transform",
            "weight": 0.5,
            "kwargs": {
                "values": "$zero_coeffs",
                "coeffs": "$coeffs",
                "sequences": "$g0_sequences"
            }
        },
        {
            "level": 3,
            "algorithm": "affine_transform",
            "weight": 0.5,
            "kwargs": {
                "values": "$zero_coeffs",
                "coeffs": "$coeffs",
                "sequences": "$g1_sequences"
            }
        },
        {
            "level": 5,
            "algorithm": "affine_transform",
            "weight": 0.5,
            "kwargs": {
                "values": "$zero_coeffs",
                "coeffs": "$coeffs",
                "sequences": "$g2_sequences"
            }
        },
        {
            "level": 2,
            "algorithm": "linear_combination",
            "weight": 0.5,
            "kwargs": {
                "num_items": [2],
                "coeffs": "$coeffs",
                "sequences": "$g0_sequences"
            }
        },
        {
            "level": 5,
            "algorithm": "choice",
            "weight": 1.0,
            "kwargs": {
                "sequences": "$g3_sequences"
            }
        },
        {
            "level": 5,
            "algorithm": "choice",
            "weight": 0.1,
            "kwargs": {
                "sequences": "$g4_sequences"
            }
        },
        {
            "level": 2,
            "algorithm": "functional",
            "weight": 0.5,
            "kwargs": {
                "sequences": "$g0_sequences",
                "functionals": "$g0_functionals"
            }
        },
        {
            "level": 3,
            "algorithm": "functional",
            "weight": 0.5,
            "kwargs": {
                "sequences": "$g1_sequences",
                "functionals": "$g0_functionals"
            }
        },
        {
            "level": 4,
            "algorithm": "functional",
            "weight": 0.5,
            "kwargs": {
                "sequences": "$g2_sequences",
                "functionals": "$g0_functionals"
            }
        },
        {
            "level": 5,
            "algorithm": "functional",
            "weight": 0.5,
            "kwargs": {
                "sequences": "$g3_sequences",
                "functionals": "$g0_functionals"
            }
        },
        {
            "level": 3,
            "algorithm": "polygonal",
            "weight": 0.5,
            "kwargs": {
                "sides": "$g0_sides"
            }
        },
        {
            "level": 3,
            "algorithm": "compose",
            "weight": 0.5,
            "kwargs": {
                "sequence_groups": "$g0_sequence_groups"
            }
        },
        {
            "level": 3,
            "algorithm": "roundrobin",
            "weight": 0.5,
            "kwargs": {
                "sequences": "$g0_sequences",
                "num": 2
            }
        },
        {
            "level": 4,
            "algorithm": "roundrobin",
            "weight": 0.05,
            "kwargs": {
                "sequences": "$g0_sequences",
                "num": 3
            }
        },
        {
            "level": 4,
            "algorithm": "roundrobin",
            "weight": 0.25,
            "kwargs": {
                "sequences": "$g1_sequences",
                "num": 2
            }
        },
        {
            "level": 4,
            "algorithm": "geometric",
            "weight": 0.25,
            "kwargs": {
                "a_values": "$zero_coeffs",
                "b_values": "$coeffs",
                "c_values": [2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        }
    ]
}
"""


@functools.singledispatch
def _expand_macros(obj, macros):
    return obj


@_expand_macros.register(str)
def _(obj, macros):
    if obj.startswith("$"):
        macro = obj[1:]
        if macro in macros:
            return macros[macro]
        else:
            raise KeyError("macro {} not found".format(macro))
    return obj


@_expand_macros.register(collections.abc.Mapping)
def _(obj, macros):
    newobj = obj
    for key, value in obj.items():
        e_value = _expand_macros(value, macros)
        if e_value is not value:
            if newobj is obj:
                newobj = obj.copy()
            newobj[key] = e_value
    return newobj


@_expand_macros.register(collections.abc.Sequence)
def _(obj, macros):
    newobj = obj
    for idx, value in enumerate(obj):
        e_value = _expand_macros(value, macros)
        if e_value is not value:
            if newobj is obj:
                newobj = list(obj)
            newobj[idx] = e_value
    return newobj

    
def generate_choice(sequences):
    return compile_sequence(random.choice(sequences))


def generate_binary(operators, sequences):
    ls, rs = random.sample(sequences, 2)
    op = random.choice(operators)
    ops = {
        "add": lambda x, y: x + y,
        "sub": lambda x, y: x - y,
        "mul": lambda x, y: x * y,
        "div": lambda x, y: x / y,
        "pow": lambda x, y: x ** y,
    }
    return ops[op](compile_sequence(ls), compile_sequence(rs))


def generate_linear_combination(coeffs, sequences, num_items):
    num_items = random.choice(num_items)
    slist = random.sample(sequences, num_items)
    clist = random.sample(coeffs, num_items)
    sequences = [compile_sequence(s) for s in slist]
    return make_linear_combination(clist, sequences)


def generate_affine_transform(values, coeffs, sequences):
    sequence = compile_sequence(random.choice(sequences))
    value = random.choice(values)
    coeff = random.choice(coeffs)
    return (value + coeff * sequence).simplify()


def generate_functional(functionals, sequences):
    sequence = random.choice(sequences)
    return (lc * compile_sequence(ls) + rc * compile_sequence(rs)).simplify()


def generate_functional(functionals, sequences):
    sequence = random.choice(sequences)
    functional = random.choice(functionals)
    return compile_sequence("{}({})".format(functional, sequence))
    
    
def generate_polygonal(sides):
    sides = random.choice(sides)
    return compile_sequence("Polygonal({})".format(sides))
    

def generate_compose(sequence_groups):
    sequence = None
    for sequence_group in sequence_groups:
        seq = compile_sequence(random.choice(sequence_group))
        if sequence is None:
            sequence = seq
        else:
            sequence = sequence | seq
    return sequence
    

def generate_roundrobin(sequences, num):
    sequences = [compile_sequence(seq) for seq in random.sample(sequences, num)]
    return roundrobin(*sequences)
    

def generate_geometric(a_values, b_values, c_values):
    a_value = random.choice(a_values)
    b_value = random.choice(b_values)
    c_value = random.choice(c_values)
    sequence = Geometric(c_value)
    return (a_value + b_value * sequence).simplify()


def generate_arithmetic(start_values, step_values):
    start_value = random.choice(start_values)
    step_value = random.choice(step_values)
    return Arithmetic(start=start_value, step=step_value)


def generate_recursive_sequence(sequences, coeffs, denom, known_items):
    clist = []
    slist = []
    for coeff, sequence in zip(coeffs, sequences):
        clist.append(pick(coeff))
        slist.append(compile_sequence(pick(sequence)))
    denom = pick(denom)
    gseq = make_linear_combination(clist, slist, denom)
    args = [pick(x) for x in known_items] + [gseq]
    return rseq(*args)
        

ALGORITHMS = {
    "choice": generate_choice,
    "binary": generate_binary,
    "linear_combination": generate_linear_combination,
    "affine_transform": generate_affine_transform,
    "functional": generate_functional,
    "polygonal": generate_polygonal,
    "compose": generate_compose,
    "roundrobin": generate_roundrobin,
    "arithmetic": generate_arithmetic,
    "geometric": generate_geometric,
    "recursive_sequence": generate_recursive_sequence,
}


Algorithm = collections.namedtuple('Algorithm', 'name level weight function kwargs')


def compile_config(config):
    macros = config['macros']
    algorithms = _expand_macros(config['algorithms'], macros)

    ldict = collections.defaultdict(list)
    for entry in algorithms:
        ldict[entry['level']].append((
            entry['weight'],
            entry['algorithm'],
            entry['kwargs'],
        ))
    cfg = collections.OrderedDict()
    for level in sorted(ldict):
        ldata = ldict[level]
        ldata.sort(key=lambda e: e[0])
        l_algorithms = []
        for weight, name, kwargs in ldata:
            algorithm = Algorithm(
                name=name,
                level=level,
                function=ALGORITHMS[name],
                weight=weight,
                kwargs=kwargs)
            l_algorithms.append(algorithm)
        cfg[level] = l_algorithms
    return cfg
        

def generate(level=None, algorithm=None):
    config = compile_config(json.loads(CONFIG))

    def make_select(level, algorithm):
        select_functions = []
        if algorithm:
            select_functions.append(lambda algorithm_config: algorithm_config.name == algorithm)
        if level:
            levels = set()
            if isinstance(level, int):
                levels.add(level)
            else:
                min_level, max_level = level
                all_levels = list(config)
                if min_level is None:
                    min_level = min(all_levels)
                if max_level is None:
                    max_level = max(all_levels)
                levels.update(range(min_level, max_level + 1))
            select_functions.append(lambda algorithm_config: algorithm_config.level in levels)
        if select_functions:
            def select(algorithm_config):
                for select_function in select_functions:
                    if not select_function(algorithm_config):
                        return False
                return True
        else:
            def select(algorithm_config):
                return True
        return select

    def run_algorithm(algorithm_config):
        return algorithm_config.function(**algorithm_config.kwargs)

    select = make_select(level, algorithm)
    selected = []
    for level_config in config.values():
        for algorithm_config in level_config:
            if select(algorithm_config):
                selected.append(algorithm_config)
    if len(selected) == 1:
        return run_algorithm(selected[0])
    elif selected:
        lst = []
        tot = sum(algorithm_config.weight for algorithm_config in selected)
        cumulated_p = 0.0
        for algorithm_config in sorted(selected, key=lambda x: x.weight):
            normalized_p = float(algorithm_config.weight) / tot
            cumulated_p += normalized_p
            lst.append((cumulated_p, algorithm_config))
        p = random.random()
        for cumulated_p, algorithm_config in lst:
            if p <= cumulated_p:
                return run_algorithm(algorithm_config)


def generate_sequences(level=None, algorithm=None):
    while True:
        yield generate(level=level, algorithm=algorithm)
