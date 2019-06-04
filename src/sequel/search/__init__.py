"""
Search package
"""

import inspect

from ..config import register_config, get_config
from ..modules import make_ref, load_ref

from .manager import (
    Manager,
    Collector,
    Handler,
    StopAtFirst,
    StopAtLast,
    StopAtNum,
    StopBelowComplexity,
)
from .base import Algorithm
from .first_level import (
    CatalogAlgorithm,
    ConstAlgorithm,
    AffineTransformAlgorithm,
    ArithmeticAlgorithm,
    GeometricAlgorithm,
    PowerAlgorithm,
    FibonacciAlgorithm,
    PolynomialAlgorithm,
    LinearCombinationAlgorithm,
    RepunitAlgorithm,
)
from .common_factors import (
    CommonFactorsAlgorithm,
)
from .compose import (
    ComposeAlgorithm,
)
from .functional import (
    SummationAlgorithm,
    ProductAlgorithm,
    IntegralAlgorithm,
    DerivativeAlgorithm,
)
from .binary import (
    AddAlgorithm,
    SubAlgorithm,
    MulAlgorithm,
    DivAlgorithm,
    PowAlgorithm,
)
from .roundrobin import (
    RoundrobinAlgorithm,
)

__all__ = [
    "Algorithm",
    "RecursiveAlgorithm",
    "Manager",
    "create_manager",
]


def search_config(defaults=True):
    configs = []
    algorithm_types = [
        CatalogAlgorithm,
        ConstAlgorithm,
        AffineTransformAlgorithm,
        ArithmeticAlgorithm,
        GeometricAlgorithm,
        PowerAlgorithm,
        FibonacciAlgorithm,
        PolynomialAlgorithm,
        RepunitAlgorithm,
        LinearCombinationAlgorithm,
        AddAlgorithm,
        SubAlgorithm,
        MulAlgorithm,
        DivAlgorithm,
        PowAlgorithm,
        CommonFactorsAlgorithm,
        ComposeAlgorithm,
        SummationAlgorithm,
        ProductAlgorithm,
        IntegralAlgorithm,
        DerivativeAlgorithm,
        RoundrobinAlgorithm,
    ]
    for algorithm_type in algorithm_types:
        algorithm_config = {
            'type': make_ref(algorithm_type),
        }
        kwargs = {}
        if defaults:
            sig = inspect.signature(algorithm_type)
            for arg, parameter in sig.parameters.items():
                if parameter.default is not parameter.empty:
                    kwargs[arg] = parameter.default
            algorithm_config["kwargs"] = kwargs
        configs.append(algorithm_config)
    return {
        'algorithms': configs,
    }


register_config(
    name="search",
    default=search_config(),
)


def create_manager(size, config=None):
    if config is None:
        config = get_config()
    manager = Manager(size)
    search_algorithms = config["search"]["algorithms"]
    for algorithm_config in search_algorithms:
        algorithm_type = load_ref(algorithm_config['type'])
        kwargs = algorithm_config.get('kwargs', {})
        algorithm = algorithm_type(**kwargs)
        manager.add_algorithm(algorithm)
    return manager

