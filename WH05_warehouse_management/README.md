# Система управления складом (Warehouse Management)

Проект реализует DDD (Domain-Driven Design) и Clean Architecture для системы управления складом товаров и заказов.

## Архитектура

Проект разделен на слои:
- **Domain** - бизнес-логика и модели
- **Infrastructure** - работа с базой данных и ORM
- **Tests** - тесты для проверки функциональности

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

### Основное приложение

```bash
python main.py
```

**Пример вывода:**
```
create product: Product(id=5, name='test1', quantity=1, price=100)
create product: Product(id=6, name='test2', quantity=5, price=200)
create order: Order(id=1, products=[Product(id=5, name='test1', quantity=1, price=100), Product(id=6, name='test2', quantity=5, price=200)])
Total products: 6
Total orders: 1
```

### Тесты

#### Запуск всех тестов
```bash
python -m pytest tests/ -v
```

#### Запуск тестов с покрытием кода
```bash
python -m pytest tests/ --cov=domain --cov=infrastructure --cov-report=term-missing
```

**Пример вывода:**
```
=========================================== test session starts ===========================================
collected 7 items

tests\test_domain\test_services.py ..                                                                [ 28%]
tests\test_infrastructure\test_unit_of_work.py .....                                                 [100%]

============================================= tests coverage ==============================================
Name                             Stmts   Miss  Cover   Missing
--------------------------------------------------------------
domain\services.py                  15      0   100%
infrastructure\unit_of_work.py      14      0   100%
domain\models.py                    14      1    93%   17
domain\repositories.py              23      6    74%   8, 12, 16, 21, 25, 29
domain\unit_of_work.py              14      4    71%   6, 10, 14, 18
--------------------------------------------------------------
TOTAL                              135     66    51%
============================================ 7 passed in 1.10s ============================================
```

## Основные компоненты

### Domain Layer
- **models.py** - модели Product и Order
- **services.py** - бизнес-логика WarehouseService
- **repositories.py** - абстрактные репозитории
- **unit_of_work.py** - абстрактный Unit of Work

### Infrastructure Layer
- **orm.py** - SQLAlchemy ORM модели
- **repositories.py** - реализации репозиториев для SQLAlchemy
- **unit_of_work.py** - реализация Unit of Work для SQLAlchemy
- **database.py** - конфигурация базы данных

### Тесты
- **test_services.py** - тесты бизнес-логики
- **test_unit_of_work.py** - тесты Unit of Work

## База данных

Проект использует SQLite базу данных (`warehouse.db`), которая создается автоматически при первом запуске.

## Паттерны

- **Repository Pattern** - для работы с данными
- **Unit of Work Pattern** - для управления транзакциями
- **Domain-Driven Design** - для организации бизнес-логики 