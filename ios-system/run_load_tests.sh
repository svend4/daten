#!/bin/bash
# Load Testing Runner для IOS System
# Запускает различные сценарии нагрузочного тестирования

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   IOS SYSTEM - LOAD TESTING RUNNER${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Проверка установки Locust
if ! command -v locust &> /dev/null; then
    echo -e "${RED}❌ Locust не установлен!${NC}"
    echo "Установите: pip install locust"
    exit 1
fi

echo -e "${GREEN}✓ Locust установлен${NC}"

# Функция для вывода меню
show_menu() {
    echo ""
    echo -e "${YELLOW}Выберите сценарий тестирования:${NC}"
    echo ""
    echo "1) Light Load Test - 10 пользователей, 5 минут"
    echo "2) Normal Load Test - 50 пользователей, 10 минут"
    echo "3) Heavy Load Test - 100 пользователей, 10 минут"
    echo "4) Stress Test - 200 пользователей, 15 минут"
    echo "5) Spike Test - 500 пользователей, 5 минут"
    echo "6) Endurance Test - 50 пользователей, 1 час"
    echo "7) Custom - указать параметры вручную"
    echo "8) Web UI - запустить Locust Web Interface"
    echo "9) Exit"
    echo ""
}

# Функция запуска теста
run_test() {
    local users=$1
    local spawn_rate=$2
    local runtime=$3
    local test_name=$4
    
    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   Запуск: $test_name${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo -e "Пользователей: ${GREEN}$users${NC}"
    echo -e "Spawn rate: ${GREEN}$spawn_rate/sec${NC}"
    echo -e "Длительность: ${GREEN}$runtime${NC}"
    echo ""
    
    # Создаем директорию для отчетов
    mkdir -p load-test-reports
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    report_name="load-test-reports/${test_name}_${timestamp}"
    
    echo -e "${YELLOW}Запуск теста...${NC}"
    echo ""
    
    # Запускаем Locust в headless режиме
    locust -f tests/locustfile.py \
        --host=http://localhost:8000 \
        --users=$users \
        --spawn-rate=$spawn_rate \
        --run-time=$runtime \
        --headless \
        --html="${report_name}.html" \
        --csv="${report_name}" \
        --loglevel=INFO
    
    echo ""
    echo -e "${GREEN}✓ Тест завершен!${NC}"
    echo -e "Отчет: ${BLUE}${report_name}.html${NC}"
    echo ""
}

# Основной цикл
while true; do
    show_menu
    read -p "Выберите опцию [1-9]: " choice
    
    case $choice in
        1)
            run_test 10 2 "5m" "light_load"
            ;;
        2)
            run_test 50 5 "10m" "normal_load"
            ;;
        3)
            run_test 100 10 "10m" "heavy_load"
            ;;
        4)
            run_test 200 20 "15m" "stress_test"
            ;;
        5)
            run_test 500 50 "5m" "spike_test"
            ;;
        6)
            run_test 50 5 "1h" "endurance_test"
            ;;
        7)
            echo ""
            read -p "Количество пользователей: " custom_users
            read -p "Spawn rate (users/sec): " custom_spawn
            read -p "Длительность (напр. 10m, 1h): " custom_time
            run_test $custom_users $custom_spawn $custom_time "custom_test"
            ;;
        8)
            echo ""
            echo -e "${YELLOW}Запуск Locust Web UI...${NC}"
            echo -e "Откройте браузер: ${BLUE}http://localhost:8089${NC}"
            echo ""
            locust -f tests/locustfile.py --host=http://localhost:8000
            ;;
        9)
            echo ""
            echo -e "${GREEN}Выход...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Неверный выбор. Попробуйте снова.${NC}"
            ;;
    esac
    
    echo ""
    read -p "Нажмите Enter для продолжения..."
done
