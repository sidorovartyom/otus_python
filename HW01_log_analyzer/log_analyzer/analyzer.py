#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import json
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger()


class LogAnalyzer:
    """Анализатор логов nginx для создания отчетов о производительности."""
    
    def __init__(self, config: Dict):
        """
        Инициализация анализатора.
        
        Args:
            config: Конфигурация анализатора
        """
        self.config = config
        self.logger = structlog.get_logger()
    
    def find_latest_log(self, log_dir: str) -> Optional[Tuple[str, datetime]]:
        """Найти последний лог-файл в директории."""
        log_path = Path(log_dir)
        if not log_path.exists():
            self.logger.error("Директория логов не существует", log_dir=log_dir)
            return None
        
        # Паттерн для поиска лог-файлов
        pattern = r'nginx-access-ui\.log-(\d{8})(?:\.gz)?$'
        
        latest_file = None
        latest_date = None
        
        for file_path in log_path.iterdir():
            if file_path.is_file():
                match = re.match(pattern, file_path.name)
                if match:
                    try:
                        date_str = match.group(1)
                        file_date = datetime.strptime(date_str, '%Y%m%d')
                        
                        if latest_date is None or file_date > latest_date:
                            latest_date = file_date
                            latest_file = file_path
                    except ValueError:
                        self.logger.warning("Не удалось распарсить дату из имени файла", file=file_path.name)
        
        if latest_file:
            self.logger.info("Найден последний лог-файл", file=latest_file.name, date=latest_date)
            return str(latest_file), latest_date
        else:
            self.logger.info("Лог-файлы для обработки не найдены")
            return None
    
    def parse_log_line(self, line: str) -> Optional[Tuple[str, float]]:
        """Парсить одну строку лога и извлечь URL и время запроса."""
        try:
            # Разбиваем строку по пробелам
            parts = line.split()
            if len(parts) < 12:
                return None
            
            # Извлекаем request (часть в кавычках)
            request_part = ' '.join(parts[5:8])  # Объединяем части request
            if not (request_part.startswith('"') and request_part.endswith('"')):
                return None
            
            # Убираем кавычки и разбираем request
            request = request_part[1:-1]  # убираем кавычки
            request_parts = request.split()
            if len(request_parts) < 2:
                return None
            
            url = request_parts[1]
            
            # Извлекаем request_time (последнее поле)
            request_time = float(parts[-1])
            
            return url, request_time
        except (ValueError, IndexError):
            return None
    
    def parse_log_file(self, log_file_path: str) -> Tuple[Dict[str, List[float]], int, int]:
        """Парсить лог-файл и собрать статистику по URL'ам."""
        url_times = defaultdict(list)
        total_lines = 0
        parsed_lines = 0
        
        # Определяем, как открывать файл
        if log_file_path.endswith('.gz'):
            opener = gzip.open
            mode = 'rt'
        else:
            opener = open
            mode = 'r'
        
        try:
            with opener(log_file_path, mode, encoding='utf-8') as f:
                for line in f:
                    total_lines += 1
                    result = self.parse_log_line(line.strip())
                    if result:
                        url, request_time = result
                        url_times[url].append(request_time)
                        parsed_lines += 1
        except Exception as e:
            self.logger.error("Ошибка при чтении лог-файла", error=str(e), file=log_file_path)
            raise
        
        # Проверяем процент ошибок парсинга
        if total_lines > 0:
            error_rate = (total_lines - parsed_lines) / total_lines
            if error_rate > self.config["ERROR_THRESHOLD"]:
                self.logger.error("Превышен порог ошибок парсинга", 
                                error_rate=f"{error_rate:.2%}", 
                                threshold=f"{self.config['ERROR_THRESHOLD']:.2%}")
                raise ValueError(f"Слишком много ошибок парсинга: {error_rate:.2%}")
        
        self.logger.info("Лог-файл обработан", 
                        total_lines=total_lines, 
                        parsed_lines=parsed_lines, 
                        unique_urls=len(url_times))
        
        return dict(url_times), total_lines, parsed_lines
    
    def parse_log_generator(self, log_file_path: str):
        """Генератор для парсинга лог-файла."""
        # Определяем, как открывать файл
        if log_file_path.endswith('.gz'):
            opener = gzip.open
            mode = 'rt'
        else:
            opener = open
            mode = 'r'
        
        try:
            with opener(log_file_path, mode, encoding='utf-8') as f:
                for line in f:
                    result = self.parse_log_line(line.strip())
                    if result:
                        yield result
        except Exception as e:
            self.logger.error("Ошибка при чтении лог-файла", error=str(e), file=log_file_path)
            raise
    
    def calculate_statistics(self, url_times: Dict[str, List[float]]) -> List[Dict]:
        """Вычислить статистику по URL'ам."""
        total_requests = sum(len(times) for times in url_times.values())
        total_time = sum(sum(times) for times in url_times.values())
        
        stats = []
        for url, times in url_times.items():
            count = len(times)
            time_sum = sum(times)
            
            stat = {
                'url': url,
                'count': count,
                'count_perc': round(count / total_requests * 100, 3) if total_requests > 0 else 0,
                'time_sum': round(time_sum, 3),
                'time_perc': round(time_sum / total_time * 100, 3) if total_time > 0 else 0,
                'time_avg': round(time_sum / count, 3) if count > 0 else 0,
                'time_max': round(max(times), 3),
                'time_med': round(statistics.median(times), 3)
            }
            stats.append(stat)
        
        # Сортируем по time_sum (убывание)
        stats.sort(key=lambda x: x['time_sum'], reverse=True)
        
        # Ограничиваем размер отчета
        stats = stats[:self.config["REPORT_SIZE"]]
        
        return stats
    
    def render_report(self, stats: List[Dict], report_date: datetime) -> str:
        """Создать HTML-отчет."""
        # Читаем шаблон
        template_path = Path(__file__).parent / "report.html"
        if not template_path.exists():
            self.logger.error("Шаблон отчета не найден", template=template_path)
            raise FileNotFoundError("report.html не найден")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Создаем JSON для подстановки
        table_json = json.dumps(stats, ensure_ascii=False, indent=2)
        
        # Подставляем данные в шаблон
        template = Template(template_content)
        report_html = template.safe_substitute(table_json=table_json)
        
        return report_html
    
    def save_report(self, report_html: str, report_date: datetime) -> str:
        """Сохранить отчет в файл."""
        report_dir = Path(self.config["REPORT_DIR"])
        report_dir.mkdir(exist_ok=True)
        
        report_filename = f"report-{report_date.strftime('%Y.%m.%d')}.html"
        report_path = report_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        self.logger.info("Отчет сохранен", file=str(report_path))
        return str(report_path)
    
    def run(self) -> Optional[str]:
        """
        Запустить анализ логов.
        
        Returns:
            Путь к созданному отчету или None, если отчет не был создан
        """
        try:
            # Ищем последний лог-файл
            log_result = self.find_latest_log(self.config["LOG_DIR"])
            if not log_result:
                self.logger.info("Нет логов для обработки")
                return None
            
            log_file_path, log_date = log_result
            
            # Проверяем, не был ли уже создан отчет
            report_filename = f"report-{log_date.strftime('%Y.%m.%d')}.html"
            report_path = Path(self.config["REPORT_DIR"]) / report_filename
            if report_path.exists():
                self.logger.info("Отчет уже существует, пропускаем обработку", report=str(report_path))
                return str(report_path)
            
            # Парсим лог-файл
            url_times, total_lines, parsed_lines = self.parse_log_file(log_file_path)
            
            # Вычисляем статистику
            stats = self.calculate_statistics(url_times)
            
            # Создаем отчет
            report_html = self.render_report(stats, log_date)
            
            # Сохраняем отчет
            report_path = self.save_report(report_html, log_date)
            
            self.logger.info("Обработка завершена успешно", 
                           log_file=log_file_path, 
                           report_file=report_path,
                           stats_count=len(stats))
            
            return report_path
            
        except Exception as e:
            self.logger.error("Критическая ошибка", error=str(e), exc_info=True)
            raise 