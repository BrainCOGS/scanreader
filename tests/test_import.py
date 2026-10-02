"""Smoke tests: the package imports and its public entry point exists."""

import scanreader
from scanreader import exceptions, multiroi, scans


def test_public_api():
    assert callable(scanreader.read_scan)


def test_submodules_import():
    assert scans.__name__ == "scanreader.scans"
    assert multiroi.__name__ == "scanreader.multiroi"
    assert issubclass(exceptions.ScanReaderException, Exception)
