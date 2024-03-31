import json
from typing import Dict

from .user import User

class Guild:
    def __init__(self, guild_id: str, data: dict) -> None:
        self.guild_id = guild_id
        self.data = self._load_data(data)
    
    def _load_data(self, raw_data: dict) -> Dict[str, User]:
        resp = {}
        for user_id, data in raw_data.items():
            resp[user_id] = User(user_id, data)
    
        return resp
    
    def __repr__(self) -> str:
        return self.data.__repr__()
    
    def __dict__(self) -> dict:
        return self.data


class GuildEncoder(json.JSONEncoder):
    def default(self, obj: Guild):
        
        if not isinstance(obj, Guild):
            return super().default(obj)
        
        resp = {}
        for guild_id, user_data in obj.data.items():
            resp[guild_id] = user_data.data
        
        return resp
        