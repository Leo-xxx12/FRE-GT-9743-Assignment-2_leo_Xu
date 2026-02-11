import os
import yaml
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Any
from OptionStrategyRegistry.data.strategies import OptionStrategy

logger = logging.getLogger(__name__)
import os

def get_config_folder():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs")


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
class OptionStrategyRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
            cls._instance._load_defaults()
        return cls._instance

    def _load_defaults(self):
        # configs/strategies.yaml (relative to OptionStrategyRegistry folder)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        yaml_path = os.path.join(base_dir, "configs", "strategies.yaml")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        # data is a dict: { name: {OPT_TYPE:..., DELTA_STRIKE:..., WEIGHT:...}, ... }
        for name, d in data.items():
            self._registry[name] = OptionStrategy(
                d["OPT_TYPE"],
                d["DELTA_STRIKE"],
                d["WEIGHT"],
            )

    def register(self, name, strategy_input):
        # strategy_input can be dict or list/tuple
        if isinstance(strategy_input, dict):
            strat = OptionStrategy(
                strategy_input["OPT_TYPE"],
                strategy_input["DELTA_STRIKE"],
                strategy_input["WEIGHT"],
            )
        elif isinstance(strategy_input, (list, tuple)):
            # expect [OPT_TYPE_list, DELTA_STRIKE_list, WEIGHT_list]
            strat = OptionStrategy(strategy_input[0], strategy_input[1], strategy_input[2])
        else:
            raise TypeError("strategy_input must be a dict or a list/tuple")

        self._registry[name] = strat

    def list_registry_keys(self):
        return list(self._registry.keys())

    def get(self, name):
        return self._registry.get(name, None)