class ScanReaderException(Exception):
    """Base ScanReader exception."""


class ScanImageVersionError(ScanReaderException):
    """Exception for unsupported ScanImage versions."""


class PathnameError(ScanReaderException):
    """Exception for dealing with paths and pathname patterns (wildcards)."""


class FieldDimensionMismatch(ScanReaderException):
    """Exception for trying to slice an array with fields of different dimensions."""
