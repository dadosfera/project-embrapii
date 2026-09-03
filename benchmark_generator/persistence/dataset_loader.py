import logging
from pathlib import Path
from typing import Protocol

from benchmark_generator.domain.models import Dataset


class DatasetLoader(Protocol):
    """
    Protocol for a repository that handles retrieval of datasets.
    """

    def load(self) -> Dataset:
        """
        Load the dataset from the repository.

        :returns: A list of BenchmarkQuestion instances.
        """
        ...

class SQLFileDatasetLoader(DatasetLoader):
    """
    A SQL file-based implementation of the DatasetRepository protocol.
    """

    def __init__(self, path: str | Path, *, dataset_id: str):
        """
        Initialize repository with the target SQL file path.
        """
        self._path = Path(path)
        self._dataset_id = dataset_id
        self.logger = logging.getLogger("SQLFileDatasetLoader")

    def load(self) -> Dataset:
        schema = Path(self._path).read_text(encoding="utf-8")
        return Dataset(
            id=self._dataset_id,
            schema=schema
        )


class SQLAndDocumentationFileDatasetLoader(DatasetLoader):
    """
    An implementation of DatasetLoader that loads both SQL schema and documentation from separate files.
    """

    def __init__(
            self, sql_path: str | Path,
            doc_path: str | Path,
            *,
            dataset_id: str
    ):
        """
        Initialize repository with the target SQL file path.
        """
        self._sql_path = Path(sql_path)
        self._doc_path = Path(doc_path)
        self._dataset_id = dataset_id
        self.logger = logging.getLogger("SQLAndDocumentationFileDatasetLoader")

    def load(self) -> Dataset:
        schema = self._sql_path.read_text(encoding="utf-8")
        documentation = self._doc_path.read_text(encoding="utf-8")
        return Dataset(
            id=self._dataset_id,
            schema=schema,
            documentation=documentation,
        )