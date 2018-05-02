"""
Search package
"""

import inspect

from ..config import register_config, get_config
from ..modules import make_ref, load_ref

from .manager import Manager

from .base import SearchAlgorithm
from .first_level import (
    SearchCatalog,
    SearchAffineTransform,
    SearchArithmetic,
    SearchGeometric,
    SearchAffineGeometric,
    SearchPower,
    SearchFibonacci,
    SearchPolynomial,
    SearchLinearCombination,
    SearchRepunit,
)
from .common_factors import (
    SearchCommonFactors,
)
from .compose import (
    SearchCompose,
)
from .functional import (
    SearchSummation,
    SearchProduct,
    SearchIntegral,
    SearchDerivative,
)
from .mul_div_pow import (
    SearchMul,
    SearchDiv,
    SearchPow,
)
from .zip_sequences import (
    SearchZip,
)

__all__ = [
    "SearchAlgorithm",
    "Manager",
    "create_manager",
]


def search_config(defaults=True):
    configs = []
    algorithm_types = [
        SearchCatalog,
        SearchAffineTransform,
        SearchArithmetic,
        SearchGeometric,
        SearchAffineGeometric,
        SearchPower,
        SearchFibonacci,
        SearchPolynomial,
        SearchRepunit,
        SearchLinearCombination,
        SearchMul,
        SearchDiv,
        SearchPow,
        SearchCommonFactors,
        SearchCompose,
        SearchSummation,
        SearchProduct,
        SearchIntegral,
        SearchDerivative,
        SearchZip,
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

