# Spec: Scout Agent

## Rol
El Scout es el primer agente del pipeline editorial de The Southmetaverse Sea.
Su trabajo es monitorear fuentes externas, recolectar información relevante,
y entregarla al Analyst Agent para su procesamiento profundo.

El Scout no analiza, no verifica, no escribe. Solo recolecta y clasifica.

---

## Frecuencia de ejecución
Cada 6 horas (cron job): 00:00 / 06:00 / 12:00 / 18:00 UTC

---

## Fuentes configuradas

### X / Twitter
❌ **No incluido en MVP.** Requiere plan Basic ($200/mes). Se agrega en Fase 2 cuando el pipeline esté funcionando.

Cuentas prioritarias para cuando se active:
- @balajis — The Network State, d/acc, geopolítica tech
- @VitalikButerin — Ethereum, crypto, filosofía de protocolos
- @a16z — Venture capital, startups AI/crypto
- @0xSamm — DeFi, on-chain analysis (confirmar handle exacto)
- @higgsfield_ai — GenAI Art, video generativo (confirmar handle)

### Telegram
Canales activos en el MVP. Los IDs numéricos se resuelven con el script
`scripts/get_telegram_ids.py` antes del primer deploy.

| Canal | Temática principal |
|-------|-------------------|
| y22 trades | Trading, mercados, DeFi |
| crypto goodreads | Análisis profundo, research |
| crypto narratives | Narrativas de mercado, tendencias |

El Scout lee los últimos N mensajes desde el último checkpoint guardado en DB.

### YouTube
| Canal | Por qué |
|-------|---------|
| Network State | Balaji, soberanía digital, network states |
| a16z | Tech, AI, crypto investments |
| Y Combinator | Startups, founders, tendencias |

**Método:** RSS feed de cada canal. El Scout extrae título, descripción y transcript si está disponible.

### Noticias
| Fuente | URL |
|--------|-----|
| CoinDesk | https://coindesk.com/arc/outboundfeeds/rss/ |
| Bankless | https://banklesshq.com/feed |
| Coin Bureau | https://coinbureau.com/feed |

**Método:** RSS feed. Parsear título, excerpt y link.

### Exchanges
| Fuente | Qué recolectar |
|--------|---------------|
| Binance | Anuncios oficiales (listings, delistings, cambios de política) |

**Método:** Feed oficial de anuncios de Binance.

### On-chain / Analytics
| Fuente | Qué recolectar |
|--------|---------------|
| Nansen | Smart money movements, wallet labels, trending tokens |

**Método:** API de Nansen (requiere API key en `.env`).

---

## Qué recolecta el Scout

Por cada item encontrado, el Scout extrae y guarda:

```python
{
    "source": "coindesk",            # identificador de la fuente
    "source_type": "news",           # news | social | video | onchain
    "url": "https://...",            # URL original
    "title": "...",                  # título o primer texto del mensaje
    "excerpt": "...",                # resumen o primeros 280 chars
    "raw_content": "...",            # contenido completo si está disponible
    "author": "...",                 # autor o canal
    "published_at": "2026-03-04T...",   # timestamp original
    "collected_at": "2026-03-04T...",   # cuando lo recolectó el Scout
    "topics": ["defi", "ethereum"],  # clasificación temática (ver abajo)
    "entities": ["Uniswap", "Vitalik"],  # entidades detectadas
    "needs_research": true/false,    # flag para el Analyst
    "needs_research_reason": "...",  # por qué necesita investigación
    "status": "pending_analysis"     # siempre este valor al crear
}
```

---

## Clasificación temática

El Scout clasifica cada item en uno o más de estos topics:

- `crypto_defi` — DeFi, protocolos, yields, liquidez
- `crypto_market` — precios, volúmenes, mercados
- `web3` — NFTs, DAOs, infraestructura Web3
- `ai_tech` — modelos de IA, herramientas, investigación
- `genai_art` — arte generativo, modelos de imagen
- `geopolitics` — regulación, geopolítica con impacto en crypto/IA
- `startups` — fundraising, nuevos proyectos en AI/crypto
- `network_state` — soberanía digital, Network State, d/acc

Si un item no encaja en ninguna categoría → se descarta. No va a la DB.

---

## Detección de entidades y flag needs_research

El Scout detecta entidades nombradas en el contenido: proyectos, protocolos,
personas, tokens, empresas.

Para cada entidad detectada, consulta la tabla `knowledge_chunks` de Supabase.

**Si la entidad existe en knowledge_chunks:**
- `needs_research: false`
- El Scout continúa normalmente

**Si la entidad NO existe en knowledge_chunks:**
- `needs_research: true`
- `needs_research_reason: "Entidad desconocida: [nombre]"`
- El Analyst investigará esta entidad antes de procesar el item

El Scout **no investiga** — solo detecta y delega.

---

## Deduplicación

Antes de guardar un item, el Scout verifica:
1. ¿Ya existe un item con la misma URL en la DB? → descartar
2. ¿Ya existe un item con título muy similar (>90% similitud) en las últimas 24hs? → descartar

Esto evita que la misma noticia aparezca 5 veces porque la cubrieron 5 fuentes.

---

## Tabla en Supabase: `scout_items`

Esta tabla es nueva — no existe en el CMS actual. El Scout escribe acá,
el Analyst lee de acá.

```sql
create table scout_items (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  source_type text not null,
  url text unique,
  title text not null,
  excerpt text,
  raw_content text,
  author text,
  published_at timestamptz,
  collected_at timestamptz default now(),
  topics text[],
  entities text[],
  needs_research boolean default false,
  needs_research_reason text,
  status text default 'pending_analysis'
  -- status values:
  -- pending_analysis  → esperando al Analyst
  -- in_analysis       → Analyst trabajando en esto
  -- processed         → Analyst terminó
  -- discarded         → descartado en análisis
);
```

---

## Lo que el Scout NO hace

- No genera contenido editorial
- No verifica datos ni fuentes secundarias
- No investiga entidades desconocidas (las marca y delega)
- No escribe en la tabla `posts`
- No publica en ningún canal
- No toma decisiones editoriales

---

## Output esperado por ciclo

Cada ejecución de 6 horas produce:
- N items guardados en `scout_items` con `status: pending_analysis`
- Log de ejecución con: fuentes consultadas, items encontrados, items descartados, entidades nuevas detectadas
- Sin errores silenciosos — si una fuente falla, se loguea y se continúa con las demás

---

## Estructura de archivos

```
agents/scout/
├── scout_agent.py      # clase principal ScoutAgent
├── sources/
│   ├── rss.py          # parser de feeds RSS (noticias + YouTube)
│   ├── telegram.py     # cliente de Telegram
│   ├── binance.py      # anuncios de Binance
│   └── nansen.py       # cliente de Nansen API
├── scripts/
│   └── get_telegram_ids.py  # script auxiliar para obtener IDs de canales
├── classifier.py       # clasificación temática
├── deduplicator.py     # lógica de deduplicación
└── tests/
    ├── test_classifier.py
    ├── test_deduplicator.py
    └── test_sources.py     # tests con datos sintéticos
```

---

## Variables de entorno requeridas

```bash
# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_NAMES=y22_trades,crypto_goodreads,crypto_narratives

# Nansen
NANSEN_API_KEY=...

# Supabase (ya configuradas)
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...

# X / Twitter (Fase 2 - no requerido en MVP)
# TWITTER_BEARER_TOKEN=...
```

---

## Tests obligatorios

Antes de conectar a fuentes reales, testear con datos sintéticos:

- `test_classifier.py` — mensaje de Telegram sobre Ethereum se clasifica como `crypto_defi`
- `test_classifier.py` — noticia de política exterior sin conexión crypto se descarta
- `test_deduplicator.py` — el mismo URL no se guarda dos veces
- `test_deduplicator.py` — dos títulos casi idénticos en 24hs se deduplican
- `test_sources.py` — el parser RSS de CoinDesk devuelve la estructura correcta

---

## Fases de activación de fuentes

```
MVP (ahora):
✅ RSS — CoinDesk, Bankless, Coin Bureau
✅ Telegram — y22 trades, crypto goodreads, crypto narratives
✅ YouTube RSS — Network State, a16z, Y Combinator
✅ Binance — anuncios oficiales
⏳ Nansen — cuando se consiga API key

Fase 2 (cuando el pipeline esté funcionando):
⏳ X / Twitter — @balajis, @VitalikButerin, @a16z, @0xSamm, @higgsfield_ai
```

---

*specs/scout.md · southsea-agents · Marzo 2026*
