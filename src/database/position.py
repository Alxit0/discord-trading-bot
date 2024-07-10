import copy
from typing import Dict


DEFAULT_STATS = {
    'number_owned': 0,
    'valued_invested': 0
}

class Position:
    def __init__(self, symbol: str, data:dict = None) -> None:
        self.data = copy.deepcopy(DEFAULT_STATS) if data is None else data
        self.symbol = symbol
    
    @property
    def number_owned(self) -> float:
        if 'number_owned' not in self.data:
            self.data['number_owned'] = DEFAULT_STATS['number_owned']
         
        return self.data['number_owned']
    
    @number_owned.setter
    def number_owned(self, value: int) -> None:
        self.data['number_owned'] = value


    @property
    def valued_invested(self) -> float:
        if 'valued_invested' not in self.data:
            self.data['valued_invested'] = DEFAULT_STATS['valued_invested']
         
        return self.data['valued_invested']
    
    @valued_invested.setter
    def valued_invested(self, value: int) -> None:
        self.data['valued_invested'] = value
    
    
    def serialize(self) -> Dict[str, float]:
        resp = {}

        for i in self.data:
            resp[i] = self.data[i]
            
        return resp
    
    def __repr__(self) -> str:
        return self.data.__repr__()