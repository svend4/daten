#!/bin/bash
# Test Runner Script для IOS System
# Запускает все тесты с различными конфигурациями

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   IOS SYSTEM - TEST RUNNER${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Функция для вывода секций
print_section() {
    echo ""
    echo -e "${YELLOW}>>> $1${NC}"
    echo ""
}

# Функция для вывода успеха
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Функция для вывода ошибки
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Проверка установки pytest
if ! command -v pytest &> /dev/null; then
    print_error "pytest не установлен!"
    echo "Установите: pip install -r requirements-test.txt"
    exit 1
fi

print_success "pytest установлен"

# Создание директории для отчетов
mkdir -p test-reports
mkdir -p htmlcov

# 1. UNIT TESTS
print_section "1. Запуск Unit Tests"
if pytest tests/test_backend_comprehensive.py -v -m unit --tb=short; then
    print_success "Unit tests пройдены"
else
    print_error "Unit tests провалились"
    exit 1
fi

# 2. INTEGRATION TESTS
print_section "2. Запуск Integration Tests"
if pytest tests/test_integration.py -v -m integration --tb=short; then
    print_success "Integration tests пройдены"
else
    print_error "Integration tests провалились"
    exit 1
fi

# 3. PERFORMANCE TESTS (опционально)
print_section "3. Запуск Performance Tests (опционально)"
if pytest tests/test_performance.py -v -m performance --tb=short || true; then
    print_success "Performance tests выполнены"
else
    print_error "Performance tests пропущены или провалились"
fi

# 4. CODE COVERAGE
print_section "4. Проверка Code Coverage"
if pytest --cov=ios_system --cov-report=html --cov-report=term-missing --cov-fail-under=90; then
    print_success "Code coverage >= 90%"
    echo ""
    echo "HTML отчет: htmlcov/index.html"
else
    print_error "Code coverage < 90%"
    exit 1
fi

# 5. LINT CHECKS (опционально)
print_section "5. Lint Checks (опционально)"
if command -v pylint &> /dev/null; then
    echo "Запуск pylint..."
    pylint ios_system --exit-zero || true
    print_success "Pylint выполнен"
else
    echo "pylint не установлен, пропускаем"
fi

if command -v flake8 &> /dev/null; then
    echo "Запуск flake8..."
    flake8 ios_system --exit-zero || true
    print_success "Flake8 выполнен"
else
    echo "flake8 не установлен, пропускаем"
fi

# 6. SECURITY CHECKS (опционально)
print_section "6. Security Checks (опционально)"
if command -v bandit &> /dev/null; then
    echo "Запуск bandit..."
    bandit -r ios_system -ll -i -x tests || true
    print_success "Bandit выполнен"
else
    echo "bandit не установлен, пропускаем"
fi

# SUMMARY
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}   ✓ ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Отчеты:"
echo "  • Coverage: htmlcov/index.html"
echo "  • Test reports: test-reports/"
echo ""
echo -e "${YELLOW}Совет: Откройте htmlcov/index.html для просмотра покрытия кода${NC}"
echo ""
