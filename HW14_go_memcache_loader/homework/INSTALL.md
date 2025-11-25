# Инструкция по установке

## Установка Go

### Windows

1. Скачайте установщик с официального сайта: https://go.dev/dl/
2. Запустите MSI установщик
3. Проверьте установку:
   ```cmd
   go version
   ```

### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install golang-go

# Или скачайте последнюю версию вручную
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
```

### macOS

```bash
# Через Homebrew
brew install go

# Или скачайте PKG с https://go.dev/dl/
```

## Настройка окружения

Добавьте в `.bashrc` / `.zshrc` / `.profile`:

```bash
export GOPATH=$HOME/go
export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin
```

## Быстрый старт

```bash
# 1. Клонируйте проект
cd HW14_go_memcache_loader/homework

# 2. Установите зависимости
go mod download

# 3. Запустите тесты
go test ./internal/loader/... -v

# 4. Соберите проект
go build -o memc_load ./cmd/memc_load

# 5. Запустите в dry-run режиме
./memc_load -dry -pattern="*.tsv.gz"
```

## Использование Makefile

Если установлен `make`:

```bash
make deps    # Установить зависимости
make test    # Запустить тесты
make build   # Собрать бинарник
make run-dry # Запустить в dry режиме
```

## Troubleshooting

### Ошибка "go: command not found"

Go не установлен или не добавлен в PATH. Проверьте установку:
```bash
which go
go version
```

### Ошибка "cannot find package"

Запустите:
```bash
go mod download
go mod tidy
```

### Проблемы с protobuf

Если нужно перегенерировать protobuf код:

```bash
# Установите protoc compiler
# Windows: https://github.com/protocolbuffers/protobuf/releases
# Linux: sudo apt install protobuf-compiler
# macOS: brew install protobuf

# Установите Go плагин
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest

# Генерация
protoc --go_out=. --go_opt=paths=source_relative \
    internal/appsinstalled/appsinstalled.proto
```

## Версии

Проект тестировался с:
- Go 1.20+
- gomemcache v0.0.0-20230905024940
- google.golang.org/protobuf v1.35.2

## Дополнительные инструменты

### golangci-lint (опционально)

Для проверки качества кода:

```bash
# Установка
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Использование
golangci-lint run
```

### delve (отладчик)

```bash
go install github.com/go-delve/delve/cmd/dlv@latest
dlv debug ./cmd/memc_load
```
