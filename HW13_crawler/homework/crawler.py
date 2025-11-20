"""
Асинхронный краулер для Hacker News
"""
import asyncio
import aiohttp
import logging
from typing import List, Optional, Dict, Any
import argparse
from models import Story, Comment
from storage import Storage

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HackerNewsCrawler:
    """Асинхронный краулер для Hacker News"""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, storage: Storage, max_stories: int = 30, max_comments: int = 100):
        """
        Args:
            storage: Хранилище данных
            max_stories: Максимальное количество новостей для обработки
            max_comments: Максимальное количество комментариев на новость
        """
        self.storage = storage
        self.max_stories = max_stories
        self.max_comments = max_comments
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Создание aiohttp сессии"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие aiohttp сессии"""
        if self.session:
            await self.session.close()

    async def fetch_json(self, url: str) -> Optional[Dict[Any, Any]]:
        """Асинхронный GET запрос с возвратом JSON"""
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def get_top_stories(self) -> List[int]:
        """Получение ID топовых новостей"""
        url = f"{self.BASE_URL}/topstories.json"
        story_ids = await self.fetch_json(url)
        if story_ids:
            logger.info(f"Fetched {len(story_ids)} top story IDs")
            return story_ids[:self.max_stories]
        return []

    async def get_story(self, story_id: int) -> Optional[Story]:
        """Получение деталей новости по ID"""
        url = f"{self.BASE_URL}/item/{story_id}.json"
        data = await self.fetch_json(url)

        if not data or data.get("type") != "story":
            return None

        try:
            return Story(
                id=data["id"],
                title=data.get("title", ""),
                url=data.get("url"),
                by=data.get("by", "unknown"),
                time=data.get("time", 0),
                score=data.get("score", 0),
                descendants=data.get("descendants", 0),
                kids=data.get("kids", [])
            )
        except KeyError as e:
            logger.error(f"Missing field in story {story_id}: {e}")
            return None

    async def get_comment(self, comment_id: int) -> Optional[Comment]:
        """Получение комментария по ID"""
        url = f"{self.BASE_URL}/item/{comment_id}.json"
        data = await self.fetch_json(url)

        if not data or data.get("type") != "comment":
            return None

        try:
            return Comment(
                id=data["id"],
                by=data.get("by", "unknown"),
                time=data.get("time", 0),
                text=data.get("text", ""),
                parent=data.get("parent", 0),
                kids=data.get("kids")
            )
        except KeyError as e:
            logger.error(f"Missing field in comment {comment_id}: {e}")
            return None

    async def crawl_comments(self, story_id: int, comment_ids: List[int]) -> int:
        """
        Асинхронный обход комментариев новости

        Args:
            story_id: ID новости
            comment_ids: Список ID комментариев

        Returns:
            Количество обработанных комментариев
        """
        if not comment_ids:
            return 0

        # Ограничиваем количество комментариев
        comment_ids = comment_ids[:self.max_comments]

        # Создаем задачи для параллельной загрузки комментариев
        tasks = [self.get_comment(cid) for cid in comment_ids]
        comments = await asyncio.gather(*tasks)

        # Фильтруем None и сохраняем комментарии
        saved_count = 0
        for comment in comments:
            if comment:
                if await self.storage.save_comment(comment, story_id):
                    saved_count += 1

                # Рекурсивно обрабатываем дочерние комментарии
                if comment.kids:
                    child_count = await self.crawl_comments(story_id, comment.kids)
                    saved_count += child_count

        return saved_count

    async def crawl_story(self, story_id: int) -> bool:
        """
        Обход одной новости с комментариями

        Args:
            story_id: ID новости

        Returns:
            True если новость успешно обработана
        """
        # Проверяем, не обработана ли уже эта новость
        if await self.storage.story_exists(story_id):
            logger.debug(f"Story {story_id} already exists, skipping")
            return False

        # Получаем данные новости
        story = await self.get_story(story_id)
        if not story:
            logger.warning(f"Failed to fetch story {story_id}")
            return False

        # Сохраняем новость
        if not await self.storage.save_story(story):
            return False

        logger.info(f"Processing story {story.id}: '{story.title[:60]}...'")

        # Обрабатываем комментарии
        if story.kids:
            comments_count = await self.crawl_comments(story.id, story.kids)
            logger.info(f"Story {story.id}: saved {comments_count} comments")

        return True

    async def crawl(self):
        """Основной метод краулинга"""
        logger.info("Starting Hacker News crawl...")

        # Получаем топ новостей
        story_ids = await self.get_top_stories()
        if not story_ids:
            logger.error("No stories found")
            return

        # Создаем задачи для параллельной обработки новостей
        tasks = [self.crawl_story(story_id) for story_id in story_ids]
        results = await asyncio.gather(*tasks)

        # Статистика
        processed = sum(1 for r in results if r)
        logger.info(f"Crawl completed: {processed}/{len(story_ids)} new stories processed")

        # Показываем статистику БД
        stats = await self.storage.get_stats()
        logger.info(f"Database stats: {stats['stories']} stories, "
                    f"{stats['comments']} comments, {stats['links']} links")


async def run_crawler(max_stories: int, max_comments: int, db_path: str):
    """Запуск краулера"""
    storage = Storage(db_path)
    await storage.init_db()

    async with HackerNewsCrawler(storage, max_stories, max_comments) as crawler:
        await crawler.crawl()


async def run_periodic_crawler(interval: int, max_stories: int, max_comments: int, db_path: str):
    """Периодический запуск краулера"""
    logger.info(f"Starting periodic crawler (interval: {interval}s)")

    storage = Storage(db_path)
    await storage.init_db()

    while True:
        try:
            async with HackerNewsCrawler(storage, max_stories, max_comments) as crawler:
                await crawler.crawl()
        except Exception as e:
            logger.error(f"Crawl error: {e}", exc_info=True)

        logger.info(f"Waiting {interval} seconds before next crawl...")
        await asyncio.sleep(interval)


def main():
    """CLI интерфейс"""
    parser = argparse.ArgumentParser(description="Hacker News Async Crawler")
    parser.add_argument(
        "--max-stories",
        type=int,
        default=30,
        help="Maximum number of stories to crawl (default: 30)"
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        default=100,
        help="Maximum number of comments per story (default: 100)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Run periodically every N seconds (0 = run once, default: 0)"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="hackernews.db",
        help="Path to SQLite database (default: hackernews.db)"
    )

    args = parser.parse_args()

    if args.interval > 0:
        # Периодический режим
        asyncio.run(run_periodic_crawler(args.interval, args.max_stories, args.max_comments, args.db))
    else:
        # Однократный запуск
        asyncio.run(run_crawler(args.max_stories, args.max_comments, args.db))


if __name__ == "__main__":
    main()
