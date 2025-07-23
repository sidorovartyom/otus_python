# HW02 Type Annotations

Этот проект содержит решения для тренажера по аннотации типов Python.

## Структура проекта

```
HW02_type_annotations/
├── basic/           # Решения базового уровня
├── intermediate/    # Решения среднего уровня
├── .github/         # GitHub Actions для CI
├── Makefile         # Команды для разработки
├── mypy.ini         # Конфигурация mypy
├── requirements.txt # Зависимости
└── README.md        # Описание задания
```

## Установка и настройка

### Требования
- Python 3.11+
- Docker (опционально, для контейнерной проверки)
- mypy 1.16.1

### Установка зависимостей
```bash
pip install -r requirements.txt
```

## Проверка типов

### Локальная проверка (рекомендуется)

#### Windows PowerShell:
```powershell
.\typing-local.ps1
```

#### Windows Command Prompt:
```cmd
typing-local.bat
```

#### Linux/macOS:
```bash
make typing
```

### Проверка в контейнере

#### С Docker:
```bash
make typing
```

#### С Docker Compose:
```bash
docker-compose up -d
docker-compose exec type-checker mypy basic/ intermediate/
```

## CI/CD

Проект настроен с GitHub Actions для автоматической проверки типов при каждом push и pull request.

Workflow файл: `.github/workflows/typing-check.yml`

## Конфигурация

### mypy.ini
Файл содержит строгие настройки для проверки типов:
- `disallow_untyped_defs = True` - требует аннотации для всех функций
- `warn_return_any = True` - предупреждает о возврате Any
- `strict_equality = True` - строгая проверка равенства

### Makefile
Содержит команды для:
- `make typing` - проверка типов с mypy
- `make typing-pyright` - проверка типов с pyright
- `make test` - запуск тестов
- `make clean` - очистка временных файлов

## Решения

### Basic уровень
- `any.py` - использование Any
- `dict.py` - типизация словарей
- `final.py` - использование Final
- `kwargs.py` - типизация kwargs
- `list.py` - типизация списков
- `optoinal.py` - использование Optional
- `parameter.py` - типизация параметров
- `return.py` - типизация возвращаемых значений
- `tuple.py` - типизация кортежей
- `typealias.py` - использование TypeAlias
- `union.py` - использование Union
- `variable.py` - типизация переменных

### Intermediate уровень
- `await.py` - типизация async функций
- `callable.py` - типизация callable объектов
- `class-var.py` - использование ClassVar
- `decorator.py` - типизация декораторов
- `empty-tuple.py` - пустые кортежи
- `generic.py` - использование дженериков
- `generic2.py` - продвинутые дженерики
- `generic3.py` - сложные дженерики
- `instance-var.py` - типизация атрибутов экземпляра
- `literal.py` - использование Literal
- `literalstring.py` - использование LiteralString
- `self.py` - типизация self
- `typed-dict.py` - использование TypedDict
- `typed-dict2.py` - продвинутые TypedDict
- `typed-dict3.py` - сложные TypedDict
- `unpack.py` - использование Unpack

## Разработка

### Добавление новых решений
1. Создайте новый файл в соответствующей папке
2. Добавьте аннотации типов
3. Запустите проверку типов: `.\typing-local.ps1`
4. Убедитесь, что все проверки проходят

### Отладка ошибок типов
1. Запустите проверку типов
2. Изучите сообщения об ошибках
3. Исправьте аннотации типов
4. Повторите проверку

## Полезные ссылки

- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Python Type Challenges](https://python-type-challenges.zeabur.app) 