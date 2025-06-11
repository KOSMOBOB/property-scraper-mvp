#!/bin/bash

# ==========================================
# PROPERTY SCRAPER MVP - АВТОМАТИЧЕСКАЯ УСТАНОВКА
# ==========================================

set -e  # Остановка при ошибке

echo "🚀 Property Scraper MVP - Установка начинается..."
echo "=================================================="

# Цвета для красивого вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для красивого вывода
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Проверка операционной системы
print_info "Проверка операционной системы..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_status "Linux обнаружен"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "macOS обнаружен"
else
    print_error "Неподдерживаемая ОС: $OSTYPE"
    exit 1
fi

# Проверка Docker
print_info "Проверка Docker..."
if ! command -v docker &> /dev/null; then
    print_warning "Docker не найден. Устанавливаем..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Установка Docker на Linux
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        print_status "Docker установлен"
    else
        print_error "Установите Docker Desktop для macOS: https://docs.docker.com/desktop/mac/install/"
        exit 1
    fi
else
    print_status "Docker найден: $(docker --version)"
fi

# Проверка Docker Compose
print_info "Проверка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose не найден. Устанавливаем..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        print_status "Docker Compose установлен"
    fi
else
    print_status "Docker Compose найден: $(docker-compose --version)"
fi

# Проверка файла .env
print_info "Проверка файла конфигурации..."
if [ ! -f .env ]; then
    print_warning "Файл .env не найден. Создаём из примера..."
    cp .env.example .env
    print_warning "ВАЖНО! Отредактируйте файл .env перед продолжением!"
    print_warning "Особенно: TELEGRAM_BOT_TOKEN и TELEGRAM_ADMIN_CHAT_ID"
    
    read -p "Нажмите Enter после редактирования .env файла..."
else
    print_status "Файл .env найден"
fi

# Проверка токена Telegram
if grep -q "123456789:ABCdefGhIJKlmNOPqrsTUVwxyz" .env; then
    print_error "ОШИБКА: Замените TELEGRAM_BOT_TOKEN в файле .env!"
    print_info "1. Найдите @BotFather в Telegram"
    print_info "2. Отправьте /newbot"
    print_info "3. Скопируйте токен в .env файл"
    exit 1
fi

# Проверка свободного места
print_info "Проверка свободного места..."
FREE_SPACE=$(df . | tail -1 | awk '{print $4}')
FREE_SPACE_GB=$((FREE_SPACE / 1048576))

if [ $FREE_SPACE_GB -lt 10 ]; then
    print_warning "Мало свободного места: ${FREE_SPACE_GB}GB. Рекомендуется минимум 10GB"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_status "Свободного места: ${FREE_SPACE_GB}GB"
fi

# Проверка RAM
print_info "Проверка доступной памяти..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    TOTAL_RAM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ $TOTAL_RAM -lt 6144 ]; then  # 6GB
        print_warning "Мало RAM: ${TOTAL_RAM}MB. Рекомендуется минимум 8GB"
        print_warning "AI модель может работать медленно"
    else
        print_status "RAM: ${TOTAL_RAM}MB"
    fi
fi

# Создание необходимых директорий
print_info "Создание директорий для данных..."
mkdir -p data/{postgres,redis,grafana,ollama,n8n,crawl4ai}
mkdir -p logs
print_status "Директории созданы"

# Установка прав доступа
print_info "Настройка прав доступа..."
chmod 755 data/
chmod -R 755 scripts/
print_status "Права настроены"

# Загрузка Docker образов
print_info "Загрузка Docker образов (это может занять 10-15 минут)..."
docker-compose pull
print_status "Docker образы загружены"

# Запуск сервисов
print_info "Запуск сервисов..."
docker-compose up -d

# Ожидание запуска
print_info "Ожидание запуска сервисов (60 секунд)..."
sleep 60

# Проверка запуска
print_info "Проверка статуса сервисов..."
if docker-compose ps | grep -q "Up"; then
    print_status "Сервисы запущены"
else
    print_error "Проблема с запуском сервисов"
    docker-compose logs
    exit 1
fi

# Загрузка AI модели
print_info "Загрузка AI модели (это может занять 5-10 минут)..."
docker-compose exec -d ollama ollama pull qwen2.5:7b
print_status "AI модель загружается в фоне"

# Получение IP адреса
if command -v curl &> /dev/null; then
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
else
    SERVER_IP="localhost"
fi

# Финальная информация
echo ""
echo "🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!"
echo "================================"
echo ""
print_status "Система запущена и готова к работе!"
echo ""
echo "📊 Доступные сервисы:"
echo "   • n8n:            http://${SERVER_IP}:5678 (admin/admin123)"
echo "   • Grafana:        http://${SERVER_IP}:3000 (admin/admin123)"
echo "   • Crawl4AI:       http://${SERVER_IP}:11235"
echo "   • Ollama AI:      http://${SERVER_IP}:11434"
echo ""
echo "🤖 Telegram Bot:"
echo "   • Найдите вашего бота в Telegram"
echo "   • Отправьте /start для проверки"
echo ""
echo "🔧 Управление системой:"
echo "   • Проверка здоровья:  ./scripts/health_check.sh"
echo "   • Просмотр логов:     docker-compose logs -f"
echo "   • Перезапуск:         docker-compose restart"
echo "   • Остановка:          docker-compose down"
echo ""
echo "📚 Документация: README.md"
echo ""
print_warning "Сохраните эту информацию! IP адрес: ${SERVER_IP}"
echo ""
