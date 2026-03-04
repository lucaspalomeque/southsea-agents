# southsea-agents

Motor autónomo de contenido de **The Southmetaverse Sea** — una editorial personal de IA que cubre Crypto/Web3/DeFi, Tecnología/IA y GenAI Art.

## Qué hace

Un pipeline de agentes de IA que trabaja 24/7 para monitorear fuentes, analizar información, generar contenido editorial y distribuirlo a múltiples canales. Todo con aprobación humana obligatoria.

```
Fuentes → Scout → Analyst → Writer → Editor → [Humano aprueba] → Publisher → X / Blog / Substack / Moltbook
```

## Los agentes

| Agente | Rol |
|--------|-----|
| **Scout** | Monitorea fuentes (RSS, X, newsletters, on-chain data) y filtra por relevancia |
| **Analyst** | Verifica datos, agrega contexto, arma briefs editoriales |
| **Writer** | Genera borradores con la voz editorial de la marca |
| **Editor** | Control de calidad antes de revisión humana. Aprende del feedback |
| **Publisher** | Distribuye contenido aprobado a todos los canales |

## Stack

- **Python 3.11+**
- **Supabase** (PostgreSQL) — base de datos compartida con el CMS
- **Anthropic Claude API** — modelo principal para los agentes
- **httpx** — llamadas a Edge Functions de Supabase

## Arquitectura

Este repo es una de dos piezas:

```
southsea-agents (este repo)          southmetaverse-sea (CMS)
Python · Agentes · 24/7              React · Frontend · Lovable
         │                                     │
         └─────────────┬──────────────────────┘
                        ▼
                    Supabase
```

Los agentes **escriben** a Supabase. El CMS **lee** de Supabase. No se tocan entre sí.

## Setup

```bash
# Clonar el repo
git clone https://github.com/tu-usuario/southsea-agents.git
cd southsea-agents

# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### Variables de entorno requeridas

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
ANTHROPIC_API_KEY=sk-ant-...
```

## Estructura del proyecto

```
southsea-agents/
├── agents/
│   ├── scout/          # Monitoreo de fuentes
│   ├── analyst/        # Verificación y briefs
│   ├── writer/         # Generación de borradores
│   ├── editor/         # Control de calidad
│   └── publisher/      # Distribución a canales
├── core/
│   ├── supabase_client.py
│   ├── models.py
│   └── config.py
├── specs/              # Especificaciones de cada agente
└── docs/
```

## Roadmap

- [x] **Fase 1 — MVP:** Pipeline Scout → Writer → pending_review → aprobación humana
- [ ] **Fase 2 — Automatización:** Publisher Agent activo, distribución automática post-aprobación
- [ ] **Fase 3 — Aprendizaje:** Editor Agent que aprende de cada decisión humana
- [ ] **Fase 4 — Sala de redacción:** Visualización en tiempo real del sistema (estilo pixel art)

## Principios

- Nada se publica sin aprobación humana
- No se inventan datos ni se citan fuentes sin verificar
- Voz editorial propia, no reposteo
- Bilingue (ES/EN)
- Todo queda logeado y es trazable

---

*The Southmetaverse Sea · Marzo 2026*
