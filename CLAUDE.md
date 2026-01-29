# CB Orange Pipeline - Technical Reference

## Project Overview

Automated marketing and sales pipeline for CB Orange Athletic Solutions, a manufacturer distributor and factory agent representing premium athletic facility equipment based in Pittsburgh, Pennsylvania. This system identifies, qualifies, and nurtures prospects (colleges and large high schools) who need athletic venue lighting upgrades.

**Company:** CB Orange Athletic Solutions, Inc. (https://cborange.com)

**Target Market:** College athletics programs (D1, D2, D3, NAIA) and large high schools (5A/6A equivalent) in Ohio, Indiana, Western Pennsylvania, Northern Kentucky, and Illinois.

**Products:** Sports lighting systems, scoreboards, LED displays, scorers tables, sound systems, and athletic facility equipment. Project sizes range from $50K to $500K+.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CB ORANGE PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐ │
│   │  Prospector  │───▶│   Hygiene    │───▶│  Researcher  │───▶│ Outreach │ │
│   │              │    │              │    │              │    │          │ │
│   │ Find venues  │    │ Score ICP    │    │ Constraint   │    │ Sequence │ │
│   │ from sources │    │ Assign tiers │    │ hypothesis   │    │ drafts   │ │
│   └──────────────┘    └──────────────┘    └──────────────┘    └──────────┘ │
│          │                   │                   │                  │       │
│          └───────────────────┴───────────────────┴──────────────────┘       │
│                                      │                                       │
│                           ┌──────────▼──────────┐                           │
│                           │    Orchestrator     │                           │
│                           │                     │                           │
│                           │ Health monitoring   │                           │
│                           │ Handoff management  │                           │
│                           └─────────────────────┘                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- SQLite (development) / PostgreSQL (production)

### Local Development

```bash
# Clone and setup
cd C:\Projects\Sportsbeams-Pipeline

# Backend setup (from project root)
python -m uvicorn api.server:app --reload --port 8765

# Frontend setup (separate terminal)
cd dashboard
npm install
npm run dev
```

### URLs (Local)
| App | URL |
|-----|-----|
| Dashboard | http://localhost:3001 |
| API | http://localhost:8765 |
| API Docs | http://localhost:8765/docs |

---

## Directory Structure

```
cb-orange-pipeline/
├── CLAUDE.md                 # This file
├── README.md                 # Project overview
├── docs/
│   └── build-specs/          # Implementation specifications
│       ├── 00-project-overview.md
│       ├── 01-database-schema.md
│       ├── 02-prospector-agent.md
│       ├── 03-hygiene-agent.md
│       ├── 04-researcher-agent.md
│       ├── 05-outreach-agent.md
│       ├── 06-orchestrator-agent.md
│       └── 07-dashboard.md
├── agents/
│   ├── base.py               # BaseAgent class
│   ├── prospector/
│   ├── hygiene/
│   ├── researcher/
│   ├── outreach/
│   └── orchestrator/
├── database/
│   ├── models.py             # SQLAlchemy models
│   ├── connection.py         # DB connection
│   └── migrations/
├── api/
│   ├── server.py             # FastAPI application
│   ├── routes/
│   └── websocket.py
├── dashboard/                # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   └── package.json
└── scripts/
    └── seed_data.py
```

---

## Key Conventions

### Code Style
- Python: Black formatter, type hints required
- TypeScript: Prettier, strict mode
- Use `127.0.0.1` instead of `localhost` in fetch calls (Windows IPv6 delays)

### Agent Conventions
- All agents extend `BaseAgent` from `agents/base.py`
- Agents emit events via `emit_event()` and heartbeats via `update_heartbeat()`
- Human approval required before A1 tier outreach sends
- All agent actions logged to `agent_audit_log` table

### Database
- SQLite for development (`pipeline.db`)
- All timestamps in UTC
- Soft deletes preferred (use `deleted_at` column)

### API
- RESTful endpoints under `/api/v1/`
- WebSocket for real-time updates at `/ws`
- All responses follow `{ success: bool, data: any, error?: string }` format

---

## ICP Scoring (8 Dimensions)

| Dimension | Weight | Max Score |
|-----------|--------|-----------|
| Venue Type | 3 | 10 |
| Geography | 2 | 10 |
| Budget Signals | 3 | 10 |
| Current Lighting Age | 2 | 10 |
| Night Game Frequency | 2 | 10 |
| Broadcast Requirements | 2 | 10 |
| Decision Maker Access | 2 | 10 |
| Project Timeline | 3 | 10 |

**Total Possible:** 190 (normalized to 100)

**Tier Thresholds:**
- A1: 70+ (immediate high-touch)
- A2: 55-69 (standard priority)
- B: 40-54 (nurture)
- C: 25-39 (long-term)
- D: <25 (not a fit)

---

## Prospect State Machine

```
IDENTIFIED ──(Prospector creates)──▶ NEEDS_SCORING
     │
NEEDS_SCORING ──(Hygiene scores)──▶ SCORED
     │
     ├──(ICP < 40)──▶ DEPRIORITIZED
     │
     └──(ICP ≥ 40)──▶ NEEDS_RESEARCH
           │
NEEDS_RESEARCH ──(Researcher)──▶ RESEARCH_COMPLETE
     │
     ├──(No viable constraint)──▶ NURTURE
     │
     └──(Constraint found)──▶ READY_FOR_OUTREACH
           │
READY_FOR_OUTREACH ──(Outreach)──▶ OUTREACH_ACTIVE
     │
     ├──(Response)──▶ ENGAGED
     │
     └──(No response after sequence)──▶ NURTURE
```

---

## Environment Variables

```env
# Database
DATABASE_URL=sqlite:///./pipeline.db

# API Keys (add as needed)
ANTHROPIC_API_KEY=
HUNTER_API_KEY=
APOLLO_API_KEY=

# Email (for outreach)
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASS=

# App Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Related Documentation

- [Project Overview](docs/build-specs/00-project-overview.md)
- [Database Schema](docs/build-specs/01-database-schema.md)
- [Prospector Agent](docs/build-specs/02-prospector-agent.md)
- [Hygiene Agent](docs/build-specs/03-hygiene-agent.md)
- [Researcher Agent](docs/build-specs/04-researcher-agent.md)
- [Outreach Agent](docs/build-specs/05-outreach-agent.md)
- [Orchestrator Agent](docs/build-specs/06-orchestrator-agent.md)
- [Dashboard](docs/build-specs/07-dashboard.md)
