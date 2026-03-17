import logging

from benchmark_generator.domain.models import Dataset

class DatasetManager:
    """
    Manages a collection of datasets.
    """
    def __init__(self):
        self._datasets: dict[str, Dataset] = {}
        self.logger = logging.getLogger("DatasetManager")

    def register(self, dataset: Dataset):
        self._datasets[dataset.id] = dataset

    def get(self, dataset_id: str) -> Dataset:
        return self._datasets[dataset_id]

    def list(self) -> list[Dataset]:
        return list(self._datasets.values())