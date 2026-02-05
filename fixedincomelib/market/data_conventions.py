from abc import ABC
from enum import Enum
import pandas as pd
from fixedincomelib.date import *
from fixedincomelib.market.registries import *
from fixedincomelib.market.basics import AccrualBasis, BusinessDayConvention, HolidayConvention

class CompoundingMethod(Enum):
    
    SIMPLE = 'simple'
    ARITHMETIC = 'arithmetic'
    COMPOUND = 'compound'

    @classmethod
    def from_string(cls, value: str) -> 'CompoundingMethod':
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value

### interface
class DataConvention(ABC):

    _type = ''

    def __init__(self, unique_name : str, type : str, content : dict):
        super().__init__()
        self.conv_name = unique_name.upper()
        self.conv_type = type.upper()
        self.content = content
        assert len(self.content) != 0
    
    @property
    def name(self):
        return self.conv_name
    
    @classmethod
    def type(cls):
        return cls._type
    
    def display(self):
        to_print = []
        for k, v in self.content.items():
            k_ = k
            if k_.endswith('_'):
                k_ = k[:-1]
            to_print.append([k_.upper(), v])
        return pd.DataFrame(to_print, columns=['Name', 'Value'])

class DataConventionRegFunction(Registry):

    def __new__(cls) -> Self:
        return super().__new__(cls, '', cls.__name__)

    def register(self, key : Any, value : Any) -> None:
        super().register(key, value)
        self._map[key] = value

class DataConventionRegistry(Registry):

    def __new__(cls) -> Self:
        return super().__new__(cls, 'data_conventions', 'DataConevention')
    
    def register(self, key : Any, value : Any) -> None:
        value_ = value.copy()
        super().register(key, value_)
        type = value_['type']
        value_.pop('type')
        func = DataConventionRegFunction().get(type)
        self._map[key] = func(key, value_)

    def display_all_data_conventions(self) -> pd.DataFrame:
        to_print = []
        for k, v in self._map.items():
            to_print.append([k, v.name])
        return pd.DataFrame(to_print, columns=['Name', 'Type'])
