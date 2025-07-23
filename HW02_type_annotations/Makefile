.PHONY: typing test clean

# Проверка типов с помощью mypy
typing:
	docker run --rm -v $(PWD):/app -w /app python:3.11-slim bash -c "pip install mypy==1.16.1 && mypy basic/ intermediate/"

# Альтернативная проверка с pyright (если предпочитаете)
typing-pyright:
	docker run --rm -v $(PWD):/app -w /app node:18-slim bash -c "npm install -g pyright && pyright basic/ intermediate/"

# Запуск тестов (если будут добавлены)
test:
	python -m pytest tests/ -v

# Очистка временных файлов
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 