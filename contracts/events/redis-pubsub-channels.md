# Contrato de Eventos: Redis Pub/Sub Channels

**Versión**: 1.0.0  
**Fecha**: 2026-01-20  
**Estado**: ✅ Activo (Fase 2)  
**ADR Relacionado**: Pendiente (Redis Pub/Sub como backbone pre-Kafka)

---

## 🎯 Propósito

Define los channels de Redis Pub/Sub para comunicación asíncrona entre módulos del ecosistema OPA_Machine durante Fase 2.

**Contexto arquitectónico**:
- **Fase 2**: Redis Pub/Sub (simple, rápido, validación)
- **Fase 6**: Migración a Kafka (producción, escalabilidad)

---

## 📋 Channels Definidos

### 1. `quotes.realtime` - Cotizaciones en tiempo real

**Publisher**: `opa-quotes-streamer`  
**Subscribers**: `opa-capacity-api`, `opa-prediction-*` (futuro), sistemas de alertas

**Propósito**: Distribuir quotes de mercado en tiempo real a consumidores.

**Schema del mensaje**:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["ticker", "timestamp", "price", "volume", "source"],
  "properties": {
    "ticker": {
      "type": "string",
      "description": "Símbolo del ticker (ej: AAPL, MSFT)",
      "pattern": "^[A-Z]{1,5}$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp UTC en formato ISO 8601"
    },
    "price": {
      "type": "number",
      "description": "Precio actual (last trade)",
      "minimum": 0
    },
    "volume": {
      "type": "integer",
      "description": "Volumen acumulado del día",
      "minimum": 0
    },
    "bid": {
      "type": "number",
      "description": "Mejor precio de compra (opcional)"
    },
    "ask": {
      "type": "number",
      "description": "Mejor precio de venta (opcional)"
    },
    "source": {
      "type": "string",
      "description": "Fuente de datos (yfinance, alpaca, polygon)",
      "enum": ["yfinance", "alpaca", "polygon"]
    }
  }
}
```

**Ejemplo**:

```json
{
  "ticker": "AAPL",
  "timestamp": "2026-01-20T14:30:15.123Z",
  "price": 185.50,
  "volume": 45000000,
  "bid": 185.48,
  "ask": 185.52,
  "source": "yfinance"
}
```

**Políticas**:
- **Retención**: No persistente (Redis no guarda histórico)
- **TTL**: N/A (pub/sub no tiene TTL)
- **Throughput esperado**: 100-300 msgs/seg (Fase 2)
- **Latencia objetivo**: <50ms desde publish a subscribe

---

### 2. `capacity.scores` - Scoring de capacidad M&A

**Publisher**: `opa-capacity-compute`  
**Subscribers**: `opa-prediction-*` (futuro), dashboards, alertas

**Propósito**: Distribuir scores de capacidad cuando se recalculan.

**Schema del mensaje**:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["ticker", "timestamp", "score", "confidence", "model_version"],
  "properties": {
    "ticker": {
      "type": "string",
      "pattern": "^[A-Z]{1,5}$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp del cálculo"
    },
    "score": {
      "type": "number",
      "description": "Score de capacidad [0-100]",
      "minimum": 0,
      "maximum": 100
    },
    "confidence": {
      "type": "number",
      "description": "Nivel de confianza [0-1]",
      "minimum": 0,
      "maximum": 1
    },
    "model_version": {
      "type": "string",
      "description": "Versión del modelo MIPL usado (ej: v1.2.3)"
    },
    "features_count": {
      "type": "integer",
      "description": "Número de features documentales usadas"
    }
  }
}
```

**Ejemplo**:

```json
{
  "ticker": "AAPL",
  "timestamp": "2026-01-20T08:00:00.000Z",
  "score": 78.5,
  "confidence": 0.92,
  "model_version": "1.0.0",
  "features_count": 42
}
```

**Políticas**:
- **Frecuencia**: Diaria (08:00 UTC)
- **Throughput esperado**: ~450 msgs/día (batch diario)
- **Retención**: No persistente (consumidores deben persistir si necesario)

---

### 3. `system.health` - Health checks y estado de servicios

**Publisher**: Todos los servicios  
**Subscribers**: Sistema de monitorización, dashboards

**Propósito**: Heartbeats y cambios de estado de servicios.

**Schema del mensaje**:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["service", "timestamp", "status"],
  "properties": {
    "service": {
      "type": "string",
      "description": "Nombre del servicio",
      "pattern": "^opa-[a-z-]+$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "status": {
      "type": "string",
      "enum": ["healthy", "degraded", "unhealthy"],
      "description": "Estado del servicio"
    },
    "details": {
      "type": "object",
      "description": "Detalles adicionales (opcional)",
      "properties": {
        "uptime_seconds": {"type": "integer"},
        "memory_mb": {"type": "number"},
        "cpu_percent": {"type": "number"}
      }
    }
  }
}
```

**Ejemplo**:

```json
{
  "service": "opa-quotes-streamer",
  "timestamp": "2026-01-20T14:30:00.000Z",
  "status": "healthy",
  "details": {
    "uptime_seconds": 86400,
    "memory_mb": 256,
    "cpu_percent": 15.5
  }
}
```

**Políticas**:
- **Frecuencia**: Cada 30 segundos (heartbeat)
- **Throughput esperado**: ~8 servicios × 2/min = 16 msgs/min

---

## 🔧 Configuración de Redis

### Versión

- **Redis**: 7.2+ (soporte Pub/Sub mejorado)

### Configuración recomendada

```conf
# redis.conf (para Pub/Sub)
maxmemory 256mb
maxmemory-policy noeviction
timeout 0
tcp-keepalive 300
```

### Puertos

- **Producción**: 6379 (estándar)
- **Desarrollo/Windows**: 6381 (evitar conflicto con Redis local)

---

## 🔒 Políticas de Seguridad

### Autenticación

```bash
# En Fase 2: Sin password (red Docker interna)
# En Fase 6 (producción): AUTH + TLS
```

### Network

- Redis **NO expuesto** fuera de Docker network
- Solo servicios OPA pueden conectar

---

## 📊 Métricas Requeridas

Todos los publishers deben exponer:

```python
# Métricas Prometheus
redis_publishes_total{channel="quotes.realtime"}
redis_publish_errors_total{channel="quotes.realtime"}
redis_publish_latency_seconds{channel="quotes.realtime"}
```

---

## 🧪 Testing

### Test de integración ejemplo

```python
import redis
import json

# Setup
r = redis.Redis(host='localhost', port=6379)
pubsub = r.pubsub()
pubsub.subscribe('quotes.realtime')

# Publish
message = {
    "ticker": "AAPL",
    "timestamp": "2026-01-20T14:30:00Z",
    "price": 185.50,
    "volume": 45000000,
    "source": "yfinance"
}
r.publish('quotes.realtime', json.dumps(message))

# Subscribe (blocking)
for msg in pubsub.listen():
    if msg['type'] == 'message':
        data = json.loads(msg['data'])
        print(f"Received: {data}")
        break
```

---

## 🔄 Migración a Kafka (Fase 6)

Cuando se migre a Kafka:

| Redis Channel | Kafka Topic | Cambios |
|---------------|-------------|---------|  
| `quotes.realtime` | `opa.quotes.realtime` | + partitioning por ticker |
| `capacity.scores` | `opa.capacity.scores` | + retención 7 días |
| `system.health` | `opa.system.health` | + compaction |

**Plan de migración**: Dual-write (Redis + Kafka) durante 1 mes de transición.

---

## 📚 Referencias

- [Redis Pub/Sub Documentation](https://redis.io/docs/manual/pubsub/)
- ADR-017: Sistema Normativa Unificada

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio | Issue |
|---------|-------|--------|-------|
| 1.0.0 | 2026-01-20 | Contrato inicial con 3 channels | OPA-284 |

---

*Documento mantenido por OPA-284 Redis Pub/Sub initiative.*