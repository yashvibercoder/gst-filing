"""
Base Reader Module
Abstract base class defining the interface for all platform readers.
"""

from abc import ABC, abstractmethod


class BaseReader(ABC):
    """All platform readers inherit from this and implement the read methods."""

    def __init__(self, file_paths, config):
        self.file_paths = file_paths if isinstance(file_paths, list) else [file_paths]
        self.config = config

    @abstractmethod
    def read_all(self):
        """
        Read all data from the platform's file(s).

        Returns dict of DataFrames:
            {"b2c": df, "b2b": df, "hsn": df, "documents": df,
             "eco": df, "credit_notes": df}

        Keys with no data should map to None.
        """
        pass
