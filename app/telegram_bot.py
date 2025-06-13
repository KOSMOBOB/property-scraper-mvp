# app/telegram_bot.py - Полнофункциональный многоязычный Telegram бот
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
from decimal import Decimal

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InputMediaPhoto
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
import httpx
from sqlalchemy import select, insert, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, UserSearch, Property, Notification, database
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# МНОГОЯЗЫЧНАЯ ПОДДЕРЖКА
# ========================================

TRANSLATIONS = {
    'en': {
        'welcome': "🏠 Welcome to Buenos Aires Property Bot!\n\nI'll help you find the perfect property in Argentina's capital.",
        'choose_language': "🌍 Please choose your language:",
        'main_menu': "📱 Main Menu",
        'search': "🔍 Search Properties",
        'my_searches': "📂 My Searches",
        'alerts': "🔔 Property Alerts",
        'settings': "⚙️ Settings",
        'help': "❓ Help",
        'back': "◀️ Back",
        'cancel': "❌ Cancel",
        'language_changed': "✅ Language changed to English",
        'choose_property_type': "🏠 What type of property are you looking for?",
        'apartment': "🏢 Apartment",
        'house': "🏡 House",
        'studio': "🏨 Studio",
        'commercial': "🏪 Commercial",
        'any_type': "🎯 Any Type",
        'choose_location': "📍 Choose location:",
        'palermo': "🌳 Palermo",
        'recoleta': "🏛️ Recoleta",
        'puerto_madero': "🌊 Puerto Madero",
        'belgrano': "🏙️ Belgrano",
        'san_telmo': "🎨 San Telmo",
        'villa_crespo': "🎭 Villa Crespo",
        'caballito': "🐎 Caballito",
        'any_location': "🗺️ Any Location",
        'enter_min_price': "💰 Enter minimum price (USD) or 0 for no limit:",
        'enter_max_price': "💰 Enter maximum price (USD) or 0 for no limit:",
        'invalid_price': "❌ Please enter a valid number",
        'searching': "🔍 Searching for properties...",
        'no_results': "😔 No properties found with your criteria",
        'found_properties': "🏠 Found {count} properties:",
        'view_property': "👁️ View",
        'contact': "📞 Contact",
        'save': "💾 Save",
        'price': "💰 Price",
        'area': "📐 Area",
        'rooms': "🛏️ Rooms",
        'bathrooms': "🚿 Baths",
        'features': "✨ Features",
        'description': "📝 Description",
        'share': "📤 Share",
        'report': "⚠️ Report",
        'listing_type': "📌 Type",
        'rent': "For Rent",
        'sale': "For Sale",
        'help_text': """
🤖 **Property Bot Help**

**Available Commands:**
• /start - Start the bot
• /search - Search properties
• /alerts - Manage property alerts
• /language - Change language
• /help - Show this help

**Features:**
🔍 **Search** - Filter by type, location, and price
🔔 **Alerts** - Get notified about new properties
📂 **Saved Searches** - Quick access to your searches
📊 **Analytics** - Market insights powered by AI

**Support:** @PropertyBotSupport
        """,
        'save_search_prompt': "💾 Do you want to save this search for notifications?",
        'save_search': "💾 Save Search",
        'search_saved': "✅ Search saved! You'll receive notifications about new properties.",
        'enter_search_name': "📝 Enter a name for this search (e.g., '2BR Apartment in Palermo'):",
        'alert_frequency': "⏰ How often do you want to receive notifications?",
        'immediately': "🚀 Immediately",
        'daily': "📅 Daily Summary",
        'weekly': "📆 Weekly Summary",
        'manage_alerts': "🔔 Your Property Alerts",
        'no_alerts': "You don't have any active alerts yet.",
        'alert_enabled': "✅ Enabled",
        'alert_disabled': "❌ Disabled",
        'delete_alert': "🗑️ Delete",
        'toggle_alert': "🔄 Toggle",
        'alert_deleted': "✅ Alert deleted",
        'alert_toggled': "✅ Alert status changed",
        'new_property_alert': "🆕 New property matching your search '{search_name}'!",
        'view_all': "👀 View All",
        'property_from': "From",
        'posted': "Posted",
        'updated': "Updated",
        'error_occurred': "❌ An error occurred. Please try again.",
        'choose_bedrooms': "🛏️ How many bedrooms?",
        'studio_1': "Studio/1",
        'or_more': '+ or more',
        'search_summary': "📋 Search Summary:\n• Type: {type}\n• Location: {location}\n• Price: {price}\n• Bedrooms: {bedrooms}",
        'loading': "⏳ Loading...",
        'my_searches_list': "📂 Your Saved Searches:",
        'run_search': "🔍 Run",
        'no_saved_searches': "You don't have any saved searches yet.",
        'notifications_on': "🔔 Notifications ON",
        'notifications_off': "🔕 Notifications OFF"
    },
    'es': {
        'welcome': "🏠 ¡Bienvenido al Bot de Propiedades de Buenos Aires!\n\nTe ayudaré a encontrar la propiedad perfecta en la capital argentina.",
        'choose_language': "🌍 Por favor, elige tu idioma:",
        'main_menu': "📱 Menú Principal",
        'search': "🔍 Buscar Propiedades",
        'my_searches': "📂 Mis Búsquedas",
        'alerts': "🔔 Alertas de Propiedades",
        'settings': "⚙️ Configuración",
        'help': "❓ Ayuda",
        'back': "◀️ Atrás",
        'cancel': "❌ Cancelar",
        'language_changed': "✅ Idioma cambiado a Español",
        'choose_property_type': "🏠 ¿Qué tipo de propiedad buscas?",
        'apartment': "🏢 Departamento",
        'house': "🏡 Casa",
        'studio': "🏨 Monoambiente",
        'commercial': "🏪 Local Comercial",
        'any_type': "🎯 Cualquier Tipo",
        'choose_location': "📍 Elige la ubicación:",
        'palermo': "🌳 Palermo",
        'recoleta': "🏛️ Recoleta",
        'puerto_madero': "🌊 Puerto Madero",
        'belgrano': "🏙️ Belgrano",
        'san_telmo': "🎨 San Telmo",
        'villa_crespo': "🎭 Villa Crespo",
        'caballito': "🐎 Caballito",
        'any_location': "🗺️ Cualquier Zona",
        'enter_min_price': "💰 Ingresa el precio mínimo (USD) o 0 sin límite:",
        'enter_max_price': "💰 Ingresa el precio máximo (USD) o 0 sin límite:",
        'invalid_price': "❌ Por favor, ingresa un número válido",
        'searching': "🔍 Buscando propiedades...",
        'no_results': "😔 No se encontraron propiedades con tus criterios",
        'found_properties': "🏠 Se encontraron {count} propiedades:",
        'view_property': "👁️ Ver",
        'contact': "📞 Contactar",
        'save': "💾 Guardar",
        'price': "💰 Precio",
        'area': "📐 Área",
        'rooms': "🛏️ Ambientes",
        'bathrooms': "🚿 Baños",
        'features': "✨ Características",
        'description': "📝 Descripción",
        'share': "📤 Compartir",
        'report': "⚠️ Reportar",
        'listing_type': "📌 Tipo",
        'rent': "Alquiler",
        'sale': "Venta",
        'help_text': """
🤖 **Ayuda del Bot de Propiedades**

**Comandos Disponibles:**
• /start - Iniciar el bot
• /search - Buscar propiedades
• /alerts - Gestionar alertas
• /language - Cambiar idioma
• /help - Mostrar esta ayuda

**Funciones:**
🔍 **Buscar** - Filtra por tipo, ubicación y precio
🔔 **Alertas** - Notificaciones de nuevas propiedades
📂 **Búsquedas Guardadas** - Acceso rápido a tus búsquedas
📊 **Análisis** - Información del mercado con IA

**Soporte:** @PropertyBotSupport
        """,
        'save_search_prompt': "💾 ¿Quieres guardar esta búsqueda para recibir notificaciones?",
        'save_search': "💾 Guardar Búsqueda",
        'search_saved': "✅ ¡Búsqueda guardada! Recibirás notificaciones sobre nuevas propiedades.",
        'enter_search_name': "📝 Ingresa un nombre para esta búsqueda (ej: 'Depto 2 amb en Palermo'):",
        'alert_frequency': "⏰ ¿Con qué frecuencia quieres recibir notificaciones?",
        'immediately': "🚀 Inmediatamente",
        'daily': "📅 Resumen Diario",
        'weekly': "📆 Resumen Semanal",
        'manage_alerts': "🔔 Tus Alertas de Propiedades",
        'no_alerts': "No tienes alertas activas todavía.",
        'alert_enabled': "✅ Activada",
        'alert_disabled': "❌ Desactivada",
        'delete_alert': "🗑️ Eliminar",
        'toggle_alert': "🔄 Cambiar",
        'alert_deleted': "✅ Alerta eliminada",
        'alert_toggled': "✅ Estado de alerta cambiado",
        'new_property_alert': "🆕 ¡Nueva propiedad que coincide con tu búsqueda '{search_name}'!",
        'view_all': "👀 Ver Todas",
        'property_from': "De",
        'posted': "Publicado",
        'updated': "Actualizado",
        'error_occurred': "❌ Ocurrió un error. Por favor, intenta de nuevo.",
        'choose_bedrooms': "🛏️ ¿Cuántos dormitorios?",
        'studio_1': "Monoamb/1",
        'or_more': '+ o más',
        'search_summary': "📋 Resumen de búsqueda:\n• Tipo: {type}\n• Ubicación: {location}\n• Precio: {price}\n• Dormitorios: {bedrooms}",
        'loading': "⏳ Cargando...",
        'my_searches_list': "📂 Tus Búsquedas Guardadas:",
        'run_search': "🔍 Ejecutar",
        'no_saved_searches': "No tienes búsquedas guardadas todavía.",
        'notifications_on': "🔔 Notificaciones ACTIVADAS",
        'notifications_off': "🔕 Notificaciones DESACTIVADAS"
    },
    'pt': {
        'welcome': "🏠 Bem-vindo ao Bot de Imóveis de Buenos Aires!\n\nVou ajudá-lo a encontrar o imóvel perfeito na capital argentina.",
        'choose_language': "🌍 Por favor, escolha seu idioma:",
        'main_menu': "📱 Menu Principal",
        'search': "🔍 Buscar Imóveis",
        'my_searches': "📂 Minhas Buscas",
        'alerts': "🔔 Alertas de Imóveis",
        'settings': "⚙️ Configurações",
        'help': "❓ Ajuda",
        'back': "◀️ Voltar",
        'cancel': "❌ Cancelar",
        'language_changed': "✅ Idioma alterado para Português",
        'choose_property_type': "🏠 Que tipo de imóvel você procura?",
        'apartment': "🏢 Apartamento",
        'house': "🏡 Casa",
        'studio': "🏨 Studio",
        'commercial': "🏪 Comercial",
        'any_type': "🎯 Qualquer Tipo",
        'choose_location': "📍 Escolha a localização:",
        'palermo': "🌳 Palermo",
        'recoleta': "🏛️ Recoleta",
        'puerto_madero': "🌊 Puerto Madero",
        'belgrano': "🏙️ Belgrano",
        'san_telmo': "🎨 San Telmo",
        'villa_crespo': "🎭 Villa Crespo",
        'caballito': "🐎 Caballito",
        'any_location': "🗺️ Qualquer Local",
        'enter_min_price': "💰 Digite o preço mínimo (USD) ou 0 sem limite:",
        'enter_max_price': "💰 Digite o preço máximo (USD) ou 0 sem limite:",
        'invalid_price': "❌ Por favor, digite um número válido",
        'searching': "🔍 Procurando imóveis...",
        'no_results': "😔 Nenhum imóvel encontrado com seus critérios",
        'found_properties': "🏠 Encontrados {count} imóveis:",
        'view_property': "👁️ Ver",
        'contact': "📞 Contato",
        'save': "💾 Salvar",
        'price': "💰 Preço",
        'area': "📐 Área",
        'rooms': "🛏️ Quartos",
        'bathrooms': "🚿 Banheiros",
        'features': "✨ Características",
        'description': "📝 Descrição",
        'share': "📤 Compartilhar",
        'report': "⚠️ Reportar",
        'listing_type': "📌 Tipo",
        'rent': "Aluguel",
        'sale': "Venda",
        'help_text': """
🤖 **Ajuda do Bot de Imóveis**

**Comandos Disponíveis:**
• /start - Iniciar o bot
• /search - Buscar imóveis
• /alerts - Gerenciar alertas
• /language - Mudar idioma
• /help - Mostrar esta ajuda

**Recursos:**
🔍 **Buscar** - Filtrar por tipo, localização e preço
🔔 **Alertas** - Notificações de novos imóveis
📂 **Buscas Salvas** - Acesso rápido às suas buscas
📊 **Análise** - Insights do mercado com IA

**Suporte:** @PropertyBotSupport
        """,
        'save_search_prompt': "💾 Quer salvar esta busca para receber notificações?",
        'save_search': "💾 Salvar Busca",
        'search_saved': "✅ Busca salva! Você receberá notificações sobre novos imóveis.",
        'enter_search_name': "📝 Digite um nome para esta busca (ex: 'Apto 2 quartos em Palermo'):",
        'alert_frequency': "⏰ Com que frequência você quer receber notificações?",
        'immediately': "🚀 Imediatamente",
        'daily': "📅 Resumo Diário",
        'weekly': "📆 Resumo Semanal",
        'manage_alerts': "🔔 Seus Alertas de Imóveis",
        'no_alerts': "Você não tem alertas ativos ainda.",
        'alert_enabled': "✅ Ativado",
        'alert_disabled': "❌ Desativado",
        'delete_alert': "🗑️ Excluir",
        'toggle_alert': "🔄 Alternar",
        'alert_deleted': "✅ Alerta excluído",
        'alert_toggled': "✅ Status do alerta alterado",
        'new_property_alert': "🆕 Novo imóvel correspondente à sua busca '{search_name}'!",
        'view_all': "👀 Ver Todos",
        'property_from': "De",
        'posted': "Publicado",
        'updated': "Atualizado",
        'error_occurred': "❌ Ocorreu um erro. Por favor, tente novamente.",
        'choose_bedrooms': "🛏️ Quantos quartos?",
        'studio_1': "Studio/1",
        'or_more': '+ ou mais',
        'search_summary': "📋 Resumo da busca:\n• Tipo: {type}\n• Local: {location}\n• Preço: {price}\n• Quartos: {bedrooms}",
        'loading': "⏳ Carregando...",
        'my_searches_list': "📂 Suas Buscas Salvas:",
        'run_search': "🔍 Executar",
        'no_saved_searches': "Você não tem buscas salvas ainda.",
        'notifications_on': "🔔 Notificações ATIVADAS",
        'notifications_off': "🔕 Notificações DESATIVADAS"
    },
    'ru': {
        'welcome': "🏠 Добро пожаловать в Бот Недвижимости Буэнос-Айреса!\n\nЯ помогу вам найти идеальную недвижимость в столице Аргентины.",
        'choose_language': "🌍 Пожалуйста, выберите язык:",
        'main_menu': "📱 Главное меню",
        'search': "🔍 Поиск недвижимости",
        'my_searches': "📂 Мои поиски",
        'alerts': "🔔 Уведомления",
        'settings': "⚙️ Настройки",
        'help': "❓ Помощь",
        'back': "◀️ Назад",
        'cancel': "❌ Отмена",
        'language_changed': "✅ Язык изменен на Русский",
        'choose_property_type': "🏠 Какой тип недвижимости вы ищете?",
        'apartment': "🏢 Квартира",
        'house': "🏡 Дом",
        'studio': "🏨 Студия",
        'commercial': "🏪 Коммерческая",
        'any_type': "🎯 Любой тип",
        'choose_location': "📍 Выберите район:",
        'palermo': "🌳 Палермо",
        'recoleta': "🏛️ Реколета",
        'puerto_madero': "🌊 Пуэрто Мадеро",
        'belgrano': "🏙️ Бельграно",
        'san_telmo': "🎨 Сан-Тельмо",
        'villa_crespo': "🎭 Вилья Креспо",
        'caballito': "🐎 Кабальито",
        'any_location': "🗺️ Любой район",
        'enter_min_price': "💰 Введите минимальную цену (USD) или 0 без ограничений:",
        'enter_max_price': "💰 Введите максимальную цену (USD) или 0 без ограничений:",
        'invalid_price': "❌ Пожалуйста, введите корректное число",
        'searching': "🔍 Ищем недвижимость...",
        'no_results': "😔 Не найдено объектов по вашим критериям",
        'found_properties': "🏠 Найдено {count} объектов:",
        'view_property': "👁️ Просмотр",
        'contact': "📞 Контакт",
        'save': "💾 Сохранить",
        'price': "💰 Цена",
        'area': "📐 Площадь",
        'rooms': "🛏️ Комнат",
        'bathrooms': "🚿 Ванных",
        'features': "✨ Особенности",
        'description': "📝 Описание",
        'share': "📤 Поделиться",
        'report': "⚠️ Пожаловаться",
        'listing_type': "📌 Тип",
        'rent': "Аренда",
        'sale': "Продажа",
        'help_text': """
🤖 **Помощь по боту недвижимости**

**Доступные команды:**
• /start - Запустить бота
• /search - Поиск недвижимости
• /alerts - Управление уведомлениями
• /language - Изменить язык
• /help - Показать эту справку

**Функции:**
🔍 **Поиск** - Фильтр по типу, району и цене
🔔 **Уведомления** - Оповещения о новых объектах
📂 **Сохраненные поиски** - Быстрый доступ к поискам
📊 **Аналитика** - Анализ рынка с помощью ИИ

**Поддержка:** @PropertyBotSupport
        """,
        'save_search_prompt': "💾 Хотите сохранить этот поиск для получения уведомлений?",
        'save_search': "💾 Сохранить поиск",
        'search_saved': "✅ Поиск сохранен! Вы будете получать уведомления о новых объектах.",
        'enter_search_name': "📝 Введите название для этого поиска (напр.: 'Квартира 2 комн. в Палермо'):",
        'alert_frequency': "⏰ Как часто вы хотите получать уведомления?",
        'immediately': "🚀 Немедленно",
        'daily': "📅 Ежедневная сводка",
        'weekly': "📆 Еженедельная сводка",
        'manage_alerts': "🔔 Ваши уведомления о недвижимости",
        'no_alerts': "У вас пока нет активных уведомлений.",
        'alert_enabled': "✅ Включено",
        'alert_disabled': "❌ Выключено",
        'delete_alert': "🗑️ Удалить",
        'toggle_alert': "🔄 Переключить",
        'alert_deleted': "✅ Уведомление удалено",
        'alert_toggled': "✅ Статус уведомления изменен",
        'new_property_alert': "🆕 Новый объект по вашему поиску '{search_name}'!",
        'view_all': "👀 Посмотреть все",
        'property_from': "От",
        'posted': "Опубликовано",
        'updated': "Обновлено",
        'error_occurred': "❌ Произошла ошибка. Попробуйте снова.",
        'choose_bedrooms': "🛏️ Сколько спален?",
        'studio_1': "Студия/1",
        'or_more': '+ или больше',
        'search_summary': "📋 Параметры поиска:\n• Тип: {type}\n• Район: {location}\n• Цена: {price}\n• Спален: {bedrooms}",
        'loading': "⏳ Загрузка...",
        'my_searches_list': "📂 Ваши сохраненные поиски:",
        'run_search': "🔍 Запустить",
        'no_saved_searches': "У вас пока нет сохраненных поисков.",
        'notifications_on': "🔔 Уведомления ВКЛЮЧЕНЫ",
        'notifications_off': "🔕 Уведомления ВЫКЛЮЧЕНЫ"
    }
}

# ========================================
# СОСТОЯНИЯ FSM
# ========================================

class SearchStates(StatesGroup):
    choosing_type = State()
    choosing_location = State()
    choosing_bedrooms = State()
    entering_min_price = State()
    entering_max_price = State()
    viewing_results = State()
    saving_search = State()
    naming_search = State()
    choosing_frequency = State()

class AlertStates(StatesGroup):
    managing_alerts = State()

# ========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================================

async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя из базы данных"""
    try:
        query = select(User.language_code).where(User.telegram_id == user_id)
        result = await database.fetch_one(query)
        return result['language_code'] if result else 'en'
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return 'en'

async def save_user_language(user_id: int, language: str):
    """Сохранить язык пользователя в базе данных"""
    try:
        # Проверяем, существует ли пользователь
        query = select(User.id).where(User.telegram_id == user_id)
        existing = await database.fetch_one(query)
        
        if existing:
            # Обновляем язык
            query = update(User).where(User.telegram_id == user_id).values(
                language_code=language,
                updated_at=datetime.utcnow()
            )
            await database.execute(query)
        else:
            # Создаем нового пользователя
            query = insert(User).values(
                telegram_id=user_id,
                language_code=language,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await database.execute(query)
    except Exception as e:
        logger.error(f"Error saving user language: {e}")

def t(key: str, lang: str, **kwargs) -> str:
    """Получить перевод с подстановкой параметров"""
    translation = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
    if kwargs:
        return translation.format(**kwargs)
    return translation

# ========================================
# API ФУНКЦИИ
# ========================================

async def fetch_properties(search_params: Dict[str, Any]) -> List[Dict]:
    """Получить объекты недвижимости от API"""
    try:
        async with httpx.AsyncClient() as client:
            # Подготавливаем параметры запроса
            params = {
                'limit': 10,
                'offset': 0,
                'site': None  # Все сайты
            }
            
            # Добавляем фильтры
            if search_params.get('property_type') and search_params['property_type'] != 'any':
                params['property_type'] = search_params['property_type']
            
            if search_params.get('location') and search_params['location'] != 'any':
                params['location'] = search_params['location'].replace('_', ' ').title()
            
            if search_params.get('min_price', 0) > 0:
                params['min_price'] = search_params['min_price']
            
            if search_params.get('max_price', 0) > 0:
                params['max_price'] = search_params['max_price']
            
            # Запрос к API
            response = await client.get(
                f"{settings.API_SERVER_URL}/properties",
                params=params,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('properties', [])
            else:
                logger.error(f"API error: {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"Error fetching properties: {e}")
        return []

async def save_search_to_db(user_id: int, search_criteria: Dict, name: str, frequency: str) -> bool:
    """Сохранить поиск в базу данных"""
    try:
        # Получаем ID пользователя
        user_query = select(User.id).where(User.telegram_id == user_id)
        user_result = await database.fetch_one(user_query)
        
        if not user_result:
            # Создаем пользователя если не существует
            user_insert = insert(User).values(
                telegram_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            user_result = await database.execute(user_insert)
            user_uuid = user_result
        else:
            user_uuid = user_result['id']
        
        # Сохраняем поиск
        search_insert = insert(UserSearch).values(
            user_id=user_uuid,
            name=name,
            search_criteria=search_criteria,
            notification_frequency=frequency,
            notifications_enabled=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await database.execute(search_insert)
        return True
        
    except Exception as e:
        logger.error(f"Error saving search: {e}")
        return False

async def get_user_searches(user_id: int) -> List[Dict]:
    """Получить сохраненные поиски пользователя"""
    try:
        query = """
        SELECT us.* 
        FROM user_searches us
        JOIN users u ON us.user_id = u.id
        WHERE u.telegram_id = :telegram_id AND us.is_active = true
        ORDER BY us.created_at DESC
        """
        results = await database.fetch_all(query, {'telegram_id': user_id})
        return [dict(r) for r in results]
    except Exception as e:
        logger.error(f"Error getting user searches: {e}")
        return []

async def toggle_search_notifications(search_id: str, enabled: bool) -> bool:
    """Включить/выключить уведомления для поиска"""
    try:
        query = update(UserSearch).where(UserSearch.id == search_id).values(
            notifications_enabled=enabled,
            updated_at=datetime.utcnow()
        )
        await database.execute(query)
        return True
    except Exception as e:
        logger.error(f"Error toggling notifications: {e}")
        return False

async def delete_search(search_id: str) -> bool:
    """Удалить сохраненный поиск"""
    try:
        query = update(UserSearch).where(UserSearch.id == search_id).values(
            is_active=False,
            updated_at=datetime.utcnow()
        )
        await database.execute(query)
        return True
    except Exception as e:
        logger.error(f"Error deleting search: {e}")
        return False

# ========================================
# КЛАВИАТУРЫ
# ========================================

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton(text="🇪🇸 Español", callback_data="lang_es")
        ],
        [
            InlineKeyboardButton(text="🇵🇹 Português", callback_data="lang_pt"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]
    ])
    return keyboard

def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Главное меню с кнопками"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t('search', lang)),
                KeyboardButton(text=t('my_searches', lang))
            ],
            [
                KeyboardButton(text=t('alerts', lang)),
                KeyboardButton(text=t('settings', lang))
            ],
            [KeyboardButton(text=t('help', lang))]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_property_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора типа недвижимости"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t('apartment', lang), callback_data="type_apartment"),
            InlineKeyboardButton(text=t('house', lang), callback_data="type_house")
        ],
        [
            InlineKeyboardButton(text=t('studio', lang), callback_data="type_studio"),
            InlineKeyboardButton(text=t('commercial', lang), callback_data="type_commercial")
        ],
        [InlineKeyboardButton(text=t('any_type', lang), callback_data="type_any")],
        [InlineKeyboardButton(text=t('cancel', lang), callback_data="cancel")]
    ])
    return keyboard

def get_location_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора района"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t('palermo', lang), callback_data="loc_palermo"),
            InlineKeyboardButton(text=t('recoleta', lang), callback_data="loc_recoleta")
        ],
        [
            InlineKeyboardButton(text=t('puerto_madero', lang), callback_data="loc_puerto_madero"),
            InlineKeyboardButton(text=t('belgrano', lang), callback_data="loc_belgrano")
        ],
        [
            InlineKeyboardButton(text=t('san_telmo', lang), callback_data="loc_san_telmo"),
            InlineKeyboardButton(text=t('villa_crespo', lang), callback_data="loc_villa_crespo")
        ],
        [
            InlineKeyboardButton(text=t('caballito', lang), callback_data="loc_caballito"),
            InlineKeyboardButton(text=t('any_location', lang), callback_data="loc_any")
        ],
        [InlineKeyboardButton(text=t('back', lang), callback_data="back")]
    ])
    return keyboard

def get_bedrooms_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора количества спален"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t('studio_1', lang), callback_data="bed_0"),
            InlineKeyboardButton(text="2", callback_data="bed_2"),
            InlineKeyboardButton(text="3", callback_data="bed_3")
        ],
        [
            InlineKeyboardButton(text="4", callback_data="bed_4"),
            InlineKeyboardButton(text="5+", callback_data="bed_5")
        ],
        [InlineKeyboardButton(text=t('any_type', lang), callback_data="bed_any")],
        [InlineKeyboardButton(text=t('back', lang), callback_data="back")]
    ])
    return keyboard

def get_cancel_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t('cancel', lang), callback_data="cancel")]
    ])
    return keyboard

def get_save_search_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура для сохранения поиска"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t('save_search', lang), callback_data="save_search_yes"),
            InlineKeyboardButton(text=t('cancel', lang), callback_data="save_search_no")
        ]
    ])
    return keyboard

def get_frequency_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора частоты уведомлений"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t('immediately', lang), callback_data="freq_immediate")],
        [InlineKeyboardButton(text=t('daily', lang), callback_data="freq_daily")],
        [InlineKeyboardButton(text=t('weekly', lang), callback_data="freq_weekly")]
    ])
    return keyboard

def get_property_card_keyboard(lang: str, property_id: str, url: str = None) -> InlineKeyboardMarkup:
    """Клавиатура для карточки объекта"""
    buttons = []
    
    if url:
        buttons.append([InlineKeyboardButton(text=t('view_property', lang), url=url)])
    
    buttons.append([
        InlineKeyboardButton(text=t('contact', lang), callback_data=f"contact_{property_id}"),
        InlineKeyboardButton(text=t('share', lang), callback_data=f"share_{property_id}")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_search_actions_keyboard(lang: str, search_id: str, enabled: bool) -> InlineKeyboardMarkup:
    """Клавиатура действий с сохраненным поиском"""
    toggle_text = t('notifications_off' if enabled else 'notifications_on', lang)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t('run_search', lang), callback_data=f"run_{search_id}"),
            InlineKeyboardButton(text=toggle_text, callback_data=f"toggle_{search_id}")
        ],
        [InlineKeyboardButton(text=t('delete_alert', lang), callback_data=f"delete_{search_id}")]
    ])
    return keyboard

# ========================================
# ИНИЦИАЛИЗАЦИЯ БОТА
# ========================================

# Создаем бота и диспетчер
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# ========================================
# ОБРАБОТЧИКИ КОМАНД
# ========================================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    # Сохраняем информацию о пользователе
    user_data = {
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name,
    }
    
    # Проверяем, есть ли уже язык у пользователя
    existing_lang = await get_user_language(message.from_user.id)
    
    if existing_lang != 'en':  # Если язык уже выбран
        user_data['language'] = existing_lang
        await state.update_data(**user_data)
        
        # Показываем главное меню
        await message.answer(
            t('welcome', existing_lang),
            reply_markup=get_main_menu_keyboard(existing_lang)
        )
    else:
        # Показываем выбор языка для новых пользователей
        await state.update_data(**user_data)
        await message.answer(
            "🌍 Please choose your language / Por favor elige tu idioma / Por favor escolha seu idioma / Пожалуйста, выберите язык:",
            reply_markup=get_language_keyboard()
        )

@router.message(Command("language"))
async def cmd_language(message: Message, state: FSMContext):
    """Изменить язык"""
    await message.answer(
        t('choose_language', 'en'),
        reply_markup=get_language_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Показать помощь"""
    lang = await get_user_language(message.from_user.id)
    await message.answer(t('help_text', lang), parse_mode=ParseMode.MARKDOWN)

@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    """Начать поиск"""
    lang = await get_user_language(message.from_user.id)
    await state.update_data(language=lang)
    
    await message.answer(
        t('choose_property_type', lang),
        reply_markup=get_property_type_keyboard(lang)
    )
    await state.set_state(SearchStates.choosing_type)

@router.message(Command("alerts"))
async def cmd_alerts(message: Message, state: FSMContext):
    """Управление уведомлениями"""
    lang = await get_user_language(message.from_user.id)
    await show_user_searches(message, lang)

# ========================================
# ОБРАБОТЧИКИ CALLBACK КНОПОК
# ========================================

@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора языка"""
    lang_code = callback.data.split("_")[1]
    await state.update_data(language=lang_code)
    
    # Сохраняем язык в базе данных
    await save_user_language(callback.from_user.id, lang_code)
    
    await callback.message.edit_text(t('language_changed', lang_code))
    
    # Показываем главное меню
    await callback.message.answer(
        t('welcome', lang_code),
        reply_markup=get_main_menu_keyboard(lang_code)
    )

@router.callback_query(F.data.startswith("type_"))
async def process_property_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа недвижимости"""
    property_type = callback.data.split("_")[1]
    await state.update_data(property_type=property_type)
    
    data = await state.get_data()
    lang = data.get('language', 'en')
    
    await callback.message.edit_text(
        t('choose_location', lang),
        reply_markup=get_location_keyboard(lang)
    )
    await state.set_state(SearchStates.choosing_location)

@router.callback_query(F.data.startswith("loc_"))
async def process_location(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора района"""
    location = callback.data.split("_")[1]
    await state.update_data(location=location)
    
    data = await state.get_data()
    lang = data.get('language', 'en')
    
    await callback.message.edit_text(
        t('choose_bedrooms', lang),
        reply_markup=get_bedrooms_keyboard(lang)
    )
    await state.set_state(SearchStates.choosing_bedrooms)

@router.callback_query(F.data.startswith("bed_"))
async def process_bedrooms(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора количества спален"""
    bedrooms = callback.data.split("_")[1]
    await state.update_data(bedrooms=bedrooms)
    
    data = await state.get_data()
    lang = data.get('language', 'en')
    
    await callback.message.edit_text(
        t('enter_min_price', lang),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(SearchStates.entering_min_price)

@router.callback_query(F.data == "cancel")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена текущей операции"""
    lang = await get_user_language(callback.from_user.id)
    
    await callback.message.edit_text(t('cancel', lang))
    await state.clear()
    
    await callback.message.answer(
        t('main_menu', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )

# ========================================
# ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ
# ========================================

@router.message(SearchStates.entering_min_price)
async def process_min_price(message: Message, state: FSMContext):
    """Обработка ввода минимальной цены"""
    data = await state.get_data()
    lang = data.get('language', 'en')
    
    try:
        min_price = float(message.text.replace(',', '').replace(', ''))
        await state.update_data(min_price=min_price)
        
        await message.answer(
            t('enter_max_price', lang),
            reply_markup=get_cancel_keyboard(lang)
        )
        await state.set_state(SearchStates.entering_max_price)
    except ValueError:
        await message.answer(t('invalid_price', lang))

@router.message(SearchStates.entering_max_price)
async def process_max_price(message: Message, state: FSMContext):
    """Обработка ввода максимальной цены и выполнение поиска"""
    data = await state.get_data()
    lang = data.get('language', 'en')
    
    try:
        max_price = float(message.text.replace(',', '').replace(', ''))
        await state.update_data(max_price=max_price)
        
        # Выполняем поиск
        await perform_search(message, state)
        
    except ValueError:
        await message.answer(t('invalid_price', lang))

async def perform_search(message: Message, state: FSMContext):
    """Выполнение поиска недвижимости"""
    data = await state.get_data()
    lang = data.get('language', 'en')
    
    # Показываем сообщение о поиске
    searching_msg = await message.answer(t('searching', lang))
    
    # Получаем объекты от API
    properties = await fetch_properties(data)
    
    # Удаляем сообщение о поиске
    await searching_msg.delete()
    
    if properties:
        # Показываем результаты
        results_text = t('found_properties', lang, count=len(properties)) + "\n\n"
        
        for i, prop in enumerate(properties[:5], 1):  # Показываем первые 5
            # Форматируем цену
            price = f"${prop.get('price', 0):,.0f}" if prop.get('price') else "N/A"
            
            # Определяем тип листинга
            listing_type = t(prop.get('listing_type', 'sale'), lang)
            
            # Формируем текст
            results_text += f"{i}. **{prop.get('title', 'Sin título')}**\n"
            results_text += f"{t('price', lang)}: {price} ({listing_type})\n"
            results_text += f"{t('location', lang)}: {prop.get('location', 'N/A')}\n"
            
            if prop.get('bedrooms'):
                results_text += f"{t('rooms', lang)}: {prop['bedrooms']} | "
            if prop.get('bathrooms'):
                results_text += f"{t('bathrooms', lang)}: {prop['bathrooms']} | "
            if prop.get('area'):
                results_text += f"{t('area', lang)}: {prop['area']}m²"
            
            results_text += "\n"
            
            # Источник и дата
            if prop.get('site'):
                results_text += f"{t('property_from', lang)}: {prop['site'].title()}\n"
            if prop.get('created_at'):
                results_text += f"{t('posted', lang)}: {prop['created_at'][:10]}\n"
            
            results_text += "\n➖➖➖➖➖➖➖➖➖➖\n\n"
        
        # Отправляем результаты
        await message.answer(results_text, parse_mode=ParseMode.MARKDOWN)
        
        # Показываем первый объект подробнее
        if properties:
            first_prop = properties[0]
            await show_property_details(message, first_prop, lang)
        
        # Спрашиваем о сохранении поиска
        await message.answer(
            t('save_search_prompt', lang),
            reply_markup=get_save_search_keyboard(lang)
        )
        await state.set_state(SearchStates.saving_search)
        
    else:
        # Нет результатов
        await message.answer(
            t('no_results', lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t('new_search', lang), callback_data="new_search")]
            ])
        )

async def show_property_details(message: Message, prop: Dict, lang: str):
    """Показать детали объекта"""
    # Форматируем детали
    details = f"🏠 **{prop.get('title', 'Sin título')}**\n\n"
    
    price = f"${prop.get('price', 0):,.0f}" if prop.get('price') else "N/A"
    listing_type = t(prop.get('listing_type', 'sale'), lang)
    
    details += f"{t('price', lang)}: **{price}** ({listing_type})\n"
    details += f"{t('location', lang)}: {prop.get('location', 'N/A')}\n"
    
    if prop.get('neighborhood'):
        details += f"🏘️ Barrio: {prop['neighborhood']}\n"
    
    if prop.get('bedrooms'):
        details += f"{t('rooms', lang)}: {prop['bedrooms']} | "
    if prop.get('bathrooms'):
        details += f"{t('bathrooms', lang)}: {prop['bathrooms']} | "
    if prop.get('area'):
        details += f"{t('area', lang)}: {prop['area']}m²\n"
    else:
        details += "\n"
    
    if prop.get('description'):
        details += f"\n{t('description', lang)}:\n{prop['description'][:300]}..."
    
    if prop.get('features'):
        details += f"\n\n{t('features', lang)}:\n"
        for feature in prop['features'][:5]:
            details += f"• {feature}\n"
    
    # Información del sitio
    details += f"\n📍 {t('property_from', lang)}: {prop.get('site', 'N/A').title()}\n"
    details += f"📅 {t('posted', lang)}: {prop.get('created_at', 'N/A')[:10]}\n"
    
    # Enviar con botones
    await message.answer(
        details,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_property_card_keyboard(lang, prop.get('id'), prop.get('url'))
    )

@router.callback_query(F.data == "save_search_yes")
async def save_search_yes(callback: CallbackQuery, state: FSMContext):
    """Guardar búsqueda"""
    data = await state.get_data()
    lang = data.get('language', 'en')
    
    await callback.message.edit_text(
        t('enter_search_name', lang),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(SearchStates.naming_search)

@router.callback_query(F.data == "save_search_no")
async def save_search_no(callback: CallbackQuery, state: FSMContext):
    """No guardar búsqueda"""
    lang = await get_user_language(callback.from_user.id)
    
    await callback.message.edit_text(t('main_menu', lang))
    await state.clear()
    
    await callback.message.answer(
        t('main_menu', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )

@router.message(SearchStates.naming_search)
async def process_search_name(message: Message, state: FSMContext):
    """Procesar nombre del search"""
    data = await state.get_data()
    lang = data.get('language', 'en')
    
    search_name = message.text.strip()
    await state.update_data(search_name=search_name)
    
    # Preguntar frecuencia
    await message.answer(
        t('alert_frequency', lang),
        reply_markup=get_frequency_keyboard(lang)
    )
    await state.set_state(SearchStates.choosing_frequency)

@router.callback_query(F.data.startswith("freq_"))
async def process_frequency(callback: CallbackQuery, state: FSMContext):
    """Procesar frecuencia de notificaciones"""
    frequency = callback.data.split("_")[1]
    data = await state.get_data()
    lang = data.get('language', 'en')
    
    # Preparar criterios de búsqueda
    search_criteria = {
        'property_type': data.get('property_type'),
        'location': data.get('location'),
        'bedrooms': data.get('bedrooms'),
        'min_price': data.get('min_price', 0),
        'max_price': data.get('max_price', 0)
    }
    
    # Guardar en base de datos
    success = await save_search_to_db(
        callback.from_user.id,
        search_criteria,
        data.get('search_name', 'Mi búsqueda'),
        frequency
    )
    
    if success:
        await callback.message.edit_text(t('search_saved', lang))
    else:
        await callback.message.edit_text(t('error_occurred', lang))
    
    await state.clear()
    
    # Volver al menú principal
    await callback.message.answer(
        t('main_menu', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )

# ========================================
# MANEJADORES DE BÚSQUEDAS GUARDADAS
# ========================================

async def show_user_searches(message: Message, lang: str):
    """Mostrar búsquedas guardadas del usuario"""
    searches = await get_user_searches(message.from_user.id)
    
    if not searches:
        await message.answer(
            t('no_saved_searches', lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
        return
    
    text = t('my_searches_list', lang) + "\n\n"
    
    for search in searches:
        text += f"📍 **{search['name']}**\n"
        criteria = search['search_criteria']
        
        # Mostrar criterios
        if criteria.get('property_type') and criteria['property_type'] != 'any':
            text += f"• {t('property_type', lang)}: {t(criteria['property_type'], lang)}\n"
        if criteria.get('location') and criteria['location'] != 'any':
            text += f"• {t('location', lang)}: {t(criteria['location'], lang)}\n"
        if criteria.get('bedrooms') and criteria['bedrooms'] != 'any':
            text += f"• {t('bedrooms', lang)}: {criteria['bedrooms']}\n"
        
        # Precio
        min_p = criteria.get('min_price', 0)
        max_p = criteria.get('max_price', 0)
        if min_p > 0 or max_p > 0:
            if min_p == 0:
                price_text = f"< ${max_p:,.0f}"
            elif max_p == 0:
                price_text = f"> ${min_p:,.0f}"
            else:
                price_text = f"${min_p:,.0f} - ${max_p:,.0f}"
            text += f"• {t('price', lang)}: {price_text}\n"
        
        # Estado de notificaciones
        if search['notifications_enabled']:
            text += f"• 🟢 {t('alert_enabled', lang)}\n"
        else:
            text += f"• 🔴 {t('alert_disabled', lang)}\n"
        
        text += "\n"
    
    # Mostrar con botones de acción
    if searches:
        first_search = searches[0]
        keyboard = get_search_actions_keyboard(
            lang, 
            str(first_search['id']), 
            first_search['notifications_enabled']
        )
        
        await message.answer(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

# ========================================
# MANEJADORES DEL MENÚ PRINCIPAL
# ========================================

@router.message(F.text)
async def handle_text_message(message: Message, state: FSMContext):
    """Manejar mensajes de texto del menú principal"""
    lang = await get_user_language(message.from_user.id)
    
    # Verificar texto en todos los idiomas
    for language, translations in TRANSLATIONS.items():
        if message.text == translations.get('search'):
            await cmd_search(message, state)
            return
        elif message.text == translations.get('my_searches'):
            await show_user_searches(message, lang)
            return
        elif message.text == translations.get('alerts'):
            await show_user_searches(message, lang)
            return
        elif message.text == translations.get('settings'):
            await message.answer(
                t('choose_language', lang),
                reply_markup=get_language_keyboard()
            )
            return
        elif message.text == translations.get('help'):
            await cmd_help(message)
            return

# ========================================
# SISTEMA DE NOTIFICACIONES (BACKGROUND TASK)
# ========================================

async def check_new_properties():
    """Verificar nuevas propiedades para todas las búsquedas activas"""
    while True:
        try:
            # Obtener todas las búsquedas activas con notificaciones inmediatas
            query = """
            SELECT us.*, u.telegram_id, u.language_code 
            FROM user_searches us
            JOIN users u ON us.user_id = u.id
            WHERE us.is_active = true 
            AND us.notifications_enabled = true
            AND us.notification_frequency = 'immediate'
            """
            searches = await database.fetch_all(query)
            
            for search in searches:
                try:
                    # Verificar nuevas propiedades
                    criteria = search['search_criteria']
                    properties = await fetch_properties(criteria)
                    
                    if properties:
                        # Verificar cuáles son nuevas (publicadas en las últimas 2 horas)
                        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
                        new_properties = [
                            p for p in properties 
                            if p.get('created_at') and 
                            datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')) > two_hours_ago
                        ]
                        
                        if new_properties:
                            # Enviar notificación
                            lang = search['language_code'] or 'es'
                            
                            for prop in new_properties[:3]:  # Máximo 3 por notificación
                                notification_text = t(
                                    'new_property_alert', 
                                    lang, 
                                    search_name=search['name']
                                )
                                notification_text += "\n\n"
                                
                                # Detalles de la propiedad
                                price = f"${prop.get('price', 0):,.0f}" if prop.get('price') else "N/A"
                                notification_text += f"🏠 **{prop.get('title', 'Sin título')}**\n"
                                notification_text += f"{t('price', lang)}: {price}\n"
                                notification_text += f"{t('location', lang)}: {prop.get('location', 'N/A')}\n"
                                
                                if prop.get('bedrooms'):
                                    notification_text += f"{t('rooms', lang)}: {prop['bedrooms']} | "
                                if prop.get('area'):
                                    notification_text += f"{t('area', lang)}: {prop['area']}m²\n"
                                
                                # Enviar notificación
                                try:
                                    await bot.send_message(
                                        search['telegram_id'],
                                        notification_text,
                                        parse_mode=ParseMode.MARKDOWN,
                                        reply_markup=get_property_card_keyboard(
                                            lang, 
                                            prop.get('id'), 
                                            prop.get('url')
                                        )
                                    )
                                    
                                    # Registrar notificación enviada
                                    await record_notification(
                                        search['user_id'],
                                        prop.get('id'),
                                        search['id'],
                                        'new_property'
                                    )
                                    
                                except Exception as e:
                                    logger.error(f"Error sending notification: {e}")
                
                except Exception as e:
                    logger.error(f"Error checking properties for search {search['id']}: {e}")
            
            # Esperar 5 minutos antes de la siguiente verificación
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Error in notification checker: {e}")
            await asyncio.sleep(60)  # Esperar 1 minuto en caso de error

async def send_daily_summary():
    """Enviar resumen diario de propiedades"""
    while True:
        try:
            # Esperar hasta las 9 AM
            now = datetime.now()
            next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            
            wait_seconds = (next_run - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Obtener búsquedas con notificaciones diarias
            query = """
            SELECT us.*, u.telegram_id, u.language_code 
            FROM user_searches us
            JOIN users u ON us.user_id = u.id
            WHERE us.is_active = true 
            AND us.notifications_enabled = true
            AND us.notification_frequency = 'daily'
            """
            searches = await database.fetch_all(query)
            
            for search in searches:
                try:
                    criteria = search['search_criteria']
                    properties = await fetch_properties(criteria)
                    
                    if properties:
                        # Filtrar propiedades de las últimas 24 horas
                        yesterday = datetime.utcnow() - timedelta(days=1)
                        recent_properties = [
                            p for p in properties 
                            if p.get('created_at') and 
                            datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')) > yesterday
                        ]
                        
                        if recent_properties:
                            lang = search['language_code'] or 'es'
                            
                            summary_text = f"📊 **Resumen diario - {search['name']}**\n\n"
                            summary_text += f"Nuevas propiedades en las últimas 24 horas: {len(recent_properties)}\n\n"
                            
                            for i, prop in enumerate(recent_properties[:10], 1):
                                price = f"${prop.get('price', 0):,.0f}" if prop.get('price') else "N/A"
                                summary_text += f"{i}. {prop.get('title', 'Sin título')[:50]}...\n"
                                summary_text += f"   💰 {price} | 📍 {prop.get('location', 'N/A')}\n\n"
                            
                            if len(recent_properties) > 10:
                                summary_text += f"... y {len(recent_properties) - 10} propiedades más\n"
                            
                            await bot.send_message(
                                search['telegram_id'],
                                summary_text,
                                parse_mode=ParseMode.MARKDOWN
                            )
                
                except Exception as e:
                    logger.error(f"Error sending daily summary: {e}")
            
        except Exception as e:
            logger.error(f"Error in daily summary: {e}")

async def record_notification(user_id: str, property_id: str, search_id: str, notification_type: str):
    """Registrar notificación enviada"""
    try:
        query = insert(Notification).values(
            user_id=user_id,
            property_id=property_id,
            search_id=search_id,
            title=f"Notificación de {notification_type}",
            message="Notificación enviada",
            notification_type=notification_type,
            status='sent',
            telegram_sent=True,
            sent_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        await database.execute(query)
    except Exception as e:
        logger.error(f"Error recording notification: {e}")

# ========================================
# CALLBACKS PARA GESTIÓN DE BÚSQUEDAS
# ========================================

@router.callback_query(F.data.startswith("run_"))
async def run_saved_search(callback: CallbackQuery, state: FSMContext):
    """Ejecutar búsqueda guardada"""
    search_id = callback.data.split("_")[1]
    lang = await get_user_language(callback.from_user.id)
    
    # Obtener la búsqueda
    query = "SELECT * FROM user_searches WHERE id = :id"
    search = await database.fetch_one(query, {'id': search_id})
    
    if search:
        # Actualizar estado con los criterios
        criteria = search['search_criteria']
        await state.update_data(**criteria, language=lang)
        
        # Ejecutar búsqueda
        await callback.message.edit_text(t('searching', lang))
        await perform_search(callback.message, state)
    else:
        await callback.answer(t('error_occurred', lang))

@router.callback_query(F.data.startswith("toggle_"))
async def toggle_search_notifications(callback: CallbackQuery):
    """Activar/desactivar notificaciones"""
    search_id = callback.data.split("_")[1]
    lang = await get_user_language(callback.from_user.id)
    
    # Obtener estado actual
    query = "SELECT notifications_enabled FROM user_searches WHERE id = :id"
    result = await database.fetch_one(query, {'id': search_id})
    
    if result:
        new_status = not result['notifications_enabled']
        success = await toggle_search_notifications(search_id, new_status)
        
        if success:
            await callback.answer(t('alert_toggled', lang))
            # Actualizar la vista
            await show_user_searches(callback.message, lang)
        else:
            await callback.answer(t('error_occurred', lang))
    else:
        await callback.answer(t('error_occurred', lang))

@router.callback_query(F.data.startswith("delete_"))
async def delete_saved_search(callback: CallbackQuery):
    """Eliminar búsqueda guardada"""
    search_id = callback.data.split("_")[1]
    lang = await get_user_language(callback.from_user.id)
    
    success = await delete_search(search_id)
    
    if success:
        await callback.answer(t('alert_deleted', lang))
        # Actualizar la vista
        await show_user_searches(callback.message, lang)
    else:
        await callback.answer(t('error_occurred', lang))

@router.callback_query(F.data.startswith("contact_"))
async def contact_property(callback: CallbackQuery):
    """Mostrar información de contacto"""
    property_id = callback.data.split("_")[1]
    lang = await get_user_language(callback.from_user.id)
    
    # Aquí podrías obtener información real de contacto de la BD
    contact_info = f"""
📞 **{t('contact', lang)}**

🏢 Inmobiliaria Premium BA
📱 WhatsApp: +54 11 4555-0123
📧 Email: info@premium-ba.com
🌐 Web: www.premium-ba.com

ID: #{property_id}
    """
    
    await callback.message.answer(contact_info, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("share_"))
async def share_property(callback: CallbackQuery):
    """Compartir propiedad"""
    property_id = callback.data.split("_")[1]
    lang = await get_user_language(callback.from_user.id)
    
    # Crear enlace de compartir
    share_text = f"🏠 ¡Mira esta propiedad que encontré!\n\nhttps://propertybot.com/property/{property_id}"
    
    await callback.answer(t('share', lang))
    await callback.message.answer(share_text)

# ========================================
# FUNCIONES DE INICIO Y PARADA
# ========================================

async def on_startup():
    """Acciones al iniciar el bot"""
    logger.info("Bot starting...")
    
    # Conectar a la base de datos
    await database.connect()
    logger.info("Connected to database")
    
    # Iniciar tareas en segundo plano
    asyncio.create_task(check_new_properties())
    asyncio.create_task(send_daily_summary())
    
    # Notificar al admin
    if hasattr(settings, 'TELEGRAM_ADMIN_CHAT_ID') and settings.TELEGRAM_ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                settings.TELEGRAM_ADMIN_CHAT_ID,
                "🚀 Bot de propiedades iniciado y conectado a la base de datos"
            )
        except Exception as e:
            logger.error(f"Error notifying admin: {e}")

async def on_shutdown():
    """Acciones al detener el bot"""
    logger.info("Bot shutting down...")
    
    # Desconectar de la base de datos
    await database.disconnect()
    logger.info("Disconnected from database")
    
    # Cerrar sesión del bot
    await bot.session.close()

# ========================================
# FUNCIÓN PRINCIPAL
# ========================================

async def main():
    """Función principal para ejecutar el bot"""
    # Incluir el router
    dp.include_router(router)
    
    # Registrar funciones de inicio/parada
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Iniciar el bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()"""
