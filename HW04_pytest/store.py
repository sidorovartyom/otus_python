#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import logging
from typing import Optional, Any
from abc import ABC, abstractmethod

# Попытка импорта Redis, если доступен
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Попытка импорта Memcached, если доступен
try:
    import memcache
    MEMCACHE_AVAILABLE = True
except ImportError:
    MEMCACHE_AVAILABLE = False


class StoreError(Exception):
    """Базовый класс для ошибок хранилища"""
    pass


class ConnectionError(StoreError):
    """Ошибка подключения к хранилищу"""
    pass


class TimeoutError(StoreError):
    """Ошибка таймаута"""
    pass


class BaseStore(ABC):
    """Абстрактный базовый класс для хранилища"""
    
    def __init__(self, max_retries: int = 3, timeout: float = 1.0):
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def _get(self, key: str) -> Optional[str]:
        """Получить значение по ключу"""
        pass
    
    @abstractmethod
    def _set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Установить значение по ключу"""
        pass
    
    def _retry_operation(self, operation, *args, **kwargs):
        """Выполнить операцию с retry логикой"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except (ConnectionError, TimeoutError) as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Экспоненциальная задержка
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise
        
        self.logger.error(f"All {self.max_retries} attempts failed")
        raise last_exception
    
    def get(self, key: str) -> Optional[str]:
        """Получить значение из персистентного хранилища"""
        try:
            return self._retry_operation(self._get, key)
        except StoreError:
            # Для персистентного хранилища возвращаем None при ошибках
            self.logger.error(f"Failed to get key {key} from persistent storage")
            return None
    
    def cache_get(self, key: str) -> Optional[str]:
        """Получить значение из кеша"""
        try:
            return self._retry_operation(self._get, key)
        except StoreError:
            # Для кеша возвращаем None при ошибках
            self.logger.error(f"Failed to get key {key} from cache")
            return None
    
    def cache_set(self, key: str, value: Any, ttl: int) -> bool:
        """Установить значение в кеш с TTL"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)
            
            return self._retry_operation(self._set, key, value, ttl)
        except StoreError:
            # Для кеша игнорируем ошибки записи
            self.logger.error(f"Failed to set key {key} in cache")
            return False


class RedisStore(BaseStore):
    """Реализация хранилища на основе Redis"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, 
                 max_retries: int = 3, timeout: float = 1.0):
        super().__init__(max_retries, timeout)
        
        if not REDIS_AVAILABLE:
            raise ImportError("Redis library not available. Install with: pip install redis")
        
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            socket_timeout=timeout,
            socket_connect_timeout=timeout,
            retry_on_timeout=True,
            health_check_interval=30
        )
    
    def _get(self, key: str) -> Optional[str]:
        """Получить значение из Redis"""
        try:
            value = self.redis_client.get(key)
            return value.decode('utf-8') if value else None
        except redis.ConnectionError as e:
            raise ConnectionError(f"Redis connection error: {e}")
        except redis.TimeoutError as e:
            raise TimeoutError(f"Redis timeout error: {e}")
        except Exception as e:
            raise StoreError(f"Redis error: {e}")
    
    def _set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Установить значение в Redis"""
        try:
            if ttl:
                return self.redis_client.setex(key, ttl, value)
            else:
                return self.redis_client.set(key, value)
        except redis.ConnectionError as e:
            raise ConnectionError(f"Redis connection error: {e}")
        except redis.TimeoutError as e:
            raise TimeoutError(f"Redis timeout error: {e}")
        except Exception as e:
            raise StoreError(f"Redis error: {e}")


class MemcacheStore(BaseStore):
    """Реализация хранилища на основе Memcached"""
    
    def __init__(self, servers: list = None, max_retries: int = 3, timeout: float = 1.0):
        super().__init__(max_retries, timeout)
        
        if not MEMCACHE_AVAILABLE:
            raise ImportError("Memcache library not available. Install with: pip install python-memcached")
        
        if servers is None:
            servers = ['localhost:11211']
        
        self.memcache_client = memcache.Client(servers, debug=0)
    
    def _get(self, key: str) -> Optional[str]:
        """Получить значение из Memcached"""
        try:
            value = self.memcache_client.get(key)
            return value if value else None
        except Exception as e:
            raise StoreError(f"Memcache error: {e}")
    
    def _set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Установить значение в Memcached"""
        try:
            return self.memcache_client.set(key, value, time=ttl or 0)
        except Exception as e:
            raise StoreError(f"Memcache error: {e}")


class MockStore(BaseStore):
    """Mock хранилище для тестирования"""
    
    def __init__(self, max_retries: int = 3, timeout: float = 1.0):
        super().__init__(max_retries, timeout)
        self._storage = {}
        self._cache = {}
        self._should_fail = False
        self._connection_errors = 0
    
    def _get(self, key: str) -> Optional[str]:
        """Получить значение из mock хранилища"""
        if self._should_fail:
            raise ConnectionError("Mock connection error")
        
        if self._connection_errors > 0:
            self._connection_errors -= 1
            raise ConnectionError("Mock connection error")
        
        return self._storage.get(key)
    
    def _set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Установить значение в mock хранилище"""
        if self._should_fail:
            raise ConnectionError("Mock connection error")
        
        if self._connection_errors > 0:
            self._connection_errors -= 1
            raise ConnectionError("Mock connection error")
        
        self._storage[key] = value
        return True
    
    def cache_get(self, key: str) -> Optional[str]:
        """Получить значение из mock кеша"""
        try:
            if self._should_fail:
                raise ConnectionError("Mock connection error")
            
            if self._connection_errors > 0:
                self._connection_errors -= 1
                raise ConnectionError("Mock connection error")
            
            return self._cache.get(key)
        except Exception:
            # Публичные методы должны возвращать None при ошибках
            return None
    
    def cache_set(self, key: str, value: Any, ttl: int) -> bool:
        """Установить значение в mock кеш"""
        try:
            if self._should_fail:
                raise ConnectionError("Mock connection error")
            
            if self._connection_errors > 0:
                self._connection_errors -= 1
                raise ConnectionError("Mock connection error")
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)
            
            self._cache[key] = value
            return True
        except Exception:
            # Публичные методы должны возвращать False при ошибках
            return False
    
    # Методы для тестирования
    def set_should_fail(self, should_fail: bool):
        """Установить флаг для симуляции ошибок"""
        self._should_fail = should_fail
    
    def set_connection_errors(self, count: int):
        """Установить количество ошибок подключения"""
        self._connection_errors = count
    
    def clear(self):
        """Очистить хранилище"""
        self._storage.clear()
        self._cache.clear()


def create_store(store_type: str = 'mock', **kwargs) -> BaseStore:
    """Фабрика для создания хранилища"""
    if store_type == 'redis':
        return RedisStore(**kwargs)
    elif store_type == 'memcache':
        return MemcacheStore(**kwargs)
    elif store_type == 'mock':
        return MockStore(**kwargs)
    else:
        raise ValueError(f"Unknown store type: {store_type}")


# Для обратной совместимости
class Store:
    """Класс-обертка для создания хранилища по умолчанию"""
    
    def __init__(self, store_type: str = 'mock', **kwargs):
        self._store = create_store(store_type, **kwargs)
    
    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)
    
    def cache_get(self, key: str) -> Optional[str]:
        return self._store.cache_get(key)
    
    def cache_set(self, key: str, value: Any, ttl: int) -> bool:
        return self._store.cache_set(key, value, ttl) 