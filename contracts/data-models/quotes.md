# Data Models: Quotes

Modelos de datos para cotizaciones y datos de mercado.

## Schemas

### Quote

Cotización en tiempo real de un ticker.

```yaml
Quote:
  type: object
  required:
    - ticker
    - price
    - change
    - change_percent
    - volume
    - timestamp
    - market_status
  properties:
    ticker:
      type: string
      pattern: '^[A-Z]{1,5}$'
      description: Símbolo bursátil
      example: AAPL
    
    price:
      type: number
      format: float
      description: Precio actual (last trade)
      example: 189.75
    
    change:
      type: number
      format: float
      description: Cambio absoluto desde cierre anterior
      example: 2.34
    
    change_percent:
      type: number
      format: float
      description: Cambio porcentual
      example: 1.25
    
    volume:
      type: integer
      format: int64
      description: Volumen acumulado del día
      example: 52847291
    
    # Bid/Ask
    bid:
      type: number
      format: float
      nullable: true
      description: Mejor precio bid
      example: 189.74
    
    ask:
      type: number
      format: float
      nullable: true
      description: Mejor precio ask
      example: 189.76
    
    bid_size:
      type: integer
      nullable: true
      description: Tamaño del bid (shares)
      example: 200
    
    ask_size:
      type: integer
      nullable: true
      description: Tamaño del ask (shares)
      example: 300
    
    # Intraday
    open:
      type: number
      format: float
      description: Precio de apertura
      example: 187.50
    
    high:
      type: number
      format: float
      description: Máximo del día
      example: 190.12
    
    low:
      type: number
      format: float
      description: Mínimo del día
      example: 187.25
    
    previous_close:
      type: number
      format: float
      description: Cierre del día anterior
      example: 187.41
    
    # Métricas adicionales
    market_cap:
      type: number
      format: int64
      nullable: true
      description: Capitalización de mercado (USD)
      example: 2945000000000
    
    pe_ratio:
      type: number
      format: float
      nullable: true
      description: Price-to-Earnings ratio
      example: 29.5
    
    avg_volume_10d:
      type: integer
      format: int64
      nullable: true
      description: Volumen promedio 10 días
      example: 58000000
    
    # Metadata
    timestamp:
      type: string
      format: date-time
      description: Timestamp de la cotización
      example: "2025-11-10T15:30:00Z"
    
    market_status:
      type: string
      enum: [pre_market, open, after_hours, closed]
      description: Estado actual del mercado
      example: open
    
    exchange:
      type: string
      enum: [NYSE, NASDAQ, AMEX]
      description: Exchange donde cotiza
      example: NASDAQ
```

### OHLCV

Barra de datos históricos (Open, High, Low, Close, Volume).

```yaml
OHLCV:
  type: object
  required:
    - timestamp
    - open
    - high
    - low
    - close
    - volume
  properties:
    timestamp:
      type: string
      format: date-time
      description: Timestamp del inicio del período
      example: "2025-11-10T09:30:00Z"
    
    open:
      type: number
      format: float
      description: Precio de apertura del período
      example: 187.50
    
    high:
      type: number
      format: float
      description: Precio máximo del período
      example: 190.12
    
    low:
      type: number
      format: float
      description: Precio mínimo del período
      example: 187.25
    
    close:
      type: number
      format: float
      description: Precio de cierre del período
      example: 189.75
    
    volume:
      type: integer
      format: int64
      description: Volumen total del período
      example: 52847291
    
    # Métricas derivadas
    vwap:
      type: number
      format: float
      nullable: true
      description: Volume-Weighted Average Price
      example: 188.95
    
    trades:
      type: integer
      nullable: true
      description: Número de trades en el período
      example: 125430
    
    # Datos ajustados (splits/dividends)
    adjusted_close:
      type: number
      format: float
      nullable: true
      description: Cierre ajustado por splits y dividendos
      example: 189.75
    
    dividend:
      type: number
      format: float
      nullable: true
      description: Dividendo pagado en el período
      example: 0.0
    
    split_coefficient:
      type: number
      format: float
      nullable: true
      description: Coeficiente de split (1.0 si no hay split)
      example: 1.0
```

### TickerInfo

Información y metadatos de un ticker.

```yaml
TickerInfo:
  type: object
  required:
    - ticker
    - name
    - exchange
    - currency
    - type
  properties:
    ticker:
      type: string
      pattern: '^[A-Z]{1,5}$'
      example: AAPL
    
    name:
      type: string
      description: Nombre de la empresa
      example: Apple Inc.
    
    exchange:
      type: string
      enum: [NYSE, NASDAQ, AMEX]
      example: NASDAQ
    
    currency:
      type: string
      pattern: '^[A-Z]{3}$'
      description: Moneda de cotización (ISO 4217)
      example: USD
    
    type:
      type: string
      enum: [stock, etf, index]
      description: Tipo de activo
      example: stock
    
    # Detalles adicionales
    sector:
      type: string
      nullable: true
      description: Sector GICS
      example: Technology
    
    industry:
      type: string
      nullable: true
      description: Industria GICS
      example: Consumer Electronics
    
    website:
      type: string
      format: uri
      nullable: true
      example: https://www.apple.com
    
    description:
      type: string
      nullable: true
      description: Descripción del negocio
      example: Apple Inc. designs, manufactures, and markets smartphones...
    
    # Fechas importantes
    ipo_date:
      type: string
      format: date
      nullable: true
      description: Fecha de IPO
      example: "1980-12-12"
    
    fiscal_year_end:
      type: string
      nullable: true
      description: Mes de cierre fiscal (Jan-Dec)
      example: September
    
    # Contacto
    employees:
      type: integer
      nullable: true
      description: Número de empleados
      example: 164000
    
    address:
      type: string
      nullable: true
      example: One Apple Park Way, Cupertino, CA 95014
    
    phone:
      type: string
      nullable: true
      example: +1 408-996-1010
```

## Storage

### TimescaleDB Tables

#### quotes_realtime

Tabla hypertable para cotizaciones en tiempo real.

```sql
CREATE TABLE quotes_realtime (
    time TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(5) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    change DOUBLE PRECISION NOT NULL,
    change_percent DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    bid DOUBLE PRECISION,
    ask DOUBLE PRECISION,
    bid_size INTEGER,
    ask_size INTEGER,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    previous_close DOUBLE PRECISION NOT NULL,
    market_cap BIGINT,
    pe_ratio DOUBLE PRECISION,
    avg_volume_10d BIGINT,
    market_status VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL
);

SELECT create_hypertable('quotes_realtime', 'time');

CREATE INDEX idx_quotes_realtime_ticker_time ON quotes_realtime (ticker, time DESC);
CREATE INDEX idx_quotes_realtime_exchange ON quotes_realtime (exchange, time DESC);
```

**Política de retención**: 90 días (Fase 2), 1 año (Fase 6)

#### quotes_ohlcv

Tabla hypertable para barras OHLCV.

```sql
CREATE TABLE quotes_ohlcv (
    time TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(5) NOT NULL,
    interval VARCHAR(10) NOT NULL, -- '1m', '5m', '15m', '1h', '1d'
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    vwap DOUBLE PRECISION,
    trades INTEGER,
    adjusted_close DOUBLE PRECISION,
    dividend DOUBLE PRECISION,
    split_coefficient DOUBLE PRECISION
);

SELECT create_hypertable('quotes_ohlcv', 'time');

CREATE INDEX idx_quotes_ohlcv_ticker_interval_time 
    ON quotes_ohlcv (ticker, interval, time DESC);
```

**Política de retención**: 
- `1m`: 7 días
- `5m`, `15m`: 30 días
- `1h`, `1d`: 5 años (permanente)

#### tickers_info

Tabla de metadatos (no hypertable, estática).

```sql
CREATE TABLE tickers_info (
    ticker VARCHAR(5) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    type VARCHAR(10) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    website VARCHAR(255),
    description TEXT,
    ipo_date DATE,
    fiscal_year_end VARCHAR(10),
    employees INTEGER,
    address TEXT,
    phone VARCHAR(20),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tickers_info_exchange ON tickers_info (exchange);
CREATE INDEX idx_tickers_info_sector ON tickers_info (sector);
```

## Referencias

- [quotes-api.yaml](../apis/quotes/quotes-api.yaml) - API REST para consultas
- [redis-pubsub-channels.md](../events/redis-pubsub-channels.md) - Eventos Pub/Sub
- [ADR-009](../../adr/ADR-009-secuenciacion-fases-desarrollo.md) - Secuenciación de fases

---

*Contrato mantenido por OPA_Machine supervisor*