#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from scoring import get_score, get_interests

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class CharField(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if value is None:
            if self.required:
                raise ValueError("Field is required")
            if not self.nullable:
                raise ValueError("Field cannot be null")
            return True

        if not isinstance(value, str):
            raise ValueError("Field must be a string")
        return True


class ArgumentsField(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if value is None:
            if self.required:
                raise ValueError("Field is required")
            if not self.nullable:
                raise ValueError("Field cannot be null")
            return True

        if not isinstance(value, dict):
            raise ValueError("Field must be a dictionary")
        return True


class EmailField(CharField):
    def validate(self, value):
        super().validate(value)
        if value is not None and '@' not in value:
            raise ValueError("Email must contain @ symbol")
        return True


class PhoneField(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if value is None:
            if self.required:
                raise ValueError("Field is required")
            if not self.nullable:
                raise ValueError("Field cannot be null")
            return True

        if isinstance(value, int):
            value = str(value)
        if not isinstance(value, str):
            raise ValueError("Phone must be string or integer")
        if len(value) != 11:
            raise ValueError("Phone must be 11 digits long")
        if not value.startswith('7'):
            raise ValueError("Phone must start with 7")
        if not value.isdigit():
            raise ValueError("Phone must contain only digits")
        return True


class DateField(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if value is None:
            if self.required:
                raise ValueError("Field is required")
            if not self.nullable:
                raise ValueError("Field cannot be null")
            return True

        if not isinstance(value, str):
            raise ValueError("Date must be a string")
        try:
            datetime.datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Date must be in DD.MM.YYYY format")
        return True


class BirthDayField(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if value is None:
            if self.required:
                raise ValueError("Field is required")
            if not self.nullable:
                raise ValueError("Field cannot be null")
            return True

        if not isinstance(value, str):
            raise ValueError("Date must be a string")
        try:
            birth_date = datetime.datetime.strptime(value, "%d.%m.%Y")
            today = datetime.datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age > 70:
                raise ValueError("Age cannot be more than 70 years")
            return True
        except ValueError as e:
            if "Age cannot be more than 70 years" in str(e):
                raise e
            raise ValueError("Date must be in DD.MM.YYYY format")


class GenderField(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if value is None:
            if self.required:
                raise ValueError("Field is required")
            if not self.nullable:
                raise ValueError("Field cannot be null")
            return True

        if not isinstance(value, int):
            raise ValueError("Gender must be an integer")
        if value not in [0, 1, 2]:
            raise ValueError("Gender must be 0, 1 or 2")
        return True


class ClientIDsField(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if value is None:
            if self.required:
                raise ValueError("Field is required")
            if not self.nullable:
                raise ValueError("Field cannot be null")
            return True

        if not isinstance(value, list):
            raise ValueError("Client IDs must be a list")
        if not value:
            raise ValueError("Client IDs cannot be empty")
        if not all(isinstance(x, int) for x in value):
            raise ValueError("All client IDs must be integers")
        return True


class RequestMeta(type):
    def __new__(mcs, name, bases, namespace):
        fields = {}
        for key, value in namespace.items():
            if hasattr(value, 'validate'):
                fields[key] = value
        namespace['_fields'] = fields
        return super().__new__(mcs, name, bases, namespace)


class Request(object, metaclass=RequestMeta):
    def __init__(self, data):
        self.data = data
        self.errors = []
        self._validate()

    def _validate(self):
        for field_name, field in self._fields.items():
            try:
                value = self.data.get(field_name)
                field.validate(value)
                setattr(self, field_name, value)
            except ValueError as e:
                self.errors.append(f"{field_name}: {str(e)}")

    def is_valid(self):
        return len(self.errors) == 0


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def _validate(self):
        super()._validate()

        # Проверяем наличие хотя бы одной пары
        has_phone_email = bool(self.phone and self.email)
        has_name_pair = bool(self.first_name and self.last_name)
        has_gender_birthday = bool(self.gender is not None and self.birthday)

        if not (has_phone_email or has_name_pair or has_gender_birthday):
            self.errors.append(
                "At least one pair of phone-email, first_name-last_name, or gender-birthday must be provided")


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):
    response, code = None, None

    # Валидация основного запроса
    method_request = MethodRequest(request["body"])
    if not method_request.is_valid():
        return ", ".join(method_request.errors), INVALID_REQUEST

    # Проверка аутентификации
    if not check_auth(method_request):
        return "Forbidden", FORBIDDEN

    # Обработка методов
    if method_request.method == "online_score":
        return handle_online_score(method_request, ctx, store)
    elif method_request.method == "clients_interests":
        return handle_clients_interests(method_request, ctx, store)
    else:
        return "Method not found", NOT_FOUND


def handle_online_score(request, ctx, store):
    # Валидация аргументов
    score_request = OnlineScoreRequest(request.arguments)
    if not score_request.is_valid():
        return ", ".join(score_request.errors), INVALID_REQUEST

    # Заполнение контекста
    ctx["has"] = [field for field in score_request._fields.keys()
                  if getattr(score_request, field) is not None]

    # Проверка на админа
    if request.is_admin:
        return {"score": 42}, OK

    # Вычисление скора
    score = get_score(
        store,
        score_request.phone,
        score_request.email,
        score_request.birthday,
        score_request.gender,
        score_request.first_name,
        score_request.last_name
    )

    return {"score": score}, OK


def handle_clients_interests(request, ctx, store):
    # Валидация аргументов
    interests_request = ClientsInterestsRequest(request.arguments)
    if not interests_request.is_valid():
        return ", ".join(interests_request.errors), INVALID_REQUEST

    # Заполнение контекста
    ctx["nclients"] = len(interests_request.client_ids)

    # Получение интересов для каждого клиента
    result = {}
    for client_id in interests_request.client_ids:
        result[str(client_id)] = get_interests(store, client_id)

    return result, OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()