"""
Модели данных для Hacker News crawler
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Story:
    """Модель новости с Hacker News"""
    id: int
    title: str
    url: Optional[str]
    by: str
    time: int
    score: int
    descendants: int  # количество комментариев
    kids: List[int]  # ID комментариев

    @property
    def created_at(self) -> datetime:
        """Конвертация timestamp в datetime"""
        return datetime.fromtimestamp(self.time)

    def __repr__(self):
        return f"Story(id={self.id}, title='{self.title[:50]}...', by={self.by}, score={self.score})"


@dataclass
class Comment:
    """Модель комментария с Hacker News"""
    id: int
    by: str
    time: int
    text: str
    parent: int
    kids: Optional[List[int]] = None

    @property
    def created_at(self) -> datetime:
        """Конвертация timestamp в datetime"""
        return datetime.fromtimestamp(self.time)

    def __repr__(self):
        text_preview = self.text[:50] if self.text else ""
        return f"Comment(id={self.id}, by={self.by}, text='{text_preview}...')"
