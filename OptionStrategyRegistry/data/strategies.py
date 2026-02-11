import os
import yaml
import logging
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Optional, Tuple
from abc import ABC, abstractmethod
from .definitions import OptionPayoff


logger = logging.getLogger(__name__)
def get_config_folder():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs")

class Registry:
    def __init__(self):
        if not hasattr(self, "_registry"):
            self._registry = {}

### Option Strategy Class that Supports Arithemtics (see demo)
class OptionStrategy:

    schema = ["OPT_TYPE", "DELTA_STRIKE", "WEIGHT"]

    def __init__(self, name: str, content: dict):
        self.name_ = name
        self.content_ = content

    @classmethod
    def createFromDict(cls, name: str, content: dict):
        # validation
        lst = []
        for k, v in content.items():
            assert k in content
            lst.append(v)
        assert len(lst) == len(OptionStrategy.schema)

        # build content dict
        # key   : (opt_type, delta_strike)
        # value : weight
        result = {}
        for i in range(len(lst[0])):
            t = OptionPayoff.FORWARD
            if lst[0][i].upper() == "C":
                t = OptionPayoff.CALL
            elif lst[0][i].upper() == "P":
                t = OptionPayoff.PUT
            result[(t, lst[1][i])] = lst[2][i]
        return OptionStrategy(name, result)

    @classmethod
    def createFromList(
        cls, name: str, opt_types: list, delta_strikes: list, weights: list
    ):
        assert len(opt_types) == len(delta_strikes) == len(weights)
        # build content dict
        # key   : (opt_type, delta_strike)
        # value : weight
        result = {}
        for i in range(len(opt_types)):
            t = OptionPayoff.FORWARD
            if opt_types[i].upper() == "C":
                t = OptionPayoff.CALL
            elif opt_types[i].upper() == "P":
                t = OptionPayoff.PUT
            result[(t, delta_strikes[i])] = weights[i]
        return OptionStrategy(name, result)

    ### simple getters
    @property
    def name(self):
        return self.name_

    @property
    def content(self):
        return self.content_

    ### utilities

    # back out absolute strike from delta (model implied)
    @staticmethod
    def strike_from_delta(
        delta: float,
        opt_type: OptionPayoff,
        underlying: float,
        vol: float,
        time_to_expiry: float,
        is_log_normal: bool,
    ):

        if opt_type == OptionPayoff.PUT:
            delta = 1.0 + delta

        cutoff = norm.ppf(delta)
        var = vol * vol * time_to_expiry

        if is_log_normal:
            return underlying / np.exp(cutoff * np.sqrt(var) - 0.5 * var)
        else:
            return underlying - cutoff * np.sqrt(var)

    # european call/put payoff
    @staticmethod
    def payoff_helper(underlying: float, strike: float, call_or_put: OptionPayoff):
        sign = 1.0 if call_or_put == OptionPayoff.CALL else -1.0
        return np.maximum(sign * (underlying - strike), 0.0)

    # payoff
    def run(
        self,
        underlying_rng: list,
        forward: float,
        time_to_expiry: float,
        vol: float,
        is_log_normal: Optional[bool] = True,
    ):
        # strike translation
        strikes_map = {}
        for k, v in self.content_.items():
            strikes_map[k[1]] = OptionStrategy.strike_from_delta(
                k[1], k[0], forward, vol, time_to_expiry, is_log_normal
            )

        # payoff sampling
        result = []
        for x in underlying_rng:
            acc = 0.0
            for k, v in self.content.items():
                acc += OptionStrategy.payoff_helper(x, strikes_map[k[1]], k[0]) * v
            result.append([x, acc])
        return pd.DataFrame(result, columns=["FORWARD", "PAYOFF"])

    ### operator overloading

    def __contains__(self, key: Tuple):
        return (key[0], key[1]) in self.content

    def __getitem__(self, key: Tuple):
        if not self.content.__contains__(key):
            raise Exception(
                f"{key[0]} and {key[1]} is not part of strategy definition."
            )
        return self.content[(key[0], key[1])]

    def __len__(self):
        return len(self.content)

    def __add__(self, in_strategy: "OptionStrategy"):
        content = dict()
        traversed_keys = []
        for k, v in self.content.items():
            content[k] = v
            if k in in_strategy.content:
                content[k] += in_strategy[k]
                traversed_keys.append(k)
            if content[k] == 0.0:
                content.pop(k)
        for k, v in in_strategy.content.items():
            if k not in traversed_keys:
                content[k] = v
        return OptionStrategy(f"{self.name}_ADD_{in_strategy.name}", content)

    def __mul__(self, scaler: float):
        content = dict()
        for k, v in self.content.items():
            if scaler != 0.0:
                content[k] = v * scaler
        return OptionStrategy(f"{self.name}_SCALED_BY_{scaler}", content)


### Option Strategy Registry
class OptionStrategyRegistry(Registry):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
            cls._instance._load_defaults()
        return cls._instance

    def _load_defaults(self):
        config_folder = get_config_folder()
        yaml_path = os.path.join(config_folder, "strategies.yaml")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        for name, content in data.items():
            self._registry[name] = OptionStrategy.createFromDict(name, content)

    def register(self, name: str, strategy_input):

        if isinstance(strategy_input, dict):
            strat = OptionStrategy.createFromDict(name, strategy_input)

        elif isinstance(strategy_input, (list, tuple)):
            strat = OptionStrategy.createFromList(
                name,
                strategy_input[0],
                strategy_input[1],
                strategy_input[2],
            )

        else:
            raise TypeError("strategy_input must be dict or list/tuple")

        self._registry[name] = strat

    def list_registry_keys(self):
        return list(self._registry.keys())

    def get(self, name: str):
        return self._registry.get(name)
