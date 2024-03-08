from abc import ABC, abstractmethod
from typing import Dict, Any
import pickle

class CheckpointStrategy(ABC):
    @abstractmethod
    async def save(self, data: Dict[str, Any], identifier: str):
        pass

    @abstractmethod
    async def restore(self, identifier: str) -> Dict[str, Any]:
        pass

class FileCheckpointStrategy(CheckpointStrategy):
    async def save(self, data: Dict[str, Any], identifier: str):
        with open(identifier, 'wb') as f:
            pickle.dump(data, f)

    async def restore(self, identifier: str) -> Dict[str, Any]:
        with open(identifier, 'rb') as f:
            return pickle.load(f)
