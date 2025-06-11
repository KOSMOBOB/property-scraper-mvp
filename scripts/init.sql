-- =========================================
-- PROPERTY SCRAPER MVP - DATABASE SCHEMA
-- =========================================
-- Создание базы данных для системы парсинга недвижимости

-- Включаем расширения PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Для поиска по тексту

-- =========================================
-- ОСНОВНЫЕ ТАБЛИЦЫ
-- =========================================

-- Таблица объявлений недвижимости
CREATE TABLE IF NOT EXISTS properties (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    -- Основная информация
    title VARCHAR(500) NOT NULL,
    description TEXT,
    price DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'ARS',
    price_usd DECIMAL(12, 2), -- Цена в долларах для сравнения
    
    -- Характеристики
    property_type VARCHAR(50) DEFAULT 'apartment', -- apartment, house, studio, etc.
    bedrooms INTEGER DEFAULT 0,
    bathrooms INTEGER DEFAULT 0,
    area DECIMAL(8, 2), -- площадь в м²
    
    -- Местоположение
    location VARCHAR(200),
    neighborhood VARCHAR(100),
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Источник
    site VARCHAR(50) NOT NULL,
    external_id VARCHAR(200), -- ID на сайте-источнике
    url VARCHAR(1000),
    
    -- Медиа
    images JSONB, -- массив URL изображений
    virtual_tour_url VARCHAR(500),
    
    -- Дополнительные характеристики
    features JSONB, -- гараж, терраса, лифт и т.д.
    amenities JSONB, -- удобства: бассейн, спортзал и т.д.
    
    -- Мета-информация
    listing_type VARCHAR(20) DEFAULT 'rent', -- rent, sale
    is_active BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    
    -- Временные метки
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Индексы для быстрого поиска
    search_vector tsvector
);

-- Таблица пользователей Telegram
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    language_code VARCHAR(10) DEFAULT 'es',
    
    -- Подписка
    subscription_type VARCHAR(20) DEFAULT 'free', -- free, basic, premium, pro
    subscription_expires_at TIMESTAMP,
    
    -- Настройки
    notifications_enabled BOOLEAN DEFAULT true,
    max_notifications_per_day INTEGER DEFAULT 10,
    preferred_neighborhoods JSONB,
    price_range JSONB, -- {min: 100000, max: 500000}
    
    -- Статистика
    searches_count INTEGER DEFAULT 0,
    notifications_sent INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Мета
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица поисковых запросов пользователей
CREATE TABLE IF NOT EXISTS user_searches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Критерии поиска
    search_criteria JSONB NOT NULL, -- фильтры поиска
    name VARCHAR(100), -- название поиска от пользователя
    
    -- Настройки уведомлений
    notifications_enabled BOOLEAN DEFAULT true,
    notification_frequency VARCHAR(20) DEFAULT 'immediate', -- immediate, daily, weekly
    last_notification_sent TIMESTAMP,
    
    -- Статистика
    results_count INTEGER DEFAULT 0,
    notifications_sent INTEGER DEFAULT 0,
    
    -- Мета
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица уведомлений
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    search_id UUID REFERENCES user_searches(id) ON DELETE SET NULL,
    
    -- Содержание уведомления
    title VARCHAR(200),
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'new_property', -- new_property, price_change, etc.
    
    -- Статус доставки
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed, read
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    error_message TEXT,
    
    -- Каналы доставки
    telegram_sent BOOLEAN DEFAULT false,
    email_sent BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица истории изменения цен
CREATE TABLE IF NOT EXISTS price_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    
    old_price DECIMAL(12, 2),
    new_price DECIMAL(12, 2),
    old_currency VARCHAR(3),
    new_currency VARCHAR(3),
    
    change_type VARCHAR(20), -- increase, decrease, currency_change
    change_percentage DECIMAL(5, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица статистики парсинга
CREATE TABLE IF NOT EXISTS scraping_stats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    site VARCHAR(50) NOT NULL,
    scraping_date DATE DEFAULT CURRENT_DATE,
    
    -- Статистика парсинга
    pages_scraped INTEGER DEFAULT 0,
    properties_found INTEGER DEFAULT 0,
    properties_new INTEGER DEFAULT 0,
    properties_updated INTEGER DEFAULT 0,
    properties_removed INTEGER DEFAULT 0,
    
    -- Производительность
    duration_seconds INTEGER,
    errors_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 2),
    
    -- Детали
    error_details JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =========================================

-- Основные индексы для properties
CREATE INDEX IF NOT EXISTS idx_properties_site ON properties(site);
CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price);
CREATE INDEX IF NOT EXISTS idx_properties_location ON properties(location);
CREATE INDEX IF NOT EXISTS idx_properties_neighborhood ON properties(neighborhood);
CREATE INDEX IF NOT EXISTS idx_properties_type ON properties(property_type);
CREATE INDEX IF NOT EXISTS idx_properties_active ON properties(is_active);
CREATE INDEX IF NOT EXISTS idx_properties_created_at ON properties(created_at);
CREATE INDEX IF NOT EXISTS idx_properties_url ON properties(url);
CREATE INDEX IF NOT EXISTS idx_properties_external_id ON properties(external_id);

-- Составные индексы для сложных запросов
CREATE INDEX IF NOT EXISTS idx_properties_search ON properties(price, bedrooms, neighborhood, property_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_properties_location_price ON properties(location, price) WHERE is_active = true;

-- Индексы для полнотекстового поиска
CREATE INDEX IF NOT EXISTS idx_properties_search_vector ON properties USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_properties_title_gin ON properties USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_properties_description_gin ON properties USING gin(description gin_trgm_ops);

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_type, subscription_expires_at);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Индексы для notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_status ON notifications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_property ON notifications(property_id);

-- =========================================
-- ТРИГГЕРЫ
-- =========================================

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Применяем триггер к таблицам
CREATE TRIGGER update_properties_updated_at 
    BEFORE UPDATE ON properties 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_searches_updated_at 
    BEFORE UPDATE ON user_searches 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Триггер для обновления search_vector
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('spanish', 
        COALESCE(NEW.title, '') || ' ' ||
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.location, '') || ' ' ||
        COALESCE(NEW.neighborhood, '')
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_properties_search_vector 
    BEFORE INSERT OR UPDATE ON properties 
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- =========================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- =========================================

-- Создаём админского пользователя
INSERT INTO users (telegram_id, username, first_name, is_admin, subscription_type) 
VALUES (123456789, 'admin', 'Admin', true, 'pro') 
ON CONFLICT (telegram_id) DO NOTHING;

-- Тестовые данные (можно удалить в продакшене)
INSERT INTO properties (
    title, price, currency, property_type, bedrooms, bathrooms, area,
    location, neighborhood, site, url, listing_type, is_active
) VALUES 
(
    'Departamento 2 ambientes en Palermo',
    450000, 'ARS', 'apartment', 1, 1, 45.5,
    'Palermo, CABA', 'Palermo', 'zonaprop',
    'https://www.zonaprop.com.ar/ejemplo1', 'rent', true
),
(
    'Casa 3 dormitorios en Recoleta',
    850000, 'ARS', 'house', 3, 2, 120.0,
    'Recoleta, CABA', 'Recoleta', 'argenprop',
    'https://www.argenprop.com/ejemplo2', 'sale', true
)
ON CONFLICT DO NOTHING;

-- =========================================
-- ПОЛЕЗНЫЕ ФУНКЦИИ
-- =========================================

-- Функция для конвертации валют (упрощённая)
CREATE OR REPLACE FUNCTION convert_to_usd(amount DECIMAL, currency VARCHAR)
RETURNS DECIMAL AS $$
BEGIN
    CASE currency
        WHEN 'USD' THEN RETURN amount;
        WHEN 'ARS' THEN RETURN amount / 1000; -- Примерный курс, нужно обновлять
        ELSE RETURN NULL;
    END CASE;
END;
$$ language 'plpgsql';

-- Функция для поиска дубликатов
CREATE OR REPLACE FUNCTION find_duplicate_properties(
    p_title VARCHAR,
    p_site VARCHAR,
    p_price DECIMAL,
    p_location VARCHAR
)
RETURNS UUID AS $$
DECLARE
    result_id UUID;
BEGIN
    SELECT id INTO result_id
    FROM properties
    WHERE site = p_site
    AND (
        url = p_title OR
        (title = p_title AND ABS(price - p_price) < 1000) OR
        (similarity(title, p_title) > 0.8 AND location = p_location)
    )
    AND is_active = true
    LIMIT 1;
    
    RETURN result_id;
END;
$$ language 'plpgsql';

-- =========================================
-- ПРЕДСТАВЛЕНИЯ (VIEWS)
-- =========================================

-- Представление активных объявлений с дополнительной информацией
CREATE OR REPLACE VIEW active_properties AS
SELECT 
    p.*,
    convert_to_usd(p.price, p.currency) as price_usd_calculated,
    EXTRACT(days FROM (CURRENT_TIMESTAMP - p.created_at)) as days_since_created,
    CASE 
        WHEN p.price < 200000 THEN 'budget'
        WHEN p.price < 500000 THEN 'mid_range'
        WHEN p.price < 1000000 THEN 'premium'
        ELSE 'luxury'
    END as price_category
FROM properties p
WHERE p.is_active = true;

-- Представление статистики по сайтам
CREATE OR REPLACE VIEW site_statistics AS
SELECT 
    site,
    COUNT(*) as total_properties,
    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '7 days') as new_this_week,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    COUNT(DISTINCT neighborhood) as neighborhoods_count
FROM properties
WHERE is_active = true
GROUP BY site;

-- =========================================
-- КОММЕНТАРИИ И ДОКУМЕНТАЦИЯ
-- =========================================

COMMENT ON TABLE properties IS 'Основная таблица объявлений недвижимости';
COMMENT ON TABLE users IS 'Пользователи Telegram бота';
COMMENT ON TABLE user_searches IS 'Сохранённые поисковые запросы пользователей';
COMMENT ON TABLE notifications IS 'История уведомлений пользователям';
COMMENT ON TABLE price_history IS 'История изменения цен на объекты';
COMMENT ON TABLE scraping_stats IS 'Статистика работы парсера';

COMMENT ON COLUMN properties.search_vector IS 'Полнотекстовый поиск по объявлению';
COMMENT ON COLUMN properties.external_id IS 'ID объявления на сайте-источнике';
COMMENT ON COLUMN users.subscription_type IS 'Тип подписки: free, basic, premium, pro';

-- =========================================
-- ФИНАЛЬНЫЕ НАСТРОЙКИ
-- =========================================

-- Обновляем статистику для оптимизатора запросов
ANALYZE;

-- Выводим информацию об успешной инициализации
DO $$
BEGIN
    RAISE NOTICE '✅ База данных Property Scraper успешно инициализирована!';
    RAISE NOTICE '📊 Создано таблиц: %', (
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    );
    RAISE NOTICE '🔍 Создано индексов: %', (
        SELECT COUNT(*) 
        FROM pg_indexes 
        WHERE schemaname = 'public'
    );
END $$;
