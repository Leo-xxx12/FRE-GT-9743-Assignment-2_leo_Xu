import os
import yaml
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Any
from .utils import get_config_folder

logger = logging.getLogger(__name__)


class ProblemType(Enum):
    OPTIMAL_EXCU = "OPTIMAL_EXCU"
    # SELECTED_DATA = "SELECTED_DATA"
    FUTURE_PRICE_PREDICT = "FUTURE_PRICE_PREDICT"
    OPTIMAL_EXCU_RE = "OPTIMAL_EXCU_RE"


class Registry:

    _instance = None
    _registry_type = None

    def __new__(
        cls, registry_type: str, file_name: Optional[str] = None, *args, **kwargs
    ):
        if cls._instance is None:
            cls._registry_type = registry_type
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
            # if no preloaded file, we start with a empty registry
            if file_name is not None:
                this_file = os.path.join(get_config_folder(), file_name)
                if os.path.exists(this_file):
                    with open(this_file, "r") as f:
                        strategies = yaml.safe_load(f)
                        for strat_name, strat_content in strategies.items():
                            try:
                                cls._instance.register(strat_name, strat_content)
                            except ValueError:
                                logger.info(
                                    f"Warning: {cls._registry_type} name {strat_name} is not valid. Skipping."
                                )
        return cls._instance

    @abstractmethod
    def register(cls, query_key: str, inserted_object: Any):

        if query_key in cls._instance._registry:
            logger.info(
                f"Warning: {cls._registry_type} name {query_key} exists in the registry already."
            )
            return False
        return True

    def get(self, name: str):
        if name in self._registry:
            return self._registry.get(name, None)
        raise Exception(f"{Registry._registry_type} {name} does not exist")

    def display(self, name: str):
        return self.get(name).content

    def list_registry_keys(self):
        return list(self._registry.keys())
