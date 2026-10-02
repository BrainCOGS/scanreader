"""Tests for the index helpers in scanreader.utils."""

import numpy as np
import pytest

from scanreader import utils


def test_fill_key_scalar_and_tuple():
    assert utils.fill_key(0, 3) == (0, slice(None), slice(None))
    assert utils.fill_key((1, 2), 3) == (1, 2, slice(None))


def test_fill_key_exact_and_too_many():
    assert utils.fill_key((1, 2, 3), 3) == (1, 2, 3)
    with pytest.raises(IndexError):
        utils.fill_key((1, 2, 3, 4), 3)


def test_check_index_type_accepts_valid():
    for index in (0, -1, np.int64(2), slice(None), [0, 1], (0, -1), np.arange(3)):
        utils.check_index_type(0, index)


def test_check_index_type_rejects_invalid():
    for index in (1.5, "a", [0.5], np.zeros((2, 2), dtype=int), np.arange(3.0)):
        with pytest.raises(TypeError):
            utils.check_index_type(0, index)


def test_bounds_edges():
    utils.check_index_is_in_bounds(0, -3, 3)  # -dim_size is valid
    utils.check_index_is_in_bounds(0, 2, 3)  # dim_size - 1 is valid
    with pytest.raises(IndexError):
        utils.check_index_is_in_bounds(0, 3, 3)
    with pytest.raises(IndexError):
        utils.check_index_is_in_bounds(0, -4, 3)
    with pytest.raises(IndexError):
        utils.check_index_is_in_bounds(0, 0, 0)  # empty dimension


def test_bounds_slice_never_out_of_bounds():
    utils.check_index_is_in_bounds(0, slice(-100, 100), 3)


def test_listify_index():
    assert utils.listify_index(-1, 5) == [4]
    assert utils.listify_index(0, 5) == [0]
    assert utils.listify_index([0, -2], 5) == [0, 3]
    assert utils.listify_index(slice(None), 3) == [0, 1, 2]
    assert utils.listify_index(slice(None, None, -1), 3) == [2, 1, 0]
    assert utils.listify_index(slice(0, 0), 3) == []
    with pytest.raises(TypeError):
        utils.listify_index("a", 3)
