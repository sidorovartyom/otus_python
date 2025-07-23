.PHONY: install test run clean help docker-build docker-run docker-stop docker-logs

# Переменные
PYTHON = python
PIP = pip
PYTEST = pytest
DOCKER = docker
DOCKER_COMPOSE = docker-compose

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	$(PIP) install -r requirements.txt

install-dev: ## Установить зависимости для разработки
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

test: ## Запустить тесты
	$(PYTEST) tests/ -v

test-coverage: ## Запустить тесты с покрытием
	$(PYTEST) tests/ --cov=log_analyzer --cov-report=html --cov-report=term

run: ## Запустить анализатор логов
	$(PYTHON) -m log_analyzer

run-config: ## Запустить с кастомной конфигурацией
	$(PYTHON) -m log_analyzer --config config.json

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .pytest_cache/

build: ## Собрать пакет
	$(PYTHON) setup.py sdist bdist_wheel

check: ## Проверить код
	$(PYTHON) -m flake8 log_analyzer/ tests/
	$(PYTHON) -m mypy log_analyzer/

all: install test run ## Установить, протестировать и запустить

# Docker команды
docker-build: ## Собрать Docker образ
	$(DOCKER_COMPOSE) build

docker-run: ## Запустить приложение в Docker
	$(DOCKER_COMPOSE) up -d log-analyzer

docker-run-cron: ## Запустить приложение в Docker с периодическим выполнением
	$(DOCKER_COMPOSE) up -d log-analyzer-cron

docker-stop: ## Остановить Docker контейнеры
	$(DOCKER_COMPOSE) down

docker-logs: ## Показать логи Docker контейнеров
	$(DOCKER_COMPOSE) logs -f

docker-shell: ## Запустить shell в Docker контейнере
	$(DOCKER_COMPOSE) run --rm log-analyzer /bin/bash

docker-test: ## Запустить тесты в Docker
	$(DOCKER_COMPOSE) run --rm log-analyzer python -m pytest tests/ -v

docker-clean: ## Очистить Docker образы и контейнеры
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans 