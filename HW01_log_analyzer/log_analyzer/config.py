#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from typing import Dict

import structlog

logger = structlog.get_logger()

# Конфигурация по умолчанию
DEFAULT_CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOG_FILE": None,  # если None, то логи в stdout
    "ERROR_THRESHOLD": 0.1  # 10% ошибок парсинга
}


def load_config(config_path: str) -> Dict:
    """
    Загрузить конфигурацию из файла.
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Объединенная конфигурация
        
    Raises:
        FileNotFoundError: Если файл конфигурации не найден
        json.JSONDecodeError: Если файл содержит невалидный JSON
    """
    if not os.path.exists(config_path):
        logger.error("Файл конфигурации не найден", config_path=config_path)
        raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            file_config = json.load(f)
        
        # Объединяем с дефолтным конфигом
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(file_config)
        
        logger.info("Конфигурация загружена", config_path=config_path)
        return merged_config
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Ошибка при загрузке конфигурации", error=str(e), config_path=config_path)
        raise


def setup_logging(config: Dict):
    """
    Настроить логирование.
    
    Args:
        config: Конфигурация с настройками логирования
    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Настраиваем вывод логов
    if config.get("LOG_FILE"):
        import logging
        logging.basicConfig(
            format="%(message)s",
            stream=open(config["LOG_FILE"], 'w', encoding='utf-8'),
            level=logging.INFO,
        )
    else:
        import logging
        logging.basicConfig(
            format="%(message)s",
            level=logging.INFO,
        ) 