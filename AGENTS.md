# AGENTS.md - opa-infrastructure-state

**Versión**: 1.0.0  
**Fecha**: 2026-01-20  
**Mantenido por**: Supervisor OPA_Machine

---

## 🎯 Identidad del Repositorio

**Tipo**: Shared resource (estado + contratos)  
**Código operativo**: NO (solo datos y scripts de consulta)  
**Mantenedor**: Supervisor OPA_Machine (GitHub Copilot Agent)  
**Consumidores**: Todos los repos operativos del ecosistema

---

## 📜 Responsabilidades del Supervisor

Como agente supervisor, tus responsabilidades en este repo son:

### 1. Mantener state.yaml actualizado

**Cuándo actualizar**:
- Cambio de puerto/credenciales de contenedor
- Deploy de nuevo servicio
- Actualización de estado de servicio (post-run de repos operativos)
- Nuevo conflicto conocido detectado

**Cómo actualizar**:
```bash
# Opción 1: Manual (editar vim/VSCode)
vim state.yaml
git add state.yaml
git commit -m "OPA-XXX: Descripción del cambio"
git push origin main

# Opción 2: Automático desde repo operativo
python ../opa-infrastructure-state/scripts/update_state.py \
  --repo opa-quotes-streamer \
  --commit ed42f4a \
  --issues OPA-281,OPA-282
```

### 2. Copiar contratos desde supervisor

**Cuándo copiar**:
- Nuevo contrato creado en `OPA_Machine/docs/contracts/`
- Actualización de versión de contrato existente

**Workflow**:
```bash
# 1. Verificar cambios en supervisor
cd OPA_Machine
git diff HEAD~1 docs/contracts/

# 2. Copiar a opa-infrastructure-state
cp docs/contracts/events/redis-pubsub-channels.md \
   ../opa-infrastructure-state/contracts/events/

# 3. Actualizar versión en state.yaml
vim ../opa-infrastructure-state/state.yaml
# contracts:
#   redis-pubsub:
#     version: "1.1.0"  # <-- Actualizar

# 4. Commit y push
cd ../opa-infrastructure-state
git add contracts/ state.yaml
git commit -m "OPA-XXX: Update redis-pubsub contract to v1.1.0"
git push origin main
```

### 3. Validar consistencia de estado

**Cuándo validar**:
- Antes de cada commit a state.yaml
- En CI/CD (automático)
- Cuando repo operativo reporta error de conexión

**Cómo validar**:
```bash
python scripts/validate_state.py
# Exit code 0 = OK
# Exit code 1 = Errores (ver stdout para detalles)
```

### 4. Detectar desincronización
**Escenarios a detectar**:

1. **Puerto en state.yaml no coincide con docker-compose.yml de repo operativo**
   - Generar issue en repo operativo para fix
   - Issue type: bug, severity: high

2. **Contrato en state.yaml desactualizado vs supervisor**
   - Copiar versión actual desde supervisor
   - Commit con mensaje de actualización

3. **Servicio en state.yaml sin actividad reciente (>7 días)**
   - Verificar si repo sigue operativo
   - Comentar en última issue del repo para confirmar estado

---

## 🛠️ Uso del Repo en Repos Operativos

### Integración Pre-Flight Checklist

Todos los repos operativos deben consultar estado ANTES de Docker/DB:

```python
# En inicio de run de repo operativo:
import subprocess
import json

def get_db_config(container_name):
    result = subprocess.run(
        ['python', '../opa-infrastructure-state/scripts/query_state.py', 'db', container_name],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Ejemplo:
config = get_db_config('timescaledb_quotes')
conn_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
```

### Post-Run Update

Repos operativos deben actualizar estado al finalizar:

```bash
# En fin de run exitoso:
python ../opa-infrastructure-state/scripts/update_state.py \
  --repo $(basename $PWD) \
  --commit $(git rev-parse HEAD) \
  --issues $(linear issue list --format json | jq -r '.[] | select(.state=="Done") | .identifier' | paste -sd,)
```

---

## ⚠️ Errores Críticos a Evitar

### 1. Editar state.yaml sin validar

```bash
❌ vim state.yaml && git commit && git push  # MAL
✅ vim state.yaml && python scripts/validate_state.py && git commit && git push  # BIEN
```

### 2. Copiar contrato obsoleto

```bash
❌ cp old_version.md contracts/  # MAL
✅ # BIEN: Verificar versión en supervisor primero
grep "Versión:" OPA_Machine/docs/contracts/events/redis-pubsub-channels.md
cp OPA_Machine/docs/contracts/events/redis-pubsub-channels.md contracts/events/
```

### 3. Pushear sin actualizar last_updated

```yaml
❌ # MAL: Editar containers pero NO actualizar last_updated
containers:
  timescaledb_quotes:
    port: 5434  # Cambio
last_updated: "2026-01-19T10:00:00Z"  # OBSOLETO

✅ # BIEN: Actualizar last_updated
containers:
  timescaledb_quotes:
    port: 5434
last_updated: "2026-01-20T12:30:00Z"  # ACTUALIZADO
```

### 4. Usar update_state.py con repo incorrecto

```bash
❌ # En opa-quotes-streamer:
python ../opa-infrastructure-state/scripts/update_state.py --repo opa-quotes-api  # MAL

✅ # BIEN:
python ../opa-infrastructure-state/scripts/update_state.py --repo opa-quotes-streamer
```

---

## 📚 Convenciones

### Commits

**Formato**: `OPA-XXX: Descripción imperativa`

**Ejemplos**:
```bash
git commit -m "OPA-294: Add initial state.yaml with container configs"
git commit -m "OPA-301: Update redis-pubsub contract to v1.1.0"
git commit -m "OPA-305: Add port conflict documentation for 5432"
```

### Branches

**Uso**: Solo `main` (repo simple, cambios atómicos)

**Excepciones**: Si cambio requiere validación compleja (ej: refactor de state.yaml), usar branch temporal:
```bash
git checkout -b supervisor/opa-xxx-refactor-state-schema
# Hacer cambios, validar, PR
```

### Issues Linear

Este repo NO tiene issues propias. Issues están en supervisor OPA_Machine.

**Tags relevantes**:
- `infrastructure` - Cambios de puertos/contenedores
- `contracts` - Actualizaciones de contratos
- `supervisor-maintenance` - Tareas de mantenimiento del supervisor

---

## 🔄 Integración con Supervisor

### Sincronización de contratos

**Workflow automático** (cuando se implementa):

1. Supervisor detecta cambio en `OPA_Machine/docs/contracts/`
2. Compara con `opa-infrastructure-state/contracts/`
3. Si hay diferencia:
   - Copia versión nueva a opa-infrastructure-state
   - Actualiza `state.yaml` (versión de contrato)
   - Commit + push
   - Genera issue en repos consumidores para actualizar código

**Manual** (mientras no está automático):

Cuando cierres issue en supervisor que modifica contrato, verificar:
```bash
cd OPA_Machine
git diff HEAD~1 docs/contracts/

# Si hay cambios:
cd ../opa-infrastructure-state
cp ../OPA_Machine/docs/contracts/[...].md contracts/[...]/
git add contracts/
git commit -m "OPA-XXX: Sync contract from supervisor"
git push origin main
```

---

## 📊 Métricas de Salud del Repo

### Indicadores de calidad

- `state.yaml` pasa validación: ✅ Siempre
- Contratos sincronizados con supervisor: ✅ Verificar semanalmente
- Servicios sin actividad >7 días: ⚠️ Investigar
- Conflictos sin workaround: ❌ Documentar

### Alertas a generar

```python
# Pseudo-código para alertas
if service['last_run'] > 7_days_ago:
    create_issue(
        repo="OPA_Machine",
        title=f"Servicio {service['name']} sin actividad >7d",
        labels=["infrastructure", "monitoring"]
    )

if contract['version'] != supervisor_contract['version']:
    sync_contract(contract)
    notify_consumers(contract)
```

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio | Issue |
|---------|-------|--------|-------|
| 1.0.0 | 2026-01-20 | Documento inicial con responsabilidades supervisor | OPA-294 |

---

*Documento mantenido por OPA-294 Infrastructure State initiative.*