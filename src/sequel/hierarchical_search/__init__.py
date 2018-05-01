"""
Hierarchical search algorithms
"""

import collections
import inspect

import abc
import collections

from ..catalog import create_catalog
from ..config import register_config, get_config
from ..items import Items
from ..sequence import Sequence

from .aggregate import SearchAggregate
from .base import SearchAlgorithm, Serialization, SearchInfo

from .functional import (
    SearchSum,
    SearchProd,
    SearchDerivative,
    SearchIntegral,
)
from .zip_sequences import (
    SearchZip,
)
from .common_factors import (
    SearchCommonFactors,
)
from .compose import (
    SearchCompose,
)
from .mul_div_pow import (
    SearchMul,
    SearchDiv,
    SearchPow,
)
from .non_recursive import (
    SearchCatalog,
    SearchAffineTransform,
    SearchArithmetic,
    SearchGeometric,
    SearchAffineGeometric,
    SearchPower,
    SearchFibonacci,
    SearchPolynomial,
    SearchLinearCombination,
)


__all__ = [
    "SearchInfo",
    "Searialization",
    "SearchAlgorithm",
    "SearchAggregate",
    "SearchCatalog",
    "SearchArithmetic",
    "SearchAffineTransform",
    "SearchGeometric",
    "SearchAffineGeometric",
    "SearchPower",
    "SearchFibonacci",
    "SearchPolynomial",
    "SearchLinearCombination",
    "SearchSum",
    "SearchDerivative",
    "SearchIntegral",
    "SearchMul",
    "SearchDiv",
    "SearchPow",
    "SearchCompose",
    "SearchCommonFactors",
    "SearchZip",
    "create_algorithm",
    "search_config",
    "search",
]


def search_config():
    l0 = SearchAggregate(name="l0", algorithms=[
        SearchCatalog(name="l0_catalog"),
        SearchArithmetic(name="l0_arithmetic"),
        SearchAffineTransform(name="l0_affine_transform"),
        SearchGeometric(name="l0_geometric"),
        SearchAffineGeometric(name="l0_affine_geometric"),
        SearchPower(name="l0_power"),
        SearchFibonacci(name="l0_fibonacci"),
        SearchPolynomial(name="l0_polynomial"),
    ])
    l1 = SearchAggregate(name="l1", algorithms=[
        l0,
        SearchLinearCombination(name="l1_lin_comb_fast", max_elapsed=2)
    ])
    l2 = SearchAggregate(name="l2", algorithms=[l1])
    l2.add_algorithms(
        SearchMul(name="l2_mul", sub_algorithm=l1),
        SearchDiv(name="l2_div", sub_algorithm=l1),
        SearchPow(name="l2_pow", sub_algorithm=l1),
        SearchCommonFactors(name="l2_common_factors", sub_algorithm=l1),
        SearchSum(name="l2_sum", sub_algorithm=l1),
        SearchProd(name="l2_prod", sub_algorithm=l1),
        SearchDerivative(name="l2_derivative", sub_algorithm=l1),
        SearchIntegral(name="l2_integral", sub_algorithm=l1),
        SearchCompose(name="l2_compose", sub_algorithm=l1),
        SearchZip(name="l2_zip", sub_algorithm=l1),
    )
    l3 = SearchAggregate(name="l3", algorithms=[l2])
    l3.add_algorithms(
        SearchMul(name="l3_mul", sub_algorithm=l2),
        SearchDiv(name="l3_div", sub_algorithm=l2),
        SearchPow(name="l3_pow", sub_algorithm=l2),
        SearchCommonFactors(name="l3_common_factors", sub_algorithm=l2),
        SearchDerivative(name="l3_derivative", sub_algorithm=l2),
        SearchIntegral(name="l3_integral", sub_algorithm=l2),
        SearchCompose(name="l3_compose", sub_algorithm=l2),
        SearchZip(name="l3_zip", sub_algorithm=l2),
    )
    # l3 = SearchAggregate(name="l3", algorithms=[
    #     l1,
    #     l2,
    # ])
    serialization = Serialization()
    algorithm = l3
    serialization.store(algorithm)
    return {
        "algorithms": serialization.data(),
        "algorithm_name": algorithm.name,
    }

register_config(
    name="hierarchical_search",
    default=search_config(),
)


def create_algorithm(size, config=None):
    if config is None:
        config = get_config()
    search_config = config["hierarchical_search"]
    algorithms_config = search_config["algorithms"]
    serialization = Serialization(algorithms_config)
    return serialization.load(search_config["algorithm_name"])


def search(items, max_len=10, max_depth=10):
    items = Items(items)
    info = SearchInfo(
        max_depth=max_depth,
        max_len=max_len)
    catalog = create_catalog(size=len(items))
    algorithm = create_algorithm()
    yield from algorithm(catalog, items, info)

