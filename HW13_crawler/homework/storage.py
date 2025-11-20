"""
Хранилище данных для Hacker News crawler (SQLite)
"""
import aiosqlite
import logging
from typing import List, Optional
from models import Story, Comment
import re

logger = logging.getLogger(__name__)


class Storage:
    """Асинхронное хранилище на основе SQLite"""

    def __init__(self, db_path: str = "hackernews.db"):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица новостей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stories (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT,
                    by TEXT NOT NULL,
                    time INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    descendants INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица комментариев
            await db.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY,
                    story_id INTEGER NOT NULL,
                    by TEXT NOT NULL,
                    time INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    parent INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                )
            """)

            # Таблица ссылок из комментариев
            await db.execute("""
                CREATE TABLE IF NOT EXISTS comment_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comment_id INTEGER NOT NULL,
                    story_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (comment_id) REFERENCES comments(id),
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                )
            """)

            # Индексы для быстрого поиска
            await db.execute("CREATE INDEX IF NOT EXISTS idx_stories_time ON stories(time)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_comments_story ON comments(story_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_links_story ON comment_links(story_id)")

            await db.commit()
            logger.info(f"Database initialized: {self.db_path}")

    async def save_story(self, story: Story) -> bool:
        """Сохранение новости"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO stories (id, title, url, by, time, score, descendants)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (story.id, story.title, story.url, story.by, story.time, story.score, story.descendants))
                await db.commit()
                logger.debug(f"Saved story: {story.id}")
                return True
        except Exception as e:
            logger.error(f"Error saving story {story.id}: {e}")
            return False

    async def save_comment(self, comment: Comment, story_id: int) -> bool:
        """Сохранение комментария"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO comments (id, story_id, by, time, text, parent)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (comment.id, story_id, comment.by, comment.time, comment.text, comment.parent))
                await db.commit()

                # Извлечение и сохранение ссылок из текста комментария
                links = self._extract_links(comment.text)
                if links:
                    await self._save_links(comment.id, story_id, links)

                logger.debug(f"Saved comment: {comment.id} with {len(links)} links")
                return True
        except Exception as e:
            logger.error(f"Error saving comment {comment.id}: {e}")
            return False

    def _extract_links(self, text: str) -> List[str]:
        """Извлечение URL из текста комментария"""
        if not text:
            return []

        # Регулярное выражение для поиска URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        links = re.findall(url_pattern, text)

        # Убираем дубликаты
        return list(set(links))

    async def _save_links(self, comment_id: int, story_id: int, links: List[str]):
        """Сохранение ссылок из комментария"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for link in links:
                    await db.execute("""
                        INSERT INTO comment_links (comment_id, story_id, url)
                        VALUES (?, ?, ?)
                    """, (comment_id, story_id, link))
                await db.commit()
        except Exception as e:
            logger.error(f"Error saving links for comment {comment_id}: {e}")

    async def story_exists(self, story_id: int) -> bool:
        """Проверка существования новости"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM stories WHERE id = ?", (story_id,)) as cursor:
                result = await cursor.fetchone()
                return result is not None

    async def get_stats(self) -> dict:
        """Получение статистики по базе данных"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM stories") as cursor:
                stories_count = (await cursor.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM comments") as cursor:
                comments_count = (await cursor.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM comment_links") as cursor:
                links_count = (await cursor.fetchone())[0]

        return {
            "stories": stories_count,
            "comments": comments_count,
            "links": links_count
        }
