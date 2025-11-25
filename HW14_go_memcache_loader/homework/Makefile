.PHONY: build test clean run help

# Build binary
build:
	go build -o bin/memc_load ./cmd/memc_load

# Run tests
test:
	go test ./internal/loader/... -v

# Test with coverage
cover:
	go test ./internal/loader/... -coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html

# Download dependencies
deps:
	go mod download
	go mod tidy

# Clean build artifacts
clean:
	rm -rf bin/
	rm -f coverage.out coverage.html

# Run in dry mode
run-dry:
	go run ./cmd/memc_load -dry -pattern="*.tsv.gz"

# Format code
fmt:
	go fmt ./...

# Lint code (requires golangci-lint)
lint:
	golangci-lint run

# Build for multiple platforms
build-all:
	GOOS=linux GOARCH=amd64 go build -o bin/memc_load-linux-amd64 ./cmd/memc_load
	GOOS=darwin GOARCH=amd64 go build -o bin/memc_load-darwin-amd64 ./cmd/memc_load
	GOOS=windows GOARCH=amd64 go build -o bin/memc_load-windows-amd64.exe ./cmd/memc_load

help:
	@echo "Available targets:"
	@echo "  build      - Build the binary"
	@echo "  test       - Run tests"
	@echo "  cover      - Run tests with coverage"
	@echo "  deps       - Download dependencies"
	@echo "  clean      - Clean build artifacts"
	@echo "  run-dry    - Run in dry mode"
	@echo "  fmt        - Format code"
	@echo "  build-all  - Build for all platforms"
