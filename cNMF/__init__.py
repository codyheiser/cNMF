# -*- coding: utf-8 -*-
"""
Consensus Non-negative Matrix Factorization
"""
from .cnmf import (
    cNMF,
    cnmf_load_results,
    prepare,
    factorize,
    combine,
    consensus,
    k_selection,
)

__all__ = [
    "cNMF",
    "cnmf_load_results",
    "prepare",
    "factorize",
    "combine",
    "consensus",
    "k_selection",
]

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
