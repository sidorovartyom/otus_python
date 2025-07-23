#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from log_analyzer.analyzer import LogAnalyzer
from log_analyzer.config import load_config, DEFAULT_CONFIG


@pytest.fixture
def sample_config():
    """Фикстура с тестовой конфигурацией."""
    return {
        "REPORT_SIZE": 100,
        "REPORT_DIR": "./test_reports",
        "LOG_DIR": "./test_logs",
        "LOG_FILE": None,
        "ERROR_THRESHOLD": 0.1
    }


@pytest.fixture
def analyzer(sample_config):
    """Фикстура с экземпляром LogAnalyzer."""
    return LogAnalyzer(sample_config)


def test_parse_log_line_valid(analyzer):
    """Тест парсинга валидной строки лога."""
    log_line = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2194394393-4708-9752759" "dc7161be3dad21d2b384473db6eb70d8" "-" 0.390'
    
    result = analyzer.parse_log_line(log_line)
    assert result is not None
    url, request_time = result
    assert url == '/api/v2/banner/25019354'
    assert request_time == 0.39


def test_parse_log_line_invalid(analyzer):
    """Тест парсинга невалидной строки лога."""
    invalid_lines = [
        'invalid log line',
        '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300]',
        '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927',
    ]
    
    for line in invalid_lines:
        result = analyzer.parse_log_line(line)
        assert result is None


def test_calculate_statistics(analyzer):
    """Тест вычисления статистики."""
    url_times = {
        '/api/v1/banners': [1.0, 2.0, 3.0],
        '/api/v2/banners': [0.5, 1.5],
        '/api/v3/banners': [2.0]
    }
    
    stats = analyzer.calculate_statistics(url_times)
    
    assert len(stats) == 3
    
    # Проверяем первую запись (с наибольшим time_sum)
    first_stat = stats[0]
    assert first_stat['url'] == '/api/v1/banners'
    assert first_stat['count'] == 3
    assert first_stat['time_sum'] == 6.0
    assert first_stat['time_avg'] == 2.0
    assert first_stat['time_max'] == 3.0
    assert first_stat['time_med'] == 2.0


def test_find_latest_log_no_files(analyzer, tmp_path):
    """Тест поиска логов в пустой директории."""
    result = analyzer.find_latest_log(str(tmp_path))
    assert result is None


def test_find_latest_log_with_files(analyzer, tmp_path):
    """Тест поиска последнего лог-файла."""
    # Создаем тестовые файлы
    (tmp_path / 'nginx-access-ui.log-20170629.gz').touch()
    (tmp_path / 'nginx-access-ui.log-20170630.gz').touch()
    (tmp_path / 'nginx-access-ui.log-20170701').touch()
    (tmp_path / 'other-file.txt').touch()
    
    result = analyzer.find_latest_log(str(tmp_path))
    assert result is not None
    
    file_path, date = result
    assert '20170701' in file_path  # Самый новый файл
    assert date.year == 2017
    assert date.month == 7
    assert date.day == 1


def test_load_config_valid(tmp_path):
    """Тест загрузки валидной конфигурации."""
    config_file = tmp_path / 'config.json'
    config_content = '{"REPORT_SIZE": 500, "LOG_DIR": "/custom/log"}'
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    config = load_config(str(config_file))
    assert config['REPORT_SIZE'] == 500
    assert config['LOG_DIR'] == '/custom/log'
    assert config['REPORT_DIR'] == './reports'  # дефолтное значение


def test_load_config_invalid_json(tmp_path):
    """Тест загрузки невалидной конфигурации."""
    config_file = tmp_path / 'config.json'
    config_content = '{"REPORT_SIZE": 500, "LOG_DIR": "/custom/log"'  # неполный JSON
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    with pytest.raises(Exception):
        load_config(str(config_file))


def test_load_config_file_not_found():
    """Тест загрузки несуществующего файла конфигурации."""
    with pytest.raises(FileNotFoundError):
        load_config('nonexistent.json')


def test_analyzer_initialization(sample_config):
    """Тест инициализации LogAnalyzer."""
    analyzer = LogAnalyzer(sample_config)
    assert analyzer.config == sample_config
    assert analyzer.logger is not None


if __name__ == '__main__':
    pytest.main([__file__]) 