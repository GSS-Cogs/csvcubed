"""
Iterables
---------

Function to help when working with lists/iterables.
"""
from collections.abc import Iterable
from typing import Callable, TypeVar, Optional

T = TypeVar("T")


def first(
    xs: Iterable[T], predicate: Callable[[T], bool] = lambda a: True
) -> Optional[T]:
    """
    :return: the first item in the :obj:`~collections.abc.Iterable` :obj:`xs` which matches
        the :func:`predicate` function.
    """
    return next(filter(predicate, xs), None)
