# CB Orange Pipeline

Automated marketing and sales pipeline for CB Orange Athletic Solutions, targeting colleges and large high schools for athletic venue equipment installations including LED lighting, scoreboards, and audio systems.

## Overview

This system automates the prospecting, qualification, research, and outreach process for B2B athletic facility sales. It uses a fleet of AI agents coordinated by an orchestrator to move prospects through the pipeline.

```
Prospector → Hygiene → Researcher → Outreach
     ↓           ↓          ↓           ↓
  Find new    Score ICP   Develop    Execute
  prospects   & assign    constraint  email
              tiers       hypothesis  sequences
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- SQLite (development)

### Installation

```bash
# Clone the repository
git clone git@github.com:ucsandman/CB-Orange.git
cd CB-Orange

# Backend setup (from project root)
python -m uvicorn api.server:app --reload --port 8765
```

```bash
# Frontend setup (new terminal)
cd dashboard
npm install
npm run dev
```

### URLs

| Application | URL |
|-------------|-----|
| Dashboard | http://localhost:3001 |
| API | http://localhost:8765 |
| API Docs | http://localhost:8765/docs |

## Architecture

### Agent Fleet

| Agent | Purpose | Schedule |
|-------|---------|----------|
| **Prospector** | Find new prospects from directories, bid portals | Daily |
| **Hygiene** | Score prospects on 8 ICP dimensions, assign tiers | On new prospects |
| **Researcher** | Develop constraint hypotheses for A1/A2 prospects | On scored prospects |
| **Outreach** | Execute tier-appropriate email sequences | Continuous |
| **Orchestrator** | Monitor health, coordinate handoffs | Every 5 minutes |

### ICP Scoring (8 Dimensions)

1. Venue Type (college D1/D2, high school 5A/6A)
2. Geography (OH, IN, PA, KY, IL = target territory)
3. Budget Signals (bonds, capital campaigns)
4. Current Lighting Age (metal halide = high score)
5. Night Game Frequency
6. Broadcast Requirements
7. Decision Maker Access
8. Project Timeline

**Tiers:**
- A1 (70+): High-touch, requires approval
- A2 (55-69): Standard automation
- B (40-54): Nurture
- C/D (<40): Deprioritized

### Prospect States

```
identified → needs_scoring → scored → needs_research →
research_complete → ready_for_outreach → outreach_active → engaged
```

## Documentation

Full build specifications are in `docs/build-specs/`:

- [00-project-overview.md](docs/build-specs/00-project-overview.md) - Business context and goals
- [01-database-schema.md](docs/build-specs/01-database-schema.md) - All table definitions
- [02-prospector-agent.md](docs/build-specs/02-prospector-agent.md) - Prospect discovery
- [03-hygiene-agent.md](docs/build-specs/03-hygiene-agent.md) - ICP scoring
- [04-researcher-agent.md](docs/build-specs/04-researcher-agent.md) - Constraint research
- [05-outreach-agent.md](docs/build-specs/05-outreach-agent.md) - Email sequences
- [06-orchestrator-agent.md](docs/build-specs/06-orchestrator-agent.md) - Coordination
- [07-dashboard.md](docs/build-specs/07-dashboard.md) - UI specifications

## Development

### Running Agents

```bash
# Run all agents once
python scripts/run_agents.py --all

# Run specific agent
python scripts/run_agents.py --agent hygiene

# Run with verbose logging
python scripts/run_agents.py --agent prospector --verbose
```

### Importing Prospects

Use the dashboard Import page at http://localhost:3001/import to upload JSON files from:
- `athletic-director-prospecting` skill
- `contact-finder` skill

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/agents/test_hygiene.py
```

## Target Market

**CB Orange Athletic Solutions** (https://cborange.com) is a manufacturer distributor and factory agent representing premium athletic facility equipment:
- Sports lighting systems
- Scoreboards and LED displays
- Scorers tables
- Digital walls of fame
- Sound systems

**Target Customers:**
- College athletics (D1, D2, D3, NAIA)
- Large high schools (5A, 6A)
- Primary geography: OH, IN, PA, KY, IL

**Typical Deal Size:** $50K - $500K+

## License

Proprietary - Internal use only
