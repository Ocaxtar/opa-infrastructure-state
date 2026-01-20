# opa-infrastructure-state

**Versión**: 1.0.0  
**Estado**: ✅ Activo (Fase 2)  
**Mantenido por**: Supervisor OPA_Machine

---

## 🎯 Propósito

Repositorio que actúa como **fuente única de verdad (single source of truth)** para el estado de infraestructura del ecosistema OPA_Machine.

**Problema que resuelve**:

Cada vez que un repo operativo interactuar con contenedores Docker o bases de datos, se consumía tiempo diagnosticando:
- ¿Qué puertos están en uso?
- ¿Cuáles son las credenciales actuales?
- ¿Está el contenedor actualizado o tiene código obsoleto?
- ¿Dónde está el contrato de este servicio?
- ¿Hay conflictos conocidos (ej: PostgreSQL local en Windows)?

**Solución**:

Centralizar TODO el estado de infraestructura en un repositorio git-versionado que:
1. Es consultable mediante CLI/scripts (`query_state.py`)
2. Se actualiza automáticamente al finalizar operaciones (`update_state.py`)
3. Centraliza contratos de APIs/eventos/data models
4. Documenta conflictos conocidos
5. Se valida en CI/CD (`validate_state.py`)

---

## 🚀 Quick Start

### 1. Consultar estado de base de datos

```bash
python scripts/query_state.py db timescaledb_quotes
```

**Output**:
```json
{
  "host": "localhost",
  "port": 5433,
  "database": "opa_quotes",
  "user": "opa_user",
  "password": "opa_password"
}
```

### 2. Ver todos los puertos asignados

```bash
python scripts/query_state.py ports
```

**Output**:
```json
{
  "5432": "BLOQUEADO - PostgreSQL Local Windows (CONFLICT)",
  "5433": "TimescaleDB Quotes (Docker)",
  "5434": "TimescaleDB Capacity (Docker)",
  "6381": "Redis Dev (Docker)"
}
```

### 3. Consultar estado de un servicio

```bash
python scripts/query_state.py service opa-quotes-streamer
```

**Output**:
```json
{
  "last_run": "2026-01-20T11:44:00Z",
  "last_commit": "ed42f4a",
  "status": "operational",
  "completed_issues": ["OPA-281", "OPA-282"]
}
```

### 4. Ver conflictos conocidos

```bash
python scripts/query_state.py conflicts
```

**Output**:
```json
[
  {
    "id": "port-5432-postgres-local",
    "description": "Puerto 5432 ocupado por PostgreSQL local Windows",
    "severity": "high",
    "workaround": "Usar puerto 5433+ para contenedores Docker"
  }
]
```

---

## 📚 Estructura del Repositorio

```
opa-infrastructure-state/
├── state.yaml                  # Estado dinámico de infraestructura
├── scripts/
│   ├── query_state.py        # CLI para consultas
│   ├── update_state.py       # Actualización automática post-run
│   └── validate_state.py     # Validación CI/CD
├── contracts/
│   ├── events/               # Contratos Pub/Sub
│   │   └── redis-pubsub-channels.md
│   └── data-models/         # Modelos de datos
│       ├── quotes.md
│       └── capacity.md
├── README.md
└── AGENTS.md
```

---

## 🛠️ Uso desde Repos Operativos

### Pre-Flight Checklist (OBLIGATORIO)

**Todos los repos operativos deben consultar estado ANTES de usar Docker/DB**:

```bash
# En inicio de run:
python ../opa-infrastructure-state/scripts/query_state.py db timescaledb_quotes

# Verificar puerto antes de docker-compose up:
python ../opa-infrastructure-state/scripts/query_state.py port 5433
```

### Post-Run Update (RECOMENDADO)

```bash
# Al finalizar operaciones exitosas:
python ../opa-infrastructure-state/scripts/update_state.py \
  --repo opa-quotes-streamer \
  --commit $(git rev-parse HEAD) \
  --issues OPA-281,OPA-282
```

Esto actualiza `state.yaml` y hace commit+push automáticamente.

---

## 📝 Estructura de state.yaml

```yaml
version: "1.0.0"
last_updated: "2026-01-20T12:00:00Z"

containers:
  timescaledb_quotes:
    image: timescale/timescaledb:latest-pg14
    port: 5433
    status: active
    credentials:
      user: opa_user
      password: opa_password
      database: opa_quotes

ports:
  5432: "BLOQUEADO - PostgreSQL Local Windows"
  5433: "TimescaleDB Quotes (Docker)"
  6381: "Redis Dev (Docker)"

services:
  opa-quotes-streamer:
    last_run: "2026-01-20T11:44:00Z"
    last_commit: "ed42f4a"
    status: operational
    completed_issues: ["OPA-281", "OPA-282"]

contracts:
  redis-pubsub:
    version: "1.0.0"
    file: "contracts/events/redis-pubsub-channels.md"
    consumers: ["opa-quotes-streamer", "opa-capacity-api"]

known_conflicts:
  - id: port-5432-postgres-local
    description: "Puerto 5432 ocupado por PostgreSQL local Windows"
    severity: high
    workaround: "Usar puerto 5433+ para contenedores Docker"
```

---

## 🤖 Scripts Disponibles

### query_state.py

CLI para consultar estado de infraestructura.

**Comandos**:
```bash
# Configuración de base de datos
query_state.py db <container_name>

# Todos los puertos
query_state.py ports

# Info de un puerto específico
query_state.py port <port_number>

# Credenciales de contenedor
query_state.py credentials <container_name>

# Estado de servicio
query_state.py service <repo_name>

# Conflictos conocidos
query_state.py conflicts
```

**Output**: JSON (para parsing automático)

### update_state.py

Actualiza estado de servicios y hace commit+push automático.

**Uso**:
```bash
update_state.py --repo <repo_name> --commit <commit_hash> [--issues OPA-X,OPA-Y]
```

**Qué hace**:
1. Actualiza `state.yaml` con timestamp/commit/issues
2. `git add state.yaml`
3. `git commit -m "Update <repo> state"`
4. `git push origin main`

### validate_state.py

Valida estructura y formato de `state.yaml` (usado en CI/CD).

**Validaciones**:
- Claves requeridas presentes
- Formato de versión correcto (X.Y.Z)
- Timestamps en formato ISO 8601
- Puertos como enteros
- Campos obligatorios de contenedores

**Uso**:
```bash
validate_state.py  # Exit code 0 si OK, 1 si error
```

---

## 🔒 Mantenimiento

### ¿Cuándo actualizar manualmente?

1. **Cambio de puerto/credenciales**: Editar `state.yaml` directamente
2. **Nuevo contenedor**: Añadir entrada en `containers:`
3. **Nuevo conflicto conocido**: Añadir a `known_conflicts:`
4. **Actualización de contrato**: Copiar desde supervisor

### ¿Quién mantiene este repo?

**Supervisor OPA_Machine (GitHub Copilot Agent)**

- Actualiza contratos cuando cambian en supervisor
- Valida consistencia de estado
- Propaga cambios a repos operativos
- Genera issues si detecta desincronización

### Workflow de cambios

```bash
# 1. Editar state.yaml localmente
vim state.yaml

# 2. Validar cambios
python scripts/validate_state.py

# 3. Commit y push
git add state.yaml
git commit -m "OPA-XXX: Descripción del cambio"
git push origin main
```

---

## 🔗 Contratos Disponibles

### Eventos

- [redis-pubsub-channels.md](contracts/events/redis-pubsub-channels.md) - Channels Redis Pub/Sub
  - `quotes.realtime` - Cotizaciones en tiempo real
  - `capacity.scores` - Scores de capacidad M&A
  - `system.health` - Health checks de servicios

### Data Models

- [quotes.md](contracts/data-models/quotes.md) - Modelos de cotizaciones (Quote, OHLCV, TickerInfo)
- [capacity.md](contracts/data-models/capacity.md) - Modelos de capacidad (CapacityScore, Components)

**Cómo consultar contratos desde repos**:

```bash
# Leer contrato de Redis Pub/Sub
cat ../opa-infrastructure-state/contracts/events/redis-pubsub-channels.md

# O importar desde Python (si está en sistema de archivos)
import yaml
with open('../opa-infrastructure-state/state.yaml') as f:
    state = yaml.safe_load(f)
    print(state['contracts']['redis-pubsub']['file'])
```

---

## ⚠️ Conflictos Conocidos

### 1. Puerto 5432 - PostgreSQL Local Windows

**Problema**: PostgreSQL local de Windows ocupa puerto 5432, causando conflicto con contenedores Docker.

**Workaround**: Usar puertos 5433+ para TimescaleDB en Docker.

**Estado**: Documentado en `state.yaml` y [service-inventory.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md) del supervisor.

### 2. Encoding Windows CP850

**Problema**: Terminal Windows usa CP850 en lugar de UTF-8, causando errores con caracteres especiales en logs.

**Workaround**: Configurar Python con `PYTHONIOENCODING=utf-8` o usar WSL.

---

## 🧪 Testing

### Test de integración

```python
import subprocess
import json

def test_query_db():
    result = subprocess.run(
        ['python', 'scripts/query_state.py', 'db', 'timescaledb_quotes'],
        capture_output=True,
        text=True
    )
    config = json.loads(result.stdout)
    assert config['port'] == 5433
    assert config['user'] == 'opa_user'

def test_query_conflicts():
    result = subprocess.run(
        ['python', 'scripts/query_state.py', 'conflicts'],
        capture_output=True,
        text=True
    )
    conflicts = json.loads(result.stdout)
    assert any(c['id'] == 'port-5432-postgres-local' for c in conflicts)
```

---

## 📚 Referencias

- [AGENTS.md](AGENTS.md) - Guía para agentes IA que mantienen este repo
- [OPA_Machine supervisor](https://github.com/Ocaxtar/OPA_Machine) - Repositorio principal
- [service-inventory.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md) - Documento original migrado
- [OPA-294](https://linear.app/opa/issue/OPA-294) - Issue de creación de este repo

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio | Issue |
|---------|-------|--------|-------|
| 1.0.0 | 2026-01-20 | Repo inicial con state.yaml, scripts, contratos | OPA-294 |

---

*Repositorio mantenido por OPA-294 Infrastructure State initiative.*