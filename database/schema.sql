"""
Схема базы данных для маркетинговой аналитики "Евгенич"
"""

-- Таблица каналов привлечения
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    cost_per_month DECIMAL(10, 2) DEFAULT 0,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица лидов
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    channel_id INTEGER REFERENCES channels(id),
    source VARCHAR(255),
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    lead_date TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'new',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица клиентов
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    phone VARCHAR(50) UNIQUE,
    email VARCHAR(255),
    first_visit_date DATE,
    last_visit_date DATE,
    total_visits INTEGER DEFAULT 0,
    total_revenue DECIMAL(10, 2) DEFAULT 0,
    average_check DECIMAL(10, 2) DEFAULT 0,
    segment VARCHAR(50) DEFAULT 'Новый',
    lead_id INTEGER REFERENCES leads(id),
    channel_id INTEGER REFERENCES channels(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица посещений (чеков)
CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    visit_date TIMESTAMP NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    guests_count INTEGER DEFAULT 1,
    duration_minutes INTEGER,
    room_type VARCHAR(100),
    services TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица резервов RestoPlace
CREATE TABLE IF NOT EXISTS reserves (
    id SERIAL PRIMARY KEY,
    reserve_id VARCHAR(255),
    guest_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    visit_datetime TIMESTAMP,
    status VARCHAR(100),
    amount DECIMAL(10, 2) DEFAULT 0,
    guests_count INTEGER DEFAULT 1,
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(reserve_id)
);

-- Таблица метрик каналов (агрегированные данные)
CREATE TABLE IF NOT EXISTS channel_metrics (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES channels(id),
    date DATE NOT NULL,
    leads_count INTEGER DEFAULT 0,
    clients_count INTEGER DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,
    cost DECIMAL(10, 2) DEFAULT 0,
    cac DECIMAL(10, 2) DEFAULT 0,
    ltv DECIMAL(10, 2) DEFAULT 0,
    roi DECIMAL(10, 4) DEFAULT 0,
    conversion_rate DECIMAL(5, 4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, date)
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_leads_channel_date ON leads(channel_id, lead_date);
CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);
CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone);
CREATE INDEX IF NOT EXISTS idx_visits_client_date ON visits(client_id, visit_date);
CREATE INDEX IF NOT EXISTS idx_reserves_phone ON reserves(phone);
CREATE INDEX IF NOT EXISTS idx_channel_metrics_date ON channel_metrics(date);

-- Триггеры для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_channels_updated_at BEFORE UPDATE ON channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_visits_updated_at BEFORE UPDATE ON visits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reserves_updated_at BEFORE UPDATE ON reserves
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channel_metrics_updated_at BEFORE UPDATE ON channel_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Вставка базовых каналов
INSERT INTO channels (name, cost_per_month, description) VALUES
    ('Yandex', 50000, 'Яндекс.Директ реклама'),
    ('Google', 45000, 'Google Ads реклама'),
    ('VK', 25000, 'ВКонтакте реклама'),
    ('Instagram', 30000, 'Instagram реклама'),
    ('Сайт', 15000, 'Органический трафик с сайта'),
    ('Рекомендации', 0, 'Рекомендации клиентов'),
    ('RestoPlace', 5000, 'Бронирования через RestoPlace')
ON CONFLICT (name) DO NOTHING;
