#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import argparse
import os
import sys
import time
from datetime import datetime
import urllib.parse

# MIME типы согласно требованиям тест-сьюта
MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.swf': 'application/x-shockwave-flash'
}

class HTTPServer:
    def __init__(self, host='localhost', port=80, document_root='./www'):
        self.host = host
        self.port = port
        self.document_root = os.path.abspath(document_root)
        self.socket = None
        
        # Проверяем существование document_root
        if not os.path.exists(self.document_root):
            print(f"Error: DOCUMENT_ROOT '{self.document_root}' не существует")
            sys.exit(1)
            
    def start(self):
        """Запуск HTTP сервера"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            
            print(f"HTTP сервер запущен на {self.host}:{self.port}")
            print(f"DOCUMENT_ROOT: {self.document_root}")
            
            while True:
                client_socket, client_address = self.socket.accept()
                # Создаем новый поток для каждого клиента
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\nОстанавливаем сервер...")
        except Exception as e:
            print(f"Ошибка сервера: {e}")
        finally:
            if self.socket:
                self.socket.close()

    def handle_client(self, client_socket, client_address):
        """Обработка клиентского соединения"""
        try:
            # Читаем HTTP запрос
            request_data = client_socket.recv(4096).decode('utf-8')
            if not request_data:
                return
                
            # Парсим запрос
            method, path, headers = self.parse_request(request_data)
            
            # Обрабатываем запрос
            status, response_headers, body = self.process_request(method, path)
            
            # Отправляем ответ
            self.send_response(client_socket, status, response_headers, body)
            
        except Exception as e:
            # В случае ошибки отправляем 500
            self.send_error_response(client_socket, 500, "Internal Server Error")
        finally:
            client_socket.close()

    def parse_request(self, request_data):
        """Парсинг HTTP запроса"""
        lines = request_data.split('\r\n')
        if not lines:
            raise ValueError("Пустой запрос")
            
        # Парсим первую строку: METHOD /path HTTP/1.1
        request_line = lines[0].split()
        if len(request_line) != 3:
            raise ValueError("Неверный формат запроса")
            
        method = request_line[0].upper()
        path = request_line[1]
        
        # Парсим заголовки
        headers = {}
        for line in lines[1:]:
            if not line:
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
                
        return method, path, headers

    def process_request(self, method, path):
        """Обработка HTTP запроса согласно требованиям тест-сьюта"""
        
        # Декодируем URL (percent-encoding)
        try:
            path = urllib.parse.unquote(path)
        except:
            return 400, {}, "Bad Request"
            
        # Проверяем безопасность пути
        if not self.is_safe_path(path):
            return 403, {}, "Forbidden"
            
        # Обрабатываем разные HTTP методы
        if method in ['GET', 'HEAD']:
            return self.handle_get_head(method, path)
        else:
            # Все остальные методы → 405
            return self.handle_method_not_allowed()

    def handle_get_head(self, method, path):
        """Обработка GET и HEAD запросов"""
        # Убираем параметры запроса
        if '?' in path:
            path = path.split('?')[0]
            
        # Нормализуем путь
        if path.endswith('/'):
            path += 'index.html'
        elif path == '':
            path = '/index.html'
        elif not path.startswith('/'):
            path = '/' + path
            
        # Строим полный путь к файлу
        if path.startswith('/'):
            path = path[1:]  # убираем ведущий слеш
            
        full_path = os.path.join(self.document_root, path)
        full_path = os.path.abspath(full_path)
        
        # Проверяем, что путь находится внутри document_root
        if not full_path.startswith(self.document_root):
            return 403, {}, "Forbidden"
            
        # Проверяем существование файла
        if not os.path.exists(full_path):
            return 404, {}, "Not Found"
            
        # Проверяем, что это файл, а не директория
        if os.path.isdir(full_path):
            # Пытаемся найти index.html в директории
            index_path = os.path.join(full_path, 'index.html')
            if os.path.exists(index_path) and os.path.isfile(index_path):
                full_path = index_path
            else:
                return 404, {}, "Not Found"
                
        # Проверяем права на чтение
        if not os.access(full_path, os.R_OK):
            return 403, {}, "Forbidden"
            
        # Читаем файл
        try:
            with open(full_path, 'rb') as f:
                file_content = f.read()
        except:
            return 403, {}, "Forbidden"
            
        # Определяем MIME тип
        content_type = self.get_mime_type(full_path)
        
        # Формируем заголовки для успешного ответа
        response_headers = {
            'Content-Length': str(len(file_content)),
            'Content-Type': content_type
        }
        
        # Для HEAD запроса не отправляем тело
        body = file_content if method == 'GET' else b''
        
        return 200, response_headers, body

    def handle_method_not_allowed(self):
        """Обработка неподдерживаемых HTTP методов"""
        return 405, {}, "Method Not Allowed"

    def get_mime_type(self, file_path):
        """Определение MIME типа файла"""
        _, ext = os.path.splitext(file_path.lower())
        return MIME_TYPES.get(ext, 'application/octet-stream')

    def is_safe_path(self, path):
        """Проверка безопасности пути"""
        # Блокируем попытки выйти за пределы document_root
        # Но разрешаем .. внутри имен файлов (например, text..txt)
        if '../' in path or path.startswith('../') or path.endswith('/..'):
            return False
        return True

    def send_response(self, client_socket, status, response_headers, body):
        """Отправка HTTP ответа"""
        # Формируем статусную строку
        status_text = {
            200: 'OK',
            403: 'Forbidden', 
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error'
        }.get(status, 'Unknown')
        
        response = f"HTTP/1.1 {status} {status_text}\r\n"
        
        # Добавляем обязательные заголовки согласно тест-сьюту
        required_headers = {
            'Server': 'httpd/1.0',
            'Date': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'Connection': 'close'
        }
        
        # Объединяем обязательные и дополнительные заголовки
        all_headers = {**required_headers, **response_headers}
        
        # Добавляем заголовки к ответу
        for key, value in all_headers.items():
            response += f"{key}: {value}\r\n"
            
        response += "\r\n"
        
        # Отправляем заголовки
        client_socket.send(response.encode('utf-8'))
        
        # Отправляем тело ответа (если есть)
        if body:
            if isinstance(body, str):
                body = body.encode('utf-8')
            client_socket.send(body)

    def send_error_response(self, client_socket, status, message):
        """Отправка ошибки"""
        self.send_response(client_socket, status, {}, message)


def main():
    parser = argparse.ArgumentParser(description='HTTP Server')
    parser.add_argument('-r', '--document-root', 
                       default='./www',
                       help='DOCUMENT_ROOT путь (по умолчанию: ./www)')
    parser.add_argument('-p', '--port',
                       type=int, default=80,
                       help='Порт для прослушивания (по умолчанию: 80)')
    parser.add_argument('--host',
                       default='localhost', 
                       help='Хост для прослушивания (по умолчанию: localhost)')
    
    args = parser.parse_args()
    
    # Создаем и запускаем сервер
    server = HTTPServer(
        host=args.host,
        port=args.port, 
        document_root=args.document_root
    )
    
    try:
        server.start()
    except PermissionError:
        print(f"Ошибка: нет прав для привязки к порту {args.port}")
        print("Попробуйте запустить с правами администратора или используйте другой порт")
        sys.exit(1)


if __name__ == '__main__':
    main() 