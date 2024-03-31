class User:
    def __init__(self, user_id: str, data: dict) -> None:
        self.user_id = user_id
        self.data = data
    
    def __repr__(self) -> str:
        return self.data.__repr__()