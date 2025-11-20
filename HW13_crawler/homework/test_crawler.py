"""
Тесты для Hacker News crawler
"""
import pytest
import pytest_asyncio
import asyncio
import os
from datetime import datetime
from models import Story, Comment
from storage import Storage
from crawler import HackerNewsCrawler


@pytest_asyncio.fixture
async def storage():
    """Фикстура для временной БД"""
    db_path = "test_hackernews.db"
    storage = Storage(db_path)
    await storage.init_db()
    yield storage
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


class TestModels:
    """Тесты моделей данных"""

    def test_story_creation(self):
        """Тест создания Story"""
        story = Story(
            id=12345,
            title="Test Story",
            url="https://example.com",
            by="testuser",
            time=1234567890,
            score=100,
            descendants=50,
            kids=[1, 2, 3]
        )
        assert story.id == 12345
        assert story.title == "Test Story"
        assert isinstance(story.created_at, datetime)

    def test_comment_creation(self):
        """Тест создания Comment"""
        comment = Comment(
            id=67890,
            by="testuser",
            time=1234567890,
            text="Test comment with https://example.com",
            parent=12345,
            kids=[10, 20]
        )
        assert comment.id == 67890
        assert isinstance(comment.created_at, datetime)


class TestStorage:
    """Тесты хранилища"""

    @pytest.mark.asyncio
    async def test_init_db(self, storage):
        """Тест инициализации БД"""
        stats = await storage.get_stats()
        assert stats["stories"] == 0
        assert stats["comments"] == 0
        assert stats["links"] == 0

    @pytest.mark.asyncio
    async def test_save_story(self, storage):
        """Тест сохранения новости"""
        story = Story(
            id=12345,
            title="Test Story",
            url="https://example.com",
            by="testuser",
            time=1234567890,
            score=100,
            descendants=50,
            kids=[]
        )
        result = await storage.save_story(story)
        assert result is True

        stats = await storage.get_stats()
        assert stats["stories"] == 1

    @pytest.mark.asyncio
    async def test_save_comment(self, storage):
        """Тест сохранения комментария"""
        # Сначала создаем новость
        story = Story(
            id=12345,
            title="Test Story",
            url="https://example.com",
            by="testuser",
            time=1234567890,
            score=100,
            descendants=50,
            kids=[]
        )
        await storage.save_story(story)

        # Теперь комментарий
        comment = Comment(
            id=67890,
            by="commenter",
            time=1234567890,
            text="Great article!",
            parent=12345
        )
        result = await storage.save_comment(comment, story.id)
        assert result is True

        stats = await storage.get_stats()
        assert stats["comments"] == 1

    @pytest.mark.asyncio
    async def test_extract_links(self, storage):
        """Тест извлечения ссылок из комментария"""
        story = Story(
            id=12345,
            title="Test",
            url=None,
            by="user",
            time=1234567890,
            score=10,
            descendants=1,
            kids=[]
        )
        await storage.save_story(story)

        comment = Comment(
            id=67890,
            by="commenter",
            time=1234567890,
            text="Check out https://example.com and https://test.org",
            parent=12345
        )
        await storage.save_comment(comment, story.id)

        stats = await storage.get_stats()
        assert stats["links"] == 2

    @pytest.mark.asyncio
    async def test_story_exists(self, storage):
        """Тест проверки существования новости"""
        exists = await storage.story_exists(99999)
        assert exists is False

        story = Story(
            id=12345,
            title="Test",
            url=None,
            by="user",
            time=1234567890,
            score=10,
            descendants=0,
            kids=[]
        )
        await storage.save_story(story)

        exists = await storage.story_exists(12345)
        assert exists is True


class TestCrawler:
    """Тесты краулера"""

    @pytest.mark.asyncio
    async def test_crawler_context_manager(self, storage):
        """Тест создания и закрытия сессии"""
        crawler = HackerNewsCrawler(storage, max_stories=5, max_comments=10)

        async with crawler:
            assert crawler.session is not None

        # После выхода из контекста сессия должна быть закрыта
        assert crawler.session.closed

    @pytest.mark.asyncio
    async def test_fetch_json_invalid_url(self, storage):
        """Тест обработки невалидного URL"""
        async with HackerNewsCrawler(storage) as crawler:
            result = await crawler.fetch_json("https://invalid-url-that-does-not-exist-12345.com")
            assert result is None

    def test_link_extraction(self, storage):
        """Тест извлечения ссылок из текста"""
        links = storage._extract_links(
            "Check https://example.com and http://test.org/path"
        )
        assert len(links) == 2
        assert "https://example.com" in links
        assert "http://test.org/path" in links

    def test_link_extraction_empty(self, storage):
        """Тест извлечения ссылок из пустого текста"""
        links = storage._extract_links("")
        assert len(links) == 0

        links = storage._extract_links(None)
        assert len(links) == 0

    def test_link_extraction_duplicates(self, storage):
        """Тест удаления дубликатов ссылок"""
        links = storage._extract_links(
            "Visit https://example.com and https://example.com again"
        )
        assert len(links) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
