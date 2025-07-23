#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys

from log_analyzer import LogAnalyzer
from log_analyzer.config import load_config, setup_logging, DEFAULT_CONFIG


def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(description='Анализатор логов nginx')
    parser.add_argument('--config', default='config.json', 
                       help='Путь к файлу конфигурации (по умолчанию: config.json)')
    args = parser.parse_args()
    
    try:
        # Загружаем конфигурацию
        try:
            current_config = load_config(args.config)
        except FileNotFoundError:
            print("Используется конфигурация по умолчанию")
            current_config = DEFAULT_CONFIG.copy()
        
        # Настраиваем логирование
        setup_logging(current_config)
        
        # Создаем анализатор и запускаем
        analyzer = LogAnalyzer(current_config)
        result = analyzer.run()
        
        if result:
            print(f"Отчет создан: {result}")
        else:
            print("Отчет не был создан")
            
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 