import json
from pprint import pprint
from typing import Dict

from .guild import Guild, GuildEncoder


class InMemoryDatabase:
    def __init__(self, data_json_path: str):
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
            json.dump(self.data, f, indent=4, cls=GuildEncoder)

    def display_all(self):
        pprint(self.data)

    def get_user(self, guild_id: int, auther_id: int):
        
        guild_id = hex(guild_id)
        
        # check if the guild exists
        if guild_id not in self.data:
            self.data[guild_id] = Guild(guild_id)
        
        guild = self.data[guild_id]
        
        return guild.get_user(auther_id)


def main():
    file_path = "../data.json"
    db = InMemoryDatabase(file_path)

    db.display_all()
    db.save_data("../data.json")

if __name__ == "__main__":
    main()
