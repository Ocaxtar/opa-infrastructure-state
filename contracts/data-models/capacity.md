# Data Models: Capacity

Modelos de datos para el módulo de Capacidad M&A.

> **⚠️ Nota ADR-015**: Las métricas financieras numéricas han sido **eliminadas** del pipeline MIPL.
> El modelo usa exclusivamente evidencia documental para descubrir patrones latentes.
> Ver ADR-015 para detalles.

## Schemas

### CapacityScore

Score de capacidad financiera para M&A de una empresa.

```yaml
CapacityScore:
  type: object
  required:
    - ticker
    - company_name
    - score
    - grade
    - as_of_date
    - components
    - last_updated
  properties:
    ticker:
      type: string
      pattern: '^[A-Z]{1,5}$'
      description: Símbolo bursátil
      example: AAPL
    
    company_name:
      type: string
      description: Nombre de la empresa
      example: Apple Inc.
    
    score:
      type: number
      format: float
      minimum: 0
      maximum: 100
      description: |
        Score global de capacidad M&A (0-100)
        - 90-100: Capacidad excelente (AAA/AA)
        - 70-89: Capacidad buena (A/BBB)
        - 50-69: Capacidad moderada (BB/B)
        - 0-49: Capacidad limitada (CCC o inferior)
      example: 92.5
    
    grade:
      type: string
      enum: [AAA, AA, A, BBB, BB, B, CCC, CC, C, D]
      description: Rating tipo crediticio
      example: AAA
    
    as_of_date:
      type: string
      format: date
      description: Fecha de los datos financieros base
      example: "2025-11-10"
    
    components:
      $ref: '#/CapacityComponents'
      description: Componentes detallados del score
    
    last_updated:
      type: string
      format: date-time
      description: Timestamp del último cálculo
      example: "2025-11-10T22:00:00Z"
```

### CapacityComponents

Componentes del score de capacidad (sub-scores).

```yaml
CapacityComponents:
  type: object
  required:
    - financial_strength
    - liquidity
    - leverage
    - cash_generation
  properties:
    financial_strength:
      type: object
      required:
        - score
        - weight
      properties:
        score:
          type: number
          format: float
          minimum: 0
          maximum: 100
          description: Score de solidez financiera
          example: 95.0
        weight:
          type: number
          format: float
          minimum: 0
          maximum: 1
          description: Peso en score global
          example: 0.30
        metrics:
          type: object
          description: Métricas específicas
          properties:
            market_cap:
              type: number
              format: int64
            ebitda:
              type: number
              format: int64
            revenue_ttm:
              type: number
              format: int64
    
    liquidity:
      type: object
      required:
        - score
        - weight
      properties:
        score:
          type: number
          format: float
          minimum: 0
          maximum: 100
          description: Score de liquidez
          example: 88.0
        weight:
          type: number
          format: float
          example: 0.25
        metrics:
          type: object
          properties:
            cash_and_equivalents:
              type: number
              format: int64
            current_ratio:
              type: number
              format: float
            quick_ratio:
              type: number
              format: float
    
    leverage:
      type: object
      required:
        - score
        - weight
      properties:
        score:
          type: number
          format: float
          minimum: 0
          maximum: 100
          description: Score de apalancamiento (inverso)
          example: 92.0
        weight:
          type: number
          format: float
          example: 0.25
        metrics:
          type: object
          properties:
            debt_to_equity:
              type: number
              format: float
            debt_to_ebitda:
              type: number
              format: float
            interest_coverage:
              type: number
              format: float
    
    cash_generation:
      type: object
      required:
        - score
        - weight
      properties:
        score:
          type: number
          format: float
          minimum: 0
          maximum: 100
          description: Score de generación de caja
          example: 94.0
        weight:
          type: number
          format: float
          example: 0.20
        metrics:
          type: object
          properties:
            free_cash_flow:
              type: number
              format: int64
            operating_cash_flow:
              type: number
              format: int64
            fcf_margin:
              type: number
              format: float
```

## Storage

### TimescaleDB Tables

#### capacity_scores

Tabla hypertable para scores de capacidad.

```sql
CREATE TABLE capacity_scores (
    time TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(5) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    score DOUBLE PRECISION NOT NULL CHECK (score >= 0 AND score <= 100),
    grade VARCHAR(3) NOT NULL,
    as_of_date DATE NOT NULL,
    
    -- Components
    financial_strength_score DOUBLE PRECISION NOT NULL,
    financial_strength_weight DOUBLE PRECISION NOT NULL,
    liquidity_score DOUBLE PRECISION NOT NULL,
    liquidity_weight DOUBLE PRECISION NOT NULL,
    leverage_score DOUBLE PRECISION NOT NULL,
    leverage_weight DOUBLE PRECISION NOT NULL,
    cash_generation_score DOUBLE PRECISION NOT NULL,
    cash_generation_weight DOUBLE PRECISION NOT NULL,
    
    -- Metadata
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('capacity_scores', 'time');

CREATE INDEX idx_capacity_scores_ticker_time ON capacity_scores (ticker, time DESC);
CREATE INDEX idx_capacity_scores_grade ON capacity_scores (grade, time DESC);
```

**Política de retención**: 5 años (permanente)

## Referencias

- [capacity-api.yaml](../apis/capacity/capacity-api.yaml) - API REST
- [redis-pubsub-channels.md](../events/redis-pubsub-channels.md) - Canal capacity.scores
- ADR-015 - Eliminación métricas financieras del pipeline MIPL

---

*Contrato mantenido por OPA_Machine supervisor*