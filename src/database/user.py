import copy
from typing import Dict, List, Tuple

DEFAULT_STATS = {
    "cash": 4000,
    "stocks" : {}
}

class User:
    def __init__(self, user_id: str, data: dict=None) -> None:
        self.user_id = user_id
        
        self.data = copy.deepcopy(DEFAULT_STATS) if data is None else data


    @property
    def cash(self) -> int:
        if 'cash' not in self.data:
            self.data['cash'] = DEFAULT_STATS['cash']
        
        return self.data['cash']
        
    @cash.setter
    def cash(self, value: int) -> None:
        self.data['cash'] = value
    
    @property
    def stocks(self) -> Dict[str, float]:
        if 'stocks' not in self.data:
            self.data['stocks'] = DEFAULT_STATS['stocks']
         
        return self.data['stocks']
    
    
    def __repr__(self) -> str:
        return self.data.__repr__()