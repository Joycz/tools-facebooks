from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Account:
    id: int
    name: str
    cookie: str
    added_date: str
    updated_date: Optional[str] = None
    
    @classmethod
    def create(cls, id: int, name: str, cookie: str) -> 'Account':
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls(
            id=id,
            name=name,
            cookie=cookie,
            added_date=now
        )
        
    def update(self, name: str, cookie: str):
        self.name = name
        self.cookie = cookie
        self.updated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'cookie': self.cookie,
            'added_date': self.added_date,
            'updated_date': self.updated_date
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Account':
        return cls(
            id=data['id'],
            name=data['name'],
            cookie=data['cookie'],
            added_date=data['added_date'],
            updated_date=data.get('updated_date')
        ) 