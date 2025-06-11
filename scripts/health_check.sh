#!/bin/bash

# ==========================================
# HEALTH CHECK - ПРОВЕРКА ЗДОРОВЬЯ СИСТЕМЫ
# ==========================================

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔍 Property Scraper - Проверка здоровья системы"
echo "==============================================="
echo ""

# Функции для красивого вывода
check_ok() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Переменные для подсчёта статуса
total_checks=0
passed_checks=0

# Функция проверки HTTP сервиса
check_http_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    total_checks=$((total_checks + 1))
    echo -n "Проверка $name... "
    
    if response=$(curl -s -w "%{http_code}" -o /dev/null --connect-timeout 5 "$url" 2>/dev/null); then
        if [ "$response" -eq "$expected_code" ]; then
            check_ok "$name работает (HTTP $response)"
            passed_checks=$((passed_checks + 1))
            return 0
        else
            check_error "$name вернул HTTP $response"
            return 1
        fi
    else
        check_error "$name недоступен"
        return 1
    fi
}

# Функция проверки Docker контейнера
check_container() {
    local name=$1
    total_checks=$((total_checks + 1))
    echo -n "Проверка контейнера $name... "
    
    if docker-compose ps $name 2>/dev/null | grep -q "Up"; then
        check_ok "Контейнер $name запущен"
        passed_checks=$((passed_checks + 1))
        return 0
    else
        check_error "Контейнер $name остановлен или не найден"
        return 1
    fi
}

# 1. ПРОВЕРКА DOCKER КОНТЕЙНЕРОВ
echo "📦 Проверка Docker контейнеров:"
containers=("postgres" "redis" "crawl4ai" "ollama" "n8n" "grafana")

for container in "${containers[@]}"; do
    check_container $container
done

echo ""

# 2. ПРОВЕРКА HTTP СЕРВИСОВ
echo "🌐 Проверка HTTP сервисов:"

check_http_service "Crawl4AI" "http://localhost:11235/health"
check_http_service "Ollama" "http://localhost:11434/api/tags"
check_http_service "n8n" "http://localhost:5678"
check_http_service "Grafana" "http://localhost:3000"

echo ""

# 3. ПРОВЕРКА БАЗЫ ДАННЫХ
echo "🗄️ Проверка базы данных:"
total_checks=$((total_checks + 1))
if docker-compose exec -T postgres psql -U scraper -d property_scraper -c "SELECT 1;" > /dev/null 2>&1; then
    check_ok "PostgreSQL подключение работает"
    passed_checks=$((passed_checks + 1))
    
    # Проверка таблиц
    total_checks=$((total_checks + 1))
    if docker-compose exec -T postgres psql -U scraper -d property_scraper -c "\dt" 2>/dev/null | grep -q "properties"; then
        check_ok "Таблица properties существует"
        passed_checks=$((passed_checks + 1))
        
        # Количество записей
        count=$(docker-compose exec -T postgres psql -U scraper -d property_scraper -t -c "SELECT COUNT(*) FROM properties;" 2>/dev/null | tr -d ' \n' || echo "0")
        check_info "Объявлений в базе: $count"
    else
        check_warning "Таблица properties не найдена (база не инициализирована)"
    fi
else
    check_error "Не удалось подключиться к PostgreSQL"
fi

echo ""

# 4. ПРОВЕРКА REDIS
echo "💾 Проверка Redis:"
total_checks=$((total_checks + 1))
if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    check_ok "Redis работает"
    passed_checks=$((passed_checks + 1))
else
    check_error "Redis недоступен"
fi

echo ""

# 5. ПРОВЕРКА AI МОДЕЛИ
echo "🤖 Проверка AI модели:"
total_checks=$((total_checks + 1))
if docker-compose exec -T ollama ollama list 2>/dev/null | grep -q "qwen"; then
    check_ok "AI модель Qwen загружена"
    passed_checks=$((passed_checks + 1))
else
    check_warning "AI модель не найдена"
    check_info "Для загрузки выполните: docker-compose exec ollama ollama pull qwen2.5:7b"
fi

echo ""

# 6. ПРОВЕРКА РЕСУРСОВ
echo "💻 Проверка ресурсов системы:"

# Проверка места на диске
free_space_kb=$(df . | tail -1 | awk '{print $4}')
free_space_gb=$(echo "scale=1; $free_space_kb / 1048576" | bc -l 2>/dev/null || echo "N/A")
if [ "$free_space_gb" != "N/A" ] && (( $(echo "$free_space_gb < 2.0" | bc -l 2>/dev/null || echo 0) )); then
    check_warning "Мало свободного места: ${free_space_gb}GB"
else
    check_info "Свободного места: ${free_space_gb}GB"
fi

# Проверка использования RAM
if command -v free &> /dev/null; then
    used_ram_percent=$(free | awk 'NR==2{printf "%.1f", $3*100/$2 }' 2>/dev/null || echo "N/A")
    if [ "$used_ram_percent" != "N/A" ] && (( $(echo "$used_ram_percent > 90.0" | bc -l 2>/dev/null || echo 0) )); then
        check_warning "Высокое использование RAM: ${used_ram_percent}%"
    else
        check_info "Использование RAM: ${used_ram_percent}%"
    fi
fi

echo ""

# 7. ИТОГОВЫЙ СТАТУС
echo "📊 Итоговый статус:"
success_rate=$((passed_checks * 100 / total_checks))

if [ $success_rate -eq 100 ]; then
    check_ok "Все проверки пройдены ($passed_checks/$total_checks)"
    echo ""
    echo "🎉 Система работает отлично!"
    echo ""
    echo "📋 Быстрые ссылки:"
    echo "   • n8n:      http://$(curl -s ifconfig.me 2>/dev/null || echo localhost):5678"
    echo "   • Grafana:  http://$(curl -s ifconfig.me 2>/dev/null || echo localhost):3000"
    echo "   • Logs:     docker-compose logs -f"
    exit_code=0
elif [ $success_rate -gt 70 ]; then
    check_warning "Большинство проверок пройдено ($passed_checks/$total_checks)"
    echo ""
    echo "⚠️  Система работает с предупреждениями"
    exit_code=1
else
    check_error "Много проблем ($passed_checks/$total_checks проверок пройдено)"
    echo ""
    echo "❌ Система требует внимания"
    echo ""
    echo "🔧 Для устранения проблем:"
    echo "   • Перезапуск: docker-compose restart"
    echo "   • Логи:       docker-compose logs"
    echo "   • Полная переустановка: docker-compose down && docker-compose up -d"
    exit_code=2
fi

echo ""
exit $exit_code
