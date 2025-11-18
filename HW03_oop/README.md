# Scoring API

Декларативный язык описания и система валидации запросов к HTTP API сервиса скоринга.

## Описание

API реализует два метода:
- `online_score` - вычисление скора на основе персональных данных
- `clients_interests` - получение интересов клиентов

## Архитектура

### Поля валидации
Все поля наследуются от `object` и имеют метод `validate()`:
- `CharField` - строковые поля
- `EmailField` - email с проверкой символа @
- `PhoneField` - телефон (11 цифр, начинается с 7)
- `DateField` - дата в формате DD.MM.YYYY
- `BirthDayField` - дата рождения (не старше 70 лет)
- `GenderField` - пол (0, 1, 2)
- `ClientIDsField` - массив чисел
- `ArgumentsField` - словарь аргументов

### Метакласс
`RequestMeta` автоматически собирает все поля при создании класса запроса.

### Базовый класс
`Request` содержит общую логику валидации для всех запросов.

## Запуск

### Боевой режим
```bash
# Запуск сервера на порту 8080
python api.py

# Запуск с кастомным портом
python api.py -p 9000

# Запуск с логированием в файл
python api.py -l server.log
```

### Тестовый режим
```bash
# Запуск всех тестов
python test.py

# Запуск с подробным выводом
python -v test.py
```

## Примеры запросов

### online_score
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "account": "horns&hoofs",
    "login": "h&f",
    "method": "online_score",
    "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95",
    "arguments": {
      "phone": "79175002040",
      "email": "stupnikov@otus.ru",
      "first_name": "Стансилав",
      "last_name": "Ступников",
      "birthday": "01.01.1990",
      "gender": 1
    }
  }' \
  http://127.0.0.1:8080/method/
```

**Ответ:**
```json
{"code": 200, "response": {"score": 5.0}}
```

### clients_interests
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "account": "horns&hoofs",
    "login": "admin",
    "method": "clients_interests",
    "token": "d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f24091386050205c324687a0",
    "arguments": {
      "client_ids": [1,2,3,4],
      "date": "20.07.2017"
    }
  }' \
  http://127.0.0.1:8080/method/
```

**Ответ:**
```json
{"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4": ["cinema", "geek"]}}
```

## Аутентификация

Для обычных пользователей:
```
token = sha512(account + login + SALT)
```

Для админа:
```
token = sha512(YYYYMMDDHH + ADMIN_SALT)
```

## Валидация

### online_score
- Требуется хотя бы одна пара: phone-email, first_name-last_name, или gender-birthday
- Все поля валидируются по отдельности

### clients_interests
- client_ids обязателен и не может быть пустым
- date опциональна

## Логирование

Логи пишутся в формате:
```
[2024.01.15 14:30:25] I Starting server at 8080
[2024.01.15 14:30:30] I /method: {"account": "test"} request_id
```

## Структура файлов

- `api.py` - основной файл с API и валидацией
- `scoring.py` - функции для вычисления скора и интересов
- `test.py` - тесты функциональности
- `readme.md` - полное описание задания
- `readme_new.md` - эта документация 