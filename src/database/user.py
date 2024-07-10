import copy
import json
from typing import Dict

from database.position import Position

DEFAULT_STATS = {
    "cash": 4000,
    "stocks" : {}
}

class User:
    def __init__(self, user_id: str, data: dict=None) -> None:
        self.user_id = user_id

        self.data = copy.deepcopy(DEFAULT_STATS) if data is None else self._load_data(data)

    def _load_data(self, raw_data: dict) -> Dict[str, Position]:
        resp = {}
        
        resp['cash'] = raw_data['cash']
        resp['stocks'] = {}
        
        for symbol, data in raw_data['stocks'].items():
            resp['stocks'][symbol] = Position(symbol, data)
    
        return resp

    @property
    def cash(self) -> int:
        if 'cash' not in self.data:
            self.data['cash'] = DEFAULT_STATS['cash']
        
        return self.data['cash']
        
    @cash.setter
    def cash(self, value: int) -> None:
        self.data['cash'] = value
    
    @property
    def stocks(self) -> Dict[str, Position]:
        if 'stocks' not in self.data:
            self.data['stocks'] = DEFAULT_STATS['stocks']
         
        return self.data['stocks']
    
    
    def serialize(self) -> Dict[str, dict]:
        resp = {}
        
        resp['cash'] = self.cash
        resp['stocks'] = {}

        for i in self.stocks:
            resp['stocks'][i] = self.stocks[i].serialize()
        
        return resp
    
    def __repr__(self) -> str:
        return self.data.__repr__()
