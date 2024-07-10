import json
from pprint import pprint
from typing import Dict, List

from database.user import User
from utils import default_data_file

from .guild import Guild


class InMemoryDatabase:
    def __init__(self, data_json_path: str):
        default_data_file(data_json_path)
        
        self.file_path = data_json_path
        self.data = self._load_data(data_json_path)
    
    def _load_data(self, file_path) -> Dict[str, Guild]:
        if file_path is None:
            return {}
        
        with open(file_path, 'r') as f:
            raw_data: dict = json.load(f)

        resp = {}
        for guild_id, data in raw_data.items():
            resp[guild_id] = Guild(guild_id, data)

        return resp
    
    def save_data(self):
        if self.file_path is None:
            return
        
        with open(self.file_path, 'w') as f:
            json.dump(self.serialize(), f, indent=4)

    def display_all(self):
        pprint(self.data)

    def get_guild_users(self, guild_id: int) -> List[User]:
        return list(self.get_guild(guild_id).data.values())

    def get_guild(self, guild_id: int) -> Guild:
        guild_id = hex(guild_id)
        
        # check if the guild exists
        if guild_id not in self.data:
            self.data[guild_id] = Guild(guild_id)
        
        return self.data[guild_id]

    def get_user(self, guild_id: int, auther_id: int):
        
        guild_id = hex(guild_id)
        
        # check if the guild exists
        if guild_id not in self.data:
            self.data[guild_id] = Guild(guild_id)
        
        guild = self.data[guild_id]
        
        return guild.get_user(auther_id)

    def serialize(self) -> Dict[str, dict]:
        resp = {}
        
        for i in self.data:
            resp[i] = self.data[i].serialize()
        
        return resp


def main():
    file_path = "../data.json"
    db = InMemoryDatabase(file_path)

    db.display_all()
    db.save_data("../data.json")

if __name__ == "__main__":
    main()
