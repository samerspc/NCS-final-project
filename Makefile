.PHONY: help install lint format check test security clean

help:
	@echo "Доступные команды:"
	@echo "  make install     - Установить зависимости для разработки"
	@echo "  make lint        - Запустить все линтеры"
	@echo "  make format      - Автоматически исправить форматирование кода"
	@echo "  make check       - Проверить форматирование без изменений"
	@echo "  make security    - Проверить безопасность с помощью bandit"
	@echo "  make clean       - Очистить кэш и временные файлы"

install:
	pip install -r requirements-dev.txt

lint:
	@echo "=== Запуск Flake8 ==="
	flake8 .
	@echo "\n=== Запуск Pylint ==="
	pylint insecure/security/ insecure/insecure/ --load-plugins=pylint_django || true
	@echo "\n=== Запуск MyPy ==="
	mypy insecure/ --ignore-missing-imports || true

format:
	@echo "=== Форматирование кода с Black ==="
	black .
	@echo "\n=== Сортировка импортов с isort ==="
	isort .

check:
	@echo "=== Проверка форматирования Black ==="
	black --check --diff .
	@echo "\n=== Проверка сортировки импортов isort ==="
	isort --check-only --diff .
	@echo "\n=== Запуск всех линтеров ==="
	$(MAKE) lint

security:
	@echo "=== Проверка безопасности с Bandit ==="
	bandit -r insecure/security

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -f bandit-report.json

