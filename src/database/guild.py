import copy
import json
from typing import Dict

from .user import User

DEFAULT_STATS = {}

class Guild:
    def __init__(self, guild_id: str, data: dict=None) -> None:
        self.guild_id = guild_id
        
        self.data = copy.deepcopy(DEFAULT_STATS) if data is None else self._load_data(data)

    
    def _load_data(self, raw_data: dict) -> Dict[str, User]:
        resp = {}
        for user_id, data in raw_data.items():
            resp[user_id] = User(int(user_id, 16), data)
    
        return resp
    
    def get_user(self, user_id: int) -> User:

        user_id = hex(user_id)

        if user_id not in self.data:
            self.data[user_id] = User(user_id)
        
        return self.data[user_id]
    
    
    def serialize(self) -> Dict[str, dict]:
        resp = {}
        
        for i in self.data:
            resp[i] = self.data[i].serialize()
        
        return resp
    
    def __repr__(self) -> str:
        return self.data.__repr__()
